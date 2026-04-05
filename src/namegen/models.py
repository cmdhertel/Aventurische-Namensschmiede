"""Pydantic v2 data models for species, cultures, origins, and generator output."""

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


class NameSchemaType(StrEnum):
    GIVEN_FAMILY = "given_family"
    GIVEN_FAMILY_CONNECTOR = "given_family_connector"
    GIVEN_PATRONYM = "given_patronym"
    GIVEN_BYNAME = "given_byname"
    SINGLE_NAME = "single_name"


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


class NameSchema(BaseModel):
    """Describes how a generated full name is assembled."""

    type: NameSchemaType = NameSchemaType.GIVEN_FAMILY
    connector: str | None = None
    male_patronym_pattern: str = "{parent}son"
    female_patronym_pattern: str = "{parent}dottir"
    neutral_patronym_pattern: str = "{parent}"
    description: str = ""


class SimpleConfig(BaseModel):
    first: GenderedStringPool = Field(default_factory=GenderedStringPool)
    last: GenderedStringPool = Field(default_factory=GenderedStringPool)
    parent: GenderedStringPool = Field(default_factory=GenderedStringPool)
    byname: GenderedStringPool = Field(default_factory=GenderedStringPool)


class ComposeConfig(BaseModel):
    first: ComposeSection = Field(default_factory=ComposeSection)
    last: ComposeSection = Field(default_factory=ComposeSection)


class RegionMeta(BaseModel):
    region: str
    abbreviation: Annotated[str, Field(min_length=3, max_length=3)]
    language: str = "de"
    notes: str = ""


class SpeciesMeta(BaseModel):
    name: str
    notes: str = ""


class CultureMeta(BaseModel):
    name: str
    notes: str = ""


class SpeciesStats(BaseModel):
    ap_value: int | None = None
    life_points: int | None = None
    soul_power: int | None = None
    toughness: int | None = None
    speed: int | None = None
    attribute_modifiers: list[str] = Field(default_factory=list)
    automatic_advantages: list[str] = Field(default_factory=list)
    automatic_disadvantages: list[str] = Field(default_factory=list)
    adult_age: int = 18
    max_age: int = 80


class CharacterConfig(BaseModel):
    """Character-relevant data from species, culture, and origin."""

    professions: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    scripts: list[str] = Field(default_factory=list)
    local_knowledge: list[str] = Field(default_factory=list)
    social_status: list[str] = Field(default_factory=list)
    typical_advantages: list[str] = Field(default_factory=list)
    typical_disadvantages: list[str] = Field(default_factory=list)
    typical_talents: list[str] = Field(default_factory=list)
    personality: list[str] = Field(default_factory=list)
    motivations: list[str] = Field(default_factory=list)
    quirks: list[str] = Field(default_factory=list)
    hair: list[str] = Field(default_factory=list)
    eyes: list[str] = Field(default_factory=list)
    build: list[str] = Field(default_factory=list)


class SpeciesData(BaseModel):
    meta: SpeciesMeta
    stats: SpeciesStats = Field(default_factory=SpeciesStats)
    usual_cultures: list[str] = Field(default_factory=list)
    character: CharacterConfig = Field(default_factory=CharacterConfig)


class CultureData(BaseModel):
    meta: CultureMeta
    naming_schema: NameSchema = Field(default_factory=NameSchema)
    simple: SimpleConfig = Field(default_factory=SimpleConfig)
    compose: ComposeConfig = Field(default_factory=ComposeConfig)
    character: CharacterConfig = Field(default_factory=CharacterConfig)
    package_ap: int | None = None


class OriginRef(BaseModel):
    species_id: str = "human"
    culture_id: str = "generic"
    region_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class RegionData(BaseModel):
    """Resolved origin profile representing one playable naming origin."""

    meta: RegionMeta
    origin: OriginRef = Field(default_factory=OriginRef)
    naming_schema: NameSchema = Field(default_factory=NameSchema)
    simple: SimpleConfig = Field(default_factory=SimpleConfig)
    compose: ComposeConfig = Field(default_factory=ComposeConfig)
    character: CharacterConfig = Field(default_factory=CharacterConfig)
    species: SpeciesData | None = None
    culture: CultureData | None = None


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
    language: str | None = None
    script: str | None = None
    social_status: str | None = None
    species_stats: SpeciesStats | None = None
    typical_advantages: list[str] = Field(default_factory=list)
    typical_disadvantages: list[str] = Field(default_factory=list)
    typical_talents: list[str] = Field(default_factory=list)

    @property
    def full_name(self) -> str:
        return self.name.full_name

    @property
    def gender(self) -> Gender:
        return self.name.gender

    @property
    def region(self) -> str:
        return self.name.region

    @property
    def culture(self) -> str | None:
        return self.name.culture

    @property
    def species(self) -> str | None:
        return self.name.species


class NameResult(BaseModel):
    """Structured result returned by the generator."""

    first_name: str
    last_name: str | None
    full_name: str
    gender: Gender  # angefordertes Geschlecht
    resolved_gender: Gender  # tatsächlicher Pool des Vornamens
    region: str
    culture: str | None = None
    species: str | None = None
    origin_id: str | None = None
    mode: GenerationMode
    name_schema: NameSchemaType = NameSchemaType.GIVEN_FAMILY
    connector: str | None = None
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
        culture: str | None = None,
        species: str | None = None,
        origin_id: str | None = None,
        name_schema: NameSchemaType = NameSchemaType.GIVEN_FAMILY,
        connector: str | None = None,
        full_name_override: str | None = None,
    ) -> NameResult:
        if full_name_override is not None:
            full = full_name_override
        elif last and connector:
            full = f"{first} {connector} {last}"
        elif last:
            full = f"{first} {last}"
        else:
            full = first

        return cls(
            first_name=first,
            last_name=last,
            full_name=full,
            gender=gender,
            resolved_gender=resolved_gender if resolved_gender is not None else gender,
            region=region,
            culture=culture,
            species=species,
            origin_id=origin_id,
            mode=mode,
            name_schema=name_schema,
            connector=connector,
            components=components,
        )
