"""SQLite audit log.

Append-only, hash-only. SQLite calls are synchronous but fast; they are pushed
to a worker thread (`asyncio.to_thread`) so they never block the event loop.
A single connection with a lock keeps writes serialised and safe.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from ..logging_config import get_logger
from ..schemas import AuditEntry, ScanResult

log = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                   TEXT NOT NULL,
    doc_hash             TEXT NOT NULL,
    verdict              TEXT NOT NULL,
    classification_level TEXT NOT NULL,
    cui_categories       TEXT NOT NULL,   -- JSON array
    engine               TEXT NOT NULL,
    degraded             INTEGER NOT NULL,
    latency_ms           INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit (ts DESC);
"""


class AuditLog:
    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path)
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None

    # ── lifecycle ────────────────────────────────────────────
    def connect(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            self._path, check_same_thread=False, isolation_level=None
        )
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(_SCHEMA)
        log.info("audit log ready at %s", self._path)

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    # ── writes ───────────────────────────────────────────────
    def _record_sync(self, result: ScanResult, doc_hash: str) -> None:
        if self._conn is None:  # storage unavailable — audit disabled, scan still works
            return
        with self._lock:
            self._conn.execute(
                "INSERT INTO audit "
                "(ts, doc_hash, verdict, classification_level, cui_categories, "
                " engine, degraded, latency_ms) VALUES (?,?,?,?,?,?,?,?)",
                (
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    doc_hash,
                    result.verdict.value,
                    result.classification_level.value,
                    json.dumps([c.value for c in result.cui_categories]),
                    result.engine,
                    int(result.degraded),
                    result.latency_ms,
                ),
            )

    async def record(self, result: ScanResult, doc_hash: str) -> None:
        # Audit failures must never break a scan — log and move on.
        try:
            await asyncio.to_thread(self._record_sync, result, doc_hash)
        except Exception as e:  # noqa: BLE001
            log.warning("failed to write audit entry: %s", e)

    # ── reads ────────────────────────────────────────────────
    def _list_sync(self, limit: int) -> list[AuditEntry]:
        if self._conn is None:  # storage unavailable — no history to show
            return []
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, ts, doc_hash, verdict, classification_level, "
                "cui_categories, engine, degraded, latency_ms "
                "FROM audit ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            AuditEntry(
                id=r[0],
                ts=r[1],
                doc_hash=r[2],
                verdict=r[3],
                classification_level=r[4],
                cui_categories=json.loads(r[5]),
                engine=r[6],
                degraded=bool(r[7]),
                latency_ms=r[8],
            )
            for r in rows
        ]

    async def list(self, limit: int = 50) -> list[AuditEntry]:
        limit = max(1, min(limit, 500))
        return await asyncio.to_thread(self._list_sync, limit)
