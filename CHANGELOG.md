# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
