from sqlalchemy.orm import Session

from app.ai.models import AIPrompt


def get_prompt_by_name(db: Session, *, name: str) -> AIPrompt | None:
    return db.query(AIPrompt).filter(AIPrompt.name == name).first()


def list_prompts(db: Session) -> list[AIPrompt]:
    return db.query(AIPrompt).order_by(AIPrompt.name.asc()).all()
