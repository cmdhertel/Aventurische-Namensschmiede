"""Interaktives Menü für die Namens-Generierung."""

from __future__ import annotations

from pathlib import Path

import questionary
from rich.console import Console
from rich.rule import Rule

from .chargen import generate_character
from .generator import GeneratorError, generate
from .loader import LoaderError, list_regions, load_region
from .models import CharacterResult, Gender, GenerationMode, NameResult, ProfessionCategory
from .models import ExperienceLevel
from .output import OutputFormat, default_filename, write as output_write

console = Console()

_STYLE = questionary.Style([
    ("qmark",       "fg:#a855f7 bold"),
    ("question",    "bold"),
    ("answer",      "fg:#a855f7 bold"),
    ("pointer",     "fg:#a855f7 bold"),
    ("highlighted", "fg:#a855f7 bold"),
    ("selected",    "fg:#a855f7"),
])

# Formate die immer in eine Datei schreiben oder nicht (clipboard)
_ALWAYS_FILE  = {OutputFormat.PDF}
_NEVER_FILE   = {OutputFormat.RICH, OutputFormat.CLIPBOARD}


def run() -> None:
    """Startet das interaktive Menü. Läuft bis der Nutzer abbricht."""
    console.print()
    console.print(Rule("[bold magenta]Das Schwarze Auge – Namensgenerator[/bold magenta]"))
    console.print()

    while True:
        config = _ask_configuration()
        if config is None:
            break

        mode, region, gender, count, show_components, character, profession_category, experience, fmt, dest = config
        _generate_and_output(mode, region, gender, count, show_components, character, profession_category, experience, fmt, dest)

        console.print()
        again = questionary.confirm(
            "Weitere Namen generieren?",
            default=True,
            style=_STYLE,
        ).ask()
        if not again:
            break
        console.print()

    console.print()
    console.print("[dim]Auf Wiedersehen![/dim]")


def _ask_configuration() -> tuple[GenerationMode, str, Gender, int, bool, bool, ProfessionCategory, ExperienceLevel, OutputFormat, Path | None] | None:
    """Fragt alle Einstellungen interaktiv ab. Gibt None zurück bei Abbruch (Ctrl+C)."""

    # ── Modus ──────────────────────────────────────────────────────────────────
    mode_str = questionary.select(
        "Generierungsmodus:",
        choices=[
            questionary.Choice("Einfach       – Namen aus vordefinierten Listen", value="simple"),
            questionary.Choice("Komposition   – Namen aus Silbenbausteinen",      value="compose"),
        ],
        style=_STYLE,
    ).ask()
    if mode_str is None:
        return None
    mode = GenerationMode(mode_str)

    # ── Region ─────────────────────────────────────────────────────────────────
    try:
        region_ids = list_regions()
    except Exception as exc:
        console.print(f"[red]Fehler beim Laden der Regionen:[/red] {exc}")
        return None

    region_choices = []
    for rid in region_ids:
        try:
            data = load_region(rid)
            label = f"{data.meta.region:<18} {data.meta.notes}"
        except Exception:
            label = rid
        region_choices.append(questionary.Choice(label, value=rid))

    region = questionary.select("Region:", choices=region_choices, style=_STYLE).ask()
    if region is None:
        return None

    # ── Geschlecht ─────────────────────────────────────────────────────────────
    gender_str = questionary.select(
        "Geschlecht:",
        choices=[
            questionary.Choice("Beliebig", value="any"),
            questionary.Choice("Männlich", value="male"),
            questionary.Choice("Weiblich", value="female"),
        ],
        style=_STYLE,
    ).ask()
    if gender_str is None:
        return None
    gender = Gender(gender_str)

    # ── Anzahl ─────────────────────────────────────────────────────────────────
    count_str = questionary.text(
        "Anzahl Namen:",
        default="1",
        validate=lambda v: True if (v.isdigit() and 1 <= int(v) <= 100)
                           else "Bitte eine Zahl zwischen 1 und 100 eingeben.",
        style=_STYLE,
    ).ask()
    if count_str is None:
        return None
    count = int(count_str)

    # ── Silbenbausteine (nur Compose) ──────────────────────────────────────────
    show_components = False
    if mode == GenerationMode.COMPOSE:
        show_components = questionary.confirm(
            "Silbenbausteine anzeigen?",
            default=False,
            style=_STYLE,
        ).ask()
        if show_components is None:
            return None

    # ── Charakterbogen ─────────────────────────────────────────────────────────
    character = questionary.confirm(
        "Charakterbogen generieren? (Beruf, Alter, Eigenschaften)",
        default=False,
        style=_STYLE,
    ).ask()
    if character is None:
        return None

    # ── Berufskategorie (nur wenn Charakterbogen aktiv) ────────────────────────
    profession_category = ProfessionCategory.ALL
    experience = ExperienceLevel.GESELLE
    if character:
        cat_str = questionary.select(
            "Berufskategorie:",
            choices=[
                questionary.Choice("Alle Professionen",     value="alle"),
                questionary.Choice("Geweihte",              value="geweihte"),
                questionary.Choice("Zauberer",              value="zauberer"),
                questionary.Choice("Kämpfer & Ordensleute", value="kaempfer"),
                questionary.Choice("Profane Berufe",        value="profan"),
            ],
            style=_STYLE,
        ).ask()
        if cat_str is None:
            return None
        profession_category = ProfessionCategory(cat_str)

        experience_str = questionary.select(
            "Erfahrungsstufe:",
            choices=[
                questionary.Choice("Lehrling", value="lehrling"),
                questionary.Choice("Geselle", value="geselle"),
                questionary.Choice("Meister", value="meister"),
                questionary.Choice("Veteran", value="veteran"),
            ],
            default="geselle",
            style=_STYLE,
        ).ask()
        if experience_str is None:
            return None
        experience = ExperienceLevel(experience_str)

    # ── Ausgabeformat ──────────────────────────────────────────────────────────
    fmt_str = questionary.select(
        "Ausgabeformat:",
        choices=[
            questionary.Choice("Terminal-Tabelle  (Rich)",   value="rich"),
            questionary.Choice("Nur Namen         (Plain)",  value="plain"),
            questionary.Choice("JSON",                       value="json"),
            questionary.Choice("CSV",                        value="csv"),
            questionary.Choice("Markdown",                   value="markdown"),
            questionary.Choice("Zwischenablage    (Clipboard)", value="clipboard"),
            questionary.Choice("PDF",                        value="pdf"),
        ],
        style=_STYLE,
    ).ask()
    if fmt_str is None:
        return None
    fmt = OutputFormat(fmt_str)

    # ── Ausgabedatei ───────────────────────────────────────────────────────────
    dest: Path | None = None

    if fmt in _ALWAYS_FILE:
        # PDF: immer eine Datei, Standardname vorschlagen
        filename = questionary.text(
            "Dateiname:",
            default=default_filename(fmt, region),
            style=_STYLE,
        ).ask()
        if filename is None:
            return None
        dest = Path(filename)

    elif fmt not in _NEVER_FILE:
        # plain/json/csv/markdown: optional in Datei speichern
        save_to_file = questionary.confirm(
            "In Datei speichern?",
            default=False,
            style=_STYLE,
        ).ask()
        if save_to_file is None:
            return None
        if save_to_file:
            filename = questionary.text(
                "Dateiname:",
                default=default_filename(fmt, region),
                style=_STYLE,
            ).ask()
            if filename is None:
                return None
            dest = Path(filename)

    return mode, region, gender, count, show_components, character, profession_category, experience, fmt, dest


def _generate_and_output(
    mode: GenerationMode,
    region: str,
    gender: Gender,
    count: int,
    show_components: bool,
    character: bool,
    profession_category: ProfessionCategory,
    experience: ExperienceLevel,
    fmt: OutputFormat,
    dest: Path | None,
) -> None:
    try:
        if character:
            results: list[CharacterResult] | list[NameResult] = [
                generate_character(region=region, mode=mode, gender=gender,
                                   profession_category=profession_category,
                                   experience=experience)
                for _ in range(count)
            ]
        else:
            results = [
                generate(region=region, mode=mode, gender=gender)
                for _ in range(count)
            ]
    except (GeneratorError, LoaderError) as exc:
        console.print(f"[red]Fehler:[/red] {exc}")
        return

    console.print()
    output_write(results, fmt=fmt, dest=dest, show_components=show_components)
