from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.responses import success_response
from app.monitoring.agent_auth import get_current_agent
from app.monitoring.models import MonitoringAgent
from app.monitoring.schemas import AgentIngestRequest, AgentRegisterRequest
from app.monitoring.services.enrollment_service import register_agent
from app.monitoring.services.ingest_service import ingest_agent_payload

router = APIRouter()

_INSTALL_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail

API_URL="${SANDBOX_API_URL:-}"
TOKEN="${SANDBOX_ENROLLMENT_TOKEN:-}"

if [[ -z "$API_URL" || -z "$TOKEN" ]]; then
  echo "Set SANDBOX_API_URL and SANDBOX_ENROLLMENT_TOKEN before running this script." >&2
  echo "Example:" >&2
  echo "  curl -fsSL {api_url}/monitoring/install.sh | sudo env SANDBOX_API_URL={api_url} SANDBOX_ENROLLMENT_TOKEN=sbe_... bash" >&2
  exit 1
fi

STATE_DIR="${SANDBOX_AGENT_HOME:-${HOME}/.sandbox-agent}"
mkdir -p "$STATE_DIR"
umask 077
cat > "$STATE_DIR/env" <<EOF
SANDBOX_API_URL=$API_URL
SANDBOX_ENROLLMENT_TOKEN=$TOKEN
SANDBOX_AGENT_HOME=$STATE_DIR
EOF

echo "Enrollment token saved to $STATE_DIR/env (expires quickly; used once)."
echo "The agent will exchange it for a per-server credential on first start."
echo
echo "If the agent package is not installed yet:"
echo "  pip install -r requirements.txt && python -m agent"
echo

set -a
# shellcheck disable=SC1091
source "$STATE_DIR/env"
set +a

if python3 -c "import agent" >/dev/null 2>&1; then
  exec python3 -m agent
fi
if python -c "import agent" >/dev/null 2>&1; then
  exec python -m agent
fi

echo "Python package 'agent' not found on PATH. Copy the agent/ directory to this host, install requirements, then run: python -m agent"
exit 1
"""


@router.get("/install.sh")
def download_install_script() -> PlainTextResponse:
    api_url = get_settings().PUBLIC_API_URL.rstrip("/")
    script = _INSTALL_SCRIPT.replace("{api_url}", api_url)
    return PlainTextResponse(content=script, media_type="text/x-shellscript")


@router.post("/register")
def register_monitoring_agent(
    body: AgentRegisterRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    result = register_agent(db, body=body)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/ingest")
def ingest_metrics(
    body: AgentIngestRequest,
    db: Session = Depends(get_db),
    agent: MonitoringAgent = Depends(get_current_agent),
) -> JSONResponse:
    result = ingest_agent_payload(db, agent=agent, body=body)
    db.commit()
    return success_response(data=result.model_dump(mode="json"))
