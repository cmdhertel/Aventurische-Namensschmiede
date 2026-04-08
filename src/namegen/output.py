"""Ausgabe-Formate für generierte Namen."""

from __future__ import annotations

import csv
import io
import json
import sys
from enum import StrEnum
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table

from .models import CharacterResult, GenerationMode, NameResult

console = Console()

_GENDER_DE = {"male": "Männlich", "female": "Weiblich", "any": "Beliebig"}


class OutputFormat(StrEnum):
    RICH = "rich"
    PLAIN = "plain"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    CLIPBOARD = "clipboard"
    PDF = "pdf"


def write(
    results: list[NameResult] | list[CharacterResult],
    fmt: OutputFormat = OutputFormat.RICH,
    dest: Path | None = None,
    show_components: bool = False,
) -> None:
    """Gibt die Ergebnisse im gewählten Format aus oder speichert sie."""
    if not results:
        return

    if isinstance(results[0], CharacterResult):
        _write_characters(results, fmt, dest)  # type: ignore[arg-type]
        return

    match fmt:
        case OutputFormat.RICH:
            _write_rich(results, show_components)  # type: ignore[arg-type]
        case OutputFormat.PLAIN:
            _write_text(_to_plain(results), dest)  # type: ignore[arg-type]
        case OutputFormat.JSON:
            _write_text(_to_json(results), dest)  # type: ignore[arg-type]
        case OutputFormat.CSV:
            _write_text(_to_csv(results, show_components), dest)  # type: ignore[arg-type]
        case OutputFormat.MARKDOWN:
            _write_text(_to_markdown(results, show_components), dest)  # type: ignore[arg-type]
        case OutputFormat.CLIPBOARD:
            _write_clipboard(results)  # type: ignore[arg-type]
        case OutputFormat.PDF:
            _write_pdf(results, dest, show_components)  # type: ignore[arg-type]


# ── Character output ──────────────────────────────────────────────────────────


def _write_characters(
    results: list[CharacterResult],
    fmt: OutputFormat,
    dest: Path | None,
) -> None:
    match fmt:
        case OutputFormat.JSON:
            _write_text(_chars_to_json(results), dest)
        case OutputFormat.PLAIN:
            _write_text(_chars_to_plain(results), dest)
        case OutputFormat.CSV:
            _write_text(_chars_to_csv(results), dest)
        case OutputFormat.PDF:
            _write_pdf_characters(results, dest)
        case OutputFormat.CLIPBOARD:
            text = "\n".join(r.full_name for r in results)
            try:
                import pyperclip

                pyperclip.copy(text)
                console.print(f"[green]✓[/green] {len(results)} Charakter(e) kopiert.")
            except ImportError:
                console.print("[red]pyperclip nicht gefunden.[/red]")
        case _:
            _write_rich_characters(results)


def _write_rich_characters(results: list[CharacterResult]) -> None:
    from rich.panel import Panel

    for r in results:
        t = r.traits
        lines = [
            f"[bold amber]{r.full_name}[/bold amber]",
            (
                f"[dim]{r.species or '–'}  ·  {r.culture or '–'}  ·  {r.name.region}"
                f"  ·  {_GENDER_DE[r.gender.value]}  ·  {r.experience.value}"
                f"  ·  {r.age} Jahre  ·  {r.profession}[/dim]"
            ),
            "",
            (
                f"[bold]Äußeres:[/bold]  Haare {t.physical.hair},"
                f" Augen {t.physical.eyes}, Statur {t.physical.build}"
            ),
            f"[bold]Wesen:[/bold]    {t.personality}",
            f"[bold]Ziel:[/bold]     {t.motivation}",
            f"[bold]Eigenart:[/bold] {t.quirk}",
            (
                f"[bold]Hintergrund:[/bold] Sprache {r.language or '–'},"
                f" Schrift {r.script or '–'}, Sozialstatus {r.social_status or '–'}"
            ),
        ]
        console.print(Panel("\n".join(lines), border_style="magenta", padding=(0, 1)))


def _chars_to_plain(results: list[CharacterResult]) -> str:
    lines: list[str] = []
    for r in results:
        t = r.traits
        lines += [
            (
                f"{r.full_name}  ({r.species or '–'}, {r.culture or '–'}, {r.name.region},"
                f" {_GENDER_DE[r.gender.value]},"
                f" {r.experience.value if r.experience else '–'}, {r.age} J., {r.profession})"
            ),
            (
                f"  Äußeres:  Haare {t.physical.hair},"
                f" Augen {t.physical.eyes}, Statur {t.physical.build}"
            ),
            f"  Wesen:    {t.personality}",
            f"  Ziel:     {t.motivation}",
            f"  Eigenart: {t.quirk}",
            (
                f"  Kontext:  Sprache {r.language or '–'},"
                f" Schrift {r.script or '–'}, Sozialstatus {r.social_status or '–'}"
            ),
            "",
        ]
    return "\n".join(lines)


def _chars_to_json(results: list[CharacterResult]) -> str:
    def _dump(r: CharacterResult) -> dict:
        return {
            "name": r.name.model_dump(mode="json", exclude_none=True),
            "experience": r.experience.value if r.experience else None,
            "age": r.age,
            "profession": r.profession,
            "species": r.species,
            "culture": r.culture,
            "language": r.language,
            "script": r.script,
            "social_status": r.social_status,
            "traits": {
                "hair": r.traits.physical.hair,
                "eyes": r.traits.physical.eyes,
                "build": r.traits.physical.build,
                "personality": r.traits.personality,
                "motivation": r.traits.motivation,
                "quirk": r.traits.quirk,
            },
        }

    return json.dumps([_dump(r) for r in results], ensure_ascii=False, indent=2) + "\n"


def _chars_to_csv(results: list[CharacterResult]) -> str:
    buf = io.StringIO()
    fieldnames = [
        "full_name",
        "gender",
        "experience",
        "species",
        "culture",
        "region",
        "age",
        "profession",
        "language",
        "script",
        "social_status",
        "hair",
        "eyes",
        "build",
        "personality",
        "motivation",
        "quirk",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(
            {
                "full_name": r.full_name,
                "gender": r.gender.value,
                "experience": r.experience.value if r.experience else "",
                "species": r.species or "",
                "culture": r.culture or "",
                "region": r.region,
                "age": r.age,
                "profession": r.profession,
                "language": r.language or "",
                "script": r.script or "",
                "social_status": r.social_status or "",
                "hair": r.traits.physical.hair,
                "eyes": r.traits.physical.eyes,
                "build": r.traits.physical.build,
                "personality": r.traits.personality,
                "motivation": r.traits.motivation,
                "quirk": r.traits.quirk,
            }
        )
    return buf.getvalue()


# ── Rich (Terminal-Tabelle) ────────────────────────────────────────────────────


def _write_rich(results: list[NameResult], show_components: bool) -> None:
    if len(results) == 1 and not show_components:
        console.print(f"[bold]{results[0].full_name}[/bold]")
        return

    cols = ["Name", "Geschlecht", "Spezies", "Kultur"]
    if show_components and results[0].mode == GenerationMode.COMPOSE:
        cols.append("Bausteine")

    table = Table(*cols, box=box.ROUNDED, header_style="bold magenta", border_style="magenta")

    for r in results:
        row = [
            f"[bold]{r.full_name}[/bold]",
            _GENDER_DE[r.resolved_gender.value],
            r.species or "–",
            r.culture or "–",
        ]
        if show_components and r.mode == GenerationMode.COMPOSE and r.components:
            row.append(_format_components(r))
        table.add_row(*row)

    console.print(table)


# ── Text-Datei / stdout ───────────────────────────────────────────────────────


def _write_text(text: str, dest: Path | None) -> None:
    if dest is None:
        sys.stdout.write(text)
    else:
        dest.write_text(text, encoding="utf-8")
        console.print(f"[green]✓ Gespeichert:[/green] {dest}")


# ── Plain Text ─────────────────────────────────────────────────────────────────


def _to_plain(results: list[NameResult]) -> str:
    return "\n".join(r.full_name for r in results) + "\n"


# ── JSON ───────────────────────────────────────────────────────────────────────


def _to_json(results: list[NameResult]) -> str:
    return (
        json.dumps(
            [r.model_dump(mode="json", exclude_none=True) for r in results],
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


# ── CSV ────────────────────────────────────────────────────────────────────────


def _to_csv(results: list[NameResult], show_components: bool) -> str:
    buf = io.StringIO()
    fieldnames = [
        "full_name",
        "first_name",
        "last_name",
        "gender",
        "species",
        "culture",
        "region",
        "mode",
    ]
    if show_components:
        fieldnames += [
            "first_prefix",
            "first_infix",
            "first_suffix",
            "last_prefix",
            "last_infix",
            "last_suffix",
        ]

    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for r in results:
        row: dict = {
            "full_name": r.full_name,
            "first_name": r.first_name,
            "last_name": r.last_name or "",
            "gender": r.gender.value,
            "species": r.species or "",
            "culture": r.culture or "",
            "region": r.region,
            "mode": r.mode.value,
        }
        if show_components and r.components:
            c = r.components
            row |= {
                "first_prefix": c.first_prefix or "",
                "first_infix": c.first_infix or "",
                "first_suffix": c.first_suffix or "",
                "last_prefix": c.last_prefix or "",
                "last_infix": c.last_infix or "",
                "last_suffix": c.last_suffix or "",
            }
        writer.writerow(row)

    return buf.getvalue()


# ── Markdown ───────────────────────────────────────────────────────────────────


def _to_markdown(results: list[NameResult], show_components: bool) -> str:
    r0 = results[0]
    mode_label = "Einfach" if r0.mode == GenerationMode.SIMPLE else "Komposition"

    cols = ["Name", "Geschlecht", "Spezies", "Kultur"]
    if show_components and r0.mode == GenerationMode.COMPOSE:
        cols.append("Bausteine")

    def md_row(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    lines = [
        f"## DSA Namen – {r0.region}",
        "",
        (
            f"Spezies: **{r0.species or '–'}** · Kultur: **{r0.culture or '–'}**"
            f" · Region: **{r0.region}** · Modus: **{mode_label}** · {len(results)} Namen"
        ),
        "",
        md_row(cols),
        md_row(["---"] * len(cols)),
    ]
    for r in results:
        row = [r.full_name, _GENDER_DE[r.resolved_gender.value], r.species or "–", r.culture or "–"]
        if show_components and r.mode == GenerationMode.COMPOSE and r.components:
            row.append(_format_components(r))
        lines.append(md_row(row))

    lines.append("")
    return "\n".join(lines)


# ── Clipboard ──────────────────────────────────────────────────────────────────


def _write_clipboard(results: list[NameResult]) -> None:
    try:
        import pyperclip
    except ImportError:
        console.print("[red]pyperclip nicht gefunden.[/red] Installieren mit: uv add pyperclip")
        return

    text = "\n".join(r.full_name for r in results)
    try:
        pyperclip.copy(text)
        console.print(f"[green]✓[/green] {len(results)} Name(n) in die Zwischenablage kopiert.")
    except Exception as exc:
        console.print(f"[red]Clipboard-Fehler:[/red] {exc}")
        console.print("[dim]Tipp unter Linux: xclip oder xdotool installieren.[/dim]")


# ── PDF ────────────────────────────────────────────────────────────────────────


def _write_pdf(results: list[NameResult], dest: Path | None, show_components: bool) -> None:
    try:
        from .pdf_builder import build_name_pdf
    except ImportError:
        console.print("[red]reportlab nicht gefunden.[/red] Installieren mit: uv add reportlab")
        return

    r0 = results[0]
    if dest is None:
        region_slug = r0.region.lower().replace(" ", "_")
        dest = Path(f"dsa_namen_{region_slug}.pdf")

    name_data = [
        {
            "full_name": r.full_name,
            "gender": r.resolved_gender.value,
            "region": r.region,
            "region_abbr": r.region_abbreviation or "",
        }
        for r in results
    ]
    build_name_pdf(name_data, dest=dest)
    console.print(f"[green]✓ PDF gespeichert:[/green] {dest}")


def _write_pdf_characters(results: list[CharacterResult], dest: Path | None) -> None:
    try:
        from .pdf_builder import build_character_pdf
    except ImportError:
        console.print("[red]reportlab nicht gefunden.[/red] Installieren mit: uv add reportlab")
        return

    r0 = results[0]
    if dest is None:
        region_slug = r0.region.lower().replace(" ", "_")
        dest = Path(f"dsa_charaktere_{region_slug}.pdf")

    char_data = [
        {
            "full_name": r.full_name,
            "gender": r.gender.value,
            "region": r.region,
            "age": r.age,
            "profession": r.profession,
            "hair": r.traits.physical.hair,
            "eyes": r.traits.physical.eyes,
            "build": r.traits.physical.build,
            "personality": r.traits.personality,
            "motivation": r.traits.motivation,
            "quirk": r.traits.quirk,
        }
        for r in results
    ]
    build_character_pdf(char_data, dest=dest)
    console.print(f"[green]✓ PDF gespeichert:[/green] {dest}")


# ── Hilfsfunktionen ────────────────────────────────────────────────────────────


def _format_components(r: NameResult) -> str:
    """Gibt die Silbenbausteine als lesbaren String zurück."""
    if not r.components:
        return ""
    c = r.components
    first = "+".join(p for p in [c.first_prefix, c.first_infix, c.first_suffix] if p)
    last = "+".join(p for p in [c.last_prefix, c.last_infix, c.last_suffix] if p)
    return f"{first}  |  {last}" if last else first


def default_filename(fmt: OutputFormat, region: str) -> str:
    """Liefert einen sinnvollen Standarddateinamen für ein Format."""
    slug = region.lower().replace(" ", "_")
    extensions = {
        OutputFormat.PLAIN: f"dsa_namen_{slug}.txt",
        OutputFormat.JSON: f"dsa_namen_{slug}.json",
        OutputFormat.CSV: f"dsa_namen_{slug}.csv",
        OutputFormat.MARKDOWN: f"dsa_namen_{slug}.md",
        OutputFormat.PDF: f"dsa_namen_{slug}.pdf",
    }
    return extensions.get(fmt, f"dsa_namen_{slug}.txt")
