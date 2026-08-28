from __future__ import annotations

import io
import re
from urllib.parse import quote

from fastapi.responses import StreamingResponse

from app.reports.models import Report


def _content_disposition(filename: str) -> str:
    """Build a header safe for latin-1 while preserving UTF-8 names via RFC 5987."""
    ascii_fallback = re.sub(
        r"[^\w.\-]",
        "-",
        filename.encode("ascii", "ignore").decode(),
    ).strip("-")
    if not ascii_fallback.lower().endswith(".pdf"):
        ascii_fallback = f"{ascii_fallback or 'report'}.pdf"
    return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{quote(filename)}'


def pdf_download_response(report: Report, pdf_bytes: bytes) -> StreamingResponse:
    filename = f"{report.name.replace(' ', '-').lower()}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(filename)},
    )
