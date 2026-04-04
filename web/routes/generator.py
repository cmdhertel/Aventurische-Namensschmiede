"""Generator-Routen: Startseite, Namens-Generierung, PDF-Download."""

from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

from namegen.chargen import generate_character
from namegen.generator import generate
from namegen.loader import get_origin_catalog, load_region
from namegen.models import Gender, GenerationMode, ProfessionCategory

router = APIRouter()

_TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).parent.parent / "templates")
)

_GENDER_DE = {
    "male":   "♂ Männlich",
    "female": "♀ Weiblich",
    "any":    "⚥ Beliebig",
}


def _get_origins() -> list[dict]:
    return get_origin_catalog()


@router.get("/")
async def index(
    request: Request,
    region: str | None = Query(default=None),
):
    origins = _get_origins()
    selected = region or (origins[0]["id"] if origins else "")
    return _TEMPLATES.TemplateResponse(request, "index.html", {
        "origins":         origins,
        "selected_region": selected,
    })


@router.get("/rechtliches")
async def legal_page(request: Request):
    return _TEMPLATES.TemplateResponse(request, "rechtliches.html", {})


@router.post("/generate")
async def generate_names(
    request: Request,
    region:              str  = Form(...),
    gender:              str  = Form("any"),
    mode:                str  = Form("simple"),
    count:               int  = Form(5),
    character:           bool = Form(False),
    profession_category: str  = Form("alle"),
):
    count = max(1, min(count, 50))
    region_data = load_region(region)
    gmode    = GenerationMode(mode)
    gend     = Gender(gender)
    category = ProfessionCategory(profession_category)

    if character:
        results = [
            generate_character(region=region, mode=gmode, gender=gend,
                               profession_category=category)
            for _ in range(count)
        ]
        template = "partials/character_row.html"
    else:
        results = [
            generate(region=region, mode=gmode, gender=gend)
            for _ in range(count)
        ]
        template = "partials/name_row.html"

    return _TEMPLATES.TemplateResponse(
        request, template,
        {
            "results":      results,
            "gender_de":    _GENDER_DE,
            "region_abbr":  region_data.meta.abbreviation,
            "origin_data":  region_data,
        },
    )


@router.post("/pdf")
async def download_pdf(names: str = Form(...)):
    from pdf_utils import build_pdf_bytes  # noqa: PLC0415

    name_data: list[dict] = json.loads(names)
    pdf_bytes = build_pdf_bytes(name_data)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="dsa_namen.pdf"'},
    )
