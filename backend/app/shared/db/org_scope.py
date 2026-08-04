"""Organization isolation helpers — apply to every tenant-scoped lookup."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Query, Session

from app.core.exceptions import NotFoundError
from app.organizations.models import Organization


def require_active_organization(organization: Organization | None) -> Organization:
    if organization is None or not organization.is_active:
        raise NotFoundError("Organization")
    return organization


def scope_by_organization_id[T](
    query: Query[T],
    model: type,
    organization_id: uuid.UUID,
) -> Query[T]:
    """Filter a SQLAlchemy query to the current organization."""
    return query.filter(model.organization_id == organization_id)
