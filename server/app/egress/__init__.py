"""Egress monitor — the demo's proof that the model never phones home."""

from .monitor import EgressStatus, get_egress_status

__all__ = ["EgressStatus", "get_egress_status"]
