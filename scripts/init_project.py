from __future__ import annotations

import sys

from scaffold import main as scaffold_main


def main() -> int:
    print("[INFO] init_project.py -> scaffold.py (use scaffold for new projects)")
    return scaffold_main()


if __name__ == "__main__":
    raise SystemExit(main())
