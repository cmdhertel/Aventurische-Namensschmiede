"""Generator-Routen: Startseite, Namens-Generierung, PDF-Download."""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from opentelemetry.trace import Tracer, get_tracer

from namegen.chargen import generate_character
from namegen.generator import generate
from namegen.loader import list_regions, load_region
from namegen.models import Gender, GenerationMode, ProfessionCategory
from observability import AppMetrics
from observability_utils import safe_full_name
from observability_utils import safe_full_name

router = APIRouter()

_TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).parent.parent / "templates")
)

_GENDER_DE = {
    "male": "♂ Männlich",
    "female": "♀ Weiblich",
    "any": "⚥ Beliebig",
}

_logger = logging.getLogger("namenschmiede.observability")
_tracer: Tracer = get_tracer("namenschmiede.web")
_metrics: AppMetrics | None = None

def configure_observability(
    *,
    logger: logging.Logger,
    tracer: Tracer,
    app_metrics: AppMetrics,
) -> None:
    """Wird beim App-Start aus main.py aufgerufen."""
    global _logger, _tracer, _metrics
    _logger = logger
    _tracer = tracer
    _metrics = app_metrics


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
    return _TEMPLATES.TemplateResponse(request, "index.html", {
        "regions": regions,
        "selected_region": selected,
    })


@router.post("/generate")
async def generate_names(
    request: Request,
    region: str = Form(...),
    gender: str = Form("any"),
    mode: str = Form("simple"),
    count: int = Form(5),
    character: bool = Form(False),
    profession_category: str = Form("alle"),
):
    with _tracer.start_as_current_span("namegen.generate") as span:
        count = max(1, min(count, 50))
        region_data = load_region(region)
        gmode = GenerationMode(mode)
        gend = Gender(gender)
        category = ProfessionCategory(profession_category)

        if character:
            results = [
                generate_character(
                    region=region,
                    mode=gmode,
                    gender=gend,
                    profession_category=category,
                )
                for _ in range(count)
            ]
            template = "partials/character_row.html"
            output_chars = sum(len(f"{safe_full_name(c)} {c.profession}".strip()) for c in results)
            output_chars = sum(len(f"{safe_full_name(c)} {c.profession}".strip()) for c in results)
        else:
            results = [
                generate(region=region, mode=gmode, gender=gend)
                for _ in range(count)
            ]
            template = "partials/name_row.html"
            output_chars = sum(len(safe_full_name(n)) for n in results)
            output_chars = sum(len(safe_full_name(n)) for n in results)

        input_chars = sum(len(value) for value in [region, gender, mode, profession_category])

        span.set_attribute("namegen.region", region)
        span.set_attribute("namegen.mode", mode)
        span.set_attribute("namegen.gender", gender)
        span.set_attribute("namegen.character", character)
        span.set_attribute("namegen.profession_category", profession_category)
        span.set_attribute("namegen.requested_count", count)
        span.set_attribute("namegen.input_chars", input_chars)
        span.set_attribute("namegen.output_chars", output_chars)

        if _metrics:
            attrs = {
                "namegen.region": region,
                "namegen.mode": mode,
                "namegen.gender": gender,
                "namegen.character": character,
                "namegen.profession_category": profession_category,
            }
            _metrics.generate_calls.add(1, attrs)
            _metrics.input_chars.add(input_chars, attrs)
            _metrics.output_chars.add(output_chars, attrs)

        _logger.info(
            "event=namegen.generate region=%s mode=%s gender=%s character=%s profession_category=%s count=%s input_chars=%s output_chars=%s",
            region,
            mode,
            gender,
            character,
            profession_category,
            count,
            input_chars,
            output_chars,
        )

        return _TEMPLATES.TemplateResponse(
            request,
            template,
            {
                "results": results,
                "gender_de": _GENDER_DE,
                "region_abbr": region_data.meta.abbreviation,
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
