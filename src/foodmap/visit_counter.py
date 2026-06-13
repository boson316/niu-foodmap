"""Public visit counter via CounterAPI (Streamlit Cloud compatible)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

_API_BASE = "https://api.counterapi.com/v1"
_DEFAULT_NAMESPACE = "niu-foodmap"
_DEFAULT_KEY = "pageviews"
_TIMEOUT_SEC = 8


def counter_namespace() -> str:
    return os.environ.get("VISIT_COUNTER_NAMESPACE", _DEFAULT_NAMESPACE).strip() or _DEFAULT_NAMESPACE


def counter_key() -> str:
    return os.environ.get("VISIT_COUNTER_KEY", _DEFAULT_KEY).strip() or _DEFAULT_KEY


def _counter_url(action: str) -> str:
    namespace = counter_namespace()
    key = counter_key()
    return f"{_API_BASE}/{action}/{namespace}/{key}"


def _parse_value(raw: object) -> int | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float) and raw.is_integer() and raw >= 0:
        return int(raw)
    return None


def _fetch_count(url: str) -> int | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "niu-foodmap/1.0 (visit-counter)"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SEC) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError):
        return None
    return _parse_value(payload.get("value"))


def increment_visit_count() -> int | None:
    """Increment global counter and return the new total."""
    return _fetch_count(_counter_url("hit"))


def get_visit_count() -> int | None:
    """Read counter without incrementing."""
    return _fetch_count(_counter_url("get"))


def format_visit_count(count: int | None) -> str:
    if count is None:
        return "瀏覽人次統計暫不可用"
    return f"累計瀏覽 {count:,} 人次"
