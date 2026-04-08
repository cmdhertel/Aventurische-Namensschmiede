"""ZIP export helpers for web-generated result sets."""

from __future__ import annotations

import csv
import io
import json
import zipfile

from pdf_utils import build_pdf_bytes
from result_transfer import CharacterExportEntry, NameExportEntry, ResultsExport

from namegen.pdf_builder import derive_region_abbr


def build_export_zip(export: ResultsExport) -> bytes:
    """Build an in-memory ZIP with JSON plus CSV/PDF artifacts."""
    names = [entry for entry in export.entries if isinstance(entry, NameExportEntry)]
    characters = [entry for entry in export.entries if isinstance(entry, CharacterExportEntry)]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "namenschmiede_results.json",
            json.dumps(export.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        )

        if names:
            zf.writestr("namen.csv", _names_to_csv(names))
            zf.writestr("namen.pdf", build_pdf_bytes(_names_for_pdf(names), kind="name"))

        if characters:
            zf.writestr("charaktere.csv", _characters_to_csv(characters))
            zf.writestr(
                "charaktere.pdf",
                build_pdf_bytes(_characters_for_pdf(characters), kind="character"),
            )

    return buf.getvalue()


def _names_to_csv(entries: list[NameExportEntry]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=[
            "full_name",
            "gender",
            "species",
            "culture",
            "region",
            "region_abbr",
            "mode",
        ],
    )
    writer.writeheader()
    for entry in entries:
        writer.writerow(entry.model_dump(mode="json", exclude={"kind"}))
    return buf.getvalue()


def _characters_to_csv(entries: list[CharacterExportEntry]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=[
            "full_name",
            "gender",
            "species",
            "culture",
            "region",
            "region_abbr",
            "mode",
            "age",
            "profession",
            "hair",
            "eyes",
            "build",
            "personality",
            "motivation",
            "quirk",
        ],
    )
    writer.writeheader()
    for entry in entries:
        writer.writerow(entry.model_dump(mode="json", exclude={"kind"}))
    return buf.getvalue()


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
            "region_abbr": entry.region_abbr or derive_region_abbr(entry.region, entry.region_abbr),
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
