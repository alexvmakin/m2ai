#!/usr/bin/env python3
"""Apply same_as/refines review decisions to the graph."""
import json
from pathlib import Path
G = Path(__file__).resolve().parent
nodes = json.loads((G/"nodes.json").read_text(encoding="utf-8"))
edges = json.loads((G/"edges.json").read_text(encoding="utf-8"))
dec = json.loads((G/"review_decisions.json").read_text(encoding="utf-8"))
by = {n["id"]: n for n in nodes}
PRI = {"concepts":0,"theories":1,"methodologies":2,"methods":3,"theses":4,"schemas":5}

def canon(a, b):
    na, nb = by.get(a), by.get(b)
    if not na or not nb: return a, b
    ka = (PRI.get(na["category"],9), -len(na.get("versions",[])), -na.get("degree",0), len(na["title"]))
    kb = (PRI.get(nb["category"],9), -len(nb.get("versions",[])), -nb.get("degree",0), len(nb["title"]))
    return (a, b) if ka <= kb else (b, a)

# union-find for merges
parent = {n["id"]: n["id"] for n in nodes}
def find(x):
    while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
    return x
merges=[]
for d in dec:
    if d["decision"]=="merge" and d["a"] in by and d["b"] in by:
        keep, drop = canon(d["a"], d["b"])
        parent[find(drop)] = find(keep)
        merges.append((keep, drop))

# resolve canonical per node
def cid(x): return find(x) if x in parent else x
# fold dropped nodes into canonical
keep_nodes={}
alias={}
for n in nodes:
    c = cid(n["id"])
    if c == n["id"]:
        keep_nodes[n["id"]] = n
for n in nodes:
    c = cid(n["id"])
    if c != n["id"]:
        alias[n["id"]] = c
        k = keep_nodes[c]
        k.setdefault("merged_ids", []).append(n["id"])
        k.setdefault("aliases", [])
        if n["title"] not in k["aliases"] and n["title"]!=k["title"]:
            k["aliases"].append(n["title"])
        # fold versions/sources
        ex={v.get("source") for v in k.get("versions",[])}
        for v in n.get("versions",[]):
            if v.get("source") not in ex: k.setdefault("versions",[]).append(v)
        for s in n.get("sources",[]):
            if s not in k.get("sources",[]): k.setdefault("sources",[]).append(s)
        exa={(a.get("file"),a.get("page")) for a in k.get("anchors",[])}
        for a in n.get("anchors",[]):
            if (a.get("file"),a.get("page")) not in exa: k.setdefault("anchors",[]).append(a)

# redirect edges through canonical; drop self-loops; dedup
seen=set(); new_edges=[]
for e in edges:
    f, t = cid(e["from"]), cid(e["to"])
    if f==t: continue
    key=(f,t,e.get("rel"),e.get("rel_type"))
    if key in seen: continue
    seen.add(key); ee=dict(e); ee["from"]=f; ee["to"]=t; new_edges.append(ee)

# add refines edges
added=0
for d in dec:
    if d["decision"] in ("refa","refb"):
        a,b = cid(d["a"]), cid(d["b"])
        frm, to = (a,b) if d["decision"]=="refa" else (b,a)
        if frm==to or frm not in keep_nodes or to not in keep_nodes: continue
        key=(frm,to,"refines",None)
        if key in seen: continue
        seen.add(key); new_edges.append({"from":frm,"to":to,"rel":"refines","rel_type":"уточнение"}); added+=1

nodes2=list(keep_nodes.values())
# recompute degree + backlinks
inc={}
for e in new_edges: inc.setdefault(e["to"],[]).append({"from":e["from"],"rel":e["rel"]})
for n in nodes2:
    n["backlinks"]=inc.get(n["id"],[])
    n["degree"]=len([e for e in new_edges if e["from"]==n["id"] or e["to"]==n["id"]])

(G/"nodes.json").write_text(json.dumps(nodes2,ensure_ascii=False,indent=1),encoding="utf-8")
(G/"edges.json").write_text(json.dumps(new_edges,ensure_ascii=False,indent=1),encoding="utf-8")
(G/"aliases.json").write_text(json.dumps(alias,ensure_ascii=False,indent=1),encoding="utf-8")
print(f"merges={len(merges)} aliases={len(alias)} refines_added={added}")
print(f"nodes {len(nodes)}->{len(nodes2)} edges {len(edges)}->{len(new_edges)}")
