from __future__ import annotations

from foodmap.visit_counter import (
    build_visit_counter_html,
    counter_page_url,
    format_visit_count,
)


def test_format_visit_count_with_number() -> None:
    assert format_visit_count(1234) == "累計瀏覽 1,234 人次"


def test_format_visit_count_when_unavailable() -> None:
    assert format_visit_count(None) == "瀏覽人次統計暫不可用"


def test_counter_page_url_default() -> None:
    assert counter_page_url().endswith("streamlit.app")


def test_build_visit_counter_html_includes_author_and_api() -> None:
    html_out = build_visit_counter_html(
        "https://niu-foodmap.streamlit.app",
        author_line="© 2026 Boson Huang",
    )
    assert "© 2026 Boson Huang" in html_out
    assert "hits.seeyoufarm.com/api/count" in html_out
    assert "niu-visit-count" in html_out
    assert "sessionStorage" in html_out
