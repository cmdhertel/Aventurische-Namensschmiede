"""Tests for web JSON import/export helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.requests import Request

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

from result_transfer import parse_results_json  # noqa: E402
from routes.generator import import_results_json  # noqa: E402


def test_parse_results_json_supports_mixed_name_and_character_entries() -> None:
    payload = {
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

    results = parse_results_json(json.dumps(payload))

    assert len(results) == 2
    assert results[0].kind == "name"
    assert results[0].resolved_gender.value == "male"
    assert results[1].kind == "character"
    assert results[1].name.resolved_gender.value == "female"
    assert results[1].traits.physical.hair == "blond"


def test_parse_results_json_rejects_invalid_payload() -> None:
    payload = {"entries": []}

    try:
        parse_results_json(json.dumps(payload))
    except ValueError as exc:
        assert "Ungültige JSON-Datei" in str(exc)
    else:
        raise AssertionError("invalid JSON import should raise ValueError")


def _request(body: str) -> Request:
    async def receive() -> dict:
        return {"type": "http.request", "body": body.encode("utf-8"), "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/import-json",
            "headers": [],
            "query_string": b"",
        },
        receive=receive,
    )


@pytest.mark.anyio
async def test_import_json_route_renders_imported_entries() -> None:
    payload = {
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

    response = await import_results_json(_request(json.dumps(payload)))

    assert response.status_code == 200
    body = response.body.decode("utf-8")
    assert "Alrik von Gareth" in body
    assert "Linya vom Blautann" in body
    assert 'data-profession="Jägerin"' in body


@pytest.mark.anyio
async def test_import_json_route_rejects_invalid_payload() -> None:
    with pytest.raises(HTTPException) as excinfo:
        await import_results_json(_request('{"entries":[]}'))

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Ungültige Eingabe"
