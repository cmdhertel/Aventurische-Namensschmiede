"""Guard against accidentally committed merge conflict markers."""

from __future__ import annotations

from pathlib import Path


SCAN_DIRS = ("src", "web", "tests")
SKIP_PARTS = {".venv", "node_modules", "__pycache__"}


def _has_conflict_markers(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("<<<<<<< "):
            return True
        if stripped == "=======" or stripped.startswith("======="):
            return True
        if stripped.startswith(">>>>>>> "):
            return True
    return False


def test_no_merge_conflict_markers() -> None:
    root = Path(__file__).resolve().parents[1]
    offending: list[str] = []

    for rel in SCAN_DIRS:
        base = root / rel
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if SKIP_PARTS.intersection(path.parts):
                continue

            text = path.read_text(encoding="utf-8", errors="ignore")
            if _has_conflict_markers(text):
                offending.append(str(path.relative_to(root)))

    assert not offending, f"Merge conflict marker found in: {', '.join(offending)}"
