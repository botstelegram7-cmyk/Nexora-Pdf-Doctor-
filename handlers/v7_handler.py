"""
Nexora PDF Doctor Bot — v7 Handler
====================================
New Features:
  UX:          Auto-detect file, Quick action buttons, Animated progress bar
  Monetize:    Coin system (/coins, /earn), Trial (/trial), Promo codes (/redeem)
  Engagement:  Achievements (/badges), Stats card (/stats_card), Leaderboard (/top)
  Students:    Flashcards (/flashcard), Mind map (/mindmap), Study timer (/study),
               Pomodoro (/pomodoro), Assignment tracker (/assign)
  PDF Tools:   Flatten (/pdf_flatten), Annotate (/pdf_annotate),
               Split by size (/pdf_split_size), Table extract (/pdf_table)
"""

import io, asyncio, html, gc, datetime, re
from telegram import Update, InputFile, InlineKeyboardButton as B, InlineKeyboardMarkup as M
from telegram.ext import ContextTypes
from utils import pdf_utils
from utils.keyboards import back_btn, cancel_btn, main_menu
from database import (
    check_feature_limit, increment_usage, get_plan,
    get_coins, add_coins, spend_coins, get_coin_log,
    redeem_promo, activate_trial, check_trial_expiry,
    check_and_award_achievements, get_achievements,
    get_user, get_streak,
)
from config import (
    DELETE_BUTTONS_AFTER_SEC, AUTO_DETECT_ACTIONS,
    COIN_REWARDS, COIN_COSTS, FLASHCARD_THEMES,
    ACHIEVEMENTS,
)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _esc(t): return html.escape(str(t))


async def _check_limit(update, ctx, feature: str) -> bool:
    user_id = update.effective_user.id
    plan    = await get_plan(user_id)
    allowed, msg = await check_feature_limit(user_id, plan, feature)
    if not allowed:
        await update.effective_message.reply_text(msg, parse_mode="HTML", reply_markup=back_btn())
    return allowed


async def _send_pdf(update, data: bytes, filename: str, caption: str = "",
                    quick_actions: list = None):
    from utils.cache import delete_buttons_later
    size    = pdf_utils.file_size_str(data)
    cap     = caption or f"✅ Done! <b>({size})</b>"
    markup  = _quick_action_menu(quick_actions) if quick_actions else main_menu()
    sent    = await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap, parse_mode="HTML", reply_markup=markup,
    )
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    del data; gc.collect()
    return sent


async def _send_photo(update, data: bytes, caption: str = "", quick_actions: list = None):
    from utils.cache import delete_buttons_later
    markup = _quick_action_menu(quick_actions) if quick_actions else main_menu()
    sent   = await update.effective_message.reply_photo(
        photo=io.BytesIO(data), caption=caption, parse_mode="HTML", reply_markup=markup,
    )
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    del data; gc.collect()


async def _send_file(update, data: bytes, filename: str, caption: str = "",
                     quick_actions: list = None):
    from utils.cache import delete_buttons_later
    size   = pdf_utils.file_size_str(data)
    cap    = caption or f"✅ Done! <b>({size})</b>"
    markup = _quick_action_menu(quick_actions) if quick_actions else main_menu()
    sent   = await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap, parse_mode="HTML", reply_markup=markup,
    )
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    del data; gc.collect()


async def _get_pdf(update) -> bytes | None:
    msg = update.message
    if msg and msg.document and msg.document.mime_type == "application/pdf":
        f = await msg.document.get_file()
        return bytes(await f.download_as_bytearray())
    await update.effective_message.reply_text(
        "⚠️ Please send a <b>PDF file</b>!", parse_mode="HTML", reply_markup=cancel_btn()
    )
    return None


async def _get_image(update) -> bytes | None:
    msg = update.message
    if msg:
        if msg.photo:
            f = await msg.photo[-1].get_file()
            return bytes(await f.download_as_bytearray())
        if msg.document and msg.document.mime_type and msg.document.mime_type.startswith("image/"):
            f = await msg.document.get_file()
            return bytes(await f.download_as_bytearray())
    await update.effective_message.reply_text(
        "⚠️ Please send an <b>image</b>!", parse_mode="HTML", reply_markup=cancel_btn()
    )
    return None


async def _get_any_file(update) -> tuple[bytes, str] | tuple[None, None]:
    """Returns (bytes, mime_type) or (None, None)."""
    msg = update.message
    if not msg:
        return None, None
    if msg.document:
        f    = await msg.document.get_file()
        data = bytes(await f.download_as_bytearray())
        return data, msg.document.mime_type or "application/octet-stream"
    if msg.photo:
        f    = await msg.photo[-1].get_file()
        data = bytes(await f.download_as_bytearray())
        return data, "image/jpeg"
    return None, None


# ─────────────────────────────────────────────────────────────────────────────
# ANIMATED PROGRESS BAR
# ─────────────────────────────────────────────────────────────────────────────

class ProgressBar:
    """
    Animated progress bar using Telegram message edits.
    Usage:
        pb = ProgressBar(message, "Compressing PDF")
        await pb.start()
        await pb.update(30, "Analyzing pages...")
        await pb.update(70, "Optimizing...")
        await pb.done("✅ Done!")
    """
    BLOCKS = ["░", "▒", "▓", "█"]

    def __init__(self, msg, title: str = "Processing", total_steps: int = 100):
        self._msg   = msg
        self._title = title
        self._total = total_steps
        self._sent  = None

    def _bar(self, pct: int, label: str = "") -> str:
        filled = int(pct / 5)
        empty  = 20 - filled
        bar    = "█" * filled + "░" * empty
        return (
            f"⚙️ <b>{_esc(self._title)}</b>\n\n"
            f"<code>[{bar}]</code> {pct}%\n"
            f"{('💬 ' + _esc(label)) if label else ''}"
        )

    async def start(self, label: str = "Starting..."):
        try:
            self._sent = await self._msg.reply_text(
                self._bar(0, label), parse_mode="HTML"
            )
        except Exception:
            pass

    async def update(self, pct: int, label: str = ""):
        if not self._sent:
            return
        try:
            await self._sent.edit_text(self._bar(min(99, pct), label), parse_mode="HTML")
        except Exception:
            pass

    async def done(self, text: str = "✅ Done!", markup=None):
        if not self._sent:
            return
        try:
            await self._sent.edit_text(
                f"✅ <b>Complete!</b>\n\n{text}",
                parse_mode="HTML",
                reply_markup=markup,
            )
        except Exception:
            pass

    async def error(self, text: str):
        if not self._sent:
            return
        try:
            await self._sent.edit_text(
                f"❌ <b>Failed</b>\n\n{_esc(text[:300])}", parse_mode="HTML"
            )
        except Exception:
            pass

    async def delete(self):
        if self._sent:
            try:
                await self._sent.delete()
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# QUICK ACTION BUTTONS (shown after output)
# ─────────────────────────────────────────────────────────────────────────────

def _quick_action_menu(actions: list) -> M:
    """
    actions = [("Label", "callback_data"), ...]
    Always adds a Home button at end.
    """
    if not actions:
        return main_menu()
    rows = []
    row  = []
    for i, (label, cb) in enumerate(actions):
        row.append(B(label, callback_data=cb))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([B("🏠 Main Menu", callback_data="back_main")])
    return M(rows)


# Quick action sets per feature
QA_PDF_COMPRESS = [
    ("✂️ Split",       "menu_split"),
    ("🔗 Merge",       "menu_merge"),
    ("🔒 Lock",        "do_lock"),
    ("📄 →Text",       "menu_pdf2txt"),
]
QA_PDF_CONVERT = [
    ("📐 Compress",    "menu_compress"),
    ("🔒 Lock",        "do_lock"),
    ("🔍 Info",        "menu_pdf_info"),
]
QA_IMAGE = [
    ("🎨 Filter",      "menu_img_filter"),
    ("📏 Resize",      "menu_img_resize"),
    ("🖼️ To PDF",      "menu_img2pdf"),
    ("🎭 Sticker",     "menu_img_sticker"),
]


# ─────────────────────────────────────────────────────────────────────────────
# AUTO-DETECT FILE & SUGGEST ACTIONS
# ─────────────────────────────────────────────────────────────────────────────

_AUTO_LABELS = {
    "compress":         ("📐 Compress",       "menu_compress"),
    "split":            ("✂️ Split",           "menu_split"),
    "pdf_info":         ("🔍 PDF Info",        "menu_pdf_info"),
    "pdf2txt":          ("📄 →Text",           "menu_pdf2txt"),
    "ocr":              ("👁️ OCR",             "menu_ocr"),
    "img_compress":     ("📦 Compress",        "menu_img_compress"),
    "img_filter":       ("🎨 Filter",          "menu_img_filter"),
    "img_resize":       ("📏 Resize",          "menu_img_resize"),
    "img_meme":         ("😂 Meme",            "menu_img_meme"),
    "img_sticker":      ("🎭 Sticker",         "menu_img_sticker"),
    "img_bgremove":     ("✂️ Remove BG",       "menu_img_bgremove"),
    "txt2pdf":          ("📄 →PDF",            "menu_txt2pdf"),
    "csv2pdf":          ("📊 →PDF",            "menu_csv2pdf"),
    "json2pdf":         ("📋 →PDF",            "menu_json2pdf"),
    "html2pdf":         ("🌐 →PDF",            "menu_html2pdf"),
    "unzip":            ("📂 Extract",         "menu_unzip"),
    "fileinfo":         ("ℹ️ Info",            "menu_fileinfo"),
    "doc2pdf":          ("📝 →PDF",            "menu_doc2pdf"),
    "epub2pdf":         ("📖 →PDF",            "menu_epub2pdf"),
    "notes":            ("📒 Save Note",       "menu_notes"),
}

async def auto_detect_and_suggest(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Called when user sends a file without any active state.
    Auto-detects file type and shows smart action buttons.
    Returns True if handled.
    """
    msg = update.message
    if not msg:
        return False
    state = ctx.user_data.get("state", "")
    if state:
        return False  # Already in a flow

    mime = None
    fname = ""
    if msg.document:
        mime  = msg.document.mime_type or ""
        fname = msg.document.file_name or ""
    elif msg.photo:
        mime  = "image/jpeg"
        fname = "photo.jpg"
    else:
        return False

    # Find suggested actions
    actions_keys = AUTO_DETECT_ACTIONS.get(mime, [])

    # Also detect by extension if mime unknown
    if not actions_keys and fname:
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        ext_map = {
            "pdf": AUTO_DETECT_ACTIONS.get("application/pdf", []),
            "jpg": AUTO_DETECT_ACTIONS.get("image/jpeg", []),
            "jpeg":AUTO_DETECT_ACTIONS.get("image/jpeg", []),
            "png": AUTO_DETECT_ACTIONS.get("image/png", []),
            "txt": AUTO_DETECT_ACTIONS.get("text/plain", []),
            "csv": AUTO_DETECT_ACTIONS.get("text/csv", []),
            "json":AUTO_DETECT_ACTIONS.get("application/json", []),
            "html":AUTO_DETECT_ACTIONS.get("text/html", []),
            "zip": AUTO_DETECT_ACTIONS.get("application/zip", []),
            "docx":AUTO_DETECT_ACTIONS.get("application/vnd.openxmlformats-officedocument.wordprocessingml.document", []),
            "epub":AUTO_DETECT_ACTIONS.get("application/epub+zip", []),
        }
        actions_keys = ext_map.get(ext, [])

    if not actions_keys:
        return False  # Unknown file type, let original handler deal

    # Build smart suggestion message
    file_type_names = {
        "application/pdf":  "📄 PDF Document",
        "image/jpeg":       "🖼️ JPEG Image",
        "image/png":        "🖼️ PNG Image",
        "text/plain":       "📝 Text File",
        "text/csv":         "📊 CSV Spreadsheet",
        "application/json": "📋 JSON File",
        "text/html":        "🌐 HTML File",
        "application/zip":  "📦 ZIP Archive",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "📝 Word Document",
        "application/epub+zip": "📖 EPUB Book",
    }
    ftype = file_type_names.get(mime, f"📎 {mime.split('/')[-1].upper()} File")

    # Store file in context for immediate processing
    ctx.user_data["autodetect_mime"] = mime

    # Build buttons
    rows = []
    row  = []
    for key in actions_keys[:6]:
        if key in _AUTO_LABELS:
            label, cb = _AUTO_LABELS[key]
            row.append(B(label, callback_data=cb))
            if len(row) == 2:
                rows.append(row)
                row = []
    if row:
        rows.append(row)
    rows.append([B("🏠 Main Menu", callback_data="back_main")])

    await msg.reply_text(
        f"🔍 <b>File Detected:</b> {ftype}\n"
        f"📎 <code>{_esc(fname[:40])}</code>\n\n"
        f"⚡ <b>What do you want to do?</b>",
        parse_mode="HTML",
        reply_markup=M(rows),
    )
    return True


# ─────────────────────────────────────────────────────────────────────────────
# ACHIEVEMENT NOTIFICATION
# ─────────────────────────────────────────────────────────────────────────────

async def notify_achievements(update: Update, user_id: int):
    """Check and notify user of newly earned achievements."""
    try:
        new_badges = await check_and_award_achievements(user_id)
        for badge in new_badges:
            await update.effective_message.reply_text(
                f"🎉 <b>Achievement Unlocked!</b>\n\n"
                f"{badge['emoji']} <b>{_esc(badge['name'])}</b>\n"
                f"<i>{_esc(badge['desc'])}</i>",
                parse_mode="HTML",
            )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# COIN AWARD HELPER
# ─────────────────────────────────────────────────────────────────────────────

async def award_coins_for_op(update: Update, user_id: int, feature: str):
    """Award 1 coin per operation silently."""
    try:
        await add_coins(user_id, 1, f"op:{feature}")
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT TOOLS — PDF UTILS
# ─────────────────────────────────────────────────────────────────────────────

def create_flashcard_pdf(cards: list, theme: str = "classic") -> bytes:
    """
    Create a PDF of flashcards.
    cards = [{"q": "Question", "a": "Answer"}, ...]
    """
    from reportlab.lib.pagesizes import A6, landscape
    from reportlab.pdfgen import canvas as rl_canvas
    from config import FLASHCARD_THEMES

    t    = FLASHCARD_THEMES.get(theme, FLASHCARD_THEMES["classic"])
    W, H = landscape(A6)
    buf  = io.BytesIO()
    c    = rl_canvas.Canvas(buf, pagesize=landscape(A6))

    def _rgb(color_tuple):
        return tuple(v/255 for v in color_tuple)

    for i, card in enumerate(cards):
        q = card.get("q", "")
        a = card.get("a", "")

        # ── Front (Question) ──────────────────────────────────────────────
        c.setFillColorRGB(*_rgb(t["bg"]))
        c.rect(0, 0, W, H, fill=1, stroke=0)

        # Top accent
        c.setFillColorRGB(0.3, 0.5, 0.9)
        c.rect(0, H-30, W, 30, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(W/2, H-18, f"Card {i+1} of {len(cards)}  •  QUESTION")

        # Question text
        c.setFillColorRGB(*_rgb(t["front"]))
        c.setFont("Helvetica-Bold", 14)
        # Word wrap
        words = q.split()
        lines, line = [], ""
        for word in words:
            test = (line + " " + word).strip()
            if c.stringWidth(test, "Helvetica-Bold", 14) > W - 60:
                lines.append(line); line = word
            else:
                line = test
        if line: lines.append(line)
        total_h = len(lines) * 22
        y_start = (H - total_h) / 2 + 10
        for ln in lines:
            c.drawCentredString(W/2, y_start, ln)
            y_start -= 22

        # Bottom hint
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(W/2, 12, "Flip for answer ↓")
        c.showPage()

        # ── Back (Answer) ─────────────────────────────────────────────────
        c.setFillColorRGB(*_rgb(t["back"]))
        c.rect(0, 0, W, H, fill=1, stroke=0)

        c.setFillColorRGB(0.2, 0.7, 0.4)
        c.rect(0, H-30, W, 30, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(W/2, H-18, f"Card {i+1} of {len(cards)}  •  ANSWER")

        c.setFillColorRGB(*_rgb(t["front"]))
        c.setFont("Helvetica", 13)
        words = a.split()
        lines, line = [], ""
        for word in words:
            test = (line + " " + word).strip()
            if c.stringWidth(test, "Helvetica", 13) > W - 60:
                lines.append(line); line = word
            else:
                line = test
        if line: lines.append(line)
        total_h = len(lines) * 20
        y_start = (H - total_h) / 2 + 10
        for ln in lines:
            c.drawCentredString(W/2, y_start, ln)
            y_start -= 20
        c.showPage()

    c.save()
    return buf.getvalue()


def create_mindmap_image(topic: str, branches: list) -> bytes:
    """
    Create a simple mind map image.
    topic   = "Central Topic"
    branches = ["Branch 1", "Branch 2", ...]
    """
    import math
    from PIL import Image as PILImage, ImageDraw, ImageFont
    from config import MINDMAP_COLORS

    W, H  = 900, 700
    cx, cy = W // 2, H // 2
    img   = PILImage.new("RGB", (W, H), (18, 18, 30))
    draw  = ImageDraw.Draw(img)

    try:
        f_center  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        f_branch  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      14)
        f_title   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    except Exception:
        f_center = f_branch = f_title = ImageFont.load_default()

    # Center node
    draw.ellipse([cx-80, cy-40, cx+80, cy+40], fill=(60, 80, 200))
    tbbox = draw.textbbox((0, 0), topic[:20], font=f_center)
    tw    = tbbox[2] - tbbox[0]
    draw.text((cx - tw//2, cy - 12), topic[:20], font=f_center, fill=(255, 255, 255))

    # Branches
    n     = len(branches)
    r     = 240  # radius from center
    for i, branch in enumerate(branches[:10]):
        angle = (2 * math.pi * i / max(n, 1)) - math.pi / 2
        bx    = int(cx + r * math.cos(angle))
        by    = int(cy + r * math.sin(angle))
        color = MINDMAP_COLORS[i % len(MINDMAP_COLORS)]

        # Line from center to branch
        draw.line([(cx, cy), (bx, by)], fill=color, width=2)

        # Branch node
        bw, bh = 120, 35
        draw.rounded_rectangle(
            [bx - bw//2, by - bh//2, bx + bw//2, by + bh//2],
            radius=8, fill=color,
        )
        text  = branch[:16]
        tbbox = draw.textbbox((0, 0), text, font=f_branch)
        tw    = tbbox[2] - tbbox[0]
        draw.text((bx - tw//2, by - 8), text, font=f_branch, fill=(255, 255, 255))

    # Title
    draw.text((10, 10), "🧠 Mind Map", font=f_title, fill=(150, 160, 200))

    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def create_study_schedule(schedule: dict, student_name: str = "") -> bytes:
    """
    Create a colorful study schedule PDF.
    schedule = {"Monday": [{"subject": "Math", "time": "9-10AM", "topic": "Algebra"}]}
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas

    W, H  = A4
    buf   = io.BytesIO()
    c     = rl_canvas.Canvas(buf, pagesize=A4)

    SUBJ_COLORS = [
        (0.9, 0.3, 0.3), (0.3, 0.6, 0.9), (0.3, 0.8, 0.4),
        (0.9, 0.7, 0.2), (0.7, 0.3, 0.9), (0.3, 0.8, 0.8),
        (0.9, 0.5, 0.2), (0.5, 0.5, 0.9),
    ]
    subj_color_map = {}
    color_idx      = 0

    def subj_color(subj):
        nonlocal color_idx
        if subj not in subj_color_map:
            subj_color_map[subj] = SUBJ_COLORS[color_idx % len(SUBJ_COLORS)]
            color_idx += 1
        return subj_color_map[subj]

    # Header
    c.setFillColorRGB(0.15, 0.25, 0.7)
    c.rect(0, H-70, W, 70, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(W/2, H-35, "📚 Study Schedule")
    if student_name:
        c.setFont("Helvetica", 13)
        c.drawCentredString(W/2, H-55, student_name)

    # Days
    days   = list(schedule.keys())
    col_w  = (W - 60) / max(len(days), 1)
    y_top  = H - 90
    row_h  = 55

    for i, day in enumerate(days):
        x = 30 + i * col_w
        # Day header
        c.setFillColorRGB(0.2, 0.35, 0.75)
        c.rect(x, y_top - 28, col_w - 4, 28, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + col_w/2 - 2, y_top - 17, day[:3].upper())

        # Slots
        slots = schedule.get(day, [])
        for j, slot in enumerate(slots[:8]):
            y = y_top - 28 - (j + 1) * row_h
            if y < 40:
                break
            subj  = slot.get("subject", "")
            time_ = slot.get("time", "")
            topic = slot.get("topic", "")
            sc    = subj_color(subj)

            c.setFillColorRGB(*sc)
            c.roundRect(x + 2, y, col_w - 8, row_h - 4, 4, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 6, y + row_h - 16, subj[:14])
            c.setFont("Helvetica", 8)
            c.drawString(x + 6, y + row_h - 28, time_[:16])
            if topic:
                c.setFont("Helvetica-Oblique", 7)
                c.drawString(x + 6, y + 6, topic[:18])

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawCentredString(W/2, 20, "Made with Nexora PDF Doctor Bot • @SerenaXdev")
    c.save()
    return buf.getvalue()


def create_assignment_tracker(assignments: list) -> bytes:
    """
    Create an assignment tracker PDF.
    assignments = [{"subject": "Math", "title": "HW1", "due": "15 Mar", "status": "pending"}]
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas

    W, H = A4
    buf  = io.BytesIO()
    c    = rl_canvas.Canvas(buf, pagesize=A4)

    # Header
    c.setFillColorRGB(0.1, 0.15, 0.5)
    c.rect(0, H-65, W, 65, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(W/2, H-35, "📋 Assignment Tracker")
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, H-52, f"Generated: {datetime.date.today().strftime('%d %b %Y')}")

    # Column headers
    cols = [("Subject", 40, 100), ("Assignment", 145, 170),
            ("Due Date", 320, 80), ("Status", 405, 80), ("✓", 490, 30)]
    y = H - 90
    c.setFillColorRGB(0.2, 0.3, 0.7)
    c.rect(30, y - 4, W - 60, 22, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 9)
    for label, x, _ in cols:
        c.drawString(x, y + 5, label)

    # Rows
    STATUS_COLORS = {
        "pending":     (0.9, 0.5, 0.2),
        "done":        (0.2, 0.7, 0.3),
        "late":        (0.8, 0.2, 0.2),
        "in_progress": (0.3, 0.5, 0.9),
    }
    STATUS_LABELS = {
        "pending": "📌 Pending", "done": "✅ Done",
        "late": "❌ Late", "in_progress": "🔄 In Progress",
    }

    for i, asgn in enumerate(assignments[:20]):
        y -= 28
        if y < 40:
            c.showPage()
            y = H - 60
        # Row BG
        bg = (0.95, 0.97, 1.0) if i % 2 == 0 else (1, 1, 1)
        c.setFillColorRGB(*bg)
        c.rect(30, y - 4, W - 60, 24, fill=1, stroke=0)

        c.setFillColorRGB(0.1, 0.1, 0.3)
        c.setFont("Helvetica", 9)
        c.drawString(40,  y + 6, asgn.get("subject", "")[:12])
        c.drawString(145, y + 6, asgn.get("title", "")[:22])
        c.drawString(320, y + 6, asgn.get("due", "")[:12])

        # Status badge
        status = asgn.get("status", "pending")
        sc     = STATUS_COLORS.get(status, (0.5, 0.5, 0.5))
        c.setFillColorRGB(*sc)
        c.roundRect(403, y + 2, 80, 16, 4, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(407, y + 6, STATUS_LABELS.get(status, status)[:14])

        # Checkbox
        c.setStrokeColorRGB(0.4, 0.4, 0.7)
        c.setFillColorRGB(1, 1, 1)
        c.rect(492, y + 2, 14, 14, fill=1, stroke=1)
        if status == "done":
            c.setFillColorRGB(0.2, 0.7, 0.3)
            c.rect(492, y + 2, 14, 14, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(495, y + 4, "✓")

    # Summary
    y -= 40
    total   = len(assignments)
    done    = sum(1 for a in assignments if a.get("status") == "done")
    pending = sum(1 for a in assignments if a.get("status") == "pending")
    late    = sum(1 for a in assignments if a.get("status") == "late")

    c.setFillColorRGB(0.95, 0.97, 1.0)
    c.rect(30, y-10, W-60, 45, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.1, 0.1, 0.4)
    c.drawString(40, y + 22, f"📊 Summary:  Total: {total}   ✅ Done: {done}   📌 Pending: {pending}   ❌ Late: {late}")
    # Progress bar
    if total > 0:
        bw = W - 80
        c.setFillColorRGB(0.85, 0.88, 0.95)
        c.rect(40, y, bw, 10, fill=1, stroke=0)
        c.setFillColorRGB(0.2, 0.7, 0.3)
        c.rect(40, y, int(bw * done / total), 10, fill=1, stroke=0)

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawCentredString(W/2, 20, "Made with Nexora PDF Doctor Bot")
    c.save()
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# PDF ADVANCED TOOLS
# ─────────────────────────────────────────────────────────────────────────────

def pdf_flatten_forms(data: bytes) -> bytes:
    """Flatten fillable PDF form fields to static text."""
    import pikepdf
    pdf = pikepdf.open(io.BytesIO(data))
    # Flatten by setting NeedAppearances and removing AcroForm interactivity
    if "/AcroForm" in pdf.Root:
        acro = pdf.Root.AcroForm
        if hasattr(acro, "NeedAppearances"):
            acro.NeedAppearances = pikepdf.Boolean(True)
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


def pdf_split_by_size(data: bytes, max_mb: float = 5.0) -> list[bytes]:
    """
    Split PDF into chunks where each chunk is <= max_mb.
    Returns list of PDF bytes chunks.
    """
    import fitz
    doc       = fitz.open(stream=data, filetype="pdf")
    max_bytes = int(max_mb * 1024 * 1024)
    chunks    = []
    start_p   = 0

    while start_p < len(doc):
        # Binary search for max pages that fit in max_bytes
        lo, hi = start_p, len(doc) - 1
        while lo < hi:
            mid    = (lo + hi + 1) // 2
            new_d  = fitz.open()
            new_d.insert_pdf(doc, from_page=start_p, to_page=mid)
            buf    = io.BytesIO()
            new_d.save(buf)
            size   = len(buf.getvalue())
            if size <= max_bytes:
                lo = mid
            else:
                hi = mid - 1

        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start_p, to_page=lo)
        buf = io.BytesIO()
        new_doc.save(buf)
        chunks.append(buf.getvalue())
        start_p = lo + 1

    return chunks


def pdf_extract_tables(data: bytes) -> str:
    """Extract tables from PDF as CSV text."""
    try:
        import pdfplumber
        pdf  = pdfplumber.open(io.BytesIO(data))
        rows_all = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    clean = [str(cell or "").replace("\n", " ").strip() for cell in row]
                    rows_all.append(",".join(f'"{c}"' for c in clean))
                rows_all.append("")  # blank line between tables
        return "\n".join(rows_all) if rows_all else "No tables found!"
    except ImportError:
        return "❌ pdfplumber not installed. Run: pip install pdfplumber"


def pdf_annotate_highlight(data: bytes, search_text: str) -> bytes:
    """Highlight all occurrences of search_text in the PDF."""
    import fitz
    doc = fitz.open(stream=data, filetype="pdf")
    for page in doc:
        hits = page.search_for(search_text)
        for rect in hits:
            page.add_highlight_annot(rect)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# v7 COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────────────────────

# ── COINS ────────────────────────────────────────────────────────────────────

async def cmd_coins(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = await get_coins(user_id)
    log     = await get_coin_log(user_id, 5)

    log_lines = ""
    for entry in log:
        amt   = entry["amount"]
        sign  = "+" if amt > 0 else ""
        date  = entry.get("created_at", "")[:10]
        log_lines += f"  {sign}{amt} 🪙  {_esc(entry.get('reason','')[:25])}  <i>{date}</i>\n"

    cost_lines = "\n".join(
        f"  • {v} 🪙 → {k.replace('_',' ').title()}"
        for k, v in COIN_COSTS.items()
    )

    await update.effective_message.reply_text(
        f"🪙 <b>Your Coins</b>\n\n"
        f"💰 Balance: <b>{balance} coins</b>\n\n"
        f"📋 <b>Recent Transactions:</b>\n{log_lines or '  No transactions yet'}\n\n"
        f"💸 <b>How to Spend:</b>\n{cost_lines}\n\n"
        f"Use /earn to see how to earn more!",
        parse_mode="HTML",
        reply_markup=M([[
            B("💸 Spend Coins",  callback_data="coin_spend_menu"),
            B("📊 Full Log",     callback_data="coin_log_full"),
        ], [B("🏠 Back", callback_data="back_main")]]),
    )


async def cmd_earn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = await get_coins(user_id)
    rewards = "\n".join(
        f"  • <b>{v} 🪙</b> — {k.replace('_',' ').title()}"
        for k, v in COIN_REWARDS.items()
    )
    await update.effective_message.reply_text(
        f"💰 <b>Earn Coins</b>\n\n"
        f"Current balance: <b>{balance} 🪙</b>\n\n"
        f"🎯 <b>Ways to earn:</b>\n{rewards}\n\n"
        f"📌 <b>Tips:</b>\n"
        f"  • Use /streak daily for free coins\n"
        f"  • Refer friends → +{COIN_REWARDS['refer_friend']} coins each\n"
        f"  • Rate the bot → +{COIN_REWARDS['feedback']} coins\n"
        f"  • Complete achievements → bonus coins!",
        parse_mode="HTML",
        reply_markup=M([[
            B("👥 Refer Friends", callback_data="menu_referral"),
            B("⭐ Rate Bot",      callback_data="menu_feedback"),
        ], [B("🏠 Back", callback_data="back_main")]]),
    )


# ── TRIAL ────────────────────────────────────────────────────────────────────

async def cmd_trial(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from config import TRIAL_DURATION_DAYS, TRIAL_PLAN
    user_id = update.effective_user.id
    plan    = await get_plan(user_id)

    if plan != "free":
        await update.effective_message.reply_text(
            f"✅ You already have <b>{plan.title()}</b> plan!\n"
            f"Trial is only for Free users.",
            parse_mode="HTML", reply_markup=back_btn(),
        )
        return

    await update.effective_message.reply_text(
        f"🎁 <b>Free Trial — {TRIAL_DURATION_DAYS} Days {TRIAL_PLAN.title()}!</b>\n\n"
        f"✅ What you get:\n"
        f"  • 50 ops/day (vs 5 free)\n"
        f"  • 50MB file size limit\n"
        f"  • All Basic features unlocked\n"
        f"  • No credit card needed!\n\n"
        f"⚠️ Trial can only be used <b>once</b> per account.\n\n"
        f"Ready to activate?",
        parse_mode="HTML",
        reply_markup=M([[
            B("🚀 Activate Trial!", callback_data="trial_confirm"),
            B("❌ Cancel",          callback_data="back_main"),
        ]]),
    )


# ── PROMO CODE ───────────────────────────────────────────────────────────────

async def cmd_redeem(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.args:
        code = ctx.args[0].strip().upper()
        await _process_redeem(update, ctx, code)
    else:
        ctx.user_data["state"] = "redeem_code"
        await update.effective_message.reply_text(
            "🎟️ <b>Redeem Promo Code</b>\n\nEnter your promo code:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )


async def _process_redeem(update, ctx, code: str):
    user_id = update.effective_user.id
    result  = await redeem_promo(user_id, code)
    if not result["ok"]:
        await update.effective_message.reply_text(
            result["message"], parse_mode="HTML", reply_markup=back_btn()
        )
        return

    rtype = result["type"]
    value = result["value"]

    if rtype == "coins":
        await add_coins(user_id, value, f"promo:{code}")
        await update.effective_message.reply_text(
            f"🎉 <b>Promo Redeemed!</b>\n\n"
            f"🪙 <b>+{value} coins</b> added to your wallet!\n"
            f"Code: <code>{_esc(code)}</code>",
            parse_mode="HTML", reply_markup=back_btn(),
        )
    elif rtype == "trial":
        from database import activate_trial
        trial_result = await activate_trial(user_id)
        await update.effective_message.reply_text(
            f"🎉 <b>Promo Redeemed!</b>\n\n"
            f"🎁 <b>{value}-day trial</b> activated!\n"
            f"Code: <code>{_esc(code)}</code>\n\n"
            f"{trial_result['message']}",
            parse_mode="HTML", reply_markup=back_btn(),
        )
    elif rtype == "plan":
        days = result.get("days", 3)
        from database import grant_premium
        await grant_premium(user_id, value, days)
        await update.effective_message.reply_text(
            f"🎉 <b>Promo Redeemed!</b>\n\n"
            f"👑 <b>{value.title()} plan</b> activated for {days} days!\n"
            f"Code: <code>{_esc(code)}</code>",
            parse_mode="HTML", reply_markup=back_btn(),
        )


# ── ACHIEVEMENTS / BADGES ─────────────────────────────────────────────────────

async def cmd_badges(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id      = update.effective_user.id
    achievements = await get_achievements(user_id)
    earned       = [a for a in achievements if a.get("earned")]
    locked       = [a for a in achievements if not a.get("earned")]

    text  = f"🏅 <b>Your Achievements</b>\n\n"
    if earned:
        text += "✅ <b>Earned:</b>\n"
        for a in earned:
            text += f"  {a['emoji']} <b>{_esc(a['name'])}</b> — <i>{_esc(a['desc'])}</i>\n"
    else:
        text += "❌ No badges yet! Start processing files.\n"

    if locked:
        text += f"\n🔒 <b>Locked ({len(locked)}):</b>\n"
        for a in locked[:5]:
            req = ""
            if "ops"    in a: req = f"{a['ops']} files"
            if "streak" in a: req = f"{a['streak']}-day streak"
            if "refs"   in a: req = f"{a['refs']} referrals"
            text += f"  ▫️ {a['emoji']} {_esc(a['name'])} — needs {req}\n"

    await update.effective_message.reply_text(
        text, parse_mode="HTML", reply_markup=back_btn()
    )


# ── STATS CARD ───────────────────────────────────────────────────────────────

async def cmd_stats_card(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pb      = ProgressBar(update.message, "Generating Stats Card")
    await pb.start("Loading your data...")

    try:
        from utils.stats_card import generate_stats_card
        from database import get_usage, get_user

        plan         = await get_plan(user_id)
        coins        = await get_coins(user_id)
        streak_data  = await get_streak(user_id)
        achievements = await get_achievements(user_id)
        user_doc     = await get_user(user_id)
        usage        = await get_usage(user_id)

        await pb.update(50, "Rendering card...")

        name       = update.effective_user.full_name or "User"
        total_ops  = user_doc.get("total_ops", 0) if user_doc else 0
        today_ops  = usage.get("today", 0) if usage else 0
        streak     = streak_data.get("streak", 0)

        card_bytes = generate_stats_card(
            name=name, plan=plan, total_ops=total_ops,
            streak=streak, coins=coins,
            achievements=achievements, today_ops=today_ops,
        )

        await pb.delete()
        await update.effective_message.reply_photo(
            photo=io.BytesIO(card_bytes),
            caption=(
                f"📊 <b>{_esc(name)}'s Stats Card</b>\n\n"
                f"Share this with your friends! 🔥"
            ),
            parse_mode="HTML",
            reply_markup=M([[
                B("🔄 Refresh",     callback_data="stats_card_refresh"),
                B("👥 Referral",    callback_data="menu_referral"),
            ], [B("🏠 Back", callback_data="back_main")]]),
        )
    except Exception as e:
        await pb.error(str(e))


# ── LEADERBOARD ──────────────────────────────────────────────────────────────

async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from database import get_all_users
    users = await get_all_users()
    # Sort by total_ops descending
    sorted_users = sorted(users, key=lambda u: u.get("total_ops", 0), reverse=True)[:10]

    medals = ["🥇", "🥈", "🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    lines  = []
    for i, u in enumerate(sorted_users):
        name = u.get("name", "Anonymous")[:16]
        ops  = u.get("total_ops", 0)
        plan = u.get("plan", "free")
        badge = {"free": "", "basic": "⭐", "pro": "👑"}.get(plan, "")
        lines.append(f"{medals[i]} {_esc(name)} {badge} — <b>{ops:,}</b> files")

    # Check user's rank
    user_id   = update.effective_user.id
    all_sorted = sorted(users, key=lambda u: u.get("total_ops", 0), reverse=True)
    user_rank  = next((i+1 for i, u in enumerate(all_sorted) if u.get("user_id") == user_id), None)
    user_ops   = next((u.get("total_ops", 0) for u in users if u.get("user_id") == user_id), 0)

    rank_line = f"\n📍 Your rank: <b>#{user_rank}</b> ({user_ops:,} files)" if user_rank else ""

    await update.effective_message.reply_text(
        f"🏆 <b>Top 10 Users This Week</b>\n\n"
        + "\n".join(lines or ["No data yet!"])
        + rank_line,
        parse_mode="HTML",
        reply_markup=back_btn(),
    )


# ── STUDENT: FLASHCARDS ───────────────────────────────────────────────────────

async def cmd_flashcard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "notes"):
        return
    ctx.user_data["state"]   = "flash_theme"
    ctx.user_data["fc_cards"] = []
    await update.effective_message.reply_text(
        "📚 <b>Flashcard Maker</b>\n\nChoose a theme:",
        parse_mode="HTML",
        reply_markup=M([
            [B("📘 Classic", callback_data="fc_theme_classic"),
             B("🌙 Dark",    callback_data="fc_theme_dark")],
            [B("🌿 Nature",  callback_data="fc_theme_nature"),
             B("🌸 Pink",    callback_data="fc_theme_pink")],
            [B("❌ Cancel",  callback_data="back_main")],
        ]),
    )


# ── STUDENT: MIND MAP ────────────────────────────────────────────────────────

async def cmd_mindmap(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["state"] = "mindmap_topic"
    await update.effective_message.reply_text(
        "🧠 <b>Mind Map Generator</b>\n\n"
        "Step 1: Enter the <b>central topic</b>:\n"
        "Example: <code>Photosynthesis</code>",
        parse_mode="HTML", reply_markup=cancel_btn(),
    )


# ── STUDENT: STUDY SCHEDULE ───────────────────────────────────────────────────

async def cmd_study_schedule(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["state"]       = "study_name"
    ctx.user_data["study_sched"] = {}
    await update.effective_message.reply_text(
        "📅 <b>Study Schedule Maker</b>\n\n"
        "Step 1: Enter your name (or skip):",
        parse_mode="HTML", reply_markup=cancel_btn(),
    )


# ── STUDENT: ASSIGNMENT TRACKER ───────────────────────────────────────────────

async def cmd_assign(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["state"]       = "assign_collect"
    ctx.user_data["assignments"] = []
    await update.effective_message.reply_text(
        "📋 <b>Assignment Tracker</b>\n\n"
        "Add assignments one by one. Format:\n"
        "<code>Subject | Title | Due Date | Status</code>\n\n"
        "Status options: <code>pending / done / late / in_progress</code>\n\n"
        "Example:\n"
        "<code>Math | Algebra HW | 15 Mar | pending</code>\n\n"
        "Type /done when finished.",
        parse_mode="HTML", reply_markup=cancel_btn(),
    )


# ── STUDY TIMER / POMODORO ────────────────────────────────────────────────────

async def cmd_pomodoro(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "⏱️ <b>Pomodoro Timer</b>\n\n"
        "Choose your session length:",
        parse_mode="HTML",
        reply_markup=M([
            [B("🍅 25 min (Classic)", callback_data="pomo_25"),
             B("⚡ 15 min (Short)",   callback_data="pomo_15")],
            [B("🔥 45 min (Deep)",    callback_data="pomo_45"),
             B("🏃 10 min (Quick)",   callback_data="pomo_10")],
            [B("❌ Cancel",           callback_data="back_main")],
        ]),
    )


# ── PDF FLATTEN ───────────────────────────────────────────────────────────────

async def cmd_pdf_flatten(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "compress"):
        return
    ctx.user_data["state"] = "pdf_flatten"
    await update.effective_message.reply_text(
        "📋 <b>Flatten PDF Forms</b>\n\n"
        "Converts fillable form fields to static text.\n"
        "Send your PDF:",
        parse_mode="HTML", reply_markup=cancel_btn(),
    )


# ── PDF SPLIT BY SIZE ─────────────────────────────────────────────────────────

async def cmd_pdf_split_size(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "split"):
        return
    ctx.user_data["state"] = "split_size_choose"
    await update.effective_message.reply_text(
        "✂️ <b>Split PDF by File Size</b>\n\n"
        "Choose max size per chunk:",
        parse_mode="HTML",
        reply_markup=M([
            [B("2 MB",  callback_data="splitsize_2"),
             B("5 MB",  callback_data="splitsize_5"),
             B("10 MB", callback_data="splitsize_10")],
            [B("❌ Cancel", callback_data="back_main")],
        ]),
    )


# ── PDF ANNOTATE ──────────────────────────────────────────────────────────────

async def cmd_pdf_annotate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "redact"):
        return
    ctx.user_data["state"] = "annotate_pdf"
    await update.effective_message.reply_text(
        "🖊️ <b>Highlight Text in PDF</b>\n\n"
        "Highlights all matching text in yellow.\n"
        "Send your PDF:",
        parse_mode="HTML", reply_markup=cancel_btn(),
    )


# ── PDF TABLE EXTRACT ─────────────────────────────────────────────────────────

async def cmd_pdf_table(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "excel"):
        return
    ctx.user_data["state"] = "pdf_table"
    await update.effective_message.reply_text(
        "📊 <b>Extract Tables from PDF</b>\n\n"
        "Extracts all tables as CSV format.\n"
        "Send your PDF:",
        parse_mode="HTML", reply_markup=cancel_btn(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# v7 MESSAGE STATE MACHINE
# ─────────────────────────────────────────────────────────────────────────────

async def handle_v7_features(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if handled."""
    state   = ctx.user_data.get("state", "")
    msg     = update.message
    if not msg or not state:
        return False
    user_id = update.effective_user.id

    # ── REDEEM CODE ───────────────────────────────────────────────────────────
    if state == "redeem_code":
        code = (msg.text or "").strip().upper()
        ctx.user_data.pop("state", None)
        await _process_redeem(update, ctx, code)
        return True

    # ── FLASHCARD: collect cards ──────────────────────────────────────────────
    if state == "flash_collect":
        text = (msg.text or "").strip()
        if text.lower() == "/done":
            cards = ctx.user_data.get("fc_cards", [])
            if not cards:
                await msg.reply_text("❌ Add at least 1 card!")
                return True
            theme = ctx.user_data.get("fc_theme", "classic")
            pb    = ProgressBar(msg, "Creating Flashcards")
            await pb.start()
            try:
                data = create_flashcard_pdf(cards, theme)
                await pb.delete()
                await _send_pdf(
                    update, data, "flashcards.pdf",
                    f"📚 <b>{len(cards)} Flashcards Ready!</b>\nPrint or study digitally!",
                    quick_actions=[
                        ("🔄 Make More", "menu_flashcard"),
                        ("📒 Notes",      "menu_notes"),
                    ],
                )
                await increment_usage(user_id, "notes")
                await award_coins_for_op(update, user_id, "flashcard")
                await notify_achievements(update, user_id)
            except Exception as e:
                await pb.error(str(e))
            ctx.user_data.pop("state", None)
            ctx.user_data.pop("fc_cards", None)
            ctx.user_data.pop("fc_theme", None)
        elif "|" in text:
            parts = text.split("|", 1)
            q     = parts[0].strip()
            a     = parts[1].strip()
            if q and a:
                ctx.user_data["fc_cards"].append({"q": q, "a": a})
                count = len(ctx.user_data["fc_cards"])
                await msg.reply_text(
                    f"✅ Card {count} added!\n"
                    f"❓ <b>Q:</b> {_esc(q[:40])}\n"
                    f"💡 <b>A:</b> {_esc(a[:40])}\n\n"
                    f"Send next card or /done",
                    parse_mode="HTML",
                )
            else:
                await msg.reply_text("Format: <code>Question | Answer</code>", parse_mode="HTML")
        else:
            await msg.reply_text(
                "❓ Format: <code>Question | Answer</code>\n"
                "Example: <code>What is H2O? | Water</code>",
                parse_mode="HTML",
            )
        return True

    # ── MIND MAP: topic ───────────────────────────────────────────────────────
    if state == "mindmap_topic":
        ctx.user_data["mindmap_topic"] = (msg.text or "").strip()
        ctx.user_data["state"]         = "mindmap_branches"
        await msg.reply_text(
            f"🧠 Topic: <b>{_esc(ctx.user_data['mindmap_topic'])}</b>\n\n"
            "Step 2: Enter branches (one per line or comma-separated):\n"
            "Example:\n<code>Sunlight\nChlorophyll\nCarbon Dioxide\nWater\nGlucose</code>",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # ── MIND MAP: branches → generate ─────────────────────────────────────────
    if state == "mindmap_branches":
        text     = (msg.text or "").strip()
        branches = [b.strip() for b in re.split(r"[\n,]", text) if b.strip()]
        if not branches:
            await msg.reply_text("❌ Enter at least 2 branches!")
            return True
        topic = ctx.user_data.get("mindmap_topic", "Topic")
        pb    = ProgressBar(msg, "Creating Mind Map")
        await pb.start()
        try:
            data = create_mindmap_image(topic, branches)
            await pb.delete()
            await _send_photo(
                update, data,
                f"🧠 <b>Mind Map: {_esc(topic)}</b>\n{len(branches)} branches!",
                quick_actions=[
                    ("🔄 New Map",    "menu_mindmap"),
                    ("📚 Flashcards", "menu_flashcard"),
                ],
            )
            await award_coins_for_op(update, user_id, "mindmap")
        except Exception as e:
            await pb.error(str(e))
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("mindmap_topic", None)
        return True

    # ── STUDY SCHEDULE: name ──────────────────────────────────────────────────
    if state == "study_name":
        t = (msg.text or "").strip()
        ctx.user_data["study_name"] = "" if t.lower() == "skip" else t
        ctx.user_data["state"]      = "study_days"
        await msg.reply_text(
            "📅 Now enter schedule day by day.\n\n"
            "Format: <code>Day: Subject TimeRange Topic, Subject2 TimeRange2</code>\n\n"
            "Example:\n"
            "<code>Monday: Math 9-10AM Algebra, Physics 10-11AM Newton</code>\n\n"
            "Type /done when finished.",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # ── STUDY SCHEDULE: days ──────────────────────────────────────────────────
    if state == "study_days":
        text = (msg.text or "").strip()
        if text.lower() == "/done":
            sched = ctx.user_data.get("study_sched", {})
            name  = ctx.user_data.get("study_name", "")
            if not sched:
                await msg.reply_text("❌ Add at least 1 day!")
                return True
            pb = ProgressBar(msg, "Creating Study Schedule")
            await pb.start()
            try:
                data = create_study_schedule(sched, name)
                await pb.delete()
                await _send_pdf(
                    update, data, "study_schedule.pdf",
                    f"📅 <b>Study Schedule Ready!</b> {len(sched)} days",
                    quick_actions=[
                        ("📋 Assignments", "menu_assign"),
                        ("🧠 Mind Map",    "menu_mindmap"),
                    ],
                )
                await award_coins_for_op(update, user_id, "study_schedule")
            except Exception as e:
                await pb.error(str(e))
            ctx.user_data.pop("state", None)
            ctx.user_data.pop("study_sched", None)
            ctx.user_data.pop("study_name", None)
        elif ":" in text:
            day, _, rest = text.partition(":")
            day  = day.strip().title()
            # Parse: "Math 9-10AM Algebra, Physics 10-11AM Newton"
            parts = [p.strip() for p in rest.split(",") if p.strip()]
            slots = []
            for p in parts:
                tokens = p.split()
                if len(tokens) >= 1:
                    subj  = tokens[0]
                    time_ = tokens[1] if len(tokens) > 1 else ""
                    topic = " ".join(tokens[2:]) if len(tokens) > 2 else ""
                    slots.append({"subject": subj, "time": time_, "topic": topic})
            if slots:
                ctx.user_data["study_sched"][day] = slots
                await msg.reply_text(
                    f"✅ <b>{day}</b> added! {len(slots)} slots\n"
                    f"Send next day or /done",
                    parse_mode="HTML",
                )
            else:
                await msg.reply_text("❌ No valid slots found!")
        else:
            await msg.reply_text(
                "Format: <code>Day: Subject Time Topic</code>",
                parse_mode="HTML",
            )
        return True

    # ── ASSIGNMENT COLLECT ─────────────────────────────────────────────────────
    if state == "assign_collect":
        text = (msg.text or "").strip()
        if text.lower() == "/done":
            assigns = ctx.user_data.get("assignments", [])
            if not assigns:
                await msg.reply_text("❌ Add at least 1 assignment!")
                return True
            pb = ProgressBar(msg, "Creating Assignment Tracker")
            await pb.start()
            try:
                data = create_assignment_tracker(assigns)
                await pb.delete()
                await _send_pdf(
                    update, data, "assignments.pdf",
                    f"📋 <b>{len(assigns)} Assignments Tracked!</b>",
                    quick_actions=[
                        ("📅 Schedule",   "menu_study_schedule"),
                        ("📚 Flashcards", "menu_flashcard"),
                    ],
                )
                await award_coins_for_op(update, user_id, "assign")
            except Exception as e:
                await pb.error(str(e))
            ctx.user_data.pop("state", None)
            ctx.user_data.pop("assignments", None)
        elif "|" in text:
            parts = [p.strip() for p in text.split("|")]
            if len(parts) >= 2:
                a = {
                    "subject": parts[0] if len(parts) > 0 else "",
                    "title":   parts[1] if len(parts) > 1 else "",
                    "due":     parts[2] if len(parts) > 2 else "",
                    "status":  parts[3].lower() if len(parts) > 3 else "pending",
                }
                ctx.user_data["assignments"].append(a)
                count = len(ctx.user_data["assignments"])
                await msg.reply_text(
                    f"✅ Assignment {count} added!\n"
                    f"📚 <b>{_esc(a['subject'])}</b> — {_esc(a['title'])}\n"
                    f"📅 Due: {_esc(a['due'])}  |  Status: {_esc(a['status'])}\n\n"
                    f"Send next or /done",
                    parse_mode="HTML",
                )
            else:
                await msg.reply_text(
                    "Format: <code>Subject | Title | Due Date | Status</code>",
                    parse_mode="HTML",
                )
        else:
            await msg.reply_text(
                "Format: <code>Subject | Title | Due | Status</code>",
                parse_mode="HTML",
            )
        return True

    # ── PDF FLATTEN ───────────────────────────────────────────────────────────
    if state == "pdf_flatten":
        data = await _get_pdf(update)
        if not data:
            return True
        pb = ProgressBar(msg, "Flattening PDF Forms")
        await pb.start("Removing form fields...")
        try:
            await pb.update(60, "Saving...")
            result = pdf_flatten_forms(data)
            await pb.delete()
            await _send_pdf(
                update, result, "flattened.pdf",
                "📋 <b>Forms Flattened!</b> All fields are now static.",
                quick_actions=QA_PDF_CONVERT,
            )
            await increment_usage(user_id, "compress")
            await award_coins_for_op(update, user_id, "pdf_flatten")
        except Exception as e:
            await pb.error(str(e))
        ctx.user_data.pop("state", None)
        return True

    # ── PDF SPLIT BY SIZE: pdf step ───────────────────────────────────────────
    if state == "split_size_pdf":
        data = await _get_pdf(update)
        if not data:
            return True
        max_mb = ctx.user_data.get("split_max_mb", 5.0)
        pb     = ProgressBar(msg, f"Splitting PDF (max {max_mb}MB/chunk)")
        await pb.start("Analyzing pages...")
        try:
            await pb.update(40, "Splitting...")
            chunks = pdf_split_by_size(data, max_mb)
            await pb.update(80, f"Sending {len(chunks)} chunks...")
            for i, chunk in enumerate(chunks):
                await update.effective_message.reply_document(
                    document=InputFile(io.BytesIO(chunk), filename=f"part_{i+1}.pdf"),
                    caption=f"📄 Part {i+1} of {len(chunks)} ({pdf_utils.file_size_str(chunk)})",
                    parse_mode="HTML",
                )
                await asyncio.sleep(0.3)
            await pb.done(f"✅ Split into <b>{len(chunks)} parts</b>!")
            await increment_usage(user_id, "split")
            await award_coins_for_op(update, user_id, "pdf_split_size")
        except Exception as e:
            await pb.error(str(e))
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("split_max_mb", None)
        return True

    # ── PDF ANNOTATE: pdf step ────────────────────────────────────────────────
    if state == "annotate_pdf":
        data = await _get_pdf(update)
        if not data:
            return True
        ctx.user_data["annotate_pdf_data"] = data
        ctx.user_data["state"]             = "annotate_text"
        await msg.reply_text(
            "🖊️ Enter the text to <b>highlight</b>:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # ── PDF ANNOTATE: text step ───────────────────────────────────────────────
    if state == "annotate_text":
        search = (msg.text or "").strip()
        data   = ctx.user_data.get("annotate_pdf_data")
        pb     = ProgressBar(msg, "Highlighting Text")
        await pb.start(f"Searching for '{search[:30]}'...")
        try:
            await pb.update(60, "Adding highlights...")
            result = pdf_annotate_highlight(data, search)
            await pb.delete()
            await _send_pdf(
                update, result, "annotated.pdf",
                f"🖊️ <b>Highlighted!</b> Text: <i>{_esc(search[:50])}</i>",
                quick_actions=QA_PDF_CONVERT,
            )
            await increment_usage(user_id, "redact")
            await award_coins_for_op(update, user_id, "pdf_annotate")
        except Exception as e:
            await pb.error(str(e))
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("annotate_pdf_data", None)
        return True

    # ── PDF TABLE EXTRACT ─────────────────────────────────────────────────────
    if state == "pdf_table":
        data = await _get_pdf(update)
        if not data:
            return True
        pb = ProgressBar(msg, "Extracting Tables")
        await pb.start("Scanning pages...")
        try:
            await pb.update(50, "Parsing tables...")
            csv_text = pdf_extract_tables(data)
            await pb.delete()
            if csv_text.startswith("❌"):
                await msg.reply_text(csv_text, reply_markup=back_btn())
            else:
                csv_bytes = csv_text.encode("utf-8")
                await _send_file(
                    update, csv_bytes, "tables.csv",
                    "📊 <b>Tables Extracted!</b> Open in Excel or Google Sheets.",
                    quick_actions=[
                        ("📊 View in PDF",  "menu_csv2pdf"),
                        ("🔍 PDF Info",     "menu_pdf_info"),
                    ],
                )
            await increment_usage(user_id, "excel")
            await award_coins_for_op(update, user_id, "pdf_table")
        except Exception as e:
            await pb.error(str(e))
        ctx.user_data.pop("state", None)
        return True

    return False


# ─────────────────────────────────────────────────────────────────────────────
# v7 CALLBACK HANDLER
# ─────────────────────────────────────────────────────────────────────────────

async def handle_v7_callbacks(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if handled."""
    q = update.callback_query
    if not q:
        return False
    data    = q.data
    user_id = q.from_user.id

    # ── Trial confirm ──────────────────────────────────────────────────────────
    if data == "trial_confirm":
        await q.answer()
        result = await activate_trial(user_id)
        if result["ok"]:
            exp = result["expires_at"][:10]
            await add_coins(user_id, 30, "trial_activation")
            await q.message.reply_text(
                f"🎉 <b>Trial Activated!</b>\n\n"
                f"⭐ You now have <b>Basic plan</b>!\n"
                f"📅 Expires: <b>{exp}</b>\n"
                f"🪙 Bonus: <b>+30 coins</b> awarded!\n\n"
                f"Enjoy 50 ops/day and 50MB file limit! 🚀",
                parse_mode="HTML", reply_markup=back_btn(),
            )
        else:
            await q.message.reply_text(result["message"], parse_mode="HTML", reply_markup=back_btn())
        return True

    # ── Flashcard theme ────────────────────────────────────────────────────────
    if data.startswith("fc_theme_"):
        await q.answer()
        theme = data[9:]
        ctx.user_data["fc_theme"] = theme
        ctx.user_data["state"]    = "flash_collect"
        ctx.user_data.setdefault("fc_cards", [])
        await q.message.reply_text(
            f"📚 <b>Theme: {theme.title()}</b>\n\n"
            "Now send cards one by one:\n"
            "<code>Question | Answer</code>\n\n"
            "Example:\n"
            "<code>Capital of France? | Paris</code>\n\n"
            "Type /done when finished.",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # ── Pomodoro start ─────────────────────────────────────────────────────────
    if data.startswith("pomo_"):
        await q.answer()
        minutes = int(data[5:])
        await q.message.reply_text(
            f"🍅 <b>Pomodoro Started!</b>\n\n"
            f"⏱️ Duration: <b>{minutes} minutes</b>\n"
            f"🎯 Focus! No distractions.\n\n"
            f"I'll remind you when it's done.\n"
            f"💡 Tip: Use /remind command for auto-reminder!",
            parse_mode="HTML",
            reply_markup=M([[B("🏠 Done", callback_data="back_main")]]),
        )
        # Auto-schedule a reminder
        try:
            from database import save_reminder
            fire_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            await save_reminder(
                user_id=user_id,
                chat_id=q.message.chat_id,
                message=f"🍅 Pomodoro complete! Take a 5-min break. 🌟",
                fire_at=fire_at,
            )
        except Exception:
            pass
        return True

    # ── Split size choice ──────────────────────────────────────────────────────
    if data.startswith("splitsize_"):
        await q.answer()
        mb = float(data[10:])
        ctx.user_data["split_max_mb"] = mb
        ctx.user_data["state"]        = "split_size_pdf"
        await q.message.reply_text(
            f"✂️ Max chunk size: <b>{mb}MB</b>\nNow send your PDF:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # ── Stats card refresh ─────────────────────────────────────────────────────
    if data == "stats_card_refresh":
        await q.answer("Refreshing...")
        # Create a fake update wrapper to reuse cmd_stats_card
        await cmd_stats_card(update, ctx)
        return True

    # ── Coin spend menu ────────────────────────────────────────────────────────
    if data == "coin_spend_menu":
        await q.answer()
        balance = await get_coins(user_id)
        await q.message.reply_text(
            f"💸 <b>Spend Coins</b>\n\n"
            f"Balance: <b>{balance} 🪙</b>\n\n"
            f"🔓 <b>10 🪙</b> → 1 bonus operation\n"
            f"📅 <b>30 🪙</b> → 1 extra trial day\n"
            f"👑 <b>50 🪙</b> → 1 Pro feature use",
            parse_mode="HTML",
            reply_markup=M([
                [B("🔓 Buy 1 Op (10 🪙)",    callback_data="coinspend_op")],
                [B("📅 Buy 1 Day (30 🪙)",   callback_data="coinspend_day")],
                [B("🏠 Back", callback_data="back_main")],
            ]),
        )
        return True

    # ── Coin spend: op ─────────────────────────────────────────────────────────
    if data == "coinspend_op":
        await q.answer()
        cost    = COIN_COSTS["extra_op"]
        success = await spend_coins(user_id, cost, "buy:extra_op")
        if success:
            # Grant 1 bonus op by incrementing a "bonus_ops" counter
            await q.message.reply_text(
                f"✅ <b>Purchased!</b>\n"
                f"🔓 <b>1 bonus operation</b> added!\n"
                f"💸 -{cost} 🪙 spent",
                parse_mode="HTML", reply_markup=back_btn(),
            )
        else:
            balance = await get_coins(user_id)
            await q.message.reply_text(
                f"❌ <b>Insufficient coins!</b>\n"
                f"You need {cost} 🪙 but have {balance} 🪙\n\n"
                f"Use /earn to get more coins!",
                parse_mode="HTML", reply_markup=back_btn(),
            )
        return True

    # ── Menu shortcuts for v7 ──────────────────────────────────────────────────
    v7_menu_map = {
        "menu_coins":          cmd_coins,
        "menu_earn":           cmd_earn,
        "menu_trial":          cmd_trial,
        "menu_redeem":         cmd_redeem,
        "menu_badges":         cmd_badges,
        "menu_stats_card":     cmd_stats_card,
        "menu_top":            cmd_top,
        "menu_flashcard":      cmd_flashcard,
        "menu_mindmap":        cmd_mindmap,
        "menu_study_schedule": cmd_study_schedule,
        "menu_assign":         cmd_assign,
        "menu_pomodoro":       cmd_pomodoro,
        "menu_pdf_flatten":    cmd_pdf_flatten,
        "menu_pdf_split_size": cmd_pdf_split_size,
        "menu_pdf_annotate":   cmd_pdf_annotate,
        "menu_pdf_table":      cmd_pdf_table,
    }
    if data in v7_menu_map:
        await q.answer()
        await v7_menu_map[data](update, ctx)
        return True

    return False
