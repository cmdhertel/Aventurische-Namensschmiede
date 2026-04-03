"""Tests für den Data-Loader (loader.py)."""

from __future__ import annotations

import pytest

from namegen.loader import LoaderError, list_regions, load_region


# ── list_regions ──────────────────────────────────────────────────────────────

def test_list_regions_returns_nonempty_list() -> None:
    regions = list_regions()
    assert isinstance(regions, list)
    assert len(regions) > 0


def test_list_regions_is_sorted() -> None:
    regions = list_regions()
    assert regions == sorted(regions)


def test_list_regions_contains_known_regions() -> None:
    regions = list_regions()
    for expected in ("mittelreich_kosch", "horasreich", "bornland", "aranien"):
        assert expected in regions, f"Erwartete Region '{expected}' nicht gefunden"


def test_list_regions_contains_only_strings() -> None:
    for r in list_regions():
        assert isinstance(r, str)
        assert len(r) > 0


# ── load_region ───────────────────────────────────────────────────────────────

def test_load_region_returns_region_data() -> None:
    from namegen.models import RegionData
    data = load_region("mittelreich_kosch")
    assert isinstance(data, RegionData)


def test_load_region_meta_fields() -> None:
    data = load_region("mittelreich_kosch")
    assert data.meta.region == "Kosch"
    assert data.meta.abbreviation == "KOS"
    assert len(data.meta.abbreviation) == 3


def test_load_region_case_insensitive() -> None:
    lower = load_region("bornland")
    upper = load_region("BORNLAND")
    assert lower.meta.region == upper.meta.region


def test_load_region_unknown_raises_loader_error() -> None:
    with pytest.raises(LoaderError):
        load_region("does_not_exist_xyz")


def test_load_region_all_known_regions_load_without_error() -> None:
    for region_id in list_regions():
        data = load_region(region_id)
        assert data.meta.region, f"Region '{region_id}' hat keinen Anzeigenamen"
        assert len(data.meta.abbreviation) == 3


def test_load_region_notes_is_string() -> None:
    for region_id in list_regions():
        data = load_region(region_id)
        assert isinstance(data.meta.notes, str)


# ── TOML-Schema: Felder sind optional und haben sinnvolle Defaults ─────────────

def test_region_simple_pools_are_lists() -> None:
    data = load_region("mittelreich_kosch")
    assert isinstance(data.simple.first.male, list)
    assert isinstance(data.simple.first.female, list)
    assert isinstance(data.simple.first.neutral, list)
    assert isinstance(data.simple.last.neutral, list)


def test_region_compose_infix_probability_in_range() -> None:
    for region_id in list_regions():
        data = load_region(region_id)
        assert 0.0 <= data.compose.first.infix_probability <= 1.0
        assert 0.0 <= data.compose.last.infix_probability <= 1.0


def test_region_character_professions_is_list() -> None:
    for region_id in list_regions():
        data = load_region(region_id)
        assert isinstance(data.character.professions, list)


def test_regions_with_character_professions_have_nonempty_list() -> None:
    """Regionen denen explizit Berufe zugewiesen wurden, sollen welche haben."""
    for region_id in ("mittelreich_kosch", "horasreich", "mittelreich", "aranien", "bornland"):
        data = load_region(region_id)
        assert len(data.character.professions) > 0, (
            f"Region '{region_id}' sollte regionsspezifische Berufe haben"
        )
