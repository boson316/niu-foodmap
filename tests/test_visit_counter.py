from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from foodmap.visit_counter import format_visit_count, get_visit_count, increment_visit_count


def test_format_visit_count_with_number() -> None:
    assert format_visit_count(1234) == "累計瀏覽 1,234 人次"


def test_format_visit_count_when_unavailable() -> None:
    assert format_visit_count(None) == "瀏覽人次統計暫不可用"


def test_increment_visit_count_parses_response() -> None:
    body = json.dumps({"value": 42}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda self: self
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("foodmap.visit_counter.urllib.request.urlopen", return_value=mock_resp):
        assert increment_visit_count() == 42


def test_increment_visit_count_accepts_whole_float() -> None:
    body = json.dumps({"value": 7.0}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda self: self
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("foodmap.visit_counter.urllib.request.urlopen", return_value=mock_resp):
        assert increment_visit_count() == 7


def test_counter_url_uses_counterapi_domain() -> None:
    from foodmap.visit_counter import _counter_url

    assert _counter_url("hit").startswith("https://api.counterapi.com/v1/hit/")


def test_get_visit_count_returns_none_on_network_error() -> None:
    with patch("foodmap.visit_counter.urllib.request.urlopen", side_effect=TimeoutError):
        assert get_visit_count() is None
