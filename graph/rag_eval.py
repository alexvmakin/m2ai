#!/usr/bin/env python3
"""P3-S3 eval: retrieval recall@k and MRR for the GraphRAG engine."""
import sys, json
sys.path.insert(0, "/tmp/m2ai")
from server.main import rag_search, GRAPH_BY_ID  # noqa

EVAL = [
    ("что такое рефлексия", {"C003"}),
    ("рефлексивный выход и поглощение", {"C003", "S005"}),
    ("что такое мыследеятельность", {"C005"}),
    ("схема мыследеятельности", {"S013"}),
    ("знак значение и смысл", {"C069", "C201", "C010"}),
    ("что такое смысл", {"C010"}),
    ("верстак и кладовая", {"C093", "M016", "S069", "S070"}),
    ("содержательно-генетическая логика", {"C101"}),
    ("что такое онтология", {"C054"}),
    ("оестествление и артификация", {"C037", "T023"}),
    ("организационно-деятельностная игра ОДИ", {"C059"}),
    ("кентавр-объекты", {"C064"}),
    ("что такое программирование", {"C032"}),
    ("воспроизводство деятельности", {"C067", "C025"}),
    ("что такое понимание", {"C009"}),
    ("формальная диалектическая содержательная логика", {"C101", "C102", "C204", "C123"}),
]
K = 6


def run():
    hits = 0; mrr = 0.0; top1 = 0; rows = []
    for q, gold in EVAL:
        top, _ = rag_search(q, K)
        ids = [i for _, i in top]
        rank = next((r for r, i in enumerate(ids, 1) if i in gold), None)
        if rank:
            hits += 1; mrr += 1 / rank
            if rank == 1:
                top1 += 1
        rows.append((q, rank, ids[:3]))
    n = len(EVAL)
    print(f"recall@{K}: {hits}/{n} = {hits/n:.0%}  |  MRR: {mrr/n:.3f}  |  top-1: {top1}/{n}")
    for q, rank, ids in rows:
        mark = f"rank {rank}" if rank else "MISS"
        print(f"  [{mark:>7}] {q[:42]:42} -> {ids}")


if __name__ == "__main__":
    run()
