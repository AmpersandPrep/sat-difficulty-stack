# sat-difficulty-stack

Pre-existing: the Cognitive Agency Approach to SAT difficulty, and the College Board educator question bank the ratings are scored against. Built during the hackathon (Oct 26 – Nov 4, 2026): the blind rating pipeline, the fresh-agent baseline run, and everything in this repository.

## What this is

An agent stack, built with Muse, that judges the difficulty of SAT questions from the student's side of the desk — and is scored against the College Board's official domain, skill, difficulty, and answer for every item in the bank (3,770 items: 1,845 Reading & Writing, 1,925 Math).

## How the measurement stays honest

- The bank is rated blind: questions are shuffled, and the rating agent sees only the question and its answer choices — no domain, no skill, no difficulty, no answer key.
- `results.csv` publishes, for every item: its College Board question ID, the official domain, skill, difficulty, and answer, and the agent's predicted domain, skill, rating, and answer. Question text is never published; the question ID is the citation, and anyone with bank access can look the item up.
- Every batch's raw transcript is committed to this repo before any scoring against the official labels happens, so the commit history is the proof that predictions came first.
