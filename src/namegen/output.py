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
    RICH      = "rich"
    PLAIN     = "plain"
    JSON      = "json"
    CSV       = "csv"
    MARKDOWN  = "markdown"
    CLIPBOARD = "clipboard"
    PDF       = "pdf"


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
                f"[dim]{r.name.region}  ·  {_GENDER_DE[r.gender.value]}"
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
        ]
        console.print(Panel("\n".join(lines), border_style="magenta", padding=(0, 1)))


def _chars_to_plain(results: list[CharacterResult]) -> str:
    lines: list[str] = []
    for r in results:
        t = r.traits
        lines += [
            (
                f"{r.full_name}  ({r.name.region},"
                f" {_GENDER_DE[r.gender.value]}, {r.age} J., {r.profession})"
            ),
            (
                f"  Äußeres:  Haare {t.physical.hair},"
                f" Augen {t.physical.eyes}, Statur {t.physical.build}"
            ),
            f"  Wesen:    {t.personality}",
            f"  Ziel:     {t.motivation}",
            f"  Eigenart: {t.quirk}",
            "",
        ]
    return "\n".join(lines)


def _chars_to_json(results: list[CharacterResult]) -> str:
    def _dump(r: CharacterResult) -> dict:
        return {
            "name": r.name.model_dump(mode="json", exclude_none=True),
            "age": r.age,
            "profession": r.profession,
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
    fieldnames = ["full_name", "gender", "region", "age", "profession",
                  "hair", "eyes", "build", "personality", "motivation", "quirk"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow({
            "full_name":    r.full_name,
            "gender":       r.gender.value,
            "region":       r.region,
            "age":          r.age,
            "profession":   r.profession,
            "hair":         r.traits.physical.hair,
            "eyes":         r.traits.physical.eyes,
            "build":        r.traits.physical.build,
            "personality":  r.traits.personality,
            "motivation":   r.traits.motivation,
            "quirk":        r.traits.quirk,
        })
    return buf.getvalue()


# ── Rich (Terminal-Tabelle) ────────────────────────────────────────────────────

def _write_rich(results: list[NameResult], show_components: bool) -> None:
    if len(results) == 1 and not show_components:
        console.print(f"[bold]{results[0].full_name}[/bold]")
        return

    cols = ["Name", "Geschlecht"]
    if show_components and results[0].mode == GenerationMode.COMPOSE:
        cols.append("Bausteine")

    table = Table(*cols, box=box.ROUNDED, header_style="bold magenta", border_style="magenta")

    for r in results:
        row = [
            f"[bold]{r.full_name}[/bold]",
            _GENDER_DE[r.resolved_gender.value],
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
    return json.dumps(
        [r.model_dump(mode="json", exclude_none=True) for r in results],
        ensure_ascii=False,
        indent=2,
    ) + "\n"


# ── CSV ────────────────────────────────────────────────────────────────────────

def _to_csv(results: list[NameResult], show_components: bool) -> str:
    buf = io.StringIO()
    fieldnames = ["full_name", "first_name", "last_name", "gender", "region", "mode"]
    if show_components:
        fieldnames += ["first_prefix", "first_infix", "first_suffix",
                       "last_prefix",  "last_infix",  "last_suffix"]

    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for r in results:
        row: dict = {
            "full_name":  r.full_name,
            "first_name": r.first_name,
            "last_name":  r.last_name or "",
            "gender":     r.gender.value,
            "region":     r.region,
            "mode":       r.mode.value,
        }
        if show_components and r.components:
            c = r.components
            row |= {
                "first_prefix": c.first_prefix or "",
                "first_infix":  c.first_infix  or "",
                "first_suffix": c.first_suffix or "",
                "last_prefix":  c.last_prefix  or "",
                "last_infix":   c.last_infix   or "",
                "last_suffix":  c.last_suffix  or "",
            }
        writer.writerow(row)

    return buf.getvalue()


# ── Markdown ───────────────────────────────────────────────────────────────────

def _to_markdown(results: list[NameResult], show_components: bool) -> str:
    r0 = results[0]
    mode_label = "Einfach" if r0.mode == GenerationMode.SIMPLE else "Komposition"

    cols = ["Name", "Geschlecht"]
    if show_components and r0.mode == GenerationMode.COMPOSE:
        cols.append("Bausteine")

    def md_row(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    lines = [
        f"## DSA Namen – {r0.region}",
        "",
        f"Region: **{r0.region}** · Modus: **{mode_label}** · {len(results)} Namen",
        "",
        md_row(cols),
        md_row(["---"] * len(cols)),
    ]
    for r in results:
        row = [r.full_name, _GENDER_DE[r.resolved_gender.value]]
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
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        console.print("[red]reportlab nicht gefunden.[/red] Installieren mit: uv add reportlab")
        return

    _GENDER_SHORT = {"male": "M", "female": "W", "any": "–"}

    r0 = results[0]
    if dest is None:
        region_slug = r0.region.lower().replace(" ", "_")
        dest = Path(f"dsa_namen_{region_slug}.pdf")

    BORDER = colors.HexColor("#999999")
    HEADER_BG = colors.HexColor("#DDDDDD")
    ROW_ALT   = colors.HexColor("#F5F5F5")

    doc = SimpleDocTemplate(
        str(dest),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DSATitle",
        parent=styles["Heading1"],
        textColor=colors.black,
        fontSize=16,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DSASubtitle",
        parent=styles["Normal"],
        textColor=colors.HexColor("#555555"),
        fontSize=9,
        spaceAfter=14,
    )

    mode_label = "Einfach" if r0.mode == GenerationMode.SIMPLE else "Komposition"
    story = [
        Paragraph("Das Schwarze Auge – Namensliste", title_style),
        Paragraph(
            f"Region: {r0.region}  ·  Modus: {mode_label}  ·  {len(results)} Namen",
            subtitle_style,
        ),
    ]

    # Zwei Namen pro Zeile: [Name1, G1, Name2, G2]
    header = ["Name", "G", "Name", "G"]
    table_data = [header]

    for i in range(0, len(results), 2):
        left = results[i]
        right = results[i + 1] if i + 1 < len(results) else None
        row = [
            left.full_name,
            _GENDER_SHORT[left.resolved_gender.value],
            right.full_name if right else "",
            _GENDER_SHORT[right.resolved_gender.value] if right else "",
        ]
        table_data.append(row)

    # Seitenbreite A4 - Ränder = 17cm; Geschlechts-Spalten schmal
    name_w = 7.25*cm
    g_w    = 1.0*cm
    col_widths = [name_w, g_w, name_w, g_w]

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0),  HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.black),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("TOPPADDING",    (0, 0), (-1, 0),  6),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  6),
        # Datenzeilen
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, ROW_ALT]),
        # Trennlinie zwischen linker und rechter Namensspalte
        ("LINEAFTER",     (1, 0), (1, -1),  1.0, BORDER),
        # Äußerer Rahmen + horizontale Linien
        ("BOX",           (0, 0), (-1, -1), 0.75, BORDER),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        # Geschlechts-Spalten zentrieren
        ("ALIGN",         (1, 0), (1, -1),  "CENTER"),
        ("ALIGN",         (3, 0), (3, -1),  "CENTER"),
    ]))

    story.append(tbl)
    story.append(Spacer(1, 0.5*cm))
    doc.build(story)

    console.print(f"[green]✓ PDF gespeichert:[/green] {dest}")


def _write_pdf_characters(results: list[CharacterResult], dest: Path | None) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        console.print("[red]reportlab nicht gefunden.[/red] Installieren mit: uv add reportlab")
        return

    _GENDER_SHORT = {"male": "M", "female": "W", "any": "–"}

    r0 = results[0]
    if dest is None:
        region_slug = r0.region.lower().replace(" ", "_")
        dest = Path(f"dsa_charaktere_{region_slug}.pdf")

    BORDER    = colors.HexColor("#999999")
    HEADER_BG = colors.HexColor("#DDDDDD")
    ROW_ALT   = colors.HexColor("#F5F5F5")

    doc = SimpleDocTemplate(
        str(dest),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DSATitle", parent=styles["Heading1"],
        textColor=colors.black, fontSize=16, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DSASubtitle", parent=styles["Normal"],
        textColor=colors.HexColor("#555555"), fontSize=9, spaceAfter=14,
    )
    cell_style = ParagraphStyle(
        "DSACell", parent=styles["Normal"],
        fontSize=8, leading=10,
    )

    story = [
        Paragraph("Das Schwarze Auge – Charakterliste", title_style),
        Paragraph(
            f"Region: {r0.region}  ·  {len(results)} Charaktere",
            subtitle_style,
        ),
    ]

    # Columns: Name | G | Alter | Beruf | Eigenschaften
    name_w   = 3.8 * cm
    g_w      = 0.6 * cm
    age_w    = 1.0 * cm
    job_w    = 3.0 * cm
    traits_w = 8.6 * cm  # 17cm total - others

    header = ["Name", "G", "Alter", "Beruf", "Eigenschaften"]
    table_data = [header]

    for r in results:
        t = r.traits
        traits_text = (
            f"Haare {t.physical.hair}, Augen {t.physical.eyes}, {t.physical.build} · "
            f"{t.personality} · {t.motivation} · {t.quirk}"
        )
        table_data.append([
            Paragraph(f"<b>{r.full_name}</b>", cell_style),
            _GENDER_SHORT.get(r.gender.value, "–"),
            str(r.age),
            Paragraph(r.profession, cell_style),
            Paragraph(traits_text, cell_style),
        ])

    tbl = Table(
        table_data,
        colWidths=[name_w, g_w, age_w, job_w, traits_w],
        repeatRows=1,
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  HEADER_BG),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("TOPPADDING",    (0, 0), (-1, 0),  6),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  6),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("BOX",           (0, 0), (-1, -1), 0.75, BORDER),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (1, 0), (1, -1),  "CENTER"),
        ("ALIGN",         (2, 0), (2, -1),  "CENTER"),
    ]))

    story.append(tbl)
    story.append(Spacer(1, 0.5 * cm))
    doc.build(story)

    console.print(f"[green]✓ PDF gespeichert:[/green] {dest}")


# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def _format_components(r: NameResult) -> str:
    """Gibt die Silbenbausteine als lesbaren String zurück."""
    if not r.components:
        return ""
    c = r.components
    first = "+".join(p for p in [c.first_prefix, c.first_infix, c.first_suffix] if p)
    last  = "+".join(p for p in [c.last_prefix,  c.last_infix,  c.last_suffix]  if p)
    return f"{first}  |  {last}" if last else first


def default_filename(fmt: OutputFormat, region: str) -> str:
    """Liefert einen sinnvollen Standarddateinamen für ein Format."""
    slug = region.lower().replace(" ", "_")
    extensions = {
        OutputFormat.PLAIN:    f"dsa_namen_{slug}.txt",
        OutputFormat.JSON:     f"dsa_namen_{slug}.json",
        OutputFormat.CSV:      f"dsa_namen_{slug}.csv",
        OutputFormat.MARKDOWN: f"dsa_namen_{slug}.md",
        OutputFormat.PDF:      f"dsa_namen_{slug}.pdf",
    }
    return extensions.get(fmt, f"dsa_namen_{slug}.txt")
