"""Character generation with species, culture, and origin context."""

from __future__ import annotations

import random
import re
import tomllib
from collections.abc import Collection
from functools import lru_cache
from importlib.resources import files

from .catalog import pick_generation_target, resolve_generation_targets
from .generator import generate
from .loader import load_region
from .models import (
    CharacterResult,
    CharacterTraits,
    ExperienceLevel,
    Gender,
    GenerationMode,
    PhysicalTraits,
    ProfessionCategory,
    ProfessionChoiceGroup,
    ProfessionEntry,
    ProfessionSelectionPreview,
    ProfessionTheme,
    RegionData,
)


@lru_cache(maxsize=1)
def _load_regelwiki_raw() -> dict:
    data = files("namegen.data").joinpath("professions_regelwiki.toml").read_bytes()
    return tomllib.loads(data.decode())


@lru_cache(maxsize=1)
def _load_traits_raw() -> dict:
    data = files("namegen.data").joinpath("traits.toml").read_bytes()
    return tomllib.loads(data.decode())


@lru_cache(maxsize=1)
def _load_profession_themes_raw() -> dict:
    data = files("namegen.data").joinpath("profession_themes.toml").read_bytes()
    return tomllib.loads(data.decode())


@lru_cache(maxsize=1)
def _load_profession_themes() -> dict[str, ProfessionTheme]:
    raw = _load_profession_themes_raw().get("themes", {})
    return {theme_id: ProfessionTheme(id=theme_id, **config) for theme_id, config in raw.items()}


def _collect_themed_profession_ids(entries: Collection[ProfessionEntry]) -> set[str]:
    theme_ids: set[str] = set()
    for entry in entries:
        theme_ids.update(entry.themes)
    return theme_ids


def _slugify(value: str) -> str:
    normalized = value.casefold().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    normalized = normalized.replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def _build_profession_entry(
    name: str,
    *,
    categories: list[ProfessionCategory],
    weight: int = 1,
    themes: list[str] | None = None,
) -> ProfessionEntry:
    return ProfessionEntry(
        name=name,
        categories=categories,
        weight=weight,
        themes=themes or [],
    )


@lru_cache(maxsize=1)
def _load_general_professions() -> tuple[ProfessionEntry, ...]:
    raw = _load_regelwiki_raw()["professionen"]
    merged: dict[str, ProfessionEntry] = {}

    def add_many(names: list[str], category: ProfessionCategory) -> None:
        for name in names:
            existing = merged.get(name)
            if existing is None:
                merged[name] = _build_profession_entry(name, categories=[category])
                continue
            if category not in existing.categories:
                existing.categories.append(category)

    add_many(raw["geweihte"], ProfessionCategory.GEWEIHTE)
    add_many(raw["zauberer"], ProfessionCategory.ZAUBERER)
    add_many(raw["weltliche"]["kaempfer"], ProfessionCategory.KAEMPFER)
    add_many(raw["weltliche"]["ordensleute"], ProfessionCategory.KAEMPFER)
    add_many(raw["weltliche"]["profane"], ProfessionCategory.PROFAN)
    return tuple(merged.values())


@lru_cache(maxsize=1)
def _general_profession_category_map() -> dict[str, tuple[ProfessionCategory, ...]]:
    mapping: dict[str, set[ProfessionCategory]] = {}
    for entry in _load_general_professions():
        mapping.setdefault(entry.name, set()).update(entry.categories)
    return {
        name: tuple(sorted(categories, key=lambda item: item.value))
        for name, categories in mapping.items()
    }


def _infer_categories_for_profession(name: str) -> list[ProfessionCategory]:
    categories = _general_profession_category_map().get(name)
    if categories is not None:
        return list(categories)

    lowered = name.casefold()
    if any(token in lowered for token in ("geweih", "priester", "schamane")):
        return [ProfessionCategory.GEWEIHTE]
    if any(
        token in lowered
        for token in ("mag", "zauber", "hex", "druid", "geode", "elf", "schelm", "zibil")
    ):
        return [ProfessionCategory.ZAUBERER]
    if any(
        token in lowered
        for token in (
            "krieger",
            "ritter",
            "soldat",
            "söldner",
            "soeldner",
            "reiter",
            "wache",
            "wächter",
            "waechter",
            "kämpfer",
            "kaempfer",
            "gardist",
            "plünder",
            "pluender",
            "lanzer",
            "schwert",
            "duellant",
            "amazon",
        )
    ):
        return [ProfessionCategory.KAEMPFER]
    return [ProfessionCategory.PROFAN]


def _load_professions_by_category(category: ProfessionCategory) -> list[str]:
    return [
        entry.name
        for entry in _load_general_professions()
        if category == ProfessionCategory.ALL or category in entry.categories
    ]


def _normalize_regional_profession(entry: str | ProfessionEntry) -> ProfessionEntry:
    if isinstance(entry, ProfessionEntry):
        if entry.categories:
            return entry
        return ProfessionEntry(
            name=entry.name,
            categories=_infer_categories_for_profession(entry.name),
            weight=entry.weight,
            themes=entry.themes,
        )
    return ProfessionEntry(name=entry, categories=_infer_categories_for_profession(entry), weight=3)


def _profession_matches_category(
    entry: ProfessionEntry,
    category: ProfessionCategory,
) -> bool:
    return (
        category == ProfessionCategory.ALL
        or ProfessionCategory.ALL in entry.categories
        or category in entry.categories
    )


def _resolve_profession_pool(
    data: RegionData,
    category: ProfessionCategory,
    profession_theme: str | None,
) -> list[tuple[str, int]]:
    theme_id = (profession_theme or "").strip()
    if theme_id and theme_id not in _load_profession_themes():
        raise ValueError(f"Unknown profession theme: {profession_theme}")

    weighted_professions: dict[str, int] = {}

    def add_entry(entry: ProfessionEntry, base_weight: int) -> None:
        if not _profession_matches_category(entry, category):
            return
        if theme_id and theme_id not in entry.themes:
            return
        extra_weight = entry.weight
        if theme_id and theme_id in entry.themes:
            extra_weight += 5
        weighted_professions[entry.name] = (
            weighted_professions.get(entry.name, 0) + base_weight + extra_weight
        )

    for entry in _load_general_professions():
        add_entry(entry, 1)

    regional_entries = [
        _normalize_regional_profession(entry) for entry in data.character.profession_entries
    ]
    regional_entries.extend(
        _normalize_regional_profession(entry) for entry in data.character.professions
    )
    for entry in regional_entries:
        add_entry(entry, 3)

    return [(name, weight) for name, weight in weighted_professions.items() if weight > 0]


def get_profession_groups() -> list[tuple[str, list[str]]]:
    """Return professions grouped for CLI display and user-facing filtering."""
    return [
        ("Geweihte", _load_professions_by_category(ProfessionCategory.GEWEIHTE)),
        ("Zauberer", _load_professions_by_category(ProfessionCategory.ZAUBERER)),
        ("Kämpfer & Ordensleute", _load_professions_by_category(ProfessionCategory.KAEMPFER)),
        ("Profane", _load_professions_by_category(ProfessionCategory.PROFAN)),
    ]


def get_profession_themes() -> list[ProfessionTheme]:
    return list(_load_profession_themes().values())


def get_profession_themes_for_selection(
    selection_id: str,
    category: ProfessionCategory = ProfessionCategory.ALL,
) -> list[ProfessionTheme]:
    theme_catalog = _load_profession_themes()
    theme_ids: set[str] = set()

    for target_id in resolve_generation_targets(selection_id):
        data = load_region(target_id)
        regional_entries = [
            _normalize_regional_profession(entry) for entry in data.character.profession_entries
        ]
        regional_entries.extend(
            _normalize_regional_profession(entry) for entry in data.character.professions
        )
        matching_entries = [
            entry for entry in regional_entries if _profession_matches_category(entry, category)
        ]
        theme_ids.update(_collect_themed_profession_ids(matching_entries))

    return [theme_catalog[theme_id] for theme_id in sorted(theme_ids) if theme_id in theme_catalog]


def get_profession_preview_for_selection(
    selection_id: str,
    category: ProfessionCategory = ProfessionCategory.ALL,
) -> ProfessionSelectionPreview:
    targets = resolve_generation_targets(selection_id)
    grouped_professions: dict[ProfessionCategory, set[str]] = {
        ProfessionCategory.GEWEIHTE: set(),
        ProfessionCategory.ZAUBERER: set(),
        ProfessionCategory.KAEMPFER: set(),
        ProfessionCategory.PROFAN: set(),
    }

    for target_id in targets:
        data = load_region(target_id)
        for group_category in grouped_professions:
            if category != ProfessionCategory.ALL and group_category != category:
                continue
            grouped_professions[group_category].update(
                name for name, _weight in _resolve_profession_pool(data, group_category, None)
            )

    groups = [
        ProfessionChoiceGroup(
            id=ProfessionCategory.GEWEIHTE.value,
            label="Geweihte",
            professions=sorted(grouped_professions[ProfessionCategory.GEWEIHTE]),
        ),
        ProfessionChoiceGroup(
            id=ProfessionCategory.ZAUBERER.value,
            label="Zauberer",
            professions=sorted(grouped_professions[ProfessionCategory.ZAUBERER]),
        ),
        ProfessionChoiceGroup(
            id=ProfessionCategory.KAEMPFER.value,
            label="Kämpfer & Ordensleute",
            professions=sorted(grouped_professions[ProfessionCategory.KAEMPFER]),
        ),
        ProfessionChoiceGroup(
            id=ProfessionCategory.PROFAN.value,
            label="Profane",
            professions=sorted(grouped_professions[ProfessionCategory.PROFAN]),
        ),
    ]

    return ProfessionSelectionPreview(
        selection_id=selection_id,
        groups=groups,
        themes=get_profession_themes_for_selection(selection_id, category=category),
    )


def _generate_age(data: RegionData, rng: random.Random) -> int:
    """Generate an age within the species' adult range, with soft cap near the upper end."""
    adult_age = data.species.stats.adult_age if data.species else 18
    max_age = data.species.stats.max_age if data.species else 80

    while True:
        age = rng.randint(adult_age, max_age)
        soft_cap = adult_age + int((max_age - adult_age) * 0.75)
        if age <= soft_cap:
            return age
        threshold = max(0.1, 1.0 - (age - soft_cap) / max(1, max_age - soft_cap))
        if rng.random() < threshold:
            return age


def _generate_experience_age(
    experience: ExperienceLevel,
    rng: random.Random,
) -> int:
    """Generate an age from the user-facing experience brackets."""
    match experience:
        case ExperienceLevel.LEHRLING:
            return rng.randint(10, 16)
        case ExperienceLevel.GESELLE:
            return rng.randint(17, 25)
        case ExperienceLevel.MEISTER:
            return rng.randint(26, 45)
        case ExperienceLevel.VETERAN:
            return rng.randint(46, 80)


def _pick_profession(
    data: RegionData,
    category: ProfessionCategory,
    profession_theme: str | None,
    rng: random.Random,
) -> str:
    pool = _resolve_profession_pool(data, category, profession_theme)
    if not pool:
        raise ValueError(
            "No professions available for the selected region/category/theme combination."
        )
    weighted_names = [name for name, weight in pool for _ in range(weight)]
    return rng.choice(weighted_names)


def _weighted_pool(base: list[str], extra: list[str], multiplier: int = 3) -> list[str]:
    # multiplier=3: regional entries appear 3× more often than generic pool entries
    if not extra:
        return base
    return base + extra * multiplier


def _generate_traits(data: RegionData, rng: random.Random) -> CharacterTraits:
    raw = _load_traits_raw()
    char = data.character
    return CharacterTraits(
        physical=PhysicalTraits(
            hair=rng.choice(_weighted_pool(raw["physical"]["hair"], char.hair)),
            eyes=rng.choice(_weighted_pool(raw["physical"]["eyes"], char.eyes)),
            build=rng.choice(_weighted_pool(raw["physical"]["build"], char.build)),
        ),
        personality=rng.choice(_weighted_pool(raw["personality"]["traits"], char.personality)),
        motivation=rng.choice(_weighted_pool(raw["background"]["motivations"], char.motivations)),
        quirk=rng.choice(_weighted_pool(raw["background"]["quirks"], char.quirks)),
    )


# ── Public API ─────────────────────────────────────────────────────────────────


def generate_character(
    region: str,
    mode: GenerationMode = GenerationMode.SIMPLE,
    gender: Gender = Gender.ANY,
    profession_category: ProfessionCategory = ProfessionCategory.ALL,
    profession_theme: str | None = None,
    experience: ExperienceLevel | None = None,
    infix_probability_override: float | None = None,
    min_syllables: int = 2,
    max_syllables: int = 4,
    exclude_names: Collection[str] | None = None,
    rng: random.Random | None = None,
) -> CharacterResult:
    _rng = rng if rng is not None else random
    target_id = pick_generation_target(region, _rng, compose_only=mode == GenerationMode.COMPOSE)
    data = load_region(target_id)

    name = generate(
        region=target_id,
        mode=mode,
        gender=gender,
        rng=_rng,
        infix_probability_override=infix_probability_override,
        min_syllables=min_syllables,
        max_syllables=max_syllables,
        exclude_names=exclude_names,
    )
    if experience is None:
        age = _generate_age(data, _rng)
    else:
        age = _generate_experience_age(experience, _rng)
    profession = _pick_profession(data, profession_category, profession_theme, _rng)
    traits = _generate_traits(data, _rng)

    language = _rng.choice(data.character.languages) if data.character.languages else None
    script = _rng.choice(data.character.scripts) if data.character.scripts else None
    social_status = (
        _rng.choice(data.character.social_status) if data.character.social_status else None
    )

    return CharacterResult(
        name=name,
        experience=experience,
        age=age,
        profession=profession,
        traits=traits,
        language=language,
        script=script,
        social_status=social_status,
        species_stats=data.species.stats if data.species else None,
        typical_advantages=data.character.typical_advantages,
        typical_disadvantages=data.character.typical_disadvantages,
        typical_talents=data.character.typical_talents,
    )
