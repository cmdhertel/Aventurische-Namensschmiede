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
