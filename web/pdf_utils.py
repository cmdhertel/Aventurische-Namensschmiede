"""PDF-Generierung für den Web-Download (in-memory, gibt bytes zurück)."""

from __future__ import annotations

from result_transfer import CharacterExportEntry, NameExportEntry, ResultsExport

from namegen.pdf_builder import build_character_pdf, build_mixed_pdf, build_name_pdf


def build_pdf_bytes(name_data: list[dict], kind: str = "name") -> bytes:
    """Dispatcher: routes to character or name PDF builder."""
    if kind == "character":
        return build_character_pdf(name_data) or b""
    return build_name_pdf(name_data) or b""


def build_export_pdf_bytes(export: ResultsExport) -> tuple[bytes, str]:
    """Build a PDF from a mixed export envelope and return bytes plus filename."""
    names = [entry for entry in export.entries if isinstance(entry, NameExportEntry)]
    characters = [entry for entry in export.entries if isinstance(entry, CharacterExportEntry)]

    if names and characters:
        pdf_bytes = build_mixed_pdf(
            _names_for_pdf(names),
            _characters_for_pdf(characters),
        ) or b""
        return pdf_bytes, "dsa_export.pdf"
    if characters:
        return (
            build_character_pdf(_characters_for_pdf(characters)) or b"",
            "dsa_charaktere.pdf",
        )
    return build_name_pdf(_names_for_pdf(names)) or b"", "dsa_namen.pdf"


def _names_for_pdf(entries: list[NameExportEntry]) -> list[dict]:
    return [
        {
            "full_name": entry.full_name,
            "gender": entry.gender,
            "region": entry.region,
            "region_abbr": entry.region_abbr or "",
            "mode": entry.mode,
        }
        for entry in entries
    ]


def _characters_for_pdf(entries: list[CharacterExportEntry]) -> list[dict]:
    return [
        {
            "full_name": entry.full_name,
            "gender": entry.gender,
            "region": entry.region,
            "region_abbr": entry.region_abbr or "",
            "age": entry.age,
            "profession": entry.profession,
            "hair": entry.hair,
            "eyes": entry.eyes,
            "build": entry.build,
            "personality": entry.personality,
            "motivation": entry.motivation,
            "quirk": entry.quirk,
        }
        for entry in entries
    ]
