from __future__ import annotations

import pytest

from foodmap.providers import MockRestaurantProvider
from foodmap.service import FoodMapService


def test_service_rejects_nonpositive_radius() -> None:
    svc = FoodMapService(MockRestaurantProvider())
    with pytest.raises(ValueError, match="radius_km"):
        svc.rank_nearby(center_lat=25.0, center_lon=121.0, radius_km=0.0)


def test_service_rejects_unknown_sort() -> None:
    svc = FoodMapService(MockRestaurantProvider())
    with pytest.raises(ValueError, match="unknown sort_by"):
        svc.rank_nearby(center_lat=25.033, center_lon=121.5654, radius_km=5.0, sort_by="not_a_mode")  # type: ignore[arg-type]
