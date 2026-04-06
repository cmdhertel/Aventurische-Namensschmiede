"""CLI profile storage helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

from .models import ExperienceLevel, Gender, GenerationMode, ProfessionCategory
from .output import OutputFormat


class GenerationProfile(BaseModel):
    region: str
    mode: GenerationMode = GenerationMode.SIMPLE
    gender: Gender = Gender.ANY
    count: int = Field(default=1, ge=1, le=100)
    fmt: OutputFormat = OutputFormat.RICH
    character: bool = False
    profession_category: ProfessionCategory = ProfessionCategory.ALL
    profession_theme: str | None = None
    experience: ExperienceLevel = ExperienceLevel.GESELLE
    show_components: bool = False
    infix_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    min_syllables: int = Field(default=2, ge=1)
    max_syllables: int = Field(default=4, ge=1)
    exclude_file: str | None = None


def profile_dir() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "namegen" / "profiles"


def profile_path(name: str) -> Path:
    return profile_dir() / f"{name}.json"


def save_profile(name: str, profile: GenerationProfile) -> Path:
    path = profile_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


def load_profile(name: str) -> GenerationProfile:
    path = profile_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Profile '{name}' not found: {path}")
    return GenerationProfile.model_validate_json(path.read_text(encoding="utf-8"))


def list_profiles() -> list[str]:
    base = profile_dir()
    if not base.exists():
        return []
    return sorted(path.stem for path in base.glob("*.json"))


def dump_profile(profile: GenerationProfile) -> str:
    return json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
