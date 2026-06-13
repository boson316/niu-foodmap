from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MAX_RESTAURANT_JSON_BYTES = 5 * 1024 * 1024
MAX_RESTAURANT_RECORDS = 10_000


def read_bounded_text(path: Path, *, max_bytes: int = MAX_RESTAURANT_JSON_BYTES) -> str:
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(
            f"JSON file too large: {size} bytes (max {max_bytes})"
        )
    return path.read_text(encoding="utf-8")


def validate_restaurant_record(raw: Any, *, index: int) -> None:
    prefix = f"record[{index}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{prefix} must be a JSON object")

    for key in ("id", "name", "lat", "lon", "rating", "review_count"):
        if key not in raw:
            raise ValueError(f"{prefix} missing required field: {key}")

    if not str(raw["id"]).strip():
        raise ValueError(f"{prefix}.id must be a non-empty string")
    if not str(raw["name"]).strip():
        raise ValueError(f"{prefix}.name must be a non-empty string")

    lat = float(raw["lat"])
    lon = float(raw["lon"])
    if not -90.0 <= lat <= 90.0:
        raise ValueError(f"{prefix}.lat must be between -90 and 90")
    if not -180.0 <= lon <= 180.0:
        raise ValueError(f"{prefix}.lon must be between -180 and 180")

    rating = float(raw["rating"])
    if not 0.0 <= rating <= 5.0:
        raise ValueError(f"{prefix}.rating must be between 0 and 5")

    review_count = int(raw["review_count"])
    if review_count < 0:
        raise ValueError(f"{prefix}.review_count must be non-negative")

    if raw.get("price_level") is not None:
        price_level = int(raw["price_level"])
        if not 1 <= price_level <= 4:
            raise ValueError(f"{prefix}.price_level must be between 1 and 4")


def load_restaurant_array(
    path: Path,
    *,
    max_bytes: int = MAX_RESTAURANT_JSON_BYTES,
    max_records: int = MAX_RESTAURANT_RECORDS,
) -> list[dict[str, Any]]:
    text = read_bounded_text(path, max_bytes=max_bytes)
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.name}: {exc.msg}") from exc

    if not isinstance(raw, list):
        raise ValueError(f"{path.name} must be a JSON array")

    if len(raw) > max_records:
        raise ValueError(
            f"too many records: {len(raw)} (max {max_records})"
        )

    for index, item in enumerate(raw):
        validate_restaurant_record(item, index=index)

    return raw
