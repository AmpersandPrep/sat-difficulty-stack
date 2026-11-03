#!/usr/bin/env python3
"""Val with no comparison questions and no spectrum placement.

Lydia's direction, Nov 2, 2026, voice call: if Val is going to use
comparison examples as College Board anchors, one example per band is
not enough, and Lydia does not want to supply a large comp set. Remove
the comparison questions instead. Val still receives the reference
document's general and skill descriptions, including its examples, so
she can understand what Easy, Medium, and Hard mean. She rates from
the completed counterintuitive-element count and those descriptions.
She does not place the target question against supplied comparison
questions, does not make a comparison rating, and cannot pull comps.

This variant starts from Lydia's v2 brief and makes only the changes
needed for that architecture:
  * the Tools list names reference descriptions and examples instead
    of three labeled comparison examples, and the extra-pull sentence
    is removed;
  * the domain/skill step consults the reference descriptions and
    examples instead of pulling examples;
  * Lydia's approved two-anchor comparison block is replaced with a
    rating-from-the-count block;
  * the COUNT BEFORE YOU JUDGE block is retained, with clause 6
    rewritten as a direct count rating (zero elements = Easy, one =
    Medium, two or more distinct interacting elements = Hard), so no
    Hard-example showing can move the count rating;
  * the runner mechanics offer no COMP request and require a
    COUNT RATING line equal to the final RATING line.

Usage:
  run_val_no_comps.py --build-only   # write brief.txt and packet.txt
  run_val_no_comps.py                # also run fresh Val on 797
"""
import json
import os
import re
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import val as val_mod
import val_v2
import run_val_new

SRC = f"{BASE}/val-v2-2q/systems-797"
OUT = f"{SRC}/val-no-comps"
ITEM_ID = "797a81fb"

TOOLS_OLD = (
    "three labeled comparison examples for the surmised skill, one "
    "Easy, one Medium, and one Hard\n"
    "You may ask for more comparison examples for a domain and skill "
    "whenever the ones you have are not enough; asking again returns "
    "new examples, not the same ones.")
TOOLS_NEW = (
    "the reference document's descriptions of Easy, Medium, and Hard "
    "for the surmised skill, including examples that illustrate what "
    "each band looks like")

DOMAIN_STEP_OLD = (
    "Sol was only given predetermined examples. You, however, will "
    "keep pulling examples until you are certain. Also, you must "
    "consult the descriptions in the overview document.")
DOMAIN_STEP_NEW = (
    "Sol was only given predetermined examples. You must consult the "
    "descriptions and examples in the overview document until you "
    "are certain.")

RATING_BLOCK = (
    "You need to develop a difficulty rating at this point, but only "
    "after you've gone through the prior steps.\n"
    "Use the descriptions of Easy, Medium, and Hard, and the examples "
    "in the reference document, to understand what each band means. "
    "Your rating comes from the completed count of counterintuitive "
    "elements in this question and from the band definitions:\n"
    "A question is Hard if a high-scoring student is likely to miss "
    "it.\n"
    "A question is Medium if a middle-scoring student is likely to "
    "miss it.\n"
    "A question is Easy if most students will get it right, even "
    "those who struggle with Algebra and Geometry.")

COUNT_CLAUSE_OLD = (
    "**6. Floor.** Zero qualifying elements: Easy may be considered. "
    "One qualifying element: do not rate Easy. Two or more distinct, "
    "interacting elements: presume Hard; rate Medium only by "
    "showing, against the Hard comparison example, why this question "
    "sits below it.")
COUNT_CLAUSE_NEW = (
    "**6. Count rating.** Zero qualifying elements: the count rating "
    "is Easy. One qualifying element: the count rating is Medium. "
    "Two or more distinct, interacting elements: the count rating "
    "is Hard.")

FINAL_SECTION = """## RATING FROM THE COUNT

Record the count rating on its own line immediately before the final
rating:

COUNT RATING: <Easy, Medium, or Hard>

The final rating is the count rating."""

MECHANICS_NEW = (
    "\n\nRUNNER MECHANICS (these are plumbing, not instructions)\n"
    "When you have finished, include the COUNT RATING line described "
    "above and end your reply with a final line in exactly this "
    "shape:\n"
    "RATING: <Easy, Medium, or Hard>")

COUNT_RATING_RE = re.compile(
    r"(?m)^COUNT RATING:\s*(Easy|Medium|Hard)\s*$", re.I)
FINAL_RATING_RE = re.compile(
    r"(?m)^RATING:\s*(Easy|Medium|Hard)\s*$", re.I)


def build_brief():
    brief = val_v2.build_brief()
    assert TOOLS_OLD in brief, "tools text not found"
    brief = brief.replace(TOOLS_OLD, TOOLS_NEW, 1)
    assert DOMAIN_STEP_OLD in brief, "domain step text not found"
    brief = brief.replace(DOMAIN_STEP_OLD, DOMAIN_STEP_NEW, 1)
    assert val_v2.NEW_BLOCK in brief, "comparison block not found"
    brief = brief.replace(val_v2.NEW_BLOCK, RATING_BLOCK, 1)

    count_block = run_val_new.COUNT_BLOCK
    assert COUNT_CLAUSE_OLD in count_block, "count clause not found"
    count_block = count_block.replace(
        COUNT_CLAUSE_OLD, COUNT_CLAUSE_NEW, 1)

    assert val_v2.MECHANICS in brief, "mechanics text not found"
    brief = brief.replace(val_v2.MECHANICS, "", 1)
    return (brief.rstrip() + "\n\n" + count_block + "\n\n" +
            FINAL_SECTION + MECHANICS_NEW + "\n")


def build_packet():
    packet = open(f"{SRC}/val-packet.txt").read()
    start_marker = ("COMPARISON EXAMPLES FOR THE SURMISED SKILL "
                    "(one per difficulty band)")
    end_marker = "FROM THE OVERVIEW DOCUMENT: THE GENERAL OVERVIEW"
    assert start_marker in packet, "packet comp heading not found"
    assert end_marker in packet, "packet overview heading not found"
    start = packet.index(start_marker)
    end = packet.index(end_marker)
    return packet[:start].rstrip() + "\n\n" + packet[end:]


def build_outputs():
    os.makedirs(OUT, exist_ok=True)
    brief = build_brief()
    packet = build_packet()
    open(f"{OUT}/brief.txt", "w").write(brief)
    open(f"{OUT}/packet.txt", "w").write(packet)
    return brief, packet


def main():
    build_only = "--build-only" in sys.argv
    brief, packet = build_outputs()
    print(f"built {OUT}/brief.txt ({len(brief)} chars)")
    print(f"built {OUT}/packet.txt ({len(packet)} chars)")
    if build_only:
        return
    messages = [{"role": "system", "content": brief},
                {"role": "user", "content": packet}]
    record = {"item_no": 1, "id": ITEM_ID, "packet": packet,
              "turns": [], "continuations": 0}
    print(f"[{time.strftime('%H:%M:%S')}] Val with no comps "
          "running...", flush=True)
    while True:
        resp = val_mod.call_api(messages)
        record["turns"].append(resp)
        content = ((resp.get("choices") or [{}])[0].get("message") or {}
                   ).get("content") or ""
        messages.append({"role": "assistant", "content": content})
        fm = FINAL_RATING_RE.search(content)
        if fm:
            cr = COUNT_RATING_RE.search(content)
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
                    "RATING line. Complete the same evaluation and "
                    "include COUNT RATING: <Easy, Medium, or Hard> "
                    "immediately before the final RATING line. The "
                    "final rating is the count rating."})
                continue
            record["rating"] = fm.group(1).capitalize()
            record["final_text"] = content
            record["error"] = "final rating without a count rating"
            break
        if record["continuations"] < val_v2.MAX_CONTINUATIONS:
            record["continuations"] += 1
            messages.append({"role": "user", "content":
                "You have not finished yet. Complete your evaluation "
                "of the same question. Include COUNT RATING: <Easy, "
                "Medium, or Hard> immediately before the final line "
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
    json.dump(record, open(f"{OUT}/val-transcript.json", "w"), indent=1)
    print(f"Val (no comps): {record.get('rating')} (CB Hard) | "
          f"count {record.get('count_rating')} | rule followed "
          f"{record.get('rule_followed')} | ${record['cost_usd']}",
          flush=True)


if __name__ == "__main__":
    main()
