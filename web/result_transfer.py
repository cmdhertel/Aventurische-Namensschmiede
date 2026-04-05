"""JSON-Import/Export helpers for web result lists."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, Field, ValidationError

_FORMAT = "namenschmiede-results"
_VERSION = 1


class _BaseEntry(BaseModel):
    full_name: str
    gender: Literal["male", "female", "any"]
    region: str
    culture: str | None = None
    species: str | None = None
    region_abbr: str | None = None
    mode: Literal["simple", "compose"]


class NameExportEntry(_BaseEntry):
    kind: Literal["name"]


class CharacterExportEntry(_BaseEntry):
    kind: Literal["character"]
    age: int
    profession: str
    hair: str
    eyes: str
    build: str
    personality: str
    motivation: str
    quirk: str


Entry = Annotated[NameExportEntry | CharacterExportEntry, Field(discriminator="kind")]


class ResultsExport(BaseModel):
    format: Literal[_FORMAT]
    version: Literal[_VERSION]
    exported_at: str | None = None
    entries: list[Entry]


# ── Template result types ──────────────────────────────────────────────────────
# These mirror the attribute-access patterns used in Jinja2 templates,
# so that imported results and generated results are structurally identical.


@dataclass
class _GenderValue:
    value: str


@dataclass
class _ModeValue:
    value: str


@dataclass
class _PhysicalTraits:
    hair: str
    eyes: str
    build: str


@dataclass
class _CharacterTraits:
    physical: _PhysicalTraits
    personality: str
    motivation: str
    quirk: str


@dataclass
class _NameRef:
    """Minimal name sub-object for character template access (r.name.resolved_gender.value)."""

    resolved_gender: _GenderValue
    mode: _ModeValue


@dataclass
class NameTemplateResult:
    kind: str
    full_name: str
    region: str
    culture: str | None
    species: str | None
    region_abbreviation: str | None
    resolved_gender: _GenderValue
    mode: _ModeValue


@dataclass
class CharacterTemplateResult:
    kind: str
    full_name: str
    region: str
    culture: str | None
    species: str | None
    region_abbreviation: str | None
    age: int
    profession: str
    traits: _CharacterTraits
    name: _NameRef


# ── Public API ─────────────────────────────────────────────────────────────────


def parse_results_json(
    payload: str,
) -> list[NameTemplateResult | CharacterTemplateResult]:
    """Validate and normalize imported result JSON for template rendering."""
    try:
        parsed = ResultsExport.model_validate(json.loads(payload))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("Ungültige JSON-Datei für Namensliste/Charakterliste.") from exc

    return [_to_template_result(entry) for entry in parsed.entries]


def _to_template_result(
    entry: NameExportEntry | CharacterExportEntry,
) -> NameTemplateResult | CharacterTemplateResult:
    if entry.kind == "name":
        return NameTemplateResult(
            kind="name",
            full_name=entry.full_name,
            region=entry.region,
            culture=entry.culture,
            species=entry.species,
            region_abbreviation=entry.region_abbr,
            resolved_gender=_GenderValue(entry.gender),
            mode=_ModeValue(entry.mode),
        )
    return CharacterTemplateResult(
        kind="character",
        full_name=entry.full_name,
        region=entry.region,
        culture=entry.culture,
        species=entry.species,
        region_abbreviation=entry.region_abbr,
        age=entry.age,
        profession=entry.profession,
        traits=_CharacterTraits(
            physical=_PhysicalTraits(
                hair=entry.hair,
                eyes=entry.eyes,
                build=entry.build,
            ),
            personality=entry.personality,
            motivation=entry.motivation,
            quirk=entry.quirk,
        ),
        name=_NameRef(
            resolved_gender=_GenderValue(entry.gender),
            mode=_ModeValue(entry.mode),
        ),
    )
