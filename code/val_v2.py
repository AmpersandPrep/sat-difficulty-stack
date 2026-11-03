#!/usr/bin/env python3
"""Val v2 — first run of Lydia's rewritten instructions (Nov 2, 2026).

Lydia's go: run the two known-miss questions from the morning's
iteration protocol, item 3 (Transitions) and item 8 (Ratios), both
College Board Medium, both rated Easy by every earlier version.

Brief: Lydia's own pasted instruction text
(val-10/instructions-v2-lydia-paste-2026-11-02.txt) with ONLY her two
approved fixes applied:
  1. the comparison block appears once (her paste carried it twice);
  2. the comparison rules use her two-anchor wording, approved in
     chat Nov 2 ("find a similar Hard question and a Medium question
     the hard question is harder than," extended to Medium and Easy
     in the same pattern).
A short RUNNER MECHANICS appendix (comp-request line format; finish
with a RATING: line) is appended after her text and marked as
mechanics, not instructions. The assembled brief is saved to
val-v2-2q/brief.txt.

Packet per her TOOLS list: the question and choices; the surmised
domain and skill; Sol's transcript with the tentative rating
mechanically stripped (vera.strip_sol_rating); the Sol-Vera back and
forth (none for these two items, stated as none per her Vera
paragraph); Snap's scramble and surmised topic; the heuristics list
(in her brief); three labeled comps, one per band, for the surmised
skill; the reference Overview plus the surmised skill's section from
files/difficulty-reference-by-domain-and-skill.md; and Lydia's
coverage card for the skill plus her General card from
files/coverage-and-heuristics-lydia.md. No checker's ruling (her v2
text: Vera produces no report for Val). No token traces (not in her
v2 tools list).

Usage: val_v2.py run [n...]   (default 3 8)
"""
import json
import os
import re
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import val as val_mod
import vera as vera_mod

GOAL = os.path.dirname(os.path.dirname(BASE))
PASTE = f"{BASE}/val-10/instructions-v2-lydia-paste-2026-11-02.txt"
REFERENCE = f"{GOAL}/files/difficulty-reference-by-domain-and-skill.md"
COVERAGE = f"{GOAL}/files/coverage-and-heuristics-lydia.md"
OUT_DIR = f"{BASE}/val-v2-2q"
MAX_COMPS = 3
MAX_CONTINUATIONS = 2

OLD_BLOCK_START = "You need to develop a difficulty rating at this point"
OLD_BLOCK_END = "instead of in isolation."
NEW_BLOCK = (
    "You need to develop a difficulty rating at this point, but only "
    "after you've gone through the prior steps.\n"
    "Because you start from the assumption that the question is Hard, "
    "any move downward must be earned by comparison against the "
    "spectrum:\n"
    "To call it Hard, find a similar Hard question from the question "
    "bank, and find a Medium question that this question is harder "
    "than. Make the case for both.\n"
    "To call it Medium, find a similar Medium question from the "
    "question bank, and place this question relative to an Easy "
    "question it is harder than and a Hard question it is easier "
    "than. Make an explicit case for why it sits between them.\n"
    "To call it Easy, find a similar Easy question from the question "
    "bank, and find a Medium question that this question is easier "
    "than. Make the case for both.")

MECHANICS = (
    "\n\nRUNNER MECHANICS (how to talk to the runner; these are "
    "plumbing, not instructions)\n"
    "To ask for more comparison examples for a domain and skill, "
    "include a line `COMP: <Domain> | <Skill>` anywhere in your "
    "reply. The runner will bring new examples before you rule. "
    "When you have finished, end your reply with a final line in "
    "exactly this shape:\n"
    "RATING: <Easy, Medium, or Hard>")


def build_brief():
    text = open(PASTE).read()
    starts = [m.start() for m in re.finditer(
        re.escape(OLD_BLOCK_START), text)]
    assert len(starts) == 2, f"comparison block count: {len(starts)}"
    spans = []
    for s in starts:
        e = text.index(OLD_BLOCK_END, s) + len(OLD_BLOCK_END)
        spans.append((s, e))
    # remove the second occurrence first, then replace the first
    s2, e2 = spans[1]
    text = text[:s2] + text[e2:]
    s1, e1 = spans[0]
    text = text[:s1] + NEW_BLOCK + text[e1:]
    return text.rstrip() + MECHANICS + "\n"


def extract_section(md, heading):
    """Text from the line equal to `heading` up to (not including)
    the next heading of the same or higher level."""
    lines = md.split("\n")
    level = len(heading) - len(heading.lstrip("#"))
    out, on = [], False
    for ln in lines:
        if ln.strip() == heading:
            on = True
            out.append(ln)
            continue
        if on:
            m = re.match(r"^(#+)\s", ln)
            if m and len(m.group(1)) <= level:
                break
            out.append(ln)
    return "\n".join(out).strip()


def build_packet(n, item):
    sol_results = val_mod.load_json(val_mod.SOL_RESULTS)
    vera_results = val_mod.load_json(val_mod.VERA_RESULTS)
    snap_results = val_mod.load_json(val_mod.SNAP_RESULTS)
    sol_final = sol_results[str(n)]["solver"]
    vera_final = vera_results[str(n)]["vera"]
    snap_rec = snap_results[str(n)]
    sol_raw = vera_mod.sol_assistant_text(n)
    sol_view, strip_log = vera_mod.strip_sol_rating(sol_raw)
    comps_text, _pulled = vera_mod.fulfill_comp(
        vera_final["domain"], vera_final["skill"], item["id"])
    ref = open(REFERENCE).read()
    overview = extract_section(ref, "# Overview")
    skill_section = extract_section(ref, f"## Skill: {vera_final['skill']}")
    cov = open(COVERAGE).read()
    cov_skill = extract_section(cov, f"## {vera_final['skill']}")
    gen_head = next(ln for ln in cov.split("\n")
                    if ln.startswith("## General"))
    cov_general = extract_section(cov, gen_head)
    lines = []
    lines.append("Here is one SAT question to evaluate, with "
                 "everything assembled for you.")
    lines.append("")
    lines.append("THE QUESTION")
    lines.append(item["question"].strip())
    for L in "ABCD":
        if item["choices"].get(L):
            lines.append(f"{L}) {item['choices'][L]}")
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
    lines.append(cov_skill if cov_skill else "(no card for this skill)")
    lines.append("")
    lines.append("COVERAGE NOTES, GENERAL (all skills)")
    lines.append(cov_general)
    return "\n".join(lines), strip_log


RATING_RE = re.compile(r"RATING:\s*(Easy|Medium|Hard)", re.I)
COMP_RE = val_mod.COMP_RE


def run_item(n, item, brief):
    packet, strip_log = build_packet(n, item)
    messages = [{"role": "system", "content": brief},
                {"role": "user", "content": packet}]
    record = {"item_no": n, "id": item["id"], "model": val_mod.MODEL,
              "packet": packet, "strip_log": strip_log, "turns": [],
              "comp_pulls": [], "continuations": 0}
    comps_left = MAX_COMPS
    while True:
        try:
            resp = val_mod.call_api(messages)
        except Exception as e:
            record["error"] = f"{type(e).__name__}: {e}"
            break
        record["turns"].append(resp)
        content = ((resp.get("choices") or [{}])[0].get("message") or {}
                   ).get("content") or ""
        messages.append({"role": "assistant", "content": content})
        cm = COMP_RE.search(content)
        m = RATING_RE.search(content)
        if cm and comps_left > 0 and not m:
            comps_left -= 1
            reply, _p = vera_mod.fulfill_comp(cm.group(1), cm.group(2),
                                              item["id"])
            record["comp_pulls"].append({"domain": cm.group(1),
                                         "skill": cm.group(2)})
            messages.append({"role": "user", "content": reply})
            continue
        if m:
            record["rating"] = m.group(1).capitalize()
            record["final_text"] = content
            break
        if record["continuations"] < MAX_CONTINUATIONS:
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
    return record


def main():
    which = [int(x) for x in sys.argv[1:]] or [3, 8]
    os.makedirs(OUT_DIR, exist_ok=True)
    brief = build_brief()
    open(f"{OUT_DIR}/brief.txt", "w").write(brief)
    items = val_mod.load_json(val_mod.ITEMS)
    results = {}
    for n in which:
        item = items[n - 1]
        print(f"[{time.strftime('%H:%M:%S')}] item {n} ({item['id']}, "
              f"CB {item['cb_rating']}) running...", flush=True)
        rec = run_item(n, item, brief)
        json.dump(rec, open(f"{OUT_DIR}/item-{n}-transcript.json", "w"),
                  indent=1)
        results[str(n)] = {"id": rec["id"], "rating": rec.get("rating"),
                           "cb": item["cb_rating"],
                           "tokens": rec["tokens"],
                           "cost_usd": rec["cost_usd"],
                           "comp_pulls": rec["comp_pulls"],
                           "error": rec.get("error")}
        print(f"  -> {rec.get('rating')} (CB {item['cb_rating']}) | "
              f"${rec['cost_usd']} | pulls {len(rec['comp_pulls'])}",
              flush=True)
    json.dump(results, open(f"{OUT_DIR}/results.json", "w"), indent=1)
    print("total $", round(sum(r["cost_usd"] for r in results.values()), 4))


if __name__ == "__main__":
    main()
