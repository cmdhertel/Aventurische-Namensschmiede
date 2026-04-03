"""PDF-Generierung für den Web-Download (in-memory, gibt bytes zurück)."""

from __future__ import annotations

import io

_GENDER_SHORT = {"male": "M", "female": "W", "any": "–"}


def build_pdf_bytes(name_data: list[dict]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()

    BORDER    = colors.HexColor("#999999")
    HEADER_BG = colors.HexColor("#DDDDDD")
    ROW_ALT   = colors.HexColor("#F5F5F5")

    doc = SimpleDocTemplate(
        buf,
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
            abbr = (cleaned[:3] if cleaned else "???")
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
        left  = name_data[i]
        right = name_data[i + 1] if i + 1 < len(name_data) else None
        if has_multiple_regions:
            table_data.append([
                left["full_name"],
                _GENDER_SHORT.get(left.get("gender", "any"), "–"),
                region_to_abbr.get(left.get("region", ""), "–"),
                right["full_name"] if right else "",
                _GENDER_SHORT.get(right.get("gender", "any"), "–") if right else "",
                region_to_abbr.get(right.get("region", ""), "–") if right else "",
            ])
        else:
            table_data.append([
                left["full_name"],
                _GENDER_SHORT.get(left.get("gender", "any"), "–"),
                right["full_name"] if right else "",
                _GENDER_SHORT.get(right.get("gender", "any"), "–") if right else "",
            ])

    if has_multiple_regions:
        name_w = 7.0 * cm
        g_w = 0.8 * cm
        region_w = 0.7 * cm
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
        ("BACKGROUND",    (0, 0), (-1, 0),  HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.black),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("TOPPADDING",    (0, 0), (-1, 0),  6),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  6),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("BOX",           (0, 0), (-1, -1), 0.75, BORDER),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    for col in center_columns:
        styles.append(("ALIGN", (col, 0), (col, -1), "CENTER"))
    if has_multiple_regions:
        styles.append(("FONTSIZE", (2, 1), (2, -1), 8))
        styles.append(("FONTSIZE", (5, 1), (5, -1), 8))
    for col in separator_columns:
        styles.append(("LINEAFTER", (col, 0), (col, -1), 1.0, BORDER))

    tbl.setStyle(TableStyle(styles))

    story.append(tbl)
    story.append(Spacer(1, 0.5*cm))
    doc.build(story)

    return buf.getvalue()
