"""Pure helper functions for observability logic."""

from __future__ import annotations


def safe_full_name(value: object) -> str:
    """Read full name defensively from NameResult/CharacterResult-like objects."""
    full_name = getattr(value, "full_name", None)
    if isinstance(full_name, str) and full_name:
        return full_name

    first_name = getattr(value, "first_name", getattr(value, "first", ""))
    last_name = getattr(value, "last_name", getattr(value, "last", ""))
    return f"{first_name} {last_name}".strip()


def name_length(value: object) -> int:
    """Return non-negative name length for NameResult-like objects."""
    return max(0, len(safe_full_name(value)))


def count_empty_names(values: list[object]) -> int:
    """Count results without a usable full name."""
    return sum(1 for item in values if not safe_full_name(item))
