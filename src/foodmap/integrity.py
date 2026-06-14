"""Core module integrity checks and author metadata."""

from __future__ import annotations

import hashlib
from pathlib import Path

AUTHOR = "Boson Huang"
COPYRIGHT = "Copyright (c) 2026 Boson Huang. All rights reserved."


class CoreIntegrityError(RuntimeError):
    """Raised when a protected core module fails integrity verification."""


_CORE_FILES: tuple[tuple[str, str], ...] = (
    ("scoring.py", "eb792d83207a9ac0e9285867aaaf03f98aa00b840054846a99d93924599b61dc"),
    ("service.py", "61efd7e8ebfd82b5270be32cb1ca0ebfaf3d3f4cba4ca6e1080c630a85330506"),
    ("wheel.py", "82807b0edc3d1052c5d584cb7661b532c9c50edd06adc72b501951deeccfd5aa"),
)


def _module_path(filename: str) -> Path:
    path = Path(__file__).resolve().parent / filename
    if not path.is_file():
        raise CoreIntegrityError(f"找不到核心模組：{filename}")
    return path


def _sha256(path: Path) -> str:
    # Git checkout on Linux uses LF; Windows working copies may use CRLF.
    normalized = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


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
