"""Render ReportData to HTML and PDF."""

from __future__ import annotations

import uuid
from io import BytesIO
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.report_engine.data import ReportData
from app.reports.enums import ReportType

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def _storage_dir() -> Path:
    base = Path(__file__).resolve().parents[3] / "storage" / "reports"
    base.mkdir(parents=True, exist_ok=True)
    return base


def report_file_path(report_id: uuid.UUID, *, ext: str = "pdf") -> Path:
    return _storage_dir() / f"{report_id}.{ext}"


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
        from xhtml2pdf import pisa

        output = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=output, encoding="utf-8")
        if pisa_status.err:
            raise RuntimeError("PDF rendering failed")
        return output.getvalue()
    except Exception:
        # Fallback: store HTML-only artifact path handled by caller
        raise


def write_report_artifacts(data: ReportData) -> tuple[Path, Path, int]:
    report_id = uuid.UUID(data.report_id)
    html = render_report_html(data)
    html_path = report_file_path(report_id, ext="html")
    html_path.write_text(html, encoding="utf-8")

    pdf_path = report_file_path(report_id, ext="pdf")
    try:
        pdf_bytes = html_to_pdf(html)
        pdf_path.write_bytes(pdf_bytes)
        file_size = len(pdf_bytes)
    except Exception:
        # Minimal fallback PDF via existing text builder
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
        pdf_path.write_bytes(pdf_bytes)
        file_size = len(pdf_bytes)

    return pdf_path, html_path, file_size
