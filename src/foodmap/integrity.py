"""Core module integrity checks and author metadata."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

AUTHOR = "Boson Huang"
COPYRIGHT = "Copyright (c) 2026 Boson Huang. All rights reserved."


class CoreIntegrityError(RuntimeError):
    """Raised when a protected core module fails integrity verification."""


_CORE_FILES: tuple[tuple[str, str], ...] = (
    ("scoring.py", "6dd25e8f6dc6d9a703e66e76749406957447057790dd0794b36063f1e8dc97d3"),
    ("service.py", "84313a93232c59de6603e4747b6be83a9bb6aa7d824dc085d2d8b345817bc8eb"),
    ("wheel.py", "f1342c4b4d894fe9b11a4c8ef712546e00020d343b58998d0c966fbf4244d716"),
)


def _module_path(filename: str) -> Path:
    spec = importlib.util.find_spec(f"foodmap.{filename[:-3]}")
    if spec is None or not spec.origin:
        raise CoreIntegrityError(f"找不到核心模組：{filename}")
    return Path(spec.origin)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_core_modules() -> None:
    """Fail fast if protected algorithm files were modified."""
    for filename, expected in _CORE_FILES:
        path = _module_path(filename)
        actual = _sha256(path)
        if actual != expected:
            raise CoreIntegrityError(
                f"核心模組 {filename} 完整性驗證失敗（可能被竄改）。"
                " 請使用作者官方部署版本。"
            )


def author_notice() -> str:
    return f"© 2026 {AUTHOR} · 核心演算法受著作權保護 · 禁止未授權複製或修改"
