"""Tests for web app docs, favourites page, and ZIP export."""

from __future__ import annotations

import io
import json
import os
import sys
import zipfile
from base64 import b64encode
from pathlib import Path

import httpx
import pytest
from starlette.requests import Request

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

from export_bundle import build_export_zip  # noqa: E402
import main as main_module  # noqa: E402
from result_transfer import load_results_export  # noqa: E402
from routes.generator import favourites_page, index  # noqa: E402

app = main_module.app


def test_fastapi_docs_are_enabled() -> None:
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"
    assert app.openapi_url == "/openapi.json"


def test_env_flag_can_disable_api_docs(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENABLE_API_DOCS", "0")
    assert main_module._env_flag("APP_ENABLE_API_DOCS", default=True) is False


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


@pytest.mark.anyio
async def test_index_page_renders_profession_preview_payload() -> None:
    response = await index(_request(), region="mittelreich_perricum")
    assert response.status_code == 200
    body = response.body.decode("utf-8")
    assert "profession-preview-map" in body
    assert "character-preview-panel" in body
    assert "Graumagier aus Perricum" in body
    assert "Thema/Gruppe" not in body


def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


def _basic_auth_header(username: str, password: str) -> dict[str, str]:
    token = b64encode(f"{username}:{password}".encode()).decode("ascii")
    return {"Authorization": f"Basic {token}"}


@pytest.mark.anyio
async def test_web_app_requires_basic_auth_when_password_is_configured(monkeypatch) -> None:
    old_password = os.environ.get("APP_BASIC_AUTH_PASSWORD")
    old_username = os.environ.get("APP_BASIC_AUTH_USERNAME")
    monkeypatch.setenv("APP_BASIC_AUTH_PASSWORD", "secret-pass")
    monkeypatch.setenv("APP_BASIC_AUTH_USERNAME", "gm")

    try:
        async with _client() as client:
            blocked = await client.get("/")
            health = await client.get("/health")
            allowed = await client.get("/", headers=_basic_auth_header("gm", "secret-pass"))
    finally:
        if old_password is None:
            monkeypatch.delenv("APP_BASIC_AUTH_PASSWORD", raising=False)
        else:
            monkeypatch.setenv("APP_BASIC_AUTH_PASSWORD", old_password)
        if old_username is None:
            monkeypatch.delenv("APP_BASIC_AUTH_USERNAME", raising=False)
        else:
            monkeypatch.setenv("APP_BASIC_AUTH_USERNAME", old_username)

    assert blocked.status_code == 401
    assert blocked.headers["www-authenticate"].startswith("Basic")
    assert health.status_code == 200
    assert allowed.status_code == 200


@pytest.mark.anyio
async def test_web_app_accepts_non_ascii_basic_auth_credentials(monkeypatch) -> None:
    old_password = os.environ.get("APP_BASIC_AUTH_PASSWORD")
    old_username = os.environ.get("APP_BASIC_AUTH_USERNAME")
    monkeypatch.setenv("APP_BASIC_AUTH_PASSWORD", "pässwort")
    monkeypatch.setenv("APP_BASIC_AUTH_USERNAME", "jörg")

    try:
        async with _client() as client:
            response = await client.get("/", headers=_basic_auth_header("jörg", "pässwort"))
    finally:
        if old_password is None:
            monkeypatch.delenv("APP_BASIC_AUTH_PASSWORD", raising=False)
        else:
            monkeypatch.setenv("APP_BASIC_AUTH_PASSWORD", old_password)
        if old_username is None:
            monkeypatch.delenv("APP_BASIC_AUTH_USERNAME", raising=False)
        else:
            monkeypatch.setenv("APP_BASIC_AUTH_USERNAME", old_username)

    assert response.status_code == 200
