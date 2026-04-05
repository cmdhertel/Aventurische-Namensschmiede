# Abgleich: Aventurische Namen vs. `namegen`

Diese Übersicht gleicht die regionalen, kulturellen und speziesspezifischen Kapitel aus `Aventurische Namen` mit den in `namegen` verfügbaren TOMLs ab.

## Bereits vor dieser Änderung vorhanden

| Buchkapitel | `namegen`-ID |
|---|---|
| Al'Anfa & Tiefer Süden | `alanfa` |
| Andergast | `andergast` |
| Aranien | `aranien` |
| Bornland | `bornland` |
| Ferkina | `ferkina` |
| Fjarninger | `fjarninger` |
| Freie Städte des Nordens & Dominium Donnerbach | `freiestaedte` |
| Gjalsker | `gjalsker` |
| Hoher Norden | `hoher_norden` |
| Horasreich | `horasreich` |
| Kemi | `kemi` |
| Maraskan | `maraskan` |
| Mittelreich: Albernia | `mittelreich_albernia` |
| Mittelreich: Almada | `mittelreich_almada` |
| Mittelreich: Garetien | `mittelreich_garetien` |
| Mittelreich: Greifenfurt | `mittelreich_greifenfurt` |
| Mittelreich: Kosch | `mittelreich_kosch` |
| Mittelreich: Perricum | `mittelreich_perricum` |
| Mittelreich: Rabenmark | `mittelreich_rabenmark` |
| Mittelreich: Rommilyser Mark | `mittelreich_rommilysermark` |
| Mittelreich: Sonnenmark | `mittelreich_sonnenmark` |
| Mittelreich: Tobrien | `mittelreich_tobrien` |
| Nivesen | `nivesen` |
| Novadis | `novadis` |
| Thorwal | `thorwal` |
| Auelfen | `auelfen` |
| Firnelfen | `elfen_firnelfen` |
| Waldelfen | `elfen_waldelfen` |
| Ambosszwerge | `ambosszwerge` |

## Mit dieser Änderung ergänzt

| Buchkapitel | Neue `namegen`-ID | Hinweis |
|---|---|---|
| Kalifat | `kalifat` | eigener novadischer Zuschnitt mit Patronymik |
| Mittelreich: Nordmarken | `mittelreich_nordmarken` | konservative mittelreichische Namen |
| Mittelreich: Warunk | `mittelreich_warunk` | tobrisch-rondrianisch, Schattenland-Nachklang |
| Mittelreich: Weiden | `mittelreich_weiden` | altertümlich-weidener Namenraum |
| Mittelreich: Windhag | `mittelreich_windhag` | albernisch-nordmärkisch gemischt |
| Norbarden | `norbarden` | Sippennamen der Meschpochen |
| Nostria | `nostria` | altmodische nostrische Namen |
| Selem | `selem` | selemer Zischlaut-Varianten |
| Südmeer & Bukanier | `suedmeer_bukanier` | charyptische Piratennamen |
| Svellttal | `svelltal` | gemischter nördlicher Grenzraum |
| Thalusien | `thalusien` | tulamidisch mit regionalen Eigenformen |
| Trollzacker | `trollzacker` | trollzackische Stammesnamen |
| Tulamidenlande | `tulamidenlande` | breiter tulamidischer Kulturraum |
| Waldmenschenstämme & Utulu | `waldmenschen_utulu` | als menschlicher Kulturraum modelliert |
| Zahori | `zahori` | fahrendes Volk mit Sippennamen |
| Zyklopeninseln | `zyklopeninseln` | zyklopäische Inselnamen |
| Steppenelfen | `elfen_steppenelfen` | elfischer Reitervolk-Zuschnitt |
| Hochelfen | `elfen_hochelfen` | mythisch-elfischer Altstil |
| Shakagra | `elfen_shakagra` | Nachtalben-Profil |
| Brillantzwerge | `brillantzwerge` | zwergische Feinsinn-Variante |
| Hügelzwerge | `huegelzwerge` | menschennahere Zwergennamen |
| Tiefzwerge | `tiefzwerge` | reduzierte, verfallene Namensformen |

## Bewusst nicht als eigene Region umgesetzt

| Buchkapitel | Grund |
|---|---|
| Namen der Urtulamiden | historischer Exkurs, kein eigenes modernes Herkunftsprofil |
| Namen der Bosparaner | historischer Exkurs |
| Namen der Nordprovinzen | historischer Exkurs |
| Alhanische Namen | historischer Exkurs, fließt in Norbarden-Kontext ein |
| Elemitische Namen | historischer Exkurs, Selem deckt den spielbaren Gegenwartsraum ab |
| Cyclopeische Namen | historischer Exkurs, Zyklopeninseln decken den spielbaren Gegenwartsraum ab |
| Zwölfgötternamen | kein regionales Herkunftsprofil |
| Magier- und Weihenamen | kein regionales Herkunftsprofil |
| Bühnen- & Künstlernamen | kein regionales Herkunftsprofil |
| Namen für Tierbegleiter | kein regionales Herkunftsprofil |
| Namen für Waffen | kein regionales Herkunftsprofil |
| Anagramme / Sprechende Namen / Silbenbaukasten | Hilfskapitel, keine Regionsdaten |

## Hinweise

- `goblins` und `grolme` bleiben vorerst unmodelliert, weil das aktuelle Datenmodell keine passenden Speziesprofile dafür mitbringt und die vorhandenen `species/*.toml` nur Mensch, Elf, Halbelf, Zwerg, Ork und Achaz abdecken.
- `Schattenlande` wird nicht als eigenes generisches Profil angelegt. Die im Buch klar benennbaren Gegenwartsräume werden über `mittelreich_warunk` und bestehende tobrische / rabenmärkische Daten abgedeckt.
