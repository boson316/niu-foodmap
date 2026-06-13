from __future__ import annotations

import argparse
import json
from pathlib import Path

from slo_lib import evaluate_gate, find_slo_config, load_slo_config


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate GO/NO-GO from benchmark artifacts.")
    parser.add_argument("--baseline", required=True, help="Path to baseline_metrics.json")
    parser.add_argument("--optimized", required=True, help="Path to optimized_metrics.json")
    parser.add_argument("--out", default="artifacts/gate_result.json", help="Output gate result path")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to slo.config.json (default: search from cwd)",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve() if args.config else find_slo_config()
    slo = load_slo_config(config_path)
    baseline = _load_json(Path(args.baseline))
    optimized = _load_json(Path(args.optimized))
    result = evaluate_gate(baseline, optimized, slo)

    out_path = Path(args.out)
    _write_json(out_path, result)
    print(f"[{result['status']}] Gate evaluated: {out_path}")
    return 0 if result["status"] == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
