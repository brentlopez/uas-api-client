# Security Policy

## Supported Versions

We actively support and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in `uas-api-client`, please report it responsibly.

### How to Report

**Please DO NOT open a public GitHub issue for security vulnerabilities.**

Instead, please use one of these methods:

1. **GitHub Security Advisories** (Preferred)
   - Go to: https://github.com/brentlopez/uas-api-client/security/advisories
   - Click "Report a vulnerability"
   - Provide detailed information about the vulnerability

2. **Email** (Alternative)
   - Contact: brent@brentlopez.dev
   - Include "SECURITY: uas-api-client" in the subject line
   - Provide detailed information about the vulnerability

### What to Include

When reporting a vulnerability, please include:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Affected versions**
- **Potential impact** assessment
- **Suggested fix** (if you have one)
- **Your contact information** (for follow-up)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Assessment**: We will assess the vulnerability within 7 days
- **Updates**: We will keep you informed of progress
- **Resolution**: We aim to release a fix within 30 days for critical issues
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Features

This library is built with security in mind:

- ✅ **Core library inheritance**: Inherits security best practices from `asset-marketplace-client-core`
- ✅ **Path traversal prevention**: Built-in protection against directory traversal attacks
- ✅ **SSL verification**: SSL certificate verification enabled by default
- ✅ **Environment variable support**: Secure token loading from environment variables
- ✅ **No token logging**: Tokens are never logged or exposed in string representations
- ✅ **Type-safe**: Full mypy strict mode compliance
- ✅ **Input validation**: Uses core utilities for sanitizing filenames and validating URLs
- ✅ **Security tests**: Comprehensive test suite for security validation

## Security Best Practices for Users

### 1. Credential Management

**DO:**
- Load tokens from environment variables:
  ```python
  # Token loaded from UNITY_ACCESS_TOKEN env var
  auth = BearerTokenAuthProvider(endpoints=endpoints)
  ```
- Use secure credential stores
- Rotate tokens regularly

**DON'T:**
- Hardcode tokens in source code
- Commit tokens to version control
- Share tokens between environments

### 2. SSL/TLS Security

**DO:**
- Keep SSL verification enabled (default):
  ```python
  auth = BearerTokenAuthProvider(
      access_token=token,
      endpoints=endpoints,
      verify_ssl=True  # Default, never disable in production
  )
  ```

**DON'T:**
- Disable SSL verification in production
- Ignore SSL certificate warnings

### 3. File Downloads

**DO:**
- Use absolute paths for output directories
- Validate output directory exists and is writable
- Use the built-in path traversal prevention:
  ```python
  from uas_api_client.utils import safe_download_path
  
  base_dir = Path("/safe/downloads")
  safe_path = safe_download_path(base_dir, filename)
  ```

**DON'T:**
- Construct file paths manually without validation
- Allow user-controlled filenames without sanitization

### 4. Error Handling

**DO:**
- Handle exceptions appropriately
- Log errors without exposing sensitive data
- Use structured error handling:
  ```python
  try:
      result = client.download_asset(asset_uid, output_dir)
      if not result.success:
          logger.error(f"Download failed: {result.error}")
  except UnityError as e:
      logger.error(f"Unity API error: {e.message}")
  ```

**DON'T:**
- Log full exception details that might contain tokens
- Expose internal error details to end users

### 5. Dependencies

**DO:**
- Keep dependencies up to date:
  ```bash
  uv sync
  uv run pip-audit
  ```
- Monitor security advisories
- Use dependency scanning in CI/CD

**DON'T:**
- Ignore dependency updates
- Use packages with known vulnerabilities

## Unity-Specific Security Considerations

### Token Extraction

- Tokens are extracted from Unity Hub by the `uas-adapter` package
- Never extract tokens manually or use unofficial methods
- Tokens have expiration - check with `auth.is_token_expired()`

### Encrypted Packages

- Downloaded packages are AES encrypted
- Decryption is handled by `uas-adapter` (separate package)
- Never attempt to decrypt packages manually

### Rate Limiting

- Built-in rate limiting prevents API abuse
- Default: 1.5 seconds between requests
- Adjust if needed, but respect Unity's terms of service

## Additional Resources

For general security best practices, see:
- [asset-marketplace-client-core SECURITY.md](https://github.com/brentlopez/asset-marketplace-client-core/blob/main/SECURITY.md)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Questions?

If you have questions about the security of this library, please:
- Open a GitHub Discussion for general security questions
- Contact the maintainer at brent@brentlopez.dev for specific concerns

---

**Last Updated:** 2024-12-23
