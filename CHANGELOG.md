# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-23

### Breaking Changes

- **Python 3.11+ Required**: Minimum Python version upgraded from 3.7 to 3.11
- **download_asset() Signature Changed**: Now takes `asset_uid: str` instead of `asset: UnityAsset`, returns `DownloadResult` instead of `Path`
- **ApiEndpoints Renamed**: Now `UnityEndpoints` (backward compatibility alias provided)
- **Exception Hierarchy**: All exceptions now inherit from `asset-marketplace-client-core` base exceptions
- **New Dependency**: `asset-marketplace-client-core>=0.1.0` required

### Added

- **Core Library Integration**: Extended `MarketplaceClient` from `asset-marketplace-client-core`
- **get_collection() Method**: New method implementing core interface, maps to `get_library()`
- **Security Features**: Environment variable support (`UNITY_ACCESS_TOKEN`), SSL verification, path traversal prevention
- **Security Tests**: Comprehensive test suite for security validation
- **New Utilities Module**: `utils.py` with `safe_download_path()` and `sanitize_filename()`
- **SECURITY.md**: Security policy and best practices documentation

### Changed

- **Build System**: Migrated from setuptools to hatchling
- **Domain Models**: `UnityAsset` extends `BaseAsset`, `UnityCollection` extends `BaseCollection`
- **Auth Provider**: `UnityAuthProvider` extends core `AuthProvider`
- **Client**: `UnityClient` extends `MarketplaceClient`
- **Code Quality**: Enabled mypy strict mode, using ruff for linting/formatting

### Backward Compatibility

- `ApiEndpoints` alias for `UnityEndpoints`
- `get_library()` kept alongside `get_collection()`
- `on_progress` callbacks still supported

## [1.0.0] - 2024-12-22

### Added
- Initial release of uas-api-client
- Core `UnityClient` for API interactions
- `BearerTokenAuthProvider` for OAuth authentication
- Domain models: `UnityAsset` and `UnityCollection`
- API response models: `ProductResponse`
- Comprehensive exception hierarchy
- Rate limiting support
- Progress callback system (no side effects)
- Asset metadata fetching via `get_asset()`
- Asset downloading via `download_asset()`
- Unity version compatibility checking
- Collection filtering and sorting capabilities
- Full type hints for better IDE support
- Documentation and examples

### Features
- Fetch asset information from Unity Asset Store API
- Download encrypted .unitypackage files from CDN
- Check token expiration
- Handle authentication, network, and API errors gracefully
- Filter assets by category, publisher, and Unity version compatibility
- Sort assets by title or price
- Progress callbacks for async operations

### Notes
- Downloaded packages are AES encrypted and require uas-adapter for decryption
- Requires Unity Hub tokens (extract using uas-adapter)
- Follows clean architecture with two-layer model system
- No side effects (print statements, etc.)
- Built-in rate limiting (default 1.5s between requests)
