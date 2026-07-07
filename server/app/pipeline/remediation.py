"""Auto-remediation.

Spillguard doesn't just detect a spillage — it can *fix* it. Given a document
and the CUI categories found in it, this produces a compliant version:

  * redacts PII (SSNs) so the sensitive value is gone, and
  * prepends the correct CUI portion marking(s) for the remaining categories.

The remediated text is then re-scanned so the UI can show an honest before/after
(e.g. BLOCK -> ALLOW after redaction, or BLOCK -> FLAG once correctly marked).

Classified content is deliberately NOT auto-fixable — you cannot "mark" your way
out of classified material; it must be removed or routed to a security officer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..rules.cui_categories import expected_markings
from ..rules.patterns import SSN_RE, count_ssns, find_portion_markings
from ..schemas import ClassificationLevel, CUICategory

_SSN_REDACTION = "[SSN REDACTED]"


@dataclass
class RemediationResult:
    fixable: bool
    remediated_text: str
    changes: list[str] = field(default_factory=list)
    note: str = ""


def remediate(
    text: str,
    categories: list[CUICategory],
    classification_level: ClassificationLevel,
) -> RemediationResult:
    # Classified material cannot be auto-remediated.
    if classification_level == ClassificationLevel.CLASSIFIED:
        return RemediationResult(
            fixable=False,
            remediated_text=text,
            note=(
                "This document contains classified material. It cannot be "
                "auto-remediated — remove the classified content or route it to "
                "your security officer."
            ),
        )

    new_text = text
    changes: list[str] = []

    # 1) Redact SSNs (removes the PII value entirely).
    ssn_count = count_ssns(new_text)
    if ssn_count:
        new_text = SSN_RE.sub(_SSN_REDACTION, new_text)
        changes.append(f"Redacted {ssn_count} SSN{'s' if ssn_count > 1 else ''}")

    # 2) Apply the correct portion marking(s) for every detected category, so a
    #    document that still *references* sensitive material is properly labelled
    #    (redacting a value doesn't erase that the document is about CUI).
    marking_categories = _dedupe(categories)
    existing = find_portion_markings(new_text)
    to_add = [m for m in expected_markings(marking_categories) if m not in existing]
    if to_add:
        banner = "\n".join(to_add)
        new_text = f"{banner}\n{new_text}"
        changes.append("Added portion marking: " + ", ".join(to_add))

    if not changes:
        return RemediationResult(
            fixable=False,
            remediated_text=text,
            note="Nothing to auto-remediate on this document.",
        )

    return RemediationResult(fixable=True, remediated_text=new_text, changes=changes)


def _dedupe(items: list[CUICategory]) -> list[CUICategory]:
    seen: list[CUICategory] = []
    for i in items:
        if i not in seen:
            seen.append(i)
    return seen
