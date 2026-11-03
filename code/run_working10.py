#!/usr/bin/env python3
"""Driver: run Sol (solver.py, unmodified) on the working set of 10.

Items are the 10 IDs in files/working-set-10.md, in that file's order.
Transcripts, results, and report go to working-10/ next to solver.py.
Resumable: items with an existing transcript are skipped.
"""
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import solver  # noqa: E402  (Sol exactly as built; nothing patched)

OUT = f"{BASE}/working-10"
IDS = ["da2e9202", "6e06a0a7", "8622320e", "029c2dc2", "3f236877",
       "8391a002", "f7dbde16", "d28c29e1", "67b59a67", "155239cf"]


def build_items():
    blind, scored = solver.load_bank()
    items = []
    for qid in IDS:
        b, s = blind[qid], scored[qid]
        items.append({
            "id": qid, "question": b["question"], "choices": b["choices"],
            "section": s["section"],
            "cb_domain": s["cb_domain"], "cb_skill": s["cb_skill"],
            "cb_rating": s["cb_rating"], "cb_answer": s["cb_answer"],
        })
    return items


def main():
    os.makedirs(OUT, exist_ok=True)
    items = build_items()
    json.dump(items, open(f"{OUT}/items.json", "w"), indent=1)
    results_path = f"{OUT}/results.json"
    results = {}
    if os.path.exists(results_path):
        results = json.load(open(results_path))
    for n, item in enumerate(items, 1):
        tpath = f"{OUT}/item-{n}-transcript.json"
        if str(n) in results and os.path.exists(tpath):
            print(f"item {n} ({item['id']}): already done, skipping",
                  flush=True)
            continue
        print(f"[{time.strftime('%H:%M:%S')}] item {n} ({item['id']}, "
              f"{item['section']}, CB {item['cb_rating']}) running...",
              flush=True)
        rec = solver.run_item(n, item)
        json.dump(rec, open(tpath, "w"), indent=1)
        results[str(n)] = solver.summarize(rec)
        json.dump(results, open(results_path, "w"), indent=1)
        s = results[str(n)]
        print(f"  -> solver: {s['solver']} | verdicts {s['verdicts']} | "
              f"lookups {s['n_lookups']} | tokens {s['tokens']} | "
              f"error {s['error']}", flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
