#!/usr/bin/env bash
# Ensure docs/testing/inventory.md references existing test modules (no silent drift).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INVENTORY="${ROOT}/docs/testing/inventory.md"
TESTS_DIR="${ROOT}/backend/tests"

if [[ ! -f "${INVENTORY}" ]]; then
  echo "Missing ${INVENTORY}" >&2
  exit 1
fi

missing=0

check_file() {
  local name="$1"
  local path="${TESTS_DIR}/${name}"
  if [[ ! -f "${path}" ]]; then
    echo "Inventory references missing test file: ${name}" >&2
    missing=1
  fi
}

# Explicit modules listed in inventory (stable quality-gate set).
for name in \
  test_auth.py \
  test_jwt_security.py \
  test_rbac.py \
  test_organizations.py \
  test_organization_activity.py \
  test_members.py \
  test_member_lifecycle.py \
  test_invitations.py \
  test_projects.py \
  test_org_isolation.py \
  test_assets.py \
  test_scans.py \
  test_scan_history.py \
  test_product_pipeline.py \
  test_asset_verification.py \
  test_risk_engine.py \
  test_dashboard.py \
  test_production_config.py \
  test_production_security_boundary.py \
  test_project_reports.py \
  test_asset_reports.py \
  test_reports_rbac.py \
  test_report_storage.py \
  test_backup_restore.py \
  test_worker_reliability.py \
  test_staging_acceptance.py \
  test_monitoring.py \
  test_audit_logs.py
do
  check_file "${name}"
done

# Every backend/tests/test_*.py must appear in inventory (prevents untracked suites).
while IFS= read -r path; do
  base="$(basename "${path}")"
  if ! grep -q "${base}" "${INVENTORY}"; then
    echo "Test file not documented in inventory: ${base}" >&2
    missing=1
  fi
done < <(find "${TESTS_DIR}" -maxdepth 1 -name 'test_*.py' -type f | sort)

if [[ "${missing}" -ne 0 ]]; then
  echo "Test inventory drift detected — update docs/testing/inventory.md" >&2
  exit 1
fi

echo "Test inventory check passed."
