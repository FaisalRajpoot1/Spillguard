"""Stage 1 — deterministic pre-check.

Cheap, explainable, GPU-free. Runs first and always. Doubles as the "old DLP"
baseline shown side-by-side in the demo: it only sees explicit markings,
keywords, and SSNs, so it *misses* unmarked semantic CUI — which is the whole
point of the contrast.
"""

from __future__ import annotations

from ..rules.patterns import (
    SSN_RE,
    count_ssns,
    find_classified_banner,
    find_portion_markings,
    keyword_category_hits,
)
from ..schemas import (
    BaselineResult,
    CUICategory,
    DeterministicSignals,
    Span,
    Verdict,
)


def run_deterministic(text: str) -> DeterministicSignals:
    markings = find_portion_markings(text)
    classified = find_classified_banner(text)
    kw_hits = keyword_category_hits(text)
    ssns = count_ssns(text)

    matched_rules: list[str] = []
    if classified:
        matched_rules.append(f"classified banner: {classified}")
    for marking in markings:
        matched_rules.append(f"marking present: {marking}")
    for cat, words in kw_hits.items():
        matched_rules.append(f"keyword[{cat.value}]: {', '.join(words)}")
    if ssns:
        matched_rules.append(f"SSN pattern ×{ssns}")

    return DeterministicSignals(
        banner_markings=markings,
        classified_banner=classified,
        keyword_categories=list(kw_hits.keys()),
        ssn_hits=ssns,
        matched_rules=matched_rules,
    )


def deterministic_spans(text: str) -> list[Span]:
    """Offending spans derivable without the model (SSNs, etc.).
    Used to keep evidence useful when running degraded."""
    spans: list[Span] = []
    for m in SSN_RE.finditer(text):
        spans.append(
            Span(
                text=m.group(0),
                category=CUICategory.PRVCY,
                reason="Social security number.",
                start=m.start(),
                end=m.end(),
            )
        )
    return spans


def baseline_verdict(sig: DeterministicSignals) -> BaselineResult:
    """What a legacy regex/keyword DLP would decide from the same document.

    It has no semantic understanding, so a document that is sensitive only in
    *meaning* (no marking, no keyword) sails through as ALLOW.
    """
    if sig.classified_banner:
        return BaselineResult(
            verdict=Verdict.BLOCK,
            matched_rules=[f"classified banner: {sig.classified_banner}"],
            note="Blocked on a literal classified banner.",
        )

    literal_hits = list(sig.matched_rules)
    if sig.banner_markings or sig.keyword_categories or sig.ssn_hits:
        return BaselineResult(
            verdict=Verdict.FLAG,
            matched_rules=literal_hits,
            note="Flagged on explicit markings/keywords only.",
        )

    return BaselineResult(
        verdict=Verdict.ALLOW,
        matched_rules=[],
        note="No literal markers found — legacy DLP sees nothing.",
    )
