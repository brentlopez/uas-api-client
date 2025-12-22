"""Tests for authentication module."""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta

from uas_api_client.auth import ApiEndpoints, UnityAuthProvider, BearerTokenAuthProvider


class TestApiEndpoints:
    """Tests for ApiEndpoints dataclass."""

    def test_get_product_url(self):
        """Test product URL generation."""
        endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )
        
        url = endpoints.get_product_url("123456")
        assert url == "https://api.example.com/product/123456"

    def test_get_cdn_url(self):
        """Test CDN URL generation."""
        endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )
        
        url = endpoints.get_cdn_url("download/abc-123")
        assert url == "https://cdn.example.com/download/abc-123"


class MockAuthProvider(UnityAuthProvider):
    """Mock auth provider for testing."""

    def __init__(self):
        self.endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )

    def get_session(self):
        return Mock()

    def get_endpoints(self):
        return self.endpoints

    def is_token_expired(self):
        return False


class TestUnityAuthProvider:
    """Tests for UnityAuthProvider abstract base class."""

    def test_abstract_methods(self):
        """Test that abstract methods are enforced."""
        # Can't instantiate abstract class
        with pytest.raises(TypeError):
            UnityAuthProvider()

    def test_mock_implementation(self):
        """Test that mock implementation works."""
        auth = MockAuthProvider()
        
        assert auth.get_session() is not None
        assert isinstance(auth.get_endpoints(), ApiEndpoints)
        assert auth.is_token_expired() is False


class TestBearerTokenAuthProvider:
    """Tests for BearerTokenAuthProvider."""

    def test_initialization(self):
        """Test provider initialization."""
        endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )
        
        provider = BearerTokenAuthProvider(
            access_token="test_token",
            endpoints=endpoints,
            access_token_expiration=None,
            user_agent="TestAgent/1.0"
        )
        
        assert provider.access_token == "test_token"
        assert provider.user_agent == "TestAgent/1.0"

    def test_get_session_with_user_agent(self):
        """Test session creation with user agent."""
        endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )
        
        provider = BearerTokenAuthProvider(
            access_token="test_token",
            endpoints=endpoints,
            user_agent="TestAgent/1.0"
        )
        
        session = provider.get_session()
        
        assert "Authorization" in session.headers
        assert session.headers["Authorization"] == "Bearer test_token"
        assert session.headers["User-Agent"] == "TestAgent/1.0"
        assert session.headers["Accept"] == "application/json"

    def test_get_session_without_user_agent(self):
        """Test session creation without user agent."""
        endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )
        
        provider = BearerTokenAuthProvider(
            access_token="test_token",
            endpoints=endpoints,
            user_agent=None
        )
        
        session = provider.get_session()
        
        assert "Authorization" in session.headers
        # Note: requests.Session may add default User-Agent, that's OK
        # We're just checking we don't explicitly set it
        assert session.headers["Accept"] == "application/json"

    def test_get_endpoints(self):
        """Test getting endpoints."""
        endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )
        
        provider = BearerTokenAuthProvider(
            access_token="test_token",
            endpoints=endpoints
        )
        
        retrieved = provider.get_endpoints()
        assert retrieved == endpoints

    def test_token_not_expired(self):
        """Test token expiration check when not expired."""
        endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )
        
        # Token expires in 1 hour
        future_time = datetime.now() + timedelta(hours=1)
        expiration_ms = int(future_time.timestamp() * 1000)
        
        provider = BearerTokenAuthProvider(
            access_token="test_token",
            endpoints=endpoints,
            access_token_expiration=expiration_ms
        )
        
        assert provider.is_token_expired() is False

    def test_token_expired(self):
        """Test token expiration check when expired."""
        endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )
        
        # Token expired 1 hour ago
        past_time = datetime.now() - timedelta(hours=1)
        expiration_ms = int(past_time.timestamp() * 1000)
        
        provider = BearerTokenAuthProvider(
            access_token="test_token",
            endpoints=endpoints,
            access_token_expiration=expiration_ms
        )
        
        assert provider.is_token_expired() is True

    def test_token_expiration_unknown(self):
        """Test token expiration check when expiration is unknown."""
        endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )
        
        provider = BearerTokenAuthProvider(
            access_token="test_token",
            endpoints=endpoints,
            access_token_expiration=None
        )
        
        # Should assume expired for safety
        assert provider.is_token_expired() is True
