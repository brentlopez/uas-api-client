"""Tests for async authentication providers."""

import os
from datetime import datetime, timedelta

import aiohttp
import pytest

from uas_api_client.auth import (
    AsyncBearerTokenAuthProvider,
    AsyncUnityAuthProvider,
    UnityEndpoints,
)


class MockAsyncUnityAuthProvider(AsyncUnityAuthProvider):
    """Mock async auth provider for testing."""

    def __init__(self, token: str = "mock_token", expired: bool = False):
        self.token = token
        self.expired = expired
        self.endpoints = UnityEndpoints(
            base_url="https://api.unity.test",
            product_api="https://api.unity.test/v1/product",
            cdn_base="https://cdn.unity.test",
        )
        self._session: aiohttp.ClientSession | None = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def get_endpoints(self) -> UnityEndpoints:
        return self.endpoints

    def is_token_expired(self) -> bool:
        return self.expired

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


@pytest.mark.asyncio
class TestAsyncBearerTokenAuthProvider:
    """Tests for AsyncBearerTokenAuthProvider."""

    async def test_init_with_token(self):
        """Test initialization with access token."""
        endpoints = UnityEndpoints(
            base_url="https://api.unity.test",
            product_api="https://api.unity.test/product",
            cdn_base="https://cdn.unity.test",
        )
        
        provider = AsyncBearerTokenAuthProvider(
            access_token="test_token_123",
            endpoints=endpoints,
        )
        
        assert provider.access_token == "test_token_123"
        assert provider.get_endpoints() == endpoints
        await provider.close()

    async def test_init_from_env_var(self):
        """Test initialization from environment variable."""
        os.environ["UNITY_ACCESS_TOKEN"] = "env_token_456"
        try:
            provider = AsyncBearerTokenAuthProvider()
            assert provider.access_token == "env_token_456"
            await provider.close()
        finally:
            del os.environ["UNITY_ACCESS_TOKEN"]

    async def test_init_missing_token_raises_error(self):
        """Test that missing token raises ValueError."""
        # Ensure env var is not set
        if "UNITY_ACCESS_TOKEN" in os.environ:
            del os.environ["UNITY_ACCESS_TOKEN"]
        
        with pytest.raises(ValueError, match="access_token is required"):
            AsyncBearerTokenAuthProvider()

    async def test_get_session_creates_session(self):
        """Test that get_session creates and configures aiohttp session."""
        provider = AsyncBearerTokenAuthProvider(
            access_token="test_token",
            user_agent="TestAgent/1.0",
        )
        
        session = await provider.get_session()
        
        assert isinstance(session, aiohttp.ClientSession)
        assert session.headers["Authorization"] == "Bearer test_token"
        assert session.headers["Accept"] == "application/json"
        assert session.headers["User-Agent"] == "TestAgent/1.0"
        
        await provider.close()

    async def test_get_session_reuses_session(self):
        """Test that get_session reuses existing session."""
        provider = AsyncBearerTokenAuthProvider(access_token="test_token")
        
        session1 = await provider.get_session()
        session2 = await provider.get_session()
        
        assert session1 is session2
        
        await provider.close()

    async def test_ssl_verification_enabled_by_default(self):
        """Test that SSL verification is enabled by default."""
        provider = AsyncBearerTokenAuthProvider(access_token="test_token")
        
        assert provider.verify_ssl is True
        
        session = await provider.get_session()
        assert not session.connector._ssl is False  # SSL should be enabled
        
        await provider.close()

    async def test_token_expiration_check_expired(self):
        """Test token expiration check when token is expired."""
        # Token expired 1 hour ago
        expiration = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
        
        provider = AsyncBearerTokenAuthProvider(
            access_token="test_token",
            access_token_expiration=expiration,
        )
        
        assert provider.is_token_expired() is True
        await provider.close()

    async def test_token_expiration_check_not_expired(self):
        """Test token expiration check when token is valid."""
        # Token expires 1 hour from now
        expiration = int((datetime.now() + timedelta(hours=1)).timestamp() * 1000)
        
        provider = AsyncBearerTokenAuthProvider(
            access_token="test_token",
            access_token_expiration=expiration,
        )
        
        assert provider.is_token_expired() is False
        await provider.close()

    async def test_token_expiration_unknown(self):
        """Test that missing expiration is treated as expired."""
        provider = AsyncBearerTokenAuthProvider(
            access_token="test_token",
            access_token_expiration=None,
        )
        
        assert provider.is_token_expired() is True
        await provider.close()

    async def test_close_closes_session(self):
        """Test that close() properly closes the session."""
        provider = AsyncBearerTokenAuthProvider(access_token="test_token")
        
        session = await provider.get_session()
        assert not session.closed
        
        await provider.close()
        assert session.closed

    async def test_custom_timeout(self):
        """Test custom timeout configuration."""
        custom_timeout = aiohttp.ClientTimeout(total=60, connect=10)
        provider = AsyncBearerTokenAuthProvider(
            access_token="test_token",
            timeout=custom_timeout,
        )
        
        assert provider.timeout == custom_timeout
        await provider.close()


@pytest.mark.asyncio
class TestMockAsyncUnityAuthProvider:
    """Tests for mock auth provider (used in other tests)."""

    async def test_mock_provider_basic_functionality(self):
        """Test that mock provider works as expected."""
        provider = MockAsyncUnityAuthProvider()
        
        session = await provider.get_session()
        assert isinstance(session, aiohttp.ClientSession)
        
        endpoints = provider.get_endpoints()
        assert endpoints.base_url == "https://api.unity.test"
        
        assert provider.is_token_expired() is False
        
        await provider.close()

    async def test_mock_provider_expired_token(self):
        """Test mock provider with expired token."""
        provider = MockAsyncUnityAuthProvider(expired=True)
        
        assert provider.is_token_expired() is True
        
        await provider.close()
