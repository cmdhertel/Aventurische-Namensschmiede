"""Character generation: wraps name generation with age, profession, and traits."""

from __future__ import annotations

import random
import tomllib
from functools import lru_cache
from importlib.resources import files

from .generator import generate
from .loader import load_region
from .models import (
    CharacterResult,
    CharacterTraits,
    Gender,
    GenerationMode,
    PhysicalTraits,
    ProfessionCategory,
)


# ── Data loading ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_regelwiki_raw() -> dict:
    data = files("namegen.data").joinpath("professions_regelwiki.toml").read_bytes()
    return tomllib.loads(data.decode())


@lru_cache(maxsize=1)
def _load_traits_raw() -> dict:
    data = files("namegen.data").joinpath("traits.toml").read_bytes()
    return tomllib.loads(data.decode())


def _load_professions_by_category(category: ProfessionCategory) -> list[str]:
    """Return the regelwiki profession list for the given category."""
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
        case _:  # ALL
            w = raw["weltliche"]
            return (
                raw["geweihte"]
                + raw["zauberer"]
                + w["kaempfer"]
                + w["ordensleute"]
                + w["profane"]
            )


# ── Age distribution ───────────────────────────────────────────────────────────

def _generate_age(rng: random.Random) -> int:
    """
    Ages 18–80 for humans. Ages 70+ become progressively less likely:
    probability drops linearly from 1.0 at age 70 to ~0.1 at age 80.
    """
    while True:
        age = rng.randint(18, 80)
        if age <= 70:
            return age
        threshold = 1.0 - (age - 70) * 0.09
        if rng.random() < threshold:
            return age


# ── Profession selection ───────────────────────────────────────────────────────

def _pick_profession(
    region: str,
    category: ProfessionCategory,
    rng: random.Random,
) -> str:
    """
    Pick a profession from the regelwiki list for the given category.
    For ProfessionCategory.ALL, regional professions are added with 2× weight
    to reflect local prevalence.
    """
    base_pool = _load_professions_by_category(category)

    if category == ProfessionCategory.ALL:
        regional = load_region(region).character.professions
        pool = base_pool + regional * 2 if regional else base_pool
    else:
        pool = base_pool

    return rng.choice(pool)


# ── Traits generation ──────────────────────────────────────────────────────────

def _generate_traits(rng: random.Random) -> CharacterTraits:
    raw = _load_traits_raw()
    return CharacterTraits(
        physical=PhysicalTraits(
            hair=rng.choice(raw["physical"]["hair"]),
            eyes=rng.choice(raw["physical"]["eyes"]),
            build=rng.choice(raw["physical"]["build"]),
        ),
        personality=rng.choice(raw["personality"]["traits"]),
        motivation=rng.choice(raw["background"]["motivations"]),
        quirk=rng.choice(raw["background"]["quirks"]),
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_character(
    region: str,
    mode: GenerationMode = GenerationMode.SIMPLE,
    gender: Gender = Gender.ANY,
    profession_category: ProfessionCategory = ProfessionCategory.ALL,
    rng: random.Random | None = None,
) -> CharacterResult:
    """Generate a full fluff character (name + age + profession + traits)."""
    _rng = rng if rng is not None else random

    name = generate(region=region, mode=mode, gender=gender, rng=_rng)
    age = _generate_age(_rng)
    profession = _pick_profession(region, profession_category, _rng)
    traits = _generate_traits(_rng)

    return CharacterResult(
        name=name,
        age=age,
        profession=profession,
        traits=traits,
    )
