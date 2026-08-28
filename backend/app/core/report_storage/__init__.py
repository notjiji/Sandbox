"""Report file storage — local volume or S3-compatible object storage."""

from functools import lru_cache

from app.core.config import get_settings
from app.core.report_storage.base import ReportStorageBackend
from app.core.report_storage.local import LocalReportStorage


@lru_cache
def get_report_storage() -> ReportStorageBackend:
    settings = get_settings()
    if settings.REPORT_STORAGE_BACKEND == "s3":
        from app.core.report_storage.s3 import S3ReportStorage

        return S3ReportStorage(
            bucket=settings.REPORT_S3_BUCKET,
            prefix=settings.REPORT_S3_PREFIX,
            region=settings.REPORT_S3_REGION,
            endpoint_url=settings.REPORT_S3_ENDPOINT_URL or None,
            access_key_id=settings.REPORT_S3_ACCESS_KEY_ID or None,
            secret_access_key=settings.REPORT_S3_SECRET_ACCESS_KEY or None,
        )
    return LocalReportStorage(root=settings.report_storage_root_path)


def reset_report_storage_cache() -> None:
    get_report_storage.cache_clear()
