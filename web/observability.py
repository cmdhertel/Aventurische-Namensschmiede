"""Logging, metrics und tracing für die Web-App."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from time import perf_counter

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
from rich.logging import RichHandler


_LOGGER_NAME = "namenschmiede.observability"


@dataclass(slots=True)
class AppMetrics:
    """Alle benutzerdefinierten Metriken für die App."""

    request_count: Counter
    request_duration_ms: Histogram
    generate_calls: Counter
    input_chars: Counter
    output_chars: Counter


def _bool_from_env(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


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
    handler.setFormatter(logging.Formatter("%(message)s"))

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

        response = await call_next(request)

        elapsed_ms = (perf_counter() - start) * 1000
        attrs = {
            "http.method": method,
            "http.route": path,
            "http.status_code": response.status_code,
        }
        app_metrics.request_count.add(1, attrs)
        app_metrics.request_duration_ms.record(elapsed_ms, attrs)

        logger.info(
            "event=http.request method=%s path=%s status=%s duration_ms=%.2f",
            method,
            path,
            response.status_code,
            elapsed_ms,
        )
        return response

    return middleware
