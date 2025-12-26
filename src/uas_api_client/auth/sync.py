"""Authentication providers for Unity Asset Store API."""

import os
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from asset_marketplace_core import AuthProvider, EndpointConfig


@dataclass
class UnityEndpoints(EndpointConfig):
    """Unity Asset Store API endpoints.

    Extends EndpointConfig from asset-marketplace-client-core with
    Unity-specific endpoint URLs.

    Note: Concrete endpoint URLs should be provided by the auth provider.
    This allows the adapter to handle platform-specific endpoint discovery.
    """

    base_url: str = ""  # Override parent to provide default
    product_api: str = ""
    cdn_base: str = ""

    def get_product_url(self, asset_id: str) -> str:
        """Get URL for asset product info.

        Args:
            asset_id: Unity asset ID

        Returns:
            Full API URL for the asset
        """
        return f"{self.product_api}/{asset_id}"

    def get_cdn_url(self, download_s3_key: str) -> str:
        """Get CDN URL for asset download.

        Args:
            download_s3_key: S3 key from API response (e.g., "download/uuid")

        Returns:
            Full CDN URL for the download
        """
        return f"{self.cdn_base}/{download_s3_key}"


# Backward compatibility alias
ApiEndpoints = UnityEndpoints


class UnityAuthProvider(AuthProvider):
    """Abstract base class for Unity Asset Store authentication providers.

    Extends AuthProvider from asset-marketplace-client-core with Unity-specific
    token expiration checking.
    """

    @abstractmethod
    def get_session(self) -> Any:
        """Get authenticated requests session.

        Returns:
            Configured requests.Session with authentication
        """
        pass

    @abstractmethod
    def get_endpoints(self) -> UnityEndpoints:
        """Get API endpoints configuration.

        Returns:
            UnityEndpoints instance
        """
        pass

    @abstractmethod
    def is_token_expired(self) -> bool:
        """Check if the current access token is expired.

        Unity-specific method for token expiration checking.

        Returns:
            True if token is expired, False otherwise
        """
        pass


class BearerTokenAuthProvider(UnityAuthProvider):
    """Authentication provider using OAuth Bearer tokens.

    This is the standard authentication method for Unity Asset Store API.
    Tokens can be obtained using the uas-adapter package.

    Security features:
    - Supports environment variable loading (UNITY_ACCESS_TOKEN)
    - SSL certificate verification enabled by default
    - Configurable timeouts
    - Never logs tokens
    """

    def __init__(
        self,
        access_token: str | None = None,
        endpoints: UnityEndpoints | None = None,
        access_token_expiration: int | None = None,
        user_agent: str | None = None,
        verify_ssl: bool = True,
        timeout: tuple[int, int] = (5, 30),
    ) -> None:
        """Initialize Bearer token auth provider.

        Args:
            access_token: OAuth access token (if None, loads from env var)
            endpoints: API endpoint configuration (provided by adapter)
            access_token_expiration: Token expiration timestamp (ms since epoch)
            user_agent: Optional User-Agent header (adapter-provided)
            verify_ssl: SSL verification (default: True, never disable in prod)
            timeout: Request timeout as (connect_timeout, read_timeout) in secs

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
        self.timeout = timeout
        self._endpoints = endpoints or UnityEndpoints(base_url="")

    def get_session(self) -> requests.Session:
        """Get authenticated requests session.

        Returns:
            Session configured with Bearer token authentication and security settings
        """
        session = requests.Session()

        # Security: Enable SSL verification (never disable in production)
        session.verify = self.verify_ssl

        # Security: Set timeouts to prevent hanging requests
        # This is applied per-request in the client, stored here for reference

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

        if self.user_agent:
            headers["User-Agent"] = self.user_agent

        session.headers.update(headers)
        return session

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

    def close(self) -> None:
        """Clean up resources.

        Default implementation does nothing as session is managed by client.
        """
        pass
