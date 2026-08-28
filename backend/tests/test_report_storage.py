"""Report storage backend tests."""

from __future__ import annotations

import uuid

import pytest

from app.core.report_storage.local import LocalReportStorage


def test_local_storage_write_read_delete(tmp_path) -> None:
    storage = LocalReportStorage(root=tmp_path)
    report_id = uuid.uuid4()
    artifact = storage.write(
        report_id,
        ext="pdf",
        data=b"%PDF-1.4 test",
        content_type="application/pdf",
    )
    assert artifact.key == f"reports/{report_id}.pdf"
    assert artifact.size == len(b"%PDF-1.4 test")
    assert storage.exists(report_id, ext="pdf")
    assert storage.read(report_id, ext="pdf") == b"%PDF-1.4 test"

    storage.delete(report_id)
    assert not storage.exists(report_id, ext="pdf")
