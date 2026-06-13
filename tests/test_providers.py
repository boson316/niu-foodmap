from __future__ import annotations

import json
from pathlib import Path

import pytest

from foodmap.models import Restaurant
from foodmap.providers import (
    GooglePlacesProvider,
    MockRestaurantProvider,
    grid_offsets_meters,
    merge_restaurants_unique,
    offset_center_meters,
)


def test_mock_provider_loads_bundled_sample() -> None:
    p = MockRestaurantProvider()
    rows = p.list_restaurants()
    assert len(rows) >= 10
    assert rows[0].name


def test_google_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_MAPS_API_KEY"):
        GooglePlacesProvider(center_lat=24.7464, center_lon=121.7457, api_key="").list_restaurants()


def test_google_parse_price_level_enum_and_int() -> None:
    assert GooglePlacesProvider._parse_price_level("PRICE_LEVEL_MODERATE") == 2
    assert GooglePlacesProvider._parse_price_level("PRICE_LEVEL_INEXPENSIVE") == 1
    assert GooglePlacesProvider._parse_price_level("PRICE_LEVEL_VERY_EXPENSIVE") == 4
    assert GooglePlacesProvider._parse_price_level(3) == 3
    assert GooglePlacesProvider._parse_price_level(None) is None
    assert GooglePlacesProvider._parse_price_level("PRICE_LEVEL_FREE") is None


def test_google_parse_places_handles_enum_price_level() -> None:
    rows = GooglePlacesProvider._parse_places(
        [
            {
                "id": "abc",
                "displayName": {"text": "測試店"},
                "location": {"latitude": 24.7464, "longitude": 121.7457},
                "rating": 4.2,
                "userRatingCount": 100,
                "primaryType": "restaurant",
                "priceLevel": "PRICE_LEVEL_MODERATE",
            }
        ]
    )
    assert len(rows) == 1
    assert rows[0].name == "測試店"
    assert rows[0].price_level == 2


def test_grid_offsets_3x3_has_nine_points() -> None:
    assert len(grid_offsets_meters(3, 1000.0)) == 9


def test_merge_restaurants_dedupes_by_id() -> None:
    seen: dict[str, Restaurant] = {}
    a = Restaurant("x1", "A", 24.0, 121.0, 4.0, 10, "")
    b = Restaurant("x1", "A dup", 24.1, 121.1, 3.0, 5, "")
    c = Restaurant("x2", "B", 24.2, 121.2, 4.5, 20, "")
    merge_restaurants_unique(seen, [a, b, c])
    assert len(seen) == 2
    assert seen["x1"].name == "A dup"


def test_offset_center_moves_north() -> None:
    lat, lon = offset_center_meters(24.0, 121.0, north_m=1000.0, east_m=0.0)
    assert lat > 24.0
    assert lon == pytest.approx(121.0, abs=1e-6)


def test_mock_provider_rejects_non_array(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"x": 1}), encoding="utf-8")
    with pytest.raises(ValueError, match="array"):
        MockRestaurantProvider(json_path=path).list_restaurants()
