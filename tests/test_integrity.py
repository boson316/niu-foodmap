from __future__ import annotations

import pytest

from foodmap.integrity import verify_core_modules


def test_core_modules_integrity() -> None:
    verify_core_modules()
