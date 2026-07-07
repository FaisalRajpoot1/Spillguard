"""Swappable model backends. One interface (`ModelClient`), three
implementations selected by MODEL_BACKEND: mock | fireworks | vllm-local."""

from .base import ModelClient
from .factory import build_model_client

__all__ = ["ModelClient", "build_model_client"]
