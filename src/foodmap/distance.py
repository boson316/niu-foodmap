from __future__ import annotations

import math
from dataclasses import dataclass

_EARTH_RADIUS_KM = 6371.0
_KM_PER_DEG_LAT = 111.0


@dataclass(frozen=True, slots=True)
class HaversineCenter:
    """中心點弧度預計算，批次 haversine 時避免重複 radians/cos。"""

    lat_rad: float
    lon_rad: float
    cos_lat: float

    @classmethod
    def from_degrees(cls, lat: float, lon: float) -> HaversineCenter:
        lat_rad = math.radians(lat)
        return cls(lat_rad=lat_rad, lon_rad=math.radians(lon), cos_lat=math.cos(lat_rad))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """兩點球面距離（公里）。"""
    return haversine_km_from_center(HaversineCenter.from_degrees(lat1, lon1), lat2, lon2)


def haversine_km_from_center(center: HaversineCenter, lat2: float, lon2: float) -> float:
    lat2_rad = math.radians(lat2)
    dphi = lat2_rad - center.lat_rad
    dlmb = math.radians(lon2) - center.lon_rad
    a = math.sin(dphi / 2) ** 2 + center.cos_lat * math.cos(lat2_rad) * math.sin(dlmb / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return _EARTH_RADIUS_KM * c


def approx_in_radius_bbox(
    center_lat: float,
    center_lon: float,
    lat: float,
    lon: float,
    radius_km: float,
) -> bool:
    """粗篩：外接正方形（略大於圓），大量資料時先過濾再算 haversine。"""
    km_per_deg_lon = _KM_PER_DEG_LAT * max(math.cos(math.radians(center_lat)), 1e-6)
    dlat = radius_km / _KM_PER_DEG_LAT
    dlon = radius_km / km_per_deg_lon
    return (
        center_lat - dlat <= lat <= center_lat + dlat
        and center_lon - dlon <= lon <= center_lon + dlon
    )
