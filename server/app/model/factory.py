"""Backend factory — turns settings into a concrete ModelClient."""

from __future__ import annotations

from ..config import Settings
from ..logging_config import get_logger
from .base import ModelClient
from .mock import MockModelClient
from .openai_compatible import FireworksClient, VLLMClient

log = get_logger(__name__)

# Fireworks' OpenAI-compatible base URL for Gemma models.
_FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"


def build_model_client(settings: Settings) -> ModelClient:
    backend = settings.model_backend
    log.info("Initialising model backend: %s (%s)", backend, settings.model_name)

    if backend == "mock":
        return MockModelClient()

    if backend == "fireworks":
        return FireworksClient(
            base_url=settings.model_url or _FIREWORKS_BASE_URL,
            model_name=settings.model_name,
            api_key=settings.fireworks_api_key,
            timeout_s=settings.request_timeout_s,
        )

    if backend == "vllm-local":
        # settings.model_url is validated non-None at startup for this backend.
        return VLLMClient(
            base_url=settings.model_url or "http://gemma-vllm:8000/v1",
            model_name=settings.model_name,
            api_key=None,  # self-hosted, no auth
            timeout_s=settings.request_timeout_s,
        )

    # Unreachable given the Literal type, but fail loud if it ever happens.
    raise ValueError(f"Unknown MODEL_BACKEND: {backend!r}")
