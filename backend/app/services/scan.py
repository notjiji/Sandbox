from app.core.exceptions import NotImplementedFeatureError
from app.schemas.scan import CreateScanRequest, ScanListResponse


def list_scans() -> ScanListResponse:
    return ScanListResponse(items=[], total=0)


def create_scan(*, body: CreateScanRequest) -> None:
    raise NotImplementedFeatureError("Scan creation")


def get_scan(*, scan_id: str) -> None:
    raise NotImplementedFeatureError("Scan retrieval")


def run_scan(*, scan_id: str) -> None:
    raise NotImplementedFeatureError("Scan execution")


def cancel_scan(*, scan_id: str) -> None:
    raise NotImplementedFeatureError("Scan cancellation")
