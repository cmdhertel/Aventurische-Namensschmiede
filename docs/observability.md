# Observability & Monitoring

## Container-Stack (Grafana Best Practices)

Der Docker-Compose-Stack umfasst eine vollständige, entkoppelte Pipeline:

1. **Web-App** exportiert OTLP-Metriken und OTLP-Spans an den Collector.
2. **OpenTelemetry Collector** übernimmt Entgegennahme, Batching und Routing.
3. **Prometheus** scraped die Collector-Metriken (`otel-collector:9464`).
4. **Tempo** speichert Traces/Spans.
5. **Grafana** nutzt provisionierte Datasources für Prometheus + Tempo sowie ein sofort nutzbares Dashboard.

Starten:

```bash
docker compose up --build
```

Zugriff:
- Grafana: `http://localhost:3000` (admin/admin)
- Prometheus: `http://localhost:9090`
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
  - `http.server.request.duration` (route `/generate`)
  - `namegen.generate_loop.duration_ms`
  - `namegen.load_region.duration_ms`
  - `namegen.template_render.duration_ms`

### Fehler-SLO
- Ziel: **< 1% `app.errors.count`** pro Stunde für Produktivumgebung.
- Gruppierung nach `http.route`, `http.status_class`, `error.type`.

## Alert-Empfehlungen

1. **High 5xx Rate**
   - Bedingung: `app.errors.count` / `http.server.request.count` > 1% für 10 Minuten.
   - Schweregrad: High.

2. **Latency Regression `/generate`**
   - Bedingung: p95(`http.server.request.duration` bei route `/generate`) > 500ms für 15 Minuten.
   - Schweregrad: Medium.

3. **Data Quality Drift**
   - Bedingung: `namegen.empty_results.count` > 5 pro 100 `namegen.generate.count`.
   - Schweregrad: Medium.

## Kardinalitätsrichtlinien
- Verwende `route`/`route_template` statt rohem Pfad.
- Keine Benutzer-IDs oder freie Strings als Metrik-Label.
- `error.type` nur als Klassenname.

## Korrelation
- Alle HTTP-Responses enthalten `X-Request-ID`.
- Logs enthalten `trace_id`/`span_id` für direkte Trace-Korrelation.
