"""Tests für Pydantic-Modelle und Enums (models.py)."""

from __future__ import annotations

import pytest

from namegen.models import (
    CharacterConfig,
    CharacterResult,
    CharacterTraits,
    ExperienceLevel,
    Gender,
    GenerationMode,
    NameComponents,
    NameResult,
    PhysicalTraits,
    ProfessionCategory,
    RegionData,
    RegionMeta,
)

# ── Enum-Werte ────────────────────────────────────────────────────────────────

def test_gender_values() -> None:
    assert Gender.MALE   == "male"
    assert Gender.FEMALE == "female"
    assert Gender.ANY    == "any"


def test_generation_mode_values() -> None:
    assert GenerationMode.SIMPLE  == "simple"
    assert GenerationMode.COMPOSE == "compose"


def test_profession_category_values() -> None:
    assert ProfessionCategory.ALL      == "alle"
    assert ProfessionCategory.GEWEIHTE == "geweihte"
    assert ProfessionCategory.ZAUBERER == "zauberer"
    assert ProfessionCategory.KAEMPFER == "kaempfer"
    assert ProfessionCategory.PROFAN   == "profan"
    assert len(ProfessionCategory) == 5


def test_experience_level_values() -> None:
    assert ExperienceLevel.LEHRLING == "lehrling"
    assert ExperienceLevel.GESELLE == "geselle"
    assert ExperienceLevel.MEISTER == "meister"
    assert ExperienceLevel.VETERAN == "veteran"


def test_enums_are_string_comparable() -> None:
    assert Gender.MALE == "male"
    assert ProfessionCategory.ALL == "alle"
    assert GenerationMode.SIMPLE == "simple"


# ── RegionMeta Validierung ────────────────────────────────────────────────────

def test_region_meta_valid() -> None:
    meta = RegionMeta(region="Testland", abbreviation="TST")
    assert meta.region == "Testland"
    assert meta.abbreviation == "TST"
    assert meta.language == "de"  # Default
    assert meta.notes == ""       # Default


def test_region_meta_abbreviation_too_short() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        RegionMeta(region="X", abbreviation="AB")


def test_region_meta_abbreviation_too_long() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        RegionMeta(region="X", abbreviation="ABCD")


# ── NameResult.build ──────────────────────────────────────────────────────────

def test_name_result_build_with_last_name() -> None:
    r = NameResult.build(
        first="Adalhard", last="Kessler",
        gender=Gender.MALE, region="Kosch", mode=GenerationMode.SIMPLE,
    )
    assert r.full_name == "Adalhard Kessler"
    assert r.first_name == "Adalhard"
    assert r.last_name == "Kessler"
    assert r.resolved_gender == Gender.MALE  # defaults to gender when not provided


def test_name_result_build_without_last_name() -> None:
    r = NameResult.build(
        first="Itta", last=None,
        gender=Gender.FEMALE, region="Kosch", mode=GenerationMode.SIMPLE,
    )
    assert r.full_name == "Itta"
    assert r.last_name is None


def test_name_result_build_resolved_gender_override() -> None:
    r = NameResult.build(
        first="Pat", last=None,
        gender=Gender.ANY, region="Kosch", mode=GenerationMode.SIMPLE,
        resolved_gender=Gender.MALE,
    )
    assert r.gender == Gender.ANY
    assert r.resolved_gender == Gender.MALE


def test_name_result_build_with_components() -> None:
    components = NameComponents(
        first_prefix="Kos", first_infix=None, first_suffix="ch",
    )
    r = NameResult.build(
        first="Kosch", last=None,
        gender=Gender.ANY, region="X", mode=GenerationMode.COMPOSE,
        components=components,
    )
    assert r.components is not None
    assert r.components.first_prefix == "Kos"
    assert r.components.first_suffix == "ch"
    assert r.components.first_infix is None


# ── CharacterResult Properties ────────────────────────────────────────────────

def _make_character_result() -> CharacterResult:
    name = NameResult.build(
        first="Adalhard", last="Kessler",
        gender=Gender.MALE, region="Kosch", mode=GenerationMode.SIMPLE,
    )
    return CharacterResult(
        name=name,
        experience=ExperienceLevel.MEISTER,
        age=35,
        profession="Söldner",
        traits=CharacterTraits(
            physical=PhysicalTraits(hair="schwarz", eyes="blau", build="kräftig"),
            personality="mutig",
            motivation="Ruhm suchen",
            quirk="pfeift beim Denken",
        ),
    )


def test_character_result_full_name_property() -> None:
    cr = _make_character_result()
    assert cr.full_name == "Adalhard Kessler"


def test_character_result_gender_property() -> None:
    cr = _make_character_result()
    assert cr.gender == Gender.MALE


def test_character_result_region_property() -> None:
    cr = _make_character_result()
    assert cr.region == "Kosch"


def test_character_result_age_and_profession() -> None:
    cr = _make_character_result()
    assert cr.experience == ExperienceLevel.MEISTER
    assert cr.age == 35
    assert cr.profession == "Söldner"


def test_character_result_traits() -> None:
    cr = _make_character_result()
    assert cr.traits.physical.hair == "schwarz"
    assert cr.traits.physical.eyes == "blau"
    assert cr.traits.personality == "mutig"
    assert cr.traits.quirk == "pfeift beim Denken"


# ── RegionData Defaults ───────────────────────────────────────────────────────

def test_region_data_all_sections_default_to_empty() -> None:
    meta = RegionMeta(region="Minimal", abbreviation="MIN")
    data = RegionData(meta=meta)
    assert data.simple.first.male == []
    assert data.simple.last.neutral == []
    assert data.character.professions == []
    assert data.compose.first.infix_probability == 0.3


def test_character_config_default_empty() -> None:
    cfg = CharacterConfig()
    assert cfg.professions == []
