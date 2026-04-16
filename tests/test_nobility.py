"""Tests für den NobilityStatus-Pfad: Modell, Generator, Charaktergenerator."""

from __future__ import annotations

import random

import pytest

from namegen.chargen import generate_character, _profession_matches_nobility
from namegen.generator import generate
from namegen.models import (
    Gender,
    GenerationMode,
    NobilityStatus,
    ProfessionCategory,
    ProfessionEntry,
)


# ── Modell-Tests ──────────────────────────────────────────────────────────────


def test_nobility_status_values() -> None:
    assert NobilityStatus.ANY == "any"
    assert NobilityStatus.NOBLE == "noble"
    assert NobilityStatus.COMMON == "common"


def test_nobility_status_from_string() -> None:
    assert NobilityStatus("any") is NobilityStatus.ANY
    assert NobilityStatus("noble") is NobilityStatus.NOBLE
    assert NobilityStatus("common") is NobilityStatus.COMMON


def test_profession_entry_social_statuses_default() -> None:
    entry = ProfessionEntry(name="Händler")
    assert entry.social_statuses == []


def test_profession_entry_social_statuses_noble() -> None:
    entry = ProfessionEntry(name="Ritter", social_statuses=[NobilityStatus.NOBLE])
    assert NobilityStatus.NOBLE in entry.social_statuses


def test_profession_entry_from_string_has_no_social_statuses() -> None:
    """Strings die per _from_string-Validator gewandelt werden haben leere social_statuses."""
    entry = ProfessionEntry.model_validate("Händler")
    assert entry.social_statuses == []


# ── _profession_matches_nobility ──────────────────────────────────────────────


def test_matches_nobility_any_accepts_all() -> None:
    noble_entry = ProfessionEntry(name="Ritter", social_statuses=[NobilityStatus.NOBLE])
    common_entry = ProfessionEntry(name="Händler")
    assert _profession_matches_nobility(noble_entry, NobilityStatus.ANY)
    assert _profession_matches_nobility(common_entry, NobilityStatus.ANY)


def test_matches_nobility_noble_accepts_untagged() -> None:
    """Unmarkierte Berufe (Magier, Geweihte etc.) sind auch für Adlige verfügbar."""
    entry = ProfessionEntry(name="Gildenmagier")
    assert _profession_matches_nobility(entry, NobilityStatus.NOBLE)


def test_matches_nobility_noble_accepts_noble_tagged() -> None:
    entry = ProfessionEntry(name="Ritter", social_statuses=[NobilityStatus.NOBLE])
    assert _profession_matches_nobility(entry, NobilityStatus.NOBLE)


def test_matches_nobility_common_excludes_noble_tagged() -> None:
    entry = ProfessionEntry(name="Ritter", social_statuses=[NobilityStatus.NOBLE])
    assert not _profession_matches_nobility(entry, NobilityStatus.COMMON)


def test_matches_nobility_common_accepts_untagged() -> None:
    entry = ProfessionEntry(name="Händler")
    assert _profession_matches_nobility(entry, NobilityStatus.COMMON)


# ── Generator: Namensgenerierung ──────────────────────────────────────────────


def test_generate_default_nobility_any() -> None:
    """Ohne noble_status verhält sich generate wie bisher (any)."""
    rng = random.Random(42)
    result = generate("mittelreich_kosch", rng=rng)
    assert result.nobility_status == NobilityStatus.ANY


def test_generate_noble_kosch_has_von_lastname() -> None:
    """Bei noble liefert Kosch nur Nachnamen aus der noble-Liste."""
    rng = random.Random(0)
    for _ in range(20):
        result = generate(
            "mittelreich_kosch",
            nobility_status=NobilityStatus.NOBLE,
            rng=rng,
        )
        assert result.last_name is not None
        assert result.last_name.startswith("von") or result.last_name.startswith("vom"), (
            f"Erwartet 'von/vom', erhalten: {result.last_name!r}"
        )
        assert result.nobility_status == NobilityStatus.NOBLE


def test_generate_common_kosch_no_von_lastname() -> None:
    """Bei common dürfen keine adligen Nachnamen vorkommen."""
    rng = random.Random(1)
    for _ in range(20):
        result = generate(
            "mittelreich_kosch",
            nobility_status=NobilityStatus.COMMON,
            rng=rng,
        )
        if result.last_name:
            assert not result.last_name.startswith("von"), (
                f"Unerwarteter Adelsnachname: {result.last_name!r}"
            )
            assert not result.last_name.startswith("vom"), (
                f"Unerwarteter Adelsnachname: {result.last_name!r}"
            )
        assert result.nobility_status == NobilityStatus.COMMON


def test_generate_any_kosch_is_mixed() -> None:
    """Bei any kommen sowohl bürgerliche als auch adlige Nachnamen vor (Stichprobe)."""
    rng = random.Random(7)
    last_names = {
        generate("mittelreich_kosch", nobility_status=NobilityStatus.ANY, rng=rng).last_name
        for _ in range(50)
    }
    von_names = {n for n in last_names if n and n.startswith("von")}
    common_names = {n for n in last_names if n and not n.startswith("von")}
    assert von_names, "Erwartet mind. einen Adelsnamen bei any"
    assert common_names, "Erwartet mind. einen bürgerlichen Namen bei any"


def test_generate_noble_region_without_noble_data_no_error() -> None:
    """Regionen ohne noble-Daten liefern bei noble keinen Fehler."""
    rng = random.Random(5)
    result = generate("thorwal", nobility_status=NobilityStatus.NOBLE, rng=rng)
    assert result.nobility_status == NobilityStatus.NOBLE


def test_generate_noble_garetien_von_lastname() -> None:
    rng = random.Random(0)
    for _ in range(20):
        result = generate(
            "mittelreich_garetien",
            nobility_status=NobilityStatus.NOBLE,
            rng=rng,
        )
        assert result.last_name is not None
        assert result.last_name.startswith("von") or result.last_name.startswith("vom"), (
            f"Erwartet 'von/vom', erhalten: {result.last_name!r}"
        )


def test_generate_noble_horasreich() -> None:
    rng = random.Random(0)
    results = [
        generate("horasreich", nobility_status=NobilityStatus.NOBLE, rng=rng)
        for _ in range(20)
    ]
    assert all(r.last_name is not None for r in results)


def test_generate_backwards_compat_no_param() -> None:
    """Bestehendes Verhalten ohne nobility_status bleibt identisch."""
    rng_old = random.Random(99)
    rng_new = random.Random(99)
    old = generate("mittelreich_kosch", rng=rng_old)
    new = generate("mittelreich_kosch", nobility_status=NobilityStatus.ANY, rng=rng_new)
    assert old.full_name == new.full_name


# ── Charaktergenerator ────────────────────────────────────────────────────────


def test_generate_character_default_nobility_any() -> None:
    rng = random.Random(42)
    char = generate_character("mittelreich_kosch", rng=rng)
    assert char.nobility_status == NobilityStatus.ANY


def test_generate_character_noble_has_noble_profession() -> None:
    """Adlige Charaktere bekommen Berufe die für Adlige geeignet sind."""
    rng = random.Random(0)
    professions = {
        generate_character(
            "mittelreich_kosch",
            nobility_status=NobilityStatus.NOBLE,
            rng=rng,
        ).profession
        for _ in range(30)
    }
    # Adelsexklusive Berufe müssen vorkommen
    noble_professions = {"Ritter", "Adlige", "Herrscher", "Höfling", "Distelritter", "Feenritter"}
    assert professions & noble_professions, (
        f"Erwartet mind. einen Adelsberuf in: {sorted(professions)}"
    )


def test_generate_character_common_no_noble_profession() -> None:
    """Bürgerliche Charaktere bekommen keine adelsexklusiven Berufe."""
    rng = random.Random(0)
    noble_professions = {"Ritter", "Adlige", "Herrscher", "Höfling", "Distelritter", "Feenritter"}
    for _ in range(30):
        char = generate_character(
            "mittelreich_kosch",
            nobility_status=NobilityStatus.COMMON,
            rng=rng,
        )
        assert char.profession not in noble_professions, (
            f"Unerwarteter Adelsberuf für common: {char.profession!r}"
        )


def test_generate_character_noble_and_common_name_consistent() -> None:
    """nobility_status wirkt konsistent auf Name UND Beruf."""
    rng = random.Random(11)
    char = generate_character(
        "mittelreich_kosch",
        nobility_status=NobilityStatus.NOBLE,
        rng=rng,
    )
    assert char.nobility_status == NobilityStatus.NOBLE
    assert char.name.nobility_status == NobilityStatus.NOBLE


def test_generate_character_with_profession_category_and_nobility() -> None:
    """Kombination aus Berufskategorie und Adelsstatus funktioniert ohne Fehler."""
    rng = random.Random(3)
    char = generate_character(
        "mittelreich_kosch",
        profession_category=ProfessionCategory.KAEMPFER,
        nobility_status=NobilityStatus.COMMON,
        rng=rng,
    )
    assert char.profession  # nicht leer
