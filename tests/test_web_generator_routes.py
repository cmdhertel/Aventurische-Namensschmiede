"""Regression tests for web generator form parsing."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

from routes.generator import _default_selected_region, _parse_checkbox_value  # noqa: E402


def test_parse_checkbox_value_treats_missing_checkbox_as_false() -> None:
    assert _parse_checkbox_value(None) is False


def test_parse_checkbox_value_treats_false_like_values_as_false() -> None:
    for value in ("", "false", "False", "0", "off", "no"):
        assert _parse_checkbox_value(value) is False


def test_parse_checkbox_value_treats_checked_values_as_true() -> None:
    for value in ("true", "True", "1", "on", "yes"):
        assert _parse_checkbox_value(value) is True


def test_default_selected_region_prefers_human_entries() -> None:
    origins = [
        {
            "id": "human",
            "species_id": "human",
            "culture_id": "all__human",
        },
        {"id": "firnelfen", "species_id": "elf"},
        {"id": "thorwal", "species_id": "human"},
        {"id": "ambosszwerge", "species_id": "dwarf"},
    ]

    assert _default_selected_region(origins) == "human"
