# Profession Audit

Stand: 2026-04-06

## Ziel

Dieses Dokument auditierte **alle aktuell im Repo definierten Professionen** und bewertet, ob sie am richtigen Ort liegen:

- `src/namegen/data/professions_regelwiki.toml` für wirklich globale Professionen
- Kultur-Dateien für kulturgebundene Professionen
- Regions-Dateien für regionale Professionen
- `profession_themes.toml` plus strukturierte `profession_entries` für eng gefasste Themen, Orden, Schulen oder Traditionslinien

Leitregel für dieses Audit:

- **Strikt spezifisch raus aus global**.
- Wenn eine Profession klar an Spezies, Kultur, Region, Schule, Orden, Tempel, Tradition oder eine benannte Gruppe gebunden ist, soll sie **nicht** im globalen Katalog verbleiben.
- Wenn ich die fachliche Einordnung nicht belastbar genug belegen konnte, ist der Fall als `REVIEW` markiert und muss gemeinsam entschieden werden.

## Methodik

Ich habe alle Professionen aus folgenden Quellen inventarisiert:

- `src/namegen/data/professions_regelwiki.toml`
- alle `character.professions` in `src/namegen/data/*.toml`
- alle `character.professions` in `src/namegen/data/cultures/*.toml`
- alle strukturierten `character.profession_entries`

Zusätzlich habe ich den Audit mit externen Quellen abgeglichen:

- DSA Regelwiki Professionen: <https://dsa.ulisses-regelwiki.de/professionen.html>
- DSA Regelwiki Stammesachaz: <https://dsa.ulisses-regelwiki.de/Kul_Stammesachaz.html>
- DSA Regelwiki Ucuriatin: <https://dsa.ulisses-regelwiki.de/Gew_ucuriatin.html>
- DSA Regelwiki Rabengardistin: <https://dsa.ulisses-regelwiki.de/Gew_rabengardistin.html>
- Wiki Aventurica Orden des Schwarzen Raben: <https://de.wiki-aventurica.de/wiki/Orden_des_Schwarzen_Raben>
- Wiki Aventurica Helden der Flusslande/Klappentext: <https://de.wiki-aventurica.de/wiki/Helden_der_Flusslande/Klappentext>

Wichtige externe Prüfpunkte:

- Die Regelwiki führt `Achazschamane` bei den Stammesachaz als übliche geweihten Profession. Das spricht klar für **spezies-/kulturgebundene** Ablage statt global.
- `Ucuriatin` und `Rabengardistin` haben in der Regelwiki explizite Voraussetzungen wie `Prinzipientreue II (Ordensregeln)` und `Verpflichtungen II (Orden)`. Das spricht klar für **Thema/Orden** statt global.
- Wiki Aventurica bestätigt für die `Rabengardistin` die Bindung an den `Orden des Schwarzen Raben`.
- Wiki Aventurica beschreibt den `Koscher Almgreve` ausdrücklich als zur Flusslande-Region passende Profession. Das spricht klar für **regional** statt global.

## Ergebnis in Zahlen

- `367` eindeutige Professionsnamen im gesamten Repo
- `207` globale Einträge in `professions_regelwiki.toml`
- `276` lokale oder kulturelle Professionsdefinitionen
- `58` Namen kommen in mehr als einer Datei vor

Audit-Status:

- `55` globale Einträge sollten aus dem globalen Katalog heraus
- `13` globale Einträge dürfen global bleiben und lokal zusätzlich zur Gewichtung auftauchen
- `0` Fälle sind derzeit bewusst als `REVIEW` markiert
- `109` globale Einträge können im aktuellen Stand global bleiben
- `161` lokale Einträge sind an ihrem spezifischen Ort plausibel und müssen nicht globalisiert werden

## Entscheidungsregeln

Eintrag bleibt global:

- breite aventurische Berufsform ohne enge Orts-, Kultur-, Ordens- oder Speziesbindung

Eintrag raus aus global:

- Demonym oder Ortsbezug im Namen
- explizite Spezies- oder Kulturbindung
- benannter Orden, Tempel, Schule, Traditionslinie oder Sondergruppe
- klar benannte regionale Variante einer ansonsten allgemeinen Profession

Global plus lokale Gewichtung ist okay:

- die Profession ist aventurisch allgemein
- lokale Datei will nur Häufigkeit oder regionale Typizität steigern
- die lokale Definition ersetzt keinen engeren Spezialfall

`REVIEW`:

- Fachbindung wahrscheinlich, aber noch nicht belastbar genug belegt
- oder gleicher Name wird lokal benutzt, obwohl unklar ist, ob damit dieselbe oder eine spezifischere Unterform gemeint ist

## Klare Umzüge aus Global

Diese Professionen sind nach aktuellem Audit **zu spezifisch für den globalen Katalog**:

- `Achazschamane`
- `Adoru-Magier`
- `Albernischer Seefahrer`
- `Aranischer Sippenkrieger`
- `Baburiner Kriegerin`
- `Badilakanerin`
- `Balihoer Krieger`
- `Brobim-Geode`
- `Chababischer Rechtswahrer`
- `Dajin-Buskur`
- `Echsenreiter`
- `Efferdgeweihter der Siebenwindküste`
- `Elenviner Kriegerin`
- `Ferdoker Lanzerin`
- `Ferkinaschamane`
- `Garether Kriegerin`
- `Harodische Pflanzenkundlerin`
- `Havener Krieger`
- `Horasischer Kartograph`
- `Hylailer Kriegerin`
- `Kasknuk (Nivesenschamane)`
- `Koscher Almgreve`
- `Küstenschmugglerin aus Havena`
- `Lyceum-Kurtisane`
- `Mada Basari-Ordensmitglied`
- `Mengbiller Krieger`
- `Mitglied des Dreischwesternordens`
- `Neersander Krieger`
- `Neethaner Kriegerin`
- `Ordenskrieger der Tarisharim`
- `Ordenskriegerin der Al’Drakorhim`
- `Ordenskriegerin der Beni Uchakâni`
- `Ordensmitglied der Beni Fessiri`
- `Ottajasko-Rekkerin`
- `Premer Kriegerin`
- `Rabengardistin`
- `Rahjakavalier`
- `Rhodensteinerin`
- `Ritter der Streitenden Königreiche`
- `Rommilyser Kriegerin`
- `Runenschöpfer (Runahöfundur)`
- `Schatzsucher der Siebenwindküste`
- `Skuldrun (Fjarningerschamanin)`
- `Tairachschamane`
- `Thorwaler Krieger`
- `Thorwalsche Godi`
- `Trollzackerschamanin`
- `Ucuriatin`
- `Vinsalter Krieger`
- `Windhager Sippenkrieger`
- `Xorloscher Drachenkämpfer`
- `Yppolitanerin`
- `Zwergenkrieger nach Hardas`
- `Zyklopäische Philosophin`
- `Zyklopäischer Avesgeweihter`

Empfohlene Zielorte:

- **Region** bei klar lokalem Bezug wie `Koscher Almgreve`, `Ferdoker Lanzerin`, `Havener Krieger`
- **Kultur/Spezies** bei klarer Volks- oder Speziesbindung wie `Achazschamane`, `Ferkinaschamane`, `Trollzackerschamanin`
- **Theme** bei Orden, Schulen, Traditionslinien oder benannten Sonderformen wie `Rabengardistin`, `Ucuriatin`, `Rahjakavalier`, `Adoru-Magier`

## Global Plus Lokale Gewichtung ist Okay

Diese Namen dürfen global bestehen bleiben, wenn lokale Dateien sie nur zur Häufigkeitssteuerung erneut nennen:

- `Fallensteller`
- `Gelehrte`
- `Hirte`
- `Holzfäller`
- `Händler`
- `Jäger`
- `Perainegeweihter`
- `Prospektor`
- `Ritter`
- `Schmied`
- `Seesoldat`
- `Söldner`
- `Wildniskundiger`

Dabei ist der fachliche Punkt wichtig:

- Die lokale Dopplung ist hier **keine andere Profession**, sondern nur regionale Gewichtung.
- Beispiel: `Perainegeweihter` darf global bleiben; `svelltal.toml` ist dann nur eine lokale Häufigkeitsaussage.

## Review Mit Dir

Alle früheren `REVIEW`-Fälle sind inzwischen gemeinsam entschieden.

## Bereits Mit Dir Entschieden

Diese früheren `REVIEW`-Fälle sind entschieden und sollen bei der Umsetzung so behandelt werden:

- `Amazone` -> aus global raus; Zielort `culture: amazonen`
- `Ardarit` -> aus global raus; Zielort `theme` plus zusätzliche lokale Verankerung im `horasreich`
- `Bannstrahler` -> aus global raus; Zielort `theme` plus zusätzliche lokale Verankerung im `mittelreich`
- `Brenoch-Dûn (Gjalskerschamane)` -> aus global raus; Zielort `gjalsker`
- `Bruder des Feuers` -> aus global raus; Zielort `theme`
- `Chr’Ssir’Ssr-Priester` -> aus global raus; Zielort `species/culture: achaz` plus lokale Verankerung bei `ctki_ssrr`
- `Draconiterin` -> aus global raus; Zielort `theme` plus zusätzliche lokale Verankerung im `horasreich`
- `Etilianer` -> aus global raus; Zielort `theme`
- `Graveshpriester` -> aus global raus; Zielort `species/culture: ork` plus lokale Verankerung im `orkland`
- `Golgaritin` -> aus global raus; Zielort `theme` plus zusätzliche lokale Verankerung im `mittelreich`
- `H’Szint-Priester` -> aus global raus; Zielort `species/culture: achaz` plus lokale Verankerung bei `ctki_ssrr`
- `Ishannah al’Kira-Balayan` -> aus global raus; Zielort `theme` plus zusätzliche lokale Verankerung in `aranien`
- `Jäger der Verfluchten` -> aus global raus; Zielort `hoher_norden`
- `Kriegerin` -> global behalten; lokale Nennungen sind Gewichtung, keine Umklassifizierung
- `Noionit` -> aus global raus; Zielort `theme` plus zusätzliche lokale Verankerung in `selem`
- `Numinorupriester` -> aus global raus; Zielort `theme`
- `Ojomyaa – Priesterin der Vier` -> aus global raus; fachlich Zielort `culture: adoru`, bis zu einem Adoru-Kulturprofil ersatzweise `theme`
- `Qabaloth` -> aus global raus; Zielort `theme` plus zusätzliche lokale Verankerung in `aranien`
- `Rikaipriester` -> aus global raus; Zielort `species/culture: ork` plus lokale Verankerung im `orkland`
- `Rur-und-Gror-Priesterin` -> aus global raus; Zielort `maraskan`
- `Rosenritter` -> aus global raus; Zielort `theme` plus zusätzliche lokale Verankerung im `horasreich`
- `Säbeltänzerin` -> aus global raus; Zielort `theme` plus zusätzliche lokale Verankerung in tulamidisch geprägten Regionen
- `Shindai (Adoru-Schwertkämpfer)` -> aus global raus; fachlich Zielort `culture: adoru`, bis zu einem Adoru-Kulturprofil ersatzweise `theme`
- `Sonnenlegionärin` -> aus global raus; Zielort `theme` plus zusätzliche lokale Verankerung im `mittelreich`
- `Stammeskriegerin` -> global behalten; breite kulturübergreifende Oberprofession
- `Tahayaschamanin` -> aus global raus; Zielort `culture: waldmenschen/utulu` plus lokale Verankerung bei `waldmenschen_utulu`
- `Therbûnit` -> aus global raus; Zielort `theme`
- `Winhaller Kriegerin` -> aus global raus; Zielort `mittelreich_albernia`
- `Zsahh-Priesterin` -> aus global raus; Zielort `species/culture: achaz` plus lokale Verankerung bei `ctki_ssrr`

## Lokal Bereits Richtig Einsortiert

Die rein lokalen oder kulturellen Einträge sind im aktuellen Stand überwiegend plausibel abgelegt. Beispiele:

- `Graumagier aus Perricum` in `mittelreich_perricum.toml`
- `Koschbauer` in `mittelreich_kosch.toml`
- `Bingewächter` in `ambosszwerge.toml`
- `Ottajaskoeld` in `thorwal.toml`
- `Zauberweber` in den Elfkulturen

Diese Fälle brauchen derzeit **keine** Rückverschiebung in den globalen Katalog.

## Reihenfolge für die spätere Umsetzung

Wenn wir den Audit in Datenmigrationen umsetzen, ist diese Reihenfolge sinnvoll:

1. zuerst die `55` klaren Umzüge aus `professions_regelwiki.toml`
2. dann Duplikate bereinigen und Themes ergänzen
3. zuletzt Tests für Professionsauflösung und Vorschau nachziehen

## Konkrete nächste gemeinsame Entscheidung

Die `REVIEW`-Liste ist abgearbeitet. Der nächste sinnvolle Schritt ist jetzt die eigentliche Umsetzungsplanung:

- globale Liste nach den entschiedenen Umzügen bereinigen
- fehlende Theme- und Zielprofile ergänzen
- danach Duplikate und Tests nachziehen
