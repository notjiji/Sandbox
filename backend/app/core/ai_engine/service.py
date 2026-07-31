"""Facade for AI capabilities used by features."""


class AIService:
    def summarize_findings(self, *, finding_ids: list[str]) -> str:
        raise NotImplementedError("AI summaries not implemented yet")

    def chat(self, *, message: str, context: dict | None = None) -> str:
        raise NotImplementedError("AI chat not implemented yet")
