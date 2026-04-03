"""Generator-Routen: Startseite, Namens-Generierung, PDF-Download."""

from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

from namegen.generator import generate
from namegen.loader import list_regions, load_region
from namegen.models import Gender, GenerationMode

router = APIRouter()

_TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).parent.parent / "templates")
)

_GENDER_DE = {
    "male":   "♂ Männlich",
    "female": "♀ Weiblich",
    "any":    "⚥ Beliebig",
}


def _get_regions() -> list[dict]:
    result = []
    for rid in list_regions():
        try:
            rd = load_region(rid)
            result.append({"id": rid, "name": rd.meta.region})
        except Exception:
            pass
    return result


@router.get("/")
async def index(
    request: Request,
    region: str | None = Query(default=None),
):
    regions = _get_regions()
    selected = region or (regions[0]["id"] if regions else "")
    return _TEMPLATES.TemplateResponse("index.html", {
        "request":         request,
        "regions":         regions,
        "selected_region": selected,
    })


@router.post("/generate")
async def generate_names(
    request: Request,
    region: str = Form(...),
    gender: str = Form("any"),
    mode:   str = Form("simple"),
    count:  int = Form(5),
):
    count = max(1, min(count, 50))
    results = [
        generate(region=region, mode=GenerationMode(mode), gender=Gender(gender))
        for _ in range(count)
    ]
    return _TEMPLATES.TemplateResponse(
        "partials/name_row.html",
        {"request": request, "results": results, "gender_de": _GENDER_DE},
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
