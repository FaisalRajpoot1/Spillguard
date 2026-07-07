"""Model warm-up / readiness probe.

Run after `docker compose up` (especially on the AMD MI300X) to force the
self-hosted Gemma to load its weights and compile CUDA/HIP graphs before the
first real request — so the live demo's first scan is fast, not a cold-start.

It sends one trivial classification through the configured backend, reports
latency, and exits non-zero if the model is unreachable (useful in a
healthcheck or CI gate).

Usage (from the server/ directory):
    python scripts/warmup.py
    python scripts/warmup.py --retries 30 --delay 5    # wait for a slow GPU boot
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SERVER_DIR))

from app.config import get_settings          # noqa: E402
from app.model.factory import build_model_client  # noqa: E402

_PROBE = "System check: this is a warm-up probe with no sensitive content."


async def _warm_once() -> tuple[bool, float, str]:
    settings = get_settings()
    client = build_model_client(settings)
    start = time.perf_counter()
    try:
        signals = await client.classify(_PROBE)
    finally:
        await client.aclose()
    elapsed = time.perf_counter() - start
    return signals.available, elapsed, client.name


async def main_async(retries: int, delay: float) -> int:
    settings = get_settings()
    print(f"Warming backend '{settings.model_backend}' (model {settings.model_name})…")

    for attempt in range(1, retries + 1):
        try:
            ok, elapsed, name = await _warm_once()
        except Exception as e:  # noqa: BLE001
            ok, elapsed, name, err = False, 0.0, settings.model_backend, str(e)
        else:
            err = ""

        if ok:
            print(f"  [{name}] ready in {elapsed * 1000:.0f} ms (attempt {attempt}/{retries}).")
            return 0

        reason = err or "backend reported unavailable"
        print(f"  attempt {attempt}/{retries}: not ready ({reason})")
        if attempt < retries:
            await asyncio.sleep(delay)

    print("Model did not become ready in time.", file=sys.stderr)
    return 1


def main() -> None:
    ap = argparse.ArgumentParser(description="Warm up / probe the model backend.")
    ap.add_argument("--retries", type=int, default=1, help="attempts before giving up")
    ap.add_argument("--delay", type=float, default=5.0, help="seconds between attempts")
    args = ap.parse_args()
    raise SystemExit(asyncio.run(main_async(args.retries, args.delay)))


if __name__ == "__main__":
    main()
