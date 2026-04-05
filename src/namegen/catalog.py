"""Catalog assembly and generation-target resolution for UI and CLI."""

from __future__ import annotations

import random
from functools import cache

from .loader import (
    LoaderError,
    _has_compose_parts,
    list_cultures,
    list_regions,
    list_species,
    load_region,
)
from .models import RegionData

_REGION_ONLY_CULTURE_ID = "mittelreicher"
_CULTURE_ONLY_CATALOG_IDS = (
    "ambosszwerge",
    "auelfen",
    "brillantzwerge",
    "firnelfen",
    "hochelfen",
    "huegelzwerge",
    "shakagra",
    "steppenelfen",
    "tiefzwerge",
    "waldelfen",
)
_SPECIES_AGGREGATE_CULTURE_PREFIX = "all__"
_SPECIES_AGGREGATE_LABEL = "Alle Kulturen und Regionen"
_REGION_AGGREGATE_LABEL = "Alle Mittelreich-Regionen"


def _region_supports_compose(data: RegionData) -> bool:
    first = data.compose.first
    return any(_has_compose_parts(parts) for parts in (first.male, first.female, first.neutral))


@cache
def _get_concrete_origin_catalog() -> tuple[dict, ...]:
    catalog: list[dict] = []
    for culture_id in _CULTURE_ONLY_CATALOG_IDS:
        data = load_region(culture_id)
        catalog.append(
            {
                "id": culture_id,
                "name": data.meta.region,
                "species_id": data.origin.species_id,
                "species_name": data.species.meta.name if data.species else data.origin.species_id,
                "culture_id": data.origin.culture_id,
                "culture_name": data.culture.meta.name if data.culture else data.origin.culture_id,
                "region_name": "",
                "has_region": False,
                "is_aggregate": False,
                "has_compose": _region_supports_compose(data),
                "notes": data.meta.notes,
            }
        )

    for origin_id in list_regions():
        data = load_region(origin_id)
        if data.origin.species_id in {"elf", "dwarf"}:
            continue

        is_region_choice = data.origin.culture_id == _REGION_ONLY_CULTURE_ID
        if origin_id == "mittelreich":
            continue
        if not is_region_choice and origin_id.startswith("mittelreich_"):
            continue
        catalog.append(
            {
                "id": origin_id,
                "name": data.meta.region,
                "species_id": data.origin.species_id,
                "species_name": data.species.meta.name if data.species else data.origin.species_id,
                "culture_id": data.origin.culture_id,
                "culture_name": data.culture.meta.name if data.culture else data.origin.culture_id,
                "region_name": data.meta.region if is_region_choice else "",
                "has_region": is_region_choice,
                "is_aggregate": False,
                "has_compose": _region_supports_compose(data),
                "notes": data.meta.notes,
            }
        )
    return tuple(
        sorted(
            catalog,
            key=lambda item: (
                item["species_name"],
                item["culture_name"],
                item["region_name"] or item["name"],
            ),
        )
    )


def get_origin_catalog() -> list[dict]:
    catalog = list(_get_concrete_origin_catalog())

    seen_species: set[str] = set()
    for item in _get_concrete_origin_catalog():
        species_id = item["species_id"]
        if species_id in seen_species:
            continue
        seen_species.add(species_id)
        catalog.append(
            {
                "id": species_id,
                "name": item["species_name"],
                "species_id": species_id,
                "species_name": item["species_name"],
                "culture_id": f"{_SPECIES_AGGREGATE_CULTURE_PREFIX}{species_id}",
                "culture_name": _SPECIES_AGGREGATE_LABEL,
                "region_name": "",
                "has_region": False,
                "is_aggregate": True,
                "has_compose": any(
                    entry["species_id"] == species_id and entry["has_compose"]
                    for entry in _get_concrete_origin_catalog()
                ),
                "notes": "Zufällige Auswahl aus allen Kulturen und Regionen dieser Spezies.",
            }
        )

    human_name = next(
        (
            item["species_name"]
            for item in _get_concrete_origin_catalog()
            if item["culture_id"] == _REGION_ONLY_CULTURE_ID
        ),
        "Mensch",
    )
    catalog.append(
        {
            "id": _REGION_ONLY_CULTURE_ID,
            "name": human_name,
            "species_id": "human",
            "species_name": human_name,
            "culture_id": _REGION_ONLY_CULTURE_ID,
            "culture_name": "Mittelreicher",
            "region_name": _REGION_AGGREGATE_LABEL,
            "has_region": True,
            "is_aggregate": True,
            "has_compose": any(
                entry["culture_id"] == _REGION_ONLY_CULTURE_ID and entry["has_compose"]
                for entry in _get_concrete_origin_catalog()
            ),
            "notes": "Zufällige Auswahl aus allen Mittelreich-Regionen.",
        }
    )

    return sorted(
        catalog,
        key=lambda item: (
            item["species_name"],
            item["culture_name"],
            not item["is_aggregate"],  # aggregates sort first within species/culture group
            item["region_name"] or item["name"],
        ),
    )


def _filter_compose_targets(selection_id: str, targets: tuple[str, ...]) -> tuple[str, ...]:
    compose_targets = tuple(target for target in targets if selection_supports_compose(target))
    if compose_targets:
        return compose_targets
    raise LoaderError(f"Selection '{selection_id}' has no Silbenbausteine.")


@cache
def resolve_generation_targets(selection_id: str, compose_only: bool = False) -> tuple[str, ...]:
    selection = selection_id.lower()
    catalog = _get_concrete_origin_catalog()

    if selection in list_regions():
        targets = (selection,)
        return _filter_compose_targets(selection_id, targets) if compose_only else targets

    direct_match = [item["id"] for item in catalog if item["id"] == selection]
    if direct_match:
        targets = tuple(direct_match)
        return _filter_compose_targets(selection_id, targets) if compose_only else targets

    if selection in list_species():
        targets = tuple(item["id"] for item in catalog if item["species_id"] == selection)
        if targets:
            return _filter_compose_targets(selection_id, targets) if compose_only else targets

    if selection in list_cultures():
        targets = [item["id"] for item in catalog if item["culture_id"] == selection]
        if targets:
            resolved = tuple(targets)
            return _filter_compose_targets(selection_id, resolved) if compose_only else resolved

    available = ", ".join(
        sorted({*list_species(), *list_cultures(), *(item["id"] for item in catalog)})
    )
    raise LoaderError(f"Selection '{selection_id}' not found. Available: {available}")


@cache
def selection_supports_compose(selection_id: str) -> bool:
    selection = selection_id.lower()
    if selection in list_regions():
        return _region_supports_compose(load_region(selection))

    concrete_catalog = _get_concrete_origin_catalog()
    if selection in list_species():
        return any(
            item["species_id"] == selection and item["has_compose"] for item in concrete_catalog
        )
    if selection in list_cultures():
        return any(
            item["culture_id"] == selection and item["has_compose"] for item in concrete_catalog
        )
    return False


def pick_generation_target(
    selection_id: str,
    rng: random.Random,
    compose_only: bool = False,
) -> str:
    targets = resolve_generation_targets(selection_id, compose_only=compose_only)
    if len(targets) == 1:
        return targets[0]
    return rng.choice(list(targets))
