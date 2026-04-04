"""Tests für den Data-Loader (loader.py)."""

from __future__ import annotations

import pytest

from namegen.loader import (
    LoaderError,
    get_origin_catalog,
    list_cultures,
    list_regions,
    list_species,
    load_culture,
    load_region,
    load_species,
)


def test_list_regions_returns_nonempty_list() -> None:
    assert list_regions()


def test_list_species_contains_core_entries() -> None:
    species = list_species()
    for expected in ("human", "elf", "dwarf", "achaz"):
        assert expected in species


def test_list_cultures_contains_core_entries() -> None:
    cultures = list_cultures()
    for expected in ("mittelreicher", "horasier", "thorwaler", "ctki_ssrr"):
        assert expected in cultures


def test_load_species_human() -> None:
    data = load_species("human")
    assert data.meta.name == "Mensch"
    assert data.stats.speed == 8


def test_load_culture_thorwaler_has_patronym_schema() -> None:
    culture = load_culture("thorwaler")
    assert culture.naming_schema.type == "given_patronym"


def test_load_region_resolves_species_and_culture() -> None:
    data = load_region("mittelreich_kosch")
    assert data.meta.region == "Kosch"
    assert data.origin.species_id == "human"
    assert data.origin.culture_id == "mittelreicher"
    assert data.species is not None
    assert data.culture is not None


def test_load_region_combines_culture_and_origin_professions() -> None:
    data = load_region("mittelreich_kosch")
    assert "Bergmann" in data.character.professions
    assert "Bauer" in data.character.professions


def test_load_region_new_nonhuman_origin() -> None:
    data = load_region("ambosszwerge")
    assert data.species is not None
    assert data.species.meta.name == "Zwerg"
    assert data.culture is not None
    assert data.culture.meta.name == "Ambosszwerge"


def test_load_region_unknown_raises_loader_error() -> None:
    with pytest.raises(LoaderError):
        load_region("does_not_exist_xyz")


def test_catalog_contains_selection_metadata() -> None:
    entry = next(item for item in get_origin_catalog() if item["id"] == "mittelreich_kosch")
    assert entry["species_name"] == "Mensch"
    assert entry["culture_name"] == "Mittelreicher"
