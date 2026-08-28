#!/usr/bin/env bash
# Shared helpers for Sandbox backup/restore scripts.
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}

die() {
  log "ERROR: $*"
  exit 1
}

require_env() {
  local name="$1"
  [[ -n "${!name:-}" ]] || die "Missing required environment variable: ${name}"
}

backup_root() {
  echo "${BACKUP_ROOT:-/backups}"
}

postgres_connect_args() {
  require_env POSTGRES_HOST
  require_env POSTGRES_USER
  require_env POSTGRES_DB
  export PGPASSWORD="${POSTGRES_PASSWORD:-}"
}

timestamp_utc() {
  date -u +'%Y%m%d-%H%M%S'
}

ensure_dirs() {
  local root
  root="$(backup_root)"
  mkdir -p "${root}/postgres" "${root}/reports" "${root}/logs" "${root}/restore-tests"
}

encrypt_file() {
  local input="$1"
  local output="$2"
  if [[ -n "${BACKUP_ENCRYPTION_PASSPHRASE:-}" ]]; then
    openssl enc -aes-256-cbc -pbkdf2 -salt \
      -pass "env:BACKUP_ENCRYPTION_PASSPHRASE" \
      -in "${input}" \
      -out "${output}"
  else
    log "WARNING: BACKUP_ENCRYPTION_PASSPHRASE unset — storing compressed backup without encryption"
    mv "${input}" "${output}"
  fi
}

decrypt_file() {
  local input="$1"
  local output="$2"
  if [[ -n "${BACKUP_ENCRYPTION_PASSPHRASE:-}" ]]; then
    openssl enc -d -aes-256-cbc -pbkdf2 \
      -pass "env:BACKUP_ENCRYPTION_PASSPHRASE" \
      -in "${input}" \
      -out "${output}"
  else
    cp "${input}" "${output}"
  fi
}

backup_extension() {
  if [[ -n "${BACKUP_ENCRYPTION_PASSPHRASE:-}" ]]; then
    echo "dump.enc"
  else
    echo "dump"
  fi
}

write_manifest() {
  local kind="$1"
  local artifact="$2"
  local manifest_dir
  manifest_dir="$(backup_root)/logs"
  local manifest="${manifest_dir}/${kind}-$(timestamp_utc).json"
  local size checksum
  size="$(wc -c < "${artifact}" | tr -d ' ')"
  checksum="$(sha256sum "${artifact}" | awk '{print $1}')"
  cat > "${manifest}" <<EOF
{
  "kind": "${kind}",
  "artifact": "${artifact}",
  "size_bytes": ${size},
  "sha256": "${checksum}",
  "created_at": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "postgres_db": "${POSTGRES_DB:-}",
  "encrypted": $([[ -n "${BACKUP_ENCRYPTION_PASSPHRASE:-}" ]] && echo true || echo false)
}
EOF
  log "Wrote manifest ${manifest}"
}

apply_retention() {
  local dir="$1"
  local days="${BACKUP_RETENTION_DAYS:-7}"
  [[ -d "${dir}" ]] || return 0
  log "Applying retention: delete files in ${dir} older than ${days} days"
  find "${dir}" -type f -mtime "+${days}" -print -delete || true
}

maybe_upload_offsite() {
  local file="$1"
  if [[ -z "${BACKUP_S3_URI:-}" ]]; then
    return 0
  fi
  if command -v aws >/dev/null 2>&1; then
    log "Uploading ${file} to ${BACKUP_S3_URI}"
    aws s3 cp "${file}" "${BACKUP_S3_URI%/}/$(basename "${file}")"
  else
    log "WARNING: BACKUP_S3_URI set but aws CLI not installed — skipping upload"
  fi
}

table_count() {
  local db="$1"
  local table="$2"
  local count
  count="$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" -d "${db}" -Atqc \
    "SELECT COUNT(*) FROM ${table}" 2>/dev/null || echo "-1")"
  echo "${count}"
}

table_exists() {
  local db="$1"
  local table="$2"
  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" -d "${db}" -Atqc \
    "SELECT to_regclass('public.${table}') IS NOT NULL" 2>/dev/null | grep -q '^t$'
}
