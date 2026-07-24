"""Domain and application exceptions."""


class AppError(Exception):
    """Base exception safe to expose to API clients."""

    def __init__(
        self, message: str, status_code: int = 400, errors: list[dict] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or []


class AuthenticationError(AppError):
    """Authentication failed."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message, 401)


class AuthorizationError(AppError):
    """Access to a resource is forbidden."""

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message, 403)


class ConflictError(AppError):
    """A resource conflicts with existing state."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 409)


class NotFoundError(AppError):
    """A resource was not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, 404)
