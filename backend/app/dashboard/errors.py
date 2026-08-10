from app.core.exceptions import AppException


class DashboardUnavailableError(AppException):
    def __init__(
        self,
        message: str = "Unable to load security dashboard data. Please try again.",
    ) -> None:
        super().__init__(
            code="DASHBOARD_UNAVAILABLE",
            message=message,
            status_code=503,
        )
