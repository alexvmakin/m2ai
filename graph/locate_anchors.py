#!/usr/bin/env python3
"""Locate page anchors for unanchored entities by searching book PDFs (page numbers only)."""
import subprocess, json, re
from pathlib import Path
G = Path(__file__).resolve().parent
BOOKS = {
 "1/na-perekrestke-mysli.pdf": ["перекрёст","перекрест","кн.1","книга 1"],
 "1/ot-logiki-nauki-k-teorii-mysleniia.pdf": ["от логики","кн.2","книга 2"],
 "1/iazykovoe-myslenie-i-metody-ego-issledovaniia.pdf": ["языков","кн.3","книга 3"],
}
cache={}
for f in BOOKS:
    txt=subprocess.run(["pdftotext","-q","content/books/"+f,"-"],capture_output=True,timeout=200).stdout.decode("utf-8","replace")
    cache[f]=[p.lower() for p in txt.split("\f")]

nodes=[n for n in json.loads((G/"nodes.json").read_text(encoding="utf-8")) if n["type"]=="entity"]
located={}
for n in nodes:
    if n.get("anchors"): continue
    title=n["title"]
    base=re.sub(r"\s*\([^)]*\)","",title).strip()  # drop parenthetical
    if len(base)<10: continue
    hint_text=(n.get("definition","")+" "+" ".join(v.get("text","") for v in n.get("versions",[]))).lower()
    # order books by hint
    order=sorted(BOOKS, key=lambda f: 0 if any(h in hint_text for h in BOOKS[f]) else 1)
    for f in order:
        pages=cache[f]; q=base.lower()
        pg=next((i for i,p in enumerate(pages,1) if q in p), None)
        if pg:
            located[n["id"]]=[{"book":f, "file":f, "page":pg, "located":True}]
            break
json.dump(located,open(G/"located_anchors.json","w"),ensure_ascii=False,indent=1)
print("located anchors for", len(located), "previously-unanchored entities")
