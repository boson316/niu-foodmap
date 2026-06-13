"""Public visit counter via CountAPI (works on Streamlit Cloud without local storage)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

_DEFAULT_NAMESPACE = "niu-foodmap"
_DEFAULT_KEY = "pageviews"
_TIMEOUT_SEC = 5


def counter_namespace() -> str:
    return os.environ.get("VISIT_COUNTER_NAMESPACE", _DEFAULT_NAMESPACE).strip() or _DEFAULT_NAMESPACE


def counter_key() -> str:
    return os.environ.get("VISIT_COUNTER_KEY", _DEFAULT_KEY).strip() or _DEFAULT_KEY


def _counter_url(action: str) -> str:
    namespace = counter_namespace()
    key = counter_key()
    return f"https://api.countapi.xyz/{action}/{namespace}/{key}"


def _fetch_count(url: str) -> int | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "niu-foodmap/1.0 (visit-counter)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SEC) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError):
        return None
    value = payload.get("value")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


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
