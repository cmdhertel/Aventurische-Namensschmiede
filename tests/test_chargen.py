"""Tests für die Charakter-Generierung (chargen.py)."""

from __future__ import annotations

import random
import statistics

import pytest

from namegen.chargen import (
    _generate_age,
    _load_professions_by_category,
    _resolve_profession_pool,
    generate_character,
    get_profession_preview_for_selection,
    get_profession_themes,
    get_profession_themes_for_selection,
)
from namegen.loader import load_region
from namegen.models import (
    CharacterResult,
    ExperienceLevel,
    Gender,
    ProfessionCategory,
)

RNG_BASE = 42


# ── CharacterResult: Grundstruktur ────────────────────────────────────────────


def test_generate_character_returns_character_result() -> None:
    result = generate_character("mittelreich_kosch", rng=random.Random(1))
    assert isinstance(result, CharacterResult)


def test_generate_character_has_context() -> None:
    result = generate_character("ambosszwerge", rng=random.Random(1))
    assert result.species == "Zwerg"
    assert result.culture == "Ambosszwerge"
    assert result.language == "Rogolan"
    assert result.species_stats is not None


def test_generate_character_human_aggregate_uses_concrete_region_context() -> None:
    result = generate_character("human", rng=random.Random(5))
    assert result.species == "Mensch"
    assert result.name.origin_id is not None
    assert result.name.origin_id != "human"


def test_generate_character_mittelreicher_aggregate_uses_subregion_context() -> None:
    result = generate_character("mittelreicher", rng=random.Random(8))
    assert result.culture == "Mittelreicher"
    assert result.region != "Mittelreicher"


def test_generate_character_has_traits_and_profession() -> None:
    result = generate_character("thorwal", rng=random.Random(1))
    assert result.profession
    assert result.traits.personality
    assert result.traits.quirk


def test_generate_character_has_experience() -> None:
    result = generate_character("mittelreich_kosch", rng=random.Random(1))
    assert result.experience == ExperienceLevel.GESELLE


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
    assert r1.full_name == r2.full_name
    assert r1.experience == r2.experience
    assert r1.age == r2.age
    assert r1.profession == r2.profession
    assert r1.traits.quirk == r2.traits.quirk


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


def test_age_median_human_is_in_expected_range() -> None:
    data = load_region("mittelreich_kosch")
    ages = [_generate_age(data, random.Random(i)) for i in range(1000)]
    med = statistics.median(ages)
    assert 18 <= med <= 70, f"Medianalter {med} außerhalb des erwarteten Bereichs 18–70"


# ── Berufskategorien ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("category", list(ProfessionCategory))
def test_profession_category_returns_nonempty_list(category: ProfessionCategory) -> None:
    assert _load_professions_by_category(category)


def test_profession_all_includes_origin_professions() -> None:
    regional = set(load_region("mittelreich_kosch").character.professions)
    professions = {
        generate_character(
            "mittelreich_kosch",
            profession_category=ProfessionCategory.ALL,
            rng=random.Random(i),
        ).profession
        for i in range(200)
    }
    assert professions & regional


@pytest.mark.parametrize("category", list(ProfessionCategory))
def test_generate_character_all_categories(category: ProfessionCategory) -> None:
    result = generate_character(
        "mittelreich_kosch",
        profession_category=category,
        rng=random.Random(7),
    )
    assert result.profession


@pytest.mark.parametrize(
    ("experience", "minimum", "maximum"),
    [
        (ExperienceLevel.LEHRLING, 10, 16),
        (ExperienceLevel.GESELLE, 17, 25),
        (ExperienceLevel.MEISTER, 26, 45),
        (ExperienceLevel.VETERAN, 46, 80),
    ],
)
def test_generate_character_respects_experience_range(
    experience: ExperienceLevel,
    minimum: int,
    maximum: int,
) -> None:
    result = generate_character("mittelreich_kosch", experience=experience, rng=random.Random(11))
    assert result.experience == experience
    assert minimum <= result.age <= maximum


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
    for category in (
        ProfessionCategory.GEWEIHTE,
        ProfessionCategory.ZAUBERER,
        ProfessionCategory.KAEMPFER,
        ProfessionCategory.PROFAN,
    ):
        cat_profs = set(_load_professions_by_category(category))
        assert cat_profs.issubset(all_profs), (
            f"Kategorie '{category}' enthält Berufe, die nicht in 'alle' sind"
        )


def test_profession_all_includes_regional_professions_in_pool() -> None:
    """Regionale Berufe sollen für category=alle berücksichtigt werden."""
    regional = set(load_region("mittelreich_kosch").character.professions)
    assert regional, "Kosch sollte regionale Berufe haben"
    pool = {
        name
        for name, _weight in _resolve_profession_pool(
            load_region("mittelreich_kosch"), ProfessionCategory.ALL, None
        )
    }
    assert pool & regional


def test_profession_non_all_category_includes_matching_regional_professions() -> None:
    """Regionale Berufe sollen auch für passende Unterkategorien gelten."""
    regional = set(load_region("mittelreich_kosch").character.professions)
    pool = {
        name
        for name, _weight in _resolve_profession_pool(
            load_region("mittelreich_kosch"), ProfessionCategory.PROFAN, None
        )
    }
    assert pool & regional


def test_profession_category_filters_out_non_matching_regional_professions() -> None:
    pool = {
        name
        for name, _weight in _resolve_profession_pool(
            load_region("mittelreich_kosch"), ProfessionCategory.GEWEIHTE, None
        )
    }
    assert "Koschbauer" not in pool
    assert "Erzschmelzer" not in pool


def test_profession_theme_catalog_exposes_stable_theme_ids() -> None:
    themes = {theme.id: theme.label for theme in get_profession_themes()}
    assert themes["graumagier_aus_perricum"] == "Graumagier aus Perricum"
    assert themes["bannstrahler"] == "Bannstrahler"
    assert themes["ardarit"] == "Ardarit"


def test_profession_themes_for_selection_only_returns_matching_region_themes() -> None:
    perricum_themes = {
        theme.id for theme in get_profession_themes_for_selection("mittelreich_perricum")
    }
    kosch_themes = {theme.id for theme in get_profession_themes_for_selection("mittelreich_kosch")}

    assert "graumagier_aus_perricum" in perricum_themes
    assert "graumagier_aus_perricum" not in kosch_themes


def test_audit_moved_professions_are_no_longer_global() -> None:
    geweihte = _load_professions_by_category(ProfessionCategory.GEWEIHTE)
    kaempfer = _load_professions_by_category(ProfessionCategory.KAEMPFER)

    assert "Bannstrahler" not in geweihte
    assert "Ardarit" not in geweihte
    assert "Amazone" not in kaempfer


def test_audit_themes_show_up_only_in_matching_regions() -> None:
    horasreich_themes = {theme.id for theme in get_profession_themes_for_selection("horasreich")}
    mittelreich_themes = {theme.id for theme in get_profession_themes_for_selection("mittelreich")}

    assert "ardarit" in horasreich_themes
    assert "rosenritter" in horasreich_themes
    assert "bannstrahler" in mittelreich_themes
    assert "ardarit" not in mittelreich_themes


def test_profession_themes_for_selection_respect_category_filter() -> None:
    perricum_kaempfer = {
        theme.id
        for theme in get_profession_themes_for_selection(
            "mittelreich_perricum", category=ProfessionCategory.KAEMPFER
        )
    }

    assert perricum_kaempfer == set()


def test_profession_theme_filters_to_structured_regional_entry() -> None:
    result = generate_character(
        "mittelreich_perricum",
        profession_category=ProfessionCategory.ZAUBERER,
        profession_theme="graumagier_aus_perricum",
        rng=random.Random(13),
    )
    assert result.profession == "Graumagier aus Perricum"


def test_profession_preview_for_region_includes_regional_professions() -> None:
    preview = get_profession_preview_for_selection("mittelreich_garetien")
    profane = next(group for group in preview.groups if group.id == ProfessionCategory.PROFAN.value)

    assert "Kaufmann" in profane.professions
    assert "Gerstenbauer" not in profane.professions


def test_profession_preview_for_region_includes_matching_themes_only() -> None:
    preview = get_profession_preview_for_selection("mittelreich_perricum")

    assert [theme.id for theme in preview.themes] == ["graumagier_aus_perricum"]


def test_profession_preview_for_aggregate_merges_subregion_professions() -> None:
    preview = get_profession_preview_for_selection("mittelreicher")
    profane = next(group for group in preview.groups if group.id == ProfessionCategory.PROFAN.value)

    assert "Koschbauer" in profane.professions
    assert "Kaufmann" in profane.professions


def test_profession_pool_deduplicates_general_and_regional_matches() -> None:
    pool = dict(
        _resolve_profession_pool(
            load_region("mittelreich_weiden"), ProfessionCategory.KAEMPFER, None
        )
    )
    assert "Ritter" in pool
    assert pool["Ritter"] > 1


# ── Alle Regionen ─────────────────────────────────────────────────────────────


def test_all_regions_generate_character() -> None:
    from namegen.loader import list_regions

    for region_id in list_regions():
        result = generate_character(region_id, rng=random.Random(3))
        assert result.full_name
        assert result.profession
        assert 17 <= result.age <= 25
