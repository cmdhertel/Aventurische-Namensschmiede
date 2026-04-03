"""Typer CLI entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from .chargen import generate_character
from .generator import GeneratorError, generate
from .loader import LoaderError, list_regions, load_region
from .models import Gender, GenerationMode, NameResult, ProfessionCategory
from .output import OutputFormat, write as output_write

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
CategoryOpt   = Annotated[ProfessionCategory, typer.Option("--category", "-k", help="Berufskategorie: alle | geweihte | zauberer | kaempfer | profan", case_sensitive=False)]
FormatOpt     = Annotated[OutputFormat,       typer.Option("--format", "-f", help="Ausgabeformat: rich | plain | json | csv | markdown | clipboard | pdf", case_sensitive=False)]
OutputOpt     = Annotated[Optional[Path],     typer.Option("--output", "-o", help="Ausgabedatei (Standard: stdout / Standardname für PDF).")]


# ── Commands ───────────────────────────────────────────────────────────────────

@app.command("simple")
def cmd_simple(
    region: RegionArg,
    gender:          GenderOpt     = Gender.ANY,
    count:           CountOpt      = 1,
    character:       CharacterOpt  = False,
    category:        CategoryOpt   = ProfessionCategory.ALL,
    fmt:             FormatOpt     = OutputFormat.RICH,
    output:          OutputOpt     = None,
) -> None:
    """Namen aus vordefinierten Listen generieren."""
    _run(region, GenerationMode.SIMPLE, gender, count, show_components=False,
         character=character, category=category, fmt=fmt, dest=output)


@app.command("compose")
def cmd_compose(
    region: RegionArg,
    gender:          GenderOpt     = Gender.ANY,
    count:           CountOpt      = 1,
    show_components: ComponentsOpt = False,
    character:       CharacterOpt  = False,
    category:        CategoryOpt   = ProfessionCategory.ALL,
    fmt:             FormatOpt     = OutputFormat.RICH,
    output:          OutputOpt     = None,
) -> None:
    """Namen aus Silbenbausteinen zusammensetzen."""
    _run(region, GenerationMode.COMPOSE, gender, count, show_components,
         character=character, category=category, fmt=fmt, dest=output)


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
        raise typer.Exit(1)

    table = Table("Region", "Anzeigename", "Beschreibung", box=box.SIMPLE, header_style="bold cyan")
    for region_id in ids:
        try:
            r = load_region(region_id)
            table.add_row(region_id, r.meta.region, r.meta.notes)
        except Exception:
            table.add_row(region_id, "?", "[red]Fehler beim Laden[/red]")

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
) -> None:
    try:
        if character:
            results = [
                generate_character(region=region, mode=mode, gender=gender,
                                   profession_category=category)
                for _ in range(count)
            ]
        else:
            results = [
                generate(region=region, mode=mode, gender=gender)
                for _ in range(count)
            ]
    except (GeneratorError, LoaderError) as exc:
        console.print(f"[red]Fehler:[/red] {exc}")
        raise typer.Exit(1)

    output_write(results, fmt=fmt, dest=dest, show_components=show_components)
