"""Public visit counter for Streamlit Cloud (no local storage)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

_COUNTERAPI_BASE = "https://api.counterapi.com/v1"
_DEFAULT_PAGE_URL = "https://niu-foodmap.streamlit.app"
_DEFAULT_NAMESPACE = "niu-foodmap"
_DEFAULT_KEY = "pageviews"
_TIMEOUT_SEC = 8
_USER_AGENT = "niu-foodmap/1.0 (visit-counter)"


def counter_page_url() -> str:
    return os.environ.get("VISIT_COUNTER_PAGE_URL", _DEFAULT_PAGE_URL).strip() or _DEFAULT_PAGE_URL


def counter_namespace() -> str:
    return os.environ.get("VISIT_COUNTER_NAMESPACE", _DEFAULT_NAMESPACE).strip() or _DEFAULT_NAMESPACE


def counter_key() -> str:
    return os.environ.get("VISIT_COUNTER_KEY", _DEFAULT_KEY).strip() or _DEFAULT_KEY


def _parse_value(raw: object) -> int | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float) and raw.is_integer() and raw >= 0:
        return int(raw)
    return None


def _parse_plain_int(text: str) -> int | None:
    stripped = text.strip()
    if not stripped.isdigit():
        return None
    return int(stripped)


def _http_get(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SEC) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError):
        return None


def _increment_seeyoufarm(page_url: str) -> int | None:
    query = urllib.parse.urlencode({"url": page_url})
    body = _http_get(f"https://hits.seeyoufarm.com/api/count/incr?{query}")
    if body is None:
        return None
    return _parse_plain_int(body)


def _increment_counterapi(namespace: str, key: str) -> int | None:
    url = f"{_COUNTERAPI_BASE}/hit/{namespace}/{key}"
    body = _http_get(url)
    if body is None:
        return None
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None
    return _parse_value(payload.get("value"))


def increment_visit_count() -> int | None:
    """Increment global counter; try multiple backends for Cloud reliability."""
    page_url = counter_page_url()
    count = _increment_seeyoufarm(page_url)
    if count is not None:
        return count
    return _increment_counterapi(counter_namespace(), counter_key())


def get_visit_count() -> int | None:
    page_url = counter_page_url()
    query = urllib.parse.urlencode({"url": page_url})
    body = _http_get(f"https://hits.seeyoufarm.com/api/count?{query}")
    if body is not None:
        parsed = _parse_plain_int(body)
        if parsed is not None:
            return parsed
    fallback = _http_get(f"{_COUNTERAPI_BASE}/get/{counter_namespace()}/{counter_key()}")
    if fallback is None:
        return None
    try:
        payload = json.loads(fallback)
    except json.JSONDecodeError:
        return None
    return _parse_value(payload.get("value"))


def format_visit_count(count: int | None) -> str:
    if count is None:
        return "瀏覽人次統計暫不可用"
    return f"累計瀏覽 {count:,} 人次"
