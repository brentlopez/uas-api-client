"""Unity Asset Store API Client.

A clean Python HTTP client library for Unity Asset Store.

Extends asset-marketplace-client-core for consistency across marketplace clients.
"""

from .auth import ApiEndpoints, UnityAuthProvider, UnityEndpoints
from .client import UnityClient
from .exceptions import (
    MarketplaceValidationError,
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
from .utils import safe_download_path, sanitize_filename

__version__ = "2.0.0"

__all__ = [
    # Client
    "UnityClient",
    # Auth (for adapter implementations)
    "UnityAuthProvider",
    "UnityEndpoints",
    "ApiEndpoints",  # Backward compatibility alias
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
    "MarketplaceValidationError",
    # Utilities
    "safe_download_path",
    "sanitize_filename",
]
