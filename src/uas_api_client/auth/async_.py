"""Asynchronous authentication providers for Unity Asset Store API."""

import os
from abc import abstractmethod
from datetime import datetime

import aiohttp
from asset_marketplace_core import AsyncAuthProvider

from .sync import UnityEndpoints


class AsyncUnityAuthProvider(AsyncAuthProvider):
    """Abstract base class for async Unity Asset Store authentication providers.

    Extends AsyncAuthProvider from asset-marketplace-client-core with Unity-specific
    token expiration checking.
    """

    @abstractmethod
    async def get_session(self) -> aiohttp.ClientSession:
        """Get authenticated aiohttp session.

        Returns:
            Configured aiohttp.ClientSession with authentication
        """
        pass

    @abstractmethod
    def get_endpoints(self) -> UnityEndpoints:
        """Get API endpoints configuration.

        Note: Synchronous method - endpoint config doesn't require async.

        Returns:
            UnityEndpoints instance
        """
        pass

    @abstractmethod
    def is_token_expired(self) -> bool:
        """Check if the current access token is expired.

        Unity-specific method for token expiration checking.
        Note: Synchronous method as it's a simple comparison.

        Returns:
            True if token is expired, False otherwise
        """
        pass


class AsyncBearerTokenAuthProvider(AsyncUnityAuthProvider):
    """Async authentication provider using OAuth Bearer tokens.

    This is the standard authentication method for Unity Asset Store API.
    Tokens can be obtained using the uas-adapter package.

    Security features:
    - Supports environment variable loading (UNITY_ACCESS_TOKEN)
    - SSL certificate verification enabled by default
    - Configurable timeouts
    - Never logs tokens
    - Proper session lifecycle management
    """

    def __init__(
        self,
        access_token: str | None = None,
        endpoints: UnityEndpoints | None = None,
        access_token_expiration: int | None = None,
        user_agent: str | None = None,
        verify_ssl: bool = True,
        timeout: aiohttp.ClientTimeout | None = None,
    ) -> None:
        """Initialize async Bearer token auth provider.

        Args:
            access_token: OAuth access token (if None, loads from env var)
            endpoints: API endpoint configuration (provided by adapter)
            access_token_expiration: Token expiration timestamp (ms since epoch)
            user_agent: Optional User-Agent header (adapter-provided)
            verify_ssl: SSL verification (default: True, never disable in prod)
            timeout: Request timeout configuration (default: 5s connect, 30s total)

        Raises:
            ValueError: If access_token is None and env var is not set
        """
        # Load token from environment if not provided
        if access_token is None:
            access_token = os.environ.get("UNITY_ACCESS_TOKEN")
            if not access_token:
                raise ValueError(
                    "access_token is required. Pass it directly or set "
                    "UNITY_ACCESS_TOKEN environment variable."
                )

        self.access_token = access_token
        self.access_token_expiration = access_token_expiration
        self.user_agent = user_agent
        self.verify_ssl = verify_ssl
        self.timeout = timeout or aiohttp.ClientTimeout(total=30, connect=5)
        self._endpoints = endpoints or UnityEndpoints(base_url="")
        self._session: aiohttp.ClientSession | None = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get authenticated aiohttp session.

        Creates session on first call and reuses it for subsequent calls.
        Session is configured with Bearer token authentication and security settings.

        Returns:
            Session configured with Bearer token authentication and security settings
        """
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            }

            if self.user_agent:
                headers["User-Agent"] = self.user_agent

            # Security: Create connector with SSL verification
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)

            self._session = aiohttp.ClientSession(
                headers=headers, connector=connector, timeout=self.timeout
            )

        return self._session

    def get_endpoints(self) -> UnityEndpoints:
        """Get API endpoints configuration.

        Returns:
            UnityEndpoints instance
        """
        return self._endpoints

    def is_token_expired(self) -> bool:
        """Check if the current access token is expired.

        Returns:
            True if token is expired or expiration is unknown, False otherwise
        """
        if self.access_token_expiration is None:
            # If we don't have expiration info, assume expired for safety
            return True

        # Token expiration is in milliseconds
        expiration_time = datetime.fromtimestamp(self.access_token_expiration / 1000)
        return datetime.now() >= expiration_time

    async def close(self) -> None:
        """Clean up resources - close aiohttp session.

        Should be called when done with the auth provider to ensure proper
        cleanup of network connections.
        """
        if self._session and not self._session.closed:
            await self._session.close()
