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
- App: **http://localhost:8000**
- Grafana: **http://localhost:3000** (Login: `admin` / `admin`)
- Prometheus: **http://localhost:9090**
- Tempo API: **http://localhost:3200**

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

## Observability (Logging, Metrics, Traces)

Die Web-App liefert strukturierte Logs und OpenTelemetry-Metriken/Traces.

Mit `docker compose up --build` startet ein kompletter Grafana-Stack containerbasiert mit:
- OpenTelemetry Collector (`otel-collector`)
- Prometheus (Metriken)
- Tempo (Spans/Traces)
- Grafana (Visualisierung)

Die Web-App sendet OTLP automatisch an `http://otel-collector:4318`.

Vorkonfiguriertes Grafana-Dashboard wird automatisch provisioniert:
- **Aventurische Namenschmiede - Observability**
- Pfad: `Namenschmiede`-Folder in Grafana
- Nützliche Metriken:
  - `http.server.request.count`
  - `http.server.request.duration` (ms)
  - `namegen.generate.count`
  - `namegen.input.chars`
  - `namegen.output.chars`

Zusätzliche Span-Attribute auf `/generate` enthalten u. a. Region, Modus, Geschlecht,
Charakter-Modus, Kategorien sowie Input/Output-Zeichenanzahl.

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
