"""End-to-end pipeline smoke tests against the mock backend."""

import pytest

from app.model.mock import MockModelClient
from app.pipeline import scan
from app.schemas import CUICategory, Verdict


@pytest.fixture
def client() -> MockModelClient:
    return MockModelClient()


async def test_money_case_unmarked_cui_blocks(client):
    """The demo's centrepiece: plain prose, no marking, no keyword →
    baseline says ALLOW, Spillguard says BLOCK."""
    text = "The propulsion test on the Vanguard program failed at 14:32 due to turbopump cavitation."
    result = await scan(text, client)

    assert result.verdict is Verdict.BLOCK
    assert CUICategory.CTI in result.cui_categories
    assert result.spillage_flag is True
    assert result.baseline.verdict is Verdict.ALLOW      # legacy DLP is fooled
    assert result.offending_spans                        # we show *why*
    assert result.engine == "mock"


async def test_clean_text_allows(client):
    result = await scan("Let's grab lunch at noon to plan the office picnic.", client)
    assert result.verdict is Verdict.ALLOW
    assert result.cui_categories == []
    assert result.baseline.verdict is Verdict.ALLOW


async def test_classified_banner_blocks(client):
    result = await scan("This assessment is SECRET and must be safeguarded.", client)
    assert result.verdict is Verdict.BLOCK


async def test_correctly_marked_cui_flags(client):
    text = "CUI//SP-CTI\nThe propulsion test on the Vanguard program failed at 14:32."
    result = await scan(text, client)
    assert result.verdict is Verdict.FLAG
    assert "CUI//SP-CTI" in result.portion_markings_found


async def test_ssn_is_caught(client):
    result = await scan("Contractor SSN: 123-45-6789 attached for onboarding.", client)
    assert result.verdict is Verdict.BLOCK
    assert CUICategory.PRVCY in result.cui_categories


async def test_latency_and_signals_present(client):
    result = await scan("hello world", client)
    assert result.latency_ms >= 0
    assert result.signals is not None
    assert result.signals.model.available is True
