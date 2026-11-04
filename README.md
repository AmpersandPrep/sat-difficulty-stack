# sat-difficulty-stack

Pre-existing: the Cognitive Agency Approach to SAT difficulty, and the College Board educator question bank the ratings are scored against. Built during the hackathon (Oct 26 – Nov 4, 2026): the blind rating pipeline, the fresh-agent baseline run, the agent stack, and everything else in this repository.

## What this is

An agent stack, built with Muse, that judges the difficulty of SAT questions from the student's side of the desk — and is scored against the College Board's official domain, skill, difficulty, and answer for every item in the bank (3,770 items: 1,845 Reading & Writing, 1,925 Math).

A fresh large language model, asked to rate difficulty cold, agrees with College Board only 50.8% of the time (kappa 0.256), and the misses lean easy: it recognizes 91.2% of Easy items but only 20.4% of Hard ones. The stack exists to close that gap by rating the way a teacher does: solve the question as a student would meet it, check the solve, notice what a student would think the question is about, and then weigh the whole picture, including the counterintuitive elements built into the question.

## The stack

- **Sol** (the Solver) solves each question blind and leaves a transcript. Two things in the transcript carry difficulty signal: how many steps the solve took, and whether Sol had to correct itself mid-solve. That Sol solved it is not evidence a student will.
- **Vera** (the Checker) verifies Sol's answer, domain, and skill against pulled comparison items, and sends mistakes back to Sol. Vera sends no report to the evaluator.
- **Snap** (the Scrambler) receives the question with function words mechanically removed and the rest scrambled, and says what a student might think the topic is. Snap exists to surface bias: the projected topic a student walks in with.
- **Val** (the Evaluator) rates difficulty. She starts from the assumption that the question is Hard and weighs the whole packet: the solver's process and its friction, any back-and-forth with the checker, the scrambled gist and the heuristics a student might employ, and the counterintuitive elements she can name as printed features of the question. No single signal decides the rating. An earlier version rated by comparing the question against one example per band; the comparison proved too open to interpretation and was removed. Val's exact instructions are in `docs/val-brief-no-comparisons.txt`, which also carries a post-run note about one sentence in that brief.

The runner between them is deterministic plumbing. It strips Sol's tentative rating before Val sees the transcript, delivers the coverage notes for the surmised skill, and makes no judgments of its own.

## Results so far

Full numbers: `results/scoreboard.md`. Headlines:

- Baseline (fresh model, all 3,770 items): 50.8% difficulty accuracy, kappa 0.256. Per-item: `results.csv`.
- Working set of 10: fresh model 4/10, Sol 4/10, Val (comparison version) 5/10, Val (no-comparisons version) 7 of the 9 run.
- A held-out test set of 100 items was excluded from every lookup and reference pool and has now been run and scored: Val matched College Board on 76 of 100 (Cohen's kappa 0.639), against 52 of 100 for the fresh-model baseline on the same items — see results/scoreboard.md. results.csv publishes College Board labels and baseline predictions for the full bank; what is withheld is the held-out set's membership list as a standalone key file, along with all question text and run packets. The held-out 100 is a separate, stratified random set (seed 20261102) drawn for the final test and is not any earlier 100-item set mentioned in the docs.

## What's here

- `code/` — the agents and runners, as run. (The API credential is supplied at runtime by the environment's credential helper; no key is in this repo.)
- `docs/` — the stack design, each agent's design note, Val's current brief, and the coverage-and-heuristics list: what students actually reach for, per skill, written from classroom observation.
- `results/` — the scoreboard and per-item records, IDs and ratings only.

## How the measurement stays honest

- The bank is rated blind: questions are shuffled, and the rating agent sees only the question and its answer choices — no domain, no skill, no difficulty, no answer key.
- `results.csv` publishes, for every item: its College Board question ID, the official domain, skill, difficulty, and answer, and the agent's predicted domain, skill, rating, and answer. Question text is never published; the question ID is the citation, and anyone with bank access can look the item up.
- Every batch's raw transcript is committed to this repo before any scoring against the official labels happens, so the commit history is the proof that predictions came first.
