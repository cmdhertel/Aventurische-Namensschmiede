"""JSON-Import/Export helpers for web result lists."""

from __future__ import annotations

import json
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


def parse_results_json(payload: str) -> list[dict]:
    """Validate and normalize imported result JSON for template rendering."""
    try:
        parsed = ResultsExport.model_validate(json.loads(payload))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("Ungültige JSON-Datei für Namensliste/Charakterliste.") from exc

    return [_to_template_result(entry) for entry in parsed.entries]


def _to_template_result(entry: NameExportEntry | CharacterExportEntry) -> dict:
    base = {
        "kind": entry.kind,
        "full_name": entry.full_name,
        "region": entry.region,
        "culture": entry.culture,
        "species": entry.species,
        "region_abbreviation": entry.region_abbr,
    }
    if entry.kind == "name":
        return {
            **base,
            "resolved_gender": {"value": entry.gender},
            "mode": {"value": entry.mode},
        }
    return {
        **base,
        "age": entry.age,
        "profession": entry.profession,
        "name": {
            "resolved_gender": {"value": entry.gender},
            "mode": {"value": entry.mode},
        },
        "traits": {
            "physical": {
                "hair": entry.hair,
                "eyes": entry.eyes,
                "build": entry.build,
            },
            "personality": entry.personality,
            "motivation": entry.motivation,
            "quirk": entry.quirk,
        },
    }
