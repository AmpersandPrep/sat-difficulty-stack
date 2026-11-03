# The Solver — Lydia's spec (dictated Nov 1, 2026)

The first agent of the stack. This is the informed agent from the stack design, specified by Lydia on Nov 1.

## What the solver is told up front

- The issue we are trying to solve (the baseline failure: a fresh model rates College Board difficulty at 50.8% accuracy, kappa 0.256, and its errors lean easier — Hard recall 20.4%, 178 Hard items called Easy vs 1 Easy item called Hard).
- It is EXPLICITLY told to let this only inform the decision, not decide it. It is just as important to correctly identify Medium and Easy as Hard.
- Then give it the stats (the baseline results).

## Process requirements

- It details its process, transcribing it down (works out loud; the transcript is data).
- If it makes a mistake, it admits it and goes back. That is recorded. That is data.
- For each answer choice A, B, C, D: it says whether it is right or wrong, and why it holds that position. Transcribed. That is data.
- If it does not end with exactly 1 right answer and 3 wrong answers, it must keep working until it does. Record that struggle; it is data.
- It may take an educated guess only after it has gone back and reconsidered more than twice.

## Outputs

- After the solving: a domain, a skill, and a rating (Easy / Medium / Hard).

## Question bank access

- The solver CAN have access to the question bank to look things up, but consulting it is a decision the solver makes. The bank is not loaded into its current memory.

## Standing constraints carried over

- Test-only sets stay untouched for calibration: the 100-item R&W population sample and the curated 40. Mechanics smoke tests use non-sample bank items.
- Transcripts are recorded in full; nothing is patched after the fact.
