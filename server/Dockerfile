# ── Spillguard image (multi-stage) ────────────────────────────
# Stage 1 builds the React client; stage 2 is the slim Python app
# with the built UI bundled in, so `docker compose up` serves the
# FULL product (UI + API) from a clean clone — no local build step.
#
# NOTE: build context is the REPO ROOT (see docker-compose.yml),
# so this Dockerfile can see both ./client and ./server.
# ──────────────────────────────────────────────────────────────

# ---- Stage 1: build the React client ----
FROM node:20-slim AS client
WORKDIR /build/client
# Install deps first (layer caching)
COPY client/package.json client/package-lock.json ./
RUN npm ci
# Build — vite.config outputs to ../server/app/ui/static,
# i.e. /build/server/app/ui/static inside this stage.
COPY client/ ./
RUN npm run build

# ---- Stage 2: the Python app ----
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first (layer caching)
COPY server/requirements.txt .
RUN pip install -r requirements.txt

# App source + eval (report.json feeds the UI accuracy tile; the dataset
# lets a judge re-run the evaluation inside the container).
COPY server/app ./app
COPY server/eval ./eval

# The built UI bundle from stage 1 → served by FastAPI at "/".
COPY --from=client /build/server/app/ui/static ./app/ui/static

# Runtime data dir (audit db) — mounted as a volume in compose
RUN mkdir -p /app/data && adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Bind to the host-provided $PORT (Render/HF/etc.), defaulting to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
