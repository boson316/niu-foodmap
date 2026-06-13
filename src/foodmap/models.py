from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Restaurant:
    """單一餐廳（評分為聚合後的平均星等）。"""

    id: str
    name: str
    lat: float
    lon: float
    rating: float
    review_count: int
    category: str = ""
    price_level: int | None = None

    @classmethod
    def from_dict(cls, raw: dict) -> Restaurant:
        return cls(
            id=str(raw["id"]),
            name=str(raw["name"]),
            lat=float(raw["lat"]),
            lon=float(raw["lon"]),
            rating=float(raw["rating"]),
            review_count=int(raw["review_count"]),
            category=str(raw.get("category", "")),
            price_level=int(raw["price_level"]) if raw.get("price_level") is not None else None,
        )
