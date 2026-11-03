#!/usr/bin/env python3
"""Snap v1 — the Scrambler (third agent of Lydia's difficulty stack).

Built to Lydia's spec of 2026-11-02
(files/snap-design-2026-11-02.md):

- The runner mechanically prepares the scramble: from the question text
  and all answer choices, remove the "to be" verbs, the articles, and
  the prepositions, then shuffle the remaining tokens. The shuffle is
  seeded by the item ID so a scramble is reproducible.
- Snap gets ONLY the scrambled text. Snap must not unscramble it and
  must not answer the question. Snap simulates the topic a student
  projects at first glance: 1-2 words typically, 3 at most, plus the
  potential heuristics list (Oct 31 revision).
- Some scrambles are just numbers and operations. Snap's brief says
  that is okay: some students literally see an item like that.
- If Snap cannot find even 2 words, it replies ASK LYDIA and the item
  is flagged for Lydia's direction instead of proceeding on an
  invented snap.

One fresh API conversation per item. Transcripts are recorded raw.

Usage:
  snap.py run [item_no...]   # run Snap on working-10 items
  snap.py report             # compile snap-10/report.md
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
ITEMS = f"{BASE}/working-10/items.json"
OUT_DIR = f"{BASE}/snap-10"
MODEL = "muse-wonder-1.0"
MAX_TOKENS = 4000  # this model reasons internally before answering; a
# small cap is consumed entirely by reasoning tokens (seen Nov 2, 2026:
# 400/400 reasoning, empty content). Snap's visible output is tiny, but
# the cap must leave room for the reasoning that precedes it.
PRICE_IN, PRICE_OUT = 4.0, 20.0  # $ per 1M tokens

BE_VERBS = {"am", "is", "are", "was", "were", "be", "been", "being"}
ARTICLES = {"a", "an", "the"}
PREPOSITIONS = {
    "about", "above", "across", "after", "against", "along", "among",
    "around", "at", "before", "behind", "below", "beneath", "beside",
    "between", "beyond", "by", "despite", "down", "during", "except",
    "for", "from", "in", "inside", "into", "like", "near", "of", "off",
    "on", "onto", "out", "over", "past", "per", "through", "to",
    "toward", "towards", "under", "until", "up", "upon", "via", "with",
    "within", "without",
}
REMOVE = BE_VERBS | ARTICLES | PREPOSITIONS
EDGE_PUNCT = ".,;:!?()\"'$*_`"


def scramble(item):
    text = item["question"].strip()
    for L in "ABCD":
        if item["choices"].get(L):
            text += " " + str(item["choices"][L]).strip()
    kept = []
    for tok in text.split():
        norm = tok.strip(EDGE_PUNCT).lower()
        if norm in REMOVE:
            continue
        kept.append(tok)
    rng = random.Random(int(item["id"], 16))
    rng.shuffle(kept)
    return " ".join(kept), len(kept)


SYSTEM = """You are Snap, one agent in a research stack studying how SAT questions look at first glance.

Students will often project a topic in their heads. Agents struggle with this because they just want to answer the question. The question and answers are purposefully mixed up here to simulate what that is like for a student. You are NOT supposed to unscramble it, and you must not try to answer the question. Use the scramble to simulate a projected or estimated meaning: the topic a 17-year-old, under pressure and time constraints, tired, might surmise at a glance.

This is not about accuracy. Do not reconstruct the original question. Do not explain your reasoning.

Some scrambles are just numbers and operations, with almost no words. That is okay. Some students literally see a math item exactly like that. Work with what is there.

Reply in exactly this shape, nothing else:

SNAP: <the projected topic, 1-2 words typically, 3 words at most>
HEURISTICS: <a short comma-separated list of the naive first-glance rules or associations this item might be trading on, or "none">

If you cannot find even 2 words for a snap, reply with only this line instead:

ASK LYDIA"""


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


SNAP_RE = re.compile(r"SNAP:\s*(.+?)\s*\n\s*HEURISTICS:\s*(.+)", re.I | re.S)


def parse(text):
    t = (text or "").strip()
    if t.upper().startswith("ASK LYDIA"):
        return {"flag": "ASK LYDIA"}
    m = SNAP_RE.search(t)
    if not m:
        return {"flag": "UNPARSED", "raw": t}
    return {"snap": m.group(1).strip(),
            "heuristics": m.group(2).strip()}


def run_item(n, item):
    scram, ntok = scramble(item)
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": scram}]
    record = {"item_no": n, "id": item["id"], "model": MODEL,
              "system_prompt": SYSTEM, "scramble": scram,
              "scramble_tokens": ntok, "turns": []}
    try:
        resp = call_api(messages)
    except urllib.error.HTTPError as e:
        record["error"] = f"HTTP {e.code}: " + e.read().decode(
            "utf-8", "replace")[:300]
        return record
    except Exception as e:
        record["error"] = f"{type(e).__name__}: {e}"
        return record
    record["turns"].append(resp)
    content = ((resp.get("choices") or [{}])[0].get("message") or {}
               ).get("content") or ""
    record["reply"] = content
    record["parsed"] = parse(content)
    u = resp.get("usage") or {}
    pt, ct = u.get("prompt_tokens") or 0, u.get("completion_tokens") or 0
    record["tokens"] = {"prompt": pt, "completion": ct}
    record["cost_usd"] = round((pt * PRICE_IN + ct * PRICE_OUT) / 1e6, 4)
    return record


def run(which):
    items = json.load(open(ITEMS))
    os.makedirs(OUT_DIR, exist_ok=True)
    results_path = f"{OUT_DIR}/results.json"
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
        json.dump(rec, open(f"{OUT_DIR}/item-{n}-transcript.json", "w"),
                  indent=1)
        results[str(n)] = rec
        json.dump(results, open(results_path, "w"), indent=1)
        print(f"  -> {rec.get('parsed')} | tokens "
              f"{rec.get('tokens')} | ${rec.get('cost_usd')}", flush=True)


def report():
    items = json.load(open(ITEMS))
    results = json.load(open(f"{OUT_DIR}/results.json"))
    lines = ["# Snap v1 — working set of 10", "",
             f"Date: {time.strftime('%Y-%m-%d')}  Model: {MODEL}. "
             "Same 10 items Sol and Vera ran. Snap is not scored for "
             "accuracy by design; the CB domain/skill is shown so the "
             "projection can be compared with what the item actually "
             "is.", ""]
    tot = 0.0
    for n, item in enumerate(items, 1):
        r = results.get(str(n))
        lines.append(f"## Item {n} — {item['id']}")
        lines.append(f"- CB: {item['cb_domain']} / {item['cb_skill']} / "
                     f"{item['cb_rating']}")
        if not r:
            lines.append("- Snap: NOT RUN")
        elif r.get("error"):
            lines.append(f"- Snap: ERROR {r['error']}")
        else:
            p = r["parsed"]
            if p.get("flag"):
                lines.append(f"- Snap: FLAG {p['flag']}")
            else:
                lines.append(f"- Snap: \"{p['snap']}\"")
                lines.append(f"- Heuristics: {p['heuristics']}")
            lines.append(f"- Scramble tokens: {r['scramble_tokens']}; "
                         f"cost ${r['cost_usd']:.4f}")
            tot += r["cost_usd"]
        lines.append("")
    lines.append(f"Total estimated cost: ${tot:.4f}")
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
