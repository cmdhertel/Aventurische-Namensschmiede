"""Integration tests for health, metrics, and structured web observability."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

os.environ.setdefault("OTEL_EXPORT_TO_CONSOLE", "0")

import routes.regions as regions_module  # noqa: E402
from main import app  # noqa: E402
from observability import _route_template, _status_class  # noqa: E402
from routes.generator import download_pdf  # noqa: E402

from namegen.loader import list_regions  # noqa: E402


def test_status_class_helper() -> None:
    assert _status_class(200) == "2xx"
    assert _status_class(404) == "4xx"
    assert _status_class(503) == "5xx"


def test_route_template_helper_knows_metrics_and_unknown_paths() -> None:
    assert _route_template("/metrics") == "/metrics"
    assert _route_template("/static/app.css") == "/static"
    assert _route_template("/totally-unknown") == "unknown"


def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.mark.anyio
async def test_health_returns_observability_metadata() -> None:
    async with _client() as client:
        response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"] == "0.1.0"
    assert payload["regions_loaded"] == len(list_regions())
    assert payload["uptime_s"] >= 0
    assert re.fullmatch(r"\d+\.\d+\.\d+", payload["python_version"])


@pytest.mark.anyio
async def test_robots_txt_and_sitemap_xml_are_public_and_advertise_site() -> None:
    old_password = os.environ.get("APP_BASIC_AUTH_PASSWORD")
    os.environ["APP_BASIC_AUTH_PASSWORD"] = "secret-pass"
    try:
        async with _client() as client:
            robots_response = await client.get("/robots.txt")
            sitemap_response = await client.get("/sitemap.xml")
    finally:
        if old_password is None:
            os.environ.pop("APP_BASIC_AUTH_PASSWORD", None)
        else:
            os.environ["APP_BASIC_AUTH_PASSWORD"] = old_password

    assert robots_response.status_code == 200
    assert "Sitemap: https://aventurische-namensschmiede.de/sitemap.xml" in robots_response.text
    assert sitemap_response.status_code == 200
    assert "<loc>https://aventurische-namensschmiede.de/regions</loc>" in sitemap_response.text
    assert "<loc>https://aventurische-namensschmiede.de/datenschutz</loc>" in sitemap_response.text
    assert "<loc>https://aventurische-namensschmiede.de/impressum</loc>" in sitemap_response.text


@pytest.mark.anyio
async def test_metrics_endpoint_exposes_http_and_namegen_metrics() -> None:
    async with _client() as client:
        await client.get("/health")
        await client.post(
            "/generate",
            data={
                "region": "human",
                "gender": "any",
                "mode": "simple",
                "count": "2",
                "profession_category": "alle",
            },
        )
        response = await client.get("/metrics")

    assert response.status_code == 200
    body = response.text
    assert "http_server_request_count_total" in body
    assert "http_server_active_requests" in body
    assert 'http_server_request_count_total{http_method="GET",http_route="/health"' in body
    assert (
        'namegen_generate_count_total{namegen_character="false",'
        'namegen_gender="any",namegen_mode="simple",'
        'namegen_profession_category="alle",namegen_profession_theme="none",'
        'namegen_region="human"}'
    ) in body
    assert "namegen_template_render_duration_ms_milliseconds_bucket" in body


@pytest.mark.anyio
async def test_generate_character_path_and_pdf_metric_are_exposed() -> None:
    async with _client() as client:
        generate_response = await client.post(
            "/generate",
            data={
                "region": "mittelreich_perricum",
                "gender": "female",
                "mode": "simple",
                "count": "1",
                "character": "on",
                "profession_category": "zauberer",
                "profession_theme": "graumagier_aus_perricum",
            },
        )
        assert generate_response.status_code == 200
        assert "name-entry" in generate_response.text

        pdf_response = await download_pdf(
            names=json.dumps(
                [
                    {
                        "full_name": "Alrik von Gareth",
                        "gender": "male",
                        "region": "Garetien",
                        "culture": "Mittelreicher",
                        "species": "Mensch",
                        "region_abbr": "GAR",
                        "mode": "simple",
                    }
                ]
            ),
            kind="name",
        )
        assert pdf_response.status_code == 200

        metrics_body = (await client.get("/metrics")).text

    assert (
        'namegen_generate_count_total{namegen_character="true",'
        'namegen_gender="female",namegen_mode="simple",'
        'namegen_profession_category="zauberer",'
        'namegen_profession_theme="graumagier_aus_perricum",namegen_region="mittelreich_perricum"}'
    ) in metrics_body
    assert "namegen_pdf_duration_ms_milliseconds_bucket" in metrics_body


@pytest.mark.anyio
async def test_pdf_route_supports_mixed_export_payload() -> None:
    payload = json.dumps(
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

    response = await download_pdf(payload=payload)

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="dsa_export.pdf"'


@pytest.mark.anyio
async def test_request_id_header_is_forwarded_and_logs_are_json(caplog) -> None:
    caplog.set_level(logging.INFO)

    async with _client() as client:
        response = await client.get("/health", headers={"x-request-id": "req-123"})

    assert response.headers["X-Request-ID"] == "req-123"
    log_lines = [record.message for record in caplog.records if record.message.strip()]
    request_log = next(
        json.loads(line) for line in reversed(log_lines) if '"event": "http.request"' in line
    )
    assert request_log["request_id"] == "req-123"
    assert request_log["path"] == "/health"
    assert request_log["route"] == "/health"
    assert request_log["status_code"] == 200


@pytest.mark.anyio
async def test_generate_request_log_includes_form_region(caplog) -> None:
    caplog.set_level(logging.INFO)

    async with _client() as client:
        response = await client.post(
            "/generate",
            data={
                "region": "human",
                "gender": "any",
                "mode": "simple",
                "count": "1",
                "profession_category": "alle",
            },
        )

    assert response.status_code == 200
    log_lines = [record.message for record in caplog.records if record.message.strip()]
    request_log = next(
        json.loads(line)
        for line in reversed(log_lines)
        if '"event": "http.request"' in line and '"path": "/generate"' in line
    )
    assert request_log["region"] == "human"


@pytest.mark.anyio
async def test_request_error_records_metrics_and_structured_log(caplog) -> None:
    caplog.set_level(logging.INFO)

    if not any(route.path == "/_boom" for route in app.router.routes):

        @app.get("/_boom")  # type: ignore[misc]
        async def _boom() -> dict:
            raise RuntimeError("boom")

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/_boom")
        metrics_body = (await client.get("/metrics")).text

    assert response.status_code == 500
    assert (
        'app_errors_count_total{error_type="RuntimeError",'
        'http_method="GET",http_route="unknown",http_status_class="5xx"}'
    ) in metrics_body
    log_lines = [record.message for record in caplog.records if record.message.strip()]
    error_log = next(
        json.loads(line) for line in reversed(log_lines) if '"event": "http.request.error"' in line
    )
    assert error_log["path"] == "/_boom"
    assert error_log["status_code"] == 500
    assert error_log["error_type"] == "RuntimeError"


@pytest.mark.anyio
async def test_import_json_rejects_invalid_payload() -> None:
    async with _client() as client:
        response = await client.post("/import-json", content="not valid json")

    assert response.status_code == 400
    assert "Ungültige Eingabe" in response.text


@pytest.mark.anyio
async def test_export_zip_rejects_invalid_payload() -> None:
    async with _client() as client:
        response = await client.post("/export/zip", content="still not json")

    assert response.status_code == 400
    assert "Ungültige Eingabe" in response.text


@pytest.mark.anyio
async def test_generate_rejects_invalid_mode_with_server_error() -> None:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/generate",
            data={
                "region": "human",
                "gender": "any",
                "mode": "invalid",
                "count": "1",
                "profession_category": "alle",
            },
        )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_regions_page_skips_unloadable_region(monkeypatch) -> None:
    def fake_list_regions() -> list[str]:
        return ["nostria", "broken"]

    class _Meta:
        region = "Nostria"
        notes = "Nordwesten"
        language = "Bosparano"

    class _Region:
        meta = _Meta()

    def fake_load_region(region_id: str):
        if region_id == "broken":
            raise ValueError("bad region")
        return _Region()

    monkeypatch.setattr(regions_module, "list_regions", fake_list_regions)
    monkeypatch.setattr(regions_module, "load_region", fake_load_region)

    async with _client() as client:
        response = await client.get("/regions")

    assert response.status_code == 200
    assert "Nostria" in response.text
    assert "broken" not in response.text
