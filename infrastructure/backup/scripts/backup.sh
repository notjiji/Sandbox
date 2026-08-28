#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

main() {
  require_env POSTGRES_HOST
  require_env POSTGRES_USER
  require_env POSTGRES_DB
  if [[ "${ENVIRONMENT:-}" == "production" && -z "${BACKUP_ENCRYPTION_PASSPHRASE:-}" ]]; then
    die "BACKUP_ENCRYPTION_PASSPHRASE is required when ENVIRONMENT=production"
  fi

  postgres_connect_args
  ensure_dirs

  local root ext stamp artifact tmp_dump tmp_out
  root="$(backup_root)"
  ext="$(backup_extension)"
  stamp="$(timestamp_utc)"
  artifact="${root}/postgres/sandbox-${stamp}.${ext}"
  tmp_dump="$(mktemp)"
  tmp_out="$(mktemp)"

  log "Starting Postgres backup for database ${POSTGRES_DB}"
  pg_dump \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -Fc \
    -f "${tmp_dump}"

  gzip -c "${tmp_dump}" > "${tmp_out}"
  rm -f "${tmp_dump}"
  encrypt_file "${tmp_out}" "${artifact}"
  rm -f "${tmp_out}"

  write_manifest "postgres-backup" "${artifact}"
  apply_retention "${root}/postgres"
  maybe_upload_offsite "${artifact}"

  if [[ "${BACKUP_REPORT_FILES:-true}" == "true" && -d "${REPORT_STORAGE_MOUNT:-/report_storage}/reports" ]]; then
    backup_reports "${stamp}"
  fi

  log "Backup complete: ${artifact}"
}

backup_reports() {
  local stamp="$1"
  local root ext artifact tmp_tar tmp_out
  root="$(backup_root)"
  ext="$(backup_extension)"
  artifact="${root}/reports/reports-${stamp}.tar.gz.${ext}"
  tmp_tar="$(mktemp)"
  tmp_out="$(mktemp)"

  log "Backing up report files from ${REPORT_STORAGE_MOUNT:-/report_storage}/reports"
  tar -czf "${tmp_tar}" -C "${REPORT_STORAGE_MOUNT:-/report_storage}" reports
  cp "${tmp_tar}" "${tmp_out}"
  rm -f "${tmp_tar}"
  encrypt_file "${tmp_out}" "${artifact}"
  rm -f "${tmp_out}"

  write_manifest "reports-backup" "${artifact}"
  apply_retention "${root}/reports"
  maybe_upload_offsite "${artifact}"
  log "Report backup complete: ${artifact}"
}

main "$@"
