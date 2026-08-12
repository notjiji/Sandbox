from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.responses import success_response
from app.monitoring.agent_auth import get_current_agent
from app.monitoring.models import MonitoringAgent
from app.monitoring.schemas import AgentIngestRequest
from app.monitoring.services.ingest_service import ingest_agent_payload

router = APIRouter()


@router.post("/ingest")
def ingest_metrics(
    body: AgentIngestRequest,
    db: Session = Depends(get_db),
    agent: MonitoringAgent = Depends(get_current_agent),
) -> JSONResponse:
    result = ingest_agent_payload(db, agent=agent, body=body)
    db.commit()
    return success_response(data=result.model_dump(mode="json"))
