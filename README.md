# Aventurische Namensschmiede

Ein Namens- und Charaktergenerator für **Das Schwarze Auge**. Das Projekt läuft
im Browser oder im Terminal und erzeugt kulturell passende Namen, regionale
Varianten und einfache NSC-Profile.

## Features

- **Web-UI und CLI** für denselben Generatorkern
- **54 konkrete auswählbare Kulturen/Regionen** sowie **6 Sammelauswahlen**
  für Spezies oder Regionen
- **Hierarchische Auswahl** über `Spezies -> Kultur -> Region`
  - Regionen werden aktuell nur für `Mittelreicher` separat gewählt
  - Sammelauswahlen wie `Mensch` oder `Mittelreicher` mischen automatisch
    passende Untereinheiten
- **Zwei Generierungsmodi**
  - `simple`: zieht aus kuratierten Namenslisten
  - `compose`: baut Namen aus Silbenbausteinen zusammen
- **Compose nur dort, wo Daten vorhanden sind**
  - in der Web-UI ausgegraut
  - im interaktiven CLI-Menü gar nicht erst angeboten
- **Geschlechtsfilter**: `male`, `female`, `any`
- **Charaktergenerierung** mit Alter, Beruf und Eigenschaften
- **Export / Import**
  - CLI: `rich`, `plain`, `json`, `csv`, `markdown`, `clipboard`, `pdf`
  - Web: `PDF`-Download sowie `JSON`-Download und `JSON`-Import
- **Observability-Stack** via Docker mit Grafana, Prometheus, Loki und Tempo

## Hinweis zur Entstehung

> **Wichtiger Hinweis:** Ein erheblicher Teil dieser Codebase wurde mit
> Unterstützung von AI-Tools erstellt, insbesondere **ChatGPT Codex** und
> **Claude Code**. Das Repository ist bewusst auch ein Lern- und
> Experimentierprojekt für AI-gestützte Softwareentwicklung.

## Schnellstart

### Lokal mit `uv`

```bash
uv sync
uv run namegen
```

`uv run namegen` startet ohne Unterbefehl direkt das interaktive Menü.

### Web-App und Observability mit Docker

```bash
docker compose up --build
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build
```

Danach verfügbar unter:

| Service | URL | Hinweis |
|---|---|---|
| Web-App | <http://localhost:8000> | Generator-Oberfläche |
| Metrics | <http://localhost:8000/metrics> | Prometheus-Format |
| Grafana | <http://localhost:3300> | Login: `admin` / `admin` |
| Prometheus | <http://localhost:9090> | Metriken |
| Loki (API) | <http://localhost:3100> | Logs |
| Tempo (API) | <http://localhost:3200> | Traces |

`docker compose up --build` startet nur die Web-App. Für den kompletten
Observability-Stack wird das Overlay `docker-compose.observability.yml`
zusätzlich eingebunden.

## CLI-Nutzung

### Katalog anzeigen

```bash
# Alle auswählbaren Kulturen, Regionen und Sammelauswahlen
uv run namegen regions

# Alle verfügbaren Professionen
uv run namegen professions
```

### Namen generieren

```bash
# 5 weibliche Namen aus dem Kosch
uv run namegen simple mittelreich_kosch --gender female --count 5

# 8 Namen aus allen menschlichen Kulturen und Regionen
uv run namegen simple human --count 8

# 6 Namen aus allen Mittelreich-Regionen
uv run namegen simple mittelreicher --count 6

# 3 komponierte Namen aus einer compose-fähigen Auswahl
uv run namegen compose nivesen --gender male --count 3 --components
```

### Charaktere generieren

```bash
# 4 profane nostrische Charaktere
uv run namegen simple nostria --character --profession-category profan --count 4

# 2 zauberische Charaktere aus allen Mittelreich-Regionen
uv run namegen simple mittelreicher --character --profession-category zauberer --count 2
```

### Ausgabeformate

```bash
# JSON nach stdout
uv run namegen simple human --format json

# CSV in Datei schreiben
uv run namegen simple thorwal --format csv --output thorwal.csv

# PDF erzeugen
uv run namegen simple mittelreich_kosch --format pdf --output kosch.pdf
```

## Web-UI

Die Web-Oberfläche ist eine HTMX-basierte Single-Page-Ansicht. Sie bietet:

- Auswahl von Spezies, Kultur und bei Bedarf Region
- automatische Deaktivierung des Compose-Modus bei fehlenden Silbenbausteinen
- Umschaltung zwischen Namensliste und Charakterbogen
- Listenverwaltung im Browser
- `PDF`-Download für reine Namens- oder reine Charakterlisten
- `JSON`-Download und `JSON`-Import für persistente Listen

Das Web-JSON ist bewusst versioniert:

```json
{
  "format": "namenschmiede-results",
  "version": 1,
  "exported_at": "2026-04-05T20:00:00Z",
  "entries": []
}
```

Jeder Eintrag trägt `kind: "name"` oder `kind: "character"`, damit beide
Listenarten sauber validiert und wiederhergestellt werden können.

## Auswahlmodell

Das Projekt unterscheidet fachlich zwischen:

- **Spezies**: z. B. `human`, `elf`, `dwarf`
- **Kultur**: z. B. `nostria`, `thorwal`, `mittelreicher`, `firnelfen`
- **Region**: aktuell nur für mittelreichische Unterräume wie
  `mittelreich_kosch`, `mittelreich_garetien`, `mittelreich_weiden`

Zusätzlich gibt es **Sammelauswahlen**:

- `human`: mischt aus allen menschlichen Kulturen und Regionen
- `mittelreicher`: mischt aus allen Mittelreich-Regionen
- entsprechende Sammelauswahlen auch für andere Spezies

Die konkrete Zielregion wird pro erzeugtem Namen oder Charakter zufällig aus der
aufgelösten Zielmenge gezogen.

## Projektstruktur

```text
src/namegen/
├── catalog.py       # Katalog und Auflösung von Sammelauswahlen
├── chargen.py       # Charaktergenerierung
├── cli.py           # Typer-CLI
├── generator.py     # Namensgenerierung
├── interactive.py   # interaktives Terminal-Menü
├── loader.py        # TOML-Laden und Datenzusammenführung
├── models.py        # Pydantic-Datenmodelle
├── output.py        # Ausgabeformate für CLI
├── pdf_builder.py   # PDF-Erzeugung für CLI/Web
└── data/
    ├── *.toml       # Regionen
    └── cultures/    # Kulturdaten

web/
├── main.py
├── observability.py
├── pdf_utils.py
├── result_transfer.py
├── routes/
│   ├── generator.py
│   └── regions.py
├── templates/
└── static/

tests/
├── test_loader.py
├── test_generator.py
├── test_cli.py
├── test_web_generator_routes.py
└── ...
```

## Datenmodell und neue Daten

Neue Inhalte liegen in TOML-Dateien unter `src/namegen/data/`.

- **Regionen** liegen direkt unter `src/namegen/data/*.toml`
- **Kulturen** liegen unter `src/namegen/data/cultures/*.toml`
- Regionen können Spezies- und Kulturdaten referenzieren und überschreiben
- nur Mittelreich nutzt aktuell eine zusätzliche Regionsebene in der UI

### Neue Region oder Kultur hinzufügen

Eine neue Datei genügt in vielen Fällen bereits, solange die `origin`-Zuordnung
korrekt gesetzt ist.

Minimales Beispiel:

```toml
[meta]
region = "Meine Region"
notes = "Kurze Beschreibung."

[origin]
species_id = "human"
culture_id = "meinekultur"
region_id = "meine_region"

[simple.first]
male = ["Aldric", "Borin"]
female = ["Alva", "Brynn"]
neutral = []

[simple.last]
male = ["von Sternfels"]
female = []
neutral = ["Sturmwind"]
```

Für Compose-Daten werden zusätzlich `compose.first` und `compose.last`
definiert. Wenn keine Compose-Daten vorhanden sind, wird der Modus automatisch
nicht angeboten.

## Entwicklung

```bash
uv sync
env UV_CACHE_DIR=/tmp/uv-cache uv run pytest
env UV_CACHE_DIR=/tmp/uv-cache uv run pytest --cov=namegen
env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
env UV_CACHE_DIR=/tmp/uv-cache uv run ruff format .
```

Das Repository nutzt außerdem einen lokalen `pre-commit`-Hook, der vor Commits
automatisch ausführt:

```bash
uv run ruff check --fix .
uv run ruff format .
```

## Observability

Die Web-App instrumentiert den Request-Lifecycle mit OpenTelemetry-Tracing,
Prometheus-Metriken auf `/metrics` und strukturierten JSON-Logs mit
`request_id`, `trace_id` und `span_id`.

Start:

```bash
docker compose up --build
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build
```

- Basis-Compose: nur die Web-App
- Overlay: OpenTelemetry Collector, Prometheus, Tempo, Loki, Alloy und Grafana

### Stack-Versionen

| Komponente | Image | Zweck |
|---|---|---|
| OpenTelemetry Collector | `otel/opentelemetry-collector-contrib:0.149.0` | OTLP-Empfang, Routing |
| Prometheus | `prom/prometheus:v3.11.0` | Metriken |
| Tempo | `grafana/tempo:2.10.3` | Traces |
| Loki | `grafana/loki:3.4.2` | Logs |
| Alloy | `grafana/alloy:v1.8.3` | Docker-Log-Kollektor |
| Grafana | `grafana/grafana:12.4.2` | Visualisierung |

### Wichtige Metriken

| Metrik | Bedeutung |
|---|---|
| `http_server_request_count_total` | HTTP-Requests gesamt |
| `http_server_request_duration_milliseconds_bucket` | HTTP-Latenz |
| `app_errors_count_total` | 5xx-Fehler |
| `namegen_generate_count_total` | Generierungsaufrufe |
| `namegen_empty_results_count_total` | leere Ergebnisse |
| `namegen_name_length_chars_bucket` | Namenslängen |

### Health & Request-Korrelation

- `/health` liefert `status`, `version`, `regions_loaded`, `uptime_s` und
  `python_version`
- jede HTTP-Response enthält `X-Request-ID`
- Web-Logs enthalten dieselbe `request_id` plus `trace_id` / `span_id`

## Rechtlicher Hinweis

**Das Schwarze Auge** ist eine eingetragene Marke der **Ulisses Spiele GmbH**.
Dieses Projekt ist ein privates, nicht-kommerzielles Fanprojekt und steht in
keiner offiziellen Verbindung zu Ulisses Spiele.

Erstellt gemäß den
[Fan-Richtlinien von Ulisses Spiele](https://ulisses-spiele.de/fan-richtlinie/).

## Datenquellen & Umsetzung

- Namens-, Kultur- und Professionsdaten nutzen bewusst Begriffe aus
  **Das Schwarze Auge**
- die Nutzung erfolgt im Rahmen der Ulisses-Fan-Richtlinie
- das Web-Frontend enthält zusätzlich die Seite [`/rechtliches`](/rechtliches)
  mit Markenhinweis und Quellenpolitik
- falls Inhalte problematisch sind, bitte ein Issue oder einen PR anlegen
