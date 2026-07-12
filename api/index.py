"""Vercel serverless entry point for Spillguard.

Vercel hosts static sites + Python functions, not Docker containers. This thin
adapter exposes the existing FastAPI app as an ASGI function; `vercel.json`
routes every request here, so the app serves its React UI + JSON API exactly as
it does locally — no code changes to the product itself.
"""
import os
import sys
from pathlib import Path

# Make the server package importable: repo_root/server/app/...
_SERVER = Path(__file__).resolve().parent.parent / "server"
sys.path.insert(0, str(_SERVER))

# Serverless has no GPU, so run the offline mock backend. The audit DB lives in
# /tmp (the only writable path on Vercel) and is non-fatal if unavailable.
os.environ.setdefault("MODEL_BACKEND", "mock")
os.environ.setdefault("AUDIT_DB_PATH", "/tmp/spillguard-audit.db")

from app.main import app  # noqa: E402  — sys.path is configured above

# Vercel's @vercel/python runtime detects and serves this ASGI `app`.
