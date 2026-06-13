from __future__ import annotations

"""一次性從 Google Places API (New) 抓資料，存成與 sample_restaurants.json 相同格式。

用法（PowerShell）— 建議抓滿 100 家：
  $env:PYTHONPATH = "src"
  $env:GOOGLE_MAPS_API_KEY = "你的金鑰"
  python scripts/fetch_places_to_json.py --target 100 --grid 3 --radius-m 4000

之後查詢走快取（不燒 API 額度）：
  python -m foodmap search --lat 24.7464 --lon 121.7457 --data data/places_cache.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foodmap.providers import GooglePlacesProvider  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Google Places nearby restaurants to JSON cache.")
    parser.add_argument("--lat", type=float, default=24.7464, help="Center latitude")
    parser.add_argument("--lon", type=float, default=121.7457, help="Center longitude")
    parser.add_argument("--radius-m", type=float, default=4000.0, help="Search radius in meters")
    parser.add_argument("--max-pages", type=int, default=3, help="Max API pages per grid cell (20/page)")
    parser.add_argument(
        "--target",
        type=int,
        default=100,
        help="Unique places to collect (uses multi-center grid when >20)",
    )
    parser.add_argument("--grid", type=int, default=3, help="Grid size (3 = 3x3 centers)")
    parser.add_argument("--out", type=Path, default=Path("data/places_cache.json"), help="Output JSON path")
    args = parser.parse_args()

    if not os.environ.get("GOOGLE_MAPS_API_KEY"):
        print(
            "[ERROR] GOOGLE_MAPS_API_KEY is not set.\n"
            "  PowerShell: $env:GOOGLE_MAPS_API_KEY = \"你的金鑰\"\n"
            "  Then re-run this script.",
            file=sys.stderr,
        )
        return 1

    provider = GooglePlacesProvider(
        center_lat=args.lat,
        center_lon=args.lon,
        radius_m=args.radius_m,
        max_pages=args.max_pages,
    )
    if args.target > 20:
        rows = provider.list_restaurants_dense(target=args.target, grid=args.grid)
    else:
        rows = provider.list_restaurants()[: args.target]

    payload = [
        {
            "id": r.id,
            "name": r.name,
            "lat": r.lat,
            "lon": r.lon,
            "rating": r.rating,
            "review_count": r.review_count,
            "category": r.category,
            "price_level": r.price_level,
        }
        for r in rows
    ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Wrote {len(payload)} restaurants -> {args.out.resolve()}")
    if len(payload) < args.target:
        print(
            f"[WARN] Only {len(payload)} unique places (target {args.target}). "
            "Try --radius-m 5000 --grid 4 or run again later.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
