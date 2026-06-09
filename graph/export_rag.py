#!/usr/bin/env python3
"""S5 · RAG export. Build per-entity documents (JSONL) + combined graph (JSON)."""
import json
from pathlib import Path
G = Path(__file__).resolve().parent
OUT = G / "export"; OUT.mkdir(exist_ok=True)
nodes = json.loads((G / "nodes.json").read_text(encoding="utf-8"))
edges = json.loads((G / "edges.json").read_text(encoding="utf-8"))
by = {n["id"]: n for n in nodes}

out_adj, in_adj = {}, {}
for e in edges:
    out_adj.setdefault(e["from"], []).append(e)
    in_adj.setdefault(e["to"], []).append(e)

docs = []
for n in nodes:
    if n.get("type") != "entity":
        continue
    rels = []
    for e in out_adj.get(n["id"], []):
        tgt = by.get(e["to"])
        if tgt:
            rels.append(f'{e.get("rel_type") or e["rel"]} → {tgt["title"]}')
    backs = []
    for e in in_adj.get(n["id"], []):
        src = by.get(e["from"])
        if src:
            backs.append(src["title"])
    versions = " | ".join(f'{v.get("source","")}: {v.get("text","")}' for v in n.get("versions", []))
    anchors = [{"book": a.get("book") or a["file"].split("/")[-1], "page": a.get("page")} for a in n.get("anchors", [])]
    # composed retrieval text
    text = f'{n["title"]}. {n.get("definition","")}'
    if rels:
        text += " Связи: " + "; ".join(rels[:12]) + "."
    docs.append({
        "id": n["id"], "title": n["title"], "category": n.get("category_label"),
        "layer": n.get("layer"), "text": text, "definition": n.get("definition", ""),
        "versions": versions, "relations": rels, "backlinks": backs[:12],
        "anchors": anchors, "aliases": n.get("aliases", []),
        "url": f"/wiki/{n['id']}",
    })

with open(OUT / "documents.jsonl", "w", encoding="utf-8") as f:
    for d in docs:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

graph = {"meta": {"entities": sum(1 for n in nodes if n.get("type") == "entity"),
                  "nodes": len(nodes), "edges": len(edges),
                  "generated_for": "RAG / GraphRAG (P3)"},
         "nodes": nodes, "edges": edges}
(OUT / "m2graph.json").write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")
print(f"export: {len(docs)} documents.jsonl, m2graph.json ({len(nodes)} nodes / {len(edges)} edges)")
