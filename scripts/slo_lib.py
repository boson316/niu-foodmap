from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def load_slo_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_slo_config(start: Path | None = None) -> Path:
    root = (start or Path.cwd()).resolve()
    for directory in (root, *root.parents):
        candidate = directory / "slo.config.json"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("slo.config.json not found in cwd or parents")


def merge_slo(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)

    def _merge(dst: dict[str, Any], src: dict[str, Any]) -> None:
        for key, value in src.items():
            if isinstance(value, dict) and isinstance(dst.get(key), dict):
                _merge(dst[key], value)
            else:
                dst[key] = value

    _merge(merged, override)
    return merged


def benchmark_compare(baseline: dict[str, Any], optimized: dict[str, Any]) -> dict[str, Any]:
    def ratio(field: str) -> float:
        base = float(baseline[field])
        if base == 0:
            return 0.0
        return round((base - float(optimized[field])) / base, 4)

    return {
        "latency_improvement_ratio": ratio("p95_latency_ms"),
        "timeout_improvement_ratio": ratio("timeout_rate"),
        "cost_improvement_ratio": ratio("cost_per_request"),
        "quality_drop_ratio": float(optimized["quality_drop_ratio"]),
        "error_improvement_ratio": ratio("error_rate"),
    }


def evaluate_gate(
    baseline: dict[str, Any],
    optimized: dict[str, Any],
    slo: dict[str, Any],
) -> dict[str, Any]:
    kpi = slo["kpi"]
    gate = slo["gate"]
    checks: dict[str, bool] = {}

    if gate.get("use_absolute_kpi", True):
        checks["p95_absolute"] = float(optimized["p95_latency_ms"]) <= float(kpi["p95_latency_ms"])
        checks["timeout_absolute"] = float(optimized["timeout_rate"]) <= float(kpi["timeout_rate"])
        checks["cost_absolute"] = float(optimized["cost_per_request"]) <= float(kpi["cost_per_request"])
        checks["quality_absolute"] = float(optimized["quality_drop_ratio"]) <= float(
            kpi["quality_drop_ratio"]
        )
        checks["error_absolute"] = float(optimized.get("error_rate", 0.0)) <= float(
            kpi.get("error_rate", 1.0)
        )

    if gate.get("require_relative_improvement", True):
        checks["p95_relative"] = float(optimized["p95_latency_ms"]) <= float(
            baseline["p95_latency_ms"]
        ) * float(gate["p95_latency_ratio_max"])
        checks["cost_relative"] = float(optimized["cost_per_request"]) <= float(
            baseline["cost_per_request"]
        ) * float(gate["cost_ratio_max"])

    failed = [name for name, ok in checks.items() if not ok]
    return {
        "status": "GO" if not failed else "NO-GO",
        "checks": checks,
        "failed_checks": failed,
        "baseline": baseline,
        "optimized": optimized,
        "slo_config": {
            "kpi": kpi,
            "gate": gate,
        },
    }


def render_kpi_md(slo: dict[str, Any]) -> str:
    kpi = slo["kpi"]
    return (
        "# KPI\n\n"
        "## 核心 KPI（與 `slo.config.json` 同步）\n\n"
        f"- `p95_latency_ms <= {kpi['p95_latency_ms']}`\n"
        f"- `timeout_rate <= {kpi['timeout_rate']}`\n"
        f"- `cost_per_request <= {kpi['cost_per_request']}`\n"
        f"- `quality_drop_ratio <= {kpi['quality_drop_ratio']}`\n"
        f"- `error_rate <= {kpi.get('error_rate', 0.01)}`\n\n"
        "## 觀測週期\n\n"
        "- 每次 benchmark 都更新 artifacts\n"
        "- 每週更新一次 `weekly_review.md`\n\n"
        "## 驗收規則\n\n"
        "- `evaluate_gates.py` 讀取 `slo.config.json` 判斷 GO/NO-GO\n"
        "- 改 KPI 後執行：`python scripts/slo_sync.py`\n"
    )


def render_ci_gates_md(slo: dict[str, Any]) -> str:
    kpi = slo["kpi"]
    gate = slo["gate"]
    cov = slo["ci"]["cov_fail_under"]
    py = slo["ci"]["python_version"]
    return (
        "# CI Gates（GO / NO-GO）\n\n"
        "> 門檻來源：`slo.config.json`（由 `scripts/slo_sync.py` 產生本檔摘要）\n\n"
        "## Gate-0 測試與覆蓋率\n\n"
        "- `pytest -q`\n"
        f"- `pytest --cov=src --cov=scripts --cov-fail-under={cov} -q`\n\n"
        "任一失敗：`NO-GO`\n\n"
        "## Gate-1 Benchmark 可重現\n\n"
        "- `python scripts/run_benchmark.py --out artifacts`\n\n"
        "任一失敗：`NO-GO`\n\n"
        "## Gate-2 KPI 達標（絕對 + 相對）\n\n"
        "- `python scripts/evaluate_gates.py --baseline artifacts/baseline_metrics.json "
        "--optimized artifacts/optimized_metrics.json --out artifacts/gate_result.json`\n"
        "- `gate_result.json.status` 必須為 `GO`\n\n"
        "**絕對 KPI（optimized 須滿足）：**\n"
        f"- `p95_latency_ms <= {kpi['p95_latency_ms']}`\n"
        f"- `timeout_rate <= {kpi['timeout_rate']}`\n"
        f"- `cost_per_request <= {kpi['cost_per_request']}`\n"
        f"- `quality_drop_ratio <= {kpi['quality_drop_ratio']}`\n\n"
        "**相對改善（相對 baseline）：**\n"
        f"- `p95_latency_ms <= baseline × {gate['p95_latency_ratio_max']}`\n"
        f"- `cost_per_request <= baseline × {gate['cost_ratio_max']}`\n\n"
        "任一失敗：`NO-GO`\n\n"
        "## Gate-3 Artifact 完整性\n\n"
        "以下檔案缺任何一個都 `NO-GO`：\n\n"
        "- `artifacts/baseline_metrics.json`\n"
        "- `artifacts/optimized_metrics.json`\n"
        "- `artifacts/benchmark_compare.json`\n"
        "- `artifacts/gate_result.json`\n\n"
        f"## CI 環境\n\n- Python {py}+\n"
    )


def render_prd_kpi_section(slo: dict[str, Any]) -> str:
    kpi = slo["kpi"]
    gate = slo["gate"]
    return (
        "## 4. KPI（可量測，同步 `slo.config.json`）\n\n"
        f"- `p95_latency_ms <= {kpi['p95_latency_ms']}`\n"
        f"- `timeout_rate <= {kpi['timeout_rate']}`\n"
        f"- `cost_per_request <= {kpi['cost_per_request']}`\n"
        f"- `quality_drop_ratio <= {kpi['quality_drop_ratio']}`\n"
        f"- `error_rate <= {kpi.get('error_rate', 0.01)}`\n"
        f"- 相對門檻：p95 ≤ baseline×{gate['p95_latency_ratio_max']}；"
        f"cost ≤ baseline×{gate['cost_ratio_max']}\n"
    )


def render_agents_md(slo: dict[str, Any]) -> str:
    project = slo["project"]
    return (
        f"# AGENTS.md — {project['name']}\n\n"
        f"## Project\n{project['title']}\n\n"
        f"- 問題：{project['problem']}\n"
        f"- SLO 單一來源：`slo.config.json`（改 KPI 後跑 `python scripts/slo_sync.py`）\n\n"
        "## Hard Constraints\n\n"
        f"- Python {project['python']}+\n"
        "- TDD：先改 `tests/`，再改 `src/`\n"
        "- 不得放寬測試語意硬過關\n"
        "- 高風險變更（routing/batch/retry/timeout）先跑 gate 再第二輪\n\n"
        "## Required Files\n\n"
        "- `slo.config.json`, `PRD.md`, `TASKS.md`\n"
        "- `src/`, `tests/`\n"
        "- `CI_GATES.md`, `.github/workflows/ci-gate.yml`\n\n"
        "## Workflow\n\n"
        "1. 寫/改測試 → `pytest -q` 紅燈\n"
        "2. 實作 `src/` → 全綠\n"
        "3. `run_benchmark.py` → `evaluate_gates.py` → GO 才合併\n"
        "4. 調參/架構選擇寫 `artifacts/decision_*.md`\n\n"
        "## 雙模型（僅高風險）\n\n"
        "- 生成模型：實作\n"
        "- Reviewer：gate 邏輯、邊界、回歸\n"
        "- 動手前先列「預計改動檔案清單」\n"
    )


def sync_project_docs(project_root: Path, slo: dict[str, Any]) -> None:
    project_root.joinpath("KPI.md").write_text(render_kpi_md(slo), encoding="utf-8")
    project_root.joinpath("CI_GATES.md").write_text(render_ci_gates_md(slo), encoding="utf-8")
    project_root.joinpath("AGENTS.md").write_text(render_agents_md(slo), encoding="utf-8")

    prd_path = project_root / "PRD.md"
    prd = prd_path.read_text(encoding="utf-8")
    start = prd.find("## 4. KPI")
    end = prd.find("## 5.", start)
    if start == -1 or end == -1:
        raise ValueError("PRD.md missing ## 4. KPI or ## 5. section")
    prd_path.write_text(prd[:start] + render_prd_kpi_section(slo) + "\n" + prd[end:], encoding="utf-8")
