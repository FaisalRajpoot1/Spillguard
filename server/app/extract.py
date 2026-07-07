"""Text extraction for uploaded files (used by POST /scan/file).

Supports plain text and PDF. Everything else is rejected with a clear error
rather than silently mis-handled.
"""

from __future__ import annotations

import io

from .errors import FileExtractionError, UnsupportedFileTypeError
from .logging_config import get_logger

log = get_logger(__name__)

_TEXT_EXTS = {".txt", ".md", ".log", ".csv", ".json"}


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()

    if any(name.endswith(ext) for ext in _TEXT_EXTS) or not name:
        try:
            return data.decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            raise FileExtractionError("Could not decode text file.", detail=str(e)) from e

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError as e:  # pragma: no cover
            raise FileExtractionError("PDF support not installed.") from e
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
        except Exception as e:  # noqa: BLE001
            raise FileExtractionError("Failed to read PDF.", detail=str(e)) from e
        if not text:
            raise FileExtractionError(
                "PDF contained no extractable text (scanned image?). "
                "Vision support is a roadmap item."
            )
        return text

    raise UnsupportedFileTypeError(
        f"Unsupported file type: {filename!r}. Supported: .txt .md .log .csv .json .pdf"
    )
