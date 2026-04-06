"""FastAPI web application for DSA Namengenerator."""

import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import monotonic

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

from namegen.loader import list_regions

app = FastAPI(
    title="DSA Namengenerator",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

logger = setup_logging()
tracer = setup_telemetry()
app_metrics = build_metrics()
configure_observability(logger=logger, tracer=tracer, app_metrics=app_metrics)

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
