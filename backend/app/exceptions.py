class DomainError(Exception):
    """Base class for business errors, mapped to HTTP responses in main.py."""

    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class UnprocessableFeedError(DomainError):
    status_code = 422
