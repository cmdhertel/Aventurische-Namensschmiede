"""Tests für Pydantic-Modelle und Enums (models.py)."""

from __future__ import annotations

import pytest

from namegen.models import (
    CharacterConfig,
    CharacterResult,
    CharacterTraits,
    Gender,
    GenerationMode,
    NameComponents,
    NameResult,
    NameSchema,
    NameSchemaType,
    PhysicalTraits,
    RegionData,
    RegionMeta,
    SpeciesStats,
)


def test_gender_values() -> None:
    assert Gender.MALE == "male"
    assert Gender.FEMALE == "female"
    assert Gender.ANY == "any"


def test_generation_mode_values() -> None:
    assert GenerationMode.SIMPLE == "simple"
    assert GenerationMode.COMPOSE == "compose"


def test_region_meta_valid() -> None:
    meta = RegionMeta(region="Testland", abbreviation="TST")
    assert meta.region == "Testland"
    assert meta.abbreviation == "TST"
    assert meta.language == "de"
    assert meta.notes == ""


def test_region_meta_abbreviation_too_short() -> None:
    with pytest.raises(Exception):
        RegionMeta(region="X", abbreviation="AB")


def test_name_schema_defaults() -> None:
    schema = NameSchema()
    assert schema.type == NameSchemaType.GIVEN_FAMILY
    assert schema.male_patronym_pattern == "{parent}son"


def test_name_result_build_with_connector() -> None:
    result = NameResult.build(
        first="Ardare",
        last="Casibelli",
        gender=Gender.FEMALE,
        region="Horasreich",
        mode=GenerationMode.SIMPLE,
        connector="dy",
        culture="Horasier",
        species="Mensch",
        name_schema=NameSchemaType.GIVEN_FAMILY_CONNECTOR,
    )
    assert result.full_name == "Ardare dy Casibelli"
    assert result.culture == "Horasier"
    assert result.species == "Mensch"


def test_name_result_build_with_components() -> None:
    components = NameComponents(first_prefix="Kos", first_suffix="ch")
    result = NameResult.build(
        first="Kosch",
        last=None,
        gender=Gender.ANY,
        region="Kosch",
        mode=GenerationMode.COMPOSE,
        components=components,
    )
    assert result.components is not None
    assert result.components.first_prefix == "Kos"


def test_character_result_exposes_context_properties() -> None:
    name = NameResult.build(
        first="Balrik",
        last="Sohn des Angrax",
        gender=Gender.MALE,
        region="Ambosszwerge",
        mode=GenerationMode.SIMPLE,
        culture="Ambosszwerge",
        species="Zwerg",
    )
    result = CharacterResult(
        name=name,
        age=78,
        profession="Schmied",
        language="Rogolan",
        script="Angram",
        social_status="Frei",
        species_stats=SpeciesStats(speed=6),
        traits=CharacterTraits(
            physical=PhysicalTraits(hair="schwarz", eyes="grau", build="kräftig"),
            personality="stur",
            motivation="Ruhm",
            quirk="prüft Steine",
        ),
    )
    assert result.full_name == "Balrik Sohn des Angrax"
    assert result.culture == "Ambosszwerge"
    assert result.species == "Zwerg"
    assert result.species_stats is not None
    assert result.species_stats.speed == 6


def test_region_data_defaults() -> None:
    data = RegionData(meta=RegionMeta(region="Minimal", abbreviation="MIN"))
    assert data.simple.first.male == []
    assert data.character.professions == []


def test_character_config_default_empty() -> None:
    cfg = CharacterConfig()
    assert cfg.languages == []
