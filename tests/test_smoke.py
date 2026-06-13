from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_benchmark_and_gate_smoke(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    scripts_dir = root / "scripts"
    out_dir = tmp_path / "artifacts"
    config_src = root / "slo.config.json"
    if not config_src.is_file():
        config_src = root / "slo.defaults.json"
    config_dst = tmp_path / "slo.config.json"
    shutil.copy(config_src, config_dst)

    subprocess.run(
        [
            sys.executable,
            str(scripts_dir / "run_benchmark.py"),
            "--out",
            str(out_dir),
            "--config",
            str(config_dst),
        ],
        check=True,
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(scripts_dir / "evaluate_gates.py"),
            "--baseline",
            str(out_dir / "baseline_metrics.json"),
            "--optimized",
            str(out_dir / "optimized_metrics.json"),
            "--out",
            str(out_dir / "gate_result.json"),
            "--config",
            str(config_dst),
        ],
        check=True,
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    gate = json.loads((out_dir / "gate_result.json").read_text(encoding="utf-8"))
    assert gate["status"] == "GO"
