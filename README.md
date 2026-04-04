# Aventurische Namensschmiede

Ein Namengenerator für **Das Schwarze Auge** – kulturell passende Vor- und Nachnamen
für aventurische Helden und Meisterpersonen, direkt aus dem Browser oder dem Terminal.

---

## Features

- **23 aventurische Regionen** – vom Hohen Norden bis Aranien, vom Horasreich bis Maraskan
- **Zwei Generierungsmodi**
  - *Einfach* – zieht aus kuratierten Namenslisten
  - *Komposition* – baut Namen silbenweise aus regionalen Bausteinen
- **Geschlechtsfilter** – männlich, weiblich oder beliebig
- **Web-UI** – HTMX-getriebene Single-Page-Ansicht, kein Reload nötig
- **CLI** – voller Funktionsumfang auch ohne Browser
- **PDF-Export** – Namensliste als druckfertiges PDF herunterladen

---

## Schnellstart (Docker)

```bash
docker compose up --build
```

Danach verfügbar unter:

| Service | URL | Hinweis |
|---|---|---|
| Web-App | <http://localhost:8000> | |
| Grafana | <http://localhost:3300> | Login: `admin` / `admin` |
| Prometheus | <http://localhost:9090> | |
| Loki (API) | <http://localhost:3100> | |
| Tempo (API) | <http://localhost:3200> | |

---

## CLI-Nutzung

```bash
# Abhängigkeiten installieren
uv sync

# Alle Regionen auflisten
uv run namegen regions

# 5 weibliche Namen aus dem Kosch
uv run namegen simple kosch --gender female --count 5

# 3 männliche Namen aus dem Mittelreich (Kompositum mit Silbendetails)
uv run namegen compose mittelreich --gender male --count 3 --components
```

---

## Projektstruktur

```
src/namegen/
├── cli.py          # Typer-CLI
├── generator.py    # Kerngenerierung (generate())
├── loader.py       # TOML-Laden via importlib.resources
├── models.py       # Pydantic-Datenmodelle
├── interactive.py  # Interaktiver Auswahlmodus
├── output.py       # Rich-Ausgabe & PDF
└── data/
    ├── alanfa.toml
    ├── aranien.toml
    ├── mittelreich_kosch.toml
    └── ...          # eine .toml pro Region

web/
├── main.py         # FastAPI-App
├── routes/
│   ├── generator.py
│   └── regions.py
├── templates/      # Jinja2-Templates
└── static/         # Tailwind CSS (kompiliert)
```

---

## Observability (Logs, Metriken, Traces)

Die Web-App instrumentiert den gesamten Request-Lifecycle mit OpenTelemetry und strukturierten Logs.
Der komplette Observability-Stack startet automatisch per `docker compose up --build`.

### Stack-Versionen

| Komponente | Image | Zweck |
|---|---|---|
| **OpenTelemetry Collector** | `otel/opentelemetry-collector-contrib:0.149.0` | OTLP-Empfang, Routing |
| **Prometheus** | `prom/prometheus:v3.11.0` | Metriken-Speicherung |
| **Tempo** | `grafana/tempo:2.10.3` | Distributed Tracing |
| **Loki** | `grafana/loki:3.4.2` | Log-Aggregation |
| **Alloy** | `grafana/alloy:v1.8.3` | Log-Kollektor (Docker → Loki) |
| **Grafana** | `grafana/grafana:12.4.2` | Visualisierung |

### Pipeline

```
Web-App (OTLP)
  └─▶ OTel Collector
        ├─▶ Prometheus (Metriken via Prometheus-Exporter :9464)
        └─▶ Tempo (Traces via OTLP gRPC)

Docker-Container-Logs
  └─▶ Alloy (Docker-Socket)
        └─▶ Loki (Log-Speicherung)
```

### Grafana-Dashboards

Alle Dashboards werden automatisch im Ordner **Namenschmiede** provisioniert:

| Dashboard | Zweck |
|---|---|
| **Namenschmiede · Overview** | Golden Signals auf einen Blick: RPS, Error-Rate, p95-Latenz, Traces |
| **Namenschmiede · HTTP & API** | HTTP-Traffic, Latenz-Perzentile (p50/p90/p95/p99), Fehler-Analyse |
| **Namenschmiede · Name Generation** | Regionen/Modi, Pipeline-Latenz, Namenslängen-Verteilung, Leerquote |
| **Namenschmiede · Logs** | Loki-Logstream, Fehlerrate, Level-Verteilung; TraceIDs sind klickbar → Tempo |

### Logs ↔ Traces Korrelation

Jede Log-Zeile enthält `trace_id=<hex>` und `span_id=<hex>`. In Grafana:
- **Log → Trace**: TraceID-Link in jedem Log-Eintrag öffnet den zugehörigen Tempo-Span
- **Trace → Log**: Klick auf einen Span in Tempo springt direkt zur Loki-Abfrage mit `filterByTraceID`

### Wichtige Metriken

| Metrik | Bedeutung |
|---|---|
| `http_server_request_count_total` | HTTP-Requests gesamt |
| `http_server_request_duration_milliseconds_bucket` | Latenz-Histogramm |
| `app_errors_count_total` | 5xx-Fehler |
| `namegen_generate_count_total` | Generierungsaufrufe |
| `namegen_empty_results_count_total` | Leere Ergebnisse (Datenqualität) |
| `namegen_name_length_chars_bucket` | Namenslängen-Histogramm |

---

## Neue Region hinzufügen

Eine neue TOML-Datei in `src/namegen/data/` ablegen – fertig.
Es sind keine Code-Änderungen nötig; die Region erscheint sofort in `namegen regions`
und der Web-UI.

**Minimales Datei-Skelett** (am Beispiel einer einfachen Region):

```toml
[meta]
region   = "Meine Region"
language = "aventurisch"
notes    = "Kurze Beschreibung."

[simple.first]
male    = ["Aldric", "Borin"]
female  = ["Alva", "Brynn"]
neutral = []

[simple.last]
male    = ["von Sternfels"]
female  = []
neutral = ["Sturmwind"]
```

Für Kompositions-Namen (`[compose.first]` / `[compose.last]`) siehe eine bestehende TOML als Vorlage.

---

## Entwicklung

```bash
uv sync                        # inkl. Dev-Abhängigkeiten
uv run pytest                  # alle Tests
uv run pytest --cov=namegen    # mit Coverage
```

Tests nutzen einen geseedeten `random.Random`-RNG – kein Monkeypatching nötig.

---

## Rechtlicher Hinweis

**Das Schwarze Auge** ist eine eingetragene Marke der **Ulisses Spiele GmbH**.
Dieses Projekt ist ein privates Fan-Projekt und steht in keiner offiziellen Verbindung
zu Ulisses Spiele. Es wird weder gesponsert noch unterstützt oder genehmigt.
Es ist nicht kommerziell und wird kostenlos bereitgestellt.

Erstellt gemäß den [Fan-Richtlinien von Ulisses Spiele](https://ulisses-spiele.de/fan-richtlinie/).
