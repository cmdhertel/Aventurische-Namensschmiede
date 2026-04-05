"""Typer CLI entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from click.core import ParameterSource
from rich import box
from rich.console import Console
from rich.table import Table

from .chargen import generate_character, get_profession_groups
from .generator import GeneratorError, generate
from .loader import LoaderError, list_regions, load_region
from .models import ExperienceLevel, Gender, GenerationMode, ProfessionCategory
from .output import OutputFormat, write as output_write
from .models import Gender, GenerationMode, ProfessionCategory
from .output import write as output_write

app = typer.Typer(
    name="namegen",
    help="Generate names for Das Schwarze Auge (The Dark Eye) RPG.",
    add_completion=False,
    rich_markup_mode="rich",
    invoke_without_command=True,
)
console = Console()


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Startet das interaktive Menü wenn kein Unterbefehl angegeben wird."""
    if ctx.invoked_subcommand is None:
        from . import interactive
        interactive.run()


# ── Shared option types ────────────────────────────────────────────────────────

RegionArg     = Annotated[str,           typer.Argument(help="Region ID (z.B. kosch, mittelreich, horasreich).")]
GenderOpt     = Annotated[Gender,        typer.Option("--gender", "-g", help="male | female | any", case_sensitive=False)]
CountOpt      = Annotated[int,           typer.Option("--count", "-n", help="Anzahl Namen.", min=1, max=100)]
ComponentsOpt = Annotated[bool,          typer.Option("--components", "-c", help="Silbenbausteine anzeigen (nur compose).")]
CharacterOpt  = Annotated[bool,               typer.Option("--character", "-C", help="Vollständigen Charakter generieren (Beruf, Alter, Eigenschaften).")]
CategoryOpt   = Annotated[ProfessionCategory, typer.Option("--profession-category", "--category", "-k", help="Berufskategorie: alle | geweihte | zauberer | kaempfer | profan", case_sensitive=False)]
ExperienceOpt = Annotated[ExperienceLevel, typer.Option("--experience", help="Erfahrungsstufe: lehrling | geselle | meister | veteran", case_sensitive=False)]
InfixProbOpt  = Annotated[float | None, typer.Option("--infix-probability", min=0.0, max=1.0, help="Überschreibt im Compose-Modus temporär die Infix-Wahrscheinlichkeit für Vor- und Nachnamen.")]
FormatOpt     = Annotated[OutputFormat,       typer.Option("--format", "-f", help="Ausgabeformat: rich | plain | json | csv | markdown | clipboard | pdf", case_sensitive=False)]
OutputOpt     = Annotated[Optional[Path],     typer.Option("--output", "-o", help="Ausgabedatei (Standard: stdout / Standardname für PDF).")]
RegionArg = Annotated[
    str,
    typer.Argument(help="Region ID (z.B. kosch, mittelreich, horasreich)."),
]
GenderOpt = Annotated[
    Gender,
    typer.Option("--gender", "-g", help="male | female | any", case_sensitive=False),
]
CountOpt = Annotated[
    int,
    typer.Option("--count", "-n", help="Anzahl Namen.", min=1, max=100),
]
ComponentsOpt = Annotated[
    bool,
    typer.Option("--components", "-c", help="Silbenbausteine anzeigen (nur compose)."),
]
CharacterOpt = Annotated[
    bool,
    typer.Option(
        "--character",
        "-C",
        help="Vollständigen Charakter generieren (Beruf, Alter, Eigenschaften).",
    ),
]
CategoryOpt = Annotated[
    ProfessionCategory,
    typer.Option(
        "--category",
        "-k",
        help="Berufskategorie: alle | geweihte | zauberer | kaempfer | profan",
        case_sensitive=False,
    ),
]
FormatOpt = Annotated[
    OutputFormat,
    typer.Option(
        "--format",
        "-f",
        help="Ausgabeformat: rich | plain | json | csv | markdown | clipboard | pdf",
        case_sensitive=False,
    ),
]
OutputOpt = Annotated[
    Path | None,
    typer.Option(
        "--output", "-o", help="Ausgabedatei (Standard: stdout / Standardname für PDF)."
    ),
]


# ── Commands ───────────────────────────────────────────────────────────────────

@app.command("simple")
def cmd_simple(
    ctx:             typer.Context,
    region: RegionArg,
    gender:          GenderOpt     = Gender.ANY,
    count:           CountOpt      = 1,
    character:       CharacterOpt  = False,
    category:        CategoryOpt   = ProfessionCategory.ALL,
    experience:      ExperienceOpt = ExperienceLevel.GESELLE,
    fmt:             FormatOpt     = OutputFormat.RICH,
    output:          OutputOpt     = None,
) -> None:
    """Namen aus vordefinierten Listen generieren."""
    _validate_character_options(ctx, character)
    _run(region, GenerationMode.SIMPLE, gender, count, show_components=False,
         character=character, category=category, experience=experience,
         fmt=fmt, dest=output)


@app.command("compose")
def cmd_compose(
    ctx:             typer.Context,
    region: RegionArg,
    gender:          GenderOpt     = Gender.ANY,
    count:           CountOpt      = 1,
    show_components: ComponentsOpt = False,
    character:       CharacterOpt  = False,
    category:        CategoryOpt   = ProfessionCategory.ALL,
    experience:      ExperienceOpt = ExperienceLevel.GESELLE,
    infix_probability: InfixProbOpt = None,
    fmt:             FormatOpt     = OutputFormat.RICH,
    output:          OutputOpt     = None,
) -> None:
    """Namen aus Silbenbausteinen zusammensetzen."""
    _validate_character_options(ctx, character)
    _run(region, GenerationMode.COMPOSE, gender, count, show_components,
         character=character, category=category, experience=experience,
         infix_probability_override=infix_probability, fmt=fmt, dest=output)


@app.command("menu")
def cmd_menu() -> None:
    """Interaktives Menü zur Namens-Generierung."""
    from . import interactive
    interactive.run()


@app.command("regions")
def cmd_regions() -> None:
    """Alle verfügbaren Regionen auflisten."""
    try:
        ids = list_regions()
    except Exception as exc:
        console.print(f"[red]Fehler:[/red] {exc}")
        raise typer.Exit(1) from None

    table = Table("Region", "Anzeigename", "Beschreibung", box=box.SIMPLE, header_style="bold cyan")
    for region_id in ids:
        try:
            r = load_region(region_id)
            table.add_row(region_id, r.meta.region, r.meta.notes)
        except Exception:
            table.add_row(region_id, "?", "[red]Fehler beim Laden[/red]")

    console.print(table)


@app.command("professions")
def cmd_professions() -> None:
    """Alle verfügbaren Professionen geordnet nach Kategorie anzeigen."""
    for title, professions in get_profession_groups():
        table = Table(title, box=box.SIMPLE, header_style="bold cyan")
        for profession in professions:
            table.add_row(profession)
        console.print(table)


# ── Shared generation + output ─────────────────────────────────────────────────

def _run(
    region: str,
    mode: GenerationMode,
    gender: Gender,
    count: int,
    show_components: bool,
    fmt: OutputFormat,
    dest: Path | None,
    character: bool = False,
    category: ProfessionCategory = ProfessionCategory.ALL,
    experience: ExperienceLevel = ExperienceLevel.GESELLE,
    infix_probability_override: float | None = None,
) -> None:
    try:
        if character:
            results = [
                generate_character(region=region, mode=mode, gender=gender,
                                   profession_category=category, experience=experience,
                                   infix_probability_override=infix_probability_override)
                for _ in range(count)
            ]
        else:
            results = [
                generate(region=region, mode=mode, gender=gender,
                         infix_probability_override=infix_probability_override)
                for _ in range(count)
            ]
    except (GeneratorError, LoaderError) as exc:
        console.print(f"[red]Fehler:[/red] {exc}")
        raise typer.Exit(1) from None

    output_write(results, fmt=fmt, dest=dest, show_components=show_components)


def _validate_character_options(ctx: typer.Context, character: bool) -> None:
    if character:
        return

    category_source = ctx.get_parameter_source("category")
    experience_source = ctx.get_parameter_source("experience")
    if category_source not in (None, ParameterSource.DEFAULT):
        console.print("[red]Fehler:[/red] --profession-category erfordert --character.")
        raise typer.Exit(1)
    if experience_source not in (None, ParameterSource.DEFAULT):
        console.print("[red]Fehler:[/red] --experience erfordert --character.")
        raise typer.Exit(1)
