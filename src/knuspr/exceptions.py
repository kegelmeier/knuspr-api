class KnusprError(Exception):
    """Base exception for all Knuspr API errors."""


class AuthenticationError(KnusprError):
    """Raised when login fails or session is expired/invalid."""


class RateLimitError(KnusprError):
    """Raised when the API returns HTTP 429."""


class APIError(KnusprError):
    """Raised when the API returns an error in the response envelope."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class NetworkError(KnusprError):
    """Raised on connection failures, timeouts, DNS resolution errors."""
