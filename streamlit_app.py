"""Streamlit Community Cloud entrypoint (repo root).

Set Main file path to ``streamlit_app.py`` (repo root) on share.streamlit.io.
Falls back to the same module when developing with ``streamlit run src/streamlit_app.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from streamlit_app import run  # noqa: E402

if __name__ == "__main__":
    run()
