# AI architecture (as built)

Two call paths share an OpenAI client when `OPENAI_API_KEY` is set.

## Chat

```
POST /api/v1/organizations/ai/chat
  → require_permission(ai:use)
  → app.services.ai.service.AIService
      → ContextBuilder (structured facts)
      → LLMProvider
      → persist conversation/messages/usage
      → audit: ai.conversation_started (new thread) + capability action
```

HTTP lives in `app/ai/router.py`. Models: `ai_conversations`, `ai_messages`, `ai_prompts`, `ai_usage`.

The assistant does not get raw table dumps. Context is summaries (scores, counts, top issues, selected asset).

Viewers cannot use AI (`ai:use` omitted from `VIEWER_PERMISSIONS`).

## Reports

`app/core/report_engine/ai_summary.py` — facts-only system prompt. If the key is missing, generation uses **offline template text**, not a live model.

## Configuration

| Env | Default |
|-----|---------|
| `OPENAI_API_KEY` | empty (live AI off) |
| `AI_MODEL` | `gpt-4o-mini` |
| `AI_TEMPERATURE` | `0.2` |
| `AI_MAX_OUTPUT_TOKENS` | `2048` |
| `AI_REQUEST_TIMEOUT_SECONDS` | `60` |

## Audit actions (code)

| Capability / event | Action |
|--------------------|--------|
| New conversation | `ai.conversation_started` |
| Explain finding | `ai.explanation_requested` |
| Remediation | `ai.remediation_generated` |
| Summary-style capabilities | `ai.summary_generated` |
| Other chat | `ai.chat` |

`ai.chat` is not the only chat-related event.
