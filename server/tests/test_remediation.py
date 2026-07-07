"""Auto-remediation logic + endpoint."""

from app.pipeline.remediation import remediate
from app.schemas import ClassificationLevel, CUICategory


def test_redacts_ssn_and_marks_privacy():
    r = remediate("Contractor SSN: 123-45-6789 for payroll.", [CUICategory.PRVCY], ClassificationLevel.CUI_SP)
    assert r.fixable
    assert "123-45-6789" not in r.remediated_text
    assert "[SSN REDACTED]" in r.remediated_text
    # Value redacted AND the document labelled privacy-controlled.
    assert r.remediated_text.startswith("CUI//SP-PRVCY")


def test_adds_marking_for_unmarked_cti():
    r = remediate("The propulsion test on the Vanguard program failed.", [CUICategory.CTI], ClassificationLevel.CUI_SP)
    assert r.fixable
    assert r.remediated_text.startswith("CUI//SP-CTI")
    assert any("marking" in c.lower() for c in r.changes)


def test_cti_plus_ssn_redacts_and_marks():
    r = remediate(
        "SSN 123-45-6789. The propulsion test on the Vanguard program failed.",
        [CUICategory.CTI, CUICategory.PRVCY],
        ClassificationLevel.CUI_SP,
    )
    assert r.fixable
    assert "[SSN REDACTED]" in r.remediated_text
    assert r.remediated_text.startswith("CUI//SP-CTI")


def test_classified_is_not_fixable():
    r = remediate("SECRET//NOFORN\nAdversary capabilities.", [], ClassificationLevel.CLASSIFIED)
    assert not r.fixable
    assert "classified" in r.note.lower()


def test_nothing_to_fix():
    r = remediate("Lunch at noon in the break room.", [], ClassificationLevel.UNCLASSIFIED)
    assert not r.fixable


def test_remediate_endpoint_improves_verdict():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        body = {
            "text": "Contractor SSN: 123-45-6789 for payroll setup.",
            "cui_categories": ["PRVCY"],
            "classification_level": "CUI//SP",
        }
        r = c.post("/remediate", json=body).json()
        assert r["fixable"] is True
        assert "[SSN REDACTED]" in r["remediated_text"]
        # After redaction the re-scan should no longer be a hard BLOCK.
        assert r["result"]["verdict"] in ("ALLOW", "FLAG")
