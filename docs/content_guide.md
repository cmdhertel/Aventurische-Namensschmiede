# Content Guide

Dieser Guide beschreibt, **welcher Inhalt wo hingehört** und **wann welche Datei erweitert werden soll**.

Ziel ist nicht nur zu zeigen, *wie* man neue Daten ergänzt, sondern vor allem *wo* sie fachlich einsortiert werden müssen, damit Loader, CLI, Web-UI und Charaktergenerator konsistent bleiben.

## Grundprinzip

Die Datenstruktur ist hierarchisch:

1. **Spezies** definiert allgemeine biologische oder übergreifende Charaktermerkmale.
2. **Kultur** definiert typische Namen, Sprache, Berufe und kulturelle Grundprägung.
3. **Region** konkretisiert eine Kultur lokal und kann Namen, Berufe und Charakterdetails überschreiben oder ergänzen.
4. **Zentrale Metadaten-Dateien** enthalten globale Listen oder fachübergreifende Kataloge, zum Beispiel Professionen oder Themen-Gruppen.

Die wichtigste Regel ist:

- **Allgemein und überall gültig** gehört in eine zentrale oder kulturelle Datei.
- **Nur für einen lokalen Raum gültig** gehört in die konkrete Regionsdatei.
- **Nur für eine Spezies gültig** gehört in die Spezies-Datei.
- **Nur für einen fachlichen Sonderfall wie eine Themen-Gruppe** gehört in den Themen-Katalog plus die passende Region/Kultur, die diesen Inhalt tatsächlich nutzt.

## Inhaltsarten und Ablageorte

### Neue Spezies

Datei:
- `src/namegen/data/species/<species_id>.toml`

Zusätzlich prüfen:
- `src/namegen/loader.py`
- `src/namegen/catalog.py`

Hier gehört hinein:
- Speziesname
- AP-/Lebens-/Alterswerte
- automatische Vorteile/Nachteile
- speziesweite Charaktertendenzen

Hier gehört **nicht** hinein:
- konkrete regionale Namenslisten
- regionale Nachnamen
- lokale Berufe

Dann eine Spezies-Datei anlegen, wenn:
- der Inhalt für alle Vertreter dieser Spezies gilt
- der Inhalt nicht von Kultur oder Region abhängt

Beispiel:
- `src/namegen/data/species/human.toml`

### Neue Kultur

Datei:
- `src/namegen/data/cultures/<culture_id>.toml`

Zusätzlich prüfen:
- `src/namegen/loader.py`
- `src/namegen/catalog.py`

Hier gehört hinein:
- Kulturname
- Namensschema
- einfache Namenslisten
- Compose-Bausteine, falls kulturweit sinnvoll
- kulturtypische Sprachen, Schriften, Berufe, Vorteile, Nachteile, Talente

Dann eine Kultur-Datei anlegen, wenn:
- der Inhalt für mehrere Regionen derselben Kultur gilt
- eine Region nicht nur ein lokaler Sonderfall, sondern ein kultureller Standardfall ist

Beispiel:
- `src/namegen/data/cultures/mittelreicher.toml`

### Neue Region

Datei:
- `src/namegen/data/<region_id>.toml`

Hier gehört hinein:
- `[meta]` mit Anzeigename, Kürzel, Notizen
- Namenslisten oder Compose-Bausteine für diesen konkreten Raum
- regionale Charakterdetails
- regionale Zusatzberufe

Dann eine Regionsdatei anlegen oder erweitern, wenn:
- Namen lokal anders klingen als in der Mutterkultur
- es lokale Nachnamen, Titel oder Adelsformen gibt
- es regionale Berufe oder typische Eigenschaften gibt
- die Region im Katalog direkt auswählbar sein soll

Beispiel:
- `src/namegen/data/mittelreich_kosch.toml`
- `src/namegen/data/mittelreich_perricum.toml`

### Neue Namen

Wo Namen hingehören, hängt vom Geltungsbereich ab:

- **Speziesweit**: selten, nur wenn wirklich für alle Kulturen der Spezies passend
- **Kulturweit**: `src/namegen/data/cultures/<culture_id>.toml`
- **Regional**: `src/namegen/data/<region_id>.toml`

Namensdaten liegen typischerweise in:
- `[simple.first]`
- `[simple.last]`
- `[simple.parent]`
- `[simple.byname]`
- `[compose.first]`
- `[compose.last]`

Faustregel:
- Wenn ein Name oder Muster in vielen Regionen derselben Kultur vorkommt, in die Kultur-Datei.
- Wenn ein Name klar lokal geprägt ist, in die Regionsdatei.

### Neue Compose-Daten

Datei:
- Kultur- oder Regionsdatei

Struktur:
- `[compose.first]`
- `[compose.first.male]`
- `[compose.first.female]`
- `[compose.first.neutral]`
- `[compose.last]`
- `[compose.last.neutral]`

Dann Compose-Daten ergänzen, wenn:
- Namen nicht nur aus festen Listen gezogen werden sollen
- ausreichend Silbenmaterial vorhanden ist
- der Stil systematisch kombinierbar ist

Wichtig:
- Ohne valide Compose-Bausteine wird der Compose-Modus für diese Auswahl automatisch nicht angeboten.

### Neue Professionen

Es gibt mehrere fachliche Orte für Professionen.

#### 1. Globale Professionen nach Kategorie

Datei:
- `src/namegen/data/professions_regelwiki.toml`

Hier gehört hinein:
- Berufe, die als Teil des allgemeinen professionellen Aventurien-Katalogs gelten
- die fachliche Zuordnung zu `geweihte`, `zauberer`, `kaempfer`, `profan`

Dann hier ergänzen, wenn:
- die Profession global oder allgemein regelrelevant ist
- sie nicht an nur eine einzelne Region gebunden ist

#### 2. Regionale oder kulturelle Zusatzberufe

Datei:
- Kultur: `src/namegen/data/cultures/<culture_id>.toml`
- Region: `src/namegen/data/<region_id>.toml`

Hier gehört hinein:
- Berufe, die nur in dieser Kultur oder Region typisch sind
- Berufe, die zwar fachlich existieren, aber nicht überall erzeugt werden sollen

Unter `[character]` sind zwei Formen erlaubt:

```toml
professions = ["Bergmann", "Förster", "Koschbauer"]
```

oder strukturiert:

```toml
professions = [
  { name = "Graumagier aus Perricum", categories = ["zauberer"], themes = ["graumagier_aus_perricum"], weight = 5 },
]
```

Faustregel:
- **Freier String** reicht für normale regionale Zusatzberufe.
- **Strukturierter Eintrag** ist richtig, wenn Kategorie, Theme oder Gewicht explizit gesteuert werden sollen.

#### 3. `professions.toml`

Datei:
- `src/namegen/data/professions.toml`

Status:
- aktuell **kein führender Runtime-Katalog** für die Charakter-Professionsauswahl

Das bedeutet:
- neue produktive Professionslogik bitte **nicht primär hier** eintragen
- stattdessen `professions_regelwiki.toml` und die passenden Kultur-/Regionsdateien pflegen

## Themen-Gruppen

Datei für die Definition:
- `src/namegen/data/profession_themes.toml`

Datei für die Nutzung:
- eine Kultur- oder Regionsdatei mit strukturierten Professionseinträgen

Eine Themen-Gruppe besteht aus zwei Teilen:

1. **Thema definieren**

```toml
[themes.graumagier_aus_perricum]
label = "Graumagier aus Perricum"
description = "Regionale Themenschablone für gildenmagische Figuren aus Perricum."
```

2. **Thema an konkrete Profession hängen**

```toml
[character]
professions = [
  { name = "Graumagier aus Perricum", categories = ["zauberer"], themes = ["graumagier_aus_perricum"], weight = 5 },
]
```

Dann eine Themen-Gruppe anlegen, wenn:
- der Nutzer gezielt eine fachliche Kombination auswählen können soll
- es nicht nur um eine Kategorie wie `zauberer`, sondern um einen engeren Kontext geht
- Beispiele sind lokale Magiertraditionen, Orden, Schulen, Kultgruppen oder ähnliche Schwerpunkte

Wichtig:
- Themen-Gruppen sollen **stabile IDs** bekommen, nicht nur schöne Labels
- Themen werden in UI und CLI nur angezeigt, wenn sie für die aktuelle Auswahl tatsächlich existieren

## Eigenschaften, Sprachen, Talente und sonstiger Charakter-Content

Diese Felder liegen in `[character]` und werden je nach Geltungsbereich in Spezies-, Kultur- oder Regionsdateien gepflegt:

- `languages`
- `scripts`
- `local_knowledge`
- `social_status`
- `typical_advantages`
- `typical_disadvantages`
- `typical_talents`
- `personality`
- `motivations`
- `quirks`
- `hair`
- `eyes`
- `build`

Faustregel:
- **Biologisch oder speziesweit**: Spezies-Datei
- **kulturell typisch**: Kultur-Datei
- **lokal besonders**: Regionsdatei

## Wann gehört was wohin?

### Entscheidungsbaum

Wenn du neuen Content hinzufügen willst, frage in dieser Reihenfolge:

1. Gilt das für alle Vertreter einer Spezies?
Dann in `src/namegen/data/species/`.

2. Gilt das für eine ganze Kultur, unabhängig von einer Unterregion?
Dann in `src/namegen/data/cultures/`.

3. Gilt das nur lokal oder soll nur lokal auswählbar sein?
Dann in `src/namegen/data/<region_id>.toml`.

4. Ist es eine allgemeine Profession mit globaler Kategorie?
Dann in `src/namegen/data/professions_regelwiki.toml`.

5. Ist es eine thematische Auswahl wie `Graumagier aus Perricum`?
Dann Thema in `src/namegen/data/profession_themes.toml` definieren und die konkrete Profession strukturiert an Kultur oder Region hängen.

6. Ist es nur eine technische oder historische Restliste?
Dann prüfen, ob sie überhaupt noch zur Laufzeit benutzt wird, bevor neue Daten eingetragen werden.

## Typische Änderungen nach Inhaltsart

### Nur neue Namen in bestehender Region

Ändern:
- `src/namegen/data/<region_id>.toml`

Tests:
- mindestens `uv run pytest tests/test_loader.py tests/test_generator.py`

### Neue Region innerhalb bestehender Kultur

Ändern:
- neue Datei `src/namegen/data/<region_id>.toml`
- bei Bedarf `src/namegen/loader.py`, falls neue Zuordnungslogik nötig ist
- bei Bedarf `src/namegen/catalog.py`, wenn die Region anders im Katalog erscheinen soll

Tests:
- `uv run pytest tests/test_loader.py tests/test_regions.py tests/test_generator.py`

### Neue Kultur

Ändern:
- neue Datei `src/namegen/data/cultures/<culture_id>.toml`
- mindestens eine passende Regions- oder kulturbasierte Auswahl prüfen
- bei Bedarf Mapping in `src/namegen/loader.py`

Tests:
- `uv run pytest tests/test_loader.py tests/test_regions.py tests/test_generator.py`

### Neue Spezies

Ändern:
- neue Datei `src/namegen/data/species/<species_id>.toml`
- meistens zusätzlich Loader-/Catalog-Mappings
- passende Kultur- oder Regionsdaten an diese Spezies anbinden

Tests:
- `uv run pytest tests/test_loader.py tests/test_regions.py tests/test_generator.py tests/test_chargen.py`

### Neue allgemeine Profession

Ändern:
- `src/namegen/data/professions_regelwiki.toml`

Tests:
- `uv run pytest tests/test_chargen.py tests/test_cli.py`

### Neue regionale Profession

Ändern:
- `src/namegen/data/<region_id>.toml` oder `src/namegen/data/cultures/<culture_id>.toml`

Tests:
- `uv run pytest tests/test_chargen.py`

### Neue Themen-Gruppe

Ändern:
- `src/namegen/data/profession_themes.toml`
- passende Region/Kultur mit strukturiertem Professions-Eintrag
- optional Doku oder Beispiele

Tests:
- `uv run pytest tests/test_chargen.py tests/test_cli.py tests/test_web_generator_routes.py`

## Checkliste vor dem Commit

1. Liegt der Content im richtigen fachlichen Layer?
2. Ist die ID konsistent benannt, klein geschrieben und mit Unterstrichen?
3. Wird wirklich die Runtime-Datei erweitert und nicht nur eine Alt- oder Hilfsdatei?
4. Sind Name und Notizen in `meta` sinnvoll gepflegt?
5. Hat neuer Compose-Content ausreichend Prefix/Suffix-Daten?
6. Sind neue Themen-Gruppen sowohl definiert als auch tatsächlich verwendet?
7. Sind neue regionale Professionen als String oder als strukturierter Eintrag korrekt modelliert?
8. Laufen die passenden Tests?

## Empfohlene Kommandos

```bash
uv sync
env UV_CACHE_DIR=/tmp/uv-cache uv run pytest
env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
```

Für fokussierte Content-Änderungen oft sinnvoll:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_loader.py tests/test_generator.py tests/test_chargen.py
```

## Relevante Dateien im Überblick

- `src/namegen/loader.py`: lädt und merged Spezies, Kultur und Region
- `src/namegen/catalog.py`: baut den Auswahlkatalog für CLI und Web
- `src/namegen/generator.py`: reine Namensgenerierung
- `src/namegen/chargen.py`: Charaktergenerierung inklusive Professionen und Themen
- `src/namegen/models.py`: Pydantic-Modelle für die TOML-Strukturen
- `src/namegen/data/species/*.toml`: Speziesdaten
- `src/namegen/data/cultures/*.toml`: Kulturdaten
- `src/namegen/data/*.toml`: konkrete Regionen
- `src/namegen/data/professions_regelwiki.toml`: globaler Professionskatalog nach Kategorien
- `src/namegen/data/profession_themes.toml`: Themen-Gruppen für Professionen

