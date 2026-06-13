from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_search_json_smoke() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "foodmap",
            "search",
            "--lat",
            "24.7464",
            "--lon",
            "121.7457",
            "--radius",
            "3.0",
            "--format",
            "json",
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(src)},
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(proc.stdout)
    assert isinstance(data, list)
    assert len(data) >= 5
    assert "composite_score" in data[0]
