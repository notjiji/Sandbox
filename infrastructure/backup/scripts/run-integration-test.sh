#!/usr/bin/env bash
# End-to-end backup + restore test against an ephemeral Compose stack.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE_FILE="${ROOT}/docker-compose.backup-test.yml"
PASSPHRASE="${BACKUP_ENCRYPTION_PASSPHRASE:-test-backup-passphrase-minimum-32-chars}"

cd "${ROOT}"

cleanup() {
  docker compose -f "${COMPOSE_FILE}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

log() { printf '[integration] %s\n' "$*"; }

log "Starting backup integration stack"
docker compose -f "${COMPOSE_FILE}" up -d postgres --wait

log "Running backup"
docker compose -f "${COMPOSE_FILE}" run --rm \
  -e BACKUP_ENCRYPTION_PASSPHRASE="${PASSPHRASE}" \
  -e ENVIRONMENT=production \
  backup backup

log "Running restore test"
docker compose -f "${COMPOSE_FILE}" run --rm \
  -e BACKUP_ENCRYPTION_PASSPHRASE="${PASSPHRASE}" \
  -e ENVIRONMENT=production \
  backup restore-test

log "Backup integration test passed"
