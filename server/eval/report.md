# Spillguard — Evaluation Report

- **Generated:** 2026-07-09T18:37:00+00:00
- **Backend:** `vllm-local` · model `google/gemma-3-12b-it` (self-hosted on an AMD GPU via ROCm + vLLM)
- **Documents:** 31

## Spillguard vs Legacy DLP

| Metric | Spillguard | Legacy DLP |
|---|---|---|
| Verdict accuracy | **100%** | 48% |
| Spillage recall (caught) | **100%** | 54% |
| False-positive rate (clean) | 0% | 0% |
| Missed spillage (FN) | **0** | 11 |

Spillage recall — Spillguard `████████████████████` 100%
Spillage recall — Legacy DLP `███████████░░░░░░░░░` 54%

## Confusion matrix (Spillguard)

Rows = ground truth, columns = predicted.

| expected ↓ / predicted → | ALLOW | FLAG | BLOCK |
|---|---|---|---|
| **ALLOW** | 7 | 0 | 0 |
| **FLAG** | 0 | 5 | 0 |
| **BLOCK** | 0 | 0 | 19 |

## Per-bucket accuracy

| Bucket | N | Spillguard | Legacy DLP |
|---|---|---|---|
| classified | 3 | 100% | 100% |
| clean | 7 | 100% | 100% |
| hard_semantic | 4 | 100% | 0% |
| marked_cui | 3 | 100% | 100% |
| mismarked_cui | 2 | 100% | 100% |
| pii | 3 | 100% | 0% |
| unmarked_cui | 9 | 100% | 0% |

> Self-hosted Gemma 3 12B on AMD caught **every** spillage — including the colloquial-prose `hard_semantic` cases that keyword DLP and the offline mock miss. The offline `mock` fallback backend scores 87%; real Gemma reaches 100%.
