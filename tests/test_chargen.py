"""Tests für die Charakter-Generierung (chargen.py)."""

from __future__ import annotations

import random

import pytest

from namegen.chargen import _generate_age, _load_professions_by_category, generate_character
from namegen.loader import load_region
from namegen.models import CharacterResult, ProfessionCategory


def test_generate_character_returns_character_result() -> None:
    result = generate_character("mittelreich_kosch", rng=random.Random(1))
    assert isinstance(result, CharacterResult)


def test_generate_character_has_context() -> None:
    result = generate_character("ambosszwerge", rng=random.Random(1))
    assert result.species == "Zwerg"
    assert result.culture == "Ambosszwerge"
    assert result.language == "Rogolan"
    assert result.species_stats is not None


def test_generate_character_has_traits_and_profession() -> None:
    result = generate_character("thorwal", rng=random.Random(1))
    assert result.profession
    assert result.traits.personality
    assert result.traits.quirk


def test_generate_character_same_seed_deterministic() -> None:
    r1 = generate_character("mittelreich_kosch", rng=random.Random(99))
    r2 = generate_character("mittelreich_kosch", rng=random.Random(99))
    assert r1.full_name == r2.full_name
    assert r1.age == r2.age
    assert r1.profession == r2.profession


def test_generate_age_human_range() -> None:
    data = load_region("mittelreich_kosch")
    for i in range(100):
        age = _generate_age(data, random.Random(i))
        assert 18 <= age <= 80


def test_generate_age_dwarf_range() -> None:
    data = load_region("ambosszwerge")
    for i in range(100):
        age = _generate_age(data, random.Random(i))
        assert 30 <= age <= 220


@pytest.mark.parametrize("category", list(ProfessionCategory))
def test_profession_category_returns_nonempty_list(category: ProfessionCategory) -> None:
    assert _load_professions_by_category(category)


def test_profession_all_includes_origin_professions() -> None:
    regional = set(load_region("mittelreich_kosch").character.professions)
    professions = {
        generate_character("mittelreich_kosch", profession_category=ProfessionCategory.ALL, rng=random.Random(i)).profession
        for i in range(200)
    }
    assert professions & regional


def test_profession_non_all_category_ignores_origin_professions() -> None:
    regional = set(load_region("mittelreich_kosch").character.professions)
    geweihte_pool = set(_load_professions_by_category(ProfessionCategory.GEWEIHTE))
    assert not (regional & geweihte_pool)


def test_all_regions_generate_character() -> None:
    from namegen.loader import list_regions

    for region_id in list_regions():
        result = generate_character(region_id, rng=random.Random(3))
        assert result.full_name
        assert result.profession
