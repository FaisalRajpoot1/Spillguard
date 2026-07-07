# ── Spillguard app image ──────────────────────────────────────
# Slim, non-root, healthcheck-friendly. Serves the pre-built
# React bundle (client/dist copied in at build time) + the API.
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first (layer caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# App source + eval (report.json feeds the UI accuracy tile; dataset lets a
# judge re-run the evaluation inside the container).
COPY app ./app
COPY eval ./eval

# The built client bundle is expected at ./app/ui/static when present.
# (Day 3: `npm run build` in ../client, copy dist → server/app/ui/static.)

# Runtime data dir (audit db) — mounted as a volume in compose
RUN mkdir -p /app/data && \
    adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
