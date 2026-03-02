import os
from dotenv import load_dotenv

load_dotenv()

# ─── Core Settings ──────────────────────────────
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "")
OWNER_ID    = int(os.environ.get("OWNER_ID", "0"))
PORT        = int(os.environ.get("PORT", "8080"))
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "nexora_admin_2024")  # Web panel password

# ─── Optional Payment Settings ──────────────────
UPI_ID      = os.environ.get("UPI_ID", "")
UPI_QR_URL  = os.environ.get("UPI_QR_URL", "")

# ─── Optional Start Media ────────────────────────
START_IMAGE = os.environ.get("START_IMAGE", "")

# ─── Optional MongoDB ────────────────────────────
MONGODB_URL = os.environ.get("MONGODB_URL", "")

# ─── Pricing ─────────────────────────────────────
BASIC_PRICE  = "₹99"
PRO_PRICE    = "₹249"
BASIC_LABEL  = "Basic – ₹99/month"
PRO_LABEL    = "Pro – ₹249/year"

# ─── Per-Feature Rate Limits (ops/day) ───────────
# Format: { feature_name: {free: N, basic: N, pro: N} }
# None = unlimited
FEATURE_LIMITS = {
    # PDF Tools
    "compress":     {"free": 3,  "basic": 30, "pro": None},
    "split":        {"free": 2,  "basic": 20, "pro": None},
    "merge":        {"free": 2,  "basic": 20, "pro": None},
    "lock":         {"free": 3,  "basic": 30, "pro": None},
    "unlock":       {"free": 3,  "basic": 30, "pro": None},
    "repair":       {"free": 2,  "basic": 15, "pro": None},
    # Visual
    "watermark":    {"free": 2,  "basic": 20, "pro": None},
    "darkmode":     {"free": 2,  "basic": 20, "pro": None},
    "bgchange":     {"free": 2,  "basic": 20, "pro": None},
    "rotate":       {"free": 5,  "basic": 50, "pro": None},
    "resize":       {"free": 3,  "basic": 30, "pro": None},
    # Convert
    "pdf2img":      {"free": 2,  "basic": 15, "pro": None},
    "img2pdf":      {"free": 3,  "basic": 20, "pro": None},
    "excel":        {"free": 2,  "basic": 15, "pro": None},
    "pdf2word":     {"free": 2,  "basic": 15, "pro": None},
    "pdf2ppt":      {"free": 0,  "basic": 0,  "pro": None},  # Pro only
    # Creative
    "handwrite":    {"free": 5,  "basic": 50, "pro": None},
    "addtext":      {"free": 5,  "basic": 50, "pro": None},
    "footer":       {"free": 5,  "basic": 50, "pro": None},
    "pagenos":      {"free": 3,  "basic": 30, "pro": None},
    "crop":         {"free": 5,  "basic": 50, "pro": None},
    "qr":           {"free": 10, "basic": None,"pro": None},  # QR mostly free
    # Pages
    "extract":      {"free": 3,  "basic": 30, "pro": None},
    "delete_pages": {"free": 2,  "basic": 20, "pro": None},
    "reorder":      {"free": 3,  "basic": 30, "pro": None},
    "reverse":      {"free": 5,  "basic": 50, "pro": None},
    "pdf_compare":  {"free": 1,  "basic": 10, "pro": None},
    # Tools
    "ocr":          {"free": 3,  "basic": 20, "pro": None},
    "metadata":     {"free": 10, "basic": None,"pro": None},
}

FREE_DAILY_LIMIT = 5   # Global fallback

# ─── Handwritten Fonts (14 fonts!) ───────────────
FONTS = {
    "caveat":       {"name": "✍️ Caveat",               "file": "fonts/Caveat.ttf"},
    "dancing":      {"name": "💃 Dancing Script",        "file": "fonts/DancingScript.ttf"},
    "kalam":        {"name": "📝 Kalam",                 "file": "fonts/Kalam.ttf"},
    "pacifico":     {"name": "🎨 Pacifico",              "file": "fonts/Pacifico.ttf"},
    "satisfy":      {"name": "✨ Satisfy",               "file": "fonts/Satisfy.ttf"},
    "shadows":      {"name": "🌙 Shadows Into Light",    "file": "fonts/ShadowsIntoLight.ttf"},
    "yellowtail":   {"name": "🌟 Yellowtail",            "file": "fonts/Yellowtail.ttf"},
    "sacramento":   {"name": "🌹 Sacramento",            "file": "fonts/Sacramento.ttf"},
    "amatic":       {"name": "🔠 Amatic SC",             "file": "fonts/AmaticSC.ttf"},
    "indie":        {"name": "📖 Indie Flower",          "file": "fonts/IndieFlower.ttf"},
    "patrick":      {"name": "🍀 Patrick Hand",          "file": "fonts/PatrickHand.ttf"},
    "mali":         {"name": "🌸 Mali",                  "file": "fonts/Mali.ttf"},
    "courgette":    {"name": "☕ Courgette",             "file": "fonts/Courgette.ttf"},
    "paytone":      {"name": "💪 Paytone One",           "file": "fonts/PaytoneOne.ttf"},
}

# ─── Notebook Styles ─────────────────────────────
NOTEBOOK_STYLES = {
    "classic_blue": {"name": "📘 Classic Blue Lines",   "bg": (255,255,255), "line_color": (0.65,0.82,1.0), "margin_color": (1.0,0.7,0.7),  "text_color": (0.05,0.05,0.3),  "line_spacing": 28, "margin_x": 70},
    "yellow_legal": {"name": "📒 Yellow Legal Pad",     "bg": (255,252,200), "line_color": (0.7,0.85,0.5),  "margin_color": (1.0,0.4,0.4),  "text_color": (0.05,0.05,0.05), "line_spacing": 26, "margin_x": 65},
    "graph_paper":  {"name": "📐 Graph Paper",          "bg": (248,252,255), "line_color": (0.75,0.87,1.0), "margin_color": None,            "text_color": (0.05,0.05,0.5),  "line_spacing": 20, "margin_x": 50, "is_graph": True},
    "dotted":       {"name": "🔵 Dotted Notebook",      "bg": (255,255,255), "line_color": (0.7,0.7,0.85),  "margin_color": None,            "text_color": (0.0,0.0,0.0),    "line_spacing": 28, "margin_x": 50, "is_dotted": True},
    "parchment":    {"name": "📜 Vintage Parchment",    "bg": (244,228,188), "line_color": (0.6,0.45,0.3),  "margin_color": (0.55,0.3,0.15), "text_color": (0.15,0.05,0.0),  "line_spacing": 30, "margin_x": 72},
    "dark_notebook":{"name": "🌙 Dark Night Mode",      "bg": (18,18,30),    "line_color": (0.2,0.2,0.4),   "margin_color": (0.4,0.2,0.5),  "text_color": (0.9,0.95,1.0),   "line_spacing": 28, "margin_x": 70},
    "pink_diary":   {"name": "🌸 Pink Diary",           "bg": (255,240,248), "line_color": (1.0,0.72,0.85), "margin_color": (1.0,0.5,0.7),  "text_color": (0.3,0.0,0.2),    "line_spacing": 26, "margin_x": 68},
    "green_board":  {"name": "🟢 Chalkboard Green",     "bg": (28,55,35),    "line_color": (0.3,0.6,0.35),  "margin_color": (0.5,0.75,0.5), "text_color": (0.95,0.95,0.88), "line_spacing": 32, "margin_x": 70},
}

# ─── OCR Languages ───────────────────────────────
OCR_LANGUAGES = {
    "eng":      {"name": "🇬🇧 English",        "tesseract": "eng"},
    "hin":      {"name": "🇮🇳 Hindi",           "tesseract": "hin"},
    "eng+hin":  {"name": "🇮🇳 Hindi+English",   "tesseract": "eng+hin"},
    "spa":      {"name": "🇪🇸 Spanish",         "tesseract": "spa"},
    "fra":      {"name": "🇫🇷 French",          "tesseract": "fra"},
    "kor":      {"name": "🇰🇷 Korean",          "tesseract": "kor"},
    "chi_sim":  {"name": "🇨🇳 Chinese",         "tesseract": "chi_sim"},
    "ara":      {"name": "🇸🇦 Arabic",          "tesseract": "ara"},
    "deu":      {"name": "🇩🇪 German",          "tesseract": "deu"},
    "jpn":      {"name": "🇯🇵 Japanese",        "tesseract": "jpn"},
}

# ─── Multiple Reactions (4-5 per message) ────────
# Bot will randomly pick 3 from here and react with all 3 simultaneously
REACTIONS = [
    "🔥","❤️","🎉","👏","💯","⚡","🌟","😎","🚀","💎",
    "🎯","🥰","😱","🤩","👍","🙏","❤️‍🔥","💪","🏆","✨"
]
REACTION_COUNT = 3  # How many reactions to send at once

# ─── Group Reaction Settings ─────────────────────
GROUP_REACTIONS_ENABLED = True   # React to all group messages
GROUP_REACTION_CHANCE   = 0.3    # 30% chance to react (avoid spam)

# ─── Delete Buttons Delay ────────────────────────
DELETE_BUTTONS_AFTER_SEC = 180   # Delete inline buttons after 3 minutes

# ─── Bot Info ────────────────────────────────────
BOT_VERSION = "4.0.0"
GITHUB      = "@SerenaXdev"

# ─── Handwriting Branding ──────────────────────────────────────────────────
# Shown at bottom-right of every handwritten page.
# Change to your name, or set to None to hide completely.
HANDWRITING_CREDIT = "Written By - Technical Serena"
