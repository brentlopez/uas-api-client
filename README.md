# Unity Asset Store API Client

A clean Python HTTP client library for Unity Asset Store. This library provides programmatic access to Unity Asset Store assets, including fetching asset metadata and downloading packages.

## Features

- ✅ **Clean API**: Simple, intuitive interface for Unity Asset Store
- ✅ **Type-safe**: Full type hints for better IDE support
- ✅ **No side effects**: No print statements, uses callbacks for progress
- ✅ **Rate limiting**: Built-in delays between requests
- ✅ **Error handling**: Comprehensive exception hierarchy
- ✅ **OAuth support**: Bearer token authentication (compatible with Unity Hub)

## Installation

```bash
# From source
cd ~/Projects/uas-api-client
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
from uas_api_client import UnityClient
from uas_adapter import UnityHubAuth
from uas_adapter.extractors import ElectronExtractor

# Extract tokens from Unity Hub
extractor = ElectronExtractor()
tokens = extractor.extract_tokens()

# Create auth provider (endpoints are hardcoded in adapter)
auth = UnityHubAuth(
    access_token=tokens['accessToken'],
    access_token_expiration=tokens['accessTokenExpiration'],
    refresh_token=tokens['refreshToken']
)

# Create client
client = UnityClient(auth, rate_limit_delay=1.5)

# Fetch asset information
asset = client.get_asset("330726")  # Example asset ID
print(f"Asset: {asset.title}")
print(f"Publisher: {asset.publisher}")
print(f"Category: {asset.category}")
print(f"Price: ${asset.price}")
print(f"Size: {asset.get_download_size_mb():.2f} MB")

# Check Unity version compatibility
if asset.is_compatible_with("2021.3.0f1"):
    print("Compatible with Unity 2021.3.0f1")

# Download asset (encrypted)
downloaded_path = client.download_asset(asset, output_dir="./downloads")
print(f"Downloaded to: {downloaded_path}")
```

## Progress Callbacks

Use callbacks to track progress without side effects:

```python
def progress_callback(message: str) -> None:
    print(f"[Progress] {message}")

# Fetch with progress
asset = client.get_asset("330726", on_progress=progress_callback)

# Download with progress
client.download_asset(asset, output_dir="./downloads", on_progress=progress_callback)
```

## Domain Models

### UnityAsset

Represents a Unity Asset Store asset with:
- Metadata (title, description, publisher, category)
- Pricing and rating information
- Unity version requirements
- Download information (URL, size, file count)
- Dependency tracking

### UnityCollection

Container for multiple assets with filtering and sorting:

```python
from uas_api_client import UnityCollection

# Create collection (or get from API in future)
collection = UnityCollection(assets=[asset1, asset2, asset3])

# Filter by category
tools = collection.filter_by_category("Tools")

# Filter by Unity version compatibility
compatible = collection.filter_by_unity_version("2021.3.0f1")

# Sort by price
sorted_by_price = collection.sort_by_price(reverse=True)

# Get specific asset
asset = collection.get_asset_by_id("330726")
```

## Authentication

This library uses OAuth Bearer tokens for authentication. The `uas-adapter` package provides:
- **Token extraction** from Unity Hub
- **API endpoints** (reverse-engineered)
- **Unity Hub headers** and authentication

```python
from uas_adapter import UnityHubAuth
from uas_adapter.extractors import ElectronExtractor

# Extract tokens from Unity Hub
extractor = ElectronExtractor()
tokens = extractor.extract_tokens()

# Create auth provider (includes reverse-engineered endpoints)
auth = UnityHubAuth(
    access_token=tokens['accessToken'],
    access_token_expiration=tokens['accessTokenExpiration'],
    refresh_token=tokens['refreshToken']
)

# Check if token is expired
if auth.is_token_expired():
    print("Token expired - please refresh token")
```

## Error Handling

Comprehensive exception hierarchy:

```python
from uas_api_client import (
    UnityError,  # Base exception
    UnityAuthenticationError,  # 401/403 errors
    UnityNotFoundError,  # 404 errors
    UnityAPIError,  # Other API errors
    UnityNetworkError,  # Network/timeout errors
    UnityTokenExpiredError,  # Token expiration
)

try:
    asset = client.get_asset("330726")
except UnityTokenExpiredError:
    print("Token expired - refresh tokens")
except UnityAuthenticationError:
    print("Authentication failed - check token")
except UnityNotFoundError:
    print("Asset not found - check ID")
except UnityAPIError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
except UnityNetworkError as e:
    print(f"Network error: {e.message}")
```

## Rate Limiting

Built-in rate limiting to be respectful of Unity's API:

```python
# Default: 1.5 second delay between requests
client = UnityClient(auth, rate_limit_delay=1.5)

# Custom delay
client = UnityClient(auth, rate_limit_delay=2.0)
```

## Package Decryption

**Note:** Downloaded packages are AES encrypted. This library downloads the encrypted `.unitypackage.encrypted` files. Use the `uas-adapter` package for decryption functionality.

## API Endpoints

The library uses Unity's package API. Endpoint URLs are provided by the auth provider (e.g., `uas-adapter`).

## Architecture

This library follows a clean architecture pattern:

### Two-Layer Model System
1. **API Response Types** (`models/api/`) - Raw API responses
2. **Domain Models** (`models/domain/`) - Business logic and utilities

### Separation of Concerns
- **Client** (`client.py`) - HTTP client with no reverse-engineering knowledge
- **Auth** (`auth.py`) - Abstract authentication providers
- **Exceptions** (`exceptions.py`) - Comprehensive error hierarchy

## Related Projects

- **uas-adapter** - Token extraction and package decryption (Tier 3)
- **asset-marketplace-client-system** - Architecture documentation

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/
black --check src/

# Format code
black src/
```

## Requirements

- Python 3.7+
- `requests` >= 2.31.0

## Limitations

- **Authentication**: Requires OAuth Bearer tokens from Unity Hub (use uas-adapter package)
- **Package Decryption**: Downloaded packages are encrypted (use uas-adapter package for decryption)
- **API Coverage**: Currently supports asset metadata and downloads only
- **Library Listing**: No user library listing endpoint yet (future work)

## License

MIT License - See LICENSE file

## Contributing

This is part of a private project ecosystem. For issues or improvements, please ensure:

1. Follow existing code patterns
2. Maintain the two-layer model system
3. No side effects (print, sys.exit)
4. Add tests for new functionality

## Support

For issues:
1. Check that tokens are valid and not expired
2. Verify asset ID is correct
3. Review exception messages for details

---

**Status:** ✅ Core functionality complete  
**Version:** 1.0.0  
**Last Updated:** December 2024
