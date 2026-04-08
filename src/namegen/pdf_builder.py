"""Shared PDF generation logic for CLI and web output."""

from __future__ import annotations

import io
from pathlib import Path

_GENDER_SHORT = {"male": "M", "female": "W", "any": "–"}

_BORDER_HEX = "#999999"
_HEADER_BG_HEX = "#DDDDDD"
_ROW_ALT_HEX = "#F5F5F5"
_SUBTITLE_HEX = "#555555"


def build_name_pdf(name_data: list[dict], dest: Path | io.BytesIO | None = None) -> bytes | None:
    """Build a names PDF. Writes to dest (Path or BytesIO) or returns bytes if dest is None."""
    story, _ = _build_name_story(name_data)
    return _render_story(story, dest)


def build_character_pdf(
    char_data: list[dict], dest: Path | io.BytesIO | None = None
) -> bytes | None:
    """Build a character PDF. Writes to dest (Path or BytesIO) or returns bytes if dest is None."""
    story, _ = _build_character_story(char_data)
    return _render_story(story, dest)


def build_mixed_pdf(
    name_data: list[dict],
    char_data: list[dict],
    dest: Path | io.BytesIO | None = None,
) -> bytes | None:
    """Build a single PDF containing separate sections for names and characters."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer

    combined_entries = [*name_data, *char_data]
    subtitle = (
        f"Regionen: {summarize_region_abbrs(combined_entries)}"
        f"  ·  {len(name_data)} Namen"
        f" · {len(char_data)} Charaktere"
    )
    story, styles = _story_preamble(
        "Das Schwarze Auge – Namensliste & Charakterliste",
        len(combined_entries),
        subtitle=subtitle,
    )
    story.extend(
        [
            _paragraph("Namensliste", styles["section"]),
            Spacer(1, 0.15 * cm),
            *_build_name_story(name_data, include_title=False)[0],
        ]
    )
    story.extend(
        [
            Spacer(1, 0.35 * cm),
            _paragraph("Charakterliste", styles["section"]),
            Spacer(1, 0.15 * cm),
            *_build_character_story(char_data, include_title=False)[0],
        ]
    )
    return _render_story(story, dest)


def derive_region_abbr(region: str, region_abbr: str | None = None) -> str:
    """Return a stable three-letter abbreviation for a region."""
    abbr = str(region_abbr or "").strip().upper()
    if len(abbr) == 3:
        return abbr
    cleaned = "".join(ch for ch in region if ch.isalpha()).upper()
    return cleaned[:3] if cleaned else "???"


def summarize_region_abbrs(entries: list[dict]) -> str:
    """Return a comma-separated list of distinct region labels as Region (ABK)."""
    region_labels = {
        (
            f"{str(entry.get('region', '')).strip()} "
            f"({derive_region_abbr(str(entry.get('region', '')), entry.get('region_abbr'))})"
        )
        for entry in entries
        if entry.get("region")
    }
    return ", ".join(sorted(region_labels)) if region_labels else "–"


def _build_name_story(name_data: list[dict], *, include_title: bool = True) -> tuple[list, dict]:
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer, Table, TableStyle

    story, styles = _story_preamble(
        "Das Schwarze Auge – Namensliste",
        len(name_data),
        subtitle=f"Regionen: {summarize_region_abbrs(name_data)}  ·  {len(name_data)} Namen",
        include_title=include_title,
    )

    region_to_abbr = {
        str(entry.get("region", "")): derive_region_abbr(
            str(entry.get("region", "")),
            entry.get("region_abbr"),
        )
        for entry in name_data
        if entry.get("region")
    }
    has_multiple_regions = len(region_to_abbr) > 1

    if has_multiple_regions:
        header = ["Name", "G", "Reg.", "Name", "G", "Reg."]
    else:
        header = ["Name", "G", "Name", "G"]
    table_data = [header]

    for i in range(0, len(name_data), 2):
        left = name_data[i]
        right = name_data[i + 1] if i + 1 < len(name_data) else None
        if has_multiple_regions:
            table_data.append(
                [
                    left["full_name"],
                    _GENDER_SHORT.get(left.get("gender", "any"), "–"),
                    region_to_abbr.get(left.get("region", ""), "–"),
                    right["full_name"] if right else "",
                    _GENDER_SHORT.get(right.get("gender", "any"), "–") if right else "",
                    region_to_abbr.get(right.get("region", ""), "–") if right else "",
                ]
            )
        else:
            table_data.append(
                [
                    left["full_name"],
                    _GENDER_SHORT.get(left.get("gender", "any"), "–"),
                    right["full_name"] if right else "",
                    _GENDER_SHORT.get(right.get("gender", "any"), "–") if right else "",
                ]
            )

    if has_multiple_regions:
        name_w = 6.5 * cm
        g_w = 0.8 * cm
        region_w = 1.2 * cm
        col_widths = [name_w, g_w, region_w, name_w, g_w, region_w]
        center_columns = (1, 2, 4, 5)
        separator_columns = (2,)
    else:
        name_w = 7.6 * cm
        g_w = 0.9 * cm
        col_widths = [name_w, g_w, name_w, g_w]
        center_columns = (1, 3)
        separator_columns = (1,)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_HEADER_BG_HEX)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(_ROW_ALT_HEX)]),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(_BORDER_HEX)),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor(_BORDER_HEX)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for col in center_columns:
        style_cmds.append(("ALIGN", (col, 0), (col, -1), "CENTER"))
    if has_multiple_regions:
        style_cmds.append(("FONTSIZE", (2, 0), (2, -1), 8))
        style_cmds.append(("FONTSIZE", (5, 0), (5, -1), 8))
    for col in separator_columns:
        style_cmds.append(("LINEAFTER", (col, 0), (col, -1), 1.0, colors.HexColor(_BORDER_HEX)))

    tbl.setStyle(TableStyle(style_cmds))
    story.extend([tbl, Spacer(1, 0.5 * cm)])
    return story, styles


def _build_character_story(
    char_data: list[dict], *, include_title: bool = True
) -> tuple[list, dict]:
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer, Table, TableStyle

    story, styles = _story_preamble(
        "Das Schwarze Auge – Charakterliste",
        len(char_data),
        subtitle=f"Regionen: {summarize_region_abbrs(char_data)}  ·  {len(char_data)} Charaktere",
        include_title=include_title,
    )
    cell_style = ParagraphStyle(
        "DSACell",
        parent=styles["base"]["Normal"],
        fontSize=8,
        leading=10,
    )

    name_w = 3.4 * cm
    region_w = 0.9 * cm
    g_w = 0.6 * cm
    age_w = 1.0 * cm
    job_w = 2.5 * cm
    traits_w = 7.6 * cm

    header = ["Name", "Reg.", "G", "Alter", "Beruf", "Eigenschaften"]
    table_data = [header]

    for entry in char_data:
        traits_text = (
            f"Haare {entry.get('hair', '–')}, Augen {entry.get('eyes', '–')}, "
            f"{entry.get('build', '–')} · {entry.get('personality', '–')} · "
            f"{entry.get('motivation', '–')} · {entry.get('quirk', '–')}"
        )
        table_data.append(
            [
                _paragraph(f"<b>{entry.get('full_name', '')}</b>", cell_style),
                derive_region_abbr(str(entry.get("region", "")), entry.get("region_abbr")),
                _GENDER_SHORT.get(entry.get("gender", "any"), "–"),
                str(entry.get("age", "–")),
                _paragraph(entry.get("profession", "–"), cell_style),
                _paragraph(traits_text, cell_style),
            ]
        )

    tbl = Table(
        table_data,
        colWidths=[name_w, region_w, g_w, age_w, job_w, traits_w],
        repeatRows=1,
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_HEADER_BG_HEX)),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("TOPPADDING", (0, 1), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(_ROW_ALT_HEX)]),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(_BORDER_HEX)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor(_BORDER_HEX)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (3, -1), "CENTER"),
                ("FONTSIZE", (1, 0), (1, -1), 8),
            ]
        )
    )

    story.extend([tbl, Spacer(1, 0.5 * cm)])
    return story, styles


def _story_preamble(
    title: str,
    entry_count: int,
    *,
    subtitle: str | None = None,
    include_title: bool = True,
) -> tuple[list, dict]:
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    base_styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DSATitle",
        parent=base_styles["Heading1"],
        textColor=colors.black,
        fontSize=16,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DSASubtitle",
        parent=base_styles["Normal"],
        textColor=colors.HexColor(_SUBTITLE_HEX),
        fontSize=9,
        leading=11,
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "DSASection",
        parent=base_styles["Heading2"],
        textColor=colors.black,
        fontSize=12,
        spaceAfter=6,
    )
    story: list = []
    if include_title:
        story.append(_paragraph(title, title_style))
        story.append(
            _paragraph(
                subtitle or f"{entry_count} Einträge",
                subtitle_style,
            )
        )
    return story, {
        "base": base_styles,
        "title": title_style,
        "subtitle": subtitle_style,
        "section": section_style,
    }


def _paragraph(text: str, style):
    from reportlab.platypus import Paragraph

    return Paragraph(text, style)


def _render_story(story: list, dest: Path | io.BytesIO | None = None) -> bytes | None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story)
    pdf_bytes = buf.getvalue()

    if dest is None:
        return pdf_bytes
    if isinstance(dest, Path):
        dest.write_bytes(pdf_bytes)
        return None
    dest.write(pdf_bytes)
    return None
