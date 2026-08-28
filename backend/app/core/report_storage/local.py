from __future__ import annotations

import uuid
from pathlib import Path

from app.core.report_storage.base import ReportArtifact


class LocalReportStorage:
    """Persist report files on a mounted volume (Compose `report_storage`)."""

    def __init__(self, *, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def object_key(self, report_id: uuid.UUID, *, ext: str) -> str:
        return f"reports/{report_id}.{ext}"

    def _path_for_key(self, key: str) -> Path:
        # Flatten to root/{uuid}.{ext} — key keeps a logical prefix for S3 parity.
        name = key.split("/")[-1]
        return self._root / name

    def write(
        self,
        report_id: uuid.UUID,
        *,
        ext: str,
        data: bytes,
        content_type: str,
    ) -> ReportArtifact:
        key = self.object_key(report_id, ext=ext)
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return ReportArtifact(key=key, size=len(data), content_type=content_type)

    def read(self, report_id: uuid.UUID, *, ext: str) -> bytes:
        key = self.object_key(report_id, ext=ext)
        path = self._path_for_key(key)
        return path.read_bytes()

    def exists(self, report_id: uuid.UUID, *, ext: str) -> bool:
        key = self.object_key(report_id, ext=ext)
        return self._path_for_key(key).is_file()

    def delete(self, report_id: uuid.UUID) -> None:
        for ext in ("pdf", "html"):
            path = self._path_for_key(self.object_key(report_id, ext=ext))
            if path.is_file():
                path.unlink()
