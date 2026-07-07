"""Stage 2 — semantic scan (the AI layer).

A thin, defensive wrapper around the model client. The client already returns
``ModelSignals(available=False)`` on ordinary failures; this belt-and-braces
guard also converts any *unexpected* exception into a degrade instead of a 500,
because a spillage guard must always render a verdict.
"""

from __future__ import annotations

from ..logging_config import get_logger
from ..model.base import ModelClient
from ..schemas import ModelSignals

log = get_logger(__name__)


async def run_semantic(text: str, client: ModelClient) -> ModelSignals:
    try:
        signals = await client.classify(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never let the model crash a scan
        log.exception("semantic stage crashed, degrading to deterministic: %s", e)
        return ModelSignals(available=False, rationale="Model stage error; degraded.")

    if not signals.available:
        log.info("semantic stage unavailable; running degraded")
    return signals
