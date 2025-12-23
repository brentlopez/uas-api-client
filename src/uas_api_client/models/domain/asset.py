"""Domain model for Unity Asset."""

from dataclasses import dataclass, field

from asset_marketplace_core import BaseAsset


@dataclass
class UnityAsset(BaseAsset):
    """Represents a Unity Asset Store asset.

    This is the domain model containing business logic for Unity assets.
    It's separate from the API response types to keep concerns separated.

    Extends BaseAsset from asset-marketplace-client-core and adds Unity-specific
    fields and methods.

    Inherited from BaseAsset:
        uid: Unique identifier
        title: Asset title
        description: Asset description
        created_at: Creation timestamp
        updated_at: Last update timestamp
        raw_data: Complete raw API response data
    """

    # Unity-specific fields
    category: str | None = None
    publisher: str | None = None
    publisher_id: str | None = None
    unity_version: str | None = None
    package_size: int | None = None
    rating: float | None = None
    price: float | None = None
    dependencies: list[str] = field(default_factory=list)

    # Download information
    download_url: str | None = None
    download_s3_key: str | None = None
    asset_count: int | None = None

    def is_compatible_with(self, unity_version: str) -> bool:
        """Check if asset is compatible with given Unity version.

        Args:
            unity_version: Unity version string (e.g., "2021.3.30f1")

        Returns:
            True if compatible, False otherwise
        """
        if not self.unity_version:
            # If no minimum version specified, assume compatible
            return True

        # Simple version comparison - extract major.minor
        try:
            asset_major, asset_minor = self._parse_version(self.unity_version)
            target_major, target_minor = self._parse_version(unity_version)

            # Asset is compatible if target version >= asset minimum version
            if target_major > asset_major:
                return True
            if target_major == asset_major and target_minor >= asset_minor:
                return True
            return False
        except (ValueError, IndexError):
            # If we can't parse versions, assume compatible
            return True

    @staticmethod
    def _parse_version(version_str: str) -> tuple:
        """Parse Unity version string into (major, minor) tuple.

        Args:
            version_str: Version string like "2021.3.30f1"

        Returns:
            Tuple of (major, minor) as integers
        """
        # Extract major.minor from version like "2021.3.30f1"
        parts = version_str.split(".")
        major = int(parts[0])
        minor = int(parts[1])
        return (major, minor)

    def has_dependencies(self) -> bool:
        """Check if asset has any dependencies.

        Returns:
            True if asset has dependencies, False otherwise
        """
        return len(self.dependencies) > 0

    def get_download_size_mb(self) -> float | None:
        """Get package size in megabytes.

        Returns:
            Size in MB, or None if size unknown
        """
        if self.package_size is None:
            return None
        return self.package_size / (1024 * 1024)
