"""Tests for web app docs, favourites page, and ZIP export."""

from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import pytest
from starlette.requests import Request

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

from export_bundle import build_export_zip  # noqa: E402
from main import app  # noqa: E402
from result_transfer import load_results_export  # noqa: E402
from routes.generator import favourites_page  # noqa: E402


def test_fastapi_docs_are_enabled() -> None:
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"
    assert app.openapi_url == "/openapi.json"


def test_build_export_zip_contains_expected_files() -> None:
    export = load_results_export(
        json.dumps(
            {
                "format": "namenschmiede-results",
                "version": 1,
                "entries": [
                    {
                        "kind": "name",
                        "full_name": "Alrik von Gareth",
                        "gender": "male",
                        "region": "Garetien",
                        "culture": "Mittelreicher",
                        "species": "Mensch",
                        "region_abbr": "GAR",
                        "mode": "simple",
                    },
                    {
                        "kind": "character",
                        "full_name": "Linya vom Blautann",
                        "gender": "female",
                        "region": "Nostria",
                        "culture": "Nostrier",
                        "species": "Mensch",
                        "region_abbr": "NOS",
                        "mode": "simple",
                        "age": 27,
                        "profession": "Jägerin",
                        "hair": "blond",
                        "eyes": "grün",
                        "build": "schlank",
                        "personality": "wachsam",
                        "motivation": "Schulden begleichen",
                        "quirk": "spricht mit Krähen",
                    },
                ],
            }
        )
    )

    zip_bytes = build_export_zip(export)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = set(zf.namelist())
        assert "namenschmiede_results.json" in names
        assert "namen.csv" in names
        assert "namen.pdf" in names
        assert "charaktere.csv" in names
        assert "charaktere.pdf" in names


def _request() -> Request:
    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/favourites",
            "headers": [],
            "query_string": b"",
        },
        receive=receive,
    )


@pytest.mark.anyio
async def test_favourites_page_renders() -> None:
    response = await favourites_page(_request())
    assert response.status_code == 200
    body = response.body.decode("utf-8")
    assert "Favoritenliste" in body
    assert "localStorage" in body
