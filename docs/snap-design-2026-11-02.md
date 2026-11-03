# Snap — the Scrambler: design spec (Lydia, Nov 2, 2026)

Snap was designed Nov 2, 2026 (this spec, Lydia's dictation, superseding the earlier snap iterations in GOAL.md where they differ: the one-word rule becomes 1–2 words typically, 3 if needed), then built and run on the working set of 10 the same morning at Lydia's direction. Code: hidden_files/solver-run/snap.py. Results: hidden_files/solver-run/snap-10/report.md. All 10 items produced a snap; no ASK LYDIA flags. First build pass failed on a token cap (the model's internal reasoning consumed a 400-token cap before any visible output); cap raised and re-run; total spend across both passes about $0.22.

## The scramble (mechanical, done by the runner before Snap sees anything)

Take the question and the answer choices. Remove:

- the "to be" verbs (am, is, are, was, were, be, been, being)
- the articles (a, an, the)
- the prepositions

Then scramble the remaining words. The scrambled text, question and choices mixed together, is all Snap gets.

## Snap's brief (Lydia's words, shaped only for grammar)

Students will often project a topic in their heads. Agents struggle with this because they just want to answer the question. The question and answers are purposefully mixed up here to simulate what that is like for a student. The agent is not supposed to unscramble it, but rather use the scramble to simulate a projected or estimated meaning.

## The output

The snap topic: 1–2 words typically, 3 words if that is needed. Nothing more.

- Good: "Staged Play"
- Not good: "Staged Play put on by a trope of actors in Russia" (too specific, too elaborated; that is analysis, not a projection)

For math, the two words are area + topic. That is really it:

- "Geometry polygons"
- "Trigonometry radians"

## What the snap is for

This is not about accuracy. It is about trying to predict what a 17-year-old, under pressure and time constraints, tired, might surmise. The snap records the projection, not the truth of the item. The gap between the snap and what the full rating later finds in the question is the signal; Snap itself must stay naive. (Per the Oct 31 revision, Snap also develops the potential list of heuristics the item might be trading on; the topic call above is the constrained part.)

## Numbers and operations (Lydia, Nov 2, 2026)

Some of the math scrambles will just be numbers and operations, with almost no words left. That is fine, and Snap's brief must say so explicitly: that is okay. Some students literally see a math item like that, as numbers and operations and nothing else. Snap should not strain to manufacture a topic out of it or treat the item as broken; a thin projection off numbers and operations is a faithful simulation.

## When Snap cannot find a snap (Lydia, Nov 2, 2026)

If Snap cannot find even 2 words, it does not improvise and it does not unscramble. It flags the item, and the runner asks Lydia for direction. The item waits for her ruling instead of proceeding on an invented snap.

Provisional by design: Lydia is not entirely sure how this will work yet, and this part may need finessing once Snap is built and seen in practice.
