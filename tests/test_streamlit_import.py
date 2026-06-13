from __future__ import annotations

import pytest


def test_streamlit_app_importable() -> None:
    pytest.importorskip("streamlit")
    pytest.importorskip("pandas")
    import streamlit_app  # noqa: F401
