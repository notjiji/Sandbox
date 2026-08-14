"""AI assistant orchestrator — consumes structured scan results, never runs scanners."""

from __future__ import annotations

import json
import uuid

from sqlalchemy.orm import Session

from app.ai.repositories import usage_repository
from app.audit.events import AuditAction
from app.audit.service import record_audit_event
from app.members.models import OrganizationMember
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.conversation import append_message, get_or_create_conversation
from app.services.ai.models import AICapability, AIChatRequest, AIChatResponse, AIResponsePayload
from app.services.ai.prompts import get_system_prompt, resolve_prompt_name
from app.services.ai.provider import LLMProvider
from app.services.ai.validators import validate_chat_request

_DISCLAIMER = (
    "Recommendations are guidance only. Validate changes in a non-production environment "
    "before applying them to production systems."
)

_SUMMARY_CAPABILITIES = {
    AICapability.EXECUTIVE_SUMMARY,
    AICapability.TECHNICAL_SUMMARY,
    AICapability.ASSET_SUMMARY,
    AICapability.ORGANIZATION_OVERVIEW,
    AICapability.COMPARE_SCANS,
    AICapability.EXPLAIN_RISK_SCORE,
}


def _ai_audit_action(capability: AICapability) -> str:
    if capability == AICapability.EXPLAIN_FINDING:
        return AuditAction.AI_EXPLANATION
    if capability == AICapability.REMEDIATION:
        return AuditAction.AI_REMEDIATION
    if capability in _SUMMARY_CAPABILITIES:
        return AuditAction.AI_SUMMARY
    return AuditAction.AI_CHAT


class AIService:
    def __init__(self) -> None:
        self._context_builder = ContextBuilder()
        self._provider = LLMProvider()

    def chat(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        user_id: uuid.UUID,
        request: AIChatRequest,
    ) -> AIChatResponse:
        validate_chat_request(db, membership, request)
        context = self._context_builder.build(db, membership, request)

        conversation = get_or_create_conversation(
            db,
            organization_id=membership.organization_id,
            user_id=user_id,
            conversation_id=request.conversation_id,
            title=request.message[:80] if request.conversation_id is None else None,
        )

        append_message(db, conversation_id=conversation.id, role="user", content=request.message)

        system_prompt = get_system_prompt(request.capability, audience=request.audience)
        user_payload = json.dumps(context.model_dump(mode="json", exclude_none=True), indent=2)
        user_content = f"Context JSON:\n{user_payload}\n\nUser question:\n{request.message}"

        result = self._provider.complete(system_prompt=system_prompt, user_content=user_content)
        response = result.payload
        if not response.disclaimer:
            response = response.model_copy(update={"disclaimer": _DISCLAIMER})

        append_message(
            db,
            conversation_id=conversation.id,
            role="assistant",
            content=response.answer,
            model=result.model,
            token_count=result.output_tokens,
        )

        usage_repository.record_usage(
            db,
            organization_id=membership.organization_id,
            user_id=user_id,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )

        if request.conversation_id is None:
            record_audit_event(
                db,
                organization_id=membership.organization_id,
                user_id=user_id,
                action=AuditAction.AI_CONVERSATION_STARTED,
                resource_type="ai_conversation",
                resource_id=conversation.id,
            )

        record_audit_event(
            db,
            organization_id=membership.organization_id,
            user_id=user_id,
            action=_ai_audit_action(request.capability),
            resource_type="ai_conversation",
            resource_id=conversation.id,
            details={
                key: value
                for key, value in {
                    "capability": request.capability.value,
                    "prompt": resolve_prompt_name(request.capability, audience=request.audience),
                    "model": result.model,
                    "asset_id": str(request.asset_id) if request.asset_id else None,
                }.items()
                if value is not None
            },
        )

        db.commit()

        context_keys = [key for key, value in context.model_dump(mode="json").items() if value not in (None, [], {})]
        return AIChatResponse(
            conversation_id=conversation.id,
            capability=request.capability,
            response=response,
            context_keys=context_keys,
            model=result.model,
        )


ai_service = AIService()
