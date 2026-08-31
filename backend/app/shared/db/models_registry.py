"""Register every SQLAlchemy model with Base.metadata.

Celery workers and one-off scripts do not import FastAPI routers, so they must call
``import_all_models()`` before opening a DB session that touches related mappers.
"""


def import_all_models() -> None:
    import app.ai.models  # noqa: F401
    import app.assets.link_models  # noqa: F401
    import app.assets.models  # noqa: F401
    import app.assets.saved_filter_models  # noqa: F401
    import app.audit.models  # noqa: F401
    import app.auth.models  # noqa: F401
    import app.findings.models  # noqa: F401
    import app.members.models  # noqa: F401
    import app.monitoring.models  # noqa: F401
    import app.organizations.invites  # noqa: F401
    import app.organizations.models  # noqa: F401
    import app.projects.models  # noqa: F401
    import app.reports.models  # noqa: F401
    import app.risk.models  # noqa: F401
    import app.scans.models  # noqa: F401
    import app.scans.schedule_models  # noqa: F401
    import app.users.models  # noqa: F401
