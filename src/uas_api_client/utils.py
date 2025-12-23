"""Security utilities for Unity Asset Store API client."""

from pathlib import Path

from asset_marketplace_core import MarketplaceValidationError, sanitize_filename


def safe_download_path(base_dir: Path, filename: str) -> Path:
    """Create a safe download path preventing directory traversal attacks.

    Args:
        base_dir: Base directory where files should be downloaded
        filename: Requested filename (potentially user-controlled)

    Returns:
        Sanitized, resolved path within base_dir

    Raises:
        MarketplaceValidationError: If path traversal is detected

    Example:
        >>> base = Path("/safe/downloads")
        >>> safe_download_path(base, "asset.unitypackage")
        Path("/safe/downloads/asset.unitypackage")
        >>> safe_download_path(base, "../etc/passwd")  # Raises MarketplaceValidationError
    """
    # Check for path traversal patterns before sanitization
    if ".." in filename or filename.startswith("/"):
        raise MarketplaceValidationError(
            f"Path traversal detected: {filename} resolves outside base directory"
        )

    # Sanitize the filename using core utility
    safe_name = sanitize_filename(filename)

    # Resolve the full path
    full_path = (base_dir / safe_name).resolve()
    base_resolved = base_dir.resolve()

    # Double-check: Verify the resolved path is still within base_dir
    try:
        full_path.relative_to(base_resolved)
    except ValueError as e:
        raise MarketplaceValidationError(
            f"Path traversal detected: {filename} resolves outside base directory"
        ) from e

    return full_path


__all__ = ["safe_download_path", "sanitize_filename"]
