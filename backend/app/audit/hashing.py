"""SHA-256 hash chain for tamper-evident audit logs.

Each org has its own chain. `entry_hash` covers the previous hash plus the
canonical event payload so an edited or deleted row breaks verification.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

GENESIS_HASH = "0" * 64


def canonical_created_at(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def compute_entry_hash(
    *,
    prev_hash: str,
    record_id: uuid.UUID,
    organization_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str | None,
    resource_id: uuid.UUID | None,
    severity: str,
    details: dict | None,
    created_at: datetime,
) -> str:
    payload = {
        "prev_hash": prev_hash,
        "id": str(record_id),
        "organization_id": str(organization_id) if organization_id else None,
        "user_id": str(user_id) if user_id else None,
        "action": action,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id else None,
        "severity": severity,
        "details": details or {},
        "created_at": canonical_created_at(created_at),
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8"))
    return digest.hexdigest()
