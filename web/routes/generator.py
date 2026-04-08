"""Generator-Routen: Startseite, Namens-Generierung und Web-Exporte."""

from __future__ import annotations

import io
import json
from pathlib import Path
from time import perf_counter

import structlog
from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from metrics import AppMetrics
from observability_utils import count_empty_names, name_length, safe_full_name
from opentelemetry.trace import Tracer, get_tracer
from result_transfer import load_results_export, parse_results_json
from seo import build_seo_meta

from namegen.catalog import (
    get_origin_catalog,
    resolve_generation_targets,
    selection_supports_compose,
)
from namegen.chargen import (
    generate_character,
    get_profession_preview_for_selection,
)
from namegen.generator import generate
from namegen.models import Gender, GenerationMode, ProfessionCategory

router = APIRouter()

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

_GENDER_DE = {
    "male": "♂ Männlich",
    "female": "♀ Weiblich",
    "any": "⚥ Beliebig",
}

_logger = structlog.get_logger("namenschmiede.observability")
_tracer: Tracer = get_tracer("namenschmiede.web")
_metrics: AppMetrics | None = None
_TRUE_FORM_VALUES = {"1", "true", "on", "yes"}


def configure_observability(
    *,
    logger,
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


def _profession_preview_map_for_origins(origins: list[dict]) -> dict[str, dict]:
    return {
        origin["id"]: {
            category.value: get_profession_preview_for_selection(
                origin["id"], category=category
            ).model_dump(mode="json")
            for category in ProfessionCategory
        }
        for origin in origins
    }


def _page_context(*, seo_title: str, seo_description: str, path: str) -> dict[str, object]:
    return {
        "seo_meta": build_seo_meta(
            title=seo_title,
            description=seo_description,
            path=path,
        )
    }


@router.get("/")
async def index(
    request: Request,
    region: str | None = Query(default=None),
):
    origins = _get_origins()
    selected = region or _default_selected_region(origins)
    context = {
        "origins": origins,
        "selected_region": selected,
        "compose_default_enabled": selection_supports_compose(selected),
        "profession_preview_map": _profession_preview_map_for_origins(origins),
    }
    context.update(
        _page_context(
            seo_title="DSA Namensgenerator Fantasy – Aventurische Namensschmiede",
            seo_description=(
                "DSA Namensgenerator fuer Das Schwarze Auge: Fantasy-Namen, "
                "regionale Varianten und einfache Charaktere fuer Aventurien "
                "und Pen-and-Paper-Rollenspiel direkt im Browser erzeugen."
            ),
            path="/",
        )
    )
    return _TEMPLATES.TemplateResponse(
        request,
        "index.html",
        context,
    )


@router.get("/rechtliches")
@router.get("/impressum")
async def legal_page(request: Request):
    return _TEMPLATES.TemplateResponse(
        request,
        "rechtliches.html",
        _page_context(
            seo_title="Impressum – Aventurische Namensschmiede",
            seo_description=(
                "Impressum und rechtliche Hinweise zur Aventurischen "
                "Namensschmiede, dem DSA Fantasy-Namensgenerator fuer Das "
                "Schwarze Auge."
            ),
            path="/impressum",
        ),
    )


@router.get("/datenschutz")
async def privacy_page(request: Request):
    return _TEMPLATES.TemplateResponse(
        request,
        "datenschutz.html",
        _page_context(
            seo_title="Datenschutz – Aventurische Namensschmiede",
            seo_description=(
                "Datenschutzerklaerung der Aventurischen Namensschmiede mit "
                "Hinweisen zu Server-Logs und technischen Betriebsdaten des "
                "DSA Fantasy-Namensgenerators."
            ),
            path="/datenschutz",
        ),
    )


@router.get("/favourites")
async def favourites_page(request: Request):
    return _TEMPLATES.TemplateResponse(
        request,
        "favourites.html",
        _page_context(
            seo_title="DSA Favoriten und Namenlisten – Aventurische Namensschmiede",
            seo_description=(
                "Gespeicherte Favoriten der Aventurischen Namensschmiede: lokal "
                "im Browser verwaltete DSA-Namen, Fantasy-Namen und Charaktere "
                "erneut laden und exportieren."
            ),
            path="/favourites",
        ),
    )


@router.post("/generate")
async def generate_names(
    request: Request,
    region: str = Form(...),
    gender: str = Form("any"),
    mode: str = Form("simple"),
    count: int = Form(5),
    character: str | None = Form(None),
    profession_category: str = Form("alle"),
    profession_theme: str = Form(""),
):
    with _tracer.start_as_current_span("namegen.generate") as span:
        count = max(1, min(count, 50))
        character_enabled = _parse_checkbox_value(character)
        normalized_theme = profession_theme.strip()

        labels = {
            "namegen_region": region,
            "namegen_mode": mode,
            "namegen_gender": gender,
            "namegen_character": str(character_enabled).lower(),
            "namegen_profession_category": profession_category,
            "namegen_profession_theme": normalized_theme or "none",
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
            raise HTTPException(status_code=422, detail="Ungültige Parameter") from exc
        except Exception as exc:
            span.set_attribute("error.kind", "load_region")
            span.set_attribute("validation.phase", "region")
            span.record_exception(exc)
            raise
        finally:
            if _metrics:
                _metrics.load_region_duration_ms.labels(**labels).observe(
                    (perf_counter() - load_start) * 1000
                )

        generate_start = perf_counter()
        if character_enabled:
            results = [
                generate_character(
                    region=region,
                    mode=gmode,
                    gender=gend,
                    profession_category=category,
                    profession_theme=normalized_theme or None,
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

        input_chars = sum(
            len(value) for value in [region, gender, mode, profession_category, normalized_theme]
        )
        empty_results = count_empty_names(results)

        span_attrs = {
            "namegen.region": region,
            "namegen.mode": mode,
            "namegen.gender": gender,
            "namegen.character": character_enabled,
            "namegen.profession_category": profession_category,
            "namegen.profession_theme": normalized_theme,
            "namegen.requested_count": count,
            "namegen.input_chars": input_chars,
            "namegen.output_chars": output_chars,
            "namegen.empty_results": empty_results,
        }
        span_attrs.update(
            {
                "request.id": request.headers.get("x-request-id", ""),
            }
        )
        span.set_attributes(span_attrs)

        if _metrics:
            _metrics.generate_calls.labels(**labels).inc()
            _metrics.input_chars.labels(**labels).inc(input_chars)
            _metrics.output_chars.labels(**labels).inc(output_chars)
            _metrics.generate_loop_duration_ms.labels(**labels).observe(generate_elapsed_ms)
            _metrics.empty_results.labels(**labels).inc(empty_results)
            for entry in results:
                _metrics.name_length.labels(**labels).observe(name_length(entry))

        if count > 0 and (empty_results / count) > 0.1:
            _logger.warning(
                "namegen.data_quality.warning",
                region=region,
                mode=mode,
                character=character_enabled,
                empty_ratio=round(empty_results / count, 2),
            )

        _logger.info(
            "namegen.generate",
            region=region,
            mode=mode,
            gender=gender,
            character=character_enabled,
            profession_category=profession_category,
            profession_theme=normalized_theme or None,
            count=count,
            input_chars=input_chars,
            output_chars=output_chars,
            empty_results=empty_results,
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
            _metrics.template_render_duration_ms.labels(**labels).observe(
                (perf_counter() - render_start) * 1000
            )

        return response


@router.post("/pdf")
async def download_pdf(
    payload: str | None = Form(default=None),
    names: str | None = Form(default=None),
    kind: str = Form("name"),
):
    from pdf_utils import build_export_pdf_bytes, build_pdf_bytes  # noqa: PLC0415

    with _tracer.start_as_current_span("namegen.pdf.build") as span:
        payload_value = payload if isinstance(payload, str) else None
        names_value = names if isinstance(names, str) else None
        kind_value = kind if isinstance(kind, str) else "name"

        start = perf_counter()
        if payload_value is not None:
            try:
                export = load_results_export(payload_value)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            span.set_attribute("namegen.pdf.names_count", len(export.entries))
            has_names = any(entry.kind == "name" for entry in export.entries)
            has_characters = any(entry.kind == "character" for entry in export.entries)
            export_kind = (
                "mixed"
                if has_names and has_characters
                else ("character" if has_characters else "name")
            )
            span.set_attribute("namegen.pdf.kind", export_kind)
            pdf_bytes, filename = build_export_pdf_bytes(export)
        else:
            name_data: list[dict] = json.loads(names_value or "[]")
            span.set_attribute("namegen.pdf.names_count", len(name_data))
            span.set_attribute("namegen.pdf.kind", kind_value)
            pdf_bytes = build_pdf_bytes(name_data, kind=kind_value)
            filename = "dsa_charaktere.pdf" if kind_value == "character" else "dsa_namen.pdf"
        elapsed_ms = (perf_counter() - start) * 1000

        if _metrics:
            _metrics.pdf_duration_ms.labels(route="/pdf").observe(elapsed_ms)

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@router.post("/import-json", response_class=HTMLResponse)
async def import_results_json(request: Request):
    payload = (await request.body()).decode("utf-8")
    try:
        results = parse_results_json(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ungültige Eingabe") from exc

    return _TEMPLATES.TemplateResponse(
        request,
        "partials/imported_rows.html",
        {
            "results": results,
            "gender_de": _GENDER_DE,
        },
    )


@router.post("/export/zip")
async def export_zip(request: Request):
    from export_bundle import build_export_zip  # noqa: PLC0415

    payload = (await request.body()).decode("utf-8")
    try:
        export = load_results_export(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ungültige Eingabe") from exc

    zip_bytes = build_export_zip(export)
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="namenschmiede_export.zip"'},
    )
