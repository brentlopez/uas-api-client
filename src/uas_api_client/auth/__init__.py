"""Authentication and endpoint configuration for Unity Asset Store API.

This module provides both synchronous and asynchronous authentication providers.
"""

from .async_ import AsyncBearerTokenAuthProvider, AsyncUnityAuthProvider
from .sync import (
    ApiEndpoints,
    BearerTokenAuthProvider,
    UnityAuthProvider,
    UnityEndpoints,
)

__all__ = [
    # Sync Auth
    "UnityAuthProvider",
    "BearerTokenAuthProvider",
    "UnityEndpoints",
    "ApiEndpoints",  # Backward compatibility alias
    # Async Auth
    "AsyncUnityAuthProvider",
    "AsyncBearerTokenAuthProvider",
]
