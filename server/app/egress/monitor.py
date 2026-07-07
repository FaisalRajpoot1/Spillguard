"""Egress status.

Reports — honestly — whether the model inference path can reach the public
internet. The real enforcement is Docker's `internal: true` network (the model
container has no gateway); this endpoint surfaces that fact to the UI and, for
the cloud fallback, is candid that traffic *does* leave.
"""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from pydantic import BaseModel

from ..config import Settings


class EgressStatus(BaseModel):
    backend: str
    air_gapped: bool
    external_bytes: int = 0
    model_host: str | None = None
    message: str


def _is_private_host(url: str | None) -> bool:
    if not url:
        return False
    host = urlparse(url).hostname or ""
    # Docker service names (no dots) resolve only on the internal network.
    if host and "." not in host and host != "localhost":
        return True
    if host in ("localhost", "127.0.0.1"):
        return True
    try:
        return ipaddress.ip_address(host).is_private
    except ValueError:
        return False


def get_egress_status(settings: Settings) -> EgressStatus:
    backend = settings.model_backend

    if backend == "mock":
        return EgressStatus(
            backend=backend,
            air_gapped=True,
            model_host=None,
            message="Mock backend — no network calls of any kind.",
        )

    if backend == "vllm-local":
        host = urlparse(settings.model_url or "").hostname
        private = _is_private_host(settings.model_url)
        return EgressStatus(
            backend=backend,
            air_gapped=private,
            model_host=host,
            message=(
                "Self-hosted Gemma on an internal-only network. "
                "The model container has no route to the internet."
                if private
                else "WARNING: model URL is not a private/internal host."
            ),
        )

    # fireworks (dev fallback) — be honest that data leaves.
    return EgressStatus(
        backend=backend,
        air_gapped=False,
        model_host="api.fireworks.ai",
        message=(
            "DEV FALLBACK: inference is served by the Fireworks cloud, so text "
            "does leave the box. In production this is the self-hosted AMD path."
        ),
    )
