"""Security tests for uas-api-client."""

import io
import logging
from pathlib import Path

import pytest

from uas_api_client.auth import BearerTokenAuthProvider, UnityEndpoints
from uas_api_client.exceptions import MarketplaceValidationError
from uas_api_client.utils import safe_download_path


class TestPathTraversalPrevention:
    """Test path traversal attack prevention."""

    def test_safe_download_path_normal(self, tmp_path: Path) -> None:
        """Test safe_download_path with normal filename."""
        result = safe_download_path(tmp_path, "asset.unitypackage")
        assert result == tmp_path / "asset.unitypackage"
        assert result.is_relative_to(tmp_path)

    def test_safe_download_path_prevents_parent_traversal(
        self, tmp_path: Path
    ) -> None:
        """Test that ../ path traversal is prevented."""
        with pytest.raises(MarketplaceValidationError, match="Path traversal detected"):
            safe_download_path(tmp_path, "../etc/passwd")

    def test_safe_download_path_prevents_absolute_paths(self, tmp_path: Path) -> None:
        """Test that absolute paths are prevented."""
        with pytest.raises(MarketplaceValidationError, match="Path traversal detected"):
            safe_download_path(tmp_path, "/etc/passwd")

    def test_safe_download_path_prevents_multiple_traversals(
        self, tmp_path: Path
    ) -> None:
        """Test that multiple ../ attempts are prevented."""
        with pytest.raises(MarketplaceValidationError, match="Path traversal detected"):
            safe_download_path(tmp_path, "../../etc/passwd")

    def test_safe_download_path_sanitizes_filename(self, tmp_path: Path) -> None:
        """Test that filenames are sanitized."""
        # Invalid characters should be removed/replaced
        result = safe_download_path(tmp_path, "asset:version*2.0.unitypackage")
        # Sanitization should handle special characters
        assert result.is_relative_to(tmp_path)
        assert ".." not in str(result)


class TestTokenSecurity:
    """Test that tokens are never logged."""

    def test_no_token_in_logs(self, tmp_path: Path) -> None:
        """Test that access tokens are never logged."""
        # Set up logging capture
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.DEBUG)
        logging.root.addHandler(handler)
        logging.root.setLevel(logging.DEBUG)

        secret_token = "secret_access_token_12345"

        try:
            # Create auth provider
            endpoints = UnityEndpoints(
                base_url="https://api.unity.com",
                product_api="https://api.unity.com/product",
                cdn_base="https://cdn.unity.com",
            )

            auth = BearerTokenAuthProvider(
                access_token=secret_token,
                endpoints=endpoints,
                verify_ssl=True,
            )

            # Get session (this should not log the token)
            session = auth.get_session()

            # Get log output
            log_output = log_stream.getvalue()

            # Verify token is not in logs
            assert (
                secret_token not in log_output
            ), "Access token found in logs - security violation!"

            # Verify session has the token (it's working)
            assert session.headers["Authorization"] == f"Bearer {secret_token}"

        finally:
            logging.root.removeHandler(handler)

    def test_bearer_token_auth_does_not_print_token(self) -> None:
        """Test that BearerTokenAuthProvider doesn't expose token in string representation."""
        endpoints = UnityEndpoints(
            base_url="https://api.unity.com",
            product_api="https://api.unity.com/product",
            cdn_base="https://cdn.unity.com",
        )

        secret_token = "secret_token_abc123"

        auth = BearerTokenAuthProvider(
            access_token=secret_token,
            endpoints=endpoints,
        )

        # Check various string representations
        assert secret_token not in str(auth)
        assert secret_token not in repr(auth)
