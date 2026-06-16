from __future__ import annotations

import pytest

from foodmap.wheel import (
    _polar_xy,
    _short_label,
    _svg_wheel_rotor,
    build_wheel_html,
    segment_index_at_rotation,
    spin_alignment_degrees,
    spin_delta_degrees,
)


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
    assert "wheel-maps-btn" in html
    assert "openMapsUrl" in html
    assert "openExternalUrl" in html
    assert "window.location.href" not in html
    assert 'class="wheel-svg-label">1</text>' in html
    assert 'id="wheel-rotor"' in html


def test_svg_wheel_rotor_has_matching_segment_and_label_count() -> None:
    svg = _svg_wheel_rotor(30)
    assert svg.count("<path ") == 30
    assert svg.count("<text ") == 30


def test_polar_xy_places_top_at_twelve_oclock() -> None:
    x, y = _polar_xy(200.0, 200.0, 100.0, 0.0)
    assert x == pytest.approx(200.0)
    assert y == pytest.approx(100.0)


def test_build_wheel_html_uses_top_candidate_labels() -> None:
    html = build_wheel_html(_sample_items(5))
    assert "測試餐廳 4" in html
    assert ">5</span>" in html


def test_build_wheel_html_empty_state() -> None:
    html = build_wheel_html([])
    assert "沒有可抽選" in html


def test_short_label_truncates_long_name() -> None:
    assert _short_label("八方悅宜蘭文化旗艦店", max_len=6) == "八方悅宜蘭…"


def test_spin_alignment_degrees_centers_segment_under_pointer() -> None:
    assert spin_alignment_degrees(0, 30) == 0.0
    assert spin_alignment_degrees(1, 8) == 315.0
    assert spin_alignment_degrees(7, 8) == 45.0


def test_spin_delta_accumulates_from_current_rotation() -> None:
    assert spin_delta_degrees(132.0, 12, 30, extra_turns=0) == 84.0
    assert spin_delta_degrees(0.0, 19, 30, extra_turns=0) == 132.0
    assert spin_delta_degrees(132.0, 19, 30, extra_turns=0) == 360.0


def test_segment_index_at_rotation_matches_alignment() -> None:
    for index in range(30):
        rotation = spin_alignment_degrees(index, 30)
        assert segment_index_at_rotation(rotation, 30) == index


def test_build_wheel_html_spin_controls_and_delta_logic() -> None:
    html = build_wheel_html(_sample_items(12))
    assert "開始轉盤" in html
    assert "wheel-actions-top" in html
    assert "segmentAtPointer" in html
    assert "applyRotation" in html
    assert "targetMod - currentMod" in html
    wheel_idx = html.index('class="wheel-stage"')
    result_idx = html.index('id="wheel-result"')
    legend_idx = html.index('class="wheel-legend"')
    assert wheel_idx < result_idx < legend_idx
