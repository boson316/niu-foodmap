from __future__ import annotations


def health() -> dict[str, str]:
    """Minimal health check for Day2 TDD smoke."""
    return {"status": "ok"}
