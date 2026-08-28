from __future__ import annotations

import uuid

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.core.report_storage.base import ReportArtifact


class S3ReportStorage:
    """S3-compatible object storage (AWS S3, MinIO, R2, etc.)."""

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str,
        region: str,
        endpoint_url: str | None,
        access_key_id: str | None,
        secret_access_key: str | None,
    ) -> None:
        if not bucket:
            raise ValueError("REPORT_S3_BUCKET is required when REPORT_STORAGE_BACKEND=s3")
        self._bucket = bucket
        self._prefix = prefix if prefix.endswith("/") or not prefix else f"{prefix}/"
        self._client = self._build_client(
            region=region,
            endpoint_url=endpoint_url,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
        )

    @staticmethod
    def _build_client(
        *,
        region: str,
        endpoint_url: str | None,
        access_key_id: str | None,
        secret_access_key: str | None,
    ) -> BaseClient:
        session = boto3.session.Session()
        kwargs: dict = {"service_name": "s3", "region_name": region or "us-east-1"}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        if access_key_id and secret_access_key:
            kwargs["aws_access_key_id"] = access_key_id
            kwargs["aws_secret_access_key"] = secret_access_key
        return session.client(**kwargs)

    def object_key(self, report_id: uuid.UUID, *, ext: str) -> str:
        return f"{self._prefix}reports/{report_id}.{ext}"

    def write(
        self,
        report_id: uuid.UUID,
        *,
        ext: str,
        data: bytes,
        content_type: str,
    ) -> ReportArtifact:
        key = self.object_key(report_id, ext=ext)
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return ReportArtifact(key=key, size=len(data), content_type=content_type)

    def read(self, report_id: uuid.UUID, *, ext: str) -> bytes:
        key = self.object_key(report_id, ext=ext)
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    def exists(self, report_id: uuid.UUID, *, ext: str) -> bool:
        key = self.object_key(report_id, ext=ext)
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise

    def delete(self, report_id: uuid.UUID) -> None:
        for ext in ("pdf", "html"):
            key = self.object_key(report_id, ext=ext)
            try:
                self._client.delete_object(Bucket=self._bucket, Key=key)
            except ClientError:
                continue
