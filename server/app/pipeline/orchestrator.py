"""Pipeline orchestrator — runs the four stages and assembles a ScanResult.

Design notes:
  * Deterministic (Stage 1) runs first and unconditionally.
  * Semantic (Stage 2) can fail → the whole thing degrades, never crashes.
  * The verdict is produced by the deterministic decision engine (Stage 4),
    not the model.
  * Offending spans prefer the model's evidence but fall back to deterministic
    spans so a degraded scan still shows *why*.
"""

from __future__ import annotations

from time import perf_counter

from ..logging_config import get_logger
from ..model.base import ModelClient
from ..schemas import ScanResult, Signals, Span
from .decision import decide
from .deterministic import baseline_verdict, deterministic_spans, run_deterministic
from .markings import assess_markings
from .semantic import run_semantic

log = get_logger(__name__)


async def scan(text: str, client: ModelClient, *, include_signals: bool = True) -> ScanResult:
    started = perf_counter()

    # Stage 1
    det = run_deterministic(text)
    # Stage 2
    model = await run_semantic(text, client)
    # Stage 3
    marking = assess_markings(det, model)
    # Stage 4
    outcome = decide(det, model, marking)

    baseline = baseline_verdict(det)

    # Evidence: model spans first, then deterministic ones (dedup by text).
    spans: list[Span] = list(model.offending_spans)
    if not spans:
        spans = deterministic_spans(text)
    else:
        existing = {s.text for s in spans}
        spans.extend(s for s in deterministic_spans(text) if s.text not in existing)

    latency_ms = int((perf_counter() - started) * 1000)

    result = ScanResult(
        verdict=outcome.verdict,
        classification_level=outcome.classification_level,
        cui_categories=outcome.cui_categories,
        portion_markings_found=marking.found,
        portion_markings_expected=marking.expected,
        marking_mismatch=marking.mismatch,
        spillage_flag=outcome.spillage_flag,
        offending_spans=spans,
        rationale=outcome.rationale,
        confidence=outcome.confidence,
        engine=client.name,
        degraded=outcome.degraded,
        latency_ms=latency_ms,
        baseline=baseline,
        signals=Signals(deterministic=det, model=model) if include_signals else None,
    )

    log.info(
        "scan -> %s (%s, %d cats, %dms%s)",
        result.verdict.value,
        result.engine,
        len(result.cui_categories),
        latency_ms,
        ", degraded" if result.degraded else "",
    )
    return result
