# AI Assistant

Org-scoped conversational AI for security questions, powered by structured platform context (not raw database access).

## Features

- Chat sidebar and full-page assistant
- Conversation history per organization
- Capability chips for common queries
- Asset-level "Ask AI" entry points
- Usage tracking and rate awareness

## Access

- **Permission:** `ai:use` (owner, admin, security_analyst, manager — not viewer)
- **API prefix:** `/api/v1/organizations/ai`
- **Frontend:** `/ai-assistant`, sidebar via `ChatPanelContext`

## Architecture

```
User message
    → ai/router.py
    → services/ai/service.py (AIService.chat)
    → structured context builders (org, assets, findings summaries)
    → LLMProvider (OpenAI when OPENAI_API_KEY is set)
    → response + conversation persistence
```

`app/core/ai_engine/service.py` is a leftover facade that raises `NotImplementedError`. HTTP chat does not use it. Canonical write-up: [docs/architecture/ai.md](../architecture/ai.md).

The AI receives **structured facts** (scores, finding counts, top issues) — it must not invent vulnerabilities. Same principle as report AI summaries.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `OPENAI_API_KEY` | — | API key (empty disables live AI) |
| `AI_MODEL` | `gpt-4o-mini` | Model name |
| `AI_TEMPERATURE` | `0.2` | Response randomness |
| `AI_MAX_OUTPUT_TOKENS` | `2048` | Max response length |
| `AI_REQUEST_TIMEOUT_SECONDS` | `60` | Request timeout |

## Database

Migration `037_ai_assistant_tables.py` adds conversation and message tables.

Models: `backend/app/services/ai/models.py`  
Repositories: `backend/app/ai/repositories/`

## Report integration

Report generation uses a separate AI path in `core/report_engine/ai_summary.py` with a strict facts-only system prompt. Chat and report AI share the OpenAI client but not conversation state.

## Key files

| Layer | Path |
|-------|------|
| AI router | `backend/app/ai/router.py` |
| AI engine | `backend/app/core/ai_engine/service.py` |
| OpenAI service | `backend/app/services/ai/` |
| Chat sidebar | `frontend/src/features/ai/components/AiChatSidebar.tsx` |
| Context | `frontend/src/features/ai/context/ChatPanelContext.tsx` |

## Audit events

Source: `backend/app/audit/events.py` and `_ai_audit_action()` in `backend/app/services/ai/service.py`.

**`ai.chat` is not the only AI event.** A new thread writes two rows: conversation start, then the capability action for that turn. Later turns write only the capability action.

| Event | When it is written | Typical `capability` in `details` |
|-------|--------------------|-----------------------------------|
| `ai.conversation_started` | First message of a new conversation (`request.conversation_id` is null) | — (no capability field required) |
| `ai.explanation_requested` | Capability `explain_finding` | `explain_finding` |
| `ai.remediation_generated` | Capability `remediation` | `remediation` |
| `ai.summary_generated` | Summary-style capabilities | `executive_summary`, `technical_summary`, `asset_summary`, `organization_overview`, `compare_scans`, `explain_risk_score` |
| `ai.chat` | Everything else — currently `general` | `general` |

Capability → event mapping in code:

```
explain_finding          → ai.explanation_requested
remediation              → ai.remediation_generated
executive_summary        → ai.summary_generated
technical_summary        → ai.summary_generated
asset_summary            → ai.summary_generated
organization_overview    → ai.summary_generated
compare_scans            → ai.summary_generated
explain_risk_score       → ai.summary_generated
general                  → ai.chat
```

Each capability event’s `details` JSON includes `capability`, `prompt` (template name), `model`, and `asset_id` when set. Resource is `ai_conversation`.

Canonical list also lives in [audit/event-catalog.md](../audit/event-catalog.md). Architecture note: [architecture/ai.md](../architecture/ai.md).

## Fallback behavior

When `OPENAI_API_KEY` is unset, report generation uses offline template summaries; chat may return a placeholder or error depending on endpoint configuration.
