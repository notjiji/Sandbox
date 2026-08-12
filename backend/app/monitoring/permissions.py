"""Monitoring feature permissions — re-exported from core RBAC registry."""

from app.core.permissions import Permission

MONITORING_READ = Permission.MONITORING_READ
MONITORING_MANAGE = Permission.MONITORING_MANAGE

MONITORING_PERMISSIONS = frozenset({MONITORING_READ, MONITORING_MANAGE})
