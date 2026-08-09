import uuid

from sqlalchemy.orm import Session

from app.ai.models import AIUsage


def record_usage(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost: float | None = None,
) -> AIUsage:
    row = AIUsage(
        organization_id=organization_id,
        user_id=user_id,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost,
    )
    db.add(row)
    db.flush()
    return row
