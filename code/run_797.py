#!/usr/bin/env python3
"""One-off full-stack run: the parallel-lines system, item 797a81fb
(Lydia's direction, Nov 2, 2026: "run just that question for now").

Runs Sol, Vera, and Snap fresh on this item, then Val under the v2
brief and packet (val_v2), whose General coverage card now carries
Lydia's discriminant entry. College Board: Algebra / Systems of two
linear equations in two variables / Hard / answer D.

IMPORTANT item note: the bank's extracted text for this item lost the
system itself (math notation was stripped in the PDF text layer), so
the item here uses the question exactly as a student sees it,
transcribed and verified from the bank page image on Nov 2, 2026:
-12x + 14y = 36 and -6x + 7y = -18.
"""
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import solver
import vera as vera_mod
import snap as snap_mod
import val as val_mod
import val_v2

STAGE = f"{BASE}/val-v2-2q/systems-797"
ITEM = {
    "id": "797a81fb",
    "question": ("-12x + 14y = 36\n-6x + 7y = -18\n\n"
                 "How many solutions does the given system of "
                 "equations have?"),
    "choices": {"A": "Exactly one", "B": "Exactly two",
                "C": "Infinitely many", "D": "Zero"},
    "section": "Math",
    "cb_domain": "Algebra",
    "cb_skill": "Systems of two linear equations in two variables",
    "cb_rating": "Hard",
    "cb_answer": "D",
}


def main():
    os.makedirs(STAGE, exist_ok=True)
    json.dump([ITEM], open(f"{STAGE}/items.json", "w"), indent=1)
    vera_mod.WORK_DIR = STAGE

    print(f"[{time.strftime('%H:%M:%S')}] Sol running...", flush=True)
    sol_rec = solver.run_item(1, ITEM)
    json.dump(sol_rec, open(f"{STAGE}/item-1-transcript.json", "w"),
              indent=1)
    sol_sum = solver.summarize(sol_rec)
    json.dump({"1": sol_sum}, open(f"{STAGE}/results.json", "w"), indent=1)
    sol_final = sol_sum["solver"]
    print(f"  Sol: {sol_final}", flush=True)

    print(f"[{time.strftime('%H:%M:%S')}] Vera running...", flush=True)
    vera_rec = vera_mod.run_item(1, ITEM, sol_final)
    json.dump(vera_rec, open(f"{STAGE}/vera-transcript.json", "w"), indent=1)
    vera_final = vera_mod.summarize(vera_rec)["vera"]
    print(f"  Vera: {vera_final}", flush=True)

    print(f"[{time.strftime('%H:%M:%S')}] Snap running...", flush=True)
    snap_rec = snap_mod.run_item(1, ITEM)
    json.dump(snap_rec, open(f"{STAGE}/snap-transcript.json", "w"), indent=1)
    print(f"  Snap: {snap_rec.get('parsed')}", flush=True)

    # Val v2 packet, mirroring val_v2.build_packet from staged records
    sol_raw = vera_mod.sol_assistant_text(1)
    sol_view, strip_log = vera_mod.strip_sol_rating(sol_raw)
    comps_text, _p = vera_mod.fulfill_comp(
        vera_final["domain"], vera_final["skill"], ITEM["id"])
    ref = open(val_v2.REFERENCE).read()
    overview = val_v2.extract_section(ref, "# Overview")
    skill_section = val_v2.extract_section(
        ref, f"## Skill: {vera_final['skill']}")
    cov = open(val_v2.COVERAGE).read()
    cov_skill = val_v2.extract_section(cov, f"## {vera_final['skill']}")
    gen_head = next(ln for ln in cov.split("\n")
                    if ln.startswith("## General"))
    cov_general = val_v2.extract_section(cov, gen_head)
    lines = []
    lines.append("Here is one SAT question to evaluate, with "
                 "everything assembled for you.")
    lines.append("")
    lines.append("THE QUESTION")
    lines.append(ITEM["question"])
    for L in "ABCD":
        lines.append(f"{L}) {ITEM['choices'][L]}")
    lines.append("")
    lines.append("THE SURMISED DOMAIN AND SKILL")
    lines.append(f"Domain: {sol_final['domain']}")
    lines.append(f"Skill: {sol_final['skill']}")
    lines.append("")
    lines.append("SOL'S TRANSCRIPT")
    lines.append(sol_view)
    lines.append("")
    lines.append("BACK AND FORTH BETWEEN SOL AND VERA")
    lines.append("None for this question.")
    lines.append("")
    lines.append("SNAP'S SCRAMBLE AND SURMISED TOPIC")
    lines.append(f"Scramble: {snap_rec['scramble']}")
    parsed = snap_rec.get("parsed") or {}
    if parsed.get("snap"):
        lines.append(f"Surmised topic: {parsed['snap']}")
    lines.append("")
    lines.append("COMPARISON EXAMPLES FOR THE SURMISED SKILL "
                 "(one per difficulty band)")
    lines.append(comps_text)
    lines.append("")
    lines.append("FROM THE OVERVIEW DOCUMENT: THE GENERAL OVERVIEW")
    lines.append(overview)
    lines.append("")
    lines.append("FROM THE OVERVIEW DOCUMENT: THIS SKILL")
    lines.append(skill_section)
    lines.append("")
    lines.append("COVERAGE NOTES (written by Lydia; background about "
                 "the student population for this skill, not a signal "
                 "about this question)")
    lines.append(cov_skill)
    lines.append("")
    lines.append("COVERAGE NOTES, GENERAL (all skills)")
    lines.append(cov_general)
    packet = "\n".join(lines)
    open(f"{STAGE}/val-packet.txt", "w").write(packet)

    brief = val_v2.build_brief()
    messages = [{"role": "system", "content": brief},
                {"role": "user", "content": packet}]
    record = {"item_no": 1, "id": ITEM["id"], "packet": packet,
              "strip_log": strip_log, "turns": [], "comp_pulls": [],
              "continuations": 0}
    comps_left = val_v2.MAX_COMPS
    while True:
        resp = val_mod.call_api(messages)
        record["turns"].append(resp)
        content = ((resp.get("choices") or [{}])[0].get("message") or {}
                   ).get("content") or ""
        messages.append({"role": "assistant", "content": content})
        cm = val_v2.COMP_RE.search(content)
        m = val_v2.RATING_RE.search(content)
        if cm and comps_left > 0 and not m:
            comps_left -= 1
            reply, _p = vera_mod.fulfill_comp(cm.group(1), cm.group(2),
                                              ITEM["id"])
            record["comp_pulls"].append({"domain": cm.group(1),
                                         "skill": cm.group(2)})
            messages.append({"role": "user", "content": reply})
            continue
        if m:
            record["rating"] = m.group(1).capitalize()
            record["final_text"] = content
            break
        if record["continuations"] < val_v2.MAX_CONTINUATIONS:
            record["continuations"] += 1
            messages.append({"role": "user", "content":
                "You have not finished yet. Complete your evaluation "
                "of the same question and end with the final line "
                "RATING: <Easy, Medium, or Hard>."})
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
    json.dump(record, open(f"{STAGE}/val-transcript.json", "w"), indent=1)
    print(f"Val: {record.get('rating')} (CB Hard) | "
          f"${record['cost_usd']} | pulls {len(record['comp_pulls'])}",
          flush=True)


if __name__ == "__main__":
    main()
