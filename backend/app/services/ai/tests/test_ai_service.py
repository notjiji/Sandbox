"""AI service unit tests."""

from app.services.ai.models import AICapability
from app.services.ai.prompts import get_system_prompt, resolve_prompt_name
from app.services.ai.provider import LLMProvider, _parse_response_json


def test_resolve_prompt_name_for_executive_summary() -> None:
    assert resolve_prompt_name(AICapability.EXECUTIVE_SUMMARY) == "executive_report_writer"


def test_get_system_prompt_contains_core_rules() -> None:
    prompt = get_system_prompt(AICapability.EXPLAIN_FINDING)
    assert "never invent vulnerabilities" in prompt.lower()
    assert "never calculate" in prompt.lower()


def test_parse_response_json() -> None:
    payload = _parse_response_json(
        '{"answer":"ok","summary":"s","references":[],"related_findings":[],"confidence":"high"}'
    )
    assert payload.answer == "ok"
    assert payload.confidence == "high"


def test_provider_offline_mode() -> None:
    result = LLMProvider().complete(system_prompt="test", user_content="hello")
    assert result.model == "offline"
    assert "OPENAI_API_KEY" in result.payload.answer
