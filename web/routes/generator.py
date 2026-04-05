"""Generator-Routen: Startseite, Namens-Generierung, PDF- und JSON-Import."""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from time import perf_counter

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from observability import AppMetrics
from observability_utils import count_empty_names, name_length, safe_full_name
from opentelemetry.trace import Tracer, get_tracer
from result_transfer import parse_results_json

from namegen.chargen import generate_character
from namegen.generator import generate
from namegen.loader import (
    get_origin_catalog,
    resolve_generation_targets,
    selection_supports_compose,
)
from namegen.models import Gender, GenerationMode, ProfessionCategory

router = APIRouter()

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

_GENDER_DE = {
    "male": "♂ Männlich",
    "female": "♀ Weiblich",
    "any": "⚥ Beliebig",
}

_logger = logging.getLogger("namenschmiede.observability")
_tracer: Tracer = get_tracer("namenschmiede.web")
_metrics: AppMetrics | None = None
_TRUE_FORM_VALUES = {"1", "true", "on", "yes"}


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


def _get_origins() -> list[dict]:
    return get_origin_catalog()


def _parse_checkbox_value(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in _TRUE_FORM_VALUES


def _default_selected_region(origins: list[dict]) -> str:
    for entry in origins:
        if entry["id"] == "human":
            return entry["id"]
    for entry in origins:
        if entry.get("species_id") == "human":
            return entry["id"]
    return origins[0]["id"] if origins else ""


@router.get("/")
async def index(
    request: Request,
    region: str | None = Query(default=None),
):
    origins = _get_origins()
    selected = region or _default_selected_region(origins)
    return _TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "origins": origins,
            "selected_region": selected,
            "compose_default_enabled": selection_supports_compose(selected),
        },
    )


@router.get("/rechtliches")
async def legal_page(request: Request):
    return _TEMPLATES.TemplateResponse(request, "rechtliches.html", {})


@router.post("/generate")
async def generate_names(
    request: Request,
    region: str = Form(...),
    gender: str = Form("any"),
    mode: str = Form("simple"),
    count: int = Form(5),
    character: str | None = Form(None),
    profession_category: str = Form("alle"),
):
    with _tracer.start_as_current_span("namegen.generate") as span:
        count = max(1, min(count, 50))
        character_enabled = _parse_checkbox_value(character)

        attrs = {
            "namegen.region": region,
            "namegen.mode": mode,
            "namegen.gender": gender,
            "namegen.character": character_enabled,
            "namegen.profession_category": profession_category,
        }

        load_start = perf_counter()
        try:
            resolve_generation_targets(region, compose_only=mode == "compose")
            gmode = GenerationMode(mode)
            gend = Gender(gender)
            category = ProfessionCategory(profession_category)
        except ValueError as exc:
            span.set_attribute("error.kind", "validation")
            span.set_attribute("validation.phase", "input")
            span.record_exception(exc)
            raise
        except Exception as exc:
            span.set_attribute("error.kind", "load_region")
            span.set_attribute("validation.phase", "region")
            span.record_exception(exc)
            raise
        finally:
            if _metrics:
                _metrics.load_region_duration_ms.record((perf_counter() - load_start) * 1000, attrs)

        generate_start = perf_counter()
        if character_enabled:
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
        else:
            results = [generate(region=region, mode=gmode, gender=gend) for _ in range(count)]
            template = "partials/name_row.html"
            output_chars = sum(len(safe_full_name(n)) for n in results)

        generate_elapsed_ms = (perf_counter() - generate_start) * 1000

        input_chars = sum(len(value) for value in [region, gender, mode, profession_category])
        empty_results = count_empty_names(results)

        span.set_attribute("namegen.region", region)
        span.set_attribute("namegen.mode", mode)
        span.set_attribute("namegen.gender", gender)
        span.set_attribute("namegen.character", character_enabled)
        span.set_attribute("namegen.profession_category", profession_category)
        span.set_attribute("namegen.requested_count", count)
        span.set_attribute("namegen.input_chars", input_chars)
        span.set_attribute("namegen.output_chars", output_chars)
        span.set_attribute("namegen.empty_results", empty_results)

        if _metrics:
            _metrics.generate_calls.add(1, attrs)
            _metrics.input_chars.add(input_chars, attrs)
            _metrics.output_chars.add(output_chars, attrs)
            _metrics.generate_loop_duration_ms.record(generate_elapsed_ms, attrs)
            _metrics.empty_results.add(empty_results, attrs)
            for entry in results:
                _metrics.name_length.record(name_length(entry), attrs)

        if count > 0 and (empty_results / count) > 0.1:
            _logger.warning(
                "event=namegen.data_quality.warning region=%s mode=%s"
                " character=%s empty_ratio=%.2f",
                region,
                mode,
                character_enabled,
                empty_results / count,
            )

        _logger.info(
            "event=namegen.generate region=%s mode=%s gender=%s"
            " character=%s profession_category=%s count=%s"
            " input_chars=%s output_chars=%s empty_results=%s",
            region,
            mode,
            gender,
            character_enabled,
            profession_category,
            count,
            input_chars,
            output_chars,
            empty_results,
        )

        render_start = perf_counter()
        response = _TEMPLATES.TemplateResponse(
            request,
            template,
            {
                "results": results,
                "gender_de": _GENDER_DE,
            },
        )

        if _metrics:
            _metrics.template_render_duration_ms.record(
                (perf_counter() - render_start) * 1000, attrs
            )

        return response


@router.post("/pdf")
async def download_pdf(names: str = Form(...)):
    from pdf_utils import build_pdf_bytes  # noqa: PLC0415

    with _tracer.start_as_current_span("namegen.pdf.build") as span:
        name_data: list[dict] = json.loads(names)
        span.set_attribute("namegen.pdf.names_count", len(name_data))

        start = perf_counter()
        pdf_bytes = build_pdf_bytes(name_data)
        elapsed_ms = (perf_counter() - start) * 1000

        if _metrics:
            _metrics.pdf_duration_ms.record(elapsed_ms, {"route": "/pdf"})

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="dsa_namen.pdf"'},
        )


@router.post("/import-json", response_class=HTMLResponse)
async def import_results_json(request: Request):
    payload = (await request.body()).decode("utf-8")
    try:
        results = parse_results_json(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _TEMPLATES.TemplateResponse(
        request,
        "partials/imported_rows.html",
        {
            "results": results,
            "gender_de": _GENDER_DE,
        },
    )
