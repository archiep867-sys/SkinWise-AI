"""Seasonal routine guidance and a compact shareable PDF report for SkinWise AI."""
from __future__ import annotations
from datetime import date
from io import BytesIO
from xml.sax.saxutils import escape
from typing import Any


def photo_capture_tips() -> list[str]:
    """Pre-capture tips; actual image checks run after the user captures/uploads a photo."""
    return [
        "Lighting: face a window or use soft, even light; avoid direct sun, harsh shadows, and backlighting.",
        "Angle: hold the camera at eye level and face forward; keep the whole face visible.",
        "Distance: move close enough for the face to fill most of the frame, but do not crop the forehead or chin.",
        "Sharpness: clean the lens, hold still, and turn off beauty filters; remove glasses if practical.",
    ]


def climate_season_guidance(climate: str, month: int | None = None, location: str = "Mumbai") -> dict[str, Any]:
    """Return conservative seasonal advice. This is not live weather or a live UV reading."""
    month = month or date.today().month
    city = (location or "").strip().lower()
    is_mumbai = "mumbai" in city
    if is_mumbai and month in (6, 7, 8, 9):
        season = "Monsoon / humid season"
    elif is_mumbai and month in (3, 4, 5):
        season = "Hot pre-monsoon season"
    elif is_mumbai and month in (10, 11):
        season = "Post-monsoon transition"
    elif is_mumbai:
        season = "Milder / drier season"
    else:
        season = "Seasonal guidance based on your selected climate"

    tips: list[str] = []
    if climate == "Hot / humid" or (is_mumbai and month in (6, 7, 8, 9, 10)):
        tips += [
            "Prefer a lightweight, non-comedogenic moisturizer if heavy textures feel uncomfortable; do not remove moisturizer automatically if your skin feels dry.",
            "After sweating, gently cleanse when needed rather than scrubbing or repeatedly washing.",
            "Use broad-spectrum SPF 30+ sunscreen in the morning and reapply according to its label, especially outdoors.",
        ]
    elif climate == "Hot / dry" or (is_mumbai and month in (3, 4, 5)):
        tips += [
            "Prioritize broad-spectrum SPF 30+ sunscreen and shade; reapply according to the label when outdoors.",
            "If skin feels tight, choose a moisturizer that supports the skin barrier and avoid adding extra exfoliation.",
        ]
    elif climate == "Cold / dry" or (is_mumbai and month in (12, 1, 2)):
        tips += [
            "If skin feels dry or tight, consider a richer moisturizer and gentle cleansing.",
            "Keep daytime sunscreen in the routine even when the weather feels cooler.",
        ]
    else:
        tips += [
            "Keep a gentle cleanser, moisturizer suited to how your skin feels, and broad-spectrum SPF 30+ sunscreen as routine basics.",
            "Change one routine variable at a time if weather-related dryness or oiliness changes.",
        ]
    return {
        "season": season,
        "location": location,
        "tips": tips,
        "disclaimer": "Seasonal guidance only: this app does not fetch live weather or UV-index data. Check a trusted local forecast for today's conditions and UV index.",
    }


def build_report_pdf(report: dict[str, Any]) -> bytes:
    """Create a simple shareable PDF report. No uploaded photo is embedded."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Brand", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#50394F"), alignment=TA_LEFT, spaceAfter=4))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#6D4C68"), spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name="SmallBody", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=3))
    story = [Paragraph("SkinWise AI", styles["Brand"]), Paragraph("Your skincare routine & progress report", styles["Heading2"]),
             Paragraph(f"Generated: {report.get('date', date.today().isoformat())}  |  Analysis source: {report.get('source', 'Not recorded')}", styles["SmallBody"]), Spacer(1, 5*mm)]

    profile = report.get("profile", {})
    summary = [["Skin type", escape(str(profile.get("skin_type", "Not specified")))], ["Main goals", escape(", ".join(profile.get("concerns", [])) or str(profile.get("goal", "Not specified")))],
               ["Sensitivity", escape(str(profile.get("sensitivity", "Not specified")))], ["Budget", escape(str(profile.get("budget", "Not specified")))],
               ["Climate", escape(str(profile.get("climate", "Not specified")))]]
    table = Table(summary, colWidths=[36*mm, 130*mm])
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (0,-1), colors.HexColor("#F7EFEB")), ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#302631")), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#E7DAD7")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("PADDING", (0,0), (-1,-1), 6)]))
    story += [Paragraph("Your profile", styles["Section"]), table]

    routine = report.get("routine", {})
    for key, heading in (("morning", "Morning routine"), ("evening", "Evening routine")):
        story.append(Paragraph(heading, styles["Section"]))
        items = routine.get(key, []) or []
        if not items:
            story.append(Paragraph("No routine steps were available for this report.", styles["SmallBody"]))
        for item in items:
            name = escape(str(item.get("name", "Routine step")))
            step = str(item.get("step", ""))
            why = escape(str(item.get("why", "")))
            story.append(Paragraph(f"<b>{escape(str(step))}. {name}</b> - {why}" if step else f"<b>{name}</b> - {why}", styles["SmallBody"]))

    climate = report.get("climate_guidance", {})
    if climate:
        story.append(Paragraph("Seasonal care notes", styles["Section"]))
        story.append(Paragraph(escape(f"{climate.get('season', 'Seasonal guidance')} ({climate.get('location', '')})"), styles["SmallBody"]))
        for tip in climate.get("tips", []):
            story.append(Paragraph(f"- {escape(str(tip))}", styles["SmallBody"]))

    progress = report.get("progress", {})
    if progress:
        story.append(Paragraph("Habit & progress snapshot", styles["Section"]))
        story.append(Paragraph(f"Current streak: {progress.get('streak', 0)} day(s) | Days checked in this week: {progress.get('days_this_week', 0)}/7 | Steps completed this week: {progress.get('steps_completed', 0)}/{progress.get('steps_total', 0)}", styles["SmallBody"]))
    if report.get("note"):
        story += [Paragraph("Personal note", styles["Section"]), Paragraph(escape(str(report["note"])), styles["SmallBody"])]
    story += [Spacer(1, 5*mm), Paragraph("Educational information only, not a diagnosis or medical advice. Photo-based metrics can be affected by image quality and other factors. Product details and ingredient lists should be verified. This report contains no uploaded photos.", styles["SmallBody"])]
    doc.build(story)
    return output.getvalue()
