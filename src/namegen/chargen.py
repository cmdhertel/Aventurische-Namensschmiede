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
)


# ── Data loading ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_professions() -> list[str]:
    data = files("namegen.data").joinpath("professions.toml").read_bytes()
    return tomllib.loads(data.decode())["professions"]["general"]


@lru_cache(maxsize=1)
def _load_traits_raw() -> dict:
    data = files("namegen.data").joinpath("traits.toml").read_bytes()
    return tomllib.loads(data.decode())


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
        # Linear decline: 70 → 1.0, 80 → 0.1
        threshold = 1.0 - (age - 70) * 0.09
        if rng.random() < threshold:
            return age


# ── Profession selection ───────────────────────────────────────────────────────

def _pick_profession(region: str, rng: random.Random) -> str:
    """
    Merge global professions with region-specific ones.
    Region-specific professions are weighted 2× to reflect local prevalence.
    """
    global_list = _load_professions()
    region_data = load_region(region)
    regional_list = region_data.character.professions

    pool = global_list + regional_list * 2 if regional_list else global_list
    return rng.choice(pool)


# ── Traits generation ──────────────────────────────────────────────────────────

def _generate_traits(rng: random.Random) -> CharacterTraits:
    raw = _load_traits_raw()
    physical_raw = raw["physical"]
    personality_raw = raw["personality"]
    background_raw = raw["background"]

    return CharacterTraits(
        physical=PhysicalTraits(
            hair=rng.choice(physical_raw["hair"]),
            eyes=rng.choice(physical_raw["eyes"]),
            build=rng.choice(physical_raw["build"]),
        ),
        personality=rng.choice(personality_raw["traits"]),
        motivation=rng.choice(background_raw["motivations"]),
        quirk=rng.choice(background_raw["quirks"]),
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_character(
    region: str,
    mode: GenerationMode = GenerationMode.SIMPLE,
    gender: Gender = Gender.ANY,
    rng: random.Random | None = None,
) -> CharacterResult:
    """Generate a full fluff character (name + age + profession + traits)."""
    _rng = rng if rng is not None else random

    name = generate(region=region, mode=mode, gender=gender, rng=_rng)
    age = _generate_age(_rng)
    profession = _pick_profession(region, _rng)
    traits = _generate_traits(_rng)

    return CharacterResult(
        name=name,
        age=age,
        profession=profession,
        traits=traits,
    )
