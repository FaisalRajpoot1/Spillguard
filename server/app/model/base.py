"""The model-client contract.

Every backend returns the same `ModelSignals`. Callers never know or care
which one is running — that is what makes `mock → fireworks → vllm-local` a
one-env-var swap.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas import ModelSignals


class ModelClient(ABC):
    """Semantic classifier interface."""

    #: Human-readable backend id surfaced in ScanResult.engine
    name: str = "base"

    @abstractmethod
    async def classify(self, text: str) -> ModelSignals:
        """Return the model's assessment of `text`.

        Implementations MUST NOT raise for ordinary failures (timeouts, bad
        JSON, backend down). Instead return ``ModelSignals(available=False)``
        so the pipeline degrades to a deterministic verdict. Raising is
        reserved for genuinely exceptional programmer errors.
        """
        raise NotImplementedError

    async def health(self) -> bool:
        """Best-effort readiness check. Default: assume healthy."""
        return True

    async def aclose(self) -> None:
        """Release resources (HTTP pools, etc.). Default: no-op."""
        return None
