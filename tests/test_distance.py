from __future__ import annotations

import math

from foodmap.distance import HaversineCenter, approx_in_radius_bbox, haversine_km, haversine_km_from_center


def test_same_point_zero() -> None:
    assert haversine_km(25.033, 121.5654, 25.033, 121.5654) == 0.0


def test_short_distance_reasonable() -> None:
    # 約 1 km：緯度差 ~0.009 度（中緯度近似）
    d = haversine_km(25.0330, 121.5654, 25.0420, 121.5654)
    assert 0.9 <= d <= 1.1


def test_precomputed_center_matches_haversine_km() -> None:
    center = HaversineCenter.from_degrees(25.0330, 121.5654)
    lat2, lon2 = 25.0420, 121.5700
    assert math.isclose(
        haversine_km_from_center(center, lat2, lon2),
        haversine_km(25.0330, 121.5654, lat2, lon2),
        rel_tol=1e-9,
    )


def test_bbox_superset_of_circle() -> None:
    c_lat, c_lon, r_km = 25.0330, 121.5654, 2.0
    assert approx_in_radius_bbox(c_lat, c_lon, c_lat, c_lon, r_km)
    d = haversine_km(c_lat, c_lon, 25.0420, 121.5654)
    if d <= r_km:
        assert approx_in_radius_bbox(c_lat, c_lon, 25.0420, 121.5654, r_km)
