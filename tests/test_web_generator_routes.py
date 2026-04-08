"""Regression tests for web generator form parsing."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

from routes.generator import (  # noqa: E402
    _default_selected_region,
    _parse_checkbox_value,
    _profession_preview_map_for_origins,
)


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
            "has_compose": "true",
        },
        {"id": "firnelfen", "species_id": "elf", "has_compose": "false"},
        {"id": "thorwal", "species_id": "human", "has_compose": "false"},
        {"id": "ambosszwerge", "species_id": "dwarf", "has_compose": "false"},
    ]

    assert _default_selected_region(origins) == "human"


def test_profession_preview_map_for_origins_contains_selection_specific_professions() -> None:
    preview_map = _profession_preview_map_for_origins(
        [
            {"id": "mittelreich_perricum"},
            {"id": "mittelreich_kosch"},
        ]
    )

    perricum_profane = next(
        group
        for group in preview_map["mittelreich_perricum"]["alle"]["groups"]
        if group["id"] == "profan"
    )
    kosch_profane = next(
        group
        for group in preview_map["mittelreich_kosch"]["alle"]["groups"]
        if group["id"] == "profan"
    )
    perricum_kaempfer = next(
        group
        for group in preview_map["mittelreich_perricum"]["kaempfer"]["groups"]
        if group["id"] == "kaempfer"
    )

    assert "Hafenwache" not in perricum_profane["professions"]
    assert "Koschbauer" in kosch_profane["professions"]
    assert "Hafenwache" in perricum_kaempfer["professions"]
    assert preview_map["mittelreich_perricum"]["alle"]["themes"] == [
        {
            "id": "graumagier_aus_perricum",
            "label": "Graumagier aus Perricum",
            "description": "Regionale Themenschablone für gildenmagische Figuren aus Perricum.",
        }
    ]
    assert preview_map["mittelreich_perricum"]["kaempfer"]["themes"] == []
