"""PDF-Generierung für den Web-Download (in-memory, gibt bytes zurück)."""

from __future__ import annotations

from namegen.pdf_builder import build_character_pdf, build_name_pdf


def build_pdf_bytes(name_data: list[dict], kind: str = "name") -> bytes:
    """Dispatcher: routes to character or name PDF builder."""
    if kind == "character":
        return build_character_pdf(name_data) or b""
    return build_name_pdf(name_data) or b""
