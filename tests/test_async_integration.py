"""Integration tests for async Unity Asset Store API client.

These tests require real Unity Asset Store credentials and make actual API calls.
They are marked as integration tests and skipped by default in CI.

To run these tests:
    pytest -m integration tests/test_async_integration.py
"""

import asyncio

import pytest

from uas_api_client import AsyncBearerTokenAuthProvider, UnityAsyncClient, UnityEndpoints


# Skip all tests in this module unless explicitly running integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def real_auth():
    """Create real auth provider from environment.
    
    Requires UNITY_ACCESS_TOKEN environment variable to be set.
    """
    # This will raise ValueError if token is not set, which is expected
    endpoints = UnityEndpoints(
        base_url="https://packages-v2.unity.com",
        product_api="https://packages-v2.unity.com/-/api/product",
        cdn_base="https://assetstorev1-prd-cdn.unity3d.com",
    )
    
    return AsyncBearerTokenAuthProvider(endpoints=endpoints)


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires real Unity credentials and valid asset ID")
async def test_real_get_asset(real_auth):
    """Test fetching a real asset from Unity Asset Store.
    
    This test is skipped by default. To run it:
    1. Set UNITY_ACCESS_TOKEN environment variable
    2. Replace ASSET_ID with a real asset ID you own
    3. Remove the skip decorator
    """
    ASSET_ID = "330726"  # Replace with a real asset ID
    
    async with UnityAsyncClient(real_auth) as client:
        asset = await client.get_asset(ASSET_ID)
        
        assert asset.uid == ASSET_ID
        assert asset.title is not None
        assert len(asset.title) > 0
        
        print(f"\nFetched asset: {asset.title}")
        print(f"Publisher: {asset.publisher}")
        print(f"Unity Version: {asset.unity_version}")


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires real Unity credentials")
async def test_real_get_library(real_auth):
    """Test fetching real library from Unity Asset Store.
    
    This test is skipped by default. To run it:
    1. Set UNITY_ACCESS_TOKEN environment variable
    2. Remove the skip decorator
    """
    async with UnityAsyncClient(real_auth) as client:
        library = await client.get_library(limit=5)
        
        assert library.total > 0
        assert len(library.results) > 0
        
        print(f"\nFound {library.total} assets in library")
        print(f"First 5 assets:")
        for item in library.results[:5]:
            print(f"  - {item.display_name} (ID: {item.package_id})")


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires real Unity credentials")
async def test_concurrent_real_requests(real_auth):
    """Test concurrent fetches of multiple real assets.
    
    Demonstrates async performance benefit over sync version.
    """
    # Replace with real asset IDs you own
    ASSET_IDS = ["330726", "123456", "789012"]  # Replace with real IDs
    
    async with UnityAsyncClient(real_auth) as client:
        # Fetch all assets concurrently
        tasks = [client.get_asset(asset_id) for asset_id in ASSET_IDS]
        assets = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes
        successful = [a for a in assets if not isinstance(a, Exception)]
        print(f"\nSuccessfully fetched {len(successful)}/{len(ASSET_IDS)} assets concurrently")
        
        for asset in successful:
            print(f"  - {asset.title}")
