# Scoreboard

All ratings are exact-band matches against College Board's official difficulty rating.

## Baseline: a fresh model, no stack (all 3,770 bank items)

- Difficulty accuracy: **50.8%** (Cohen's kappa 0.256; weighted kappa 0.504; Spearman rho 0.643; mean signed error −0.47, i.e. biased easy)
- Answer accuracy: 96.6% · Domain: 97.6% · Skill: 93.3%
- Band recall: Easy 91.2% · Medium 38.6% · Hard 20.4%
- Full per-item results: `results.csv` in this repo. Transcripts were committed before scoring.

## The stack on the working set of 10

A held-out working set for building (not the test set). Per-item table: `results/working-set-10-ids-and-ratings.md`.

| Rater | Exact-band score |
|---|---|
| Fresh model (baseline method) | 4 / 10 |
| Sol (solver alone) | 4 / 10 |
| Val, comparison version | 5 / 10 |
| Val, count version (no comparisons) | 7 / 9 run (item 10 not run) |

## Item 797a81fb (Algebra / Systems of two linear equations; CB Hard)

The worked example the count method was built on. The comparison version of Val rated it Medium. The count version rated it **Hard**: three distinct, interacting counterintuitive elements. Per-item record: `results/val-no-comparisons-797.json`.

## Where the count version still misses

Both misses on the working set are College Board Medium items the count version rated Easy with a count of zero (working items 3 and 9). Nothing was overrated. A held-out test set of 100 items, drawn from the full bank and excluded from every lookup and reference pool, is reserved for the final measurement; its key is not published here.
