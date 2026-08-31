#!/usr/bin/env bash
# Run the staging acceptance test against a live Compose stack.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for staging acceptance" >&2
  exit 1
fi

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-sandbox-staging-acceptance}"

if [[ ! -f .env ]]; then
  cp .env.staging.example .env
fi

python - <<'PY'
from pathlib import Path

replacements = {
    "POSTGRES_PASSWORD=CHANGE-ME-staging-postgres-password-32chars": "POSTGRES_PASSWORD=staging-acceptance-postgres-password-32",
    "SECRET_KEY=CHANGE-ME-staging-secret-key-minimum-32-characters": "SECRET_KEY=staging-acceptance-secret-key-minimum-32-chars",
    "JWT_SECRET=CHANGE-ME-staging-jwt-secret-minimum-32-characters": "JWT_SECRET=staging-acceptance-jwt-secret-minimum-32-chars",
}

for name in (".env", ".env.staging.acceptance"):
    path = Path(name)
    if not path.exists() and name == ".env.staging.acceptance":
        path.write_text(Path(".env.staging.example").read_text(encoding="utf-8"), encoding="utf-8")
    if path.exists():
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
PY

cd backend
pip install -q httpx
python -m pytest tests/test_staging_acceptance.py -q "$@"
