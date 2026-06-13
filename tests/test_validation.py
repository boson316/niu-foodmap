from __future__ import annotations

import json
from pathlib import Path

import pytest

from foodmap.providers import MockRestaurantProvider
from foodmap.validation import (
    MAX_RESTAURANT_JSON_BYTES,
    load_restaurant_array,
    read_bounded_text,
    validate_restaurant_record,
)


def test_validate_rejects_missing_field() -> None:
    with pytest.raises(ValueError, match="missing required field: lat"):
        validate_restaurant_record(
            {"id": "a", "name": "A", "lon": 121.0, "rating": 4.0, "review_count": 1},
            index=0,
        )


def test_validate_rejects_out_of_range_rating() -> None:
    with pytest.raises(ValueError, match="rating must be between 0 and 5"):
        validate_restaurant_record(
            {
                "id": "a",
                "name": "A",
                "lat": 25.0,
                "lon": 121.0,
                "rating": 5.5,
                "review_count": 1,
            },
            index=3,
        )


def test_load_rejects_oversized_file(tmp_path: Path) -> None:
    path = tmp_path / "big.json"
    path.write_bytes(b"[" + b" " * (MAX_RESTAURANT_JSON_BYTES + 1) + b"]")
    with pytest.raises(ValueError, match="too large"):
        read_bounded_text(path)


def test_load_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        load_restaurant_array(path)


def test_provider_rejects_bad_record(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps([{"id": "x", "name": "X", "lat": 25.0, "lon": 121.0, "rating": 6.0, "review_count": 1}]),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="rating must be between 0 and 5"):
        MockRestaurantProvider(json_path=path).list_restaurants()
