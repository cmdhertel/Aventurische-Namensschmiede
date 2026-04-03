"""Regionen-Übersicht."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from namegen.loader import list_regions, load_region

router = APIRouter(prefix="/regions")

_TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).parent.parent / "templates")
)


@router.get("")
async def regions_page(request: Request):
    regions = []
    for rid in list_regions():
        try:
            rd = load_region(rid)
            regions.append({
                "id":       rid,
                "name":     rd.meta.region,
                "notes":    rd.meta.notes,
                "language": rd.meta.language,
            })
        except Exception:
            pass
    return _TEMPLATES.TemplateResponse("regions.html", {
        "request": request,
        "regions": regions,
    })
