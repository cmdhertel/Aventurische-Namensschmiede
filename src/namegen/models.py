"""Pydantic v2 data models for region files and generator output."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field

# ── Enums ─────────────────────────────────────────────────────────────────────


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    ANY = "any"


class GenerationMode(StrEnum):
    SIMPLE = "simple"
    COMPOSE = "compose"


class ProfessionCategory(StrEnum):
    ALL = "alle"
    GEWEIHTE = "geweihte"
    ZAUBERER = "zauberer"
    KAEMPFER = "kaempfer"  # weltliche.kaempfer + weltliche.ordensleute
    PROFAN = "profan"  # weltliche.profane


class ExperienceLevel(StrEnum):
    LEHRLING = "lehrling"
    GESELLE = "geselle"
    MEISTER = "meister"
    VETERAN = "veteran"


# ── Region TOML sub-models ────────────────────────────────────────────────────


class GenderedStringPool(BaseModel):
    """Plain string lists split by gender. Used in [simple.first] and [simple.last]."""

    male: list[str] = Field(default_factory=list)
    female: list[str] = Field(default_factory=list)
    neutral: list[str] = Field(default_factory=list)


class ComposeParts(BaseModel):
    """Syllable building blocks for one gender within compose mode."""

    prefix: list[str] = Field(default_factory=list)
    infix: list[str] = Field(default_factory=list)
    suffix: list[str] = Field(default_factory=list)


class ComposeSection(BaseModel):
    """Gendered ComposeParts plus infix probability for one name slot (first or last)."""

    infix_probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.3
    male: ComposeParts = Field(default_factory=ComposeParts)
    female: ComposeParts = Field(default_factory=ComposeParts)
    neutral: ComposeParts = Field(default_factory=ComposeParts)


class SimpleConfig(BaseModel):
    first: GenderedStringPool = Field(default_factory=GenderedStringPool)
    last: GenderedStringPool = Field(default_factory=GenderedStringPool)


class ComposeConfig(BaseModel):
    first: ComposeSection = Field(default_factory=ComposeSection)
    last: ComposeSection = Field(default_factory=ComposeSection)


class RegionMeta(BaseModel):
    region: str
    abbreviation: Annotated[str, Field(min_length=3, max_length=3)]
    language: str = "de"
    notes: str = ""


class CharacterConfig(BaseModel):
    """Region-specific character data (professions, etc.)."""

    professions: list[str] = Field(default_factory=list)


class RegionData(BaseModel):
    """Top-level model representing one parsed region TOML file."""

    meta: RegionMeta
    simple: SimpleConfig = Field(default_factory=SimpleConfig)
    compose: ComposeConfig = Field(default_factory=ComposeConfig)
    character: CharacterConfig = Field(default_factory=CharacterConfig)


# ── Generator output ──────────────────────────────────────────────────────────


class NameComponents(BaseModel):
    """Syllable breakdown of a composed name. Only populated in compose mode."""

    first_prefix: str | None = None
    first_infix: str | None = None
    first_suffix: str | None = None
    last_prefix: str | None = None
    last_infix: str | None = None
    last_suffix: str | None = None


class PhysicalTraits(BaseModel):
    hair: str
    eyes: str
    build: str


class CharacterTraits(BaseModel):
    physical: PhysicalTraits
    personality: str
    motivation: str
    quirk: str


class CharacterResult(BaseModel):
    """Full fluff character sheet wrapping a NameResult."""

    experience: ExperienceLevel
    name: NameResult
    age: int
    profession: str
    traits: CharacterTraits

    @property
    def full_name(self) -> str:
        return self.name.full_name

    @property
    def gender(self) -> Gender:
        return self.name.gender

    @property
    def region(self) -> str:
        return self.name.region


class NameResult(BaseModel):
    """Structured result returned by the generator."""

    first_name: str
    last_name: str | None
    full_name: str
    gender: Gender  # angefordertes Geschlecht
    resolved_gender: Gender  # tatsächlicher Pool des Vornamens
    region: str
    mode: GenerationMode
    components: NameComponents | None = None

    @classmethod
    def build(
        cls,
        first: str,
        last: str | None,
        gender: Gender,
        region: str,
        mode: GenerationMode,
        components: NameComponents | None = None,
        resolved_gender: Gender | None = None,
    ) -> NameResult:
        full = f"{first} {last}" if last else first
        return cls(
            first_name=first,
            last_name=last,
            full_name=full,
            gender=gender,
            resolved_gender=resolved_gender if resolved_gender is not None else gender,
            region=region,
            mode=mode,
            components=components,
        )
