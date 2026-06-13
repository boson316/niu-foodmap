from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Record architecture/tuning decision as artifact.")
    parser.add_argument("--title", required=True, help="Decision title")
    parser.add_argument("--context", required=True, help="Problem context")
    parser.add_argument("--decision", required=True, help="Decision content")
    parser.add_argument("--tradeoff", required=True, help="Tradeoff summary")
    parser.add_argument("--out", required=True, help="Output markdown path")
    args = parser.parse_args()

    utc_now = datetime.now(timezone.utc).isoformat()
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f"# Decision: {args.title}\n\n"
        f"- timestamp_utc: `{utc_now}`\n"
        f"- context: {args.context}\n"
        f"- decision: {args.decision}\n"
        f"- tradeoff: {args.tradeoff}\n"
    )
    output.write_text(content, encoding="utf-8")
    print(f"[OK] Decision artifact written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
