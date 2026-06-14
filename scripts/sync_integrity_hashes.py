"""Sync SHA256 hashes in integrity.py from current core module files (LF-normalized)."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRITY = ROOT / "src" / "foodmap" / "integrity.py"
CORE_FILES = ("scoring.py", "service.py", "wheel.py")


def _sha256(path: Path) -> str:
    normalized = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def main() -> int:
    text = INTEGRITY.read_text(encoding="utf-8")
    updated = text
    for filename in CORE_FILES:
        path = ROOT / "src" / "foodmap" / filename
        if not path.is_file():
            print(f"MISSING: {path}", file=sys.stderr)
            return 1
        digest = _sha256(path)
        pattern = rf'(\("{re.escape(filename)}", ")[a-f0-9]{{64}}("\),)'

        def _repl(match: re.Match[str], d: str = digest) -> str:
            return f"{match.group(1)}{d}{match.group(2)}"

        new_text, count = re.subn(pattern, _repl, updated, count=1)
        if count != 1:
            print(f"FAIL: could not update hash for {filename}", file=sys.stderr)
            return 1
        updated = new_text
        print(f"{filename}: {digest}")

    if updated != text:
        INTEGRITY.write_text(updated, encoding="utf-8", newline="\n")
        print(f"Updated {INTEGRITY.relative_to(ROOT)}")
    else:
        print("integrity.py already in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
