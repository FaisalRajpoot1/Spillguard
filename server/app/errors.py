"""Domain error types and FastAPI exception handlers.

The guiding principle: a scan request must *never* crash into an opaque 500.
Every failure mode maps to a typed error with a stable machine code and a
human message, and — critically — model/infra failures degrade to a
deterministic verdict instead of erroring out (handled in the pipeline, not
here). These handlers cover the residual, truly-exceptional cases.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from .logging_config import get_logger

log = get_logger(__name__)


class SpillguardError(Exception):
    """Base class for all domain errors. Carries a stable code + HTTP status."""

    code: str = "internal_error"
    http_status: int = 500

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {"error": self.code, "message": self.message}
        if self.detail:
            payload["detail"] = self.detail
        return payload


class InputTooLargeError(SpillguardError):
    code = "input_too_large"
    http_status = 413


class EmptyInputError(SpillguardError):
    code = "empty_input"
    http_status = 422


class UnsupportedFileTypeError(SpillguardError):
    code = "unsupported_file_type"
    http_status = 415


class FileExtractionError(SpillguardError):
    code = "file_extraction_failed"
    http_status = 422


class ModelBackendError(SpillguardError):
    """Raised by model clients. The pipeline catches this and degrades;
    it should rarely surface to the HTTP layer."""

    code = "model_backend_error"
    http_status = 502


def register_exception_handlers(app) -> None:  # noqa: ANN001 (FastAPI app)
    from fastapi.encoders import jsonable_encoder
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(SpillguardError)
    async def _handle_domain(_: Request, exc: SpillguardError) -> JSONResponse:
        # 5xx are worth a stack trace; 4xx are client problems, log quietly.
        if exc.http_status >= 500:
            log.exception("Domain error [%s]: %s", exc.code, exc.message)
        else:
            log.info("Client error [%s]: %s", exc.code, exc.message)
        return JSONResponse(status_code=exc.http_status, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # exc.errors() can embed a raw ValueError in `ctx`; jsonable_encoder
        # coerces those to strings so the response is always serializable.
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Request body failed validation.",
                "detail": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(Exception)
    async def _handle_uncaught(_: Request, exc: Exception) -> JSONResponse:
        log.exception("Uncaught exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred.",
            },
        )
