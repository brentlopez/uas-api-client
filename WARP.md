# WARP.md - AI Assistant Guide for uas-api-client

This document provides guidance for AI assistants working on the `uas-api-client` project.

## Project Overview

**uas-api-client** is a clean Python HTTP client library for the Unity Asset Store. It provides programmatic access to Unity Asset Store assets, including fetching metadata and downloading packages.

### Key Principles

1. **Clean Architecture** - No reverse-engineering evidence in this library
2. **No Side Effects** - Never use `print()`, `sys.exit()`, etc. Use callbacks instead
3. **Two-Layer Model System** - API responses vs Domain models
4. **Type Safety** - Full type hints throughout
5. **Error Handling** - Comprehensive exception hierarchy

## Project Structure

```
uas-api-client/
├── src/uas_api_client/
│   ├── __init__.py           # Public API exports
│   ├── client.py             # UnityClient - main API client
│   ├── auth.py               # Authentication providers
│   ├── exceptions.py         # Exception hierarchy
│   ├── models/
│   │   ├── api/              # API response types (from JSON)
│   │   │   └── product_response.py
│   │   └── domain/           # Domain models (business logic)
│   │       ├── asset.py      # UnityAsset
│   │       └── collection.py # UnityCollection
├── tests/                    # Unit and integration tests
├── examples/                 # Usage examples
├── docs/                     # Research documentation
└── pyproject.toml           # Package configuration
```

## Architecture Patterns

### Two-Layer Model System

Following the fab-api-client pattern:

1. **API Response Types** (`models/api/`)
   - Parse raw API responses
   - Convert from JSON dictionaries
   - Method: `from_dict()` to create from API response
   - Method: `to_asset()` to convert to domain model

2. **Domain Models** (`models/domain/`)
   - Business logic and utilities
   - No API knowledge
   - Methods for filtering, sorting, compatibility checks

**Example:**
```python
# API response (raw data from Unity API)
response = ProductResponse.from_dict(json_data)

# Convert to domain model
asset = response.to_asset()

# Use domain model for business logic
if asset.is_compatible_with("2021.3.0f1"):
    print(f"Compatible!")
```

### Authentication Abstraction

- `UnityAuthProvider` - Abstract base class
- `BearerTokenAuthProvider` - OAuth Bearer token implementation
- Auth providers create configured `requests.Session` objects
- Client doesn't know about token extraction (that's in uas-adapter)

### No Side Effects

**Never do this:**
```python
# BAD - Side effects
def get_asset(self, asset_id):
    print(f"Fetching {asset_id}...")
    asset = self._fetch(asset_id)
    print(f"Done!")
    return asset
```

**Instead do this:**
```python
# GOOD - Callback system
def get_asset(self, asset_id, on_progress=None):
    if on_progress:
        on_progress(f"Fetching {asset_id}...")
    asset = self._fetch(asset_id)
    if on_progress:
        on_progress("Done!")
    return asset
```

## Common Tasks

### Adding a New API Endpoint

1. Create API response type in `models/api/`
2. Add conversion to domain model
3. Add method to `UnityClient`
4. Follow error handling patterns
5. Add tests

### Adding New Domain Model Fields

1. Update the domain model dataclass
2. Update API response `to_asset()` conversion
3. Add any business logic methods
4. Update tests

### Error Handling Pattern

```python
try:
    response = self._session.get(url, timeout=self.timeout)
    
    # Check auth errors first
    if response.status_code in (401, 403):
        raise UnityAuthenticationError("Auth failed", status_code=...)
    
    # Check not found
    if response.status_code == 404:
        raise UnityNotFoundError("Not found", status_code=...)
    
    # Generic HTTP errors
    response.raise_for_status()
    
except requests.exceptions.Timeout:
    raise UnityNetworkError("Timeout")
except requests.exceptions.ConnectionError as e:
    raise UnityNetworkError(f"Connection error: {e}")
```

## Testing Strategy

### Unit Tests
- Mock auth providers
- Test API response parsing with fixtures
- Test domain model logic (compatibility, filtering)
- Test error handling

### Integration Tests
- Real API calls (opt-in, requires valid tokens)
- Test complete workflows
- Validate downloaded files

**Mock auth provider example:**
```python
class MockUnityAuthProvider(UnityAuthProvider):
    def get_session(self):
        return Mock()
    
    def get_endpoints(self):
        return ApiEndpoints()
    
    def is_token_expired(self):
        return False
```

## Unity-Specific Patterns

### Version Compatibility

Unity version strings: `"2021.3.30f1"` (major.minor.patch + release type)

```python
def is_compatible_with(self, unity_version: str) -> bool:
    # Extract major.minor for comparison
    # Asset compatible if target >= asset minimum
```

### Asset IDs

- `packageId` - String ID from API (e.g., "330726")
- Use as `uid` in domain models
- Never assume numeric

### Download URLs

- API returns `downloadS3key` (e.g., "download/uuid")
- Auth provider constructs full CDN URL from base + S3 key
- CDN downloads don't require authentication

### Package Encryption

- Downloaded files are AES encrypted
- This library saves as `.unitypackage.encrypted`
- Decryption is handled by uas-adapter (separate package)

## Related Projects

### uas-adapter (Tier 3)
- Authentication token management
- Package decryption
- Companion library for Unity Hub integration
- **Private repository** - not for distribution

### asset-marketplace-client-system
- Architecture documentation
- Three-tier pattern (Core, Clients, Adapters)
- Design decisions and patterns

## Common Pitfalls

1. **Don't print() for output** - Use callbacks
2. **Don't assume API field presence** - Always use `.get()` for dict access
3. **Don't expose reverse-engineering** - This is a clean library
4. **Don't skip rate limiting** - Respect Unity's API
5. **Don't catch all exceptions** - Be specific
6. **Don't use numeric types for IDs** - Always strings

## Code Style

- **Type hints everywhere** - Python 3.7+ compatible
- **Docstrings** - Google style
- **Line length** - 100 characters max
- **Formatting** - Black
- **Linting** - Ruff
- **Type checking** - mypy

## Future Work

### High Priority
- User library listing endpoint (when discovered)
- Token refresh logic
- Batch asset fetching

### Medium Priority
- Caching layer
- Async support
- Retry logic with exponential backoff

### Low Priority
- Search functionality (if API discovered)
- Asset categories enumeration
- Publisher information API

## Debugging Tips

1. **Token Issues** - Check expiration first
2. **API Errors** - Look at status codes
3. **Import Errors** - Check `__init__.py` exports
4. **Type Errors** - Run mypy
5. **Network Issues** - Check timeouts and rate limiting

## Contact & Support

For questions about the project:
1. Check existing documentation in `docs/`
2. Review the implementation plan
3. Look at fab-api-client for reference patterns
4. Check the architecture docs in asset-marketplace-client-system

## Development Workflow

```bash
# Install in editable mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy src/

# Format
black src/ tests/

# Lint
ruff check src/ tests/
```

---

**Remember:** This library is clean and publishable. All Unity Hub-specific implementation details belong in uas-adapter.
