#!/usr/bin/env bash
# Fail CI if tracked files contain committed secrets or unsafe placeholders.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT}"

fail() {
  echo "SECRET CHECK FAILED: $*" >&2
  exit 1
}

echo "Checking for tracked .env files (must not commit real env)..."
while IFS= read -r tracked; do
  case "${tracked}" in
    .env.example|.env.production.example|.env.staging.example) continue ;;
    .env|.env.*)
      fail "tracked env file must not be committed: ${tracked}"
      ;;
  esac
done < <(git ls-files '.env' '.env.*' 2>/dev/null || true)

echo "Scanning tracked source for placeholder / live credential patterns..."
# Exclude examples, docs, and this script.
mapfile -t files < <(git ls-files \
  'backend/**/*.py' \
  'frontend/**/*.{ts,tsx,js,jsx}' \
  'infrastructure/**' \
  'docker-compose*.yml' \
  'Makefile' \
  | grep -Ev '(^docs/|\.env\.example$|\.env\.production\.example$|\.env\.staging\.example$|scripts/ci/check-secrets\.sh$)' || true)

patterns=(
  'CHANGE-ME'
  'change-me-to-a-long-random'
  'sk-live-'
  'sk-proj-live'
  're_live_'
  'AWS_SECRET_ACCESS_KEY='
  'BEGIN RSA PRIVATE KEY'
  'BEGIN OPENSSH PRIVATE KEY'
)

for file in "${files[@]}"; do
  [[ -f "${file}" ]] || continue
  for pattern in "${patterns[@]}"; do
    if grep -nE "${pattern}" "${file}" >/tmp/secret-hit 2>/dev/null; then
      echo "Pattern '${pattern}' found in ${file}:" >&2
      cat /tmp/secret-hit >&2
      fail "remove placeholder or secret material from tracked files"
    fi
  done
done

echo "Secret policy checks passed."
