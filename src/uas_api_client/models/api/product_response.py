"""API response models for Unity Asset Store product endpoint."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..domain.asset import UnityAsset


@dataclass
class ProductResponse:
    """Response from Unity Asset Store /api/product/{id} endpoint.

    This represents the raw API response structure. It can be converted
    to domain models for business logic usage.
    """

    id: str
    package_id: str
    name: str
    slug: str
    description: Optional[str] = None
    origin_price: Optional[str] = None
    uploads: Optional[Dict[str, Any]] = None
    category: Optional[Dict[str, Any]] = None
    product_publisher: Optional[Dict[str, Any]] = None
    main_image: Optional[Dict[str, Any]] = None
    images: Optional[List[Dict[str, Any]]] = None
    rating: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductResponse":
        """Create ProductResponse from API response dictionary.

        Args:
            data: Raw API response dictionary

        Returns:
            ProductResponse instance
        """
        return cls(
            id=data.get("id", ""),
            package_id=data.get("packageId", ""),
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            description=data.get("description"),
            origin_price=data.get("originPrice"),
            uploads=data.get("uploads"),
            category=data.get("category"),
            product_publisher=data.get("productPublisher"),
            main_image=data.get("mainImage"),
            images=data.get("images"),
            rating=data.get("rating"),
        )

    def to_asset(self) -> UnityAsset:
        """Convert API response to domain model.

        Returns:
            UnityAsset domain model
        """
        # Extract publisher info
        publisher_name = None
        publisher_id = None
        if self.product_publisher:
            publisher_name = self.product_publisher.get("name")
            publisher_id = self.product_publisher.get("id")

        # Extract category
        category_name = None
        if self.category:
            category_name = self.category.get("name")

        # Extract rating
        rating_value = None
        if self.rating:
            rating_value = self.rating.get("average")

        # Parse price
        price = None
        if self.origin_price:
            try:
                price = float(self.origin_price)
            except (ValueError, TypeError):
                pass

        # Extract download info from uploads
        # Get the first available Unity version
        download_s3_key = None
        package_size = None
        asset_count = None
        unity_version = None

        if self.uploads:
            # Get first version key
            version_keys = list(self.uploads.keys())
            if version_keys:
                unity_version = version_keys[0]
                upload_info = self.uploads[unity_version]

                download_s3_key = upload_info.get("downloadS3key")
                size_str = upload_info.get("downloadSize")
                count_str = upload_info.get("assetCount")

                if size_str:
                    try:
                        package_size = int(size_str)
                    except (ValueError, TypeError):
                        pass

                if count_str:
                    try:
                        asset_count = int(count_str)
                    except (ValueError, TypeError):
                        pass

        return UnityAsset(
            uid=self.package_id,
            title=self.name,
            description=self.description,
            category=category_name,
            publisher=publisher_name,
            publisher_id=publisher_id,
            unity_version=unity_version,
            package_size=package_size,
            rating=rating_value,
            price=price,
            download_s3_key=download_s3_key,
            asset_count=asset_count,
        )
