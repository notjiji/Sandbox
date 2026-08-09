"""AI domain entrypoint — delegates to services.ai."""

from app.services.ai import ai_service

__all__ = ["ai_service"]
