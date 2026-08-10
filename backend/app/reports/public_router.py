from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.reports.services import report_service

router = APIRouter()


@router.get("/download")
def download_report_with_token(
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
) -> FileResponse:
    report, path = report_service.resolve_signed_report_download(db, token=token)
    filename = f"{report.name.replace(' ', '-').lower()}.pdf"
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename,
    )
