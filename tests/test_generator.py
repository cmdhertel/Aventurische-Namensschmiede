"""Tests für die Namens-Generierung (generator.py)."""

from __future__ import annotations

import random

import pytest

from namegen.generator import generate
from namegen.models import Gender, GenerationMode, NameResult, NameSchemaType


def test_generate_simple_returns_name_result() -> None:
    result = generate("mittelreich_kosch", rng=random.Random(1))
    assert isinstance(result, NameResult)


def test_generate_simple_has_nonempty_names() -> None:
    result = generate("mittelreich_kosch", rng=random.Random(1))
    assert result.first_name
    assert result.full_name
    assert result.species == "Mensch"
    assert result.culture == "Mittelreicher"


def test_generate_compose_has_components() -> None:
    result = generate("mittelreich_kosch", mode=GenerationMode.COMPOSE, rng=random.Random(1))
    assert result.components is not None
    assert result.components.first_prefix
    assert result.components.first_suffix


def test_generate_same_seed_produces_same_result() -> None:
    r1 = generate("mittelreich_kosch", rng=random.Random(99))
    r2 = generate("mittelreich_kosch", rng=random.Random(99))
    assert r1.full_name == r2.full_name


def test_generate_different_seeds_likely_differ() -> None:
    names = {generate("mittelreich_kosch", rng=random.Random(i)).full_name for i in range(20)}
    assert len(names) > 1


def test_generate_male_resolved_gender_not_female() -> None:
    results = [generate("mittelreich_kosch", gender=Gender.MALE, rng=random.Random(i)) for i in range(20)]
    assert all(r.resolved_gender != Gender.FEMALE for r in results)


def test_generate_horasier_uses_connector_schema() -> None:
    result = generate("horasreich", rng=random.Random(1))
    assert result.name_schema == NameSchemaType.GIVEN_FAMILY_CONNECTOR


def test_generate_thorwaler_patronym() -> None:
    result = generate("thorwal", rng=random.Random(1))
    assert result.name_schema == NameSchemaType.GIVEN_PATRONYM
    assert result.last_name is not None
    assert result.full_name.endswith(result.last_name)


def test_generate_ctki_ssrr_byname() -> None:
    result = generate("ctki_ssrr", rng=random.Random(1))
    assert result.name_schema == NameSchemaType.GIVEN_BYNAME
    assert result.last_name is not None


def test_generate_all_regions_simple_any() -> None:
    from namegen.loader import list_regions

    for region_id in list_regions():
        result = generate(region_id, mode=GenerationMode.SIMPLE, gender=Gender.ANY, rng=random.Random(7))
        assert result.first_name
        assert result.full_name


def test_full_name_without_last_name() -> None:
    result = NameResult.build(
        first="Adalhard",
        last=None,
        gender=Gender.MALE,
        region="Test",
        mode=GenerationMode.SIMPLE,
    )
    assert result.full_name == "Adalhard"


def test_generate_unknown_region_raises_loader_error() -> None:
    from namegen.loader import LoaderError

    with pytest.raises(LoaderError):
        generate("region_which_does_not_exist")
