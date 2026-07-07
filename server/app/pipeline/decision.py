"""Stage 4 — decision engine.

Deterministic rules fuse all signals into the final verdict. The model informs
the decision; these rules *own* it. Pure and side-effect-free, so it is trivial
to unit-test every branch.

Rule table (first match wins):
  1. literal classified banner ............... BLOCK  (CLASSIFIED)
  2. CUI content + no marking (unmarked_cui) .. BLOCK  (spillage)
  3. CUI content + wrong/partial marking ...... FLAG
  4. CUI content + correct marking ............ FLAG   (advisory: verify dest.)
  5. weak/low-confidence sensitivity .......... FLAG
  6. nothing sensitive ........................ ALLOW
Degraded (model unavailable) uses only deterministic evidence and is labelled.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schemas import (
    ClassificationLevel,
    CUICategory,
    DeterministicSignals,
    ModelSignals,
    Verdict,
)
from .markings import MarkingAssessment

# Below this model confidence we treat sensitivity as "weak" → FLAG not BLOCK.
_WEAK_CONFIDENCE = 0.45


@dataclass(frozen=True)
class DecisionOutcome:
    verdict: Verdict
    classification_level: ClassificationLevel
    cui_categories: list[CUICategory]
    spillage_flag: bool
    rationale: str
    confidence: float
    degraded: bool


def decide(
    det: DeterministicSignals,
    model: ModelSignals,
    marking: MarkingAssessment,
) -> DecisionOutcome:
    degraded = not model.available

    # 1 — Literal classified banner: unconditional block.
    if det.classified_banner:
        return DecisionOutcome(
            verdict=Verdict.BLOCK,
            classification_level=ClassificationLevel.CLASSIFIED,
            cui_categories=marking.categories,
            spillage_flag=True,
            rationale=(
                f"Document carries a classified banner ({det.classified_banner}); "
                "it must not leave the enclave."
            ),
            confidence=1.0,
            degraded=degraded,
        )

    # No sensitive content from any source → clean.
    if not marking.is_cui:
        return DecisionOutcome(
            verdict=Verdict.ALLOW,
            classification_level=ClassificationLevel.UNCLASSIFIED,
            cui_categories=[],
            spillage_flag=False,
            rationale=(
                model.rationale or "No CUI content detected."
            ) if not degraded else "No literal markers found (model unavailable — degraded scan).",
            confidence=model.confidence if not degraded else 0.5,
            degraded=degraded,
        )

    # From here on the content IS CUI.
    level = (
        model.classification_level
        if model.available and model.classification_level != ClassificationLevel.UNCLASSIFIED
        else ClassificationLevel.CUI_SP
    )
    confidence = model.confidence if model.available else 0.5
    weak = model.available and confidence < _WEAK_CONFIDENCE

    # 2 — Unmarked CUI: the spillage case.
    if marking.unmarked_cui and not weak:
        cats = ", ".join(c.value for c in marking.categories)
        return DecisionOutcome(
            verdict=Verdict.BLOCK,
            classification_level=level,
            cui_categories=marking.categories,
            spillage_flag=True,
            rationale=(
                f"Contains unmarked CUI ({cats}). "
                f"{model.rationale} Required marking: {', '.join(marking.expected)}."
            ).strip(),
            confidence=confidence,
            degraded=degraded,
        )

    # 3 — Marked, but wrong/partial marking.
    if marking.mismatch:
        return DecisionOutcome(
            verdict=Verdict.FLAG,
            classification_level=level,
            cui_categories=marking.categories,
            spillage_flag=True,
            rationale=(
                f"CUI present but mismarked. Found {marking.found or 'none'}, "
                f"expected {marking.expected}. {model.rationale}"
            ).strip(),
            confidence=confidence,
            degraded=degraded,
        )

    # 5 — Weak/low-confidence sensitivity → advisory flag.
    if weak:
        return DecisionOutcome(
            verdict=Verdict.FLAG,
            classification_level=level,
            cui_categories=marking.categories,
            spillage_flag=False,
            rationale=(
                f"Possible CUI (low confidence {confidence:.2f}) — recommend human review. "
                f"{model.rationale}"
            ).strip(),
            confidence=confidence,
            degraded=degraded,
        )

    # 4 — Correctly marked CUI: advisory flag (verify destination authorisation).
    return DecisionOutcome(
        verdict=Verdict.FLAG,
        classification_level=level,
        cui_categories=marking.categories,
        spillage_flag=False,
        rationale=(
            f"CUI present and correctly marked ({', '.join(marking.found)}). "
            "Verify the destination is authorised before sending."
        ),
        confidence=confidence,
        degraded=degraded,
    )
