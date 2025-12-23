"""API response model for Unity Asset Store purchases/library endpoint."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CategoryCount:
    """Category count information from purchases response."""

    name: str
    count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CategoryCount":
        """Create CategoryCount from API response dict.

        Args:
            data: Raw API response data

        Returns:
            CategoryCount instance
        """
        return cls(name=data["name"], count=data["count"])


@dataclass
class PurchaseItem:
    """Represents a single purchased/granted asset from Unity Asset Store.

    This contains minimal information about an asset in the user's library.
    Use get_asset() with the package_id to fetch full asset details.
    """

    id: str  # Purchase/grant ID
    package_id: int  # Asset package ID (use this with get_asset())
    display_name: str
    grant_time: datetime
    is_hidden: bool
    is_publisher_asset: bool
    order_id: Optional[str] = None
    tagging: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PurchaseItem":
        """Create PurchaseItem from API response dict.

        Args:
            data: Raw API response data

        Returns:
            PurchaseItem instance
        """
        return cls(
            id=data["id"],
            package_id=data["packageId"],
            display_name=data["displayName"],
            grant_time=datetime.fromisoformat(data["grantTime"].replace("Z", "+00:00")),
            is_hidden=data["isHidden"],
            is_publisher_asset=data["isPublisherAsset"],
            order_id=data.get("orderId"),
            tagging=data.get("tagging", []),
        )


@dataclass
class PurchasesResponse:
    """Response from /purchases endpoint containing user's Asset Store library."""

    results: List[PurchaseItem]
    total: int
    categories: List[CategoryCount] = field(default_factory=list)
    publisher_suggest: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PurchasesResponse":
        """Create PurchasesResponse from API response dict.

        Args:
            data: Raw API response data

        Returns:
            PurchasesResponse instance
        """
        return cls(
            results=[PurchaseItem.from_dict(item) for item in data.get("results", [])],
            total=data.get("total", 0),
            categories=[CategoryCount.from_dict(cat) for cat in data.get("category", [])],
            publisher_suggest=data.get("publisherSuggest", []),
        )

    def get_package_ids(self, include_hidden: bool = False) -> List[int]:
        """Get list of package IDs from purchases.

        Args:
            include_hidden: Include hidden assets if True

        Returns:
            List of package IDs
        """
        if include_hidden:
            return [item.package_id for item in self.results]
        return [item.package_id for item in self.results if not item.is_hidden]

    def filter_by_category(self, category_name: str) -> List[PurchaseItem]:
        """Filter purchases by category name.

        Note: This requires fetching full asset details to get accurate categories.
        The category counts in the response are aggregate data.

        Args:
            category_name: Category to filter by (e.g., "3d/environments/fantasy")

        Returns:
            Filtered list of PurchaseItems
        """
        # Note: Individual items don't have category info, need to fetch full details
        # This is a placeholder - proper filtering requires get_asset() calls
        return self.results
