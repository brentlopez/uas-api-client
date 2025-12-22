"""Exception hierarchy for Unity Asset Store API client."""

from typing import Optional


class UnityError(Exception):
    """Base exception for all Unity Asset Store client errors."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        """Initialize Unity error.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UnityAuthenticationError(UnityError):
    """Raised when authentication fails or tokens are invalid."""

    pass


class UnityAPIError(UnityError):
    """Raised when the Unity API returns an error response."""

    pass


class UnityNotFoundError(UnityError):
    """Raised when a requested asset or resource is not found."""

    pass


class UnityNetworkError(UnityError):
    """Raised when network-related errors occur."""

    pass


class UnityDependencyError(UnityError):
    """Raised when asset dependency resolution fails."""

    pass


class UnityVersionError(UnityError):
    """Raised when Unity version compatibility check fails."""

    pass


class UnityTokenExpiredError(UnityAuthenticationError):
    """Raised when access or refresh tokens have expired."""

    pass
