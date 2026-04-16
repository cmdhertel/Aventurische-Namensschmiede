"""Prometheus metrics used by the web application."""

from __future__ import annotations

from dataclasses import dataclass

from prometheus_client import Counter, Gauge, Histogram

_HTTP_LABELS = ("http_method", "http_route", "http_status_code", "http_status_class")
_ERROR_LABELS = ("http_method", "http_route", "http_status_class", "error_type")
_ACTIVE_LABELS = ("http_method", "http_route")
_NAMEGEN_LABELS = (
    "namegen_region",
    "namegen_mode",
    "namegen_gender",
    "namegen_character",
    "namegen_profession_category",
    "namegen_profession_theme",
    "namegen_nobility_status",
)


@dataclass(slots=True)
class AppMetrics:
    """Container for custom Prometheus metrics."""

    request_count: Counter
    request_duration_ms: Histogram
    active_requests: Gauge
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


def build_metrics() -> AppMetrics:
    """Create the application's Prometheus metrics in the default registry."""
    return AppMetrics(
        request_count=Counter(
            "http_server_request_count",
            "Anzahl eingehender HTTP Requests",
            _HTTP_LABELS,
        ),
        request_duration_ms=Histogram(
            "http_server_request_duration_milliseconds",
            "Request-Latenz in Millisekunden",
            _HTTP_LABELS,
            buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000),
        ),
        active_requests=Gauge(
            "http_server_active_requests",
            "Aktive HTTP Requests",
            _ACTIVE_LABELS,
        ),
        app_errors=Counter(
            "app_errors_count",
            "Anzahl Fehler in HTTP Requests",
            _ERROR_LABELS,
        ),
        generate_calls=Counter(
            "namegen_generate_count",
            "Anzahl Aufrufe der /generate Route",
            _NAMEGEN_LABELS,
        ),
        input_chars=Counter(
            "namegen_input_chars",
            "Anzahl Zeichen in Eingabeparametern",
            _NAMEGEN_LABELS,
        ),
        output_chars=Counter(
            "namegen_output_chars",
            "Anzahl Zeichen in generierten Namen",
            _NAMEGEN_LABELS,
        ),
        load_region_duration_ms=Histogram(
            "namegen_load_region_duration_ms_milliseconds",
            "Latenz für load_region in Millisekunden",
            _NAMEGEN_LABELS,
            buckets=(0.1, 0.5, 1, 2.5, 5, 10, 25, 50, 100, 250, 500),
        ),
        generate_loop_duration_ms=Histogram(
            "namegen_generate_loop_duration_ms_milliseconds",
            "Latenz der Generierungsschleife in Millisekunden",
            _NAMEGEN_LABELS,
            buckets=(0.5, 1, 2.5, 5, 10, 25, 50, 100, 250, 500, 1000),
        ),
        template_render_duration_ms=Histogram(
            "namegen_template_render_duration_ms_milliseconds",
            "Latenz des Template-Renderings in Millisekunden",
            _NAMEGEN_LABELS,
            buckets=(0.1, 0.5, 1, 2.5, 5, 10, 25, 50, 100, 250),
        ),
        pdf_duration_ms=Histogram(
            "namegen_pdf_duration_ms_milliseconds",
            "Latenz der PDF-Erstellung in Millisekunden",
            ("route",),
            buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500),
        ),
        empty_results=Counter(
            "namegen_empty_results_count",
            "Anzahl leerer Ergebnisse in Generierungsergebnissen",
            _NAMEGEN_LABELS,
        ),
        name_length=Histogram(
            "namegen_name_length_chars",
            "Länge erzeugter Namen",
            _NAMEGEN_LABELS,
            buckets=(1, 5, 10, 15, 20, 25, 30, 40, 50),
        ),
    )
