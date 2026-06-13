from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Iterator, Literal, Sequence
from urllib.parse import quote

from foodmap.distance import HaversineCenter, approx_in_radius_bbox, haversine_km_from_center
from foodmap.models import Restaurant
from foodmap.providers import RestaurantProvider
from foodmap.scoring import (
    RatingTier,
    bayesian_average_rating,
    composite_from_rating,
    dataset_prior_mean,
    huang_weighted_rating,
    rating_tier,
)

SortMode = Literal["composite", "rating", "distance", "huang"]


def build_maps_url(name: str, lat: float, lon: float, *, place_id: str | None = None) -> str:
    """Google Maps 連結：優先用 place_id 開啟店家頁，否則用「店名@座標」搜尋。"""
    encoded_name = quote(name)
    if place_id:
        pid = place_id.removeprefix("places/")
        if pid:
            return (
                f"https://www.google.com/maps/search/?api=1"
                f"&query={encoded_name}&query_place_id={quote(pid)}"
            )
    return f"https://www.google.com/maps/search/?api=1&query={quote(f'{name}@{lat},{lon}')}"


def format_distance_m(distance_m: int) -> str:
    """距離顯示：<1000 為「N 公尺」，≥1000 為「X.X km」。"""
    if distance_m >= 1000:
        return f"{distance_m / 1000:.1f} km"
    return f"{distance_m} 公尺"


_AVG_SPEND_BY_LEVEL: dict[int, str] = {
    1: "$100–300",
    2: "$300–600",
    3: "$600–1,200",
    4: "$1,200+",
}


def format_avg_spend(price_level: int | None) -> str:
    """Google price_level（1–4）→ 宜蘭學生區間參考的人均消費文字。"""
    if price_level is None:
        return "未提供"
    return _AVG_SPEND_BY_LEVEL.get(price_level, "未提供")


@dataclass(frozen=True, slots=True)
class RankedRestaurant:
    restaurant: Restaurant
    distance_km: float
    bayesian_rating: float
    huang_rating: float
    rating_tier: RatingTier
    composite: float


class FoodMapService:
    def __init__(
        self,
        provider: RestaurantProvider,
        *,
        prior_strength: float = 8.0,
        decay_km: float = 0.6,
    ) -> None:
        self._provider = provider
        self._prior_strength = prior_strength
        self._decay_km = decay_km

    def _iter_in_radius(
        self,
        all_items: Sequence[Restaurant],
        *,
        center: HaversineCenter,
        center_lat: float,
        center_lon: float,
        radius_km: float,
        min_reviews: int,
        prior_mean: float,
        prior_strength: float,
        decay_km: float,
    ) -> Iterator[RankedRestaurant]:
        for r in all_items:
            if r.review_count < min_reviews:
                continue
            if not approx_in_radius_bbox(center_lat, center_lon, r.lat, r.lon, radius_km):
                continue
            dist = haversine_km_from_center(center, r.lat, r.lon)
            if dist > radius_km:
                continue
            bayes = bayesian_average_rating(
                r.rating,
                r.review_count,
                prior_mean=prior_mean,
                prior_strength=prior_strength,
            )
            huang = huang_weighted_rating(r.rating, r.review_count)
            tier = rating_tier(r.rating)
            comp = composite_from_rating(huang, dist, decay_km=decay_km)
            yield RankedRestaurant(
                restaurant=r,
                distance_km=dist,
                bayesian_rating=bayes,
                huang_rating=huang,
                rating_tier=tier,
                composite=comp,
            )

    def rank_nearby(
        self,
        *,
        center_lat: float,
        center_lon: float,
        radius_km: float,
        min_reviews: int = 0,
        sort_by: SortMode = "composite",
        limit: int = 50,
    ) -> list[RankedRestaurant]:
        if radius_km <= 0:
            raise ValueError("radius_km must be positive")
        if min_reviews < 0:
            raise ValueError("min_reviews must be non-negative")
        if limit <= 0:
            raise ValueError("limit must be positive")

        all_items = list(self._provider.list_restaurants())
        prior_mean = dataset_prior_mean(all_items)
        center = HaversineCenter.from_degrees(center_lat, center_lon)
        candidates = self._iter_in_radius(
            all_items,
            center=center,
            center_lat=center_lat,
            center_lon=center_lon,
            radius_km=radius_km,
            min_reviews=min_reviews,
            prior_mean=prior_mean,
            prior_strength=self._prior_strength,
            decay_km=self._decay_km,
        )

        if sort_by == "composite":
            return heapq.nlargest(limit, candidates, key=lambda x: x.composite)
        if sort_by == "rating":
            return heapq.nlargest(
                limit,
                candidates,
                key=lambda x: (x.bayesian_rating, -x.distance_km),
            )
        if sort_by == "distance":
            return heapq.nsmallest(limit, candidates, key=lambda x: x.distance_km)
        if sort_by == "huang":
            return heapq.nlargest(
                limit,
                candidates,
                key=lambda x: (x.huang_rating, -x.distance_km),
            )
        raise ValueError(f"unknown sort_by: {sort_by!r}")

    @staticmethod
    def to_public_dict(rows: Sequence[RankedRestaurant]) -> list[dict]:
        out: list[dict] = []
        for row in rows:
            r = row.restaurant
            out.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "lat": r.lat,
                    "lon": r.lon,
                    "rating": r.rating,
                    "review_count": r.review_count,
                    "category": r.category,
                    "price_level": r.price_level,
                    "avg_spend_display": format_avg_spend(r.price_level),
                    "distance_km": round(row.distance_km, 4),
                    "distance_m": int(round(row.distance_km * 1000)),
                    "distance_display": format_distance_m(int(round(row.distance_km * 1000))),
                    "bayesian_rating": round(row.bayesian_rating, 4),
                    "huang_rating": round(row.huang_rating, 4),
                    "rating_tier": row.rating_tier,
                    "composite_score": round(row.composite, 4),
                    "maps_url": build_maps_url(r.name, r.lat, r.lon, place_id=r.id),
                }
            )
        return out
