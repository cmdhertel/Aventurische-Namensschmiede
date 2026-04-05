"""Character generation with species, culture, and origin context."""

from __future__ import annotations

import random
import tomllib
from functools import lru_cache
from importlib.resources import files

from .generator import generate
from .catalog import pick_generation_target
from .loader import load_region
from .models import (
    CharacterResult,
    CharacterTraits,
    ExperienceLevel,
    Gender,
    GenerationMode,
    PhysicalTraits,
    ProfessionCategory,
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


def _load_professions_by_category(category: ProfessionCategory) -> list[str]:
    raw = _load_regelwiki_raw()["professionen"]
    match category:
        case ProfessionCategory.GEWEIHTE:
            return raw["geweihte"]
        case ProfessionCategory.ZAUBERER:
            return raw["zauberer"]
        case ProfessionCategory.KAEMPFER:
            w = raw["weltliche"]
            return w["kaempfer"] + w["ordensleute"]
        case ProfessionCategory.PROFAN:
            return raw["weltliche"]["profane"]
        case _:
            w = raw["weltliche"]
            return (
                raw["geweihte"] + raw["zauberer"] + w["kaempfer"] + w["ordensleute"] + w["profane"]
            )


def get_profession_groups() -> list[tuple[str, list[str]]]:
    """Return professions grouped for CLI display and user-facing filtering."""
    return [
        ("Geweihte", _load_professions_by_category(ProfessionCategory.GEWEIHTE)),
        ("Zauberer", _load_professions_by_category(ProfessionCategory.ZAUBERER)),
        ("Kämpfer & Ordensleute", _load_professions_by_category(ProfessionCategory.KAEMPFER)),
        ("Profane", _load_professions_by_category(ProfessionCategory.PROFAN)),
    ]


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
    rng: random.Random,
) -> str:
    base_pool = _load_professions_by_category(category)

    if category == ProfessionCategory.ALL:
        regional = data.character.professions
        pool = base_pool + regional * 2 if regional else base_pool
    else:
        pool = base_pool

    return rng.choice(pool)


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
    experience: ExperienceLevel = ExperienceLevel.GESELLE,
    infix_probability_override: float | None = None,
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
    )
    age = _generate_experience_age(experience, _rng)
    profession = _pick_profession(data, profession_category, _rng)
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
