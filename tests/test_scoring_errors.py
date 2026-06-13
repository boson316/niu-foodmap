from __future__ import annotations

import pytest

from foodmap.scoring import bayesian_average_rating, composite_score, review_weight


def test_bayesian_rejects_negative_reviews() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        bayesian_average_rating(5.0, -1, prior_mean=4.0, prior_strength=1.0)


def test_bayesian_rejects_nonpositive_prior_strength() -> None:
    with pytest.raises(ValueError, match="prior_strength"):
        bayesian_average_rating(5.0, 1, prior_mean=4.0, prior_strength=0.0)


def test_review_weight_rejects_negative_reviews() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        review_weight(-1)


def test_composite_rejects_nonpositive_decay() -> None:
    from foodmap.models import Restaurant

    r = Restaurant("x", "X", 0, 0, 4.0, 10, "")
    with pytest.raises(ValueError, match="decay_km"):
        composite_score(
            r,
            center_lat=0,
            center_lon=0,
            prior_mean=4.0,
            prior_strength=5.0,
            decay_km=0.0,
        )
