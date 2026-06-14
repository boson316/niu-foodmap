# Copyright (c) 2026 Boson Huang. All rights reserved. Unauthorized modification prohibited.
from __future__ import annotations

import math
from typing import Iterable, Literal

from foodmap.distance import HaversineCenter, haversine_km_from_center
from foodmap.models import Restaurant

RatingTier = Literal["low", "medium", "high"]

_TIER_WEIGHT: dict[RatingTier, float] = {
    "low": 0.65,      # 1～2 星
    "medium": 1.0,    # 3 星
    "high": 1.25,     # 4～5 星
}

_DEFAULT_REVIEW_SATURATION = 500


def rating_tier(rating: float) -> RatingTier:
    """Google Maps 星等分級：1～2 低、3 普通、4～5 高。"""
    if rating < 2.5:
        return "low"
    if rating < 4.0:
        return "medium"
    return "high"


def star_weight(rating: float) -> float:
    """星等愈高，權重愈大（0～1）。"""
    return max(0.0, min(1.0, rating / 5.0))


def review_weight(review_count: int, *, saturation: int = _DEFAULT_REVIEW_SATURATION) -> float:
    """評論數愈多，可信度權重愈高（對數飽和，0～1）。"""
    if review_count < 0:
        raise ValueError("review_count must be non-negative")
    if saturation <= 0:
        raise ValueError("saturation must be positive")
    if review_count == 0:
        return 0.1
    return min(1.0, math.log1p(review_count) / math.log1p(saturation))


def huang_weighted_rating(
    rating: float,
    review_count: int,
    *,
    review_saturation: int = _DEFAULT_REVIEW_SATURATION,
) -> float:
    """黃氏星等：星等分級 × 星分權重 × 評論量權重，合成單一評價分（約 0～5+）。"""
    tier_w = _TIER_WEIGHT[rating_tier(rating)]
    sw = star_weight(rating)
    rw = review_weight(review_count, saturation=review_saturation)
    return rating * tier_w * (0.5 + 0.5 * sw) * (0.4 + 0.6 * rw)


def bayesian_average_rating(
    rating: float,
    review_count: int,
    *,
    prior_mean: float,
    prior_strength: float,
) -> float:
    """貝氏平均星等，降低評論數極少時的極端高分／低分。"""
    if review_count < 0:
        raise ValueError("review_count must be non-negative")
    if prior_strength <= 0:
        raise ValueError("prior_strength must be positive")
    total = prior_strength * prior_mean + rating * review_count
    return total / (prior_strength + review_count)


def dataset_prior_mean(restaurants: Iterable[Restaurant]) -> float:
    num = 0.0
    den = 0
    rating_sum = 0.0
    count = 0
    for r in restaurants:
        num += r.rating * r.review_count
        den += r.review_count
        rating_sum += r.rating
        count += 1
    if count == 0:
        return 0.0
    return num / den if den else rating_sum / count


def composite_from_rating(
    reputation_score: float, distance_km: float,
     *, decay_km: float) -> float:
    """評價分 × 距離衰減 → 綜合分（愈近愈高）。"""
    if decay_km <= 0:
        raise ValueError("decay_km must be positive")
    return reputation_score * math.exp(-distance_km / decay_km)


def composite_from_bayes(bayesian_rating: float, distance_km: float, *, decay_km: float) -> float:
    """向後相容別名。"""
    return composite_from_rating(bayesian_rating, distance_km, decay_km=decay_km)


def composite_score(
    restaurant: Restaurant,
    *,
    center_lat: float,
    center_lon: float,
    prior_mean: float,
    prior_strength: float,
    decay_km: float,
) -> float:
    """結合貝氏星等與距離衰減（愈近愈加分）。"""
    bayes = bayesian_average_rating(
        restaurant.rating,
        restaurant.review_count,
        prior_mean=prior_mean,
        prior_strength=prior_strength,
    )
    center = HaversineCenter.from_degrees(center_lat, center_lon)
    dist = haversine_km_from_center(center, restaurant.lat, restaurant.lon)
    return composite_from_rating(bayes, dist, decay_km=decay_km)


def huang_composite_score(
    restaurant: Restaurant,
    *,
    center_lat: float,
    center_lon: float,
    decay_km: float,
    review_saturation: int = _DEFAULT_REVIEW_SATURATION,
) -> float:
    """黃氏星等 × 距離衰減 → 綜合分。"""
    huang = huang_weighted_rating(
        restaurant.rating,
        restaurant.review_count,
        review_saturation=review_saturation,
    )
    center = HaversineCenter.from_degrees(center_lat, center_lon)
    dist = haversine_km_from_center(center, restaurant.lat, restaurant.lon)
    return composite_from_rating(huang, dist, decay_km=decay_km)
