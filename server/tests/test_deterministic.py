"""Stage 1 (deterministic) + baseline behaviour."""

from app.pipeline.deterministic import baseline_verdict, run_deterministic
from app.schemas import CUICategory, Verdict


def test_detects_portion_markings():
    sig = run_deterministic("CUI//SP-CTI\nThe engine spec is attached.")
    assert "CUI//SP-CTI" in sig.banner_markings


def test_detects_classified_banner():
    sig = run_deterministic("This memo is SECRET and controlled.")
    assert sig.classified_banner == "SECRET"


def test_detects_ssn():
    sig = run_deterministic("Employee SSN: 123-45-6789 on record.")
    assert sig.ssn_hits == 1
    assert CUICategory.PRVCY in sig.keyword_categories  # via "ssn:" keyword


def test_keyword_categories():
    sig = run_deterministic("This involves ITAR-controlled hardware.")
    assert CUICategory.EXPT in sig.keyword_categories


def test_baseline_misses_unmarked_semantic_cui():
    # No markings, no keywords — the legacy baseline sees nothing (the money case).
    text = "The propulsion test on the Vanguard program failed at 14:32."
    sig = run_deterministic(text)
    assert baseline_verdict(sig).verdict is Verdict.ALLOW


def test_baseline_blocks_classified_banner():
    sig = run_deterministic("Report is SECRET.")
    assert baseline_verdict(sig).verdict is Verdict.BLOCK
