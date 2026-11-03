#!/usr/bin/env python3
"""Solver v1 — the informed agent (first agent of Lydia's difficulty stack).

Built to Lydia's spec of 2026-11-01 (files/solver-spec-2026-11-01.md):

- One question per conversation. The solver is TOLD the problem (the fresh
  model's baseline failure) and EXPLICITLY told that background may only
  inform, never decide; Easy and Medium matter as much as Hard. It is then
  given the full baseline stats.
- It must work out loud and transcribe its process. Mistakes must be
  admitted and redone in the transcript. Every choice A-D gets a verdict
  (RIGHT or WRONG) with its reason. The verdicts must come out exactly
  1 right / 3 wrong; if they don't, it keeps working in the transcript.
  An educated guess is allowed only after reconsidering more than twice.
- After solving it outputs Domain, Skill, Rating and its final answer in
  a FINAL block.
- Bank lookup (v1 design choice): the solver may, as its own decision,
  reply with ONLY a line `LOOKUP: <Domain> | <Skill>` before giving
  verdicts. The runner fulfills it from the question bank with up to
  three real example items (one per difficulty band when available) with
  their College Board ratings and answers, excluding all test-only IDs
  and the item being solved. Function calling was not used: it is
  unverified on this API, and the line protocol keeps the full decision
  visible in the transcript. Max 3 lookups per item.

Transcripts are recorded raw (every API response, every turn). Nothing
is patched or cleaned up after the fact.

Usage:
  solver.py select            # pick smoke items -> smoke-001/items.json
  solver.py run [item_no...]  # run solver on smoke items
  solver.py report            # compile smoke-001/report.md
"""
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

BASE = os.path.dirname(os.path.abspath(__file__))
GOAL = os.path.dirname(os.path.dirname(BASE))
BLIND = f"{GOAL}/hidden_files/baseline-run/blind-rows.json"
SCORED = f"{GOAL}/hidden_files/baseline-run/scored-rows.json"
LABEL_SPACE = f"{GOAL}/hidden_files/baseline-run/batch-001/label-space.json"
SMOKE_DIR = f"{BASE}/smoke-001"
MODEL = "muse-wonder-1.0"
MAX_TOKENS = 16000
MAX_LOOKUPS = 3
MAX_CONTINUATIONS = 2
PRICE_IN, PRICE_OUT = 4.0, 20.0  # $ per 1M tokens, published pricing

# ---------------------------------------------------------------- items

def load_bank():
    blind = {r["id"]: r for r in json.load(open(BLIND))}
    scored = {r["id"]: r for r in json.load(open(SCORED))}
    return blind, scored


def load_exclusions():
    ids = set()
    for name in ("population-sample-full-excluded-ids.md",):
        text = open(f"{GOAL}/files/{name}").read()
        ids |= set(re.findall(r"^[0-9a-f]{8}$", text, re.M))
    return ids


def select_items():
    blind, scored = load_bank()
    excluded = load_exclusions()
    rng = random.Random(20261101)
    chosen = []
    for band in ("Easy", "Medium", "Hard"):
        pool = []
        for qid, s in scored.items():
            if qid in excluded or s["section"] != "Reading and Writing":
                continue
            if s["cb_rating"] != band:
                continue
            b = blind[qid]
            if "[Figure" in b["question"]:
                continue
            if not all(b["choices"].get(L) for L in "ABCD"):
                continue
            pool.append(qid)
        rng.shuffle(pool)
        for qid in pool[:2]:
            b, s = blind[qid], scored[qid]
            chosen.append({
                "id": qid, "question": b["question"], "choices": b["choices"],
                "cb_domain": s["cb_domain"], "cb_skill": s["cb_skill"],
                "cb_rating": s["cb_rating"], "cb_answer": s["cb_answer"],
            })
    os.makedirs(SMOKE_DIR, exist_ok=True)
    json.dump(chosen, open(f"{SMOKE_DIR}/items.json", "w"), indent=1)
    for i, it in enumerate(chosen, 1):
        print(f"item {i}: {it['id']}  CB {it['cb_rating']}  "
              f"{it['cb_domain']} / {it['cb_skill']}  answer {it['cb_answer']}")
    print(f"excluded test-only IDs honored: {len(excluded)}")


# ---------------------------------------------------------------- prompt

def build_system_prompt():
    space = json.load(open(LABEL_SPACE))["Reading and Writing"]
    lines = []
    lines.append(
        "You are the solver in a research project that is trying to "
        "reverse-engineer how the College Board rates SAT question "
        "difficulty (Easy, Medium, or Hard, for a typical student).")
    lines.append("")
    lines.append("THE PROBLEM YOU ARE INFORMED ABOUT")
    lines.append(
        "A fresh AI model, given SAT questions cold with no background, "
        "was tested on all 3,770 questions in the College Board's own "
        "question bank. Its answers were excellent (96.6% correct), and "
        "it named the right domain 97.6% of the time and the right skill "
        "93.3% of the time. But its difficulty ratings agreed with the "
        "College Board only 50.8% of the time (Cohen's kappa 0.256; "
        "quadratic weighted kappa 0.504; Spearman rho 0.643). Its errors "
        "leaned easier: on average it rated questions 0.47 difficulty "
        "bands below the College Board. It recognized 91.2% of Easy "
        "questions, but only 38.6% of Medium questions and 20.4% of Hard "
        "questions. It called 178 truly Hard questions Easy, and only 1 "
        "truly Easy question Hard.")
    lines.append("")
    lines.append(
        "CRITICAL: this background may only INFORM your judgment. It "
        "must never decide it. Do not push a rating upward to compensate "
        "for the old model's bias; that would just trade one bias for "
        "another. Correctly identifying an Easy question as Easy and a "
        "Medium question as Medium matters exactly as much as correctly "
        "identifying a Hard question as Hard. Judge the question in front "
        "of you on its own demands: what a typical student actually has "
        "to do, notice, understand, and avoid in order to answer it "
        "correctly.")
    lines.append("")
    lines.append("HOW YOU MUST WORK")
    lines.append(
        "1. Work out loud. Transcribe your full process as you go: how "
        "you read the question, what it is asking, how you solve it, how "
        "a typical student would approach it, and where a typical student "
        "could go wrong. Your transcript is data. Do not compress it into "
        "a summary.")
    lines.append(
        "2. If you catch yourself making a mistake at any point, say so "
        "plainly, go back, and redo that part. Admitting a mistake and "
        "repairing it is wanted; it is data, not failure.")
    lines.append(
        "3. After solving, judge EVERY answer choice in a section headed "
        "VERDICTS, one line per choice, in exactly this shape:")
    lines.append("A: RIGHT - why you hold that position")
    lines.append("B: WRONG - why you hold that position")
    lines.append("(and so on for C and D; use RIGHT or WRONG on each line)")
    lines.append(
        "4. Your verdicts must come out to exactly ONE right answer and "
        "THREE wrong answers. If they do not, keep working: re-read the "
        "question, re-examine the choices, reconsider. Record that "
        "struggle in your transcript and then give a fresh VERDICTS "
        "section. Only after you have gone back and reconsidered more "
        "than twice may you settle a stuck verdict with an educated "
        "guess, and if you guess, say plainly that you guessed.")
    lines.append(
        "5. Only when your verdicts stand at exactly 1 right and 3 "
        "wrong, finish with a block in exactly this shape:")
    lines.append("FINAL")
    lines.append("Answer: <the letter you judge right>")
    lines.append("Domain: <College Board domain>")
    lines.append("Skill: <College Board skill>")
    lines.append("Rating: <Easy, Medium, or Hard>")
    lines.append("")
    lines.append("DOMAINS AND SKILLS (Reading and Writing)")
    for dom, skills in space.items():
        lines.append(f"- {dom}: " + "; ".join(skills))
    lines.append("")
    lines.append("BANK LOOKUPS")
    lines.append(
        "You do not have the question bank in your memory, but you may "
        "consult it. If, before giving your verdicts, you want to see "
        "real bank examples of a domain and skill (shown with their "
        "College Board difficulty ratings and correct answers), reply "
        "with ONLY the following line and nothing else:")
    lines.append("LOOKUP: <Domain> | <Skill>")
    lines.append(
        f"You will receive up to three example questions, and then you "
        f"continue working in your next reply. You may look up at most "
        f"{MAX_LOOKUPS} times for one question. Consulting the bank is "
        f"your decision; you are not required to.")
    return "\n".join(lines)


def build_item_prompt(item):
    lines = ["Here is one SAT Reading and Writing question. Work on it "
             "following the instructions you were given.", "",
             item["question"].strip(), ""]
    for L in "ABCD":
        lines.append(f"{L}) {item['choices'][L]}")
    return "\n".join(lines)


# ---------------------------------------------------------------- lookups

def fulfill_lookup(domain, skill, current_id):
    """Return up to 3 bank examples (one per band) for domain/skill."""
    blind, scored = load_bank()
    excluded = load_exclusions()
    want_d, want_s = domain.strip().lower(), skill.strip().lower()
    by_band = {}
    exact = True
    for qid, s in scored.items():
        if qid in excluded or qid == current_id:
            continue
        if s["section"] != "Reading and Writing":
            continue
        if s["cb_domain"].lower() == want_d and s["cb_skill"].lower() == want_s:
            by_band.setdefault(s["cb_rating"], qid)
    if not by_band:
        exact = False
        for qid, s in scored.items():
            if qid in excluded or qid == current_id:
                continue
            if s["section"] != "Reading and Writing":
                continue
            if s["cb_domain"].lower() == want_d:
                by_band.setdefault(s["cb_rating"], qid)
    if not by_band:
        return (f"No bank examples found for domain '{domain}' and skill "
                f"'{skill}'. Continue without examples.")
    lines = [f"Bank examples requested: {domain} | {skill}"]
    if not exact:
        lines.append("(No items matched that exact domain and skill; "
                     "showing examples from the domain instead.)")
    for band in ("Easy", "Medium", "Hard"):
        qid = by_band.get(band)
        if not qid:
            continue
        b, s = blind[qid], scored[qid]
        lines.append("")
        lines.append(f"--- Example, College Board rating: {band} "
                     f"({s['cb_domain']} / {s['cb_skill']}) ---")
        lines.append(b["question"].strip()[:2000])
        for L in "ABCD":
            if b["choices"].get(L):
                lines.append(f"{L}) {b['choices'][L]}")
        lines.append(f"Correct answer: {s['cb_answer']}")
    lines.append("")
    lines.append("Now continue working on the original question.")
    return "\n".join(lines)


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


# ---------------------------------------------------------------- parsing

FINAL_RE = re.compile(
    r"FINAL\s*\n\s*Answer:\s*([A-D])\s*\n\s*Domain:\s*(.+?)\s*\n\s*"
    r"Skill:\s*(.+?)\s*\n\s*Rating:\s*(Easy|Medium|Hard)", re.I)
VERDICT_RES = {L: re.compile(rf"^\s*{L}\s*[:.)]\s*(RIGHT|WRONG)\b", re.I | re.M)
               for L in "ABCD"}
LOOKUP_RE = re.compile(r"^\s*LOOKUP:\s*(.+?)\s*\|\s*(.+?)\s*$", re.I)
STRUGGLE_MARKERS = ["mistake", "i was wrong", "let me redo", "go back",
                    "reconsider", "correction", "i made an error",
                    "on second thought", "wait,", "actually,"]


def parse_final(text):
    m = FINAL_RE.search(text or "")
    if not m:
        return None
    return {"answer": m.group(1).upper(), "domain": m.group(2).strip(),
            "skill": m.group(3).strip(), "rating": m.group(4).capitalize()}


def last_verdicts(text):
    """Verdicts from the LAST complete VERDICTS pass in the text."""
    found = {}
    for L, rx in VERDICT_RES.items():
        hits = rx.findall(text or "")
        if hits:
            found[L] = hits[-1].upper()
    return found


# ---------------------------------------------------------------- run

def run_item(n, item):
    system = build_system_prompt()
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": build_item_prompt(item)}]
    record = {"item_no": n, "id": item["id"], "model": MODEL,
              "system_prompt": system,
              "turns": [], "lookups": [], "continuations": 0}
    lookups_left = MAX_LOOKUPS
    while True:
        try:
            resp = call_api(messages)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            record["turns"].append({"http_error": e.code, "body": body})
            record["error"] = f"HTTP {e.code}"
            break
        except Exception as e:
            record["turns"].append({"error": f"{type(e).__name__}: {e}"})
            record["error"] = str(e)
            break
        record["turns"].append(resp)
        content = ((resp.get("choices") or [{}])[0].get("message") or {}
                   ).get("content") or ""
        messages.append({"role": "assistant", "content": content})
        lm = LOOKUP_RE.match(content.strip())
        if lm and lookups_left > 0 and not parse_final(content):
            lookups_left -= 1
            reply = fulfill_lookup(lm.group(1), lm.group(2), item["id"])
            record["lookups"].append({"domain": lm.group(1),
                                      "skill": lm.group(2),
                                      "fulfilled": reply[:200]})
            messages.append({"role": "user", "content": reply})
            continue
        if parse_final(content):
            break
        if record["continuations"] < MAX_CONTINUATIONS:
            record["continuations"] += 1
            messages.append({"role": "user", "content":
                "You have not finished with the FINAL block yet. Keep "
                "working on the same question, following all the "
                "instructions, and finish with the VERDICTS section and "
                "the FINAL block."})
            continue
        record["error"] = "no parseable FINAL block after continuations"
        break
    record["messages_final"] = messages
    return record


def run(which):
    items = json.load(open(f"{SMOKE_DIR}/items.json"))
    results_path = f"{SMOKE_DIR}/results.json"
    results = {}
    if os.path.exists(results_path):
        results = json.load(open(results_path))
    todo = which or [i for i in range(1, len(items) + 1)
                     if str(i) not in results]
    for n in todo:
        item = items[n - 1]
        print(f"[{time.strftime('%H:%M:%S')}] item {n} ({item['id']}, "
              f"CB {item['cb_rating']}) running...", flush=True)
        rec = run_item(n, item)
        json.dump(rec, open(f"{SMOKE_DIR}/item-{n}-transcript.json", "w"),
                  indent=1)
        results[str(n)] = summarize(rec)
        json.dump(results, open(results_path, "w"), indent=1)
        s = results[str(n)]
        print(f"  -> solver: {s['solver']} | verdicts {s['verdicts']} | "
              f"lookups {s['n_lookups']} | tokens {s['tokens']}",
              flush=True)


def summarize(rec):
    text = ""
    pt = ct = 0
    for t in rec["turns"]:
        if isinstance(t, dict) and "choices" in t:
            c = ((t.get("choices") or [{}])[0].get("message") or {}
                 ).get("content") or ""
            text += "\n" + c
            u = t.get("usage") or {}
            pt += u.get("prompt_tokens") or 0
            ct += u.get("completion_tokens") or 0
    low = text.lower()
    markers = {m: low.count(m) for m in STRUGGLE_MARKERS if low.count(m)}
    return {"id": rec["id"], "solver": parse_final(text),
            "verdicts": last_verdicts(text),
            "n_lookups": len(rec["lookups"]),
            "continuations": rec["continuations"],
            "struggle_markers": markers,
            "tokens": {"prompt": pt, "completion": ct},
            "cost_usd": round((pt * PRICE_IN + ct * PRICE_OUT) / 1e6, 4),
            "error": rec.get("error")}


# ---------------------------------------------------------------- report

def report():
    items = json.load(open(f"{SMOKE_DIR}/items.json"))
    results = json.load(open(f"{SMOKE_DIR}/results.json"))
    lines = ["# Solver v1 — smoke test 001", "",
             f"Date: {time.strftime('%Y-%m-%d')}  Model: {MODEL}  "
             "Items: 6 Reading & Writing (2 Easy / 2 Medium / 2 Hard by "
             "College Board label), drawn from the bank with all 140 "
             "test-only IDs (population sample 100 + curated 40) "
             "excluded. Selection seed 20261101.", ""]
    tot_pt = tot_ct = 0
    tot_cost = 0.0
    n_ans = n_dom = n_skill = n_rate = n_struct = 0
    for n, item in enumerate(items, 1):
        s = results.get(str(n))
        lines.append(f"## Item {n} — bank ID {item['id']}")
        lines.append(f"- CB: {item['cb_domain']} / {item['cb_skill']} / "
                     f"{item['cb_rating']} / answer {item['cb_answer']}")
        if not s:
            lines.append("- Solver: NOT RUN")
            lines.append("")
            continue
        sv = s["solver"]
        if sv:
            ok_a = sv["answer"] == item["cb_answer"]
            ok_d = sv["domain"].lower() == item["cb_domain"].lower()
            ok_s = sv["skill"].lower() == item["cb_skill"].lower()
            ok_r = sv["rating"] == item["cb_rating"]
            n_ans += ok_a; n_dom += ok_d; n_skill += ok_s; n_rate += ok_r
            lines.append(f"- Solver: {sv['domain']} / {sv['skill']} / "
                         f"{sv['rating']} / answer {sv['answer']}")
            lines.append(f"- Match: answer {'YES' if ok_a else 'NO'}, "
                         f"domain {'YES' if ok_d else 'NO'}, "
                         f"skill {'YES' if ok_s else 'NO'}, "
                         f"rating {'YES' if ok_r else 'NO'}")
        else:
            lines.append(f"- Solver: no FINAL block parsed "
                         f"(error: {s.get('error')})")
        v = s["verdicts"]
        rights = sum(1 for x in v.values() if x == "RIGHT")
        struct_ok = len(v) == 4 and rights == 1
        n_struct += struct_ok
        lines.append(f"- Verdict structure: {'HELD' if struct_ok else 'DID NOT HOLD'} "
                     f"(verdicts found: {v or 'none'}, {rights} RIGHT)")
        lines.append(f"- Admitted mistakes / restarts (heuristic marker "
                     f"scan of transcript): {s['struggle_markers'] or 'none detected'}")
        lines.append(f"- Bank lookups requested: {s['n_lookups']}; "
                     f"continuation prompts needed: {s['continuations']}")
        t = s["tokens"]
        tot_pt += t["prompt"]; tot_ct += t["completion"]
        tot_cost += s["cost_usd"]
        lines.append(f"- Tokens: {t['prompt']} prompt / {t['completion']} "
                     f"completion; est. cost ${s['cost_usd']:.2f}")
        lines.append("")
    lines.append("## Totals")
    lines.append(f"- Answer {n_ans}/6, domain {n_dom}/6, skill "
                 f"{n_skill}/6, rating {n_rate}/6 vs College Board")
    lines.append(f"- Verdict structure held on {n_struct}/6 items")
    lines.append(f"- Tokens: {tot_pt} prompt / {tot_ct} completion; "
                 f"estimated total cost ${tot_cost:.2f} at published "
                 f"pricing ($4 in / $20 out per 1M)")
    lines.append("")
    lines.append("Full raw transcripts: item-N-transcript.json in this "
                 "folder (every API response, unedited). Struggle-marker "
                 "counts are a keyword heuristic over the transcript, "
                 "not a hand audit.")
    out = "\n".join(lines) + "\n"
    open(f"{SMOKE_DIR}/report.md", "w").write(out)
    print(out)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "select":
        select_items()
    elif cmd == "run":
        run([int(x) for x in sys.argv[2:]])
    elif cmd == "report":
        report()
    else:
        print(__doc__)
