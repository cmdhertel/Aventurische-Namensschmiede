"""Typer CLI entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from click.core import ParameterSource
from rich import box
from rich.console import Console
from rich.table import Table

from .catalog import get_origin_catalog
from .chargen import generate_character, get_profession_groups
from .generator import GeneratorError, generate
from .loader import LoaderError, list_regions, load_region
from .models import ExperienceLevel, Gender, GenerationMode, ProfessionCategory
from .output import OutputFormat
from .output import write as output_write
from .profiles import GenerationProfile, dump_profile, list_profiles, load_profile, save_profile

app = typer.Typer(
    name="namegen",
    help="Generate names for Das Schwarze Auge (The Dark Eye) RPG.",
    add_completion=False,
    rich_markup_mode="rich",
    invoke_without_command=True,
)
console = Console()
config_app = typer.Typer(help="Konfigurationsprofile speichern und laden.")
app.add_typer(config_app, name="config")


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Startet das interaktive Menü wenn kein Unterbefehl angegeben wird."""
    if ctx.invoked_subcommand is None:
        from . import interactive

        interactive.run()


# ── Shared option types ────────────────────────────────────────────────────────

RegionArg = Annotated[
    str | None,
    typer.Argument(
        help=(
            "Spezies-, Kultur- oder Region-ID"
            " (z.B. human, mittelreicher, mittelreich_kosch)."
            " Kommagetrennte Mischung von bis zu 3 Einträgen ist erlaubt."
        ),
    ),
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
        "--profession-category",
        "--category",
        "-k",
        help="Berufskategorie: alle | geweihte | zauberer | kaempfer | profan",
        case_sensitive=False,
    ),
]
ExperienceOpt = Annotated[
    ExperienceLevel,
    typer.Option(
        "--experience",
        help="Erfahrungsstufe: lehrling | geselle | meister | veteran",
        case_sensitive=False,
    ),
]
InfixProbOpt = Annotated[
    float | None,
    typer.Option(
        "--infix-probability",
        min=0.0,
        max=1.0,
        help=(
            "Überschreibt im Compose-Modus temporär die Infix-Wahrscheinlichkeit"
            " für Vor- und Nachnamen."
        ),
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
    typer.Option("--output", "-o", help="Ausgabedatei (Standard: stdout / Standardname für PDF)."),
]
ProfileOpt = Annotated[
    str | None,
    typer.Option(
        "--profile",
        "-p",
        help="Lädt Standardwerte aus ~/.config/namegen/profiles/<name>.json.",
    ),
]
ExcludeFileOpt = Annotated[
    Path | None,
    typer.Option(
        "--exclude-file",
        help="Datei mit bereits verwendeten Namen, ein Name pro Zeile, case-insensitive.",
    ),
]
MinSyllablesOpt = Annotated[
    int,
    typer.Option("--min-syllables", min=1, help="Minimale Part-Anzahl pro Compose-Name."),
]
MaxSyllablesOpt = Annotated[
    int,
    typer.Option("--max-syllables", min=1, help="Maximale Part-Anzahl pro Compose-Name."),
]


# ── Commands ───────────────────────────────────────────────────────────────────


@app.command("simple")
def cmd_simple(
    ctx: typer.Context,
    region: RegionArg = None,
    gender: GenderOpt = Gender.ANY,
    count: CountOpt = 1,
    character: CharacterOpt = False,
    category: CategoryOpt = ProfessionCategory.ALL,
    experience: ExperienceOpt = ExperienceLevel.GESELLE,
    fmt: FormatOpt = OutputFormat.RICH,
    output: OutputOpt = None,
    profile: ProfileOpt = None,
    exclude_file: ExcludeFileOpt = None,
) -> None:
    """Namen aus vordefinierten Listen generieren."""
    _validate_character_options(ctx, character)
    config = _resolve_profile_overrides(
        ctx,
        command_mode=GenerationMode.SIMPLE,
        region=region,
        gender=gender,
        count=count,
        character=character,
        category=category,
        experience=experience,
        fmt=fmt,
        output=output,
        profile_name=profile,
        show_components=False,
        exclude_file=exclude_file,
    )
    _run(
        config["region"],
        GenerationMode.SIMPLE,
        config["gender"],
        config["count"],
        show_components=False,
        character=config["character"],
        category=config["category"],
        experience=config["experience"],
        fmt=config["fmt"],
        dest=config["output"],
        exclude_names=_load_excluded_names(config["exclude_file"]),
    )


@app.command("compose")
def cmd_compose(
    ctx: typer.Context,
    region: RegionArg = None,
    gender: GenderOpt = Gender.ANY,
    count: CountOpt = 1,
    show_components: ComponentsOpt = False,
    character: CharacterOpt = False,
    category: CategoryOpt = ProfessionCategory.ALL,
    experience: ExperienceOpt = ExperienceLevel.GESELLE,
    infix_probability: InfixProbOpt = None,
    fmt: FormatOpt = OutputFormat.RICH,
    output: OutputOpt = None,
    profile: ProfileOpt = None,
    exclude_file: ExcludeFileOpt = None,
    min_syllables: MinSyllablesOpt = 2,
    max_syllables: MaxSyllablesOpt = 4,
) -> None:
    """Namen aus Silbenbausteinen zusammensetzen."""
    _validate_character_options(ctx, character)
    config = _resolve_profile_overrides(
        ctx,
        command_mode=GenerationMode.COMPOSE,
        region=region,
        gender=gender,
        count=count,
        character=character,
        category=category,
        experience=experience,
        fmt=fmt,
        output=output,
        profile_name=profile,
        show_components=show_components,
        infix_probability=infix_probability,
        min_syllables=min_syllables,
        max_syllables=max_syllables,
        exclude_file=exclude_file,
    )
    _run(
        config["region"],
        GenerationMode.COMPOSE,
        config["gender"],
        config["count"],
        config["show_components"],
        character=config["character"],
        category=config["category"],
        experience=config["experience"],
        infix_probability_override=config["infix_probability"],
        fmt=config["fmt"],
        dest=config["output"],
        min_syllables=config["min_syllables"],
        max_syllables=config["max_syllables"],
        exclude_names=_load_excluded_names(config["exclude_file"]),
    )


@app.command("menu")
def cmd_menu() -> None:
    """Interaktives Menü zur Namens-Generierung."""
    from . import interactive

    interactive.run()


@app.command("regions")
def cmd_regions() -> None:
    """Alle verfügbaren Regionen auflisten."""
    try:
        list_regions()
    except Exception as exc:
        console.print(f"[red]Fehler:[/red] {exc}")
        raise typer.Exit(1) from None

    table = Table(
        "ID",
        "Typ",
        "Region",
        "Anzeigename",
        "Spezies",
        "Kultur",
        "Beschreibung",
        box=box.SIMPLE,
        header_style="bold cyan",
    )
    for item in get_origin_catalog():
        try:
            if item.get("is_aggregate"):
                table.add_row(
                    item["id"],
                    "Sammlung",
                    item.get("region_name", "") or "–",
                    item["name"],
                    item["species_name"],
                    item["culture_name"],
                    item.get("notes", ""),
                )
                continue

            r = load_region(item["id"])
            table.add_row(
                item["id"],
                "Region" if item.get("has_region") else "Kultur",
                item.get("region_name", "") or "–",
                r.meta.region,
                r.species.meta.name if r.species else "?",
                r.culture.meta.name if r.culture else "?",
                r.meta.notes,
            )
        except Exception:
            table.add_row(item["id"], "?", "?", "?", "?", "[red]Fehler beim Laden[/red]")

    console.print(table)


@app.command("professions")
def cmd_professions() -> None:
    """Alle verfügbaren Professionen geordnet nach Kategorie anzeigen."""
    for title, professions in get_profession_groups():
        table = Table(title, box=box.SIMPLE, header_style="bold cyan")
        for profession in professions:
            table.add_row(profession)
        console.print(table)


@config_app.command("save")
def cmd_config_save(
    name: str,
    region: Annotated[str, typer.Option("--region", help="Standard-Selektion für das Profil.")],
    mode: Annotated[
        GenerationMode,
        typer.Option("--mode", help="simple | compose", case_sensitive=False),
    ] = GenerationMode.SIMPLE,
    gender: GenderOpt = Gender.ANY,
    count: CountOpt = 1,
    fmt: FormatOpt = OutputFormat.RICH,
    character: CharacterOpt = False,
    category: CategoryOpt = ProfessionCategory.ALL,
    experience: ExperienceOpt = ExperienceLevel.GESELLE,
    show_components: ComponentsOpt = False,
    infix_probability: InfixProbOpt = None,
    min_syllables: MinSyllablesOpt = 2,
    max_syllables: MaxSyllablesOpt = 4,
    exclude_file: ExcludeFileOpt = None,
) -> None:
    """Speichert ein JSON-Profil für häufig genutzte Einstellungen."""
    if mode != GenerationMode.COMPOSE and show_components:
        console.print("[red]Fehler:[/red] --components ist nur für compose sinnvoll.")
        raise typer.Exit(1)

    profile = GenerationProfile(
        region=region,
        mode=mode,
        gender=gender,
        count=count,
        fmt=fmt,
        character=character,
        profession_category=category,
        experience=experience,
        show_components=show_components,
        infix_probability=infix_probability,
        min_syllables=min_syllables,
        max_syllables=max_syllables,
        exclude_file=str(exclude_file) if exclude_file else None,
    )
    path = save_profile(name, profile)
    console.print(f"[green]✓ Profil gespeichert:[/green] {path}")


@config_app.command("load")
def cmd_config_load(name: str) -> None:
    """Lädt ein Profil und gibt dessen JSON-Inhalt aus."""
    try:
        profile = load_profile(name)
    except FileNotFoundError as exc:
        console.print(f"[red]Fehler:[/red] {exc}")
        raise typer.Exit(1) from None

    console.print(dump_profile(profile), end="")


@config_app.command("list")
def cmd_config_list() -> None:
    """Listet gespeicherte Profile auf."""
    names = list_profiles()
    if not names:
        console.print("[dim]Keine Profile gespeichert.[/dim]")
        return
    for name in names:
        console.print(name)


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
    min_syllables: int = 2,
    max_syllables: int = 4,
    exclude_names: set[str] | None = None,
) -> None:
    try:
        if character:
            results = [
                generate_character(
                    region=region,
                    mode=mode,
                    gender=gender,
                    profession_category=category,
                    experience=experience,
                    infix_probability_override=infix_probability_override,
                    min_syllables=min_syllables,
                    max_syllables=max_syllables,
                    exclude_names=exclude_names,
                )
                for _ in range(count)
            ]
        else:
            results = [
                generate(
                    region=region,
                    mode=mode,
                    gender=gender,
                    infix_probability_override=infix_probability_override,
                    min_syllables=min_syllables,
                    max_syllables=max_syllables,
                    exclude_names=exclude_names,
                )
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


def _resolve_profile_overrides(
    ctx: typer.Context,
    *,
    command_mode: GenerationMode,
    region: str | None,
    gender: Gender,
    count: int,
    character: bool,
    category: ProfessionCategory,
    experience: ExperienceLevel,
    fmt: OutputFormat,
    output: Path | None,
    profile_name: str | None,
    show_components: bool,
    infix_probability: float | None = None,
    min_syllables: int = 2,
    max_syllables: int = 4,
    exclude_file: Path | None = None,
) -> dict:
    try:
        profile = load_profile(profile_name) if profile_name else None
    except FileNotFoundError as exc:
        console.print(f"[red]Fehler:[/red] {exc}")
        raise typer.Exit(1) from None
    if profile and profile.mode != command_mode:
        console.print(
            f"[red]Fehler:[/red] Profil '{profile_name}' ist für Modus '{profile.mode.value}'"
            f" gespeichert, nicht für '{command_mode.value}'."
        )
        raise typer.Exit(1)

    resolved_region = region
    if resolved_region is None:
        resolved_region = profile.region if profile else None
    if not resolved_region:
        console.print(
            "[red]Fehler:[/red] Region/Selektion fehlt. Direkt angeben oder --profile nutzen."
        )
        raise typer.Exit(1)

    exclude_value = _profile_default(
        ctx,
        "exclude_file",
        str(exclude_file) if exclude_file else None,
        profile.exclude_file if profile else None,
    )

    return {
        "region": resolved_region,
        "gender": _profile_default(ctx, "gender", gender, profile.gender if profile else None),
        "count": _profile_default(ctx, "count", count, profile.count if profile else None),
        "character": _profile_default(
            ctx, "character", character, profile.character if profile else None
        ),
        "category": _profile_default(
            ctx,
            "category",
            category,
            profile.profession_category if profile else None,
        ),
        "experience": _profile_default(
            ctx,
            "experience",
            experience,
            profile.experience if profile else None,
        ),
        "fmt": _profile_default(ctx, "fmt", fmt, profile.fmt if profile else None),
        "output": output,
        "show_components": _profile_default(
            ctx,
            "show_components",
            show_components,
            profile.show_components if profile else None,
        ),
        "infix_probability": _profile_default(
            ctx,
            "infix_probability",
            infix_probability,
            profile.infix_probability if profile else None,
        ),
        "min_syllables": _profile_default(
            ctx,
            "min_syllables",
            min_syllables,
            profile.min_syllables if profile else None,
        ),
        "max_syllables": _profile_default(
            ctx,
            "max_syllables",
            max_syllables,
            profile.max_syllables if profile else None,
        ),
        "exclude_file": Path(exclude_value) if exclude_value else None,
    }


def _profile_default(
    ctx: typer.Context,
    parameter_name: str,
    current,
    profile_value,
):
    if profile_value is None:
        return current
    source = ctx.get_parameter_source(parameter_name)
    if source in (None, ParameterSource.DEFAULT):
        return profile_value
    return current


def _load_excluded_names(path: Path | None) -> set[str]:
    if path is None:
        return set()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        console.print(f"[red]Fehler:[/red] Exclude-Datei konnte nicht gelesen werden: {exc}")
        raise typer.Exit(1) from None
    return {line.strip().casefold() for line in text.splitlines() if line.strip()}
