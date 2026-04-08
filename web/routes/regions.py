"""Regionen-Übersicht."""

from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from seo import build_seo_meta

from namegen.loader import list_regions, load_region

router = APIRouter(prefix="/regions")

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
_logger = structlog.get_logger("namenschmiede.regions")


@router.get("")
async def regions_page(request: Request):
    regions = []
    for rid in list_regions():
        try:
            rd = load_region(rid)
            regions.append(
                {
                    "id": rid,
                    "name": rd.meta.region,
                    "notes": rd.meta.notes,
                    "language": rd.meta.language,
                }
            )
        except Exception:
            _logger.warning("regions.load.failed", region_id=rid, exc_info=True)
    return _TEMPLATES.TemplateResponse(
        request,
        "regions.html",
        {
            "regions": regions,
            "seo_meta": build_seo_meta(
                title="DSA Regionen und Kulturen – Aventurische Namensschmiede",
                description=(
                    "Regionenuebersicht mit DSA-Kulturen und aventurischen "
                    "Regionen fuer Fantasy-Namensgenerator und "
                    "Charaktergenerator."
                ),
                path="/regions",
            ),
        },
    )
