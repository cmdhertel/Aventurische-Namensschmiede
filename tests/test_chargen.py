"""Tests für die Charakter-Generierung (chargen.py)."""

from __future__ import annotations

import random
import statistics

import pytest

from namegen.chargen import _generate_age, _load_professions_by_category, generate_character
from namegen.models import (
    CharacterResult,
    Gender,
    GenerationMode,
    ProfessionCategory,
)


RNG_BASE = 42


# ── CharacterResult: Grundstruktur ────────────────────────────────────────────

def test_generate_character_returns_character_result() -> None:
    result = generate_character("mittelreich_kosch", rng=random.Random(1))
    assert isinstance(result, CharacterResult)


def test_generate_character_has_name() -> None:
    result = generate_character("mittelreich_kosch", rng=random.Random(1))
    assert result.full_name
    assert result.name.first_name


def test_generate_character_has_profession() -> None:
    result = generate_character("mittelreich_kosch", rng=random.Random(1))
    assert isinstance(result.profession, str)
    assert len(result.profession) > 0


def test_generate_character_has_all_traits() -> None:
    result = generate_character("mittelreich_kosch", rng=random.Random(1))
    t = result.traits
    assert t.physical.hair
    assert t.physical.eyes
    assert t.physical.build
    assert t.personality
    assert t.motivation
    assert t.quirk


def test_generate_character_properties() -> None:
    result = generate_character("mittelreich_kosch", gender=Gender.MALE, rng=random.Random(1))
    assert result.full_name == result.name.full_name
    assert result.gender == result.name.gender
    assert result.region == result.name.region


# ── Determinismus ─────────────────────────────────────────────────────────────

def test_generate_character_same_seed_deterministic() -> None:
    r1 = generate_character("mittelreich_kosch", rng=random.Random(99))
    r2 = generate_character("mittelreich_kosch", rng=random.Random(99))
    assert r1.full_name      == r2.full_name
    assert r1.age            == r2.age
    assert r1.profession     == r2.profession
    assert r1.traits.quirk   == r2.traits.quirk


# ── Altersverteilung ──────────────────────────────────────────────────────────

def test_age_always_in_valid_range() -> None:
    for i in range(500):
        age = _generate_age(random.Random(i))
        assert 18 <= age <= 80, f"Alter {age} außerhalb 18–80"


def test_age_under_70_more_frequent_than_over() -> None:
    """Statistischer Test: >85% der Altersangaben sollten unter 70 liegen."""
    ages = [_generate_age(random.Random(i)) for i in range(1000)]
    under_70 = sum(1 for a in ages if a <= 70)
    ratio = under_70 / len(ages)
    assert ratio > 0.85, f"Nur {ratio:.1%} der Altersangaben unter 70 (erwartet >85%)"


def test_age_70_plus_decreasing_frequency() -> None:
    """Höhere Altersgruppen sollen seltener vorkommen."""
    ages = [_generate_age(random.Random(i)) for i in range(5000)]
    count_71_74 = sum(1 for a in ages if 71 <= a <= 74)
    count_77_80 = sum(1 for a in ages if 77 <= a <= 80)
    assert count_71_74 > count_77_80, (
        f"71–74 ({count_71_74}×) sollte häufiger sein als 77–80 ({count_77_80}×)"
    )


def test_age_median_in_reasonable_range() -> None:
    ages = [_generate_age(random.Random(i)) for i in range(1000)]
    med = statistics.median(ages)
    assert 25 <= med <= 50, f"Medianalter {med} außerhalb des erwarteten Bereichs 25–50"


# ── Berufskategorien ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("category", list(ProfessionCategory))
def test_profession_category_returns_nonempty_list(category: ProfessionCategory) -> None:
    professions = _load_professions_by_category(category)
    assert len(professions) > 0, f"Kategorie '{category}' hat keine Berufe"


@pytest.mark.parametrize("category", list(ProfessionCategory))
def test_generate_character_all_categories(category: ProfessionCategory) -> None:
    result = generate_character(
        "mittelreich_kosch",
        profession_category=category,
        rng=random.Random(7),
    )
    assert result.profession


def test_profession_category_geweihte_contains_only_geweihte() -> None:
    profs = _load_professions_by_category(ProfessionCategory.GEWEIHTE)
    # Stichproben aus der Geweihten-Liste
    for expected in ("Borongeweihter", "Praiosgeweihte", "Tsageweihte"):
        assert expected in profs


def test_profession_category_zauberer_contains_only_zauberer() -> None:
    profs = _load_professions_by_category(ProfessionCategory.ZAUBERER)
    for expected in ("Gildenmagier", "Hexen", "Druiden"):
        assert expected in profs
    # Kämpfer dürfen nicht enthalten sein
    assert "Söldner" not in profs


def test_profession_category_kaempfer_excludes_geweihte() -> None:
    kaempfer = _load_professions_by_category(ProfessionCategory.KAEMPFER)
    geweihte = _load_professions_by_category(ProfessionCategory.GEWEIHTE)
    overlap = set(kaempfer) & set(geweihte)
    # Ausnahme: "Säbeltänzerin" ist in beiden (Ordensleute & Geweihte)
    overlap -= {"Säbeltänzerin"}
    assert not overlap, f"Unerwartete Überschneidung: {overlap}"


def test_profession_category_all_is_superset_of_others() -> None:
    all_profs = set(_load_professions_by_category(ProfessionCategory.ALL))
    for category in (ProfessionCategory.GEWEIHTE, ProfessionCategory.ZAUBERER,
                     ProfessionCategory.KAEMPFER, ProfessionCategory.PROFAN):
        cat_profs = set(_load_professions_by_category(category))
        assert cat_profs.issubset(all_profs), (
            f"Kategorie '{category}' enthält Berufe, die nicht in 'alle' sind"
        )


def test_profession_all_includes_regional_professions_in_pool() -> None:
    """Regionale Berufe sollen für category=alle berücksichtigt werden."""
    from namegen.loader import load_region
    regional = load_region("mittelreich_kosch").character.professions
    assert regional, "Kosch sollte regionale Berufe haben"
    # Mit genug Samples muss mindestens ein regionaler Beruf gewürfelt werden
    professions = {
        generate_character("mittelreich_kosch", profession_category=ProfessionCategory.ALL,
                           rng=random.Random(i)).profession
        for i in range(200)
    }
    assert professions & set(regional), "Kein regionaler Beruf in 200 Versuchen – unwahrscheinlich"


def test_profession_non_all_category_ignores_regional() -> None:
    """Kategorie-spezifische Auswahl soll KEINE regionalen Berufe enthalten."""
    from namegen.loader import load_region
    regional = set(load_region("mittelreich_kosch").character.professions)
    geweihte_pool = set(_load_professions_by_category(ProfessionCategory.GEWEIHTE))
    # Regionale Kosch-Berufe wie "Bergmann" dürfen nicht in Geweihte sein
    assert not (regional & geweihte_pool), (
        f"Regionale Berufe dürfen nicht in Geweihte-Pool: {regional & geweihte_pool}"
    )


# ── Alle Regionen ─────────────────────────────────────────────────────────────

def test_all_regions_generate_character() -> None:
    from namegen.loader import list_regions
    for region_id in list_regions():
        result = generate_character(region_id, rng=random.Random(3))
        assert result.full_name
        assert result.profession
        assert 18 <= result.age <= 80
