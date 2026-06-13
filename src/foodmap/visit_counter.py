"""Visit counter: browser-side fetch (works on Streamlit Cloud)."""

from __future__ import annotations

import html
import json
import os
import urllib.parse

_DEFAULT_PAGE_URL = "https://niu-foodmap.streamlit.app"
_SEEYOUFARM_API = "https://hits.seeyoufarm.com/api/count"
_SESSION_STORAGE_KEY = "niu_foodmap_visit_counted"


def counter_page_url() -> str:
    return os.environ.get("VISIT_COUNTER_PAGE_URL", _DEFAULT_PAGE_URL).strip() or _DEFAULT_PAGE_URL


def format_visit_count(count: int | None) -> str:
    if count is None:
        return "瀏覽人次統計暫不可用"
    return f"累計瀏覽 {count:,} 人次"


def build_visit_counter_html(page_url: str, *, author_line: str) -> str:
    """Render footer counter in the visitor browser (server outbound HTTP not required)."""
    page_url_js = json.dumps(page_url)
    storage_key_js = json.dumps(_SESSION_STORAGE_KEY)
    author_html = html.escape(author_line, quote=True)
    return f"""
<div style="font-size:0.85rem;color:#5f6368;line-height:1.6;padding:0.25rem 0;">
  <span>{author_html} · </span><span id="niu-visit-count">累計瀏覽 … 人次</span>
</div>
<script>
(function () {{
  const pageUrl = {page_url_js};
  const storageKey = {storage_key_js};
  const label = document.getElementById("niu-visit-count");
  const apiBase = "{_SEEYOUFARM_API}";
  const counted = sessionStorage.getItem(storageKey) === "1";
  const endpoint = counted
    ? apiBase + "?" + new URLSearchParams({{ url: pageUrl }}).toString()
    : apiBase + "/incr?" + new URLSearchParams({{ url: pageUrl }}).toString();

  fetch(endpoint, {{ method: "GET", mode: "cors" }})
    .then(function (response) {{
      if (!response.ok) throw new Error("bad status");
      return response.text();
    }})
    .then(function (text) {{
      const value = parseInt(text.trim(), 10);
      if (!Number.isFinite(value) || value < 0) throw new Error("bad value");
      sessionStorage.setItem(storageKey, "1");
      label.textContent = "累計瀏覽 " + value.toLocaleString("zh-TW") + " 人次";
    }})
    .catch(function () {{
      const badgeUrl = "https://hits.seeyoufarm.com/count?" +
        new URLSearchParams({{ url: pageUrl }}).toString();
      label.innerHTML = '累計瀏覽 <img src="' + badgeUrl +
        '" alt="人次" style="height:18px;vertical-align:middle;" />';
    }});
}})();
</script>
"""
