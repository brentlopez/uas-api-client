"""Asynchronous Unity Asset Store API client."""

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiohttp
from asset_marketplace_core import (
    AsyncMarketplaceClient,
    AsyncProgressCallback,
    DownloadResult,
)

if TYPE_CHECKING:
    import aiofiles

from ..auth.async_ import AsyncUnityAuthProvider
from ..exceptions import (
    UnityAPIError,
    UnityAuthenticationError,
    UnityNetworkError,
    UnityNotFoundError,
    UnityTokenExpiredError,
)
from ..models.api.product_response import ProductResponse
from ..models.api.purchases_response import PurchasesResponse
from ..models.domain.asset import UnityAsset
from ..models.domain.collection import UnityCollection
from ..utils import safe_download_path


class UnityAsyncClient(AsyncMarketplaceClient):
    """Async client for interacting with Unity Asset Store API.

    Extends AsyncMarketplaceClient from asset-marketplace-client-core.

    This client provides async methods to fetch assets, download packages,
    and manage Unity Asset Store content programmatically with high performance
    for concurrent operations.

    Example:
        ```python
        import asyncio
        from uas_api_client import UnityAsyncClient

        async def main():
            # Auth provider obtained from adapter (e.g., uas-adapter)
            auth = get_async_auth_provider()  # Adapter-specific implementation

            # Use client with async context manager
            async with UnityAsyncClient(auth) as client:
                asset = await client.get_asset("330726")
                print(f"Asset: {asset.title}")
                print(f"Size: {asset.get_download_size_mb():.2f} MB")

                # Download asset
                result = await client.download_asset("330726", output_dir="./downloads")
                if result.success:
                    print(f"Downloaded to: {result.files[0]}")

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        auth: AsyncUnityAuthProvider,
        rate_limit_delay: float = 1.5,
        timeout: float = 30.0,
    ) -> None:
        """Initialize async Unity Asset Store client.

        Args:
            auth: Async authentication provider
            rate_limit_delay: Delay between API requests in seconds (default: 1.5)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.auth = auth
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.endpoints = auth.get_endpoints()
        self._last_request_time: float | None = None

    def _check_token_expiration(self) -> None:
        """Check if access token is expired and raise error if so.

        Raises:
            UnityTokenExpiredError: If access token is expired
        """
        if self.auth.is_token_expired():
            raise UnityTokenExpiredError("Access token has expired. Please refresh tokens.")

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting delay between requests asynchronously."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    async def __aenter__(self) -> "UnityAsyncClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit - close session."""
        await self.close()

    async def close(self) -> None:
        """Close the client and clean up resources.

        Implements AsyncMarketplaceClient.close().
        """
        await self.auth.close()

    def _handle_response_errors(self, response: aiohttp.ClientResponse) -> None:
        """Handle HTTP response errors.

        Args:
            response: HTTP response to check

        Raises:
            UnityAuthenticationError: For 401/403 errors
            UnityNotFoundError: For 404 errors
            UnityAPIError: For other HTTP errors
        """
        if response.status in (401, 403):
            raise UnityAuthenticationError(
                "Authentication failed. Check your access token.", status_code=response.status
            )

        if response.status == 404:
            raise UnityNotFoundError(
                "Asset not found. Check the asset ID.", status_code=response.status
            )

        if response.status >= 400:
            raise UnityAPIError(f"API error: HTTP {response.status}", status_code=response.status)

    async def get_asset(self, asset_id: str) -> UnityAsset:
        """Get asset information from Unity Asset Store asynchronously.

        Args:
            asset_id: Unity asset package ID

        Returns:
            UnityAsset domain model with asset information

        Raises:
            UnityTokenExpiredError: If access token is expired
            UnityAuthenticationError: If authentication fails
            UnityNotFoundError: If asset not found
            UnityAPIError: If API request fails
            UnityNetworkError: If network error occurs
        """
        self._check_token_expiration()
        await self._apply_rate_limit()

        url = self.endpoints.get_product_url(asset_id)
        session = await self.auth.get_session()

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with session.get(url, timeout=timeout) as response:
                self._handle_response_errors(response)

                # Parse response
                data = await response.json()
                product_response = ProductResponse.from_dict(data)
                asset = product_response.to_asset()

                # Add full download URL if available
                if asset.download_s3_key:
                    asset.download_url = self.endpoints.get_cdn_url(asset.download_s3_key)

                return asset

        except TimeoutError as e:
            raise UnityNetworkError(f"Request timeout after {self.timeout}s") from e
        except aiohttp.ClientConnectionError as e:
            raise UnityNetworkError(f"Connection error: {e}") from e
        except aiohttp.ClientError as e:
            raise UnityNetworkError(f"Network error: {e}") from e

    async def get_library(
        self,
        offset: int = 0,
        limit: int = 0,
        search_text: str | None = None,
    ) -> PurchasesResponse:
        """Get user's Asset Store library/purchases asynchronously.

        Returns all assets the user owns/has access to in their Asset Store library.
        Use the package_id from each PurchaseItem to fetch full asset details with get_asset().

        Args:
            offset: Pagination offset (default: 0)
            limit: Number of results to return (default: 0 = all)
            search_text: Search query to filter results (default: None)

        Returns:
            PurchasesResponse containing library information

        Raises:
            UnityTokenExpiredError: If access token is expired
            UnityAuthenticationError: If authentication fails
            UnityAPIError: If API request fails
            UnityNetworkError: If network error occurs
        """
        self._check_token_expiration()
        await self._apply_rate_limit()

        # Construct purchases endpoint URL with query parameters
        base_url = self.endpoints.product_api.replace("/product", "")
        url = f"{base_url}/purchases?offset={offset}&limit={limit}"

        if search_text:
            url += f"&searchText={search_text}"

        session = await self.auth.get_session()

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with session.get(url, timeout=timeout) as response:
                self._handle_response_errors(response)

                # Parse response
                data = await response.json()
                purchases = PurchasesResponse.from_dict(data)

                return purchases

        except TimeoutError as e:
            raise UnityNetworkError(f"Request timeout after {self.timeout}s") from e
        except aiohttp.ClientConnectionError as e:
            raise UnityNetworkError(f"Connection error: {e}") from e
        except aiohttp.ClientError as e:
            raise UnityNetworkError(f"Network error: {e}") from e

    async def get_collection(self, **kwargs: Any) -> UnityCollection:
        """Get user's Asset Store library as a collection asynchronously.

        Implements AsyncMarketplaceClient.get_collection().

        This method maps to get_library() and converts PurchasesResponse
        to UnityCollection with minimal asset data.

        Args:
            **kwargs: Passed to get_library() (offset, limit, search_text)

        Returns:
            UnityCollection with minimal asset information from purchases

        Raises:
            UnityTokenExpiredError: If access token is expired
            UnityAuthenticationError: If authentication fails
            UnityAPIError: If API request fails
            UnityNetworkError: If network error occurs
        """
        # Get purchases response
        purchases = await self.get_library(**kwargs)

        # Convert PurchaseItems to minimal UnityAsset objects
        assets = [
            UnityAsset(
                uid=str(item.package_id),
                title=item.display_name,
                created_at=item.grant_time,
                raw_data={"purchase_item": vars(item)},
            )
            for item in purchases.results
        ]

        return UnityCollection(assets=assets, total_count=purchases.total)

    async def download_asset(
        self,
        asset_uid: str,
        output_dir: str | Path,
        progress_callback: AsyncProgressCallback | None = None,
        **kwargs: Any,
    ) -> DownloadResult:
        """Download asset package from CDN asynchronously.

        Implements AsyncMarketplaceClient.download_asset() with Unity-specific behavior.

        Note: Downloaded packages are AES encrypted. Use uas-adapter
        package for handling encrypted packages.

        Args:
            asset_uid: Unique identifier for the asset
            output_dir: Directory to save the downloaded file
            progress_callback: Optional async callback for progress updates
            **kwargs: Optional kwargs (reserved for future use)

        Returns:
            DownloadResult with success status, files, and metadata

        Raises:
            UnityNotFoundError: If asset not found or has no download URL
            UnityNetworkError: If download fails
        """
        try:
            # Fetch asset info to get download URL
            if progress_callback:
                await progress_callback.on_start(None)

            asset = await self.get_asset(asset_uid)

            if not asset.download_url:
                error_msg = f"Asset '{asset.title}' has no download URL"
                return DownloadResult(success=False, asset_uid=asset_uid, error=error_msg)

            await self._apply_rate_limit()

            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Create secure filename
            filename = f"{asset.uid}.unitypackage.encrypted"
            file_path = safe_download_path(output_path, filename)

            # CDN downloads don't require authentication
            # Create a separate session without auth for CDN
            cdn_timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as cdn_session:
                async with cdn_session.get(
                    asset.download_url, timeout=cdn_timeout
                ) as response:
                    # Get total size if available
                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    # Write file asynchronously (import aiofiles dynamically)
                    import aiofiles

                    async with aiofiles.open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            if chunk:
                                await f.write(chunk)
                                downloaded += len(chunk)
                                if progress_callback and total_size:
                                    await progress_callback.on_progress(downloaded, total_size)

            if progress_callback:
                await progress_callback.on_complete()

            return DownloadResult(
                success=True,
                asset_uid=asset_uid,
                files=[str(file_path)],
                metadata={
                    "unity_version": asset.unity_version,
                    "package_size": asset.package_size,
                    "encrypted": True,
                },
            )

        except UnityNotFoundError as e:
            if progress_callback:
                await progress_callback.on_error(e)
            return DownloadResult(success=False, asset_uid=asset_uid, error=f"Asset not found: {e}")
        except (TimeoutError, UnityNetworkError, aiohttp.ClientError) as e:
            if progress_callback:
                await progress_callback.on_error(e)
            return DownloadResult(success=False, asset_uid=asset_uid, error=f"Network error: {e}")
        except Exception as e:
            if progress_callback:
                await progress_callback.on_error(e)
            return DownloadResult(
                success=False, asset_uid=asset_uid, error=f"Unexpected error: {e}"
            )
