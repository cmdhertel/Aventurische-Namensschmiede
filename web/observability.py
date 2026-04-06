"""Logging, request metrics, and tracing for the web app."""

from __future__ import annotations

import os
from collections.abc import Callable
from contextlib import suppress
from time import perf_counter
from urllib.parse import parse_qs
from uuid import uuid4

import structlog
from fastapi import Request, Response
from metrics import AppMetrics
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode
from structlog.contextvars import bind_contextvars, clear_contextvars

_LOGGER_NAME = "namenschmiede.observability"


def _bool_from_env(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _status_class(status_code: int) -> str:
    return f"{status_code // 100}xx"


def _route_template(path: str) -> str:
    if path == "/":
        return "/"

    known_prefixes = ("/generate", "/pdf", "/regions", "/health", "/metrics", "/static")
    for prefix in known_prefixes:
        if path.startswith(prefix):
            return prefix

    return "unknown"


def _trace_context() -> tuple[str, str]:
    span = trace.get_current_span()
    context = span.get_span_context()
    if not context.is_valid:
        return "", ""
    return f"{context.trace_id:032x}", f"{context.span_id:016x}"


async def _request_region(request: Request) -> str:
    """Extract the region from query params or form submissions when available."""
    region = request.query_params.get("region")
    if region:
        return region

    content_type = request.headers.get("content-type", "")
    if (
        request.method in {"POST", "PUT", "PATCH"}
        and "application/x-www-form-urlencoded" in content_type
    ):
        with suppress(Exception):
            body = (await request.body()).decode("utf-8")
            values = parse_qs(body, keep_blank_values=False)
            parsed = values.get("region", [""])
            return parsed[0]
    return ""


def _add_trace_context(
    logger: object,
    method_name: str,
    event_dict: dict[str, object],
) -> dict[str, object]:
    """Attach trace/span context to structured logs when available."""
    del logger, method_name
    trace_id, span_id = _trace_context()
    if trace_id:
        event_dict["trace_id"] = trace_id
    if span_id:
        event_dict["span_id"] = span_id
    return event_dict


def setup_logging():
    """Configure structured JSON logging for the web app."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
            _add_trace_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    import logging

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(log_level)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    return structlog.get_logger(_LOGGER_NAME)


def _build_resource() -> Resource:
    return Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "aventurische-namensschmiede-web"),
            "service.version": os.getenv("OTEL_SERVICE_VERSION", "0.1.0"),
            "deployment.environment": os.getenv("APP_ENV", "dev"),
        }
    )


def setup_telemetry() -> trace.Tracer:
    """Initialize OpenTelemetry tracing."""
    resource = _build_resource()

    # --- Tracing ---
    tracer_provider = TracerProvider(resource=resource)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint.rstrip('/')}/v1/traces"))
        )
    elif _bool_from_env("OTEL_EXPORT_TO_CONSOLE", default=False):
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer("namenschmiede.web")

    return tracer


def instrument_fastapi(app, logger) -> None:
    """Aktiviert FastAPI-Instrumentation inkl. HTTP-Span-Erzeugung."""
    with suppress(Exception):
        FastAPIInstrumentor.instrument_app(app)
        logger.info("otel.fastapi.instrumented")


def create_metrics_middleware(
    logger,
    app_metrics: AppMetrics,
) -> Callable:
    """Erzeugt Middleware, die Request-Metriken und strukturierte Logs schreibt."""

    async def middleware(request: Request, call_next) -> Response:
        start = perf_counter()
        path = request.url.path
        method = request.method
        route_template = _route_template(path)
        if route_template == "/metrics":
            return await call_next(request)

        request_id = request.headers.get("x-request-id", str(uuid4()))
        region = await _request_region(request)
        active_labels = {
            "http_method": method,
            "http_route": route_template,
        }

        clear_contextvars()
        bind_contextvars(
            request_id=request_id,
            method=method,
            path=path,
            route=route_template,
            region=region,
        )
        app_metrics.active_requests.labels(**active_labels).inc()

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_ms = (perf_counter() - start) * 1000
            http_labels = {
                "http_method": method,
                "http_route": route_template,
                "http_status_code": "500",
                "http_status_class": "5xx",
            }
            error_labels = {
                "http_method": method,
                "http_route": route_template,
                "http_status_class": "5xx",
                "error_type": type(exc).__name__,
            }
            app_metrics.request_count.labels(**http_labels).inc()
            app_metrics.request_duration_ms.labels(**http_labels).observe(elapsed_ms)
            app_metrics.app_errors.labels(**error_labels).inc()
            app_metrics.active_requests.labels(**active_labels).dec()

            span = trace.get_current_span()
            if span and span.is_recording():
                span.set_attribute("http.route", route_template)
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))

            logger.exception(
                "http.request.error",
                request_id=request_id,
                method=method,
                path=path,
                route=route_template,
                status_code=500,
                duration_ms=round(elapsed_ms, 2),
                error_type=type(exc).__name__,
                region=region,
            )
            clear_contextvars()
            raise

        elapsed_ms = (perf_counter() - start) * 1000
        http_labels = {
            "http_method": method,
            "http_route": route_template,
            "http_status_code": str(response.status_code),
            "http_status_class": _status_class(response.status_code),
        }
        app_metrics.request_count.labels(**http_labels).inc()
        app_metrics.request_duration_ms.labels(**http_labels).observe(elapsed_ms)
        app_metrics.active_requests.labels(**active_labels).dec()

        if response.status_code >= 500:
            app_metrics.app_errors.labels(
                http_method=method,
                http_route=route_template,
                http_status_class=_status_class(response.status_code),
                error_type="HTTPServerError",
            ).inc()

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "http.request",
            request_id=request_id,
            method=method,
            path=path,
            route=route_template,
            status_code=response.status_code,
            duration_ms=round(elapsed_ms, 2),
            region=region,
        )
        clear_contextvars()
        return response

    return middleware
