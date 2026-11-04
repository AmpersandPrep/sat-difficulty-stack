# Held-out 100 — full results

Set: stratified random draw, seed 20261102, from the 3,770-item College Board bank. 52 Math / 48 Reading and Writing; College Board bands 35 Easy / 33 Medium / 32 Hard. The College Board key was cross-checked across four sources, agreeing on all 100 items.

Protocol: Val's ratings (IDs + ratings only) were committed to this repo before scoring — results/held-out-100-val-ratings-2026-11-04.json, commit 9c6710b, Nov 4, 2026, 4:25 AM CST. Scoring ran after that commit landed.

## Headline

| Rater | Accuracy | Cohen's kappa | Weighted kappa (linear) | Weighted kappa (quadratic) |
|---|---|---|---|---|
| Val (full stack) | 76/100 | 0.639 | 0.704 | 0.765 |
| Fresh model baseline (same 100) | 52/100 | 0.273 | 0.412 | 0.556 |
| Fresh baseline, relabeled (every Medium → Hard) | 60/100 | 0.397 | 0.529 | 0.633 |

## Per-band recall

| Rater | Easy (n=35) | Medium (n=33) | Hard (n=32) |
|---|---|---|---|
| Val | 94.3% (33) | 57.6% (19) | 75.0% (24) |
| Fresh baseline | 88.6% (31) | 36.4% (12) | 28.1% (9) |
| Relabeled baseline | 88.6% (31) | 0% (0) | 90.6% (29) |

## Confusion matrices (rows = College Board, columns = prediction)

Val:
| CB \ pred | Easy | Medium | Hard |
|---|---|---|---|
| Easy | 33 | 1 | 1 |
| Medium | 7 | 19 | 7 |
| Hard | 2 | 6 | 24 |

Fresh baseline:
| CB \ pred | Easy | Medium | Hard |
|---|---|---|---|
| Easy | 31 | 4 | 0 |
| Medium | 21 | 12 | 0 |
| Hard | 3 | 20 | 9 |

## Paired comparisons (same items)

Val vs relabeled baseline: both right 54, Val only 22, relabeled only 6, neither 18.
Val vs fresh baseline: both right 48, Val only 28, fresh only 4, neither 20.

## Other diagnostics

- Precision by predicted band, Val: Easy 78.6% (33/42), Medium 73.1% (19/26), Hard 75.0% (24/32).
- Mean signed error (Easy=0, Medium=1, Hard=2): Val −0.07; fresh baseline −0.43.
- Two-band errors (Easy called Hard or Hard called Easy): Val 3, fresh baseline 3, relabeled baseline 7.
- By section: Math — Val 41/52, fresh 29/52. Reading and Writing — Val 35/48, fresh 23/48.
