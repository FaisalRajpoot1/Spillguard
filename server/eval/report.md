# Spillguard — Evaluation Report

- **Generated:** 2026-07-07T12:11:15+00:00
- **Backend:** `mock` · model `google/gemma-3-12b-it`
- **Documents:** 31

## Spillguard vs Legacy DLP

| Metric | Spillguard | Legacy DLP |
|---|---|---|
| Verdict accuracy | **87%** | 48% |
| Spillage recall (caught) | **83%** | 54% |
| False-positive rate (clean) | 0% | 0% |
| Missed spillage (FN) | **4** | 11 |

Spillage recall — Spillguard `█████████████████░░░` 83%
Spillage recall — Legacy DLP `███████████░░░░░░░░░` 54%

## Confusion matrix (Spillguard)

Rows = ground truth, columns = predicted.

| expected ↓ / predicted → | ALLOW | FLAG | BLOCK |
|---|---|---|---|
| **ALLOW** | 7 | 0 | 0 |
| **FLAG** | 0 | 5 | 0 |
| **BLOCK** | 4 | 0 | 15 |

## Per-bucket accuracy

| Bucket | N | Spillguard | Legacy DLP |
|---|---|---|---|
| classified | 3 | 100% | 100% |
| clean | 7 | 100% | 100% |
| hard_semantic | 4 | 0% | 0% |
| marked_cui | 3 | 100% | 100% |
| mismarked_cui | 2 | 100% | 100% |
| pii | 3 | 100% | 0% |
| unmarked_cui | 9 | 100% | 0% |

## Missed spillage (honest gaps)

- `hard-01` (hard_semantic) — expected BLOCK, got ALLOW
- `hard-02` (hard_semantic) — expected BLOCK, got ALLOW
- `hard-03` (hard_semantic) — expected BLOCK, got ALLOW
- `hard-04` (hard_semantic) — expected BLOCK, got ALLOW

> These are semantic cases the current backend under-detects. They are exactly what a stronger self-hosted Gemma is expected to lift.
