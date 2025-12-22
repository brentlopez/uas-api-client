"""Unity Asset Store API Client.

A clean Python HTTP client library for Unity Asset Store.
"""

from .auth import ApiEndpoints, UnityAuthProvider
from .client import UnityClient
from .exceptions import (
    UnityAPIError,
    UnityAuthenticationError,
    UnityDependencyError,
    UnityError,
    UnityNetworkError,
    UnityNotFoundError,
    UnityTokenExpiredError,
    UnityVersionError,
)
from .models import ProductResponse, UnityAsset, UnityCollection

__version__ = "1.0.0"

__all__ = [
    # Client
    "UnityClient",
    # Auth (for adapter implementations)
    "UnityAuthProvider",
    "ApiEndpoints",
    # Models
    "UnityAsset",
    "UnityCollection",
    "ProductResponse",
    # Exceptions
    "UnityError",
    "UnityAPIError",
    "UnityAuthenticationError",
    "UnityNotFoundError",
    "UnityNetworkError",
    "UnityDependencyError",
    "UnityVersionError",
    "UnityTokenExpiredError",
]
