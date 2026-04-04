"""Core name generation logic: simple and compose modes."""

from __future__ import annotations

import random

from .loader import load_region
from .models import (
    ComposeParts,
    ComposeSection,
    Gender,
    GenerationMode,
    GenderedStringPool,
    NameComponents,
    NameResult,
    RegionData,
)


class GeneratorError(Exception):
    pass


# ── Pool resolution helpers ────────────────────────────────────────────────────

def _resolve_simple_pool(
    pool: GenderedStringPool,
    gender: Gender,
    slot: str,
    region: str,
) -> list[tuple[str, Gender]]:
    """
    Build a candidate list from a GenderedStringPool.

    Returns (name, actual_gender) pairs so callers know which sub-pool each
    name came from. Neutral names are tagged as Gender.ANY.
    Raises GeneratorError if the result is empty.
    """
    candidates: list[tuple[str, Gender]] = []

    if gender in (Gender.MALE, Gender.ANY):
        candidates += [(n, Gender.MALE) for n in pool.male]
    if gender in (Gender.FEMALE, Gender.ANY):
        candidates += [(n, Gender.FEMALE) for n in pool.female]
    candidates += [(n, Gender.ANY) for n in pool.neutral]

    if not candidates:
        raise GeneratorError(
            f"Region '{region}' has no {slot} entries for gender='{gender}'. "
            f"Add entries to the TOML file."
        )
    return candidates


def _resolve_compose_parts(
    section: ComposeSection,
    gender: Gender,
) -> tuple[ComposeParts, ComposeParts]:
    """
    Return (primary, fallback) ComposeParts for the requested gender.

    Fallback is always the neutral pool. For Gender.ANY, all pools are merged
    into primary and fallback is empty to avoid double-counting.
    """
    neutral = section.neutral
    if gender == Gender.MALE:
        return section.male, neutral
    elif gender == Gender.FEMALE:
        return section.female, neutral
    else:
        merged = ComposeParts(
            prefix=section.male.prefix + section.female.prefix + neutral.prefix,
            infix=section.male.infix + section.female.infix + neutral.infix,
            suffix=section.male.suffix + section.female.suffix + neutral.suffix,
        )
        return merged, ComposeParts()


def _pick(primary: list[str], fallback: list[str], component: str, slot: str, region: str) -> str:
    pool = primary if primary else fallback
    if not pool:
        raise GeneratorError(
            f"Region '{region}' compose mode: no '{component}' entries for {slot}."
        )
    return random.choice(pool)


# ── Public API ─────────────────────────────────────────────────────────────────

def generate(
    region: str,
    mode: GenerationMode = GenerationMode.SIMPLE,
    gender: Gender = Gender.ANY,
    rng: random.Random | None = None,
    infix_probability_override: float | None = None,
) -> NameResult:
    """
    Generate a single name.

    Parameters
    ----------
    region:
        Region file stem, e.g. "kosch" or "mittelreich".
    mode:
        "simple" draws from predefined lists; "compose" assembles syllables.
    gender:
        "male", "female", or "any". Affects pool selection and fallback.
    rng:
        Optional seeded Random instance for reproducible output (useful in tests).
    """
    _rng = rng if rng is not None else random

    data: RegionData = load_region(region)

    if mode == GenerationMode.SIMPLE:
        return _generate_simple(data, gender, _rng)
    return _generate_compose(data, gender, _rng, infix_probability_override)


def _generate_simple(data: RegionData, gender: Gender, rng: random.Random) -> NameResult:
    first_pool = _resolve_simple_pool(data.simple.first, gender, "first name", data.meta.region)
    first, resolved_gender = rng.choice(first_pool)

    last: str | None = None
    all_last = data.simple.last.male + data.simple.last.female + data.simple.last.neutral
    if all_last:
        last_pool = _resolve_simple_pool(data.simple.last, gender, "last name", data.meta.region)
        last, _ = rng.choice(last_pool)

    return NameResult.build(
        first=first,
        last=last,
        gender=gender,
        resolved_gender=resolved_gender,
        region=data.meta.region,
        mode=GenerationMode.SIMPLE,
    )


def _generate_compose(
    data: RegionData,
    gender: Gender,
    rng: random.Random,
    infix_probability_override: float | None = None,
) -> NameResult:
    first_section = data.compose.first
    fp, fn = _resolve_compose_parts(first_section, gender)
    first_infix_probability = (
        infix_probability_override
        if infix_probability_override is not None
        else first_section.infix_probability
    )

    prefix = _pick(fp.prefix, fn.prefix, "prefix", "first name", data.meta.region)
    suffix = _pick(fp.suffix, fn.suffix, "suffix", "first name", data.meta.region)

    infix: str | None = None
    infix_pool = fp.infix or fn.infix
    if infix_pool and rng.random() < first_infix_probability:
        infix = rng.choice(infix_pool)

    first = prefix + (infix or "") + suffix

    # Last name is optional — skip silently if no compose.last data exists.
    last: str | None = None
    last_prefix: str | None = None
    last_infix: str | None = None
    last_suffix: str | None = None

    last_section = data.compose.last
    lp, ln = _resolve_compose_parts(last_section, gender)
    last_infix_probability = (
        infix_probability_override
        if infix_probability_override is not None
        else last_section.infix_probability
    )
    all_prefixes = lp.prefix + ln.prefix
    all_suffixes = lp.suffix + ln.suffix

    if all_prefixes and all_suffixes:
        last_prefix = rng.choice(all_prefixes)
        last_suffix = rng.choice(all_suffixes)

        last_infix_pool = lp.infix + ln.infix
        if last_infix_pool and rng.random() < last_infix_probability:
            last_infix = rng.choice(last_infix_pool)

        last = last_prefix + (last_infix or "") + last_suffix

    return NameResult.build(
        first=first,
        last=last,
        gender=gender,
        region=data.meta.region,
        mode=GenerationMode.COMPOSE,
        components=NameComponents(
            first_prefix=prefix,
            first_infix=infix,
            first_suffix=suffix,
            last_prefix=last_prefix,
            last_infix=last_infix,
            last_suffix=last_suffix,
        ),
    )
