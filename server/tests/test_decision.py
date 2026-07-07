"""Stage 4 (decision engine) — every branch of the rule table."""

from app.pipeline.decision import decide
from app.pipeline.markings import MarkingAssessment
from app.schemas import (
    ClassificationLevel,
    CUICategory,
    DeterministicSignals,
    ModelSignals,
    Verdict,
)


def _det(**kw) -> DeterministicSignals:
    return DeterministicSignals(**kw)


def _model(available=True, cats=None, conf=0.9, level=ClassificationLevel.CUI_SP):
    return ModelSignals(
        available=available,
        classification_level=level,
        cui_categories=cats or [],
        spillage_flag=bool(cats),
        confidence=conf,
    )


def test_classified_banner_blocks():
    out = decide(_det(classified_banner="SECRET"), _model(), MarkingAssessment())
    assert out.verdict is Verdict.BLOCK
    assert out.classification_level is ClassificationLevel.CLASSIFIED


def test_clean_allows():
    out = decide(_det(), _model(available=True, cats=[]), MarkingAssessment())
    assert out.verdict is Verdict.ALLOW


def test_unmarked_cui_blocks():
    marking = MarkingAssessment(
        categories=[CUICategory.CTI], found=[], expected=["CUI//SP-CTI"], unmarked_cui=True
    )
    out = decide(_det(), _model(cats=[CUICategory.CTI]), marking)
    assert out.verdict is Verdict.BLOCK
    assert out.spillage_flag is True


def test_mismarked_cui_flags():
    marking = MarkingAssessment(
        categories=[CUICategory.CTI],
        found=["CUI//SP-PRVCY"],
        expected=["CUI//SP-CTI"],
        mismatch=True,
    )
    out = decide(_det(banner_markings=["CUI//SP-PRVCY"]), _model(cats=[CUICategory.CTI]), marking)
    assert out.verdict is Verdict.FLAG


def test_correctly_marked_cui_flags_advisory():
    marking = MarkingAssessment(
        categories=[CUICategory.CTI], found=["CUI//SP-CTI"], expected=["CUI//SP-CTI"]
    )
    out = decide(_det(banner_markings=["CUI//SP-CTI"]), _model(cats=[CUICategory.CTI]), marking)
    assert out.verdict is Verdict.FLAG
    assert out.spillage_flag is False


def test_low_confidence_downgrades_to_flag():
    marking = MarkingAssessment(
        categories=[CUICategory.CTI], found=[], expected=["CUI//SP-CTI"], unmarked_cui=True
    )
    out = decide(_det(), _model(cats=[CUICategory.CTI], conf=0.2), marking)
    assert out.verdict is Verdict.FLAG  # weak → advisory, not a hard block


def test_degraded_flag_when_model_unavailable():
    out = decide(_det(), _model(available=False), MarkingAssessment())
    assert out.degraded is True
