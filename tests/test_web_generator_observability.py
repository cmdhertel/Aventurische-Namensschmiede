"""Regression tests for web route observability helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

from observability_utils import count_empty_names, name_length, safe_full_name
from namegen.models import Gender, GenerationMode, NameResult


class _LegacyName:
    def __init__(self, first: str, last: str) -> None:
        self.first = first
        self.last = last


class _EmptyName:
    first_name = ""
    last_name = ""


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


def test_name_length_is_non_negative() -> None:
    assert name_length(_EmptyName()) == 0
    assert name_length(_LegacyName("A", "B")) == 3


def test_count_empty_names_counts_blank_entries() -> None:
    names = [_LegacyName("Alrik", "Sohn"), _EmptyName(), _LegacyName("", "")]
    assert count_empty_names(names) == 2
