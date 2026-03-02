import os
from dotenv import load_dotenv

load_dotenv()

# ─── Core Settings ──────────────────────────────
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "")
OWNER_ID    = int(os.environ.get("OWNER_ID", "0"))
PORT        = int(os.environ.get("PORT", "8080"))

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

# ─── Free Tier ───────────────────────────────────
FREE_DAILY_LIMIT = 3

# ─── Handwritten Fonts (14 fonts!) ───────────────
FONTS = {
    # Original 8
    "caveat":       {"name": "✍️ Caveat",               "file": "fonts/Caveat.ttf"},
    "dancing":      {"name": "💃 Dancing Script",        "file": "fonts/DancingScript.ttf"},
    "kalam":        {"name": "📝 Kalam",                 "file": "fonts/Kalam.ttf"},
    "pacifico":     {"name": "🎨 Pacifico",              "file": "fonts/Pacifico.ttf"},
    "satisfy":      {"name": "✨ Satisfy",               "file": "fonts/Satisfy.ttf"},
    "shadows":      {"name": "🌙 Shadows Into Light",    "file": "fonts/ShadowsIntoLight.ttf"},
    "yellowtail":   {"name": "🌟 Yellowtail",            "file": "fonts/Yellowtail.ttf"},
    "sacramento":   {"name": "🌹 Sacramento",            "file": "fonts/Sacramento.ttf"},
    # New fonts v3
    "amatic":       {"name": "🔠 Amatic SC",             "file": "fonts/AmaticSC.ttf"},
    "indie":        {"name": "📖 Indie Flower",          "file": "fonts/IndieFlower.ttf"},
    "patrick":      {"name": "🍀 Patrick Hand",          "file": "fonts/PatrickHand.ttf"},
    "mali":         {"name": "🌸 Mali",                  "file": "fonts/Mali.ttf"},
    "courgette":    {"name": "☕ Courgette",             "file": "fonts/Courgette.ttf"},
    "paytone":      {"name": "💪 Paytone One",           "file": "fonts/PaytoneOne.ttf"},
}

# ─── Notebook Styles for Handwriting ─────────────
NOTEBOOK_STYLES = {
    "classic_blue": {
        "name": "📘 Classic Blue Lines",
        "bg": (255, 255, 255),
        "line_color": (0.65, 0.82, 1.0),
        "margin_color": (1.0, 0.7, 0.7),
        "text_color": (0.05, 0.05, 0.3),
        "line_spacing": 28,
        "margin_x": 70,
    },
    "yellow_legal": {
        "name": "📒 Yellow Legal Pad",
        "bg": (255, 252, 200),
        "line_color": (0.7, 0.85, 0.5),
        "margin_color": (1.0, 0.4, 0.4),
        "text_color": (0.05, 0.05, 0.05),
        "line_spacing": 26,
        "margin_x": 65,
    },
    "graph_paper": {
        "name": "📐 Graph Paper",
        "bg": (248, 252, 255),
        "line_color": (0.75, 0.87, 1.0),
        "margin_color": None,
        "text_color": (0.05, 0.05, 0.5),
        "line_spacing": 20,
        "margin_x": 50,
        "is_graph": True,
    },
    "dotted": {
        "name": "🔵 Dotted Notebook",
        "bg": (255, 255, 255),
        "line_color": (0.7, 0.7, 0.85),
        "margin_color": None,
        "text_color": (0.0, 0.0, 0.0),
        "line_spacing": 28,
        "margin_x": 50,
        "is_dotted": True,
    },
    "parchment": {
        "name": "📜 Vintage Parchment",
        "bg": (244, 228, 188),
        "line_color": (0.6, 0.45, 0.3),
        "margin_color": (0.55, 0.3, 0.15),
        "text_color": (0.15, 0.05, 0.0),
        "line_spacing": 30,
        "margin_x": 72,
    },
    "dark_notebook": {
        "name": "🌙 Dark Night Mode",
        "bg": (18, 18, 30),
        "line_color": (0.2, 0.2, 0.4),
        "margin_color": (0.4, 0.2, 0.5),
        "text_color": (0.9, 0.95, 1.0),
        "line_spacing": 28,
        "margin_x": 70,
    },
    "pink_diary": {
        "name": "🌸 Pink Diary",
        "bg": (255, 240, 248),
        "line_color": (1.0, 0.72, 0.85),
        "margin_color": (1.0, 0.5, 0.7),
        "text_color": (0.3, 0.0, 0.2),
        "line_spacing": 26,
        "margin_x": 68,
    },
    "green_board": {
        "name": "🟢 Chalkboard Green",
        "bg": (28, 55, 35),
        "line_color": (0.3, 0.6, 0.35),
        "margin_color": (0.5, 0.75, 0.5),
        "text_color": (0.95, 0.95, 0.88),
        "line_spacing": 32,
        "margin_x": 70,
    },
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

# ─── Random Reactions ────────────────────────────
REACTIONS = ["👍","🔥","❤️","🎉","👏","💯","⚡","🌟","😎","🚀","💎","🎯","🥰","😱","🤩"]

# ─── Bot Info ────────────────────────────────────
BOT_VERSION = "3.0.0"
GITHUB      = "@SerenaXdev"
