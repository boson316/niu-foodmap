from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

from foodmap.providers import MockRestaurantProvider
from foodmap.service import FoodMapService, build_maps_url, format_avg_spend, format_distance_m


def _write_min_json(path: Path) -> None:
    payload = [
        {
            "id": "n1",
            "name": "近",
            "lat": 25.0330,
            "lon": 121.5654,
            "rating": 4.0,
            "review_count": 50,
            "category": "測試",
            "price_level": 1,
        },
        {
            "id": "f1",
            "name": "遠",
            "lat": 25.0600,
            "lon": 121.5654,
            "rating": 5.0,
            "review_count": 500,
            "category": "測試",
        },
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_radius_filters_far(tmp_path: Path) -> None:
    p = tmp_path / "t.json"
    _write_min_json(p)
    svc = FoodMapService(MockRestaurantProvider(json_path=p))
    rows = svc.rank_nearby(center_lat=25.0330, center_lon=121.5654, radius_km=2.0, sort_by="distance")
    names = {r.restaurant.name for r in rows}
    assert "近" in names
    assert "遠" not in names


def test_min_reviews_filters(tmp_path: Path) -> None:
    p = tmp_path / "t.json"
    _write_min_json(p)
    svc = FoodMapService(MockRestaurantProvider(json_path=p))
    rows = svc.rank_nearby(
        center_lat=25.0330,
        center_lon=121.5654,
        radius_km=50.0,
        min_reviews=100,
        sort_by="distance",
    )
    assert len(rows) == 1
    assert rows[0].restaurant.name == "遠"


def test_limit_uses_top_k_not_full_sort(tmp_path: Path) -> None:
    p = tmp_path / "many.json"
    base_lat, base_lon = 25.0330, 121.5654
    payload = [
        {
            "id": f"x{i}",
            "name": f"店{i}",
            "lat": base_lat + i * 0.0001,
            "lon": base_lon,
            "rating": 3.0 + i * 0.1,
            "review_count": 100 + i,
            "category": "測試",
        }
        for i in range(8)
    ]
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    svc = FoodMapService(MockRestaurantProvider(json_path=p))
    rows = svc.rank_nearby(
        center_lat=base_lat,
        center_lon=base_lon,
        radius_km=5.0,
        sort_by="composite",
        limit=2,
    )
    assert len(rows) == 2
    scores = [r.composite for r in rows]
    assert scores == sorted(scores, reverse=True)


def test_sort_huang_orders_by_huang_rating(tmp_path: Path) -> None:
    p = tmp_path / "huang.json"
    payload = [
        {
            "id": "a",
            "name": "A",
            "lat": 25.0330,
            "lon": 121.5654,
            "rating": 4.5,
            "review_count": 10,
            "category": "測試",
        },
        {
            "id": "b",
            "name": "B",
            "lat": 25.0331,
            "lon": 121.5654,
            "rating": 3.0,
            "review_count": 200,
            "category": "測試",
        },
    ]
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    svc = FoodMapService(MockRestaurantProvider(json_path=p))
    rows = svc.rank_nearby(
        center_lat=25.0330,
        center_lon=121.5654,
        radius_km=5.0,
        sort_by="huang",
        limit=10,
    )
    huang_scores = [r.huang_rating for r in rows]
    assert huang_scores == sorted(huang_scores, reverse=True)


def test_format_distance_m() -> None:
    assert format_distance_m(361) == "361 公尺"
    assert format_distance_m(1050) == "1.1 km"
    assert format_distance_m(1000) == "1.0 km"


def test_build_maps_url_uses_name_and_place_id() -> None:
    url = build_maps_url("測試店", 24.75, 121.75, place_id="places/ChIJabc123")
    assert "query=" in url
    assert "query_place_id=" in url
    assert "ChIJabc123" in url


def test_build_maps_url_falls_back_to_name_at_coords() -> None:
    url = build_maps_url("測試店", 24.75, 121.75)
    assert "%40" in url or "@" in url
    assert "24.75" in url


def test_format_avg_spend_maps_price_level() -> None:
    assert format_avg_spend(1) == "$100–300"
    assert format_avg_spend(4) == "$1,200+"
    assert format_avg_spend(None) == "未提供"


def test_to_public_dict_has_avg_spend_display(tmp_path: Path) -> None:
    p = tmp_path / "t.json"
    _write_min_json(p)
    svc = FoodMapService(MockRestaurantProvider(json_path=p))
    rows = svc.rank_nearby(center_lat=25.0330, center_lon=121.5654, radius_km=50.0, sort_by="distance", limit=2)
    out = FoodMapService.to_public_dict(rows)
    near = next(item for item in out if item["name"] == "近")
    assert near["avg_spend_display"] == "$100–300"
    assert "google.com/maps" in near["maps_url"]
