"""Core name generation logic for resolved origins and naming schemas."""

from __future__ import annotations

import random
from collections.abc import Collection

from .catalog import pick_generation_target
from .loader import load_region
from .models import (
    _DEFAULT_INFIX_PROBABILITY,
    ComposeParts,
    ComposeSection,
    Gender,
    GenderedStringPool,
    GenerationMode,
    NameComponents,
    NameResult,
    NameSchemaType,
    NobilityStatus,
    RegionData,
)


class GeneratorError(Exception):
    pass


_DEFAULT_MIN_SYLLABLES = 2
_DEFAULT_MAX_SYLLABLES = 4
_MAX_GENERATION_ATTEMPTS = 200


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


def _resolve_last_name_pool(
    pool: GenderedStringPool,
    gender: Gender,
    nobility_status: NobilityStatus,
    region: str,
) -> list[tuple[str, Gender]] | None:
    """Return last-name candidates filtered by nobility_status.

    Returns None when the pool has no entries at all (single-name regions).
    Returns an empty list only when noble data is requested but unavailable —
    callers should then omit the last name rather than raising an error.
    """
    noble_set: frozenset[str] = frozenset(pool.noble)

    if nobility_status == NobilityStatus.NOBLE:
        if not noble_set:
            return None  # region has no noble data → no last name for noble chars
        return [(n, Gender.ANY) for n in pool.noble]

    # Build the base pool (all gendered + neutral entries)
    all_candidates = _resolve_simple_pool(pool, gender, "last name", region)

    if nobility_status == NobilityStatus.COMMON:
        filtered = [(n, g) for n, g in all_candidates if n not in noble_set]
        return filtered if filtered else all_candidates  # graceful: use all if nothing left

    # NobilityStatus.ANY — original behaviour (includes noble names mixed in)
    return all_candidates


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
    nobility_status: NobilityStatus = NobilityStatus.ANY,
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
        region_abbreviation=data.meta.abbreviation,
        origin_id=data.origin.region_id,
        mode=mode,
        name_schema=schema.type,
        connector=connector,
        components=components,
        nobility_status=nobility_status,
    )


def generate(
    region: str,
    mode: GenerationMode = GenerationMode.SIMPLE,
    gender: Gender = Gender.ANY,
    rng: random.Random | None = None,
    infix_probability_override: float | None = None,
    min_syllables: int = _DEFAULT_MIN_SYLLABLES,
    max_syllables: int = _DEFAULT_MAX_SYLLABLES,
    exclude_names: Collection[str] | None = None,
    nobility_status: NobilityStatus = NobilityStatus.ANY,
) -> NameResult:
    _rng = rng if rng is not None else random
    _validate_generation_constraints(mode, min_syllables, max_syllables)
    excluded = {name.strip().casefold() for name in (exclude_names or ()) if name.strip()}

    for _ in range(_MAX_GENERATION_ATTEMPTS):
        target_id = pick_generation_target(
            region,
            _rng,
            compose_only=mode == GenerationMode.COMPOSE,
        )
        data: RegionData = load_region(target_id)

        if mode == GenerationMode.SIMPLE:
            result = _generate_simple(data, gender, _rng, nobility_status)
        else:
            result = _generate_compose(
                data,
                gender,
                _rng,
                infix_probability_override,
                min_syllables=min_syllables,
                max_syllables=max_syllables,
                nobility_status=nobility_status,
            )

        if result.full_name.casefold() not in excluded:
            return result

    raise GeneratorError("No unique name could be generated within the retry limit.")


def _validate_generation_constraints(
    mode: GenerationMode,
    min_syllables: int,
    max_syllables: int,
) -> None:
    if min_syllables < 1 or max_syllables < 1:
        raise GeneratorError("Syllable limits must be positive integers.")
    if min_syllables > max_syllables:
        raise GeneratorError("min_syllables cannot be greater than max_syllables.")
    if mode != GenerationMode.COMPOSE and (
        min_syllables != _DEFAULT_MIN_SYLLABLES or max_syllables != _DEFAULT_MAX_SYLLABLES
    ):
        raise GeneratorError("Syllable limits are only available in compose mode.")


def _generate_simple(
    data: RegionData,
    gender: Gender,
    rng: random.Random,
    nobility_status: NobilityStatus = NobilityStatus.ANY,
) -> NameResult:
    first_pool = _resolve_simple_pool(data.simple.first, gender, "first name", data.meta.region)
    first, resolved_gender = rng.choice(first_pool)

    last_candidate: str | None = None
    if _has_any_simple(data.simple.last):
        last_pool = _resolve_last_name_pool(
            data.simple.last, gender, nobility_status, data.meta.region
        )
        if last_pool:
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
        nobility_status=nobility_status,
    )


def _generate_compose(
    data: RegionData,
    gender: Gender,
    rng: random.Random,
    infix_probability_override: float | None = None,
    *,
    min_syllables: int = _DEFAULT_MIN_SYLLABLES,
    max_syllables: int = _DEFAULT_MAX_SYLLABLES,
    nobility_status: NobilityStatus = NobilityStatus.ANY,
) -> NameResult:
    for _ in range(_MAX_GENERATION_ATTEMPTS):
        first_section = data.compose.first
        fp, fn = _resolve_compose_parts(first_section, gender)
        first_infix_probability = (
            infix_probability_override
            if infix_probability_override is not None
            else (first_section.infix_probability or _DEFAULT_INFIX_PROBABILITY)
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
            else (last_section.infix_probability or _DEFAULT_INFIX_PROBABILITY)
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

        if not _components_within_syllable_limits(components, min_syllables, max_syllables):
            continue

        # resolved_gender stays as-is (including ANY): compose mode merges all gender
        # pools into one, so we can't determine which gender the syllables came from.
        # In simple mode resolved_gender is set by whichever pool the name was drawn from.
        return _apply_schema(
            data=data,
            first=first,
            gender=gender,
            resolved_gender=gender,
            rng=rng,
            mode=GenerationMode.COMPOSE,
            components=components,
            last_candidate=last_candidate,
            nobility_status=nobility_status,
        )

    raise GeneratorError("No compose name matched the requested syllable limits.")


def _count_name_parts(*parts: str | None) -> int:
    return sum(1 for part in parts if part)


def _components_within_syllable_limits(
    components: NameComponents,
    min_syllables: int,
    max_syllables: int,
) -> bool:
    first_count = _count_name_parts(
        components.first_prefix,
        components.first_infix,
        components.first_suffix,
    )
    if not (min_syllables <= first_count <= max_syllables):
        return False

    last_count = _count_name_parts(
        components.last_prefix,
        components.last_infix,
        components.last_suffix,
    )
    if last_count == 0:
        return True
    return min_syllables <= last_count <= max_syllables
