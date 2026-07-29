class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, message: str | None = None) -> None:
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message or f"{resource} not found",
            status_code=404,
        )


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=401,
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=403,
        )


class EmailNotVerifiedError(AppException):
    def __init__(
        self,
        message: str = "Email address not verified. Check your inbox for the verification code.",
    ) -> None:
        super().__init__(
            code="EMAIL_NOT_VERIFIED",
            message=message,
            status_code=403,
        )


class AccountLockedError(AppException):
    def __init__(self, retry_after_seconds: int | None = None) -> None:
        message = "Account temporarily locked due to too many failed login attempts."
        if retry_after_seconds and retry_after_seconds > 0:
            minutes = max(1, (retry_after_seconds + 59) // 60)
            message = f"{message} Try again in {minutes} minute(s)."
        super().__init__(
            code="ACCOUNT_LOCKED",
            message=message,
            status_code=429,
        )
        self.retry_after_seconds = retry_after_seconds


class ValidationAppError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=409,
        )


class InternalServerError(AppException):
    def __init__(self, message: str = "An unexpected error occurred") -> None:
        super().__init__(
            code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=500,
        )


class NotImplementedFeatureError(AppException):
    def __init__(self, feature: str) -> None:
        super().__init__(
            code="NOT_IMPLEMENTED",
            message=f"{feature} is not available yet",
            status_code=501,
        )
