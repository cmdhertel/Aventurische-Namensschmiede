"""Regression tests for web route observability helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

from observability_utils import safe_full_name
from namegen.models import Gender, GenerationMode, NameResult


class _LegacyName:
    def __init__(self, first: str, last: str) -> None:
        self.first = first
        self.last = last


def test_safe_full_name_uses_name_result_full_name() -> None:
    result = NameResult.build(
        first="Alrik",
        last="vom Berg",
        gender=Gender.ANY,
        region="kosch",
        mode=GenerationMode.SIMPLE,
    )

    assert safe_full_name(result) == "Alrik vom Berg"


def test_safe_full_name_supports_legacy_shape() -> None:
    legacy = _LegacyName("Rondra", "Löwenherz")

    assert safe_full_name(legacy) == "Rondra Löwenherz"
