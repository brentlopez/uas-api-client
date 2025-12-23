"""Unity Asset Store API client."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests
from asset_marketplace_core import DownloadResult, MarketplaceClient, ProgressCallback

from .auth import UnityAuthProvider
from .exceptions import (
    UnityAPIError,
    UnityAuthenticationError,
    UnityNetworkError,
    UnityNotFoundError,
    UnityTokenExpiredError,
)
from .models.api.product_response import ProductResponse
from .models.api.purchases_response import PurchasesResponse
from .models.domain.asset import UnityAsset
from .models.domain.collection import UnityCollection
from .utils import safe_download_path


class UnityClient(MarketplaceClient):
    """Client for interacting with Unity Asset Store API.

    Extends MarketplaceClient from asset-marketplace-client-core.

    This client provides methods to fetch assets, download packages,
    and manage Unity Asset Store content programmatically.

    Example:
        ```python
        from uas_api_client import UnityClient

        # Auth provider obtained from adapter (e.g., uas-adapter)
        # See adapter documentation for authentication setup
        auth = get_auth_provider()  # Adapter-specific implementation

        # Use client with context manager
        with UnityClient(auth) as client:
            asset = client.get_asset("330726")
            print(f"Asset: {asset.title}")
            print(f"Size: {asset.get_download_size_mb():.2f} MB")

            # Download asset
            path = client.download_asset(asset, output_dir="./downloads")
            print(f"Downloaded to: {path}")
        ```
    """

    def __init__(
        self,
        auth: UnityAuthProvider,
        rate_limit_delay: float = 1.5,
        timeout: float = 30.0,
    ) -> None:
        """Initialize Unity Asset Store client.

        Args:
            auth: Authentication provider
            rate_limit_delay: Delay between API requests in seconds (default: 1.5)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.auth = auth
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.session = auth.get_session()
        self.endpoints = auth.get_endpoints()
        self._last_request_time: float | None = None

    def _check_token_expiration(self) -> None:
        """Check if access token is expired and raise error if so.

        Raises:
            UnityTokenExpiredError: If access token is expired
        """
        if self.auth.is_token_expired():
            raise UnityTokenExpiredError("Access token has expired. Please refresh tokens.")

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting delay between requests."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - close session."""
        self.close()

    def close(self) -> None:
        """Close the client and clean up resources.

        Implements MarketplaceClient.close().
        """
        if hasattr(self, "session"):
            self.session.close()

    def _handle_response_errors(self, response: requests.Response) -> None:
        """Handle HTTP response errors.

        Args:
            response: HTTP response to check

        Raises:
            UnityAuthenticationError: For 401/403 errors
            UnityNotFoundError: For 404 errors
            UnityAPIError: For other HTTP errors
        """
        if response.status_code in (401, 403):
            raise UnityAuthenticationError(
                "Authentication failed. Check your access token.", status_code=response.status_code
            )

        if response.status_code == 404:
            raise UnityNotFoundError(
                "Asset not found. Check the asset ID.", status_code=response.status_code
            )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise UnityAPIError(
                f"API error: {e}",
                status_code=e.response.status_code if e.response else None,
            ) from e

    def get_asset(
        self, asset_id: str, on_progress: Callable[[str], None] | None = None
    ) -> UnityAsset:
        """Get asset information from Unity Asset Store.

        Args:
            asset_id: Unity asset package ID
            on_progress: Optional callback for progress updates

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
        self._apply_rate_limit()

        if on_progress:
            on_progress(f"Fetching asset {asset_id}...")

        url = self.endpoints.get_product_url(asset_id)

        try:
            response = self.session.get(url, timeout=self.timeout)
            self._handle_response_errors(response)

            # Parse response
            data = response.json()
            product_response = ProductResponse.from_dict(data)
            asset = product_response.to_asset()

            # Add full download URL if available
            if asset.download_s3_key:
                asset.download_url = self.endpoints.get_cdn_url(asset.download_s3_key)

            if on_progress:
                on_progress(f"Asset '{asset.title}' fetched successfully")

            return asset

        except requests.exceptions.Timeout as e:
            raise UnityNetworkError(f"Request timeout after {self.timeout}s") from e
        except requests.exceptions.ConnectionError as e:
            raise UnityNetworkError(f"Connection error: {e}") from e
        except requests.exceptions.RequestException as e:
            raise UnityNetworkError(f"Network error: {e}") from e

    def get_library(
        self,
        offset: int = 0,
        limit: int = 0,
        search_text: str | None = None,
        on_progress: Callable[[str], None] | None = None,
    ) -> PurchasesResponse:
        """Get user's Asset Store library/purchases.

        Returns all assets the user owns/has access to in their Asset Store library.
        Use the package_id from each PurchaseItem to fetch full asset details with get_asset().

        Endpoint reference: Unity Editor uses `/-/api/purchases` with query parameters.
        See: https://github.com/Unity-Technologies/UnityCsReference/blob/master/Modules/PackageManagerUI/Editor/Services/AssetStore/AssetStoreRestAPI.cs

        Args:
            offset: Pagination offset (default: 0)
            limit: Number of results to return (default: 0 = all)
            search_text: Search query to filter results (default: None)
            on_progress: Optional callback for progress updates

        Returns:
            PurchasesResponse containing library information

        Raises:
            UnityTokenExpiredError: If access token is expired
            UnityAuthenticationError: If authentication fails
            UnityAPIError: If API request fails
            UnityNetworkError: If network error occurs

        Example:
            ```python
            # Get all library items
            library = client.get_library()
            print(f"Total assets: {library.total}")

            # Get paginated results
            page = client.get_library(offset=0, limit=10)
            print(f"First 10 of {page.total} assets")

            # Search library
            results = client.get_library(search_text="fantasy")
            print(f"Found {len(results.results)} fantasy assets")

            # Get package IDs
            package_ids = library.get_package_ids()

            # Fetch full details for each asset
            for package_id in package_ids[:5]:  # First 5 assets
                asset = client.get_asset(str(package_id))
                print(f"{asset.title} - {asset.publisher}")
            ```
        """
        self._check_token_expiration()
        self._apply_rate_limit()

        if on_progress:
            on_progress("Fetching Asset Store library...")

        # Construct purchases endpoint URL with query parameters
        base_url = self.endpoints.product_api.replace("/product", "")
        url = f"{base_url}/purchases?offset={offset}&limit={limit}"

        if search_text:
            url += f"&searchText={search_text}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            self._handle_response_errors(response)

            # Parse response
            data = response.json()
            purchases = PurchasesResponse.from_dict(data)

            if on_progress:
                on_progress(f"Found {purchases.total} assets in library")

            return purchases

        except requests.exceptions.Timeout as e:
            raise UnityNetworkError(f"Request timeout after {self.timeout}s") from e
        except requests.exceptions.ConnectionError as e:
            raise UnityNetworkError(f"Connection error: {e}") from e
        except requests.exceptions.RequestException as e:
            raise UnityNetworkError(f"Network error: {e}") from e

    def get_collection(self, **kwargs: Any) -> UnityCollection:
        """Get user's Asset Store library as a collection.

        Implements MarketplaceClient.get_collection().

        This method maps to get_library() and converts PurchasesResponse
        to UnityCollection with minimal asset data.

        Args:
            **kwargs: Passed to get_library() (offset, limit, search_text, on_progress)

        Returns:
            UnityCollection with minimal asset information from purchases

        Raises:
            UnityTokenExpiredError: If access token is expired
            UnityAuthenticationError: If authentication fails
            UnityAPIError: If API request fails
            UnityNetworkError: If network error occurs
        """
        # Get purchases response
        purchases = self.get_library(**kwargs)

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

    def download_asset(
        self,
        asset_uid: str,
        output_dir: str | Path,
        progress_callback: ProgressCallback | None = None,
        **kwargs: Any,
    ) -> DownloadResult:
        """Download asset package from CDN.

        Implements MarketplaceClient.download_asset() with Unity-specific behavior.

        Note: Downloaded packages are AES encrypted. Use uas-adapter
        package for handling encrypted packages.

        Args:
            asset_uid: Unique identifier for the asset
            output_dir: Directory to save the downloaded file
            progress_callback: Optional callback for progress updates
            **kwargs: Optional kwargs including:
                - on_progress: Legacy callback (Callable[[str], None])

        Returns:
            DownloadResult with success status, files, and metadata

        Raises:
            UnityNotFoundError: If asset not found or has no download URL
            UnityNetworkError: If download fails
        """
        # Support legacy on_progress callback
        on_progress = kwargs.get("on_progress")

        try:
            # Fetch asset info to get download URL
            if on_progress:
                on_progress(f"Fetching asset {asset_uid} info...")
            if progress_callback:
                progress_callback.on_start(None)

            asset = self.get_asset(asset_uid, on_progress=on_progress)

            if not asset.download_url:
                error_msg = f"Asset '{asset.title}' has no download URL"
                return DownloadResult(success=False, asset_uid=asset_uid, error=error_msg)

            self._apply_rate_limit()

            if on_progress:
                on_progress(f"Downloading '{asset.title}'...")

            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Create secure filename
            filename = f"{asset.uid}.unitypackage.encrypted"
            file_path = safe_download_path(output_path, filename)

            # CDN downloads don't require authentication
            response = requests.get(asset.download_url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            # Get total size if available
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            # Write file
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size:
                            progress_callback.on_progress(downloaded, total_size)

            if on_progress:
                on_progress(f"Downloaded to {file_path}")
            if progress_callback:
                progress_callback.on_complete()

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
                progress_callback.on_error(e)
            return DownloadResult(success=False, asset_uid=asset_uid, error=f"Asset not found: {e}")
        except UnityNetworkError as e:
            if progress_callback:
                progress_callback.on_error(e)
            return DownloadResult(success=False, asset_uid=asset_uid, error=f"Network error: {e}")
        except Exception as e:
            if progress_callback:
                progress_callback.on_error(e)
            return DownloadResult(
                success=False, asset_uid=asset_uid, error=f"Unexpected error: {e}"
            )
