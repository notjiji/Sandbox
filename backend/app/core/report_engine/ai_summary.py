"""Generate AI narrative summary from structured report facts."""

from __future__ import annotations

from app.core.report_engine.data import ReportData
from app.reports.enums import ReportType

REPORT_AI_SYSTEM = """You write security report summaries for a commercial platform.
Use ONLY the facts provided. Never invent findings, scores, or assets.
Respond with JSON: {"answer": "...", "summary": "one line", "confidence": "high|medium|low", "disclaimer": "..."}"""


def _facts_block(data: ReportData) -> str:
    sev = data.severity_distribution
    top = "\n".join(f"- {f.title} ({f.severity})" for f in data.key_risks[:5]) or "- None"
    return f"""Organization: {data.organization.name}
Project: {data.project.name}
Report type: {data.report_type.value}
Security score: {data.score.current}
Previous score: {data.score.previous}
Score change: {data.score.change}
Critical findings: {sev.critical}
High findings: {sev.high}
Medium findings: {sev.medium}
Low findings: {sev.low}
Assets assessed: {data.asset_counts.total}
Top findings:
{top}
Trend: {data.score.trend}
Recommendations count: {len(data.recommendations)}"""


def _offline_summary(data: ReportData) -> str:
    sev = data.severity_distribution
    score_text = (
        f"The organization security score is {data.score.current}/100"
        if data.score.current is not None
        else "A security score is not yet available"
    )
    if data.report_type == ReportType.EXECUTIVE:
        return (
            f"{score_text}. "
            f"There are {sev.critical} critical and {sev.high} high severity open findings "
            f"across {data.asset_counts.total} assessed assets. "
            f"Priority should be given to resolving critical issues and maintaining scan cadence."
        )
    return (
        f"{score_text}. Detailed assessment covers {len(data.findings)} open findings "
        f"with plugin-level breakdown and remediation guidance included in this report."
    )


def generate_ai_summary(data: ReportData) -> str:
    prompt = (
        "Write a concise "
        + (
            "executive summary for leadership"
            if data.report_type == ReportType.EXECUTIVE
            else "technical summary for security engineers"
        )
        + " based strictly on these facts:\n\n"
        + _facts_block(data)
    )
    try:
        from app.services.ai.provider import LLMProvider

        provider = LLMProvider()
        result = provider.complete(system_prompt=REPORT_AI_SYSTEM, user_content=prompt)
        answer = result.payload.answer
        if answer and "OPENAI_API_KEY" not in answer:
            return answer
    except Exception:
        pass
    return _offline_summary(data)
