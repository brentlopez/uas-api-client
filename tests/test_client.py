"""Tests for Unity client module."""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import requests

from uas_api_client.client import UnityClient
from uas_api_client.auth import ApiEndpoints
from uas_api_client.exceptions import (
    UnityAuthenticationError,
    UnityNotFoundError,
    UnityAPIError,
    UnityNetworkError,
    UnityTokenExpiredError,
)
from uas_api_client.models.domain.asset import UnityAsset


class MockAuthProvider:
    """Mock auth provider for testing."""

    def __init__(self, token_expired=False):
        self._token_expired = token_expired
        self.endpoints = ApiEndpoints(
            product_api="https://api.example.com/product",
            cdn_base="https://cdn.example.com"
        )

    def get_session(self):
        session = Mock(spec=requests.Session)
        return session

    def get_endpoints(self):
        return self.endpoints

    def is_token_expired(self):
        return self._token_expired


class TestUnityClient:
    """Tests for UnityClient."""

    def test_initialization(self):
        """Test client initialization."""
        auth = MockAuthProvider()
        client = UnityClient(auth, rate_limit_delay=1.0, timeout=30.0)

        assert client.auth == auth
        assert client.rate_limit_delay == 1.0
        assert client.timeout == 30.0
        assert client.session is not None
        assert client.endpoints is not None

    def test_context_manager(self):
        """Test context manager support."""
        auth = MockAuthProvider()
        
        with UnityClient(auth) as client:
            assert isinstance(client, UnityClient)
            # Session should be open during context
            assert client.session is not None
        
        # Session should be closed after context
        client.session.close.assert_called_once()

    def test_token_expiration_check(self):
        """Test token expiration checking."""
        auth = MockAuthProvider(token_expired=True)
        client = UnityClient(auth)

        with pytest.raises(UnityTokenExpiredError) as exc_info:
            client.get_asset("123456")
        
        assert "expired" in str(exc_info.value).lower()

    @patch('time.sleep')
    def test_rate_limiting(self, mock_sleep):
        """Test that rate limiting is applied."""
        auth = MockAuthProvider()
        client = UnityClient(auth, rate_limit_delay=2.0)
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "packageId": "123",
            "name": "Test Asset",
            "slug": "test-asset"
        }
        
        client.session.get = Mock(return_value=mock_response)
        
        # First request - no sleep
        client.get_asset("123")
        assert mock_sleep.call_count == 0
        
        # Second request - should sleep
        client.get_asset("456")
        assert mock_sleep.call_count == 1

    def test_authentication_error_401(self):
        """Test handling of 401 authentication error."""
        auth = MockAuthProvider()
        client = UnityClient(auth)
        
        mock_response = Mock()
        mock_response.status_code = 401
        client.session.get = Mock(return_value=mock_response)
        
        with pytest.raises(UnityAuthenticationError) as exc_info:
            client.get_asset("123456")
        
        assert exc_info.value.status_code == 401

    def test_not_found_error_404(self):
        """Test handling of 404 not found error."""
        auth = MockAuthProvider()
        client = UnityClient(auth)
        
        mock_response = Mock()
        mock_response.status_code = 404
        client.session.get = Mock(return_value=mock_response)
        
        with pytest.raises(UnityNotFoundError) as exc_info:
            client.get_asset("123456")
        
        assert exc_info.value.status_code == 404

    def test_generic_api_error(self):
        """Test handling of generic API errors."""
        auth = MockAuthProvider()
        client = UnityClient(auth)
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        client.session.get = Mock(return_value=mock_response)
        
        with pytest.raises(UnityAPIError) as exc_info:
            client.get_asset("123456")
        
        assert exc_info.value.status_code == 500

    def test_timeout_error(self):
        """Test handling of timeout errors."""
        auth = MockAuthProvider()
        client = UnityClient(auth, timeout=5.0)
        
        client.session.get = Mock(side_effect=requests.exceptions.Timeout)
        
        with pytest.raises(UnityNetworkError) as exc_info:
            client.get_asset("123456")
        
        assert "timeout" in str(exc_info.value).lower()

    def test_connection_error(self):
        """Test handling of connection errors."""
        auth = MockAuthProvider()
        client = UnityClient(auth)
        
        client.session.get = Mock(side_effect=requests.exceptions.ConnectionError)
        
        with pytest.raises(UnityNetworkError) as exc_info:
            client.get_asset("123456")
        
        assert "connection" in str(exc_info.value).lower()

    def test_get_asset_success(self):
        """Test successful asset retrieval."""
        auth = MockAuthProvider()
        client = UnityClient(auth)
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "packageId": "123456",
            "name": "Test Asset",
            "slug": "test-asset-123456",
            "originPrice": "19.99",
            "uploads": {
                "2021.3.0f1": {
                    "downloadS3key": "download/abc-123",
                    "downloadSize": "1000000",
                    "assetCount": "10"
                }
            },
            "category": {"name": "Tools"},
            "productPublisher": {"name": "Test Publisher"}
        }
        
        client.session.get = Mock(return_value=mock_response)
        
        asset = client.get_asset("123456")
        
        assert isinstance(asset, UnityAsset)
        assert asset.uid == "123456"
        assert asset.title == "Test Asset"
        assert asset.price == 19.99
        assert asset.download_url == "https://cdn.example.com/download/abc-123"

    def test_get_asset_with_progress_callback(self):
        """Test asset retrieval with progress callback."""
        auth = MockAuthProvider()
        client = UnityClient(auth)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "packageId": "123",
            "name": "Test Asset",
            "slug": "test"
        }
        
        client.session.get = Mock(return_value=mock_response)
        
        progress_calls = []
        
        def progress_callback(message):
            progress_calls.append(message)
        
        client.get_asset("123", on_progress=progress_callback)
        
        assert len(progress_calls) == 2
        assert "Fetching" in progress_calls[0]
        assert "fetched successfully" in progress_calls[1]

    @patch('builtins.open', new_callable=mock_open)
    @patch('requests.get')
    def test_download_asset_success(self, mock_requests_get, mock_file):
        """Test successful asset download."""
        auth = MockAuthProvider()
        client = UnityClient(auth)
        
        # Create asset with download URL
        asset = UnityAsset(
            uid="123456",
            title="Test Asset",
            download_url="https://cdn.example.com/download/abc-123"
        )
        
        # Mock download response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content = Mock(return_value=[b'chunk1', b'chunk2'])
        mock_requests_get.return_value = mock_response
        
        # Download
        result_path = client.download_asset(asset, output_dir="/tmp/test")
        
        # Verify
        assert isinstance(result_path, Path)
        assert str(result_path) == "/tmp/test/123456.unitypackage.encrypted"
        mock_file().write.assert_called()

    def test_download_asset_no_url(self):
        """Test download without URL raises error."""
        auth = MockAuthProvider()
        client = UnityClient(auth)
        
        asset = UnityAsset(uid="123", title="Test", download_url=None)
        
        with pytest.raises(UnityNotFoundError) as exc_info:
            client.download_asset(asset)
        
        assert "no download url" in str(exc_info.value).lower()

    @patch('requests.get')
    def test_download_asset_with_progress(self, mock_requests_get):
        """Test download with progress callback."""
        auth = MockAuthProvider()
        client = UnityClient(auth)
        
        asset = UnityAsset(
            uid="123",
            title="Test",
            download_url="https://cdn.example.com/download/abc"
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content = Mock(return_value=[b'data'])
        mock_requests_get.return_value = mock_response
        
        progress_calls = []
        
        def progress_callback(message):
            progress_calls.append(message)
        
        with patch('builtins.open', mock_open()):
            client.download_asset(asset, on_progress=progress_callback)
        
        assert len(progress_calls) == 2
        assert "Downloading" in progress_calls[0]
        assert "Downloaded to" in progress_calls[1]
