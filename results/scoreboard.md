# Scoreboard

All ratings are exact-band matches against College Board's official difficulty rating.

## Baseline: a fresh model, no stack (all 3,770 bank items)

- Difficulty accuracy: **50.8%** (Cohen's kappa 0.256; weighted kappa 0.504; Spearman rho 0.643; mean signed error −0.47, i.e. biased easy)
- Answer accuracy: 96.6% · Domain: 97.6% · Skill: 93.3%
- Note: exact string matching reproduces 94.5%; the 96.6% figure uses grid-in / student-produced-response normalization (equivalent forms such as fractions and decimals counted correct), which is not part of the published scoring snippet.
- Band recall: Easy 91.2% · Medium 38.6% · Hard 20.4%
- Full per-item results: `results.csv` in this repo. Transcripts were committed before scoring.

## The stack on the working set of 10

This is a development/working set for building, not a held-out test: its ratings were visible as items ran. Per-item table: `results/working-set-10-ids-and-ratings.md`.

| Rater | Exact-band score |
|---|---|
| Fresh model (baseline method) | 4 / 10 |
| Sol (solver alone) | 4 / 10 |
| Val, comparison version | 5 / 10 |
| Val, no-comparisons version | 7 / 9 run (item 10 not run) |

## Item 797a81fb (Algebra / Systems of two linear equations; CB Hard)

The worked example the no-comparisons method was built on. The comparison version of Val rated it Medium. The no-comparisons version rated it **Hard**: three distinct, interacting counterintuitive elements. Per-item record: `results/val-no-comparisons-797.json`.

## Where the no-comparisons version still misses

Both misses on the working set are College Board Medium items the no-comparisons version rated Easy with a count of zero (working items 3 and 9). Nothing was overrated. The held-out test of 100 items has since been run and scored; see the held-out section below. Its membership list is not published as a standalone key file.

## The stack on the held-out 100

The final measurement. Stratified random draw, seed 20261102: 52 Math / 48 Reading and Writing; College Board bands 35 Easy / 33 Medium / 32 Hard. Val's ratings (IDs and ratings only, no question text) were committed to this repo before scoring: results/held-out-100-val-ratings-2026-11-04.json, commit 9c6710b, Nov 4, 2026. The stack ran with Val's brief as published in docs/val-brief-no-comparisons.txt; see the post-run note in that file about the count-rating sentence.

| Rater | Exact-band score | Cohen's kappa |
|---|---|---|
| Val (full stack) | 76 / 100 | 0.639 |
| Fresh model baseline (same 100) | 52 / 100 | 0.273 |
| Fresh baseline, relabeled (every Medium called Hard) | 60 / 100 | 0.397 |

Band recall for Val: Easy 94.3% (33/35), Medium 57.6% (19/33), Hard 75.0% (24/32). The fresh baseline on the same items: Easy 88.6%, Medium 36.4%, Hard 28.1%.
By section: Math — Val 41/52, fresh baseline 29/52. Reading and Writing — Val 35/48, fresh baseline 23/48.
Head-to-head on the same items: Val right where the fresh baseline was wrong on 28 items; the fresh baseline right where Val was wrong on 4.
Full scoring, including confusion matrices and weighted kappas: results/held-out-100-results.md.
