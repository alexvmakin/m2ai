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


def clean_text(s, limit=700):
    if not s:
        return ""
    s = re.sub(r"(?m)^\s*#{1,6}.*$", " ", s)        # drop markdown heading lines
    s = re.sub(r"-{3,}", " ", s)                      # drop horizontal rules ---
    s = re.sub(r"\*\*Источники:\*\*.*", " ", s)      # drop trailing source markers
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)          # unbold
    s = s.replace("**", "").replace("__", "")
    s = re.sub(r"^[\s\-•*]+", "", s)                  # leading bullets
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit].strip()

BOOK_FILES = [
    ("на перекр", "1/na-perekrestke-mysli.pdf"),
    ("от логики науки", "1/ot-logiki-nauki-k-teorii-mysleniia.pdf"),
    ("языков", "1/iazykovoe-myslenie-i-metody-ego-issledovaniia.pdf"),
    ("путеводитель по ору", "0/1_SHH_Putevoditel ORU.pdf"),
    ("ору", "0/1_SHH_Putevoditel ORU.pdf"),
    ("понятиям и схемам", "0/2_SHH_Putevoditel ponyatiya i shemy_pravka.pdf"),
    ("общая управленческая", "0/Общая управленческая подготовка.pdf"),
    ("рефлекси", "0/Reflexia.pdf"),
    ("мифпсихолог", "1/Shedrovickiyi_G._Mifpsihologiya._Ot_Teorii_Myishleniya_K_T.a4.pdf"),
]


def _book_file(src_low):
    for key, f in BOOK_FILES:
        if key in src_low:
            return f
    return None


try:
    _OFFSETS = {k: v.get("offset", 0) for k, v in json.loads((Path(__file__).resolve().parent / "book_offsets.json").read_text(encoding="utf-8")).items()}
except Exception:
    _OFFSETS = {}


def _deep_link(f, page):
    from urllib.parse import quote as _q
    link = "/content/books/" + "/".join(_q(p) for p in f.split("/"))
    if page:
        link += f"#page={page + _OFFSETS.get(f, 0)}"
    return link


def make_anchors(text):
    low = text.lower()
    books_in = [(k, f) for k, f in BOOK_FILES if k in low]
    out, seen = [], set()
    for m in re.finditer(r"стр\.?\s*(\d+)", text):
        page = int(m.group(1))
        win = low[max(0, m.start() - 90):m.start()]
        f = _book_file(win)
        if not f and len({f2 for _, f2 in books_in}) == 1:
            f = books_in[0][1]
        if not f:
            continue
        key = (f, page)
        if key in seen:
            continue
        seen.add(key)
        label = text[max(0, m.start() - 70):m.start() + len(m.group(0))].strip().split(chr(10))[-1][-70:]
        out.append({"label": label, "file": f, "page": page, "deep_link": _deep_link(f, page)})
        if len(out) >= 8:
            break
    return out

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
    # base definition: clean prose under ## Описание (heading lines stripped)
    versions, definition = [], ""
    dm = re.search(r"##\s+Описание\s*(.*?)(?=\n##\s|\Z)", txt, re.S)
    if dm:
        definition = clean_text(dm.group(1))
    # versions: ALL ### subsections (Папка/Книга), wherever they live
    for m in re.finditer(r"\n###\s+([^\n]+)\n(.*?)(?=\n###|\n##\s|\Z)", txt, re.S):
        head = re.sub(r"\s+", " ", m.group(1)).strip()
        if not re.search(r"Папк|Книг|П0|Кн\.|Источник", head):
            continue
        body = clean_text(m.group(2), 500)
        delta = next((v for k, v in DELTAS.items() if k in head), "new")
        versions.append({"source": head, "delta": delta, "text": body})
    # if Описание had no prose, take first version body that is real prose (not page refs)
    if not definition:
        for v in versions:
            t = v["text"]
            if t and not re.match(r"^(на перекр|от логики|языков|путеводитель|стр\.?|с\.?\s*\d)", t.lower()) and len(t) > 20:
                definition = t
                break
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
            "definition": definition, "versions": versions, "sources": src[:8], "anchors": make_anchors(txt)}


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
                          "definition": e.get("definition", ""), "versions": [], "sources": [],
                          "anchors": [dict(a, deep_link=_deep_link(a["file"], a.get("page"))) for a in e.get("anchors", [])]})
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

    # enrich: fuller paraphrase definitions for key concepts
    enr_path = OUT / "enrich.json"
    if enr_path.exists():
        enr = json.loads(enr_path.read_text(encoding="utf-8"))
        for n in nodes:
            if n.get("type") == "entity" and n["id"] in enr:
                n["definition"] = enr[n["id"]]
                n["status"] = n.get("status") or "enriched"

    # merge located anchors (PDF title-search) for entities without note-anchors
    loc_path = OUT / "located_anchors.json"
    if loc_path.exists():
        loc = json.loads(loc_path.read_text(encoding="utf-8"))
        for n in nodes:
            if n.get("type") == "entity" and not n.get("anchors") and n["id"] in loc:
                n["anchors"] = [dict(a, deep_link=_deep_link(a["file"], a.get("page"))) for a in loc[n["id"]]]

    # S3 bridge: operation layer <-> entity layer (curated, justified)
    op_ids = [n["id"] for n in nodes if n.get("type") == "operation_type"]
    ent_present = {n["id"] for n in nodes if n.get("type") == "entity"}
    def add(f, t, rel, rt):
        if t in ent_present or t in op_ids:
            edges.append({"from": f, "to": t, "rel": rel, "rel_type": rt})
    SGL = "C101"
    for oid in op_ids:                       # алфавит реализует СГЛ
        add(oid, SGL, "relates_to", "операциональная логика")
    add("A12", "C202", "produces", "замена принципа → замещение")
    add("A17", "C003", "produces", "рефлексивный режим → рефлексия")
    add("A16", "C054", "produces", "онтологическая перерамка → онтология")
    add("C112", SGL, "relates_to", "сопоставление — часть операции")   # сопоставление
    add("C113", SGL, "relates_to", "отнесение — часть операции")       # соотнесение/отнесение
    for n in nodes:
        if n.get("type") == "source":
            add(n["id"], SGL, "relates_to", "разложение по СГЛ")

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
