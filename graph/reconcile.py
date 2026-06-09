#!/usr/bin/env python3
"""S1 · резолюция и покрытие. nodes/edges/backbone -> reconcile.json."""
import json, re
from pathlib import Path
from itertools import combinations

BASE = Path(__file__).resolve().parent.parent
G = BASE / "graph"

nodes = json.loads((G / "nodes.json").read_text(encoding="utf-8"))
edges = json.loads((G / "edges.json").read_text(encoding="utf-8"))
bb = json.loads((G / "backbone.json").read_text(encoding="utf-8"))
ents = [n for n in nodes if n["type"] == "entity"]
by_id = {n["id"]: n for n in nodes}


def norm(s):
    s = (s or "").lower().strip()
    s = re.sub(r"[«»\"'()]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


# isolates (degree 0)
isolates = [{"id": n["id"], "title": n["title"], "category": n.get("category_label")}
            for n in ents if n.get("degree", 0) == 0]

# reviewed pairs to exclude (already decided on the board)
reviewed_ids, reviewed_titles = set(), set()
rd_path = G / "review_decisions.json"
if rd_path.exists():
    for d in json.loads(rd_path.read_text(encoding="utf-8")):
        reviewed_ids.add(frozenset((d["a"], d["b"])))
# refines-linked pairs also excluded
refined = {frozenset((e["from"], e["to"])) for e in edges if e.get("rel") in ("refines",)}
title_by_id = {n["id"]: norm(n["title"]) for n in ents}

# same_as candidates: equal/containment titles across different ids
cands = []
for a, b in combinations(ents, 2):
    na, nb = norm(a["title"]), norm(b["title"])
    if not na or not nb:
        continue
    reason = None
    if na == nb:
        reason = "идентичный заголовок"
    elif (na in nb or nb in na) and abs(len(na) - len(nb)) <= 12 and min(len(na), len(nb)) >= 5:
        reason = "вложенный заголовок"
    if reason and frozenset((a["id"], b["id"])) not in reviewed_ids \
            and frozenset((a["id"], b["id"])) not in refined:
        cands.append({"a": a["id"], "a_title": a["title"], "b": b["id"], "b_title": b["title"],
                      "same_category": a["category"] == b["category"], "reason": reason})

# backbone reconciliation: gaps
def match(label):
    ll = norm(label)
    for n in ents:
        t = norm(n["title"])
        if ll and (ll == t or ll in t or t in ll):
            return n
    return None

gaps, matched = [], 0
for nd in bb["nodes"]:
    m = match(nd.get("match", nd["label"]))
    if m:
        matched += 1
    else:
        gaps.append({"backbone": nd["label"], "match_key": nd.get("match")})
tot = len(bb["nodes"])

# coverage verdict (simplified 4 dims)
rel = [e for e in edges if e["rel"] == "relates_to"]
resolved = sum(1 for e in rel if e["to"] in by_id)
dims = {
    "backbone_coverage_pct": round(matched * 100 / tot) if tot else 0,
    "isolate_count": len(isolates),
    "isolate_pct": round(len(isolates) * 100 / len(ents)) if ents else 0,
    "relates_resolved_pct": round(resolved * 100 / len(rel)) if rel else 0,
    "same_as_candidates": len(cands),
    "entities": len(ents),
}
# verdict
if dims["backbone_coverage_pct"] >= 75 and dims["isolate_pct"] <= 10:
    verdict = "CAUTION" if (dims["same_as_candidates"] > 0 or gaps) else "GO"
else:
    verdict = "LOOP"
reasons = []
if gaps:
    reasons.append(f"{len(gaps)} пробелов каркаса — кандидаты на извлечение/доразметку")
if cands:
    reasons.append(f"{len(cands)} кандидатов same_as — нужен ручной разбор")
if isolates:
    reasons.append(f"{len(isolates)} сирот без связей")

out = {"verdict": verdict, "dims": dims, "reasons": reasons,
       "isolates": isolates, "same_as_candidates": cands,
       "backbone_gaps": gaps, "backbone_matched": matched, "backbone_total": tot}
(G / "reconcile.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("verdict:", verdict)
print("dims:", dims)
print("isolates:", len(isolates), "| same_as cands:", len(cands), "| gaps:", len(gaps))
print("gap labels:", [g["backbone"] for g in gaps])
print("sample same_as:", [(c["a_title"], c["b_title"]) for c in cands[:8]])
