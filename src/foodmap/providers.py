from __future__ import annotations

import json
import math
import os
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Sequence

from foodmap.models import Restaurant
from foodmap.validation import load_restaurant_array

_NEARBY_TYPES = (
    "restaurant",
    "cafe",
    "fast_food_restaurant",
    "meal_takeaway",
    "chinese_restaurant",
    "japanese_restaurant",
    "korean_restaurant",
    "breakfast_restaurant",
)


def offset_center_meters(lat: float, lon: float, north_m: float, east_m: float) -> tuple[float, float]:
    dlat = north_m / 111_320.0
    dlon = east_m / (111_320.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def grid_offsets_meters(grid: int, spacing_m: float) -> list[tuple[float, float]]:
    if grid <= 1:
        return [(0.0, 0.0)]
    half = (grid - 1) / 2.0
    return [
        ((half - row) * spacing_m, (col - half) * spacing_m)
        for row in range(grid)
        for col in range(grid)
    ]


def merge_restaurants_unique(existing: dict[str, Restaurant], rows: Sequence[Restaurant]) -> None:
    for row in rows:
        if row.id:
            existing[row.id] = row


class RestaurantProvider(ABC):
    @abstractmethod
    def list_restaurants(self) -> Sequence[Restaurant]:
        raise NotImplementedError


class MockRestaurantProvider(RestaurantProvider):
    """從套件內建 JSON 載入餐廳（離線 demo／期末報告用）。"""

    def __init__(self, json_path: Path | None = None) -> None:
        if json_path is None:
            json_path = Path(__file__).resolve().parent / "data" / "sample_restaurants.json"
        self._path = json_path
        self._cache: list[Restaurant] | None = None

    def list_restaurants(self) -> Sequence[Restaurant]:
        if self._cache is not None:
            return self._cache
        raw = load_restaurant_array(self._path)
        self._cache = [Restaurant.from_dict(item) for item in raw]
        return self._cache


class GooglePlacesProvider(RestaurantProvider):
    """Google Places API (New) — 建議先抓成 JSON 快取，查詢時用 MockRestaurantProvider。

    環境變數：GOOGLE_MAPS_API_KEY（必填）
    一次性匯出：python scripts/fetch_places_to_json.py --out data/places_cache.json
    """

    _SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"
    _FIELD_MASK = (
        "places.id,places.displayName,places.location,places.rating,places.userRatingCount,"
        "places.primaryType,places.priceLevel"
    )

    def __init__(
        self,
        *,
        center_lat: float,
        center_lon: float,
        radius_m: float = 2000.0,
        api_key: str | None = None,
        max_pages: int = 3,
    ) -> None:
        self._center_lat = center_lat
        self._center_lon = center_lon
        self._radius_m = radius_m
        self._api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY", "")
        self._max_pages = max_pages
        self._cache: list[Restaurant] | None = None

    def list_restaurants(self) -> Sequence[Restaurant]:
        if self._cache is not None:
            return self._cache
        if not self._api_key:
            raise ValueError(
                "GOOGLE_MAPS_API_KEY is required for GooglePlacesProvider; "
                "or fetch once via scripts/fetch_places_to_json.py and use --data"
            )
        self._cache = self._fetch_all_pages()
        return self._cache

    def list_restaurants_dense(
        self,
        *,
        target: int = 100,
        grid: int = 3,
        page_delay_s: float = 2.0,
    ) -> list[Restaurant]:
        """多中心格網搜尋 + 去重，突破單次 Nearby 約 20 筆上限。"""
        if target <= 0:
            raise ValueError("target must be positive")
        if grid <= 0:
            raise ValueError("grid must be positive")

        spacing_m = self._radius_m / grid
        sub_radius_m = max(self._radius_m / max(grid - 1, 1), 800.0)
        seen: dict[str, Restaurant] = {}

        for north_m, east_m in grid_offsets_meters(grid, spacing_m):
            center_lat, center_lon = offset_center_meters(
                self._center_lat,
                self._center_lon,
                north_m,
                east_m,
            )
            sub = GooglePlacesProvider(
                center_lat=center_lat,
                center_lon=center_lon,
                radius_m=sub_radius_m,
                api_key=self._api_key,
                max_pages=self._max_pages,
            )
            merge_restaurants_unique(seen, sub.list_restaurants())
            if len(seen) >= target:
                break
            if page_delay_s > 0:
                time.sleep(page_delay_s)

        return list(seen.values())[:target]

    def _fetch_all_pages(self) -> list[Restaurant]:
        body: dict[str, Any] = {
            "includedTypes": list(_NEARBY_TYPES),
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": self._center_lat, "longitude": self._center_lon},
                    "radius": min(self._radius_m, 50_000.0),
                }
            },
        }
        rows: list[Restaurant] = []
        page_token: str | None = None
        for page_idx in range(self._max_pages):
            request_body = dict(body)
            if page_token:
                if page_idx > 0:
                    time.sleep(2.0)
                request_body["pageToken"] = page_token
            payload = self._post_json(request_body)
            rows.extend(self._parse_places(payload.get("places", [])))
            page_token = payload.get("nextPageToken")
            if not page_token:
                break
        return rows

    def _post_json(self, body: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self._SEARCH_URL,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self._api_key,
                "X-Goog-FieldMask": self._FIELD_MASK,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Google Places API HTTP {exc.code}: {detail}") from exc
        if not isinstance(raw, dict):
            raise ValueError("Google Places API returned non-object JSON")
        return raw

    @staticmethod
    def _parse_price_level(raw: Any) -> int | None:
        if raw is None:
            return None
        if isinstance(raw, int):
            return raw if 1 <= raw <= 4 else None
        if isinstance(raw, str):
            mapping = {
                "PRICE_LEVEL_INEXPENSIVE": 1,
                "PRICE_LEVEL_MODERATE": 2,
                "PRICE_LEVEL_EXPENSIVE": 3,
                "PRICE_LEVEL_VERY_EXPENSIVE": 4,
            }
            if raw in mapping:
                return mapping[raw]
            if raw.isdigit():
                level = int(raw)
                return level if 1 <= level <= 4 else None
        return None

    @staticmethod
    def _parse_places(places: list[dict[str, Any]]) -> list[Restaurant]:
        out: list[Restaurant] = []
        for p in places:
            loc = p.get("location") or {}
            name = p.get("displayName") or {}
            out.append(
                Restaurant(
                    id=str(p.get("id", "")),
                    name=str(name.get("text", "unknown")),
                    lat=float(loc.get("latitude", 0.0)),
                    lon=float(loc.get("longitude", 0.0)),
                    rating=float(p.get("rating", 0.0)),
                    review_count=int(p.get("userRatingCount", 0)),
                    category=str(p.get("primaryType", "")),
                    price_level=GooglePlacesProvider._parse_price_level(p.get("priceLevel")),
                )
            )
        return out
