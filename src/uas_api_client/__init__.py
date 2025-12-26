"""Unity Asset Store API Client.

A clean Python HTTP client library for Unity Asset Store.

Extends asset-marketplace-client-core for consistency across marketplace clients.

Provides both synchronous and asynchronous APIs:
- Sync: UnityClient, UnityAuthProvider, BearerTokenAuthProvider
- Async: UnityAsyncClient, AsyncUnityAuthProvider, AsyncBearerTokenAuthProvider
"""

from .auth import (
    ApiEndpoints,
    AsyncBearerTokenAuthProvider,
    AsyncUnityAuthProvider,
    BearerTokenAuthProvider,
    UnityAuthProvider,
    UnityEndpoints,
)
from .client import UnityAsyncClient, UnityClient
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

__version__ = "2.1.0"

__all__ = [
    # Sync Client
    "UnityClient",
    # Async Client
    "UnityAsyncClient",
    # Sync Auth (for adapter implementations)
    "UnityAuthProvider",
    "BearerTokenAuthProvider",
    "UnityEndpoints",
    "ApiEndpoints",  # Backward compatibility alias
    # Async Auth
    "AsyncUnityAuthProvider",
    "AsyncBearerTokenAuthProvider",
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
