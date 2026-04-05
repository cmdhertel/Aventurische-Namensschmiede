"""Core name generation logic for resolved origins and naming schemas."""

from __future__ import annotations

import random

from .loader import load_region
from .models import (
    ComposeParts,
    ComposeSection,
    Gender,
    GenderedStringPool,
    GenerationMode,
    NameComponents,
    NameResult,
    NameSchemaType,
    RegionData,
)


class GeneratorError(Exception):
    pass


def _resolve_simple_pool(
    pool: GenderedStringPool,
    gender: Gender,
    slot: str,
    region: str,
) -> list[tuple[str, Gender]]:
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
    neutral = section.neutral
    if gender == Gender.MALE:
        return section.male, neutral
    if gender == Gender.FEMALE:
        return section.female, neutral

    merged = ComposeParts(
        prefix=section.male.prefix + section.female.prefix + neutral.prefix,
        infix=section.male.infix + section.female.infix + neutral.infix,
        suffix=section.male.suffix + section.female.suffix + neutral.suffix,
    )
    return merged, ComposeParts()


def _pick(
    primary: list[str],
    fallback: list[str],
    component: str,
    slot: str,
    region: str,
    rng: random.Random,
) -> str:
    pool = primary if primary else fallback
    if not pool:
        raise GeneratorError(
            f"Region '{region}' compose mode: no '{component}' entries for {slot}."
        )
    return rng.choice(pool)


def _has_any_simple(pool: GenderedStringPool) -> bool:
    return bool(pool.male or pool.female or pool.neutral)


def _pick_parent_name(data: RegionData, rng: random.Random) -> str:
    parent_pool = data.simple.parent
    if _has_any_simple(parent_pool):
        candidates = parent_pool.male + parent_pool.female + parent_pool.neutral
    else:
        candidates = data.simple.first.male + data.simple.first.female + data.simple.first.neutral

    if not candidates:
        raise GeneratorError(f"Region '{data.meta.region}' has no parent-name pool.")
    return rng.choice(candidates)


def _apply_schema(
    data: RegionData,
    first: str,
    gender: Gender,
    resolved_gender: Gender,
    rng: random.Random,
    mode: GenerationMode,
    components: NameComponents | None,
    last_candidate: str | None,
) -> NameResult:
    schema = data.naming_schema
    last_name: str | None = None
    connector: str | None = None

    match schema.type:
        case NameSchemaType.SINGLE_NAME:
            last_name = None
        case NameSchemaType.GIVEN_BYNAME:
            if _has_any_simple(data.simple.byname):
                byname_pool = _resolve_simple_pool(
                    data.simple.byname,
                    Gender.ANY,
                    "byname",
                    data.meta.region,
                )
                last_name, _ = rng.choice(byname_pool)
            else:
                last_name = last_candidate
        case NameSchemaType.GIVEN_PATRONYM:
            parent = _pick_parent_name(data, rng)
            if resolved_gender == Gender.FEMALE:
                last_name = schema.female_patronym_pattern.format(parent=parent)
            elif resolved_gender == Gender.ANY:
                last_name = schema.neutral_patronym_pattern.format(parent=parent)
            else:
                last_name = schema.male_patronym_pattern.format(parent=parent)
        case NameSchemaType.GIVEN_FAMILY_CONNECTOR:
            connector = schema.connector
            last_name = last_candidate
        case _:
            last_name = last_candidate

    return NameResult.build(
        first=first,
        last=last_name,
        gender=gender,
        resolved_gender=resolved_gender,
        region=data.meta.region,
        culture=data.culture.meta.name if data.culture else None,
        species=data.species.meta.name if data.species else None,
        origin_id=data.origin.region_id,
        mode=mode,
        name_schema=schema.type,
        connector=connector,
        components=components,
    )


def generate(
    region: str,
    mode: GenerationMode = GenerationMode.SIMPLE,
    gender: Gender = Gender.ANY,
    rng: random.Random | None = None,
    infix_probability_override: float | None = None,
) -> NameResult:
    _rng = rng if rng is not None else random
    data: RegionData = load_region(region)

    if mode == GenerationMode.SIMPLE:
        return _generate_simple(data, gender, _rng)
    return _generate_compose(data, gender, _rng, infix_probability_override)


def _generate_simple(data: RegionData, gender: Gender, rng: random.Random) -> NameResult:
    first_pool = _resolve_simple_pool(data.simple.first, gender, "first name", data.meta.region)
    first, resolved_gender = rng.choice(first_pool)

    last_candidate: str | None = None
    if _has_any_simple(data.simple.last):
        last_pool = _resolve_simple_pool(data.simple.last, gender, "last name", data.meta.region)
        last_candidate, _ = rng.choice(last_pool)

    return _apply_schema(
        data=data,
        first=first,
        gender=gender,
        resolved_gender=resolved_gender,
        rng=rng,
        mode=GenerationMode.SIMPLE,
        components=None,
        last_candidate=last_candidate,
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

    prefix = _pick(fp.prefix, fn.prefix, "prefix", "first name", data.meta.region, rng)
    suffix = _pick(fp.suffix, fn.suffix, "suffix", "first name", data.meta.region, rng)

    infix: str | None = None
    infix_pool = fp.infix or fn.infix
    if infix_pool and rng.random() < first_infix_probability:
        infix = rng.choice(infix_pool)

    first = prefix + (infix or "") + suffix

    last_candidate: str | None = None
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
        last_candidate = last_prefix + (last_infix or "") + last_suffix

    components = NameComponents(
        first_prefix=prefix,
        first_infix=infix,
        first_suffix=suffix,
        last_prefix=last_prefix,
        last_infix=last_infix,
        last_suffix=last_suffix,
    )

    return _apply_schema(
        data=data,
        first=first,
        gender=gender,
        resolved_gender=gender,
        rng=rng,
        mode=GenerationMode.COMPOSE,
        components=components,
        last_candidate=last_candidate,
    )
