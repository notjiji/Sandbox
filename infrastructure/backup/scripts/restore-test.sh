#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

main() {
  require_env POSTGRES_HOST
  require_env POSTGRES_USER
  require_env POSTGRES_DB
  postgres_connect_args
  ensure_dirs

  local root test_db stamp log_file result backup_file
  root="$(backup_root)"
  test_db="${BACKUP_RESTORE_TEST_DB:-sandbox_restore_test}"
  stamp="$(timestamp_utc)"
  log_file="${root}/restore-tests/restore-test-${stamp}.json"
  result="pass"

  log "Restore test starting (verify DB: ${test_db})"

  "${SCRIPT_DIR}/backup.sh" || die "Pre-restore-test backup failed"

  backup_file="$(ls -t "${root}/postgres"/sandbox-* 2>/dev/null | head -1 || true)"
  [[ -n "${backup_file}" && -f "${backup_file}" ]] || die "No backup artifact found after backup.sh"

  local source_users=-1 source_orgs=-1
  if table_exists "${POSTGRES_DB}" "users"; then
    source_users="$(table_count "${POSTGRES_DB}" "users")"
  fi
  if table_exists "${POSTGRES_DB}" "organizations"; then
    source_orgs="$(table_count "${POSTGRES_DB}" "organizations")"
  fi

  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${test_db}' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS ${test_db};
CREATE DATABASE ${test_db};
SQL

  if ! "${SCRIPT_DIR}/restore.sh" --file "${backup_file}" --target-db "${test_db}"; then
    result="fail"
  fi

  local restored_users=-1 restored_orgs=-1 verify_ok=true
  if table_exists "${test_db}" "users"; then
    restored_users="$(table_count "${test_db}" "users")"
    if [[ "${source_users}" != "-1" && "${restored_users}" != "${source_users}" ]]; then
      verify_ok=false
      result="fail"
    fi
  fi
  if table_exists "${test_db}" "organizations"; then
    restored_orgs="$(table_count "${test_db}" "organizations")"
    if [[ "${source_orgs}" != "-1" && "${restored_orgs}" != "${source_orgs}" ]]; then
      verify_ok=false
      result="fail"
    fi
  fi

  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${test_db}' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS ${test_db};
SQL

  cat > "${log_file}" <<EOF
{
  "result": "${result}",
  "verified": ${verify_ok},
  "backup_file": "${backup_file}",
  "source_db": "${POSTGRES_DB}",
  "test_db": "${test_db}",
  "counts": {
    "users": {"source": ${source_users}, "restored": ${restored_users}},
    "organizations": {"source": ${source_orgs}, "restored": ${restored_orgs}}
  },
  "finished_at": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
}
EOF

  apply_retention "${root}/postgres"
  apply_retention "${root}/reports"
  # Keep restore-test logs indefinitely (small JSON artifacts)

  if [[ "${result}" != "pass" ]]; then
    log "Restore test FAILED — see ${log_file}"
    exit 1
  fi

  log "Restore test PASSED — see ${log_file}"
}

main "$@"
