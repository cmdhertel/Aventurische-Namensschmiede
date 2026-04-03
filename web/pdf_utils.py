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
        spaceAfter=14,
    )

    region = name_data[0].get("region", "–") if name_data else "–"
    story = [
        Paragraph("Das Schwarze Auge – Namensliste", title_style),
        Paragraph(f"Region: {region}  ·  {len(name_data)} Namen", subtitle_style),
    ]

    header = ["Name", "G", "Name", "G"]
    table_data = [header]

    for i in range(0, len(name_data), 2):
        left  = name_data[i]
        right = name_data[i + 1] if i + 1 < len(name_data) else None
        table_data.append([
            left["full_name"],
            _GENDER_SHORT.get(left.get("gender", "any"), "–"),
            right["full_name"] if right else "",
            _GENDER_SHORT.get(right.get("gender", "any"), "–") if right else "",
        ])

    name_w = 7.25 * cm
    g_w    = 1.0  * cm
    tbl = Table(table_data, colWidths=[name_w, g_w, name_w, g_w], repeatRows=1)
    tbl.setStyle(TableStyle([
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
        ("LINEAFTER",     (1, 0), (1, -1),  1.0, BORDER),
        ("BOX",           (0, 0), (-1, -1), 0.75, BORDER),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (1, 0), (1, -1),  "CENTER"),
        ("ALIGN",         (3, 0), (3, -1),  "CENTER"),
    ]))

    story.append(tbl)
    story.append(Spacer(1, 0.5*cm))
    doc.build(story)

    return buf.getvalue()
