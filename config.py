import os
from dotenv import load_dotenv

load_dotenv()

# ─── Core Settings ──────────────────────────────
BOT_TOKEN    = os.environ.get("BOT_TOKEN", "")
OWNER_ID     = int(os.environ.get("OWNER_ID", "0"))
PORT         = int(os.environ.get("PORT", "8080"))
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "nexora_admin_2024")

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

# ─── FILE SIZE LIMITS (MB) ───────────────────────
MAX_FILE_SIZE_MB = {
    "free":  20,
    "basic": 50,
    "pro":   100,
}

# ─── Bulk Processing ─────────────────────────────
BULK_MAX_FILES = {
    "free":  0,
    "basic": 10,
    "pro":   25,
}
BULK_QUEUE_TIMEOUT = 120  # seconds

# ─── Broadcast Rate Limiting ─────────────────────
BROADCAST_DELAY_SEC = 0.35
BROADCAST_BATCH     = 25

# ─── Scheduled Deletion Options ──────────────────
SCHEDULED_DELETION_OPTIONS = {
    "30m":  30 * 60,
    "1h":   60 * 60,
    "3h":   3 * 60 * 60,
    "24h":  24 * 60 * 60,
}

# ─── Per-Feature Rate Limits (ops/day) ───────────
FEATURE_LIMITS = {
    # PDF Tools
    "compress":      {"free": 3,  "basic": 30, "pro": None},
    "split":         {"free": 2,  "basic": 20, "pro": None},
    "merge":         {"free": 2,  "basic": 20, "pro": None},
    "lock":          {"free": 3,  "basic": 30, "pro": None},
    "unlock":        {"free": 3,  "basic": 30, "pro": None},
    "repair":        {"free": 2,  "basic": 15, "pro": None},
    "pdf2txt":       {"free": 5,  "basic": 50, "pro": None},
    "linearize":     {"free": 3,  "basic": 30, "pro": None},
    "thumbnail":     {"free": 10, "basic": None,"pro": None},
    "pdf_info":      {"free": 10, "basic": None,"pro": None},
    "redact":        {"free": 2,  "basic": 20, "pro": None},
    "impose":        {"free": 2,  "basic": 20, "pro": None},
    "deskew":        {"free": 2,  "basic": 20, "pro": None},
    "bulk":          {"free": 0,  "basic": 5,  "pro": None},
    # Visual
    "watermark":     {"free": 2,  "basic": 20, "pro": None},
    "darkmode":      {"free": 2,  "basic": 20, "pro": None},
    "bgchange":      {"free": 2,  "basic": 20, "pro": None},
    "rotate":        {"free": 5,  "basic": 50, "pro": None},
    "resize":        {"free": 3,  "basic": 30, "pro": None},
    # Convert PDF
    "pdf2img":       {"free": 2,  "basic": 15, "pro": None},
    "img2pdf":       {"free": 3,  "basic": 20, "pro": None},
    "excel":         {"free": 2,  "basic": 15, "pro": None},
    "pdf2word":      {"free": 2,  "basic": 15, "pro": None},
    "pdf2ppt":       {"free": 0,  "basic": 0,  "pro": None},
    "pdf2epub":      {"free": 0,  "basic": 5,  "pro": None},
    "doc2pdf":       {"free": 2,  "basic": 20, "pro": None},
    "epub2pdf":      {"free": 2,  "basic": 20, "pro": None},
    # Image Tools
    "img_compress":  {"free": 5,  "basic": 50, "pro": None},
    "img_resize":    {"free": 5,  "basic": 50, "pro": None},
    "img_crop":      {"free": 5,  "basic": 50, "pro": None},
    "img_filter":    {"free": 5,  "basic": 50, "pro": None},
    "img_text":      {"free": 3,  "basic": 30, "pro": None},
    "img2jpg":       {"free": 5,  "basic": None,"pro": None},
    "img2png":       {"free": 5,  "basic": None,"pro": None},
    "img_bgremove":  {"free": 0,  "basic": 5,  "pro": None},
    # Document Convert
    "csv2pdf":       {"free": 3,  "basic": 30, "pro": None},
    "txt2pdf":       {"free": 5,  "basic": 50, "pro": None},
    "html2pdf":      {"free": 2,  "basic": 20, "pro": None},
    "json2pdf":      {"free": 3,  "basic": 30, "pro": None},
    # Security & Privacy
    "hash":          {"free": 20, "basic": None,"pro": None},
    "steganography": {"free": 2,  "basic": 15, "pro": None},
    "pdf_sign":      {"free": 2,  "basic": 20, "pro": None},
    "pwd_crack":     {"free": 0,  "basic": 0,  "pro": 1},
    # Creative
    "poster":        {"free": 3,  "basic": 30, "pro": None},
    "calendar_pdf":  {"free": 2,  "basic": 20, "pro": None},
    "invoice":       {"free": 2,  "basic": 20, "pro": None},
    "resume":        {"free": 1,  "basic": 10, "pro": None},
    "certificate":   {"free": 1,  "basic": 10, "pro": None},
    # Utility
    "zip":           {"free": 3,  "basic": 30, "pro": None},
    "unzip":         {"free": 3,  "basic": 30, "pro": None},
    "fileinfo":      {"free": 20, "basic": None,"pro": None},
    "qrcode_scan":   {"free": 10, "basic": None,"pro": None},
    "barcode":       {"free": 10, "basic": None,"pro": None},
    "remind":        {"free": 3,  "basic": 20, "pro": None},
    "notes":         {"free": 5,  "basic": 50, "pro": None},
    "history":       {"free": 5,  "basic": None,"pro": None},
    # Original features
    "handwrite":     {"free": 5,  "basic": 50, "pro": None},
    "addtext":       {"free": 5,  "basic": 50, "pro": None},
    "footer":        {"free": 5,  "basic": 50, "pro": None},
    "pagenos":       {"free": 3,  "basic": 30, "pro": None},
    "crop":          {"free": 5,  "basic": 50, "pro": None},
    "qr":            {"free": 10, "basic": None,"pro": None},
    "extract":       {"free": 3,  "basic": 30, "pro": None},
    "delete_pages":  {"free": 2,  "basic": 20, "pro": None},
    "reorder":       {"free": 3,  "basic": 30, "pro": None},
    "reverse":       {"free": 5,  "basic": 50, "pro": None},
    "pdf_compare":   {"free": 1,  "basic": 10, "pro": None},
    "ocr":           {"free": 3,  "basic": 20, "pro": None},
    "metadata":      {"free": 10, "basic": None,"pro": None},
    "metadata_edit": {"free": 0,  "basic": 10, "pro": None},
}

FREE_DAILY_LIMIT = 5

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

NOTEBOOK_STYLES = {
    "classic_blue": {"name": "📘 Classic Blue Lines",  "bg": (255,255,255), "line_color": (0.65,0.82,1.0), "margin_color": (1.0,0.7,0.7),  "text_color": (0.05,0.05,0.3),  "line_spacing": 28, "margin_x": 70},
    "yellow_legal": {"name": "📒 Yellow Legal Pad",    "bg": (255,252,200), "line_color": (0.7,0.85,0.5),  "margin_color": (1.0,0.4,0.4),  "text_color": (0.05,0.05,0.05), "line_spacing": 26, "margin_x": 65},
    "graph_paper":  {"name": "📐 Graph Paper",         "bg": (248,252,255), "line_color": (0.75,0.87,1.0), "margin_color": None,            "text_color": (0.05,0.05,0.5),  "line_spacing": 20, "margin_x": 50, "is_graph": True},
    "dotted":       {"name": "🔵 Dotted Notebook",     "bg": (255,255,255), "line_color": (0.7,0.7,0.85),  "margin_color": None,            "text_color": (0.0,0.0,0.0),    "line_spacing": 28, "margin_x": 50, "is_dotted": True},
    "parchment":    {"name": "📜 Vintage Parchment",   "bg": (244,228,188), "line_color": (0.6,0.45,0.3),  "margin_color": (0.55,0.3,0.15), "text_color": (0.15,0.05,0.0),  "line_spacing": 30, "margin_x": 72},
    "dark_notebook":{"name": "🌙 Dark Night Mode",     "bg": (18,18,30),    "line_color": (0.2,0.2,0.4),   "margin_color": (0.4,0.2,0.5),  "text_color": (0.9,0.95,1.0),   "line_spacing": 28, "margin_x": 70},
    "pink_diary":   {"name": "🌸 Pink Diary",          "bg": (255,240,248), "line_color": (1.0,0.72,0.85), "margin_color": (1.0,0.5,0.7),  "text_color": (0.3,0.0,0.2),    "line_spacing": 26, "margin_x": 68},
    "green_board":  {"name": "🟢 Chalkboard Green",    "bg": (28,55,35),    "line_color": (0.3,0.6,0.35),  "margin_color": (0.5,0.75,0.5), "text_color": (0.95,0.95,0.88), "line_spacing": 32, "margin_x": 70},
}

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

REACTIONS = [
    "🔥","❤️","🎉","👏","💯","⚡","🌟","😎","🚀","💎",
    "🎯","🥰","😱","🤩","👍","🙏","❤️‍🔥","💪","🏆","✨"
]
REACTION_COUNT = 3

GROUP_REACTIONS_ENABLED = True
GROUP_REACTION_CHANCE   = 0.3

DELETE_BUTTONS_AFTER_SEC = 180

BOT_VERSION = "5.0.0"
GITHUB      = "@SerenaXdev"

HANDWRITING_CREDIT = "Written By - Technical Serena"

IMAGE_FILTERS = {
    "blur":       "🌫️ Blur",
    "sharpen":    "🔪 Sharpen",
    "emboss":     "🌀 Emboss",
    "edge":       "⚡ Edge Enhance",
    "grayscale":  "⬜ Grayscale",
    "sepia":      "🟤 Sepia Tone",
    "brightness": "☀️ Brighten",
    "contrast":   "🔆 High Contrast",
}

PWD_CRACK_TIMEOUT_SEC = 60
PWD_CRACK_COMMON_LIST = [
    "123456","password","123456789","12345678","12345","1234567",
    "1234567890","qwerty","abc123","111111","iloveyou","admin",
    "1234","letmein","monkey","dragon","master","sunshine","princess",
    "welcome","shadow","superman","michael","football","jesus","ninja",
    "mustang","password1","123123","654321","666666","pass","test",
    "000000","zxcvbn","hello","1q2w3e","qwerty123","1q2w3e4r",
    "asdf","asdfgh","zxcvbnm","1111","2222","3333","4444","5555",
    "6666","7777","8888","9999","0000","9876","1357","2468",
]
