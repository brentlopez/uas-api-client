"""Exception hierarchy for Unity Asset Store API client."""

from asset_marketplace_core import (
    MarketplaceAPIError,
    MarketplaceAuthenticationError,
    MarketplaceError,
    MarketplaceNetworkError,
    MarketplaceNotFoundError,
    MarketplaceValidationError,
)


class UnityError(MarketplaceError):
    """Base exception for all Unity Asset Store client errors.

    Inherits from MarketplaceError to maintain compatibility with
    the asset-marketplace-client-core exception hierarchy.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize Unity error.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UnityAuthenticationError(UnityError, MarketplaceAuthenticationError):
    """Raised when authentication fails or tokens are invalid.

    Inherits from both UnityError and MarketplaceAuthenticationError
    for compatibility with both hierarchies.
    """

    pass


class UnityAPIError(UnityError, MarketplaceAPIError):
    """Raised when the Unity API returns an error response.

    Inherits from both UnityError and MarketplaceAPIError
    for compatibility with both hierarchies.
    """

    pass


class UnityNotFoundError(UnityError, MarketplaceNotFoundError):
    """Raised when a requested asset or resource is not found.

    Inherits from both UnityError and MarketplaceNotFoundError
    for compatibility with both hierarchies.
    """

    pass


class UnityNetworkError(UnityError, MarketplaceNetworkError):
    """Raised when network-related errors occur.

    Inherits from both UnityError and MarketplaceNetworkError
    for compatibility with both hierarchies.
    """

    pass


class UnityDependencyError(UnityError):
    """Raised when asset dependency resolution fails.

    Unity-specific exception for dependency-related errors.
    """

    pass


class UnityVersionError(UnityError):
    """Raised when Unity version compatibility check fails.

    Unity-specific exception for version compatibility issues.
    """

    pass


class UnityTokenExpiredError(UnityAuthenticationError):
    """Raised when access or refresh tokens have expired.

    Unity-specific exception for token expiration.
    """

    pass


# Export MarketplaceValidationError for use in security utilities
__all__ = [
    "UnityError",
    "UnityAuthenticationError",
    "UnityAPIError",
    "UnityNotFoundError",
    "UnityNetworkError",
    "UnityDependencyError",
    "UnityVersionError",
    "UnityTokenExpiredError",
    "MarketplaceValidationError",
]
