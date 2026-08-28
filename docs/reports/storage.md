# Report file storage

Report **metadata** lives in PostgreSQL (`reports` table). PDF and HTML **bytes** are stored outside the database via a pluggable backend.

```
Report Service (pipeline)
        │
        ▼
ReportStorageBackend
        │
        ├── local  →  mounted volume (Compose `report_storage`)
        └── s3     →  S3-compatible object storage
```

## Backends

| `REPORT_STORAGE_BACKEND` | Use case | Configuration |
|--------------------------|----------|---------------|
| `local` (default) | Self-hosted Compose / VM | `REPORT_STORAGE_PATH` (default `/app/storage/reports`) |
| `s3` | Cloud / commercial | `REPORT_S3_BUCKET`, optional `REPORT_S3_ENDPOINT_URL`, credentials or IAM role |

### Local (production Compose)

`docker-compose.prod.yml` mounts a named volume at `/app/storage` shared by **backend** and **celery-worker**. Container restarts do not delete PDFs.

### S3-compatible

Set in `.env`:

```env
REPORT_STORAGE_BACKEND=s3
REPORT_S3_BUCKET=sandbox-reports-prod
REPORT_S3_REGION=eu-west-1
# Optional for MinIO / custom endpoints:
REPORT_S3_ENDPOINT_URL=https://minio.example.com
REPORT_S3_ACCESS_KEY_ID=...
REPORT_S3_SECRET_ACCESS_KEY=...
```

Object keys: `{prefix}reports/{report_id}.pdf` and `.html`. The PDF key is persisted in `reports.file_url`.

On AWS with instance/task IAM roles, omit access key env vars — boto3 uses the role.

## Implementation

| Module | Role |
|--------|------|
| `app/core/report_storage/` | Backend factory + local/S3 drivers |
| `app/core/report_engine/renderer.py` | Renders and writes artifacts |
| `app/reports/services/report_service.py` | Download reads from storage; delete removes objects |

## Backup

- **Postgres:** report rows (name, status, `file_url`, `file_size`, …)
- **Storage:** backup the volume or enable S3 versioning / cross-region replication

See [deployment/backups.md](../deployment/backups.md).
