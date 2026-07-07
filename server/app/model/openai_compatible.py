"""OpenAI-compatible model backend.

Shared by Fireworks (hosted Gemma, pre-GPU) and vLLM-local (self-hosted Gemma
on the AMD MI300X). Both expose `/v1/chat/completions`, so the only real
differences are base URL, auth, and how structured output is requested.

Robustness contract (see ModelClient.classify): this NEVER raises for ordinary
failures. Timeouts, connection errors, non-200s, and unparseable JSON all
resolve to ``ModelSignals(available=False)`` so the pipeline degrades cleanly.
"""

from __future__ import annotations

import json

import httpx

from ..logging_config import get_logger
from ..rules.prompt import (
    RESPONSE_JSON_SCHEMA,
    build_system_prompt,
    build_user_prompt,
)
from ..schemas import CUICategory, ClassificationLevel, ModelSignals, Span
from .base import ModelClient

log = get_logger(__name__)

_UNAVAILABLE = ModelSignals(available=False, rationale="Model backend unavailable.")


class OpenAICompatibleClient(ModelClient):
    name = "openai-compatible"

    def __init__(
        self,
        *,
        base_url: str,
        model_name: str,
        api_key: str | None = None,
        timeout_s: float = 45.0,
        use_guided_json: bool = False,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._use_guided_json = use_guided_json
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._http = httpx.AsyncClient(
            base_url=self._base_url, headers=headers, timeout=timeout_s
        )
        self._system = build_system_prompt()

    # ── transport ────────────────────────────────────────────
    def _payload(self, text: str) -> dict:
        payload: dict = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": self._system},
                {"role": "user", "content": build_user_prompt(text)},
            ],
            "temperature": 0.0,
            "max_tokens": 1024,
            # Both Fireworks and vLLM honour json_object; it's our floor.
            "response_format": {"type": "json_object"},
        }
        if self._use_guided_json:
            # vLLM: force the exact schema via guided decoding (xgrammar).
            payload["extra_body"] = {"guided_json": RESPONSE_JSON_SCHEMA}
            payload["guided_json"] = RESPONSE_JSON_SCHEMA  # some builds read top-level
        return payload

    async def classify(self, text: str) -> ModelSignals:
        try:
            resp = await self._http.post("/chat/completions", json=self._payload(text))
        except httpx.TimeoutException:
            log.warning("model timeout after configured budget")
            return _UNAVAILABLE
        except httpx.HTTPError as e:
            log.warning("model transport error: %s", e)
            return _UNAVAILABLE

        if resp.status_code != 200:
            log.warning("model HTTP %s: %s", resp.status_code, resp.text[:300])
            return _UNAVAILABLE

        try:
            content = resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            log.warning("unexpected model envelope: %s", e)
            return _UNAVAILABLE

        parsed = _loads_lenient(content)
        if parsed is None:
            log.warning("model returned unparseable JSON; degrading")
            return _UNAVAILABLE

        return _coerce_signals(parsed, text)

    async def health(self) -> bool:
        try:
            r = await self._http.get("/models")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    async def aclose(self) -> None:
        await self._http.aclose()


class FireworksClient(OpenAICompatibleClient):
    name = "fireworks"


class VLLMClient(OpenAICompatibleClient):
    name = "vllm-local"

    def __init__(self, **kw) -> None:
        kw.setdefault("use_guided_json", True)
        super().__init__(**kw)


# ─────────────────────────────────────────────────────────────
#  Parsing helpers — tolerate the messy reality of LLM output
# ─────────────────────────────────────────────────────────────
def _loads_lenient(content: str) -> dict | None:
    """Parse JSON, tolerating code fences and leading/trailing prose."""
    if not content:
        return None
    content = content.strip()
    # Strip ```json fences if present.
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Last resort: grab the outermost {...}.
        start, end = content.find("{"), content.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None


def _coerce_signals(data: dict, original_text: str) -> ModelSignals:
    """Validate/clamp a raw model dict into ModelSignals, defensively."""

    def _enum(cls, value, default):
        try:
            return cls(value)
        except (ValueError, KeyError):
            return default

    level = _enum(
        ClassificationLevel,
        data.get("classification_level"),
        ClassificationLevel.UNCLASSIFIED,
    )

    categories: list[CUICategory] = []
    for c in data.get("cui_categories", []) or []:
        cat = _enum(CUICategory, c, None)
        if cat and cat not in categories:
            categories.append(cat)

    spans: list[Span] = []
    for raw in data.get("offending_spans", []) or []:
        if not isinstance(raw, dict):
            continue
        span_text = str(raw.get("text", "")).strip()
        if not span_text:
            continue
        cat = _enum(CUICategory, raw.get("category"), None)
        start = original_text.find(span_text)
        spans.append(
            Span(
                text=span_text,
                category=cat,
                reason=str(raw.get("reason", "")) or None,
                start=start if start >= 0 else None,
                end=(start + len(span_text)) if start >= 0 else None,
            )
        )

    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    return ModelSignals(
        available=True,
        classification_level=level,
        cui_categories=categories,
        spillage_flag=bool(data.get("spillage_flag", bool(categories))),
        offending_spans=spans,
        rationale=str(data.get("rationale", "")).strip(),
        confidence=confidence,
    )
