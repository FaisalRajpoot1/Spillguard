"""The analysis pipeline: deterministic → semantic → markings → decision,
assembled by the orchestrator into a ScanResult."""

from .orchestrator import scan

__all__ = ["scan"]
