"""FastAPI web application for DSA Namengenerator."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from observability import (
    create_metrics_middleware,
    instrument_fastapi,
    setup_logging,
    setup_telemetry,
)
from routes.generator import configure_observability, router as generator_router
from routes.regions import router as regions_router

app = FastAPI(
    title="DSA Namengenerator",
    # Swagger/ReDoc ausgeblendet – später für /api/v1/ aktivierbar
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

logger = setup_logging()
tracer, app_metrics = setup_telemetry()
configure_observability(logger=logger, tracer=tracer, app_metrics=app_metrics)

app.middleware("http")(create_metrics_middleware(logger=logger, app_metrics=app_metrics))
instrument_fastapi(app, logger=logger)

_BASE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(_BASE / "static")), name="static")

app.include_router(generator_router)
app.include_router(regions_router)


@app.get("/health", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok"}
