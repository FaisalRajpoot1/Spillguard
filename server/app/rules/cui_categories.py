"""CUI category definitions (a scoped slice of the CUI Registry).

Kept deliberately small — 5 high-signal categories — per the build plan.
Each entry carries the canonical portion marking and a plain-English
description used both in the Gemma prompt and in UI tooltips.

Marking format reference (DoDI 5200.48):
    CUI//SP-<CATEGORY>      e.g. CUI//SP-CTI
    CUI                     basic CUI, no specified category
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schemas import CUICategory


@dataclass(frozen=True)
class CategoryInfo:
    category: CUICategory
    name: str
    marking: str          # canonical portion marking for this category
    description: str
    examples: tuple[str, ...]


CATEGORY_INFO: dict[CUICategory, CategoryInfo] = {
    CUICategory.CTI: CategoryInfo(
        category=CUICategory.CTI,
        name="Controlled Technical Information",
        marking="CUI//SP-CTI",
        description=(
            "Technical data with military or space application whose export is "
            "controlled — designs, test results, performance data, engineering "
            "specifications of defense systems."
        ),
        examples=(
            "propulsion test results for a named program",
            "radar cross-section measurements",
            "failure analysis of a weapons subsystem",
        ),
    ),
    CUICategory.PRVCY: CategoryInfo(
        category=CUICategory.PRVCY,
        name="Privacy / PII",
        marking="CUI//SP-PRVCY",
        description=(
            "Personally identifiable information — SSN, DoB, home address, "
            "medical or financial records tied to an individual."
        ),
        examples=("social security numbers", "personnel medical records"),
    ),
    CUICategory.EXPT: CategoryInfo(
        category=CUICategory.EXPT,
        name="Export Controlled (ITAR/EAR)",
        marking="CUI//SP-EXPT",
        description=(
            "Information controlled under ITAR or EAR — defense articles, "
            "munitions-list technology, dual-use items restricted for export."
        ),
        examples=("ITAR-controlled component specifications", "USML technical data"),
    ),
    CUICategory.PROCURE: CategoryInfo(
        category=CUICategory.PROCURE,
        name="Procurement / Acquisition Sensitive",
        marking="CUI//SP-PROCURE",
        description=(
            "Source-selection or acquisition information — pre-award pricing, "
            "bid evaluations, contractor proposals whose disclosure would harm "
            "the integrity of a procurement."
        ),
        examples=("source-selection evaluation notes", "competitor bid pricing"),
    ),
    CUICategory.LEI: CategoryInfo(
        category=CUICategory.LEI,
        name="Law Enforcement Information",
        marking="CUI//SP-LEI",
        description=(
            "Law-enforcement-sensitive material — investigation details, "
            "informant identities, techniques and procedures."
        ),
        examples=("ongoing investigation details", "confidential informant identity"),
    ),
}


def marking_for(category: CUICategory) -> str:
    return CATEGORY_INFO[category].marking


def expected_markings(categories: list[CUICategory]) -> list[str]:
    """The portion markings a document with these categories *should* carry."""
    # De-dupe while preserving order.
    seen: dict[str, None] = {}
    for c in categories:
        seen.setdefault(marking_for(c), None)
    return list(seen)
