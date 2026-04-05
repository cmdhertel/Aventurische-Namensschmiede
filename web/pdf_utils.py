"""PDF-Generierung für den Web-Download (in-memory, gibt bytes zurück)."""

from __future__ import annotations

import io

_GENDER_SHORT = {"male": "M", "female": "W", "any": "–"}


def build_pdf_bytes(name_data: list[dict]) -> bytes:
    """Dispatcher: routes to character or name PDF builder based on data content."""
    if name_data and "age" in name_data[0]:
        return _build_character_pdf_bytes(name_data)
    return _build_name_pdf_bytes(name_data)


def _build_name_pdf_bytes(name_data: list[dict]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()

    BORDER = colors.HexColor("#999999")
    HEADER_BG = colors.HexColor("#DDDDDD")
    ROW_ALT = colors.HexColor("#F5F5F5")

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
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
        leading=11,
        spaceAfter=14,
    )
    legend_style = ParagraphStyle(
        "DSALegend",
        parent=styles["Normal"],
        textColor=colors.HexColor("#555555"),
        fontSize=8,
        leading=10,
        spaceAfter=10,
    )

    region_to_abbr: dict[str, str] = {}
    for entry in name_data:
        region = entry.get("region")
        if not region:
            continue
        abbr = str(entry.get("region_abbr", "")).strip().upper()
        if len(abbr) != 3:
            cleaned = "".join(ch for ch in region if ch.isalpha()).upper()
            abbr = cleaned[:3] if cleaned else "???"
        region_to_abbr.setdefault(region, abbr)

    regions = sorted(region_to_abbr.keys())
    has_multiple_regions = len(regions) > 1
    region_label = ", ".join(regions) if regions else "–"

    story = [
        Paragraph("Das Schwarze Auge – Namensliste", title_style),
        Paragraph(f"Region: {region_label}  ·  {len(name_data)} Namen", subtitle_style),
    ]
    if has_multiple_regions:
        code_legend = " · ".join(f"{region_to_abbr[region]} = {region}" for region in regions)
        story.append(Paragraph(f"Abkürzungen: {code_legend}", legend_style))

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
        center_columns = (1, 4)
        separator_columns = (2,)
    else:
        name_w = 7.6 * cm
        g_w = 0.9 * cm
        col_widths = [name_w, g_w, name_w, g_w]
        center_columns = (1, 3)
        separator_columns = (1,)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    styles = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for col in center_columns:
        styles.append(("ALIGN", (col, 0), (col, -1), "CENTER"))
    if has_multiple_regions:
        styles.append(("ALIGN", (2, 0), (2, -1), "CENTER"))
        styles.append(("ALIGN", (5, 0), (5, -1), "CENTER"))
        styles.append(("FONTSIZE", (2, 0), (2, 0), 8))
        styles.append(("FONTSIZE", (5, 0), (5, 0), 8))
        styles.append(("FONTSIZE", (2, 1), (2, -1), 8))
        styles.append(("FONTSIZE", (5, 1), (5, -1), 8))
    for col in separator_columns:
        styles.append(("LINEAFTER", (col, 0), (col, -1), 1.0, BORDER))

    tbl.setStyle(TableStyle(styles))

    story.append(tbl)
    story.append(Spacer(1, 0.5 * cm))
    doc.build(story)

    return buf.getvalue()


def _build_character_pdf_bytes(char_data: list[dict]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    _GENDER_SHORT = {"male": "M", "female": "W", "any": "–"}

    buf = io.BytesIO()

    BORDER = colors.HexColor("#999999")
    HEADER_BG = colors.HexColor("#DDDDDD")
    ROW_ALT = colors.HexColor("#F5F5F5")

    regions = sorted({e.get("region", "") for e in char_data if e.get("region")})
    region_label = ", ".join(regions) if regions else "–"

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )

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
        textColor=colors.HexColor("#555555"),
        fontSize=9,
        spaceAfter=14,
    )
    cell_style = ParagraphStyle(
        "DSACell",
        parent=base_styles["Normal"],
        fontSize=8,
        leading=10,
    )

    story = [
        Paragraph("Das Schwarze Auge – Charakterliste", title_style),
        Paragraph(f"Region: {region_label}  ·  {len(char_data)} Charaktere", subtitle_style),
    ]

    # Columns: Name | G | Alter | Beruf | Eigenschaften
    name_w = 3.8 * cm
    g_w = 0.6 * cm
    age_w = 1.0 * cm
    job_w = 3.0 * cm
    traits_w = 8.6 * cm

    header = ["Name", "G", "Alter", "Beruf", "Eigenschaften"]
    table_data = [header]

    for e in char_data:
        traits_text = (
            f"Haare {e.get('hair', '–')}, Augen {e.get('eyes', '–')}, {e.get('build', '–')} · "
            f"{e.get('personality', '–')} · {e.get('motivation', '–')} · {e.get('quirk', '–')}"
        )
        table_data.append(
            [
                Paragraph(f"<b>{e.get('full_name', '')}</b>", cell_style),
                _GENDER_SHORT.get(e.get("gender", "any"), "–"),
                str(e.get("age", "–")),
                Paragraph(e.get("profession", "–"), cell_style),
                Paragraph(traits_text, cell_style),
            ]
        )

    tbl = Table(
        table_data,
        colWidths=[name_w, g_w, age_w, job_w, traits_w],
        repeatRows=1,
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("TOPPADDING", (0, 1), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
                ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ]
        )
    )

    story.append(tbl)
    story.append(Spacer(1, 0.5 * cm))
    doc.build(story)

    return buf.getvalue()
