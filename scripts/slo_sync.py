from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from slo_lib import find_slo_config, load_slo_config, sync_project_docs


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync PRD/KPI/CI_GATES/AGENTS from slo.config.json")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to slo.config.json (default: search from cwd)",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root (default: parent of config file)",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve() if args.config else find_slo_config()
    project_root = Path(args.project_root).resolve() if args.project_root else config_path.parent
    slo = load_slo_config(config_path)
    sync_project_docs(project_root, slo)
    print(f"[OK] Synced docs from: {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
