#!/usr/bin/env python3
"""Vera — the Checker (second agent of Lydia's difficulty stack).

Built to Lydia's approved design of 2026-11-01
(files/vera-design-2026-11-01.md):

- Vera receives the question and Sol's transcript with Sol's tentative
  rating REMOVED (see strip_sol_rating — the FINAL block's Rating line
  is blanked and Sol's difficulty-assignment sentences in the prose are
  mechanically redacted; every redaction is logged in the record).
- Vera performs three checks, working out loud:
  1. Re-derive the answer herself; confirm Sol's marked-right choice.
  2. Confirm each choice Sol marked wrong actually fails, and why;
     flag any "wrong" choice that is defensible.
  3. Domain/skill: Vera pulls comps FIRST from the domain/skill Sol
     named (line protocol, `COMP: <Domain> | <Skill>`, fulfilled by
     this runner from the accessible bank with College Board labels,
     one example per band, the 100 test questions and the current item
     excluded). Both sections are served. If the fit is poor she may
     pull comps for a neighboring skill. Max 3 pulls per item.
- Disputes: if Vera disagrees with Sol on the answer or on domain or
  skill, she ends with a DISPUTE block instead of a ruling. The runner
  then gives Sol one response turn (Sol's own brief, same model) and
  hands it back to Vera, who rules. Vera's ruling stands.
- Vera outputs a VERA FINAL block: verified (or corrected) answer,
  verified domain and skill, the three checks' outcomes, and notes.

Transcripts are recorded raw (every API response, every turn). Nothing
is patched or cleaned up after the fact.

Usage:
  vera.py run [item_no...]   # run Vera on the working-10 items
  vera.py report             # compile vera-10/report.md
"""
import json
import os
import re
import sys
import time
import urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
GOAL = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)
import solver as sol  # reuse Sol's API client, bank loaders, brief

WORK_DIR = f"{GOAL}/hidden_files/solver-run/working-10"
OUT_DIR = f"{BASE}/vera-10"
MODEL = sol.MODEL
MAX_TOKENS = sol.MAX_TOKENS
MAX_COMPS = 3
MAX_CONTINUATIONS = 2
PRICE_IN, PRICE_OUT = sol.PRICE_IN, sol.PRICE_OUT
LABEL_SPACE = f"{GOAL}/hidden_files/baseline-run/batch-001/label-space.json"

# ---------------------------------------------------------------- items

def load_items():
    return json.load(open(f"{WORK_DIR}/items.json"))


def load_sol_results():
    return json.load(open(f"{WORK_DIR}/results.json"))


def sol_assistant_text(n):
    """Sol's own words for item n: its assistant turns, in order."""
    rec = json.load(open(f"{WORK_DIR}/item-{n}-transcript.json"))
    parts = [m["content"] for m in rec["messages_final"]
             if m["role"] == "assistant"]
    return "\n\n".join(parts)


# ------------------------------------------------------- rating stripping

_BAND = r"(?:Easy|Medium|Hard)"
_CUES = (r"rat(?:e|ed|ing)\b|difficult|demand|level|band|placing|"
         r"judg|calibrat|success rate")
_RATING_SENT_RE = re.compile(
    rf"(?i)(?=.*\b{_BAND}\b)(?=.*(?:{_CUES}))")
_BARE_SENT_RE = re.compile(
    rf"(?i)^\s*(?:that|this|it)\s+is\s+an?\s+{_BAND}\b")
# First-person band assertions Sol makes in prose ("I think this is
# Easy", "I would call it Easy", "this is Boundaries Easy" after an
# "I feel..." lead) — same sentence, an "I" and a band word.
_FIRST_PERSON_BAND_RE = re.compile(
    rf"(?i)\bI\b[^.!?]{{0,100}}?\b{_BAND}\b")


def strip_sol_rating(text):
    """Mechanically remove Sol's tentative rating from its transcript.

    Pass 1: blank the labeled field wherever it appears
    (`Rating: Easy` -> `Rating: [removed]`), including in the FINAL
    block. Pass 2: sentence-level redaction — any sentence that both
    names a difficulty band and carries a difficulty-assignment cue is
    replaced with [rating remark removed]. Returns (text, log) where
    log records exactly what was removed.
    """
    log = {"rating_fields_blanked": 0, "sentences_redacted": []}
    text, n = re.subn(rf"(?i)\bRating:\s*{_BAND}\b",
                      "Rating: [removed]", text)
    log["rating_fields_blanked"] = n
    out_lines = []
    for line in text.split("\n"):
        sents = re.split(r"(?<=[.!?])\s+", line)
        new_sents = []
        for s in sents:
            if (_RATING_SENT_RE.search(s) or _BARE_SENT_RE.search(s)
                    or _FIRST_PERSON_BAND_RE.search(s)):
                log["sentences_redacted"].append(s.strip()[:200])
                new_sents.append("[rating remark removed]")
            else:
                new_sents.append(s)
        out_lines.append(" ".join(new_sents))
    return "\n".join(out_lines), log


# ---------------------------------------------------------------- prompt

def build_vera_system_prompt():
    space = json.load(open(LABEL_SPACE))
    lines = []
    lines.append(
        "You are Vera, the checker in a research project that is "
        "reverse-engineering how the College Board classifies SAT "
        "questions. Another agent, Sol, has already solved the question "
        "you will be given and named its answer, domain, and skill. Your "
        "job is to check that work before anything downstream trusts it.")
    lines.append("")
    lines.append("WHY YOU EXIST")
    lines.append(
        "Everything downstream trusts the answer and the domain/skill. "
        "If those are wrong, the comparison examples mislead and any "
        "later judgment is built on sand. A fresh AI model's answers "
        "were 96.6% right, its domains 97.6% right, its skills 93.3% "
        "right — good, not perfect. The misses are exactly where a "
        "checker earns her keep.")
    lines.append("")
    lines.append("WHAT YOU RECEIVE")
    lines.append(
        "The question, and Sol's transcript: its worked process, its "
        "verdict on every choice with reasons, and its answer, domain, "
        "and skill. Sol also made a tentative difficulty rating; it has "
        "been removed from what you are shown, deliberately. You do not "
        "rule on difficulty. Do not guess at the removed rating, do not "
        "reinstate it, and do not let difficulty thinking into your "
        "checks.")
    lines.append("")
    lines.append("YOUR THREE CHECKS — work out loud, in this order, "
                 "under these headings:")
    lines.append("CHECK 1 — THE RIGHT ANSWER IS RIGHT")
    lines.append(
        "Solve the question yourself, independently, before crediting "
        "Sol's work. Then state whether the choice Sol marked right "
        "actually satisfies the question. If your own answer differs "
        "from Sol's, that is a dispute (see below).")
    lines.append("CHECK 2 — THE WRONG ANSWERS ARE WRONG")
    lines.append(
        "For every choice Sol marked wrong, confirm that it genuinely "
        "fails, and say why. If any choice Sol marked wrong turns out "
        "to be defensible or actually right, FLAG it explicitly: that "
        "changes what the question is. For a grid-in question with no "
        "choices, this check becomes: Sol's value is the unique correct "
        "value (equivalent forms are the same value).")
    lines.append("CHECK 3 — DOMAIN AND SKILL")
    lines.append(
        "Sol's named domain and skill tell you where to look first — a "
        "pointer, not a claim you defer to. Pull comparison examples "
        "(comps) from the question bank, first for the domain and skill "
        "Sol named, and judge whether this question sits right among "
        "them. If the fit is poor, pull comps for a neighboring skill "
        "and compare. Then confirm Sol's domain/skill or reassign them.")
    lines.append("")
    lines.append("PULLING COMPS")
    lines.append(
        "To pull comps, reply with ONLY the following line and nothing "
        "else:")
    lines.append("COMP: <Domain> | <Skill>")
    lines.append(
        "You will receive up to three real bank examples of that domain "
        "and skill (one per College Board difficulty band when "
        "available), each with its College Board domain, skill, rating, "
        "and correct answer, and then you continue. You may pull comps "
        f"at most {MAX_COMPS} times for one question.")
    lines.append(
        "You need the comps. Ask for them on every question before "
        "you rule on domain and skill. Keep asking. The only time you "
        "will not be given comps is if you already pulled comps for "
        "that same domain and skill on a previous question; then work "
        "from the ones you already have.")
    lines.append("")
    lines.append("DOMAINS AND SKILLS (both sections)")
    for sec, doms in space.items():
        lines.append(f"{sec}:")
        for dom, skills in doms.items():
            lines.append(f"- {dom}: " + "; ".join(skills))
    lines.append("")
    lines.append("DISPUTES")
    lines.append(
        "If, after your checks, you disagree with Sol on the answer, "
        "or on the domain, or on the skill, do NOT give a final ruling "
        "yet. End your reply with a block in exactly this shape (one "
        "Field line per disputed field):")
    lines.append("DISPUTE")
    lines.append("Field: Answer")
    lines.append("Sol said: <what Sol concluded>")
    lines.append("Vera says: <what you conclude>")
    lines.append("Reason: <why, grounded in the question and the comps>")
    lines.append(
        "Sol will be given one response — its reason, in its own words "
        "— and then you rule. Your ruling stands; Sol's reason is "
        "recorded alongside it either way.")
    lines.append("")
    lines.append("YOUR FINAL RULING")
    lines.append(
        "When your checks are complete (and any dispute has been "
        "answered), finish with a block in exactly this shape:")
    lines.append("VERA FINAL")
    lines.append("Answer: <the verified answer letter>")
    lines.append("Domain: <verified College Board domain>")
    lines.append("Skill: <verified College Board skill>")
    lines.append("Answer check: CONFIRMED or CORRECTED")
    lines.append("Wrong-answers check: ALL CONFIRMED WRONG or FLAG <letter>")
    lines.append("Domain-skill check: CONFIRMED or REASSIGNED")
    lines.append("Notes: <anything disputed and how it resolved, "
                 "anything odd about the question, or 'none'>")
    return "\n".join(lines)


def build_vera_item_prompt(item, sol_view, sol_final):
    lines = [f"Here is one SAT {item['section']} question to check, "
             "with Sol's work on it.", "", item["question"].strip(), ""]
    for L in "ABCD":
        if item["choices"].get(L):
            lines.append(f"{L}) {item['choices'][L]}")
    lines.append("")
    lines.append(f"Sol's conclusions: Answer {sol_final['answer']}; "
                 f"Domain {sol_final['domain']}; "
                 f"Skill {sol_final['skill']}.")
    lines.append("")
    lines.append("--- SOL'S TRANSCRIPT (its difficulty rating has been "
                 "removed) ---")
    lines.append(sol_view)
    lines.append("--- END OF SOL'S TRANSCRIPT ---")
    lines.append("")
    lines.append("Now perform your three checks.")
    return "\n".join(lines)


# ---------------------------------------------------------------- comps

def fulfill_comp(domain, skill, current_id):
    """Up to 3 bank examples (one per band) for domain/skill.

    Both sections are served. The 100 test questions and the current
    item are excluded."""
    blind, scored = sol.load_bank()
    excluded = sol.load_exclusions()
    want_d, want_s = domain.strip().lower(), skill.strip().lower()
    by_band = {}
    exact = True
    for qid, s in scored.items():
        if qid in excluded or qid == current_id:
            continue
        if s["cb_domain"].lower() == want_d and s["cb_skill"].lower() == want_s:
            by_band.setdefault(s["cb_rating"], qid)
    if not by_band:
        exact = False
        for qid, s in scored.items():
            if qid in excluded or qid == current_id:
                continue
            if s["cb_domain"].lower() == want_d:
                by_band.setdefault(s["cb_rating"], qid)
    if not by_band:
        return (f"No bank examples found for domain '{domain}' and "
                f"skill '{skill}'. Continue without examples."), []
    lines = [f"Bank examples requested: {domain} | {skill}"]
    if not exact:
        lines.append("(No items matched that exact domain and skill; "
                     "showing examples from the domain instead.)")
    pulled = []
    for band in ("Easy", "Medium", "Hard"):
        qid = by_band.get(band)
        if not qid:
            continue
        b, s = blind[qid], scored[qid]
        pulled.append({"id": qid, "band": band,
                       "cb_domain": s["cb_domain"],
                       "cb_skill": s["cb_skill"],
                       "cb_answer": s["cb_answer"], "exact": exact})
        lines.append("")
        lines.append(f"--- Example, College Board rating: {band} "
                     f"({s['cb_domain']} / {s['cb_skill']}) ---")
        lines.append(b["question"].strip()[:2000])
        for L in "ABCD":
            if b["choices"].get(L):
                lines.append(f"{L}) {b['choices'][L]}")
        lines.append(f"Correct answer: {s['cb_answer']}")
    lines.append("")
    lines.append("Now continue checking the original question.")
    return "\n".join(lines), pulled


# ---------------------------------------------------------------- parsing

VERA_FINAL_RE = re.compile(
    r"VERA FINAL\s*\n\s*Answer:\s*([A-D])\s*\n\s*Domain:\s*(.+?)\s*\n\s*"
    r"Skill:\s*(.+?)\s*\n\s*Answer check:\s*(CONFIRMED|CORRECTED)\s*\n\s*"
    r"Wrong-answers check:\s*(ALL CONFIRMED WRONG|FLAG\s+([A-D]))\s*\n\s*"
    r"Domain-skill check:\s*(CONFIRMED|REASSIGNED)"
    r"(?:\s*\n\s*Notes:\s*(.*?))?(?:\n\s*\n|\Z)", re.I | re.S)
DISPUTE_RE = re.compile(r"^\s*DISPUTE\s*$.*?(?=\n\s*\n|\Z)", re.I | re.M | re.S)
COMP_RE = re.compile(r"^\s*COMP:\s*(.+?)\s*\|\s*(.+?)\s*$", re.I | re.M)


def parse_vera_final(text):
    m = VERA_FINAL_RE.search(text or "")
    if not m:
        return None
    return {"answer": m.group(1).upper(), "domain": m.group(2).strip(),
            "skill": m.group(3).strip(),
            "answer_check": m.group(4).upper(),
            "wrong_check": ("ALL CONFIRMED WRONG" if m.group(6) is None
                            else f"FLAG {m.group(6).upper()}"),
            "domain_skill_check": m.group(7).upper(),
            "notes": (m.group(8) or "").strip()}


def find_dispute(text):
    m = DISPUTE_RE.search(text or "")
    return m.group(0).strip() if m else None


# ---------------------------------------------------------------- dispute

def sol_rebuttal(item, sol_text_raw, sol_final, dispute_text):
    """Give Sol one response turn to Vera's dispute. Returns
    (raw_response, content)."""
    system = sol.build_system_prompt()
    lines = ["You previously solved the SAT question below. Your own "
             "work on it follows, then an objection from Vera, the "
             "checker.", "", item["question"].strip(), ""]
    for L in "ABCD":
        if item["choices"].get(L):
            lines.append(f"{L}) {item['choices'][L]}")
    lines.append("")
    lines.append("--- YOUR EARLIER WORK ---")
    lines.append(sol_text_raw)
    lines.append("--- END OF YOUR EARLIER WORK ---")
    lines.append("")
    lines.append("Vera, the checker, disputes part of your work:")
    lines.append(dispute_text)
    lines.append("")
    lines.append(
        "Respond to the checker's objection with your reason, in your "
        "own words. If the objection is right, concede plainly. End "
        "with one line in this shape: POSITION: Answer <letter> | "
        "Domain <domain> | Skill <skill>")
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": "\n".join(lines)}]
    resp = sol.call_api(messages)
    content = ((resp.get("choices") or [{}])[0].get("message") or {}
               ).get("content") or ""
    return resp, content


# ---------------------------------------------------------------- run

def run_item(n, item, sol_final):
    system = build_vera_system_prompt()
    sol_raw = sol_assistant_text(n)
    sol_view, strip_log = strip_sol_rating(sol_raw)
    messages = [{"role": "system", "content": system},
                {"role": "user", "content":
                 build_vera_item_prompt(item, sol_view, sol_final)}]
    record = {"item_no": n, "id": item["id"], "model": MODEL,
              "system_prompt": system, "strip_log": strip_log,
              "turns": [], "comps": [], "continuations": 0,
              "dispute": None}
    comps_left = MAX_COMPS
    rebutted = False
    comp_nudged = False
    while True:
        try:
            resp = sol.call_api(messages)
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
        cm = COMP_RE.search(content)
        if cm and comps_left > 0 and not parse_vera_final(content):
            comps_left -= 1
            reply, pulled = fulfill_comp(cm.group(1), cm.group(2),
                                         item["id"])
            record["comps"].append({"domain": cm.group(1),
                                    "skill": cm.group(2),
                                    "examples": pulled,
                                    "fulfilled": reply[:200]})
            messages.append({"role": "user", "content": reply})
            continue
        if parse_vera_final(content):
            if not record["comps"] and not comp_nudged:
                comp_nudged = True
                record["comp_nudge"] = True
                messages.append({"role": "user", "content":
                    "You have not pulled comps for this question. "
                    "Pull them before ruling."})
                continue
            break
        dispute = find_dispute(content)
        if dispute and not rebutted:
            rebutted = True
            try:
                rresp, rcontent = sol_rebuttal(item, sol_raw, sol_final,
                                               dispute)
                record["dispute"] = {
                    "vera_dispute": dispute,
                    "sol_rebuttal_raw": rresp,
                    "sol_rebuttal": rcontent}
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")[:300]
                record["dispute"] = {
                    "vera_dispute": dispute,
                    "sol_rebuttal_raw": {"http_error": e.code,
                                         "body": body},
                    "sol_rebuttal": ""}
                record["error"] = f"rebuttal HTTP {e.code}"
                break
            except Exception as e:
                record["dispute"] = {
                    "vera_dispute": dispute,
                    "sol_rebuttal_raw": {"error": str(e)},
                    "sol_rebuttal": ""}
                record["error"] = f"rebuttal failed: {e}"
                break
            messages.append({"role": "user", "content":
                "Sol's response to your dispute:\n\n" + rcontent +
                "\n\nNow rule. Give your VERA FINAL block."})
            continue
        if record["continuations"] < MAX_CONTINUATIONS:
            record["continuations"] += 1
            messages.append({"role": "user", "content":
                "You have not finished with the VERA FINAL block yet. "
                "Complete your three checks on the same question and "
                "finish with the VERA FINAL block (or a DISPUTE block "
                "if you disagree with Sol on the answer or on domain "
                "or skill)."})
            continue
        record["error"] = "no parseable VERA FINAL block after continuations"
        break
    record["messages_final"] = messages
    return record


def usage_of(resp):
    if isinstance(resp, dict) and "choices" in resp:
        u = resp.get("usage") or {}
        return (u.get("prompt_tokens") or 0,
                u.get("completion_tokens") or 0)
    return 0, 0


def summarize(rec):
    text = ""
    pt = ct = 0
    for t in rec["turns"]:
        if isinstance(t, dict) and "choices" in t:
            c = ((t.get("choices") or [{}])[0].get("message") or {}
                 ).get("content") or ""
            text += "\n" + c
            a, b = usage_of(t)
            pt += a; ct += b
    rpt = rct = 0
    if rec.get("dispute"):
        a, b = usage_of(rec["dispute"].get("sol_rebuttal_raw") or {})
        rpt, rct = a, b
    return {"id": rec["id"], "vera": parse_vera_final(text),
            "n_comps": len(rec["comps"]),
            "comps": [{"domain": c["domain"], "skill": c["skill"],
                       "examples": c["examples"]} for c in rec["comps"]],
            "disputed": bool(rec.get("dispute")),
            "dispute_field_text": (rec["dispute"]["vera_dispute"]
                                   if rec.get("dispute") else None),
            "continuations": rec["continuations"],
            "strip_log": rec["strip_log"],
            "tokens": {"prompt": pt, "completion": ct},
            "rebuttal_tokens": {"prompt": rpt, "completion": rct},
            "cost_usd": round(((pt + rpt) * PRICE_IN +
                               (ct + rct) * PRICE_OUT) / 1e6, 4),
            "error": rec.get("error")}


def run(which):
    items = load_items()
    sol_results = load_sol_results()
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(items, open(f"{OUT_DIR}/items.json", "w"), indent=1)
    results_path = f"{OUT_DIR}/results.json"
    results = {}
    if os.path.exists(results_path):
        results = json.load(open(results_path))
    todo = which or [i for i in range(1, len(items) + 1)
                     if str(i) not in results]
    for n in todo:
        item = items[n - 1]
        sol_final = sol_results[str(n)]["solver"]
        print(f"[{time.strftime('%H:%M:%S')}] item {n} ({item['id']}, "
              f"CB {item['cb_rating']}) Vera running...", flush=True)
        rec = run_item(n, item, sol_final)
        json.dump(rec, open(f"{OUT_DIR}/item-{n}-transcript.json", "w"),
                  indent=1)
        results[str(n)] = summarize(rec)
        json.dump(results, open(results_path, "w"), indent=1)
        s = results[str(n)]
        print(f"  -> vera: {s['vera']} | comps {s['n_comps']} | "
              f"disputed {s['disputed']} | tokens {s['tokens']} + "
              f"rebuttal {s['rebuttal_tokens']}", flush=True)


# ---------------------------------------------------------------- report

def report():
    items = load_items()
    sol_results = load_sol_results()
    results = json.load(open(f"{OUT_DIR}/results.json"))
    lines = ["# Vera v1 — the Checker on the working set of 10", "",
             f"Date: {time.strftime('%Y-%m-%d')}  Model: {MODEL}  "
             "Items: the same 10 working-set questions Sol ran "
             "(hidden_files/solver-run/working-10). Vera received each "
             "question plus Sol's transcript with Sol's tentative "
             "rating mechanically removed (FINAL-block Rating field "
             "blanked; difficulty-assignment sentences redacted — counts "
             "per item below). Comps were pulled from the accessible "
             "bank with the 100 test questions and the current item "
             "excluded; both sections served.", ""]
    tot_pt = tot_ct = tot_rpt = tot_rct = 0
    tot_cost = 0.0
    n_ans_agree = n_dom_agree = n_skill_agree = 0
    n_checked = 0
    for n, item in enumerate(items, 1):
        s = results.get(str(n))
        sf = sol_results[str(n)]["solver"]
        lines.append(f"## Item {n} — bank ID {item['id']} "
                     f"({item['section']})")
        lines.append(f"- CB: {item['cb_domain']} / {item['cb_skill']} / "
                     f"{item['cb_rating']} / answer {item['cb_answer']}")
        lines.append(f"- Sol: {sf['domain']} / {sf['skill']} / "
                     f"answer {sf['answer']} (Sol rating: {sf['rating']})")
        if not s:
            lines.append("- Vera: NOT RUN")
            lines.append("")
            continue
        v = s["vera"]
        sl = s["strip_log"]
        lines.append(f"- Stripped from Sol's transcript for Vera: "
                     f"{sl['rating_fields_blanked']} Rating field(s) "
                     f"blanked, {len(sl['sentences_redacted'])} "
                     f"sentence(s) redacted")
        if v:
            n_checked += 1
            n_ans_agree += v["answer"] == item["cb_answer"]
            n_dom_agree += v["domain"].lower() == item["cb_domain"].lower()
            n_skill_agree += v["skill"].lower() == item["cb_skill"].lower()
            lines.append(f"- Vera verified: {v['domain']} / {v['skill']} "
                         f"/ answer {v['answer']}")
            lines.append(f"- Check 1 (right answer right): "
                         f"{v['answer_check']} — Vera's answer "
                         f"{v['answer']} vs CB {item['cb_answer']} "
                         f"({'MATCH' if v['answer'] == item['cb_answer'] else 'MISMATCH'})")
            lines.append(f"- Check 2 (wrong answers wrong): "
                         f"{v['wrong_check']}")
            lines.append(f"- Check 3 (domain/skill): "
                         f"{v['domain_skill_check']} — Vera "
                         f"{v['domain']} / {v['skill']} vs CB "
                         f"{item['cb_domain']} / {item['cb_skill']}")
            if v["notes"]:
                lines.append(f"- Vera notes: {v['notes']}")
        else:
            lines.append(f"- Vera: no VERA FINAL block parsed "
                         f"(error: {s.get('error')})")
        if s["comps"]:
            for c in s["comps"]:
                ex = ", ".join(f"{e['id']} ({e['band']})"
                               for e in c["examples"]) or "none found"
                lines.append(f"- Comps pulled for {c['domain']} | "
                             f"{c['skill']}: {ex}")
        else:
            lines.append("- Comps pulled: none")
        lines.append(f"- Dispute raised: "
                     f"{'YES' if s['disputed'] else 'no'}")
        if s["disputed"]:
            lines.append(f"  - Vera's dispute: "
                         f"{(s['dispute_field_text'] or '')[:400]}")
            if v:
                lines.append(f"  - Ruling (Vera's, stands): answer "
                             f"{v['answer']}, {v['domain']} / {v['skill']}")
        t, rt = s["tokens"], s["rebuttal_tokens"]
        tot_pt += t["prompt"]; tot_ct += t["completion"]
        tot_rpt += rt["prompt"]; tot_rct += rt["completion"]
        tot_cost += s["cost_usd"]
        lines.append(f"- Tokens: Vera {t['prompt']} prompt / "
                     f"{t['completion']} completion"
                     + (f"; Sol rebuttal {rt['prompt']} / {rt['completion']}"
                        if rt["prompt"] or rt["completion"] else "")
                     + f"; est. cost ${s['cost_usd']:.2f}")
        lines.append(f"- Continuation prompts needed: {s['continuations']}")
        lines.append("")
    lines.append("## Totals")
    if n_checked:
        lines.append(f"- Vera's verified answer matched CB on "
                     f"{n_ans_agree}/{n_checked} items; verified domain "
                     f"{n_dom_agree}/{n_checked}; verified skill "
                     f"{n_skill_agree}/{n_checked}")
    lines.append(f"- Tokens: Vera {tot_pt} prompt / {tot_ct} completion"
                 + (f"; Sol rebuttals {tot_rpt} / {tot_rct}"
                    if tot_rpt or tot_rct else "")
                 + f"; estimated total cost ${tot_cost:.2f} at published "
                   f"pricing ($4 in / $20 out per 1M)")
    lines.append("")
    lines.append("## Run notes")
    lines.append("- No disputes arose on these 10 items, so the Sol "
                 "rebuttal path was implemented but never triggered. "
                 "That is consistent with the set: Sol's answer, domain, "
                 "and skill already matched College Board on all 10 "
                 "(Sol's misses on this set were ratings, which Vera "
                 "never sees and does not rule on).")
    lines.append("- Line-protocol misses on items 4 and 10: Vera "
                 "embedded her COMP request at the end of a prose "
                 "sentence instead of sending it as the whole reply, so "
                 "the strict line protocol did not match it and no comps "
                 "were fulfilled. Vera completed her checks on those two "
                 "items without comps (item 4's own note misattributes "
                 "this to an empty pull). Her domain/skill confirmations "
                 "on items 4 and 10 therefore rest on the skill "
                 "definitions, not on pulled examples.")
    lines.append("- Rating stripping: one residual sentence survives "
                 "the mechanical strip on item 10 — a conditional about "
                 "bank examples ('If those examples include similar "
                 "simple FANBOYS and they're Medium, I learn'). It does "
                 "not state Sol's rating for the item. Everything else "
                 "the strip removed is logged per item in the "
                 "transcripts (strip_log).")
    lines.append("")
    lines.append("Full raw transcripts: item-N-transcript.json in this "
                 "folder (every API response, unedited, including any "
                 "Sol rebuttal exchange).")
    out = "\n".join(lines) + "\n"
    open(f"{OUT_DIR}/report.md", "w").write(out)
    print(out)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "run":
        run([int(x) for x in sys.argv[2:]])
    elif cmd == "report":
        report()
    else:
        print(__doc__)
