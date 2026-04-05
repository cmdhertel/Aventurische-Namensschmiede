"""Tests für die Namens-Generierung (generator.py)."""

from __future__ import annotations

import random

import pytest

from namegen.generator import generate
from namegen.models import Gender, GenerationMode, NameResult, NameSchemaType

RNG = random.Random(42)


# ── Grundlegende Ausgabe ──────────────────────────────────────────────────────


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


def test_generate_simple_has_no_components() -> None:
    result = generate("mittelreich_kosch", mode=GenerationMode.SIMPLE, rng=random.Random(1))
    assert result.components is None


# ── Determinismus ─────────────────────────────────────────────────────────────


def test_generate_same_seed_produces_same_result() -> None:
    r1 = generate("mittelreich_kosch", rng=random.Random(99))
    r2 = generate("mittelreich_kosch", rng=random.Random(99))
    assert r1.full_name == r2.full_name


def test_generate_different_seeds_likely_differ() -> None:
    names = {generate("mittelreich_kosch", rng=random.Random(i)).full_name for i in range(20)}
    assert len(names) > 1


def test_generate_male_resolved_gender_not_female() -> None:
    results = [
        generate("mittelreich_kosch", gender=Gender.MALE, rng=random.Random(i)) for i in range(20)
    ]
    assert all(r.resolved_gender != Gender.FEMALE for r in results)


def test_generate_horasier_uses_connector_schema() -> None:
    result = generate("horasreich", rng=random.Random(1))
    assert result.name_schema == NameSchemaType.GIVEN_FAMILY_CONNECTOR


# ── Geschlecht ────────────────────────────────────────────────────────────────


def test_generate_male_gender_field() -> None:
    result = generate("mittelreich_kosch", gender=Gender.MALE, rng=random.Random(1))
    assert result.gender == Gender.MALE


def test_generate_female_gender_field() -> None:
    result = generate("mittelreich_kosch", gender=Gender.FEMALE, rng=random.Random(1))
    assert result.gender == Gender.FEMALE


def test_generate_any_gender_field() -> None:
    result = generate("mittelreich_kosch", gender=Gender.ANY, rng=random.Random(1))
    assert result.gender == Gender.ANY


def test_generate_male_resolved_gender_not_female_extended() -> None:
    """Männliche Vornamensanfrage soll keine weiblichen Namen liefern."""
    results = [
        generate("mittelreich_kosch", gender=Gender.MALE, rng=random.Random(i)) for i in range(30)
    ]
    for r in results:
        assert r.resolved_gender != Gender.FEMALE


def test_generate_female_resolved_gender_not_male() -> None:
    results = [
        generate("mittelreich_kosch", gender=Gender.FEMALE, rng=random.Random(i)) for i in range(30)
    ]
    for r in results:
        assert r.resolved_gender != Gender.MALE


def test_generate_thorwaler_patronym() -> None:
    result = generate("thorwal", rng=random.Random(1))
    assert result.name_schema == NameSchemaType.GIVEN_PATRONYM
    assert result.last_name is not None
    assert result.full_name.endswith(result.last_name)


def test_generate_ctki_ssrr_byname() -> None:
    result = generate("ctki_ssrr", rng=random.Random(1))
    assert result.name_schema == NameSchemaType.GIVEN_BYNAME
    assert result.last_name is not None


def test_all_regions_generate_simple_any() -> None:
    from namegen.loader import list_regions

    for region_id in list_regions():
        result = generate(
            region_id, mode=GenerationMode.SIMPLE, gender=Gender.ANY, rng=random.Random(7)
        )
        assert result.first_name, f"Region '{region_id}' lieferte keinen Vornamen"
        assert result.full_name


# ── Nachname optional ─────────────────────────────────────────────────────────


def test_full_name_without_last_name() -> None:
    result = NameResult.build(
        first="Adalhard",
        last=None,
        gender=Gender.MALE,
        region="Test",
        mode=GenerationMode.SIMPLE,
    )
    assert result.full_name == "Adalhard"


def test_full_name_with_last_name() -> None:
    result = NameResult.build(
        first="Adalhard",
        last="von Kosch",
        gender=Gender.MALE,
        region="Test",
        mode=GenerationMode.SIMPLE,
    )
    assert result.last_name == "von Kosch"
    assert result.full_name == "Adalhard von Kosch"


# ── Compose-Modus: Infixe ─────────────────────────────────────────────────────


def test_compose_infix_probability_zero_never_uses_infix() -> None:
    """Mit Override 0 darf kein Infix im Vornamen oder Nachnamen auftauchen."""
    for i in range(20):
        r = generate(
            "mittelreich_kosch",
            mode=GenerationMode.COMPOSE,
            rng=random.Random(i),
            infix_probability_override=0.0,
        )
        assert r.components is not None
        assert r.components.first_infix is None
        assert r.components.last_infix is None


def test_compose_infix_probability_one_uses_infix_when_pools_exist() -> None:
    r = generate(
        "mittelreich_kosch",
        mode=GenerationMode.COMPOSE,
        rng=random.Random(1),
        infix_probability_override=1.0,
    )
    assert r.components is not None
    assert r.components.first_infix is not None
    assert r.components.last_infix is not None


def test_compose_components_reconstruct_name() -> None:
    """Bausteine sollen zusammengesetzt den generierten Namen ergeben."""
    for i in range(10):
        r = generate("mittelreich_kosch", mode=GenerationMode.COMPOSE, rng=random.Random(i))
        assert r.components is not None
        c = r.components
        expected_first = (c.first_prefix or "") + (c.first_infix or "") + (c.first_suffix or "")
        assert r.first_name == expected_first


# ── Fehlerbehandlung ──────────────────────────────────────────────────────────


def test_generate_unknown_region_raises_loader_error() -> None:
    from namegen.loader import LoaderError

    with pytest.raises(LoaderError):
        generate("region_which_does_not_exist")
