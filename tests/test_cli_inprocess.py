from __future__ import annotations

import json
import runpy
import sys

import pytest

from foodmap.cli import main


def test_cli_search_json_inprocess(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(
        [
            "search",
            "--lat",
            "24.7464",
            "--lon",
            "121.7457",
            "--radius",
            "3.0",
            "--format",
            "json",
        ]
    )
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["name"]


def test_cli_search_table_inprocess(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(
        [
            "search",
            "--lat",
            "24.7464",
            "--lon",
            "121.7457",
            "--radius",
            "0.5",
            "--format",
            "table",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "名稱" in out


def test_cli_search_empty_stderr(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    p = tmp_path / "empty.json"
    p.write_text("[]", encoding="utf-8")
    rc = main(
        [
            "search",
            "--lat",
            "24.7464",
            "--lon",
            "121.7457",
            "--radius",
            "1",
            "--data",
            str(p),
            "--format",
            "table",
        ]
    )
    assert rc == 0
    err = capsys.readouterr().err
    assert "無結果" in err


def test_cli_sort_huang_json_inprocess(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(
        [
            "search",
            "--lat",
            "24.7464",
            "--lon",
            "121.7457",
            "--radius",
            "3.0",
            "--sort",
            "huang",
            "--format",
            "json",
        ]
    )
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) >= 1
    scores = [row["huang_rating"] for row in data]
    assert scores == sorted(scores, reverse=True)


def test_cli_invalid_sort_rejected() -> None:
    with pytest.raises(SystemExit):
        main(["search", "--lat", "0", "--lon", "0", "--sort", "nope"])


def test_foodmap_dunder_main(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "foodmap",
            "search",
            "--lat",
            "24.7464",
            "--lon",
            "121.7457",
            "--radius",
            "0.8",
            "--format",
            "json",
        ],
    )
    with pytest.raises(SystemExit) as ei:
        runpy.run_module("foodmap.__main__", run_name="__main__", alter_sys=False)
    assert ei.value.code == 0
