"""Visit counter: browser-side fetch (works on Streamlit Cloud)."""
# -*- coding: utf-8 -*-

from __future__ import annotations

import html
import json
import os

_DEFAULT_PAGE_URL = "https://niu-foodmap.streamlit.app"
_COUNTERAPI_BASE = "https://api.counterapi.dev/v1"
_DEFAULT_NAMESPACE = "niu-foodmap"
_DEFAULT_KEY = "visits"
_SESSION_STORAGE_KEY = "niu_foodmap_visit_counted"
_UNAVAILABLE_LABEL = "瀏覽人次統計暫不可用"


def counter_page_url() -> str:
    return os.environ.get("VISIT_COUNTER_PAGE_URL", _DEFAULT_PAGE_URL).strip() or _DEFAULT_PAGE_URL


def counter_namespace() -> str:
    return os.environ.get("VISIT_COUNTER_NAMESPACE", _DEFAULT_NAMESPACE).strip() or _DEFAULT_NAMESPACE


def counter_key() -> str:
    return os.environ.get("VISIT_COUNTER_KEY", _DEFAULT_KEY).strip() or _DEFAULT_KEY


def counter_api_get_url(*, namespace: str | None = None, key: str | None = None) -> str:
    ns = namespace or counter_namespace()
    counter = key or counter_key()
    return f"{_COUNTERAPI_BASE}/{ns}/{counter}/"


def counter_api_up_url(*, namespace: str | None = None, key: str | None = None) -> str:
    ns = namespace or counter_namespace()
    counter = key or counter_key()
    return f"{_COUNTERAPI_BASE}/{ns}/{counter}/up"


def format_visit_count(count: int | None) -> str:
    if count is None:
        return _UNAVAILABLE_LABEL
    return f"累計瀏覽 {count:,} 人次"


def build_visit_counter_html(page_url: str, *, author_line: str) -> str:
    """Render footer counter in the visitor browser (server outbound HTTP not required)."""
    del page_url  # kept for call-site compatibility; counter uses namespace/key instead
    get_url_js = json.dumps(counter_api_get_url())
    up_url_js = json.dumps(counter_api_up_url())
    storage_key_js = json.dumps(_SESSION_STORAGE_KEY)
    unavailable_js = json.dumps(_UNAVAILABLE_LABEL)
    author_html = html.escape(author_line, quote=True)
    return f"""
<div style="font-size:0.85rem;color:#5f6368;line-height:1.55;padding:0.35rem 0 0.5rem;max-width:100%;word-break:break-word;">
  <span>{author_html} · </span><span id="niu-visit-count">累計瀏覽 … 人次</span>
</div>
<style>
@media (max-width: 768px) {{
  body {{
    margin: 0;
    padding: 0 4.5rem calc(0.5rem + env(safe-area-inset-bottom, 0px)) 0;
  }}
}}
</style>
<script>
(function () {{
  const getUrl = {get_url_js};
  const upUrl = {up_url_js};
  const storageKey = {storage_key_js};
  const unavailableLabel = {unavailable_js};
  const label = document.getElementById("niu-visit-count");
  const counted = sessionStorage.getItem(storageKey) === "1";
  const endpoint = counted ? getUrl : upUrl;

  fetch(endpoint, {{ method: "GET", mode: "cors" }})
    .then(function (response) {{
      if (!response.ok) throw new Error("bad status");
      return response.json();
    }})
    .then(function (payload) {{
      const value = Number(payload && payload.count);
      if (!Number.isFinite(value) || value < 0) throw new Error("bad value");
      if (!counted) sessionStorage.setItem(storageKey, "1");
      label.textContent = "累計瀏覽 " + value.toLocaleString("zh-TW") + " 人次";
    }})
    .catch(function () {{
      label.textContent = unavailableLabel;
    }});
}})();
</script>
"""
