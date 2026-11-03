#!/usr/bin/env python3
"""Val v1 — the Evaluator (final agent of Lydia's difficulty stack).

Built to Lydia's spec v2 of 2026-11-02
(files/val-design-2026-11-02.md):

- Val is fresh per question. She receives everything Lydia would give
  her for a newly written question she wanted sorted and evaluated:
  the question; Sol's transcribed process with Sol's tentative rating
  MECHANICALLY REMOVED (vera.strip_sol_rating, logged per item); the
  surmised domain and skill (Sol's call); Easy, Medium, and Hard comps
  for that skill (always all three bands — a band-selected comp set
  would leak the rating); the Easy/Medium/Hard descriptors write-up;
  Snap's scramble, surmised topic, and heuristics; Vera's verified
  ruling and notes (carried over from the Nov 1 design); and Sol's and
  Vera's token counts as traces.
- She NEVER receives the actual domain, skill, or rating, and never
  Sol's surmised rating.
- Her standard: a question is hard if students are likely to get it
  wrong, not if it is difficult to work out. Her reference student is
  a typical 17-year-old, an AP student in pre-calculus.
- Her job: run her own judgment; support it by bracketing against the
  comps; answer the bias question (does the correct answer cut against
  a bias a typical 17-year-old might have).
- She may pull more comps with a `COMP: <Domain> | <Skill>` line
  anywhere in a reply (same protocol and anywhere-match fix as Vera's).

Usage:
  val.py packet [n]   # assemble item n's input packet, NO API call
  val.py run [n...]   # run Val on working-10 items
  val.py report       # compile val-10/report.md
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vera as vera_mod

BASE = os.path.dirname(os.path.abspath(__file__))
GOAL = os.path.dirname(os.path.dirname(BASE))
ITEMS = f"{BASE}/working-10/items.json"
SOL_RESULTS = f"{BASE}/working-10/results.json"
VERA_RESULTS = f"{BASE}/vera-10/results.json"
SNAP_RESULTS = f"{BASE}/snap-10/results.json"
DESCRIPTORS = f"{GOAL}/files/difficulty-descriptors-v2-ela.md"
OUT_DIR = f"{BASE}/val-10"
MODEL = "muse-wonder-1.0"
MAX_TOKENS = 16000
MAX_COMPS = 3
MAX_CONTINUATIONS = 2
PRICE_IN, PRICE_OUT = 4.0, 20.0

# ---------------------------------------------------------------- brief

def build_system_prompt():
    descriptors = open(DESCRIPTORS).read()
    lines = []
    lines.append(
        "You are Val, the evaluator in a research project that "
        "reverse-engineers how the College Board rates SAT question "
        "difficulty (Easy, Medium, or Hard). You make the final "
        "rating for one question. You are given everything the "
        "question's author would hand over for a newly written "
        "question she wanted sorted and evaluated: the question, "
        "another agent's transcribed solving process, the surmised "
        "domain and skill, example questions (comps) of that skill at "
        "all three difficulty bands, a write-up of what makes a "
        "question Easy, Medium, or Hard, a word scramble of the "
        "question with a first-glance topic guessed from it, and a "
        "checker's verified ruling. You are NOT given the question's "
        "official domain, skill, or rating, and you are NOT given the "
        "solving agent's tentative rating. Those are withheld on "
        "purpose.")
    lines.append("")
    lines.append("THE REFERENCE STUDENT")
    lines.append(
        "Judge for a typical 17-year-old, presumed to be an AP "
        "student in pre-calculus: a strong student, not a struggling "
        "one. The question you ask is never whether YOU found the "
        "question easy, medium, or hard. It is whether that student "
        "would get it right.")
    lines.append("")
    lines.append("THE STANDARD")
    lines.append(
        "A question is hard if students are likely to get it wrong, "
        "NOT if it is difficult to work out. Those are not always the "
        "same thing. A long, laborious question students reliably "
        "finish is not hard by this standard; a short question whose "
        "obvious answer is wrong is.")
    lines.append("")
    lines.append("BACKGROUND THAT INFORMS, NEVER DECIDES")
    lines.append(
        "A fresh AI model judging these questions cold agreed with "
        "the College Board's difficulty ratings only 50.8% of the "
        "time (kappa 0.256), and its errors leaned easier: it "
        "recognized 91.2% of Easy questions but only 20.4% of Hard "
        "ones. Hold this as knowledge about how judgment like yours "
        "tends to fail. It must not decide any single question.")
    lines.append("")
    lines.append("YOUR JOB")
    lines.append(
        "1. Run your own judgment and rate the question.")
    lines.append(
        "2. Support the rating by bracketing. Do not simply add up "
        "the logical deductions and inferences and call the tally a "
        "judgment; that is the failure mode you exist to avoid. "
        "Consider the process the solving actually took, as shown in "
        "the transcript in front of you. And consider the comps "
        "comparatively: if you call the question Medium, explain why "
        "it is harder than the Easy comp and easier than the Hard "
        "comp. The same comparative support applies at the other "
        "bands: an Easy call explains why it does not reach the "
        "Medium comp; a Hard call explains why it exceeds the Medium "
        "comp.")
    lines.append(
        "3. Answer the bias question explicitly: does the correct "
        "answer cut against a bias a typical 17-year-old might have? "
        "Example: a student carries an impression of Abe Lincoln as "
        "an abolitionist. If a passage is about Abe Lincoln "
        "admonishing abolitionists as a senator, the correct answer "
        "cuts against that typical heuristic, and that increases the "
        "difficulty. A bias challenge can also run the other way: a "
        "shortcut or surface quirk that makes the question easier "
        "than it looks.")
    lines.append("")
    lines.append("CONSIDERATIONS — take note of things like these")
    for c in [
        "Inverse displays: a graph of pH that asks about acidity "
        "(the graph goes up as the acidity goes down); altitude "
        "paired with temperature (one rises, the other falls). "
        "Presenting a quantity through its inverse raises difficulty.",
        "Dates presented out of chronological order.",
        "An inference or conclusion that is not straight deductive "
        "logic: more 'if it's not this, then we can presume it's not "
        "that' than 'if this, then that.' Elimination-style "
        "inference is more difficult.",
        "A strong distractor placed before the correct answer in "
        "the order of the choices.",
        "A subtle catch inside a question that seems easy. Example: "
        "parallel lines presented as a system of equations, never "
        "named as parallel. Students who got good grades have "
        "typically solved many systems of equations and expect a "
        "solution; parallel lines have none. The expectation itself "
        "is the trap.",
        "Wit, metaphor, or symbolism in the material: their "
        "presence increases difficulty.",
    ]:
        lines.append(f"- {c}")
    lines.append(
        "Calibration over the whole list: Easy and Medium questions "
        "still have these elements. A Hard question may have only "
        "one of them, but it is so counterintuitive that it "
        "dominates. The presence of an element is not the verdict; "
        "its degree is.")
    lines.append("")
    lines.append("MORE COMPS")
    lines.append(
        "If you want more example questions for a domain and skill, "
        "include a line `COMP: <Domain> | <Skill>` anywhere in your "
        "reply and the examples will be brought to you before you "
        f"rule. You may do this at most {MAX_COMPS} times for one "
        "question.")
    lines.append("")
    lines.append("YOUR RULING — finish with exactly this shape:")
    lines.append("RATING: <Easy, Medium, or Hard>")
    lines.append("SUPPORT: <why this band, considering the solving "
                 "process in front of you>")
    lines.append("BRACKET: <the comparative case against the comps>")
    lines.append("BIAS: <whether the correct answer cuts against a "
                 "typical student's bias, and what that bias is; or "
                 "that there is no bias challenge in this question>")
    lines.append("")
    lines.append("THE EASY / MEDIUM / HARD WRITE-UP")
    lines.append(descriptors)
    return "\n".join(lines)


# ---------------------------------------------------------------- packet

def load_json(path):
    return json.load(open(path))


def build_packet(n, item):
    sol_results = load_json(SOL_RESULTS)
    vera_results = load_json(VERA_RESULTS)
    snap_results = load_json(SNAP_RESULTS)
    sol_final = sol_results[str(n)]["solver"]
    vera_final = vera_results[str(n)]["vera"]
    snap_rec = snap_results[str(n)]
    sol_raw = vera_mod.sol_assistant_text(n)
    sol_view, strip_log = vera_mod.strip_sol_rating(sol_raw)
    comps_text, _pulled = vera_mod.fulfill_comp(
        vera_final["domain"], vera_final["skill"], item["id"])
    tok_s = sol_results[str(n)]["tokens"]
    tok_v = vera_results[str(n)]["tokens"]
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
    lines.append("SURMISED DOMAIN AND SKILL (the solver's call)")
    lines.append(f"Domain: {sol_final['domain']}")
    lines.append(f"Skill: {sol_final['skill']}")
    lines.append("")
    lines.append("THE SOLVER'S TRANSCRIBED PROCESS (its tentative "
                 "rating has been removed)")
    lines.append(sol_view)
    lines.append("")
    lines.append("THE CHECKER'S VERIFIED RULING")
    lines.append(f"Verified answer: {vera_final['answer']}")
    lines.append(f"Answer check: {vera_final['answer_check']}; wrong "
                 f"answers check: {vera_final['wrong_check']}")
    lines.append(f"Verified domain and skill: {vera_final['domain']} "
                 f"/ {vera_final['skill']} "
                 f"({vera_final['domain_skill_check']})")
    if vera_final.get("notes") and vera_final["notes"] != "none":
        lines.append(f"Checker notes: {vera_final['notes']}")
    lines.append("")
    lines.append("COMPS FOR THIS SKILL (one per difficulty band)")
    lines.append(comps_text)
    lines.append("")
    lines.append("THE WORD SCRAMBLE AND THE SURMISED TOPIC")
    lines.append(f"Scramble: {snap_rec['scramble']}")
    parsed = snap_rec.get("parsed") or {}
    if parsed.get("snap"):
        lines.append(f"Surmised topic: {parsed['snap']}")
        lines.append(f"Heuristics it might be trading on: "
                     f"{parsed['heuristics']}")
    else:
        lines.append(f"Snap flagged: {parsed.get('flag')}")
    lines.append("")
    lines.append("TRACES (token counts; evidence, not testimony)")
    lines.append(f"Solver: {tok_s['prompt']} prompt / "
                 f"{tok_s['completion']} completion")
    lines.append(f"Checker: {tok_v['prompt']} prompt / "
                 f"{tok_v['completion']} completion")
    return "\n".join(lines), strip_log


# ---------------------------------------------------------------- api

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def call_api(messages):
    payload = {"model": MODEL, "messages": messages,
               "max_tokens": MAX_TOKENS}
    request = urllib.request.Request(
        "https://api.meta.ai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    add_surrogate_to_request(request, "custom.meta-model-api",
                             allowed_hosts=["api.meta.ai"])
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=900) as response:
        return read_json_response(response)


RATING_RE = re.compile(r"RATING:\s*(Easy|Medium|Hard)", re.I)
BLOCK_RE = re.compile(
    r"RATING:\s*(Easy|Medium|Hard)\s*\n\s*SUPPORT:\s*(.+?)\s*\n\s*"
    r"BRACKET:\s*(.+?)\s*\n\s*BIAS:\s*(.+)", re.I | re.S)
COMP_RE = re.compile(r"COMP:\s*(.+?)\s*\|\s*(.+?)\s*$", re.I | re.M)


def parse_ruling(text):
    m = BLOCK_RE.search(text or "")
    if not m:
        r = RATING_RE.search(text or "")
        return {"rating": r.group(1).capitalize() if r else None,
                "support": None, "bracket": None, "bias": None}
    return {"rating": m.group(1).capitalize(),
            "support": m.group(2).strip(), "bracket": m.group(3).strip(),
            "bias": m.group(4).strip()}


def run_item(n, item):
    system = build_system_prompt()
    packet, strip_log = build_packet(n, item)
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": packet}]
    record = {"item_no": n, "id": item["id"], "model": MODEL,
              "system_prompt": system, "packet": packet,
              "strip_log": strip_log, "turns": [], "comp_pulls": [],
              "continuations": 0}
    comps_left = MAX_COMPS
    while True:
        try:
            resp = call_api(messages)
        except urllib.error.HTTPError as e:
            record["error"] = f"HTTP {e.code}: " + e.read().decode(
                "utf-8", "replace")[:300]
            break
        except Exception as e:
            record["error"] = f"{type(e).__name__}: {e}"
            break
        record["turns"].append(resp)
        content = ((resp.get("choices") or [{}])[0].get("message") or {}
                   ).get("content") or ""
        messages.append({"role": "assistant", "content": content})
        cm = COMP_RE.search(content)
        if cm and comps_left > 0 and not parse_ruling(content)["rating"]:
            comps_left -= 1
            reply, _p = vera_mod.fulfill_comp(cm.group(1), cm.group(2),
                                              item["id"])
            record["comp_pulls"].append({"domain": cm.group(1),
                                         "skill": cm.group(2)})
            messages.append({"role": "user", "content": reply})
            continue
        if parse_ruling(content)["rating"]:
            record["ruling"] = parse_ruling(content)
            break
        if record["continuations"] < MAX_CONTINUATIONS:
            record["continuations"] += 1
            messages.append({"role": "user", "content":
                "You have not finished with the ruling yet. Rule on "
                "the same question and finish with the RATING / "
                "SUPPORT / BRACKET / BIAS block."})
            continue
        record["error"] = "no parseable ruling after continuations"
        break
    pt = ct = 0
    for t in record["turns"]:
        if isinstance(t, dict) and "usage" in t:
            u = t["usage"] or {}
            pt += u.get("prompt_tokens") or 0
            ct += u.get("completion_tokens") or 0
    record["tokens"] = {"prompt": pt, "completion": ct}
    record["cost_usd"] = round((pt * PRICE_IN + ct * PRICE_OUT) / 1e6, 4)
    record["messages_final"] = messages
    return record


def run(which):
    items = load_json(ITEMS)
    os.makedirs(OUT_DIR, exist_ok=True)
    results_path = f"{OUT_DIR}/results.json"
    results = {}
    if os.path.exists(results_path):
        results = load_json(results_path)
    todo = which or [i for i in range(1, len(items) + 1)
                     if str(i) not in results]
    for n in todo:
        item = items[n - 1]
        print(f"[{time.strftime('%H:%M:%S')}] item {n} ({item['id']}, "
              f"CB {item['cb_rating']}) running...", flush=True)
        rec = run_item(n, item)
        json.dump(rec, open(f"{OUT_DIR}/item-{n}-transcript.json", "w"),
                  indent=1)
        results[str(n)] = {"id": rec["id"], "ruling": rec.get("ruling"),
                           "tokens": rec["tokens"],
                           "cost_usd": rec["cost_usd"],
                           "comp_pulls": rec["comp_pulls"],
                           "continuations": rec["continuations"],
                           "strip_log": rec["strip_log"],
                           "error": rec.get("error")}
        json.dump(results, open(results_path, "w"), indent=1)
        print(f"  -> {rec.get('ruling', {}).get('rating')} | tokens "
              f"{rec['tokens']} | ${rec['cost_usd']}", flush=True)


def packet(n):
    items = load_json(ITEMS)
    item = items[n - 1]
    text, strip_log = build_packet(n, item)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = f"{OUT_DIR}/item-{n}-packet.txt"
    open(path, "w").write(text)
    print(f"packet for item {n} ({item['id']}) -> {path}")
    print(f"chars: {len(text)}  strip_log: {strip_log}")


def report():
    items = load_json(ITEMS)
    results = load_json(f"{OUT_DIR}/results.json")
    lines = ["# Val v1 — working set of 10", "",
             f"Date: {time.strftime('%Y-%m-%d')}  Model: {MODEL}.", ""]
    tot = 0.0
    hits = 0
    for n, item in enumerate(items, 1):
        r = results.get(str(n))
        lines.append(f"## Item {n} — {item['id']}")
        lines.append(f"- CB: {item['cb_domain']} / {item['cb_skill']} "
                     f"/ {item['cb_rating']}")
        if not r:
            lines.append("- Val: NOT RUN")
        elif r.get("error"):
            lines.append(f"- Val: ERROR {r['error']}")
        else:
            ru = r["ruling"] or {}
            ok = ru.get("rating") == item["cb_rating"]
            hits += bool(ok)
            lines.append(f"- Val: {ru.get('rating')} "
                         f"({'MATCH' if ok else 'MISS'})")
            lines.append(f"- Support: {ru.get('support')}")
            lines.append(f"- Bracket: {ru.get('bracket')}")
            lines.append(f"- Bias: {ru.get('bias')}")
            lines.append(f"- Extra comp pulls: {len(r['comp_pulls'])}; "
                         f"cost ${r['cost_usd']:.4f}")
            tot += r["cost_usd"]
        lines.append("")
    lines.append(f"Rating match: {hits}/10. Total estimated cost: "
                 f"${tot:.4f}")
    out = "\n".join(lines) + "\n"
    open(f"{OUT_DIR}/report.md", "w").write(out)
    print(out)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "packet":
        packet(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    elif cmd == "run":
        run([int(x) for x in sys.argv[2:]])
    elif cmd == "report":
        report()
    else:
        print(__doc__)
