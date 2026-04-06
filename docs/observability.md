# Observability & Monitoring

## Container-Stack (Grafana Best Practices)

Der Docker-Compose-Stack umfasst eine vollständige, entkoppelte Pipeline:

1. **Web-App** exportiert Prometheus-Metriken unter `/metrics` und sendet OTLP-Spans.
2. **OpenTelemetry Collector** übernimmt OTLP-Traces und leitet sie an Tempo weiter.
3. **Prometheus** scraped direkt `web:8000/metrics`.
4. **Tempo** speichert Traces/Spans.
5. **Alloy** shippt Docker-Logs nach Loki.
6. **Grafana** nutzt provisionierte Datasources für Prometheus, Loki und Tempo.

Starten:

```bash
docker compose up --build
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build
```

Zugriff:
- Web-App: `http://localhost:8000`
- Metrics: `http://localhost:8000/metrics`
- Grafana: `http://localhost:3300` (admin/admin)
- Prometheus: `http://localhost:9090`
- Loki: `http://localhost:3100`
- Tempo: `http://localhost:3200`

Automatisch provisioniertes Dashboard:
- Folder: `Namenschmiede`
- Dashboard: `Aventurische Namenschmiede - Observability`

## Signal-Definitionen

### Availability SLO
- Ziel: **99.5% erfolgreiche Requests** über 30 Tage.
- Erfolg: Statusklasse `2xx` und `3xx`.
- Fehlerbudget: 0.5% Requests mit Statusklasse `5xx`.

### Latenz-SLO `/generate`
- Ziel: **p95 < 500ms**, **p99 < 1000ms**.
- Primärmetriken:
  - `http_server_request_duration_milliseconds_bucket` (route `/generate`)
  - `namegen_generate_loop_duration_ms_milliseconds_bucket`
  - `namegen_load_region_duration_ms_milliseconds_bucket`
  - `namegen_template_render_duration_ms_milliseconds_bucket`

### Fehler-SLO
- Ziel: **< 1% `app_errors_count_total`** pro Stunde für Produktivumgebung.
- Gruppierung nach `http_route`, `http_status_class`, `error_type`.

## Alert-Empfehlungen

1. **High 5xx Rate**
   - Bedingung: `app_errors_count_total` / `http_server_request_count_total` > 1% für 10 Minuten.
   - Schweregrad: High.

2. **Latency Regression `/generate`**
   - Bedingung: p95(`http_server_request_duration_milliseconds_bucket` bei route `/generate`) > 500ms für 15 Minuten.
   - Schweregrad: Medium.

3. **Data Quality Drift**
   - Bedingung: `namegen_empty_results_count_total` > 5 pro 100 `namegen_generate_count_total`.
   - Schweregrad: Medium.

## Kardinalitätsrichtlinien
- Verwende `route`/`route_template` statt rohem Pfad.
- Keine Benutzer-IDs oder freie Strings als Metrik-Label.
- `error.type` nur als Klassenname.

## Korrelation
- Alle HTTP-Responses enthalten `X-Request-ID`.
- Logs enthalten `request_id`, `trace_id` und `span_id` als JSON-Felder.
