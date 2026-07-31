"""AI domain service — delegates inference to core.ai_engine."""

from app.core.ai_engine.service import AIService as CoreAIService


class AIService:
    def __init__(self) -> None:
        self._engine = CoreAIService()

    def summarize(self, *, text: str) -> str:
        return self._engine.summarize_findings(finding_ids=[])

    def chat(self, *, message: str) -> str:
        return self._engine.chat(message=message)
