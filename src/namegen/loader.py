"""Load and resolve species, culture, and origin data from the bundled data package."""

from __future__ import annotations

import tomllib
from functools import cache
from importlib.resources import files

from .models import (
    CharacterConfig,
    ComposeConfig,
    ComposeParts,
    ComposeSection,
    CultureData,
    CultureMeta,
    GenderedStringPool,
    NameSchema,
    OriginRef,
    RegionData,
    SimpleConfig,
    SpeciesData,
)


class LoaderError(Exception):
    pass


_DATA_PACKAGE = "namegen.data"
_NON_REGION_TOML = {"professions.toml", "professions_regelwiki.toml", "traits.toml", "__init__.py"}

_REAL_CULTURE_MAP = {
    "mittelreich": "mittelreicher",
    "mittelreich_albernia": "mittelreicher",
    "mittelreich_almada": "mittelreicher",
    "mittelreich_garetien": "mittelreicher",
    "mittelreich_greifenfurt": "mittelreicher",
    "mittelreich_kosch": "mittelreicher",
    "mittelreich_nordmarken": "mittelreicher",
    "mittelreich_perricum": "mittelreicher",
    "mittelreich_rabenmark": "mittelreicher",
    "mittelreich_rommilysermark": "mittelreicher",
    "mittelreich_sonnenmark": "mittelreicher",
    "mittelreich_tobrien": "mittelreicher",
    "mittelreich_warunk": "mittelreicher",
    "mittelreich_weiden": "mittelreicher",
    "mittelreich_windhag": "mittelreicher",
    "horasreich": "horasier",
    "bornland": "bornlaender",
    "ferkina": "ferkinas",
    "thorwal": "thorwaler",
    "ctki_ssrr": "ctki_ssrr",
    "auelfen": "auelfen",
    "elfen_firnelfen": "firnelfen",
    "elfen_waldelfen": "waldelfen",
    "elfen_steppenelfen": "steppenelfen",
    "elfen_hochelfen": "hochelfen",
    "elfen_shakagra": "shakagra",
    "ambosszwerge": "ambosszwerge",
    "huegelzwerge": "huegelzwerge",
    "brillantzwerge": "brillantzwerge",
    "tiefzwerge": "tiefzwerge",
}

_SPECIES_MAP = {
    "auelfen": "elf",
    "elfen_firnelfen": "elf",
    "elfen_waldelfen": "elf",
    "elfen_steppenelfen": "elf",
    "elfen_hochelfen": "elf",
    "elfen_shakagra": "elf",
    "ambosszwerge": "dwarf",
    "huegelzwerge": "dwarf",
    "brillantzwerge": "dwarf",
    "tiefzwerge": "dwarf",
    "ctki_ssrr": "achaz",
}

_CULTURE_REGION_METADATA_MAP = {
    "ambosszwerge": "ambosszwerge",
    "auelfen": "auelfen",
    "brillantzwerge": "brillantzwerge",
    "firnelfen": "elfen_firnelfen",
    "hochelfen": "elfen_hochelfen",
    "huegelzwerge": "huegelzwerge",
    "shakagra": "elfen_shakagra",
    "steppenelfen": "elfen_steppenelfen",
    "tiefzwerge": "tiefzwerge",
    "waldelfen": "elfen_waldelfen",
}
_CULTURE_SPECIES_MAP = {
    "ambosszwerge": "dwarf",
    "auelfen": "elf",
    "brillantzwerge": "dwarf",
    "firnelfen": "elf",
    "hochelfen": "elf",
    "huegelzwerge": "dwarf",
    "shakagra": "elf",
    "steppenelfen": "elf",
    "tiefzwerge": "dwarf",
    "waldelfen": "elf",
}


def _read_toml(path: str) -> dict:
    try:
        raw_bytes = files(_DATA_PACKAGE).joinpath(path).read_bytes()
    except (FileNotFoundError, TypeError) as exc:
        raise LoaderError(f"Data file '{path}' not found.") from exc

    try:
        return tomllib.loads(raw_bytes.decode())
    except tomllib.TOMLDecodeError as exc:
        raise LoaderError(f"Failed to parse '{path}': {exc}") from exc


def _concat_unique(*values: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for pool in values:
        for value in pool:
            if value not in seen:
                seen.add(value)
                merged.append(value)
    return merged


def _merge_gendered(base: GenderedStringPool, override: GenderedStringPool) -> GenderedStringPool:
    return GenderedStringPool(
        male=_concat_unique(base.male, override.male),
        female=_concat_unique(base.female, override.female),
        neutral=_concat_unique(base.neutral, override.neutral),
    )


def _merge_parts(base: ComposeParts, override: ComposeParts) -> ComposeParts:
    return ComposeParts(
        prefix=_concat_unique(base.prefix, override.prefix),
        infix=_concat_unique(base.infix, override.infix),
        suffix=_concat_unique(base.suffix, override.suffix),
    )


def _merge_section(base: ComposeSection, override: ComposeSection) -> ComposeSection:
    return ComposeSection(
        infix_probability=override.infix_probability
        if override.infix_probability is not None
        else base.infix_probability,
        male=_merge_parts(base.male, override.male),
        female=_merge_parts(base.female, override.female),
        neutral=_merge_parts(base.neutral, override.neutral),
    )


def _merge_simple(base: SimpleConfig, override: SimpleConfig) -> SimpleConfig:
    return SimpleConfig(
        first=_merge_gendered(base.first, override.first),
        last=_merge_gendered(base.last, override.last),
        parent=_merge_gendered(base.parent, override.parent),
        byname=_merge_gendered(base.byname, override.byname),
    )


def _merge_compose(base: ComposeConfig, override: ComposeConfig) -> ComposeConfig:
    return ComposeConfig(
        first=_merge_section(base.first, override.first),
        last=_merge_section(base.last, override.last),
    )


def _merge_character(base: CharacterConfig, override: CharacterConfig) -> CharacterConfig:
    return CharacterConfig(
        professions=_concat_unique(base.professions, override.professions),
        languages=_concat_unique(base.languages, override.languages),
        scripts=_concat_unique(base.scripts, override.scripts),
        local_knowledge=_concat_unique(base.local_knowledge, override.local_knowledge),
        social_status=_concat_unique(base.social_status, override.social_status),
        typical_advantages=_concat_unique(base.typical_advantages, override.typical_advantages),
        typical_disadvantages=_concat_unique(
            base.typical_disadvantages, override.typical_disadvantages
        ),
        typical_talents=_concat_unique(base.typical_talents, override.typical_talents),
        personality=_concat_unique(base.personality, override.personality),
        motivations=_concat_unique(base.motivations, override.motivations),
        quirks=_concat_unique(base.quirks, override.quirks),
        hair=_concat_unique(base.hair, override.hair),
        eyes=_concat_unique(base.eyes, override.eyes),
        build=_concat_unique(base.build, override.build),
    )


def _resolve_schema(base: NameSchema, override: NameSchema) -> NameSchema:
    return base if override.is_default() else override


def _infer_species_id(origin_id: str) -> str:
    return _SPECIES_MAP.get(origin_id, "human")


def _infer_culture_id(origin_id: str) -> str:
    return _REAL_CULTURE_MAP.get(origin_id, origin_id)


def _load_raw_origin(origin_name: str) -> dict:
    filename = f"{origin_name}.toml"
    try:
        raw = _read_toml(filename)
    except LoaderError as exc:
        available = ", ".join(list_regions())
        raise LoaderError(f"Origin '{origin_name}' not found. Available: {available}") from exc

    raw.setdefault("origin", {})
    raw["origin"].setdefault("species_id", _infer_species_id(origin_name))
    raw["origin"].setdefault("culture_id", _infer_culture_id(origin_name))
    raw["origin"].setdefault("region_id", origin_name)
    return raw


def _abbreviation_from_name(name: str) -> str:
    letters = "".join(char for char in name.upper() if char.isalpha())
    return (letters[:3] or "REG").ljust(3, "X")


def _has_compose_parts(parts: ComposeParts) -> bool:
    return bool(parts.prefix and parts.suffix)


def _load_raw_culture_region(culture_id: str) -> dict:
    raw_culture = _read_toml(f"cultures/{culture_id.lower()}.toml")
    meta = raw_culture.get("meta", {})
    metadata_id = _CULTURE_REGION_METADATA_MAP.get(culture_id)
    region_meta = {}
    if metadata_id is not None:
        try:
            region_meta = _read_toml(f"{metadata_id}.toml").get("meta", {})
        except LoaderError:
            region_meta = {}

    region_name = region_meta.get("region", meta.get("name", culture_id))
    notes = region_meta.get("notes", meta.get("notes", ""))
    abbreviation = region_meta.get("abbreviation", _abbreviation_from_name(region_name))

    return {
        "meta": {
            "region": region_name,
            "abbreviation": abbreviation,
            "notes": notes,
        },
        "origin": {
            "species_id": _CULTURE_SPECIES_MAP.get(culture_id, "human"),
            "culture_id": culture_id,
            "region_id": culture_id,
        },
    }


def _build_synthetic_culture(raw: dict) -> CultureData:
    meta = raw.get("meta", {})
    return CultureData(
        meta=CultureMeta(name=meta.get("region", meta.get("name", "Unbekannte Kultur"))),
        naming_schema=NameSchema(),
        simple=SimpleConfig.model_validate(raw.get("simple", {})),
        compose=ComposeConfig.model_validate(raw.get("compose", {})),
        character=CharacterConfig.model_validate(raw.get("character", {})),
    )


@cache
def load_species(species_id: str) -> SpeciesData:
    raw = _read_toml(f"species/{species_id.lower()}.toml")
    return SpeciesData.model_validate(raw)


@cache
def load_culture(culture_id: str) -> CultureData:
    raw = _read_toml(f"cultures/{culture_id.lower()}.toml")
    return CultureData.model_validate(raw)


def list_species() -> list[str]:
    data_dir = files(_DATA_PACKAGE).joinpath("species")
    return sorted(
        p.name.removesuffix(".toml") for p in data_dir.iterdir() if p.name.endswith(".toml")
    )


def list_cultures() -> list[str]:
    data_dir = files(_DATA_PACKAGE).joinpath("cultures")
    return sorted(
        p.name.removesuffix(".toml") for p in data_dir.iterdir() if p.name.endswith(".toml")
    )


def list_regions() -> list[str]:
    """Return all available origin IDs derived from top-level TOML filenames."""
    data_dir = files(_DATA_PACKAGE)
    return sorted(
        p.name.removesuffix(".toml")
        for p in data_dir.iterdir()
        if p.name.endswith(".toml") and p.name not in _NON_REGION_TOML
    )


@cache
def load_region(region_name: str) -> RegionData:
    """Load a resolved region profile by ID (case-insensitive)."""
    origin_id = region_name.lower()
    try:
        raw = _load_raw_origin(origin_id)
    except LoaderError:
        raw = _load_raw_culture_region(origin_id)
    region = RegionData.model_validate(raw)

    species_id = region.origin.species_id
    culture_id = region.origin.culture_id

    species = load_species(species_id)
    try:
        culture = load_culture(culture_id)
    except LoaderError:
        culture = _build_synthetic_culture(raw)

    merged_simple = _merge_simple(culture.simple, region.simple)
    merged_compose = _merge_compose(culture.compose, region.compose)
    merged_character = _merge_character(
        _merge_character(species.character, culture.character),
        region.character,
    )
    schema = _resolve_schema(culture.naming_schema, region.naming_schema)

    return RegionData(
        meta=region.meta,
        origin=OriginRef(
            species_id=species_id,
            culture_id=culture_id,
            region_id=region.origin.region_id or origin_id,
            tags=region.origin.tags,
        ),
        naming_schema=schema,
        simple=merged_simple,
        compose=merged_compose,
        character=merged_character,
        species=species,
        culture=culture,
    )
