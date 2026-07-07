"""Spillguard evaluation harness.

Runs the labelled dataset through the *real* pipeline (whichever MODEL_BACKEND
is configured) and reports how well Spillguard triages CUI spillage versus a
legacy regex/keyword DLP baseline. Produces:

    eval/report.md    — human-readable
    eval/report.json  — machine-readable (feeds the UI accuracy tile)

Usage (from the server/ directory):
    python eval/run_eval.py
    MODEL_BACKEND=fireworks python eval/run_eval.py     # once a key is set
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Make `app` importable when run as a plain script.
_SERVER_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SERVER_DIR))

from app.config import get_settings          # noqa: E402
from app.model.factory import build_model_client  # noqa: E402
from app.pipeline import scan                # noqa: E402

_DATASET = Path(__file__).parent / "dataset" / "cui_eval.jsonl"
_REPORT_MD = Path(__file__).parent / "report.md"
_REPORT_JSON = Path(__file__).parent / "report.json"

VERDICTS = ["ALLOW", "FLAG", "BLOCK"]


def load_dataset() -> list[dict]:
    rows = []
    with _DATASET.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def binary_metrics(pairs: list[tuple[str, str]]) -> dict:
    """pairs = (expected, predicted). 'Positive' = should be stopped (!= ALLOW)."""
    tp = fp = tn = fn = 0
    for expected, predicted in pairs:
        exp_stop = expected != "ALLOW"
        pred_stop = predicted != "ALLOW"
        if exp_stop and pred_stop:
            tp += 1
        elif exp_stop and not pred_stop:
            fn += 1          # missed spillage — the dangerous error
        elif not exp_stop and pred_stop:
            fp += 1          # false alarm on a clean doc
        else:
            tn += 1
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "recall": round(recall, 3),
        "precision": round(precision, 3),
        "false_positive_rate": round(fpr, 3),
    }


async def run() -> dict:
    settings = get_settings()
    client = build_model_client(settings)
    rows = load_dataset()

    results = []
    try:
        for row in rows:
            res = await scan(row["text"], client, include_signals=False)
            results.append(
                {
                    "id": row["id"],
                    "bucket": row["bucket"],
                    "expected": row["expected"],
                    "spillguard": res.verdict.value,
                    "baseline": res.baseline.verdict.value,
                    "degraded": res.degraded,
                }
            )
    finally:
        await client.aclose()

    n = len(results)
    sg_exact = sum(r["spillguard"] == r["expected"] for r in results)
    bl_exact = sum(r["baseline"] == r["expected"] for r in results)

    sg_bin = binary_metrics([(r["expected"], r["spillguard"]) for r in results])
    bl_bin = binary_metrics([(r["expected"], r["baseline"]) for r in results])

    # Confusion matrix (rows = expected, cols = predicted) for Spillguard.
    confusion = {e: {p: 0 for p in VERDICTS} for e in VERDICTS}
    for r in results:
        confusion[r["expected"]][r["spillguard"]] += 1

    # Per-bucket breakdown.
    buckets: dict[str, dict] = defaultdict(lambda: {"n": 0, "sg_correct": 0, "bl_correct": 0})
    for r in results:
        b = buckets[r["bucket"]]
        b["n"] += 1
        b["sg_correct"] += r["spillguard"] == r["expected"]
        b["bl_correct"] += r["baseline"] == r["expected"]

    misses = [r for r in results if r["expected"] != "ALLOW" and r["spillguard"] == "ALLOW"]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "backend": settings.model_backend,
        "model": settings.model_name,
        "n": n,
        "spillguard": {"accuracy": round(sg_exact / n, 3), **sg_bin},
        "baseline": {"accuracy": round(bl_exact / n, 3), **bl_bin},
        "confusion": confusion,
        "buckets": {k: dict(v) for k, v in buckets.items()},
        "misses": misses,
        "results": results,
    }


def _bar(value: float, width: int = 20) -> str:
    filled = round(value * width)
    return "█" * filled + "░" * (width - filled)


def render_markdown(m: dict) -> str:
    sg, bl = m["spillguard"], m["baseline"]
    lines = [
        "# Spillguard — Evaluation Report",
        "",
        f"- **Generated:** {m['generated_at']}",
        f"- **Backend:** `{m['backend']}` · model `{m['model']}`",
        f"- **Documents:** {m['n']}",
        "",
        "## Spillguard vs Legacy DLP",
        "",
        "| Metric | Spillguard | Legacy DLP |",
        "|---|---|---|",
        f"| Verdict accuracy | **{sg['accuracy']:.0%}** | {bl['accuracy']:.0%} |",
        f"| Spillage recall (caught) | **{sg['recall']:.0%}** | {bl['recall']:.0%} |",
        f"| False-positive rate (clean) | {sg['false_positive_rate']:.0%} | {bl['false_positive_rate']:.0%} |",
        f"| Missed spillage (FN) | **{sg['fn']}** | {bl['fn']} |",
        "",
        f"Spillage recall — Spillguard `{_bar(sg['recall'])}` {sg['recall']:.0%}",
        f"Spillage recall — Legacy DLP `{_bar(bl['recall'])}` {bl['recall']:.0%}",
        "",
        "## Confusion matrix (Spillguard)",
        "",
        "Rows = ground truth, columns = predicted.",
        "",
        "| expected ↓ / predicted → | ALLOW | FLAG | BLOCK |",
        "|---|---|---|---|",
    ]
    for e in VERDICTS:
        row = m["confusion"][e]
        lines.append(f"| **{e}** | {row['ALLOW']} | {row['FLAG']} | {row['BLOCK']} |")

    lines += ["", "## Per-bucket accuracy", "", "| Bucket | N | Spillguard | Legacy DLP |", "|---|---|---|---|"]
    for name, b in sorted(m["buckets"].items()):
        sg_pct = b["sg_correct"] / b["n"]
        bl_pct = b["bl_correct"] / b["n"]
        lines.append(f"| {name} | {b['n']} | {sg_pct:.0%} | {bl_pct:.0%} |")

    if m["misses"]:
        lines += ["", "## Missed spillage (honest gaps)", ""]
        for r in m["misses"]:
            lines.append(f"- `{r['id']}` ({r['bucket']}) — expected {r['expected']}, got ALLOW")
        lines += [
            "",
            "> These are semantic cases the current backend under-detects. "
            "They are exactly what a stronger self-hosted Gemma is expected to lift.",
        ]
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    m = asyncio.run(run())
    _REPORT_JSON.write_text(json.dumps(m, indent=2), encoding="utf-8")
    _REPORT_MD.write_text(render_markdown(m), encoding="utf-8")

    sg, bl = m["spillguard"], m["baseline"]
    print(f"\n  Backend: {m['backend']}  ·  Documents: {m['n']}")
    print(f"  {'':22}{'Spillguard':>12}{'Legacy DLP':>12}")
    print(f"  {'verdict accuracy':22}{sg['accuracy']:>11.0%}{bl['accuracy']:>12.0%}")
    print(f"  {'spillage recall':22}{sg['recall']:>11.0%}{bl['recall']:>12.0%}")
    print(f"  {'false-positive rate':22}{sg['false_positive_rate']:>11.0%}{bl['false_positive_rate']:>12.0%}")
    print(f"  {'missed spillage (FN)':22}{sg['fn']:>11}{bl['fn']:>12}")
    print(f"\n  Reports written: {_REPORT_MD.name}, {_REPORT_JSON.name}\n")


if __name__ == "__main__":
    main()
