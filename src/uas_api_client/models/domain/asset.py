"""Domain model for Unity Asset."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class UnityAsset:
    """Represents a Unity Asset Store asset.

    This is the domain model containing business logic for Unity assets.
    It's separate from the API response types to keep concerns separated.
    """

    uid: str
    title: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Unity-specific fields
    category: Optional[str] = None
    publisher: Optional[str] = None
    publisher_id: Optional[str] = None
    unity_version: Optional[str] = None
    package_size: Optional[int] = None
    rating: Optional[float] = None
    price: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)

    # Download information
    download_url: Optional[str] = None
    download_s3_key: Optional[str] = None
    asset_count: Optional[int] = None

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

    def get_download_size_mb(self) -> Optional[float]:
        """Get package size in megabytes.

        Returns:
            Size in MB, or None if size unknown
        """
        if self.package_size is None:
            return None
        return self.package_size / (1024 * 1024)
