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
