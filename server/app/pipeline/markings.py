"""Stage 3 — portion-marking checker.

Compares the markings a document *has* (from Stage 1) against the markings its
content *requires* (from Stage 1 keywords + Stage 2 semantics). The dangerous
case is unmarked CUI: sensitive content with no marking at all — a spillage
waiting to happen.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..rules.cui_categories import expected_markings
from ..schemas import CUICategory, DeterministicSignals, ModelSignals


@dataclass(frozen=True)
class MarkingAssessment:
    categories: list[CUICategory] = field(default_factory=list)  # union of all evidence
    found: list[str] = field(default_factory=list)               # markings in the doc
    expected: list[str] = field(default_factory=list)            # markings it should carry
    unmarked_cui: bool = False   # CUI content with NO marking present
    mismatch: bool = False       # marked, but not with the required marking(s)

    @property
    def is_cui(self) -> bool:
        return bool(self.categories)


def _union_categories(det: DeterministicSignals, model: ModelSignals) -> list[CUICategory]:
    ordered: list[CUICategory] = []
    for cat in list(model.cui_categories) + list(det.keyword_categories):
        if cat not in ordered:
            ordered.append(cat)
    # SSNs imply privacy CUI even if nothing else fired.
    if det.ssn_hits > 0 and CUICategory.PRVCY not in ordered:
        ordered.append(CUICategory.PRVCY)
    return ordered


def assess_markings(det: DeterministicSignals, model: ModelSignals) -> MarkingAssessment:
    categories = _union_categories(det, model)
    found = list(det.banner_markings)

    if not categories:
        return MarkingAssessment(categories=[], found=found, expected=[])

    expected = expected_markings(categories)

    if not found:
        # Sensitive content, zero markings → the classic spillage.
        return MarkingAssessment(
            categories=categories,
            found=[],
            expected=expected,
            unmarked_cui=True,
        )

    # Marked, but does it carry every required (category-specific) marking?
    missing = [m for m in expected if m not in found]
    return MarkingAssessment(
        categories=categories,
        found=found,
        expected=expected,
        mismatch=bool(missing),
    )
