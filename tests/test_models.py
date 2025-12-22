"""Tests for domain models."""

import pytest
from datetime import datetime

from uas_api_client.models.domain.asset import UnityAsset
from uas_api_client.models.domain.collection import UnityCollection
from uas_api_client.models.api.product_response import ProductResponse


class TestUnityAsset:
    """Tests for UnityAsset domain model."""

    def test_asset_creation(self):
        """Test basic asset creation."""
        asset = UnityAsset(
            uid="123456",
            title="Test Asset",
            description="A test asset",
            category="Tools",
            publisher="Test Publisher",
            unity_version="2021.3.0f1",
            price=19.99
        )

        assert asset.uid == "123456"
        assert asset.title == "Test Asset"
        assert asset.category == "Tools"
        assert asset.price == 19.99

    def test_version_compatibility_compatible(self):
        """Test version compatibility check for compatible versions."""
        asset = UnityAsset(
            uid="123",
            title="Test",
            unity_version="2020.3.0f1"
        )

        # Same version
        assert asset.is_compatible_with("2020.3.0f1") is True
        
        # Newer version
        assert asset.is_compatible_with("2021.3.0f1") is True
        assert asset.is_compatible_with("2022.1.0f1") is True

    def test_version_compatibility_incompatible(self):
        """Test version compatibility check for incompatible versions."""
        asset = UnityAsset(
            uid="123",
            title="Test",
            unity_version="2021.3.0f1"
        )

        # Older version
        assert asset.is_compatible_with("2020.1.0f1") is False
        assert asset.is_compatible_with("2021.2.0f1") is False

    def test_version_compatibility_no_requirement(self):
        """Test version compatibility when no version specified."""
        asset = UnityAsset(
            uid="123",
            title="Test",
            unity_version=None
        )

        # Should be compatible with any version
        assert asset.is_compatible_with("2020.1.0f1") is True
        assert asset.is_compatible_with("2022.1.0f1") is True

    def test_has_dependencies(self):
        """Test dependency checking."""
        asset_with_deps = UnityAsset(
            uid="123",
            title="Test",
            dependencies=["dep1", "dep2"]
        )
        
        asset_without_deps = UnityAsset(
            uid="456",
            title="Test2"
        )

        assert asset_with_deps.has_dependencies() is True
        assert asset_without_deps.has_dependencies() is False

    def test_get_download_size_mb(self):
        """Test download size conversion to MB."""
        asset = UnityAsset(
            uid="123",
            title="Test",
            package_size=1048576  # 1 MB in bytes
        )

        assert asset.get_download_size_mb() == 1.0

        asset_no_size = UnityAsset(uid="456", title="Test2")
        assert asset_no_size.get_download_size_mb() is None


class TestUnityCollection:
    """Tests for UnityCollection domain model."""

    @pytest.fixture
    def sample_assets(self):
        """Create sample assets for testing."""
        return [
            UnityAsset(
                uid="1",
                title="Asset Alpha",
                category="Tools",
                publisher="Publisher A",
                unity_version="2020.3.0f1",
                price=10.0
            ),
            UnityAsset(
                uid="2",
                title="Asset Beta",
                category="Models",
                publisher="Publisher B",
                unity_version="2021.3.0f1",
                price=20.0
            ),
            UnityAsset(
                uid="3",
                title="Asset Gamma",
                category="Tools",
                publisher="Publisher A",
                unity_version="2022.1.0f1",
                price=None
            ),
        ]

    def test_collection_creation(self, sample_assets):
        """Test collection creation."""
        collection = UnityCollection(assets=sample_assets, total_count=3)

        assert len(collection) == 3
        assert collection.total_count == 3

    def test_filter_by_category(self, sample_assets):
        """Test filtering by category."""
        collection = UnityCollection(assets=sample_assets)
        
        tools = collection.filter_by_category("Tools")
        
        assert len(tools) == 2
        assert all(a.category == "Tools" for a in tools.assets)

    def test_filter_by_publisher(self, sample_assets):
        """Test filtering by publisher."""
        collection = UnityCollection(assets=sample_assets)
        
        publisher_a = collection.filter_by_publisher("Publisher A")
        
        assert len(publisher_a) == 2
        assert all(a.publisher == "Publisher A" for a in publisher_a.assets)

    def test_filter_by_unity_version(self, sample_assets):
        """Test filtering by Unity version compatibility."""
        collection = UnityCollection(assets=sample_assets)
        
        compatible = collection.filter_by_unity_version("2021.3.0f1")
        
        # Should include assets compatible with 2021.3.0f1
        assert len(compatible) == 2
        # Asset with 2022.1.0f1 requirement should not be included
        assert not any(a.uid == "3" for a in compatible.assets)

    def test_sort_by_title(self, sample_assets):
        """Test sorting by title."""
        collection = UnityCollection(assets=sample_assets)
        
        sorted_asc = collection.sort_by_title()
        assert sorted_asc.assets[0].title == "Asset Alpha"
        assert sorted_asc.assets[2].title == "Asset Gamma"
        
        sorted_desc = collection.sort_by_title(reverse=True)
        assert sorted_desc.assets[0].title == "Asset Gamma"
        assert sorted_desc.assets[2].title == "Asset Alpha"

    def test_sort_by_price(self, sample_assets):
        """Test sorting by price."""
        collection = UnityCollection(assets=sample_assets)
        
        sorted_asc = collection.sort_by_price()
        # Assets with price should come first (sorted)
        assert sorted_asc.assets[0].price == 10.0
        assert sorted_asc.assets[1].price == 20.0
        # Asset without price should be last
        assert sorted_asc.assets[2].price is None
        
        sorted_desc = collection.sort_by_price(reverse=True)
        # When reverse, highest price first, then None values
        assert sorted_desc.assets[0].price == 20.0 or sorted_desc.assets[0].price is None

    def test_get_asset_by_id(self, sample_assets):
        """Test getting asset by ID."""
        collection = UnityCollection(assets=sample_assets)
        
        asset = collection.get_asset_by_id("2")
        assert asset is not None
        assert asset.title == "Asset Beta"
        
        not_found = collection.get_asset_by_id("999")
        assert not_found is None


class TestProductResponse:
    """Tests for ProductResponse API model."""

    def test_from_dict(self):
        """Test parsing from API response dictionary."""
        api_data = {
            "id": "999",
            "packageId": "123456",
            "name": "Test Asset",
            "slug": "test-asset",
            "originPrice": "29.99",
            "uploads": {
                "2021.3.0f1": {
                    "downloadS3key": "download/abc-123",
                    "downloadSize": "5000000",
                    "assetCount": "50"
                }
            },
            "category": {"name": "Scripts"},
            "productPublisher": {"name": "Test Dev", "id": "pub123"}
        }

        response = ProductResponse.from_dict(api_data)

        assert response.package_id == "123456"
        assert response.name == "Test Asset"
        assert response.origin_price == "29.99"

    def test_to_asset(self):
        """Test conversion to domain asset."""
        api_data = {
            "id": "999",
            "packageId": "123456",
            "name": "Test Asset",
            "slug": "test-asset",
            "description": "A test description",
            "originPrice": "29.99",
            "uploads": {
                "2021.3.0f1": {
                    "downloadS3key": "download/abc-123",
                    "downloadSize": "5000000",
                    "assetCount": "50"
                }
            },
            "category": {"name": "Scripts"},
            "productPublisher": {"name": "Test Dev", "id": "pub123"},
            "rating": {"average": 4.5}
        }

        response = ProductResponse.from_dict(api_data)
        asset = response.to_asset()

        assert isinstance(asset, UnityAsset)
        assert asset.uid == "123456"
        assert asset.title == "Test Asset"
        assert asset.description == "A test description"
        assert asset.price == 29.99
        assert asset.category == "Scripts"
        assert asset.publisher == "Test Dev"
        assert asset.publisher_id == "pub123"
        assert asset.rating == 4.5
        assert asset.unity_version == "2021.3.0f1"
        assert asset.package_size == 5000000
        assert asset.asset_count == 50
        assert asset.download_s3_key == "download/abc-123"

    def test_to_asset_minimal_data(self):
        """Test conversion with minimal API data."""
        api_data = {
            "id": "999",
            "packageId": "123",
            "name": "Minimal Asset",
            "slug": "minimal"
        }

        response = ProductResponse.from_dict(api_data)
        asset = response.to_asset()

        assert asset.uid == "123"
        assert asset.title == "Minimal Asset"
        assert asset.price is None
        assert asset.category is None
        assert asset.publisher is None
