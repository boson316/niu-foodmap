from __future__ import annotations

from foodmap.wheel import _short_label, build_wheel_html


def _sample_items(count: int = 30) -> list[dict[str, object]]:
    return [
        {
            "name": f"測試餐廳 {index}",
            "composite_score": 3.0 - index * 0.01,
            "huang_rating": 5.0 + index * 0.01,
            "distance_display": f"{300 + index} 公尺",
            "maps_url": f"https://www.google.com/maps/search/?api=1&query=shop{index}",
        }
        for index in range(count)
    ]


def test_build_wheel_html_contains_spin_controls() -> None:
    html = build_wheel_html(_sample_items())
    assert "開始轉盤" in html
    assert "wheel-spin-btn" in html
    assert "wheel-legend" in html
    assert ">1</span>" in html


def test_build_wheel_html_uses_top_candidate_labels() -> None:
    html = build_wheel_html(_sample_items(5))
    assert "測試餐廳 4" in html
    assert ">5</span>" in html


def test_build_wheel_html_empty_state() -> None:
    html = build_wheel_html([])
    assert "沒有可抽選" in html


def test_short_label_truncates_long_name() -> None:
    assert _short_label("八方悅宜蘭文化旗艦店", max_len=6) == "八方悅宜蘭…"
