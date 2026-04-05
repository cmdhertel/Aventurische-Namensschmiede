"""Logging, metrics und tracing für die Web-App."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.metrics import Counter, Histogram
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode
from rich.logging import RichHandler


_LOGGER_NAME = "namenschmiede.observability"


@dataclass(slots=True)
class AppMetrics:
    """Alle benutzerdefinierten Metriken für die App."""

    request_count: Counter
    request_duration_ms: Histogram
    app_errors: Counter
    generate_calls: Counter
    input_chars: Counter
    output_chars: Counter
    load_region_duration_ms: Histogram
    generate_loop_duration_ms: Histogram
    template_render_duration_ms: Histogram
    pdf_duration_ms: Histogram
    empty_results: Counter
    name_length: Histogram


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

    known_prefixes = ("/generate", "/pdf", "/regions", "/health", "/static")
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


class TraceContextFilter(logging.Filter):
    """Hängt Trace/Span-ID an LogRecord an, wenn vorhanden."""

    def filter(self, record: logging.LogRecord) -> bool:
        trace_id, span_id = _trace_context()
        record.trace_id = trace_id
        record.span_id = span_id
        return True


def setup_logging() -> logging.Logger:
    """Konfiguriert strukturiertes, gut lesbares Logging mit Rich."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(log_level)

    handler = RichHandler(
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    )
    handler.addFilter(TraceContextFilter())
    handler.setFormatter(logging.Formatter("%(message)s trace_id=%(trace_id)s span_id=%(span_id)s"))

    root.addHandler(handler)
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(log_level)
    return logger


def _build_resource() -> Resource:
    return Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "aventurische-namensschmiede-web"),
            "service.version": os.getenv("OTEL_SERVICE_VERSION", "0.1.0"),
            "deployment.environment": os.getenv("APP_ENV", "dev"),
        }
    )


def setup_telemetry() -> tuple[trace.Tracer, AppMetrics]:
    """Initialisiert OpenTelemetry Traces und Metrics."""
    resource = _build_resource()

    # --- Tracing ---
    tracer_provider = TracerProvider(resource=resource)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint.rstrip('/')}/v1/traces"))
        )
    elif _bool_from_env("OTEL_EXPORT_TO_CONSOLE", default=True):
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer("namenschmiede.web")

    # --- Metrics ---
    metric_readers = []
    if otlp_endpoint:
        metric_readers.append(
            PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=f"{otlp_endpoint.rstrip('/')}/v1/metrics")
            )
        )
    elif _bool_from_env("OTEL_EXPORT_TO_CONSOLE", default=True):
        metric_readers.append(PeriodicExportingMetricReader(ConsoleMetricExporter()))

    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    metrics.set_meter_provider(meter_provider)
    meter = metrics.get_meter("namenschmiede.web")

    app_metrics = AppMetrics(
        request_count=meter.create_counter(
            "http.server.request.count",
            description="Anzahl eingehender HTTP Requests",
            unit="1",
        ),
        request_duration_ms=meter.create_histogram(
            "http.server.request.duration",
            description="Request-Latenz in Millisekunden",
            unit="ms",
        ),
        app_errors=meter.create_counter(
            "app.errors.count",
            description="Anzahl Fehler in HTTP Requests",
            unit="1",
        ),
        generate_calls=meter.create_counter(
            "namegen.generate.count",
            description="Anzahl Aufrufe der /generate Route",
            unit="1",
        ),
        input_chars=meter.create_counter(
            "namegen.input.chars",
            description="Anzahl Zeichen in Eingabeparametern",
            unit="chars",
        ),
        output_chars=meter.create_counter(
            "namegen.output.chars",
            description="Anzahl Zeichen in generierten Namen",
            unit="chars",
        ),
        load_region_duration_ms=meter.create_histogram(
            "namegen.load_region.duration_ms",
            description="Latenz für load_region in Millisekunden",
            unit="ms",
        ),
        generate_loop_duration_ms=meter.create_histogram(
            "namegen.generate_loop.duration_ms",
            description="Latenz der Generierungsschleife in Millisekunden",
            unit="ms",
        ),
        template_render_duration_ms=meter.create_histogram(
            "namegen.template_render.duration_ms",
            description="Latenz des Template-Renderings in Millisekunden",
            unit="ms",
        ),
        pdf_duration_ms=meter.create_histogram(
            "namegen.pdf.duration_ms",
            description="Latenz der PDF-Erstellung in Millisekunden",
            unit="ms",
        ),
        empty_results=meter.create_counter(
            "namegen.empty_results.count",
            description="Anzahl leerer Ergebnisse in Generierungsergebnissen",
            unit="1",
        ),
        name_length=meter.create_histogram(
            "namegen.name_length",
            description="Länge erzeugter Namen",
            unit="chars",
        ),
    )

    return tracer, app_metrics


def instrument_fastapi(app, logger: logging.Logger) -> None:
    """Aktiviert FastAPI-Instrumentation inkl. HTTP-Span-Erzeugung."""
    with suppress(Exception):
        FastAPIInstrumentor.instrument_app(app)
        logger.info("event=otel.fastapi.instrumented")


def create_metrics_middleware(
    logger: logging.Logger,
    app_metrics: AppMetrics,
) -> Callable:
    """Erzeugt Middleware, die Request-Metriken und strukturierte Logs schreibt."""

    async def middleware(request: Request, call_next) -> Response:
        start = perf_counter()
        path = request.url.path
        method = request.method
        route_template = _route_template(path)
        request_id = request.headers.get("x-request-id", str(uuid4()))

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_ms = (perf_counter() - start) * 1000
            attrs = {
                "http.method": method,
                "http.route": route_template,
                "http.status_class": "5xx",
                "error.type": type(exc).__name__,
            }
            app_metrics.request_count.add(1, attrs)
            app_metrics.request_duration_ms.record(elapsed_ms, attrs)
            app_metrics.app_errors.add(1, attrs)

            span = trace.get_current_span()
            if span and span.is_recording():
                span.set_attribute("http.route", route_template)
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))

            logger.exception(
                "event=http.request.error request_id=%s method=%s path=%s route=%s duration_ms=%.2f error_type=%s",
                request_id,
                method,
                path,
                route_template,
                elapsed_ms,
                type(exc).__name__,
            )
            raise

        elapsed_ms = (perf_counter() - start) * 1000
        attrs = {
            "http.method": method,
            "http.route": route_template,
            "http.status_code": response.status_code,
            "http.status_class": _status_class(response.status_code),
        }
        app_metrics.request_count.add(1, attrs)
        app_metrics.request_duration_ms.record(elapsed_ms, attrs)

        if response.status_code >= 500:
            app_metrics.app_errors.add(
                1,
                {
                    "http.method": method,
                    "http.route": route_template,
                    "http.status_class": _status_class(response.status_code),
                    "error.type": "HTTPServerError",
                },
            )

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "event=http.request request_id=%s method=%s path=%s route=%s status=%s duration_ms=%.2f",
            request_id,
            method,
            path,
            route_template,
            response.status_code,
            elapsed_ms,
        )
        return response

    return middleware
