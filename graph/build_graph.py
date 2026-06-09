#!/usr/bin/env python3
"""M2-Граф · ingest (S0). content/entities + content/decompositions -> graph/nodes.json, edges.json."""
import json, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ENT = BASE / "content" / "entities"
DEC = BASE / "content" / "decompositions"
OUT = BASE / "graph"

CAT_LABEL = {"concepts": "Понятие", "schemas": "Схема", "theses": "Положение",
             "methods": "Методика", "methodologies": "Методология", "theories": "Теория"}
DELTAS = {"🆕": "new", "🔄": "deepened", "✅": "confirmed", "⚠️": "revised"}

nodes, edges = [], []


def field(txt, name):
    m = re.search(r">\s*\*\*" + re.escape(name) + r":\*\*\s*(.+)", txt)
    return m.group(1).strip() if m else None


def parse_entity(md_path):
    txt = md_path.read_text(encoding="utf-8", errors="replace")
    title = (re.search(r"^#\s+(.+)", txt, re.M) or [None, md_path.parent.name])[1].strip()
    eid = field(txt, "ID") or md_path.parent.name
    cat = md_path.parts[md_path.parts.index("entities") + 1]
    sub = field(txt, "Подкатегория")
    first = field(txt, "Первое появление")
    # base definition: prose under ## Описание before any ### subsection
    versions, definition = [], ""
    md = re.search(r"##\s+Описание\s*(.*?)(?=\n###|\n##|\Z)", txt, re.S)
    if md:
        definition = re.sub(r"\s+", " ", md.group(1)).strip()[:600]
    # versions: ALL ### subsections (Папка/Книга), wherever they live
    for m in re.finditer(r"\n###\s+([^\n]+)\n(.*?)(?=\n###|\n##|\Z)", txt, re.S):
        head = m.group(1).strip()
        body = re.sub(r"\s+", " ", m.group(2)).strip()[:600]
        if not re.search(r"Папк|Книг|П0|Кн\.|Источник", head):
            continue
        delta = next((v for k, v in DELTAS.items() if k in head), "new")
        versions.append({"source": head, "delta": delta, "text": body})
        if not definition and body and not body.lstrip().startswith("-"):
            definition = body
    if not definition and versions:
        definition = versions[0]["text"]
    # sources
    src = []
    ms = re.search(r"##\s+Источники(.+?)(\n##|\Z)", txt, re.S)
    if ms:
        for line in ms.group(1).splitlines():
            line = line.strip(" -•")
            if line and not line.startswith("#") and len(line) > 3:
                src.append(line)
    return {"id": eid, "type": "entity", "title": title, "category": cat,
            "category_label": CAT_LABEL.get(cat, cat), "subcategory": sub,
            "first_appearance": first, "slug": md_path.parent.name,
            "definition": definition, "versions": versions, "sources": src[:8]}


def parse_connections(conn_path, src_id):
    txt = conn_path.read_text(encoding="utf-8", errors="replace")
    types = {}
    for m in re.finditer(r"\|\s*([CSTM]\w*\d+|\w+)\s*\|\s*([^|]+?)\s*\|", txt):
        types[m.group(1).strip()] = m.group(2).strip()
    out = []
    sec = re.search(r"Исходящие связи(.+?)(##|\Z)", txt, re.S)
    if sec:
        for m in re.finditer(r"\*\*([A-ZА-Я]+\d+|[A-Za-z0-9\-]+)\*\*\s*[—-]\s*(.+)", sec.group(1)):
            tid, tname = m.group(1).strip(), m.group(2).strip()
            out.append({"target": tid, "target_name": tname,
                        "rel_type": types.get(tid, "содержательная")})
    return out


def main():
    ent_ids = set()
    for md in sorted(ENT.rglob("entity.md")):
        e = parse_entity(md)
        nodes.append(e)
        ent_ids.add(e["id"])
        conn = md.parent / "CONNECTIONS.md"
        if conn.exists():
            for c in parse_connections(conn, e["id"]):
                edges.append({"from": e["id"], "to": c["target"], "rel": "relates_to",
                              "rel_type": c["rel_type"], "to_name": c["target_name"]})

    # extra stub entities (gap concepts from integrated map)
    extra_path = ENT.parent.parent / "graph" / "extra_entities.json"
    if extra_path.exists():
        ex = json.loads(extra_path.read_text(encoding="utf-8"))
        for e in ex.get("entities", []):
            nodes.append({"id": e["id"], "type": "entity", "title": e["title"],
                          "category": e.get("category", "concepts"),
                          "category_label": CAT_LABEL.get(e.get("category", "concepts"), "Понятие"),
                          "layer": e.get("layer"), "status": e.get("status", "stub"),
                          "definition": e.get("definition", ""), "versions": [], "sources": []})
            ent_ids.add(e["id"])
            for r in e.get("relates", []):
                edges.append({"from": e["id"], "to": r["to"], "rel": "relates_to",
                              "rel_type": r.get("type", "содержательная"), "to_name": r.get("name", r["to"])})

    # weak co-mention edges (connect isolates) — distinct from curated relates_to
    ent_nodes = [n for n in nodes if n.get("type") == "entity"]
    title_idx = [(n["id"], n["title"]) for n in ent_nodes if len(n["title"]) >= 8]
    existing = {(e["from"], e["to"]) for e in edges}
    for n in ent_nodes:
        text = (n.get("definition", "") + " " + " ".join(v.get("text", "") for v in n.get("versions", []))).lower()
        if not text.strip():
            continue
        cnt = 0
        for tid, ttl in title_idx:
            if tid == n["id"]:
                continue
            if ttl.lower() in text and (n["id"], tid) not in existing:
                edges.append({"from": n["id"], "to": tid, "rel": "mentions", "rel_type": "co-mention"})
                existing.add((n["id"], tid))
                cnt += 1
                if cnt >= 8:
                    break

    # isolate-targeted lenient linking (from authored notes, threshold 5)
    deg = {}
    for e in edges:
        deg[e["from"]] = deg.get(e["from"], 0) + 1
        deg[e["to"]] = deg.get(e["to"], 0) + 1
    ent_nodes2 = [n for n in nodes if n.get("type") == "entity"]
    short_idx = [(n["id"], n["title"]) for n in ent_nodes2 if len(n["title"]) >= 5]
    existing2 = {(e["from"], e["to"]) for e in edges}
    for n in ent_nodes2:
        if deg.get(n["id"], 0) > 0:
            continue
        text = (n.get("definition", "") + " " + " ".join(v.get("text", "") for v in n.get("versions", []))).lower()
        added = 0
        for tid, ttl in short_idx:
            if tid == n["id"]:
                continue
            if ttl.lower() in text and (n["id"], tid) not in existing2:
                edges.append({"from": n["id"], "to": tid, "rel": "mentions", "rel_type": "co-mention"})
                existing2.add((n["id"], tid)); added += 1
                if added >= 5:
                    break
        # reverse: someone mentions the isolate
        if deg.get(n["id"], 0) == 0 and added == 0 and len(n["title"]) >= 5:
            for m in ent_nodes2:
                if m["id"] == n["id"]:
                    continue
                mt = (m.get("definition", "") + " " + " ".join(v.get("text", "") for v in m.get("versions", []))).lower()
                if n["title"].lower() in mt and (m["id"], n["id"]) not in existing2:
                    edges.append({"from": m["id"], "to": n["id"], "rel": "mentions", "rel_type": "co-mention"})
                    existing2.add((m["id"], n["id"])); break

    # decompositions: operation types + genetic map + operations + sources
    alpha = json.loads((DEC / "04_MERGED_ALPHABET.json").read_text(encoding="utf-8"))
    code_by_key = {}
    for i, (key, v) in enumerate(alpha["unified_alphabet"].items(), 1):
        code = f"A{i:02d}"
        code_by_key[key] = code
        nodes.append({"id": code, "type": "operation_type", "title": key.replace("_", " "),
                      "category": "operation_type", "category_label": "Тип операции",
                      "definition": v.get("definition", ""), "s_pattern": v.get("sopostavlenie_pattern"),
                      "sign": v.get("otnesenie_pattern"), "frequency": v.get("frequency"),
                      "genetic_complexity": v.get("genetic_complexity"), "key": key})
    for e in alpha["meta_genetic_map"].get("edges", []):
        edges.append({"from": e["from"], "to": e["to"], "rel": "transforms",
                      "condition": e.get("condition", ""), "weight": e.get("weight", 1)})

    for dj in sorted(DEC.glob("0[123]_*.json")):
        d = json.loads(dj.read_text(encoding="utf-8"))
        meta = d.get("metadata", {})
        sid = "SRC_" + dj.stem
        nodes.append({"id": sid, "type": "source", "title": meta.get("text", dj.stem),
                      "category": "source", "category_label": "Источник",
                      "author": meta.get("author"), "year": meta.get("year"),
                      "definition": f"GP-разложение · {len(d.get('operations',[]))} операций"})

    OUT.mkdir(exist_ok=True)
    # backlinks
    incoming = {}
    for e in edges:
        incoming.setdefault(e["to"], []).append({"from": e["from"], "rel": e["rel"]})
    by_id = {n["id"]: n for n in nodes}
    for n in nodes:
        n["backlinks"] = incoming.get(n["id"], [])
        n["degree"] = len([e for e in edges if e["from"] == n["id"] or e["to"] == n["id"]])
    (OUT / "nodes.json").write_text(json.dumps(nodes, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "edges.json").write_text(json.dumps(edges, ensure_ascii=False, indent=1), encoding="utf-8")

    cats = {}
    for n in nodes:
        cats[n["category"]] = cats.get(n["category"], 0) + 1
    resolved = sum(1 for e in edges if e["rel"] == "relates_to" and e["to"] in by_id)
    rel_total = sum(1 for e in edges if e["rel"] == "relates_to")
    print(f"nodes={len(nodes)} edges={len(edges)}")
    print("by category:", cats)
    print(f"relates_to resolved={resolved}/{rel_total} (siroty/unresolved={rel_total-resolved})")


if __name__ == "__main__":
    main()
