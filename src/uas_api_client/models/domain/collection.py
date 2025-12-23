"""Domain model for Unity Asset Collection."""

from dataclasses import dataclass, field

from asset_marketplace_core import BaseCollection

from .asset import UnityAsset


@dataclass
class UnityCollection(BaseCollection):
    """Represents a collection of Unity Asset Store assets.

    Provides filtering and search capabilities over a collection of assets.

    Extends BaseCollection from asset-marketplace-client-core and adds Unity-specific
    filtering and sorting methods.

    Inherited from BaseCollection:
        assets: List of assets (typed as List[UnityAsset] here)
        total_count: Total number of assets
        __len__(): Get number of assets
        filter(): Generic filter by predicate
        find_by_uid(): Find asset by unique identifier
    """

    assets: list[UnityAsset] = field(default_factory=list)  # type: ignore[assignment]

    def filter_by_category(self, category: str) -> "UnityCollection":
        """Filter assets by category.

        Args:
            category: Category name to filter by

        Returns:
            New collection with filtered assets
        """
        filtered = [a for a in self.assets if a.category == category]
        return UnityCollection(assets=filtered, total_count=len(filtered))

    def filter_by_publisher(self, publisher: str) -> "UnityCollection":
        """Filter assets by publisher.

        Args:
            publisher: Publisher name to filter by

        Returns:
            New collection with filtered assets
        """
        filtered = [a for a in self.assets if a.publisher == publisher]
        return UnityCollection(assets=filtered, total_count=len(filtered))

    def filter_by_unity_version(self, unity_version: str) -> "UnityCollection":
        """Filter assets compatible with given Unity version.

        Args:
            unity_version: Unity version string (e.g., "2021.3.30f1")

        Returns:
            New collection with compatible assets
        """
        filtered = [a for a in self.assets if a.is_compatible_with(unity_version)]
        return UnityCollection(assets=filtered, total_count=len(filtered))

    def sort_by_title(self, reverse: bool = False) -> "UnityCollection":
        """Sort assets by title.

        Args:
            reverse: Sort in descending order if True

        Returns:
            New collection with sorted assets
        """
        sorted_assets = sorted(self.assets, key=lambda a: a.title, reverse=reverse)
        return UnityCollection(assets=sorted_assets, total_count=self.total_count)

    def sort_by_price(self, reverse: bool = False) -> "UnityCollection":
        """Sort assets by price.

        Args:
            reverse: Sort in descending order if True (highest price first)

        Returns:
            New collection with sorted assets
        """
        # Put assets with no price at the end
        sorted_assets = sorted(
            self.assets,
            key=lambda a: (a.price is None, a.price if a.price is not None else 0),
            reverse=reverse,
        )
        return UnityCollection(assets=sorted_assets, total_count=self.total_count)

    def get_asset_by_id(self, asset_id: str) -> UnityAsset | None:
        """Get asset by ID from collection.

        Args:
            asset_id: Asset UID to find

        Returns:
            UnityAsset if found, None otherwise
        """
        for asset in self.assets:
            if asset.uid == asset_id:
                return asset
        return None
