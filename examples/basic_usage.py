"""Basic usage example for uas-api-client.

This example demonstrates how to use uas-api-client with tokens
extracted from Unity Hub using the uas-adapter package.
"""

import sys
from pathlib import Path

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uas_api_client import (
    UnityClient,
    UnityAuthenticationError,
    UnityNotFoundError,
    UnityTokenExpiredError,
)


def progress_callback(message: str) -> None:
    """Simple progress callback that prints messages."""
    print(f"[Progress] {message}")


def main() -> None:
    """Main example function."""
    # Example: Obtain tokens using uas-adapter
    # from uas_adapter import UnityHubAuth
    # from uas_adapter.extractors import ElectronExtractor
    # 
    # extractor = ElectronExtractor()
    # tokens = extractor.extract_tokens()
    # 
    # auth = UnityHubAuth(
    #     access_token=tokens['accessToken'],
    #     access_token_expiration=tokens['accessTokenExpiration'],
    #     refresh_token=tokens['refreshToken']
    # )

    # For this example, we'll use placeholder values
    print("uas-api-client Basic Usage Example")
    print("=" * 50)
    print()
    print("⚠️  This example requires valid Unity Hub tokens.")
    print("    Use uas-adapter to obtain tokens.")
    print()

    # NOTE: In real usage, use uas-adapter to get auth provider:
    # auth = UnityHubAuth(...)
    # 
    # For this example, we'll show that you need uas-adapter:
    print("To use this example, you need uas-adapter installed.")
    print("")
    print("Install and use it like this:")
    print("  from uas_adapter import UnityHubAuth")
    print("  from uas_adapter.extractors import ElectronExtractor")
    print("  ")
    print("  extractor = ElectronExtractor()")
    print("  tokens = extractor.extract_tokens()")
    print("  ")
    print("  auth = UnityHubAuth(")
    print("      access_token=tokens['accessToken'],")
    print("      access_token_expiration=tokens['accessTokenExpiration'],")
    print("      refresh_token=tokens['refreshToken']")
    print("  )")
    print("")
    return

    # Check if token is expired (if expiration is known)
    if auth.is_token_expired():
        print("❌ Token is expired. Please obtain fresh tokens.")
        return

    # Create client
    client = UnityClient(auth, rate_limit_delay=1.5)

    # Example asset ID (Unity Asset Store test asset)
    asset_id = "330726"

    try:
        print(f"Fetching asset {asset_id}...")
        print()

        # Fetch asset information
        asset = client.get_asset(asset_id, on_progress=progress_callback)

        print()
        print("Asset Information:")
        print("-" * 50)
        print(f"Title: {asset.title}")
        print(f"UID: {asset.uid}")
        print(f"Publisher: {asset.publisher}")
        print(f"Category: {asset.category}")
        print(f"Price: ${asset.price}")
        print(f"Unity Version: {asset.unity_version}")

        if asset.package_size:
            print(f"Size: {asset.get_download_size_mb():.2f} MB")

        if asset.rating:
            print(f"Rating: {asset.rating:.1f}")

        if asset.asset_count:
            print(f"Asset Count: {asset.asset_count}")

        print()

        # Check version compatibility
        test_version = "2021.3.0f1"
        if asset.is_compatible_with(test_version):
            print(f"✅ Compatible with Unity {test_version}")
        else:
            print(f"❌ Not compatible with Unity {test_version}")

        print()

        # Download asset (optional - commented out by default)
        # print("Downloading asset...")
        # downloaded_path = client.download_asset(
        #     asset,
        #     output_dir="./downloads",
        #     on_progress=progress_callback
        # )
        # print(f"✅ Downloaded to: {downloaded_path}")
        # print()
        # print("NOTE: Downloaded file is AES encrypted.")
        # print("      Use uas-adapter for decryption.")

    except UnityTokenExpiredError:
        print("❌ Token expired. Please refresh tokens.")
    except UnityAuthenticationError as e:
        print(f"❌ Authentication failed: {e.message}")
        print("   Check your access token.")
    except UnityNotFoundError:
        print(f"❌ Asset {asset_id} not found.")
        print("   Check the asset ID.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
