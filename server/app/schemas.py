"""The data contract.

These models are the stable interface shared by the pipeline, the model
clients, the HTTP layer, the audit log, and the React client. Everything
speaks `ScanResult`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────
#  Enumerations
# ─────────────────────────────────────────────────────────────
class Verdict(str, Enum):
    ALLOW = "ALLOW"          # 🟢 clean — safe to send
    FLAG = "FLAG"            # 🟡 sensitive but recoverable (e.g. marking issue)
    BLOCK = "BLOCK"          # 🔴 must not leave


class ClassificationLevel(str, Enum):
    UNCLASSIFIED = "UNCLASSIFIED"
    CUI = "CUI"              # Controlled Unclassified Information (basic)
    CUI_SP = "CUI//SP"       # CUI with a specified category
    CLASSIFIED = "CLASSIFIED"  # a literal classified banner was detected


class CUICategory(str, Enum):
    """The scoped set we handle (a slice of the CUI Registry)."""

    CTI = "CTI"              # Controlled Technical Information
    PRVCY = "PRVCY"          # Privacy / PII
    EXPT = "EXPT"            # Export-controlled (ITAR / EAR)
    PROCURE = "PROCURE"      # Procurement / acquisition sensitive
    LEI = "LEI"              # Law-enforcement information


# ─────────────────────────────────────────────────────────────
#  Request
# ─────────────────────────────────────────────────────────────
class ScanRequest(BaseModel):
    text: str = Field(..., description="The document text to inspect.")
    source: str | None = Field(
        default=None,
        description="Optional label for the outbound channel (email, upload, …).",
        max_length=200,
    )

    @field_validator("text")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        # Trailing/leading whitespace is fine, but an all-whitespace body is not
        # a document. Emptiness is enforced here *and* re-checked in the route so
        # both JSON and file paths are covered.
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v


# ─────────────────────────────────────────────────────────────
#  Signals (evidence gathered per stage)
# ─────────────────────────────────────────────────────────────
class Span(BaseModel):
    """A specific offending fragment, with best-effort character offsets."""

    text: str
    category: CUICategory | None = None
    reason: str | None = None
    start: int | None = None
    end: int | None = None


class DeterministicSignals(BaseModel):
    banner_markings: list[str] = Field(default_factory=list)   # CUI//SP-CTI, …
    classified_banner: str | None = None                       # SECRET, TOP SECRET …
    keyword_categories: list[CUICategory] = Field(default_factory=list)
    ssn_hits: int = 0
    matched_rules: list[str] = Field(default_factory=list)     # human-readable


class ModelSignals(BaseModel):
    """What the semantic (Gemma) stage returned. `available=False` means the
    model was unreachable/invalid and the verdict is running degraded."""

    available: bool = True
    classification_level: ClassificationLevel = ClassificationLevel.UNCLASSIFIED
    cui_categories: list[CUICategory] = Field(default_factory=list)
    spillage_flag: bool = False
    offending_spans: list[Span] = Field(default_factory=list)
    rationale: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Signals(BaseModel):
    deterministic: DeterministicSignals
    model: ModelSignals


# ─────────────────────────────────────────────────────────────
#  Baseline (the "old DLP" side-by-side comparison)
# ─────────────────────────────────────────────────────────────
class BaselineResult(BaseModel):
    """A naive regex/keyword DLP verdict — what legacy tools would say.
    Included in every response so the UI can show the contrast in one call."""

    verdict: Verdict
    matched_rules: list[str] = Field(default_factory=list)
    note: str = ""


# ─────────────────────────────────────────────────────────────
#  Response
# ─────────────────────────────────────────────────────────────
class ScanResult(BaseModel):
    verdict: Verdict
    classification_level: ClassificationLevel
    cui_categories: list[CUICategory] = Field(default_factory=list)

    portion_markings_found: list[str] = Field(default_factory=list)
    portion_markings_expected: list[str] = Field(default_factory=list)
    marking_mismatch: bool = False
    spillage_flag: bool = False

    offending_spans: list[Span] = Field(default_factory=list)
    rationale: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    engine: str = "mock"          # which model backend produced this
    degraded: bool = False        # model unavailable → deterministic-only
    latency_ms: int = 0

    baseline: BaselineResult
    signals: Signals | None = None  # full evidence (omit-able for slim responses)


class RemediateRequest(BaseModel):
    text: str
    cui_categories: list[CUICategory] = Field(default_factory=list)
    classification_level: ClassificationLevel = ClassificationLevel.UNCLASSIFIED

    @field_validator("text")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v


class RemediateResponse(BaseModel):
    fixable: bool
    note: str = ""
    remediated_text: str
    changes: list[str] = Field(default_factory=list)
    result: ScanResult | None = None  # re-scan of the remediated text ("after")


class AuditEntry(BaseModel):
    id: int
    ts: str
    doc_hash: str
    verdict: Verdict
    classification_level: ClassificationLevel
    cui_categories: list[CUICategory]
    engine: str
    degraded: bool
    latency_ms: int


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    model_backend: str
    model_name: str
    degraded_ready: bool = True  # deterministic path always works
