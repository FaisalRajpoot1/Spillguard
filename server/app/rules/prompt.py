"""The rules-in-context prompt handed to Gemma, plus the JSON schema used for
guided decoding. Holding the full ruleset in the prompt (no fine-tuning) is
exactly what the MI300X's large memory makes practical.
"""

from __future__ import annotations

from .cui_categories import CATEGORY_INFO

# JSON schema enforced by vLLM guided decoding (xgrammar). Mirrors ModelSignals.
RESPONSE_JSON_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "classification_level": {
            "type": "string",
            "enum": ["UNCLASSIFIED", "CUI", "CUI//SP", "CLASSIFIED"],
        },
        "cui_categories": {
            "type": "array",
            "items": {"type": "string", "enum": ["CTI", "PRVCY", "EXPT", "PROCURE", "LEI"]},
        },
        "spillage_flag": {"type": "boolean"},
        "offending_spans": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "text": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["CTI", "PRVCY", "EXPT", "PROCURE", "LEI"],
                    },
                    "reason": {"type": "string"},
                },
                "required": ["text", "reason"],
            },
        },
        "rationale": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "classification_level",
        "cui_categories",
        "spillage_flag",
        "offending_spans",
        "rationale",
        "confidence",
    ],
}


def _category_reference() -> str:
    lines = []
    for info in CATEGORY_INFO.values():
        lines.append(f"- {info.category.value} ({info.name}, marking {info.marking}): {info.description}")
    return "\n".join(lines)


def build_system_prompt() -> str:
    return f"""You are Spillguard, a data-spillage inspector for a U.S. defense enclave.
Your job: decide whether a document contains Controlled Unclassified Information
(CUI) and whether it is a spillage risk if it left the enclave.

Judge the MEANING of the text, not just keywords. Sensitive content is often
written in plain prose with no label — that is exactly what you must catch.

CUI categories you recognise:
{_category_reference()}

Rules:
- classification_level is UNCLASSIFIED, CUI, CUI//SP (CUI with a specific
  category), or CLASSIFIED (only if the text itself is classified national
  security information — be conservative; when unsure use CUI or CUI//SP).
- List every applicable CUI category in cui_categories.
- offending_spans: quote the exact sentence(s) that carry the sensitivity, each
  with a short reason. Quote verbatim from the document.
- spillage_flag = true if this content would be a spillage were it to leave the
  enclave unmarked or to an unauthorised destination.
- confidence: your calibrated 0-1 confidence in this assessment.
- Respond with JSON ONLY, matching the required schema. No prose outside JSON.
"""


def build_user_prompt(text: str) -> str:
    return f"Inspect the following document and return your JSON assessment.\n\n---\n{text}\n---"
