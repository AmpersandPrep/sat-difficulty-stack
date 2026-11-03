#!/usr/bin/env python3
"""No-comparisons Val on working-set items (Lydia, Nov 2, 2026:
"test it now on the other 9").

Runs working items 1-9 with the no-comparisons architecture built for
797a81fb in run_val_no_comps.py: the same brief (Lydia's v2 text with
the comparison block replaced by rating from the count, the COUNT
BEFORE YOU JUDGE block with the direct count-rating clause, and no
comp mechanics), and packets built the same way as the v2 packets
with the supplied comparison-examples section removed. The reference
document's band descriptions and skill sections, including their
illustrative examples, remain in the packet. Sol, Vera, and Snap are
not re-run; their existing working-10 records supply the packet.

Usage:
  run_val_no_comps_working.py --build-only   # packets + brief only
  run_val_no_comps_working.py [n ...]        # default 1..9
"""
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import val as val_mod
import val_v2
import run_val_no_comps as nocomps

OUT = f"{BASE}/val-no-comps-working"
COMP_HEADING = ("COMPARISON EXAMPLES FOR THE SURMISED SKILL "
                "(one per difficulty band)")
OVERVIEW_HEADING = ("FROM THE OVERVIEW DOCUMENT: "
                    "THE GENERAL OVERVIEW")


def strip_comps(packet):
    assert COMP_HEADING in packet, "packet comp heading not found"
    assert OVERVIEW_HEADING in packet, "overview heading not found"
    start = packet.index(COMP_HEADING)
    end = packet.index(OVERVIEW_HEADING)
    return packet[:start].rstrip() + "\n\n" + packet[end:]


def main():
    args = [a for a in sys.argv[1:] if a != "--build-only"]
    build_only = "--build-only" in sys.argv
    which = [int(x) for x in args] or list(range(1, 10))
    os.makedirs(OUT, exist_ok=True)
    brief = nocomps.build_brief()
    open(f"{OUT}/brief.txt", "w").write(brief)
    items = val_mod.load_json(val_mod.ITEMS)
    results = {}
    results_path = f"{OUT}/results.json"
    if os.path.exists(results_path):
        results = json.load(open(results_path))
    for n in which:
        item = items[n - 1]
        packet, strip_log = val_v2.build_packet(n, item)
        packet = strip_comps(packet)
        open(f"{OUT}/item-{n}-packet.txt", "w").write(packet)
        if build_only:
            print(f"item {n} ({item['id']}): packet built "
                  f"({len(packet)} chars)", flush=True)
            continue
        tpath = f"{OUT}/item-{n}-transcript.json"
        if str(n) in results and os.path.exists(tpath):
            print(f"item {n} ({item['id']}): already done, skipping",
                  flush=True)
            continue
        print(f"[{time.strftime('%H:%M:%S')}] item {n} "
              f"({item['id']}, CB {item['cb_rating']}) running...",
              flush=True)
        messages = [{"role": "system", "content": brief},
                    {"role": "user", "content": packet}]
        record = {"item_no": n, "id": item["id"], "packet": packet,
                  "strip_log": strip_log, "turns": [],
                  "continuations": 0}
        while True:
            resp = val_mod.call_api(messages)
            record["turns"].append(resp)
            content = ((resp.get("choices") or [{}])[0].get("message")
                       or {}).get("content") or ""
            messages.append({"role": "assistant", "content": content})
            fm = nocomps.FINAL_RATING_RE.search(content)
            if fm:
                cr = nocomps.COUNT_RATING_RE.search(content)
                if cr:
                    record["count_rating"] = cr.group(1).capitalize()
                    record["rating"] = fm.group(1).capitalize()
                    record["final_text"] = content
                    record["rule_followed"] = (
                        record["rating"] == record["count_rating"])
                    break
                if record["continuations"] < val_v2.MAX_CONTINUATIONS:
                    record["continuations"] += 1
                    messages.append({"role": "user", "content":
                        "Your reply has a final rating but no COUNT "
                        "RATING line. Complete the same evaluation "
                        "and include COUNT RATING: <Easy, Medium, or "
                        "Hard> immediately before the final RATING "
                        "line. The final rating is the count rating."})
                    continue
                record["rating"] = fm.group(1).capitalize()
                record["final_text"] = content
                record["error"] = "final rating without a count rating"
                break
            if record["continuations"] < val_v2.MAX_CONTINUATIONS:
                record["continuations"] += 1
                messages.append({"role": "user", "content":
                    "You have not finished yet. Complete your "
                    "evaluation of the same question. Include COUNT "
                    "RATING: <Easy, Medium, or Hard> immediately "
                    "before the final line RATING: <Easy, Medium, "
                    "or Hard>."})
                continue
            record["error"] = "no parseable rating after continuations"
            break
        pt = ct = 0
        for t in record["turns"]:
            if isinstance(t, dict) and "usage" in t:
                u = t["usage"] or {}
                pt += u.get("prompt_tokens") or 0
                ct += u.get("completion_tokens") or 0
        record["tokens"] = {"prompt": pt, "completion": ct}
        record["cost_usd"] = round(
            (pt * val_mod.PRICE_IN + ct * val_mod.PRICE_OUT) / 1e6, 4)
        record["messages_final"] = messages
        json.dump(record, open(tpath, "w"), indent=1)
        results[str(n)] = {
            "id": item["id"], "rating": record.get("rating"),
            "count_rating": record.get("count_rating"),
            "cb": item["cb_rating"],
            "correct": record.get("rating") == item["cb_rating"],
            "tokens": record["tokens"],
            "cost_usd": record["cost_usd"],
            "error": record.get("error")}
        json.dump(results, open(results_path, "w"), indent=1)
        print(f"  -> {record.get('rating')} (CB "
              f"{item['cb_rating']}) | ${record['cost_usd']}",
              flush=True)
    if not build_only:
        done = [r for r in results.values() if r["rating"]]
        print(f"total ${round(sum(r['cost_usd'] for r in results.values()), 4)} | "
              f"correct {sum(1 for r in done if r['correct'])}/{len(done)}",
              flush=True)


if __name__ == "__main__":
    main()
