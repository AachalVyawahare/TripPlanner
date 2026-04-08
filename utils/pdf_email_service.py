import re
import urllib.request
import urllib.parse
import json
import tempfile
import os
import smtplib
from email.message import EmailMessage
from concurrent.futures import ThreadPoolExecutor, as_completed

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER
from dotenv import load_dotenv
load_dotenv()
import logging
logging.basicConfig(level=logging.INFO)
# ── Email Credentials ──────────────────────────────────────
import os

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# ── Colors ─────────────────────────────────────────────────
DARK_BLUE    = colors.HexColor("#1d2671")
PINK         = colors.HexColor("#c33764")
LIGHT_GRAY   = colors.HexColor("#f5f5f5")
MID_GRAY     = colors.HexColor("#888888")
DARK_TEXT    = colors.HexColor("#222222")
WHITE        = colors.white
MORNING_BG   = colors.HexColor("#fff8f0")
AFTERNOON_BG = colors.HexColor("#f0f6ff")
EVENING_BG   = colors.HexColor("#f8f0ff")
DAY_HDR_BG   = colors.HexColor("#eef0ff")


def clean(text):
    """Convert text to safe latin-1 for ReportLab."""
    text = str(text)
    replacements = {
        "\u20b9": "Rs.", "\u25a0": "-",  "\u25a1": "-",
        "\u2588": "#",   "\u2019": "'",  "\u2018": "'",
        "\u201c": '"',   "\u201d": '"',  "\u2013": "-",
        "\u2014": "--",  "\u2022": "*",  "\u00b7": "*",
        "\u2026": "...",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text.strip()


def make_styles():
    return {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22,
            textColor=DARK_BLUE, alignment=TA_CENTER, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=10,
            textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=16),
        "section_heading": ParagraphStyle("section_heading", fontName="Helvetica-Bold",
            fontSize=13, textColor=WHITE, spaceAfter=6, spaceBefore=4, leftIndent=8),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10,
            textColor=DARK_TEXT, spaceAfter=4, leading=15),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=10,
            textColor=DARK_TEXT, spaceAfter=3, leading=14, leftIndent=12),
        "place_name": ParagraphStyle("place_name", fontName="Helvetica-Bold", fontSize=12,
            textColor=DARK_BLUE, spaceAfter=5),
        "food_item": ParagraphStyle("food_item", fontName="Helvetica", fontSize=10,
            textColor=DARK_TEXT, spaceAfter=4, leading=14, leftIndent=8),
        "day_badge": ParagraphStyle("day_badge", fontName="Helvetica-Bold", fontSize=13,
            textColor=WHITE, alignment=TA_CENTER),
        "day_title": ParagraphStyle("day_title", fontName="Helvetica-Bold", fontSize=12,
            textColor=DARK_BLUE, spaceAfter=2),
        "slot_label": ParagraphStyle("slot_label", fontName="Helvetica-Bold", fontSize=9,
            textColor=PINK, spaceAfter=2, leading=12),
        "slot_place": ParagraphStyle("slot_place", fontName="Helvetica-Bold", fontSize=11,
            textColor=DARK_BLUE, spaceAfter=3),
        "slot_detail": ParagraphStyle("slot_detail", fontName="Helvetica", fontSize=9,
            textColor=DARK_TEXT, spaceAfter=2, leading=13),
        "day_summary": ParagraphStyle("day_summary", fontName="Helvetica-Oblique", fontSize=9,
            textColor=colors.HexColor("#555555"), spaceAfter=4, leading=13, leftIndent=8),
    }


def section_header(title, styles):
    data = [[Paragraph(title, styles["section_heading"])]]
    t = Table(data, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), DARK_BLUE),
        ("TOPPADDING",    (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,-1), 9),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
    ]))
    return t


def fetch_wiki_image(place_name, city=""):
    queries = [f"{place_name} {city}".strip(), place_name]
    for query in queries:
        try:
            search_url = (
                "https://en.wikipedia.org/w/api.php"
                f"?action=query&list=search&srsearch={urllib.parse.quote(query)}"
                "&format=json&srlimit=1"
            )
            req = urllib.request.Request(search_url, headers={"User-Agent": "TripPlanner/1.0"})
            with urllib.request.urlopen(req, timeout=4) as r:
                data = json.loads(r.read())
            results = data.get("query", {}).get("search", [])
            if not results:
                continue
            page_title = results[0]["title"]
            img_url = (
                "https://en.wikipedia.org/w/api.php"
                f"?action=query&titles={urllib.parse.quote(page_title)}"
                "&prop=pageimages&format=json&pithumbsize=400"
            )
            req2 = urllib.request.Request(img_url, headers={"User-Agent": "TripPlanner/1.0"})
            with urllib.request.urlopen(req2, timeout=4) as r:
                img_data = json.loads(r.read())
            pages = img_data.get("query", {}).get("pages", {})
            page  = list(pages.values())[0]
            thumb = page.get("thumbnail", {}).get("source")
            if thumb:
                suffix = ".jpg" if "jpg" in thumb.lower() else ".png"
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                req3 = urllib.request.Request(thumb, headers={"User-Agent": "TripPlanner/1.0"})
                with urllib.request.urlopen(req3, timeout=5) as r:
                    tmp.write(r.read())
                tmp.close()
                return tmp.name
        except Exception as e:
           logging.error(f"Image fetch error: {e}")
           continue
    return None


def parse_sections(text):
    """
    Split full plan text into sections using --- separator.
    Order in textarea: budget --- weather --- destinations --- day_plan --- hotels --- transport --- verdict
    """
    # Split by lines that are exactly "---"
    parts = re.split(r'^\s*---\s*$', text, flags=re.MULTILINE)

    # Clean each part
    parts = [p.strip() for p in parts]

    # Remove empty leading part (textarea starts with newline before budget)
    while parts and not parts[0].strip():
        parts.pop(0)

    keys = ["budget", "weather", "destinations", "day_plan", "hotels", "transport", "verdict"]
    secs = {k: "" for k in keys}

    for i, key in enumerate(keys):
        if i < len(parts):
            secs[key] = parts[i].strip()

    return secs


def parse_destinations(text):
    places, food_items = [], []
    in_food = False
    current = None
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        low = line.lower()
        if "local food" in low or "food to try" in low:
            in_food = True
            if current:
                places.append(current)
                current = None
            continue
        if in_food:
            if line.startswith(("-", "•")):
                food_items.append(line.lstrip("-•").strip())
            continue
        m = re.match(r"^(\d+)[\.\)]\s+(.+)", line)
        if m:
            if current:
                places.append(current)
            current = {"name": m.group(2).strip(), "why": "", "best_time": "", "dont_miss": "", "entry": ""}
            continue
        if current:
            if low.startswith("why visit:"):
                current["why"]       = line.split(":", 1)[1].strip()
            elif low.startswith("best time:"):
                current["best_time"] = line.split(":", 1)[1].strip()
            elif re.match(r"^don'?t miss:", low):
                current["dont_miss"] = line.split(":", 1)[1].strip()
            elif low.startswith("entry"):
                current["entry"]     = line.split(":", 1)[1].strip()
    if current:
        places.append(current)
    return places, food_items


def parse_day_plan(text):
    days = []
    cur_day = None
    cur_slot = None
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        dm = re.match(r"^DAY\s+(\d+):?\s*(.*)", line, re.IGNORECASE)
        if dm:
            if cur_day:
                if cur_slot:
                    cur_day["slots"].append(cur_slot)
                    cur_slot = None
                days.append(cur_day)
            after = dm.group(2).strip()
            cur_day = {"number": dm.group(1), "title": after, "slots": [], "summary": ""}
            continue
        if not cur_day:
            continue
        if line.lower().startswith("day summary:"):
            cur_day["summary"] = line.split(":", 1)[1].strip()
            continue
        sm = re.match(r"^(Morning|Afternoon|Evening)\s*[\(\[]?(.*?)[\)\]]?:?$", line, re.IGNORECASE)
        if sm:
            if cur_slot:
                cur_day["slots"].append(cur_slot)
            cur_slot = {
                "type": sm.group(1).lower(),
                "time": sm.group(2).strip(),
                "place": "", "activity": "", "tip": "", "cost": ""
            }
            continue
        if cur_slot:
            c = line.lstrip("-• ")
            lo = c.lower()
            if lo.startswith("place:"):
                cur_slot["place"]    = c.split(":", 1)[1].strip()
            elif lo.startswith("activity:"):
                cur_slot["activity"] = c.split(":", 1)[1].strip()
            elif lo.startswith("travel tip:"):
                cur_slot["tip"]      = c.split(":", 1)[1].strip()
            elif lo.startswith("est. cost:") or lo.startswith("cost:"):
                cur_slot["cost"]     = c.split(":", 1)[1].strip()
    if cur_day:
        if cur_slot:
            cur_day["slots"].append(cur_slot)
        days.append(cur_day)
    return days


def build_body(text, styles):
    items = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            items.append(Spacer(1, 3))
            continue
        if line.startswith(("-", "•")):
            items.append(Paragraph(f"&bull; {clean(line.lstrip('-• ').strip())}", styles["bullet"]))
        elif re.match(r"^\d+\.", line):
            items.append(Paragraph(f"<b>{clean(line)}</b>", styles["body"]))
        elif ":" in line:
            parts = line.split(":", 1)
            items.append(Paragraph(
                f"<b><font color='#1d2671'>{clean(parts[0])}:</font></b> {clean(parts[1])}",
                styles["body"]
            ))
        else:
            items.append(Paragraph(clean(line), styles["body"]))
    return items


def build_day_plan_section(day_plan_text, to_city, styles, tmp_imgs):
    story_items = []
    days = parse_day_plan(day_plan_text)
    if not days:
        story_items.extend(build_body(day_plan_text, styles))
        return story_items

    # Collect all slot places for parallel image fetching
    slot_keys = []
    for d in days:
        for s in d["slots"]:
            if s["place"]:
                slot_keys.append((d["number"], s["type"], s["place"]))

    # Fetch all images in parallel
    img_map = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_wiki_image, place, to_city): (day_num, slot_type, place)
            for day_num, slot_type, place in slot_keys
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                img_map[key] = future.result()
            except Exception:
                img_map[key] = None

    slot_colors = {
        "morning":   (colors.HexColor("#e07b39"), MORNING_BG,   "Morning",   "#e07b39"),
        "afternoon": (colors.HexColor("#3a7bd5"), AFTERNOON_BG, "Afternoon", "#3a7bd5"),
        "evening":   (colors.HexColor("#9b59b6"), EVENING_BG,   "Evening",   "#9b59b6"),
    }

    for day in days:
        places_str = " - ".join([s["place"] for s in day["slots"] if s["place"]]) or to_city
        short_title = day["title"] or places_str

        # Day header
        day_hdr = Table([[
            Paragraph(f"DAY {day['number']}", styles["day_badge"]),
            Paragraph(f"<b>{clean(short_title[:80])}</b>", styles["day_title"])
        ]], colWidths=[22*mm, 142*mm])
        day_hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (0,0),   DARK_BLUE),
            ("BACKGROUND",    (1,0), (1,0),   DAY_HDR_BG),
            ("TOPPADDING",    (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("LEFTPADDING",   (0,0), (0,0),   6),
            ("LEFTPADDING",   (1,0), (1,0),   12),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story_items.append(day_hdr)

        for slot in day["slots"]:
            sc = slot_colors.get(slot["type"], (PINK, LIGHT_GRAY, slot["type"].title(), "#c33764"))
            slot_color, slot_bg, slot_label_str, slot_hex = sc

            img_key  = (day["number"], slot["type"], slot["place"])
            img_path = img_map.get(img_key)
            if img_path:
                tmp_imgs.append(img_path)

            time_str = f" ({clean(slot['time'])})" if slot["time"] else ""
            text_parts = [
                Paragraph(
                    f"<b><font color='{slot_hex}'>{slot_label_str}{time_str}</font></b>",
                    styles["slot_label"]
                )
            ]
            if slot["place"]:
                text_parts.append(Paragraph(f"<b>{clean(slot['place'])}</b>", styles["slot_place"]))
            if slot["activity"]:
                text_parts.append(Paragraph(f"<b>Activity:</b> {clean(slot['activity'])}", styles["slot_detail"]))
            if slot["tip"]:
                text_parts.append(Paragraph(f"<b>Travel Tip:</b> {clean(slot['tip'])}", styles["slot_detail"]))
            if slot["cost"]:
                text_parts.append(Paragraph(f"<b>Est. Cost:</b> {clean(slot['cost'])}", styles["slot_detail"]))

            if img_path:
                try:
                    img_obj = Image(img_path, width=48*mm, height=36*mm)
                    slot_card = Table([[text_parts, img_obj]], colWidths=[112*mm, 50*mm])
                except Exception:
                    slot_card = Table([[text_parts]], colWidths=[162*mm])
            else:
                slot_card = Table([[text_parts]], colWidths=[162*mm])

            slot_card.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), slot_bg),
                ("TOPPADDING",    (0,0), (-1,-1), 9),
                ("BOTTOMPADDING", (0,0), (-1,-1), 9),
                ("LEFTPADDING",   (0,0), (0,-1),  12),
                ("RIGHTPADDING",  (0,0), (-1,-1), 8),
                ("VALIGN",        (0,0), (-1,-1), "TOP"),
                ("LINEBELOW",     (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
                ("LINEBEFORE",    (0,0), (0,-1),  3, slot_color),
            ]))
            story_items.append(slot_card)

        if day["summary"]:
            sum_tbl = Table(
                [[Paragraph(f"* {clean(day['summary'])}", styles["day_summary"])]],
                colWidths=[164*mm]
            )
            sum_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#fff3f7")),
                ("TOPPADDING",    (0,0), (-1,-1), 7),
                ("BOTTOMPADDING", (0,0), (-1,-1), 7),
                ("LEFTPADDING",   (0,0), (-1,-1), 12),
                ("LINEBEFORE",    (0,0), (0,-1),  3, PINK),
            ]))
            story_items.append(sum_tbl)

        story_items.append(Spacer(1, 10))

    return story_items


def generate_pdf(full_plan_text, to_city=""):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()

    doc = SimpleDocTemplate(
        tmp.name, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    styles   = make_styles()
    story    = []
    tmp_imgs = []

    # ── HEADER ──
    story.append(Spacer(1, 20))
    story.append(Paragraph("AI Trip Planner", styles["title"]))
    story.append(Spacer(1, 14))
    story.append(Paragraph("Your Agentic Travel Plan", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=PINK, spaceAfter=12))

    # ── SPLIT SECTIONS BY --- ──
    secs = parse_sections(full_plan_text)

    # ── BUDGET ──
    story.append(section_header("Budget Analysis", styles))
    story.append(Spacer(1, 6))
    story.extend(build_body(secs["budget"], styles))
    story.append(Spacer(1, 10))

    # ── WEATHER ──
    story.append(section_header("Weather Report", styles))
    story.append(Spacer(1, 6))
    story.extend(build_body(secs["weather"], styles))
    story.append(Spacer(1, 10))

    # ── DESTINATIONS ──
    story.append(section_header("Places to Visit", styles))
    story.append(Spacer(1, 8))

    places, food_items = parse_destinations(secs["destinations"])

    dest_img_map = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_wiki_image, place["name"], to_city): i
            for i, place in enumerate(places)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                dest_img_map[idx] = future.result()
            except Exception:
                dest_img_map[idx] = None

    for i, place in enumerate(places):
        img_path = dest_img_map.get(i)
        if img_path:
            tmp_imgs.append(img_path)

        text_col = [Paragraph(f"<b><font color='#1d2671'>{clean(place['name'])}</font></b>", styles["place_name"])]
        if place["why"]:
            text_col.append(Paragraph(f"<b><font color='#c33764'>Why Visit:</font></b> {clean(place['why'])}", styles["body"]))
        if place["best_time"]:
            text_col.append(Paragraph(f"<b><font color='#c33764'>Best Time:</font></b> {clean(place['best_time'])}", styles["body"]))
        if place["dont_miss"]:
            text_col.append(Paragraph(f"<b><font color='#c33764'>Don't Miss:</font></b> {clean(place['dont_miss'])}", styles["body"]))
        if place["entry"]:
            text_col.append(Paragraph(f"<b><font color='#c33764'>Entry Fee:</font></b> {clean(place['entry'])}", styles["body"]))

        if img_path:
            try:
                img  = Image(img_path, width=54*mm, height=38*mm)
                card = Table([[text_col, img]], colWidths=[106*mm, 57*mm])
            except Exception:
                card = Table([[text_col]], colWidths=[163*mm])
        else:
            card = Table([[text_col]], colWidths=[163*mm])

        card.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), LIGHT_GRAY),
            ("TOPPADDING",    (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("LEFTPADDING",   (0,0), (0,-1),  12),
            ("RIGHTPADDING",  (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("LINEBELOW",     (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
        ]))
        story.append(KeepTogether([card, Spacer(1, 8)]))

    # ── FOOD ──
    if food_items:
        food_hdr = Table(
            [[Paragraph("Local Food to Try", styles["section_heading"])]],
            colWidths=[170*mm]
        )
        food_hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), PINK),
            ("TOPPADDING",    (0,0), (-1,-1), 9),
            ("BOTTOMPADDING", (0,0), (-1,-1), 9),
            ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ]))
        story.append(food_hdr)
        story.append(Spacer(1, 6))
        for item in food_items:
            parts = item.split(":", 1)
            if len(parts) == 2:
                story.append(Paragraph(
                    f"<b><font color='#c33764'>&bull; {clean(parts[0])}:</font></b> {clean(parts[1])}",
                    styles["food_item"]
                ))
            else:
                story.append(Paragraph(f"&bull; {clean(item)}", styles["food_item"]))
        story.append(Spacer(1, 10))

    # ── DAY BY DAY PLAN ──
    if secs["day_plan"].strip():
        story.append(section_header("Day-by-Day Itinerary", styles))
        story.append(Spacer(1, 8))
        story.extend(build_day_plan_section(secs["day_plan"], to_city, styles, tmp_imgs))

    # ── HOTELS ──
    story.append(section_header("Hotel Recommendations", styles))
    story.append(Spacer(1, 6))
    story.extend(build_body(secs["hotels"], styles))
    story.append(Spacer(1, 10))

    # ── TRANSPORT ──
    story.append(section_header("Transport Plan", styles))
    story.append(Spacer(1, 6))
    story.extend(build_body(secs["transport"], styles))
    story.append(Spacer(1, 10))

    # ── VERDICT ──
    story.append(section_header("AI Agent Verdict", styles))
    story.append(Spacer(1, 6))
    verdict_inner = build_body(secs["verdict"], styles)
    verdict_tbl   = Table([[verdict_inner]], colWidths=[163*mm])
    verdict_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#fff3f7")),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LINEBEFORE",    (0,0), (0,-1),  3, PINK),
    ]))
    story.append(verdict_tbl)
    story.append(Spacer(1, 16))

    # ── FOOTER ──
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE, spaceAfter=5))
    story.append(Paragraph(
        "Designed &amp; Developed by AI &amp; DS Final Year Team - BNCOE",
        styles["subtitle"]
    ))

    doc.build(story)

    for p in tmp_imgs:
        try:
            os.remove(p)
        except Exception:
            pass

    return tmp.name


def send_email_with_pdf(receiver_email, pdf_path):
    msg = EmailMessage()
    msg["Subject"] = "Your AI Generated Travel Plan"
    msg["From"]    = f"Agentic Trip Planner <{SENDER_EMAIL}>"
    msg["To"]      = receiver_email
    msg.set_content(
        "Hi!\n\nPlease find your AI-generated travel plan attached as a PDF.\n\n"
        "Safe travels!\n- AI Trip Planner, BNCOE"
    )
    with open(pdf_path, "rb") as f:
        file_data = f.read()
    msg.add_attachment(file_data, maintype="application", subtype="pdf", filename="Travel_Plan.pdf")
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            raise ValueError("Email credentials not set in environment variables")

smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)