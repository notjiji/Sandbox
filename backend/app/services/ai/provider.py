"""LLM provider — calls OpenAI; never touches scanners."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.services.ai.models import AIResponsePayload


@dataclass(frozen=True)
class LLMResult:
    payload: AIResponsePayload
    model: str
    input_tokens: int
    output_tokens: int


class LLMProvider:
    def complete(self, *, system_prompt: str, user_content: str) -> LLMResult:
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            return self._offline_response(user_content)

        payload = {
            "model": settings.AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": settings.AI_TEMPERATURE,
            "max_tokens": settings.AI_MAX_OUTPUT_TOKENS,
            "response_format": {"type": "json_object"},
        }
        with httpx.Client(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            body = response.json()

        choice = body["choices"][0]["message"]["content"]
        usage = body.get("usage") or {}
        parsed = _parse_response_json(choice)
        return LLMResult(
            payload=parsed,
            model=body.get("model") or settings.AI_MODEL,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
        )

    def _offline_response(self, user_content: str) -> LLMResult:
        settings = get_settings()
        snippet = user_content[:400].replace("\n", " ")
        return LLMResult(
            payload=AIResponsePayload(
                answer=(
                    "The AI assistant is configured but **OPENAI_API_KEY** is not set. "
                    "Structured scan context was built successfully; connect an LLM provider to generate explanations.\n\n"
                    f"Context preview: `{snippet}...`"
                ),
                summary="AI provider not configured",
                references=[],
                related_findings=[],
                confidence="low",
                disclaimer="No LLM inference was performed. Findings and scores come from scanners only.",
            ),
            model="offline",
            input_tokens=0,
            output_tokens=0,
        )


def _parse_response_json(raw: str) -> AIResponsePayload:
    try:
        data = json.loads(raw)
        return AIResponsePayload.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return AIResponsePayload.model_validate(json.loads(match.group(0)))
        except (json.JSONDecodeError, ValueError):
            pass

    return AIResponsePayload(
        answer=raw.strip(),
        summary=None,
        references=[],
        related_findings=[],
        confidence="medium",
    )
