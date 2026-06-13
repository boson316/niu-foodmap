from __future__ import annotations

import argparse
import json
from pathlib import Path

from slo_lib import benchmark_compare, find_slo_config, load_slo_config


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate baseline/optimized benchmark artifacts.")
    parser.add_argument("--out", default="artifacts", help="Output directory")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to slo.config.json (default: search from cwd)",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve() if args.config else find_slo_config()
    slo = load_slo_config(config_path)
    out_dir = Path(args.out)
    baseline = dict(slo["benchmark"]["baseline"])
    optimized = dict(slo["benchmark"]["optimized"])
    compare = benchmark_compare(baseline, optimized)

    _write_json(out_dir / "baseline_metrics.json", baseline)
    _write_json(out_dir / "optimized_metrics.json", optimized)
    _write_json(out_dir / "benchmark_compare.json", compare)
    print(f"[OK] Benchmark artifacts generated in: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
