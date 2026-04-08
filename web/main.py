"""FastAPI web application for DSA Namengenerator."""

import os
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import monotonic

from auth import basic_auth_middleware
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from metrics import build_metrics
from observability import (
    create_metrics_middleware,
    instrument_fastapi,
    setup_logging,
    setup_telemetry,
)
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from routes.generator import configure_observability
from routes.generator import router as generator_router
from routes.regions import router as regions_router
from seo import site_origin_for_robots

from namegen.loader import list_regions


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


_docs_enabled = _env_flag("APP_ENABLE_API_DOCS", default=True)

app = FastAPI(
    title="DSA Namengenerator",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)

logger = setup_logging()
tracer = setup_telemetry()
app_metrics = build_metrics()
configure_observability(logger=logger, tracer=tracer, app_metrics=app_metrics)

app.middleware("http")(basic_auth_middleware)
app.middleware("http")(create_metrics_middleware(logger=logger, app_metrics=app_metrics))
instrument_fastapi(app, logger=logger)
Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics", "/static"],
).instrument(app)

_BASE = Path(__file__).parent
_START_TIME = monotonic()
app.mount("/static", StaticFiles(directory=str(_BASE / "static")), name="static")

app.include_router(generator_router)
app.include_router(regions_router)


@app.get("/health", include_in_schema=False)
async def health() -> dict:
    try:
        app_version = version("dsa-namegen")
    except PackageNotFoundError:
        app_version = "0.1.0"

    return {
        "status": "ok",
        "version": app_version,
        "regions_loaded": len(list_regions()),
        "uptime_s": int(monotonic() - _START_TIME),
        "python_version": platform.python_version(),
    }


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt() -> Response:
    site_root = site_origin_for_robots()
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /docs",
            "Disallow: /redoc",
            "Disallow: /openapi.json",
            "",
            f"Sitemap: {site_root}/sitemap.xml",
            "",
        ]
    )
    return Response(content, media_type="text/plain; charset=utf-8")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml() -> Response:
    base_url = site_origin_for_robots()
    urls = [
        f"{base_url}/",
        f"{base_url}/regions",
        f"{base_url}/favourites",
        f"{base_url}/impressum",
        f"{base_url}/datenschutz",
    ]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append("    <changefreq>weekly</changefreq>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return Response("\n".join(lines), media_type="application/xml")
