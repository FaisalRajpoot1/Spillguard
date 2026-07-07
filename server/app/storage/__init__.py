"""Persistence — an append-only SQLite audit log. Stores a hash of each
document, never its content: a spillage guard must not hoard the secrets it
inspects."""

from .audit import AuditLog

__all__ = ["AuditLog"]
