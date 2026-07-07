"""Application configuration.

Single source of truth for runtime settings, loaded from environment
variables (or a local `.env`). Validated at import time so the process
fails fast and loudly on misconfiguration rather than mid-request.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ModelBackend = Literal["mock", "fireworks", "vllm-local"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # `MODEL_*` env vars would otherwise collide with pydantic's protected
        # namespace; disable that guard since our domain legitimately uses it.
        protected_namespaces=(),
    )

    # ── App ──────────────────────────────────────────────
    app_env: Literal["dev", "prod"] = "dev"
    log_level: str = "INFO"

    # ── Model backend ────────────────────────────────────
    model_backend: ModelBackend = "mock"
    model_name: str = "google/gemma-3-12b-it"
    model_url: str | None = None

    fireworks_api_key: str | None = None
    hf_token: str | None = None

    # ── Tuning / limits ──────────────────────────────────
    request_timeout_s: float = Field(default=45.0, gt=0, le=300)
    max_input_chars: int = Field(default=50_000, gt=0, le=1_000_000)
    audit_db_path: str = "data/audit.db"

    # ── CORS ─────────────────────────────────────────────
    # NoDecode stops pydantic-settings from JSON-decoding the env value, so a
    # plain comma-separated string is handled by the validator below instead.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        """Accept a comma-separated string from the environment."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, v: str) -> str:
        level = v.upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}, got {v!r}")
        return level

    def require_backend_credentials(self) -> None:
        """Fail fast if the selected backend is missing what it needs.

        Called during startup (not import) so unit tests using `mock`
        never trip on absent cloud credentials.
        """
        if self.model_backend == "fireworks" and not self.fireworks_api_key:
            raise RuntimeError(
                "MODEL_BACKEND=fireworks but FIREWORKS_API_KEY is not set."
            )
        if self.model_backend == "vllm-local" and not self.model_url:
            raise RuntimeError(
                "MODEL_BACKEND=vllm-local but MODEL_URL is not set "
                "(e.g. http://gemma-vllm:8000/v1)."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton. Patch-friendly for tests via cache_clear()."""
    return Settings()
