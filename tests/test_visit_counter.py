from __future__ import annotations

import json
from unittest.mock import patch

from foodmap.visit_counter import (
    _increment_counterapi,
    _increment_seeyoufarm,
    _parse_plain_int,
    format_visit_count,
    get_visit_count,
    increment_visit_count,
)


def test_format_visit_count_with_number() -> None:
    assert format_visit_count(1234) == "累計瀏覽 1,234 人次"


def test_format_visit_count_when_unavailable() -> None:
    assert format_visit_count(None) == "瀏覽人次統計暫不可用"


def test_parse_plain_int() -> None:
    assert _parse_plain_int(" 42\n") == 42
    assert _parse_plain_int("x") is None


def test_increment_seeyoufarm_parses_plain_text() -> None:
    with patch("foodmap.visit_counter._http_get", return_value="15"):
        assert _increment_seeyoufarm("https://niu-foodmap.streamlit.app") == 15


def test_increment_counterapi_parses_json() -> None:
    with patch(
        "foodmap.visit_counter._http_get",
        return_value=json.dumps({"value": 9}),
    ):
        assert _increment_counterapi("niu-foodmap", "pageviews") == 9


def test_increment_visit_count_prefers_seeyoufarm() -> None:
    with patch("foodmap.visit_counter._increment_seeyoufarm", return_value=100):
        with patch("foodmap.visit_counter._increment_counterapi") as counterapi:
            assert increment_visit_count() == 100
            counterapi.assert_not_called()


def test_increment_visit_count_falls_back_to_counterapi() -> None:
    with patch("foodmap.visit_counter._increment_seeyoufarm", return_value=None):
        with patch("foodmap.visit_counter._increment_counterapi", return_value=7):
            assert increment_visit_count() == 7


def test_get_visit_count_returns_none_on_total_failure() -> None:
    with patch("foodmap.visit_counter._http_get", return_value=None):
        assert get_visit_count() is None
