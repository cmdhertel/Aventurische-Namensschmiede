"""FastAPI web application for DSA Namengenerator."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes.generator import router as generator_router
from routes.regions import router as regions_router

app = FastAPI(
    title="DSA Namengenerator",
    # Swagger/ReDoc ausgeblendet – später für /api/v1/ aktivierbar
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

_BASE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(_BASE / "static")), name="static")

app.include_router(generator_router)
app.include_router(regions_router)


@app.get("/health", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok"}
