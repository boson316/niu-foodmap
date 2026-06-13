from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from slo_lib import load_slo_config, merge_slo, sync_project_docs


def _validate_project_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise ValueError("Project name cannot be empty.")
    invalid_chars = {"\\", "/", ":"}
    if any(char in normalized for char in invalid_chars):
        raise ValueError("Project name cannot contain path separator characters.")
    return normalized


def _clean_artifacts_dir(artifacts_dir: Path) -> None:
    if not artifacts_dir.exists():
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        return
    for child in artifacts_dir.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def _copy_ignore(_dir: str, names: list[str]) -> set[str]:
    ignored = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "slo.defaults.json",
    }
    out = set()
    for name in names:
        if name in ignored or name.endswith(".pyc"):
            out.add(name)
        if name in {
            "baseline_metrics.json",
            "optimized_metrics.json",
            "gate_result.json",
            "benchmark_compare.json",
        }:
            out.add(name)
        if name.startswith("decision_") and name.endswith(".md"):
            out.add(name)
    return out


def _build_slo(
    template_root: Path,
    project_name: str,
    title: str | None,
    slo_override_path: Path | None,
) -> dict:
    defaults = load_slo_config(template_root / "slo.defaults.json")
    defaults["project"]["name"] = project_name
    defaults["project"]["title"] = title or project_name.replace("_", " ").title()
    if slo_override_path:
        override = load_slo_config(slo_override_path)
        return merge_slo(defaults, override)
    return defaults


def _patch_prd_header(project_root: Path, slo: dict) -> None:
    prd_path = project_root / "PRD.md"
    body = prd_path.read_text(encoding="utf-8")
    title = slo["project"]["title"]
    if body.startswith("# PRD\n"):
        body = f"# PRD — {title}\n\n" + body[len("# PRD\n") :]
    prd_path.write_text(body, encoding="utf-8")


def _run_day1_verify(project_root: Path) -> int:
    commands = [
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "scripts/run_benchmark.py", "--out", "artifacts"],
        [
            sys.executable,
            "scripts/evaluate_gates.py",
            "--baseline",
            "artifacts/baseline_metrics.json",
            "--optimized",
            "artifacts/optimized_metrics.json",
            "--out",
            "artifacts/gate_result.json",
        ],
    ]
    for cmd in commands:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[FAIL] {' '.join(cmd)}", file=sys.stderr)
            if result.stdout:
                print(result.stdout, file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return result.returncode
    print("[OK] Day1 verify: pytest + benchmark + gate passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a new project (PRD + TDD + CI + synced SLO)."
    )
    parser.add_argument("project_name", nargs="?", help="New project folder name")
    parser.add_argument("--dest-root", default=None, help="Destination root (default: code/)")
    parser.add_argument("--title", default=None, help="Human-readable project title")
    parser.add_argument("--slo", default=None, help="Optional slo JSON to merge over defaults")
    parser.add_argument("--verify", action="store_true", help="Run Day1 pytest+benchmark+gate")
    args = parser.parse_args()

    try:
        project_name = _validate_project_name(args.project_name or input("Project name: ").strip())
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1

    template_root = Path(__file__).resolve().parents[1]
    dest_root = (
        Path(args.dest_root).resolve()
        if args.dest_root
        else template_root.parent.resolve()
    )
    target_dir = dest_root / project_name

    if target_dir.exists():
        print(f"[ERROR] Target already exists: {target_dir}")
        return 1
    if template_root in target_dir.parents:
        print("[ERROR] Target directory cannot be inside template directory.")
        return 1

    slo_override = Path(args.slo).resolve() if args.slo else None
    slo = _build_slo(template_root, project_name, args.title, slo_override)

    shutil.copytree(template_root, target_dir, ignore=_copy_ignore)
    _clean_artifacts_dir(target_dir / "artifacts")

    (target_dir / "slo.config.json").write_text(
        json.dumps(slo, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if (target_dir / "slo.defaults.json").exists():
        (target_dir / "slo.defaults.json").unlink()

    _patch_prd_header(target_dir, slo)
    sync_project_docs(target_dir, slo)

    print(f"[OK] Scaffolded: {target_dir}")
    print(f"[OK] SLO: {target_dir / 'slo.config.json'}")
    print("[NEXT] cd", target_dir)
    print("[NEXT] python -m pip install -U pytest pytest-cov")
    print("[NEXT] pytest -q")
    print("[NEXT] Edit PRD.md / tests/ then implement src/")

    if args.verify:
        return _run_day1_verify(target_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
