"""Facade for AI capabilities used by features."""

from app.services.ai.models import AIChatRequest, AICapability
from app.services.ai.service import ai_service


class AIService:
    def summarize_findings(self, *, finding_ids: list[str]) -> str:
        request = AIChatRequest(
            message="Summarize these findings for a security analyst.",
            capability=AICapability.TECHNICAL_SUMMARY,
        )
        raise NotImplementedError("Use ai_service.chat with full DB session and membership context")

    def chat(self, *, message: str, context: dict | None = None) -> str:
        raise NotImplementedError("Use app.services.ai.ai_service.chat via the API layer")
