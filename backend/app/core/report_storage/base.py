from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ReportArtifact:
    """Stored report object reference (metadata lives in PostgreSQL)."""

    key: str
    size: int
    content_type: str


class ReportStorageBackend(Protocol):
    def object_key(self, report_id: uuid.UUID, *, ext: str) -> str:
        """Return the stable storage key persisted in `reports.file_url`."""

    def write(
        self,
        report_id: uuid.UUID,
        *,
        ext: str,
        data: bytes,
        content_type: str,
    ) -> ReportArtifact:
        ...

    def read(self, report_id: uuid.UUID, *, ext: str) -> bytes:
        ...

    def exists(self, report_id: uuid.UUID, *, ext: str) -> bool:
        ...

    def delete(self, report_id: uuid.UUID) -> None:
        """Remove PDF and HTML artifacts for the report."""
