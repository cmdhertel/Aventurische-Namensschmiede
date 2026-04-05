"""Load and cache RegionData objects from the bundled data/ package."""

from __future__ import annotations

import tomllib
from functools import cache
from importlib.resources import files

from .models import RegionData


class LoaderError(Exception):
    pass


_DATA_PACKAGE = "namegen.data"


@cache
def _parse_region(region_name: str) -> RegionData:
    """Parse and validate one TOML file. Result is cached for the process lifetime."""
    filename = f"{region_name}.toml"
    try:
        resource = files(_DATA_PACKAGE).joinpath(filename)
        raw_bytes = resource.read_bytes()
    except (FileNotFoundError, TypeError) as exc:
        available = ", ".join(list_regions())
        raise LoaderError(f"Region '{region_name}' not found. Available: {available}") from exc

    try:
        raw_dict = tomllib.loads(raw_bytes.decode())
    except tomllib.TOMLDecodeError as exc:
        raise LoaderError(f"Failed to parse '{filename}': {exc}") from exc

    return RegionData.model_validate(raw_dict)


_NON_REGION_TOML = {"professions.toml", "professions_regelwiki.toml", "traits.toml"}


def list_regions() -> list[str]:
    """Return all region IDs derived from TOML filenames in the data package."""
    data_dir = files(_DATA_PACKAGE)
    return sorted(
        p.name.removesuffix(".toml")
        for p in data_dir.iterdir()  # type: ignore[union-attr]
        if p.name.endswith(".toml") and p.name not in _NON_REGION_TOML
    )


def load_region(region_name: str) -> RegionData:
    """Load a region by its file stem (case-insensitive)."""
    return _parse_region(region_name.lower())
