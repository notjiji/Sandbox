#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

usage() {
  cat <<'EOF'
Usage: restore.sh [--file PATH] [--target-db NAME] [--drop-first]

Restore a Sandbox Postgres backup.

  --file PATH       Backup artifact (default: latest in BACKUP_ROOT/postgres)
  --target-db NAME  Target database (default: POSTGRES_DB)
  --drop-first      Drop and recreate target database before restore

Environment: POSTGRES_* , BACKUP_ROOT, BACKUP_ENCRYPTION_PASSPHRASE
EOF
}

main() {
  local backup_file=""
  local target_db="${POSTGRES_DB:-}"
  local drop_first="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --file)
        backup_file="$2"
        shift 2
        ;;
      --target-db)
        target_db="$2"
        shift 2
        ;;
      --drop-first)
        drop_first="true"
        shift
        ;;
      -h | --help)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument: $1"
        ;;
    esac
  done

  require_env POSTGRES_HOST
  require_env POSTGRES_USER
  [[ -n "${target_db}" ]] || require_env POSTGRES_DB
  postgres_connect_args
  ensure_dirs

  if [[ -z "${backup_file}" ]]; then
    backup_file="$(ls -t "$(backup_root)/postgres"/sandbox-* 2>/dev/null | head -1 || true)"
  fi
  [[ -n "${backup_file}" && -f "${backup_file}" ]] || die "Backup file not found: ${backup_file:-<none>}"

  local tmp_dec tmp_dump
  tmp_dec="$(mktemp)"
  tmp_dump="$(mktemp)"

  log "Decrypting ${backup_file}"
  decrypt_file "${backup_file}" "${tmp_dec}"
  gunzip -c "${tmp_dec}" > "${tmp_dump}"

  if [[ "${drop_first}" == "true" ]]; then
    log "Recreating database ${target_db}"
    psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${target_db}' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS ${target_db};
CREATE DATABASE ${target_db};
SQL
  fi

  log "Restoring into ${target_db}"
  pg_restore \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER}" \
    -d "${target_db}" \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    "${tmp_dump}"

  rm -f "${tmp_dec}" "${tmp_dump}"
  log "Restore complete for database ${target_db}"
}

main "$@"
