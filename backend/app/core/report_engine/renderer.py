"""Render ReportData to HTML and PDF and persist via report storage."""

from __future__ import annotations

import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.report_engine.data import ReportData
from app.core.report_storage import get_report_storage
from app.core.report_storage.base import ReportArtifact
from app.reports.enums import ReportType

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_report_html(data: ReportData) -> str:
    template_name = (
        "executive.html"
        if data.report_type in {ReportType.EXECUTIVE, ReportType.WEEKLY, ReportType.MONTHLY}
        else "technical.html"
    )
    template = _env.get_template(template_name)
    return template.render(data=data.model_dump(mode="json"))


def html_to_pdf(html: str) -> bytes:
    try:
        from io import BytesIO

        from xhtml2pdf import pisa

        output = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=output, encoding="utf-8")
        if pisa_status.err:
            raise RuntimeError("PDF rendering failed")
        return output.getvalue()
    except Exception:
        raise


def write_report_artifacts(data: ReportData) -> tuple[ReportArtifact, ReportArtifact, int]:
    """Render HTML + PDF and store both. Returns (pdf_artifact, html_artifact, pdf_size)."""
    report_id = uuid.UUID(data.report_id)
    storage = get_report_storage()
    html = render_report_html(data)

    html_artifact = storage.write(
        report_id,
        ext="html",
        data=html.encode("utf-8"),
        content_type="text/html; charset=utf-8",
    )

    try:
        pdf_bytes = html_to_pdf(html)
    except Exception:
        from app.core.report_engine.pdf import build_text_pdf

        lines = [
            f"Organization: {data.organization.name}",
            f"Project: {data.project.name}",
            f"Score: {data.score.current}",
            f"Critical: {data.severity_distribution.critical}",
            f"High: {data.severity_distribution.high}",
        ]
        if data.ai_summary:
            lines.extend(["", "Summary:", data.ai_summary[:2000]])
        pdf_bytes = build_text_pdf(title=data.title, lines=lines)

    pdf_artifact = storage.write(
        report_id,
        ext="pdf",
        data=pdf_bytes,
        content_type="application/pdf",
    )
    return pdf_artifact, html_artifact, pdf_artifact.size
