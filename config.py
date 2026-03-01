import os
from dotenv import load_dotenv

load_dotenv()

# ─── Core Settings ──────────────────────────────
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "")
OWNER_ID    = int(os.environ.get("OWNER_ID", "0"))
PORT        = int(os.environ.get("PORT", "8080"))

# ─── Optional Payment Settings ──────────────────
UPI_ID      = os.environ.get("UPI_ID", "")          # e.g. yourname@upi
UPI_QR_URL  = os.environ.get("UPI_QR_URL", "")      # URL or Telegram file_id of QR image

# ─── Optional Start Media ────────────────────────
START_IMAGE = os.environ.get("START_IMAGE", "")      # URL or file_id of start image/gif

# ─── Optional MongoDB ────────────────────────────
MONGODB_URL = os.environ.get("MONGODB_URL", "")      # Optional, SQLite used if empty

# ─── Pricing ─────────────────────────────────────
BASIC_PRICE  = "₹99"
PRO_PRICE    = "₹249"
BASIC_LABEL  = "Basic – ₹99/month"
PRO_LABEL    = "Pro – ₹249/year"

# ─── Free Tier ───────────────────────────────────
FREE_DAILY_LIMIT = 3

# ─── Handwritten Fonts ───────────────────────────
FONTS = {
    "caveat":       {"name": "✍️ Caveat",         "file": "fonts/Caveat.ttf"},
    "dancing":      {"name": "💃 Dancing Script",  "file": "fonts/DancingScript.ttf"},
    "kalam":        {"name": "📝 Kalam",            "file": "fonts/Kalam.ttf"},
    "pacifico":     {"name": "🎨 Pacifico",         "file": "fonts/Pacifico.ttf"},
    "satisfy":      {"name": "✨ Satisfy",          "file": "fonts/Satisfy.ttf"},
    "shadows":      {"name": "🌙 Shadows Into Light","file": "fonts/ShadowsIntoLight.ttf"},
}

# ─── Random Reactions ────────────────────────────
REACTIONS = ["👍","🔥","❤️","🎉","👏","💯","⚡","🌟","😎","🚀","💎","🎯"]
