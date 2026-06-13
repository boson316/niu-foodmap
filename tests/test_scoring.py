from __future__ import annotations

import math

from foodmap.models import Restaurant
from foodmap.scoring import (
    bayesian_average_rating,
    composite_score,
    dataset_prior_mean,
    huang_composite_score,
    huang_weighted_rating,
    rating_tier,
    review_weight,
)


def test_rating_tier_boundaries() -> None:
    assert rating_tier(1.5) == "low"
    assert rating_tier(2.0) == "low"
    assert rating_tier(3.0) == "medium"
    assert rating_tier(3.9) == "medium"
    assert rating_tier(4.0) == "high"
    assert rating_tier(5.0) == "high"


def test_huang_high_star_beats_low_star_same_reviews() -> None:
    low = huang_weighted_rating(2.0, 200)
    high = huang_weighted_rating(4.5, 200)
    assert high > low


def test_huang_more_reviews_increase_score() -> None:
    few = huang_weighted_rating(4.5, 5)
    many = huang_weighted_rating(4.5, 500)
    assert many > few


def test_huang_high_tier_beats_medium_tier() -> None:
    medium = huang_weighted_rating(3.0, 100)
    high = huang_weighted_rating(4.5, 100)
    assert high > medium


def test_review_weight_saturates() -> None:
    assert review_weight(500) == 1.0
    assert review_weight(1000) == 1.0
    assert review_weight(10) < review_weight(100)


def test_bayesian_pulls_extreme_low_sample_toward_prior() -> None:
    m = 4.0
    b = bayesian_average_rating(5.0, 3, prior_mean=m, prior_strength=10.0)
    assert b < 5.0
    assert b > m


def test_dataset_prior_mean_weighted() -> None:
    rs = [
        Restaurant("a", "A", 0, 0, 4.0, 100, ""),
        Restaurant("b", "B", 0, 0, 2.0, 100, ""),
    ]
    assert math.isclose(dataset_prior_mean(rs), 3.0)


def test_composite_decreases_with_distance() -> None:
    r = Restaurant("x", "X", 25.0330, 121.5654, 4.5, 200, "")
    prior = 4.0
    s0 = composite_score(
        r,
        center_lat=25.0330,
        center_lon=121.5654,
        prior_mean=prior,
        prior_strength=8.0,
        decay_km=0.6,
    )
    s1 = composite_score(
        r,
        center_lat=25.0400,
        center_lon=121.5654,
        prior_mean=prior,
        prior_strength=8.0,
        decay_km=0.6,
    )
    assert s0 > s1


def test_huang_composite_decreases_with_distance() -> None:
    r = Restaurant("x", "X", 25.0330, 121.5654, 4.5, 200, "")
    s0 = huang_composite_score(r, center_lat=25.0330, center_lon=121.5654, decay_km=0.6)
    s1 = huang_composite_score(r, center_lat=25.0400, center_lon=121.5654, decay_km=0.6)
    assert s0 > s1
