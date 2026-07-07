"""Mock model backend.

Simulates Gemma's *semantic* judgement using the SEMANTIC_INDICATORS table, so
the full pipeline and UI can be built and demoed with no GPU and no network.
It deliberately catches meaning that the deterministic baseline misses.
"""

from __future__ import annotations

import re

from ..logging_config import get_logger
from ..rules.patterns import SEMANTIC_INDICATORS, count_ssns
from ..schemas import CUICategory, ClassificationLevel, ModelSignals, Span
from .base import ModelClient

log = get_logger(__name__)

# Split into sentences for span extraction (simple, dependency-free).
_SENTENCE_SPLIT = re.compile(r"[^.!?\n]*[.!?\n]|[^.!?\n]+$")


def _sentence_around(text: str, pos: int) -> tuple[str, int, int]:
    """Return the (sentence, start, end) containing character offset `pos`."""
    for m in _SENTENCE_SPLIT.finditer(text):
        if m.start() <= pos < m.end():
            return m.group(0).strip(), m.start(), m.end()
    return text.strip(), 0, len(text)


class MockModelClient(ModelClient):
    name = "mock"

    async def classify(self, text: str) -> ModelSignals:
        categories: list[CUICategory] = []
        spans: list[Span] = []
        reasons: list[str] = []
        seen_spans: set[str] = set()

        for pattern, category, reason in SEMANTIC_INDICATORS:
            m = pattern.search(text)
            if not m:
                continue
            sentence, start, end = _sentence_around(text, m.start())
            key = f"{category}:{sentence}"
            if key in seen_spans:
                continue
            seen_spans.add(key)
            if category not in categories:
                categories.append(category)
            spans.append(
                Span(text=sentence, category=category, reason=reason, start=start, end=end)
            )
            reasons.append(reason)

        # SSNs are unambiguous PII.
        if count_ssns(text) > 0 and CUICategory.PRVCY not in categories:
            categories.append(CUICategory.PRVCY)
            reasons.append("Contains a social security number.")

        if not categories:
            return ModelSignals(
                available=True,
                classification_level=ClassificationLevel.UNCLASSIFIED,
                cui_categories=[],
                spillage_flag=False,
                offending_spans=[],
                rationale="No CUI content detected.",
                confidence=0.9,
            )

        rationale = " ".join(reasons[:3])
        # More corroborating spans → higher confidence, capped.
        confidence = min(0.95, 0.7 + 0.08 * len(spans))

        log.debug("mock classify: %d categories, %d spans", len(categories), len(spans))
        return ModelSignals(
            available=True,
            classification_level=ClassificationLevel.CUI_SP,
            cui_categories=categories,
            spillage_flag=True,
            offending_spans=spans,
            rationale=rationale,
            confidence=round(confidence, 2),
        )
