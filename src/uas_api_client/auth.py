"""Authentication providers for Unity Asset Store API."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class ApiEndpoints:
    """Unity Asset Store API endpoints.
    
    Note: Concrete endpoint URLs should be provided by the auth provider.
    This allows the adapter to handle platform-specific endpoint discovery.
    """

    product_api: str
    cdn_base: str

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


class UnityAuthProvider(ABC):
    """Abstract base class for Unity Asset Store authentication providers."""

    @abstractmethod
    def get_session(self) -> requests.Session:
        """Get authenticated requests session.

        Returns:
            Configured requests.Session with authentication
        """
        pass

    @abstractmethod
    def get_endpoints(self) -> ApiEndpoints:
        """Get API endpoints configuration.

        Returns:
            ApiEndpoints instance
        """
        pass

    @abstractmethod
    def is_token_expired(self) -> bool:
        """Check if the current access token is expired.

        Returns:
            True if token is expired, False otherwise
        """
        pass


class BearerTokenAuthProvider(UnityAuthProvider):
    """Authentication provider using OAuth Bearer tokens.

    This is the standard authentication method for Unity Asset Store API.
    Tokens can be obtained using the uas-adapter package.
    """

    def __init__(
        self,
        access_token: str,
        endpoints: ApiEndpoints,
        access_token_expiration: Optional[int] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Initialize Bearer token auth provider.

        Args:
            access_token: OAuth access token
            endpoints: API endpoint configuration (provided by adapter)
            access_token_expiration: Token expiration timestamp (milliseconds since epoch)
            user_agent: Optional User-Agent header (adapter should provide platform-specific value)
        """
        self.access_token = access_token
        self.access_token_expiration = access_token_expiration
        self.user_agent = user_agent
        self._endpoints = endpoints

    def get_session(self) -> requests.Session:
        """Get authenticated requests session.

        Returns:
            Session configured with Bearer token authentication
        """
        session = requests.Session()
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        
        if self.user_agent:
            headers["User-Agent"] = self.user_agent
        
        session.headers.update(headers)
        return session

    def get_endpoints(self) -> ApiEndpoints:
        """Get API endpoints configuration.

        Returns:
            ApiEndpoints instance
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

        from datetime import datetime

        # Token expiration is in milliseconds
        expiration_time = datetime.fromtimestamp(self.access_token_expiration / 1000)
        return datetime.now() >= expiration_time
