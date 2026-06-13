from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from foodmap.providers import MockRestaurantProvider
from foodmap.service import FoodMapService, SortMode, format_avg_spend, format_distance_m


def _build_service(data: Path | None) -> FoodMapService:
    provider = MockRestaurantProvider(json_path=data) if data else MockRestaurantProvider()
    return FoodMapService(provider)


def _cmd_search(args: argparse.Namespace) -> int:
    service = _build_service(args.data)
    rows = service.rank_nearby(
        center_lat=args.lat,
        center_lon=args.lon,
        radius_km=args.radius,
        min_reviews=args.min_reviews,
        sort_by=cast(SortMode, args.sort),
        limit=args.limit,
    )
    payload = FoodMapService.to_public_dict(rows)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not payload:
        print("(無結果：調整半徑、最少評論數或排序方式)", file=sys.stderr)
        return 0

    score_key = "huang_rating" if args.sort == "huang" else "bayesian_rating"
    score_label = "黃氏" if args.sort == "huang" else "貝氏"
    header = f"{'名稱':<18} {'距離':>10} {'星等':>6} {'評論':>6} {'消費':>10} {score_label:>6} {'綜合':>6} 分類"
    print(header)
    print("-" * len(header))
    for item in payload:
        name = item["name"][:16] + ("…" if len(item["name"]) > 16 else "")
        print(
            f"{name:<18} "
            f"{format_distance_m(item['distance_m']):>10} "
            f"{item['rating']:>6.1f} "
            f"{item['review_count']:>6} "
            f"{item['avg_spend_display']:>10} "
            f"{item[score_key]:>6.2f} "
            f"{item['composite_score']:>6.2f} "
            f"{item.get('category', '')}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="校園附近美食地圖（Mock 資料）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="依校園中心點與半徑篩選，並排序")
    p_search.add_argument("--lat", type=float, required=True, help="校園中心緯度")
    p_search.add_argument("--lon", type=float, required=True, help="校園中心經度")
    p_search.add_argument("--radius", type=float, default=2.0, help="搜尋半徑（公里）")
    p_search.add_argument("--min-reviews", type=int, default=0, help="最少評論數門檻")
    p_search.add_argument(
        "--sort",
        choices=("composite", "rating", "distance", "huang"),
        default="composite",
        help="composite=黃氏星等×距離；rating=貝氏星等；huang=黃氏星等；distance=由近到遠",
    )
    p_search.add_argument("--limit", type=int, default=50, help="最多輸出筆數")
    p_search.add_argument("--data", type=Path, default=None, help="自訂餐廳 JSON 路徑")
    p_search.add_argument("--format", choices=("table", "json"), default="table")
    p_search.set_defaults(func=_cmd_search)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
