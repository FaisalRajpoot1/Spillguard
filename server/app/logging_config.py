"""Structured-ish logging setup.

Keeps things dependency-free (stdlib logging) but gives every log line a
consistent, greppable shape. A per-request correlation id is attached via
a context filter so pipeline logs can be traced end-to-end.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

# Correlation id for the current request; set by middleware, read by the filter.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Idempotently configure root logging. Safe to call more than once."""
    global _CONFIGURED
    if _CONFIGURED:
        logging.getLogger().setLevel(level)
        return

    # Force UTF-8 on the console so non-ASCII in messages/data never crashes a
    # log write (Windows defaults to cp1252). Guarded: not all streams support it.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    handler.addFilter(_RequestIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet noisy third-party loggers.
    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
