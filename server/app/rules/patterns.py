"""Deterministic detection patterns.

Two audiences:

  * The **deterministic pipeline stage** (also our "old DLP" baseline) uses the
    obvious, literal signals — explicit markings, SSNs, unambiguous keywords.
    It is intentionally shallow: that is the *point* of the side-by-side demo.

  * The **mock model client** uses `SEMANTIC_INDICATORS` to *simulate* what
    Gemma understands — sensitive meaning expressed in plain prose with no
    obvious keyword. This is what lets the "money case" demo work offline.

Keeping the keyword lists deliberately narrow ensures the semantic layer has
something real to catch that the baseline misses.
"""

from __future__ import annotations

import re
from re import Pattern

from ..schemas import CUICategory

# ── Portion / banner markings: CUI, CUI//SP-CTI, etc. ─────────
MARKING_RE: Pattern[str] = re.compile(r"\bCUI(?://SP-[A-Z]{2,8})?\b")

# ── Classified banners (case-sensitive to avoid "confidential" noise) ──
# Matches uppercase SECRET / TOP SECRET, optionally in a //SECRET// banner.
CLASSIFIED_RE: Pattern[str] = re.compile(r"(?:\bTOP SECRET\b|\bSECRET\b|//\s*SECRET)")

# ── US SSN ────────────────────────────────────────────────────
SSN_RE: Pattern[str] = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# ── Narrow, unambiguous keyword lists (the "dumb guard") ──────
KEYWORD_LISTS: dict[CUICategory, tuple[str, ...]] = {
    CUICategory.EXPT: ("itar", "ear-controlled", "export controlled", "export-controlled", "usml"),
    CUICategory.PROCURE: ("source selection", "source-selection", "bid pricing", "proposal pricing"),
    CUICategory.LEI: ("confidential informant", "ongoing investigation", "law enforcement sensitive"),
    CUICategory.PRVCY: ("social security number", "ssn:"),
    # CTI is intentionally sparse here so the semantic layer earns its keep.
    CUICategory.CTI: ("cui//sp-cti",),
}


def find_portion_markings(text: str) -> list[str]:
    """Distinct CUI markings present in the text, in order of appearance."""
    seen: dict[str, None] = {}
    for m in MARKING_RE.finditer(text):
        seen.setdefault(m.group(0), None)
    return list(seen)


def find_classified_banner(text: str) -> str | None:
    m = CLASSIFIED_RE.search(text)
    return m.group(0).strip("/ ").upper() if m else None


def count_ssns(text: str) -> int:
    return len(SSN_RE.findall(text))


def keyword_category_hits(text: str) -> dict[CUICategory, list[str]]:
    """Which narrow keywords fired, grouped by category (case-insensitive)."""
    low = text.lower()
    hits: dict[CUICategory, list[str]] = {}
    for cat, words in KEYWORD_LISTS.items():
        found = [w for w in words if w in low]
        if found:
            hits[cat] = found
    return hits


# ─────────────────────────────────────────────────────────────
#  SEMANTIC INDICATORS — used ONLY by the mock model client to
#  emulate Gemma. Each entry = (compiled regex, category, reason).
#  These express *meaning*, not keywords, so the deterministic
#  baseline misses them and the "smart" layer catches them.
# ─────────────────────────────────────────────────────────────
def _c(rx: str) -> Pattern[str]:
    return re.compile(rx, re.IGNORECASE)


SEMANTIC_INDICATORS: list[tuple[Pattern[str], CUICategory, str]] = [
    (
        _c(r"\b(propulsion|thrust|turbopump|engine|guidance|warhead|radar[- ]cross[- ]section|avionics)\b"
           r".{0,80}?\b(tests?|trials?|failed|failures?|anomal(?:y|ies)|results?|measurements?|yields?|performance|data)\b"),
        CUICategory.CTI,
        "Describes technical performance/test data of a defense system.",
    ),
    (
        _c(r"\bprogram\b.{0,60}?\b(test|flight|trial)\b.{0,40}?\b(fail|failed|failure|anomaly|abort)\b"),
        CUICategory.CTI,
        "Reveals a named program's test outcome — controlled technical information.",
    ),
    (
        _c(r"\b(range|accuracy|payload|thrust|yield)\b.{0,30}?\b(of|for|was|is)\b.{0,30}?\b\d"),
        CUICategory.CTI,
        "Quantitative performance parameter of a defense system.",
    ),
    (
        _c(r"\b(evaluat\w+|scored|ranked|preferred|selected)\b.{0,50}?\b(bid|proposal|offerors?|vendor|contractor|pricing)\b"),
        CUICategory.PROCURE,
        "Discloses source-selection reasoning before award.",
    ),
    (
        _c(r"\b(informant|source)\b.{0,40}?\b(identity|name|is|was)\b"),
        CUICategory.LEI,
        "May reveal a confidential source identity.",
    ),
    (
        _c(r"\b(exported|shipped|transferred)\b.{0,40}?\b(without|no)\b.{0,20}?\b(license|authorization)\b"),
        CUICategory.EXPT,
        "Implies an export-controlled transfer.",
    ),
]
