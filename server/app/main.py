"""Spillguard HTTP application.

Wires the pipeline to FastAPI: lifespan-managed model client + audit log,
per-request correlation ids, defensive error handling, and (when present) the
built React bundle served at `/`.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import Settings, get_settings
from .egress import EgressStatus, get_egress_status
from .errors import EmptyInputError, InputTooLargeError, register_exception_handlers
from .extract import extract_text
from .logging_config import configure_logging, get_logger, request_id_var
from .model import build_model_client
from .pipeline import scan
from .schemas import AuditEntry, HealthResponse, ScanRequest, ScanResult
from .storage import AuditLog

log = get_logger(__name__)

# Built client bundle (copied here by the client build).
_STATIC_DIR = Path(__file__).parent / "ui" / "static"
# Eval report produced by eval/run_eval.py (feeds the UI accuracy tile).
_EVAL_REPORT = Path(__file__).parent.parent / "eval" / "report.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    log.info("Spillguard %s starting (backend=%s)", __version__, settings.model_backend)

    settings.require_backend_credentials()

    app.state.settings = settings
    app.state.client = build_model_client(settings)

    audit = AuditLog(settings.audit_db_path)
    audit.connect()
    app.state.audit = audit

    try:
        yield
    finally:
        await app.state.client.aclose()
        audit.close()
        log.info("Spillguard stopped cleanly")


app = FastAPI(
    title="Spillguard",
    version=__version__,
    summary="Inline, air-gapped CUI data-spillage guard.",
    lifespan=lifespan,
)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _correlation_id(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    token = request_id_var.set(rid)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    return response


# ── helpers ──────────────────────────────────────────────────
def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def _run_scan(request: Request, text: str) -> ScanResult:
    settings: Settings = request.app.state.settings
    if len(text) > settings.max_input_chars:
        raise InputTooLargeError(
            f"Input exceeds the {settings.max_input_chars:,}-character limit."
        )
    result = await scan(text, request.app.state.client)
    await request.app.state.audit.record(result, _hash(text))
    return result


# ── routes ───────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health(request: Request) -> HealthResponse:
    s = _settings(request)
    return HealthResponse(
        version=__version__,
        model_backend=s.model_backend,
        model_name=s.model_name,
    )


@app.get("/egress-status", response_model=EgressStatus, tags=["ops"])
async def egress_status(request: Request) -> EgressStatus:
    return get_egress_status(_settings(request))


@app.post("/scan", response_model=ScanResult, tags=["scan"])
async def scan_text(request: Request, body: ScanRequest) -> ScanResult:
    return await _run_scan(request, body.text)


@app.post("/scan/file", response_model=ScanResult, tags=["scan"])
async def scan_file(request: Request, file: UploadFile = File(...)) -> ScanResult:
    data = await file.read()
    if not data:
        raise EmptyInputError("Uploaded file is empty.")
    text = extract_text(file.filename or "", data)
    if not text.strip():
        raise EmptyInputError("No readable text found in the file.")
    return await _run_scan(request, text)


@app.get("/audit", response_model=list[AuditEntry], tags=["ops"])
async def audit(request: Request, limit: int = 50) -> list[AuditEntry]:
    return await request.app.state.audit.list(limit)


@app.get("/eval-report", tags=["ops"])
async def eval_report() -> JSONResponse:
    """The latest evaluation metrics. Returns {available: false} rather than an
    error when no report has been generated yet, so the UI can hide the tile."""
    if not _EVAL_REPORT.is_file():
        return JSONResponse({"available": False})
    try:
        data = json.loads(_EVAL_REPORT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        log.warning("could not read eval report: %s", e)
        return JSONResponse({"available": False})
    # Trim the heavy per-doc arrays; the tile only needs the headline numbers.
    data.pop("results", None)
    data["available"] = True
    return JSONResponse(data)


# ── static client (mounted only if the built bundle exists) ──
if _STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="ui")
    log.info("Serving client bundle from %s", _STATIC_DIR)
