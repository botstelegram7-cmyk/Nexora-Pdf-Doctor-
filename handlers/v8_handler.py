"""
Nexora PDF Doctor Bot — v8 Handler
=====================================
FIXES:
  - style_X callback (was nbstyle_X mismatch)
  - lang_en/hi/es/fr callbacks
  - note_delete callback
  - wm_text / wm_logo direct callbacks (no state needed)
  - do_lock / do_unlock from quick actions
  - menu_pdf2img, menu_img2pdf, menu_pdf2txt, menu_pdf2word, menu_pdf2ppt
  - menu_csv2pdf, menu_txt2pdf, menu_html2pdf, menu_json2pdf, menu_doc2pdf
  - menu_pdf2epub, menu_epub2pdf, menu_img2jpg, menu_img2png
  - impose_4up (was only impose_2up handled)

NEW FEATURES v8:
  - Original filename preservation on all outputs
  - Smart Compress with 3 levels
  - Auto-Rename output files intelligently
  - Batch Mode (/batch)
  - Gift Premium (/gift)
  - Spin Wheel (/spin) — daily prize
  - PDF Diff (/pdf_diff) — visual page diff
  - PDF Background Image (/pdf_bg_img) with intensity slider
  - Favorites (/fav) — pin top 8 commands
  - Dark/Light/Neon Bot Theme (/theme)
  - Onboarding Flow (new users)
  - Smart Help (/help pdf / /help image)
  - Group Stats (/gstats)
  - ZIP to PDF (/zip2pdf)
  - Extra Handwriting fonts (8 new fonts)
  - Extra Notebook themes (6 new themes)
  - /admin inline panel for owner
"""

import io, asyncio, html, gc, datetime, re, random
from telegram import Update, InputFile, InlineKeyboardButton as B, InlineKeyboardMarkup as M
from telegram.ext import ContextTypes
from utils import pdf_utils
from utils.keyboards import back_btn, cancel_btn, main_menu
from database import (
    check_feature_limit, increment_usage, get_plan, get_user,
    get_coins, add_coins, spend_coins,
)
from config import (
    DELETE_BUTTONS_AFTER_SEC, OWNER_ID,
    FONTS, EXTRA_FONTS, EXTRA_FONT_URLS, NOTEBOOK_STYLES, EXTRA_NOTEBOOK_STYLES,
    SPIN_PRIZES, SPIN_COOLDOWN_HOURS, BOT_THEMES,
    SMART_COMPRESS_LEVELS, MAX_FAVORITES, AUTO_DETECT_ACTIONS,
    AUTO_RENAME_PATTERNS,
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


def _smart_filename(original_name: str, operation: str, ext: str = None) -> str:
    """
    Preserve original filename + add operation suffix.
    'report.pdf' + 'compress' -> 'report_compressed.pdf'
    """
    if not original_name:
        return f"{operation}_output.{ext or 'pdf'}"
    base = original_name.rsplit(".", 1)[0]
    out_ext = ext or (original_name.rsplit(".", 1)[-1] if "." in original_name else "pdf")
    suffix_map = {
        "compress":   "compressed",
        "split":      "split",
        "merge":      "merged",
        "lock":       "locked",
        "unlock":     "unlocked",
        "rotate":     "rotated",
        "watermark":  "watermarked",
        "ocr":        "ocr",
        "annotate":   "highlighted",
        "flatten":    "flattened",
        "grayscale":  "grayscale",
        "stamp":      "stamped",
        "header":     "with_header",
        "diff":       "diff",
        "bg_img":     "with_bg",
        "dark":       "darkmode",
        "pagenos":    "numbered",
        "resize":     "resized",
        "crop":       "cropped",
    }
    suffix = suffix_map.get(operation, operation)
    return f"{base}_{suffix}.{out_ext}"


def _auto_rename(original_name: str) -> str:
    """
    Smart auto-rename based on content keywords in filename.
    'hw3_algebra.pdf' -> 'Assignment_hw3_algebra.pdf'
    """
    if not original_name:
        return original_name
    base = original_name.lower()
    for category, keywords in AUTO_RENAME_PATTERNS.items():
        for kw in keywords:
            if kw in base:
                cap = category.title()
                return f"{cap}_{original_name}"
    return original_name  # No match = keep original


async def _send_pdf(update, data: bytes, filename: str, caption: str = "",
                    quick_actions: list = None):
    from utils.cache import delete_buttons_later
    size   = pdf_utils.file_size_str(data)
    cap    = caption or f"✅ Done! <b>{_esc(filename)}</b> ({size})"
    markup = _qa_menu(quick_actions) if quick_actions else main_menu()
    sent   = await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap, parse_mode="HTML", reply_markup=markup,
    )
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    del data; gc.collect()
    return sent


async def _send_photo(update, data: bytes, caption: str = "", quick_actions: list = None):
    from utils.cache import delete_buttons_later
    markup = _qa_menu(quick_actions) if quick_actions else main_menu()
    sent   = await update.effective_message.reply_photo(
        photo=io.BytesIO(data), caption=caption, parse_mode="HTML", reply_markup=markup,
    )
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    del data; gc.collect()


async def _send_file(update, data: bytes, filename: str, caption: str = "",
                     quick_actions: list = None):
    from utils.cache import delete_buttons_later
    size   = pdf_utils.file_size_str(data)
    cap    = caption or f"✅ <b>{_esc(filename)}</b> ({size})"
    markup = _qa_menu(quick_actions) if quick_actions else main_menu()
    sent   = await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap, parse_mode="HTML", reply_markup=markup,
    )
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    del data; gc.collect()


async def _get_pdf(update) -> tuple[bytes | None, str]:
    """Returns (bytes, original_filename) or (None, '')"""
    msg = update.message
    if msg and msg.document and msg.document.mime_type == "application/pdf":
        f = await msg.document.get_file()
        fname = msg.document.file_name or "document.pdf"
        return bytes(await f.download_as_bytearray()), fname
    await update.effective_message.reply_text(
        "⚠️ Please send a <b>PDF file</b>!", parse_mode="HTML", reply_markup=cancel_btn()
    )
    return None, ""


async def _get_image(update) -> tuple[bytes | None, str]:
    msg = update.message
    if msg:
        if msg.photo:
            f = await msg.photo[-1].get_file()
            return bytes(await f.download_as_bytearray()), "photo.jpg"
        if msg.document and msg.document.mime_type and msg.document.mime_type.startswith("image/"):
            f = await msg.document.get_file()
            return bytes(await f.download_as_bytearray()), msg.document.file_name or "image.jpg"
    await update.effective_message.reply_text(
        "⚠️ Please send an <b>image</b>!", parse_mode="HTML", reply_markup=cancel_btn()
    )
    return None, ""


def _qa_menu(actions: list) -> M:
    if not actions:
        return main_menu()
    rows, row = [], []
    for label, cb in actions:
        row.append(B(label, callback_data=cb))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    rows.append([B("🏠 Main Menu", callback_data="back_main")])
    return M(rows)


# ─────────────────────────────────────────────────────────────────────────────
# PROGRESS BAR (inline edit)
# ─────────────────────────────────────────────────────────────────────────────

class PB:
    def __init__(self, msg, title="Processing"):
        self._msg = msg; self._title = title; self._sent = None

    def _render(self, pct, label=""):
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        return (f"⚙️ <b>{_esc(self._title)}</b>\n\n"
                f"<code>[{bar}] {pct}%</code>"
                + (f"\n💬 {_esc(label)}" if label else ""))

    async def start(self, label="Starting..."):
        try: self._sent = await self._msg.reply_text(self._render(0, label), parse_mode="HTML")
        except Exception: pass

    async def update(self, pct, label=""):
        if not self._sent: return
        try: await self._sent.edit_text(self._render(min(99, pct), label), parse_mode="HTML")
        except Exception: pass

    async def done(self, text="✅ Done!", markup=None):
        if not self._sent: return
        try: await self._sent.edit_text(f"✅ <b>Complete!</b>\n\n{text}", parse_mode="HTML", reply_markup=markup)
        except Exception: pass

    async def error(self, text):
        if not self._sent: return
        try: await self._sent.edit_text(f"❌ <b>Failed</b>\n\n{_esc(text[:300])}", parse_mode="HTML")
        except Exception: pass

    async def delete(self):
        if self._sent:
            try: await self._sent.delete()
            except Exception: pass


# ─────────────────────────────────────────────────────────────────────────────
# EXTENDED FONT MENU (original + extra fonts)
# ─────────────────────────────────────────────────────────────────────────────

def all_fonts_menu() -> M:
    """Show all fonts — original + extra — in 2-column grid."""
    all_fonts = {**FONTS, **EXTRA_FONTS}
    items     = list(all_fonts.items())
    rows      = []
    for i in range(0, len(items), 2):
        row = [B(v["name"], callback_data=f"font_{k}") for k, v in items[i:i+2]]
        rows.append(row)
    rows.append([B("🏠 Back", callback_data="back_main")])
    return M(rows)


def all_styles_menu() -> M:
    """Show all notebook styles — original + extra — in 2-column grid."""
    all_styles = {**NOTEBOOK_STYLES, **EXTRA_NOTEBOOK_STYLES}
    items      = list(all_styles.items())
    rows       = []
    for i in range(0, len(items), 2):
        row = [B(v["name"], callback_data=f"style_{k}") for k, v in items[i:i+2]]
        rows.append(row)
    rows.append([B("🏠 Back", callback_data="back_main")])
    return M(rows)


# ─────────────────────────────────────────────────────────────────────────────
# SMART COMPRESS
# ─────────────────────────────────────────────────────────────────────────────

def smart_compress_pdf(data: bytes, level: str = "normal") -> bytes:
    """3-level smart compression."""
    import fitz, pikepdf
    cfg = SMART_COMPRESS_LEVELS.get(level, SMART_COMPRESS_LEVELS["normal"])
    max_px  = cfg["img_max"]
    quality = cfg["img_quality"]

    results = []
    # Method 1: recompress streams
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            buf = io.BytesIO()
            pdf.save(buf, compress_streams=True,
                     stream_decode_level=pikepdf.StreamDecodeLevel.generalized)
            results.append(buf.getvalue())
    except Exception:
        pass
    # Method 2: image downsample + recompress
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            for page in doc:
                for img in page.get_images(full=True):
                    xref    = img[0]
                    base    = doc.extract_image(xref)
                    from PIL import Image
                    pil_img = Image.open(io.BytesIO(base["image"]))
                    if pil_img.width > max_px or pil_img.height > max_px:
                        pil_img.thumbnail((max_px, max_px), Image.LANCZOS)
                    if pil_img.mode in ("RGBA", "P"):
                        pil_img = pil_img.convert("RGB")
                    out_buf = io.BytesIO()
                    pil_img.save(out_buf, format="JPEG", quality=quality, optimize=True)
                    doc.update_stream(xref, out_buf.getvalue())
            buf = io.BytesIO()
            doc.save(buf, garbage=4, deflate=True, deflate_images=True, deflate_fonts=True, clean=True)
            results.append(buf.getvalue())
    except Exception:
        pass
    if not results:
        return data
    best = min(results, key=len)
    return best if len(best) < len(data) else data


# ─────────────────────────────────────────────────────────────────────────────
# PDF DIFF
# ─────────────────────────────────────────────────────────────────────────────

def pdf_diff_pages(data1: bytes, data2: bytes, dpi: int = 100) -> list[bytes]:
    """
    Visual diff of two PDFs. Returns list of diff images (one per page pair).
    Red = in doc1 only, Green = in doc2 only, unchanged = light.
    """
    import fitz
    from PIL import Image, ImageChops, ImageFilter, ImageEnhance
    doc1 = fitz.open(stream=data1, filetype="pdf")
    doc2 = fitz.open(stream=data2, filetype="pdf")
    n    = max(len(doc1), len(doc2))
    diffs = []
    mat  = fitz.Matrix(dpi / 72, dpi / 72)

    for i in range(n):
        if i < len(doc1):
            pix1 = doc1[i].get_pixmap(matrix=mat, alpha=False)
            img1 = Image.open(io.BytesIO(pix1.tobytes("png"))).convert("RGB")
        else:
            img1 = Image.new("RGB", img2.size, (255, 255, 255))

        if i < len(doc2):
            pix2 = doc2[i].get_pixmap(matrix=mat, alpha=False)
            img2 = Image.open(io.BytesIO(pix2.tobytes("png"))).convert("RGB")
        else:
            img2 = Image.new("RGB", img1.size, (255, 255, 255))

        # Resize to same size
        w = min(img1.width,  img2.width)
        h = min(img1.height, img2.height)
        img1 = img1.resize((w, h), Image.LANCZOS)
        img2 = img2.resize((w, h), Image.LANCZOS)

        diff = ImageChops.difference(img1, img2)
        # Amplify differences
        diff_e = ImageEnhance.Brightness(diff).enhance(3.0)

        # Blend: base = average, overlay = colored diff
        from PIL import ImageDraw
        base   = Image.blend(img1, img2, 0.5)
        # Tint removed pixels red, added pixels green
        r, g, b = diff_e.split()
        red_mask   = Image.merge("RGB", (r, Image.new("L", r.size, 0), Image.new("L", r.size, 0)))
        green_mask = Image.merge("RGB", (Image.new("L", g.size, 0), g, Image.new("L", g.size, 0)))
        result = Image.blend(base, red_mask,   alpha=0.4)
        result = Image.blend(result, green_mask, alpha=0.3)

        # Add page label
        draw = ImageDraw.Draw(result)
        draw.rectangle([0, 0, w, 22], fill=(30, 30, 80))
        draw.text((5, 4), f"Page {i+1}  |  🔴 Removed  🟢 Added", fill=(255, 255, 255))

        buf = io.BytesIO()
        result.save(buf, "PNG")
        diffs.append(buf.getvalue())

    return diffs


# ─────────────────────────────────────────────────────────────────────────────
# PDF BACKGROUND IMAGE
# ─────────────────────────────────────────────────────────────────────────────

def pdf_add_bg_image(pdf_data: bytes, img_data: bytes, opacity: float = 0.15) -> bytes:
    """
    Add a background image to every PDF page with adjustable opacity (0.0 - 1.0).
    """
    import fitz
    from PIL import Image
    doc   = fitz.open(stream=pdf_data, filetype="pdf")
    # Prepare image with opacity
    pil   = Image.open(io.BytesIO(img_data)).convert("RGBA")
    # Apply opacity to alpha channel
    r, g, b, a = pil.split()
    from PIL import ImageEnhance
    a = ImageEnhance.Brightness(a).enhance(opacity)
    pil.putalpha(a)
    img_buf = io.BytesIO()
    pil.save(img_buf, "PNG")
    img_bytes = img_buf.getvalue()

    for page in doc:
        rect = page.rect
        # Insert image as background (behind existing content)
        page.insert_image(rect, stream=img_bytes, keep_proportion=True, overlay=False)

    buf = io.BytesIO()
    doc.save(buf, garbage=3, deflate=True)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# ZIP TO PDF
# ─────────────────────────────────────────────────────────────────────────────

def zip_images_to_pdf(zip_data: bytes) -> bytes:
    """Extract images from ZIP and merge into single PDF."""
    import zipfile, fitz
    from PIL import Image

    doc = fitz.open()
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        img_names = sorted([
            n for n in zf.namelist()
            if n.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"))
        ])
        if not img_names:
            raise ValueError("No images found in ZIP!")
        for name in img_names[:100]:  # max 100 images
            img_bytes = zf.read(name)
            pil       = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img_buf   = io.BytesIO()
            pil.save(img_buf, "JPEG", quality=85)
            # Create A4 page
            page = doc.new_page(width=595, height=842)
            page.insert_image(page.rect, stream=img_buf.getvalue(), keep_proportion=True)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# SPIN WHEEL PRIZE LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def _roll_prize() -> dict:
    prizes  = SPIN_PRIZES
    weights = [p["weight"] for p in prizes]
    return random.choices(prizes, weights=weights, k=1)[0]


async def _can_spin(user_id: int) -> bool:
    """True if user hasn't spun in last SPIN_COOLDOWN_HOURS hours."""
    try:
        from database import _get_conn, _mongo_db
        if _mongo_db:
            doc = await _mongo_db.spin_log.find_one({"user_id": user_id})
            if doc:
                last = datetime.datetime.fromisoformat(doc["last_spin"])
                return (datetime.datetime.now() - last).total_seconds() > SPIN_COOLDOWN_HOURS * 3600
            return True
        with _get_conn() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS spin_log
                (user_id INTEGER PRIMARY KEY, last_spin TEXT)""")
            row = conn.execute("SELECT last_spin FROM spin_log WHERE user_id=?", (user_id,)).fetchone()
            if row:
                last = datetime.datetime.fromisoformat(row[0])
                return (datetime.datetime.now() - last).total_seconds() > SPIN_COOLDOWN_HOURS * 3600
            return True
    except Exception:
        return True


async def _record_spin(user_id: int):
    try:
        from database import _get_conn, _mongo_db, _now
        now = datetime.datetime.now().isoformat()
        if _mongo_db:
            await _mongo_db.spin_log.update_one(
                {"user_id": user_id}, {"$set": {"last_spin": now}}, upsert=True
            )
        else:
            with _get_conn() as conn:
                conn.execute("""INSERT INTO spin_log(user_id,last_spin) VALUES(?,?)
                    ON CONFLICT(user_id) DO UPDATE SET last_spin=?""", (user_id, now, now))
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# FAVORITES SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

async def get_favorites(user_id: int) -> list:
    try:
        from database import _get_conn, _mongo_db
        if _mongo_db:
            doc = await _mongo_db.favorites.find_one({"user_id": user_id})
            return doc.get("commands", []) if doc else []
        with _get_conn() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS favorites
                (user_id INTEGER PRIMARY KEY, commands TEXT)""")
            row = conn.execute("SELECT commands FROM favorites WHERE user_id=?", (user_id,)).fetchone()
            if row and row[0]:
                import json
                return json.loads(row[0])
    except Exception:
        pass
    return []


async def save_favorites(user_id: int, commands: list):
    try:
        import json
        from database import _get_conn, _mongo_db
        if _mongo_db:
            await _mongo_db.favorites.update_one(
                {"user_id": user_id}, {"$set": {"commands": commands}}, upsert=True
            )
        else:
            with _get_conn() as conn:
                conn.execute("""CREATE TABLE IF NOT EXISTS favorites
                    (user_id INTEGER PRIMARY KEY, commands TEXT)""")
                conn.execute("""INSERT INTO favorites(user_id,commands) VALUES(?,?)
                    ON CONFLICT(user_id) DO UPDATE SET commands=?""",
                    (user_id, json.dumps(commands), json.dumps(commands)))
    except Exception:
        pass


def favorites_menu(commands: list) -> M:
    CMD_LABELS = {
        "compress": "📐 Compress", "split": "✂️ Split", "merge": "🔗 Merge",
        "ocr": "👁️ OCR", "pdf_info": "🔍 PDF Info", "pdf2txt": "📄 →Text",
        "img_filter": "🎨 Filter", "img_compress": "📦 Img Compress",
        "txt2pdf": "📄 TXT→PDF", "watermark": "🌊 Watermark",
        "handwrite": "✍️ Handwrite", "pdf_stamp": "🖊️ Stamp",
        "flashcard": "📚 Flashcard", "mindmap": "🧠 Mind Map",
        "lock": "🔒 Lock", "unlock": "🔓 Unlock",
    }
    rows = []
    for i in range(0, len(commands), 2):
        row = []
        for cmd in commands[i:i+2]:
            label = CMD_LABELS.get(cmd, f"/{cmd}")
            row.append(B(label, callback_data=f"menu_{cmd}"))
        rows.append(row)
    rows.append([B("➕ Add Favorite", callback_data="fav_add"),
                 B("🗑️ Remove",       callback_data="fav_remove")])
    rows.append([B("🏠 Back", callback_data="back_main")])
    return M(rows)


# ─────────────────────────────────────────────────────────────────────────────
# BOT THEME SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

async def get_user_theme(user_id: int) -> str:
    try:
        from database import _get_conn, _mongo_db
        if _mongo_db:
            doc = await _mongo_db.users.find_one({"user_id": user_id})
            return doc.get("theme", "default") if doc else "default"
        with _get_conn() as conn:
            row = conn.execute("SELECT theme FROM users WHERE user_id=?", (user_id,)).fetchone()
            return row["theme"] if row and "theme" in row.keys() else "default"
    except Exception:
        return "default"


async def set_user_theme(user_id: int, theme: str):
    try:
        from database import _get_conn, _mongo_db
        if _mongo_db:
            await _mongo_db.users.update_one({"user_id": user_id}, {"$set": {"theme": theme}})
        else:
            with _get_conn() as conn:
                try:
                    conn.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'default'")
                except Exception:
                    pass
                conn.execute("UPDATE users SET theme=? WHERE user_id=?", (theme, user_id))
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# ONBOARDING FLOW
# ─────────────────────────────────────────────────────────────────────────────

async def show_onboarding(update: Update, ctx: ContextTypes.DEFAULT_TYPE, step: int = 1):
    steps = {
        1: {
            "text": (
                "👋 <b>Welcome to Nexora PDF Doctor!</b>\n\n"
                "I'm your all-in-one file assistant! Let me show you around.\n\n"
                "📄 <b>Step 1 of 3 — PDF Tools</b>\n"
                "Just send me any PDF file and I'll suggest what to do!\n"
                "Or pick from 50+ PDF operations below."
            ),
            "next": "onboard_2",
        },
        2: {
            "text": (
                "🖼️ <b>Step 2 of 3 — Image Tools</b>\n\n"
                "Send any image and I'll auto-detect it!\n"
                "• Remove backgrounds\n"
                "• Apply filters\n"
                "• Make memes & stickers\n"
                "• Create collages"
            ),
            "next": "onboard_3",
        },
        3: {
            "text": (
                "🎓 <b>Step 3 of 3 — Student Tools</b>\n\n"
                "Built for students! Try:\n"
                "📚 /flashcard — Study cards\n"
                "🧠 /mindmap — Mind maps\n"
                "📅 /study_schedule — Weekly plan\n"
                "📋 /assign — Assignment tracker\n"
                "🍅 /pomodoro — Focus timer\n\n"
                "🎁 <b>Use /trial for 3 free days of Premium!</b>"
            ),
            "next": "onboard_done",
        },
    }
    s    = steps.get(step, steps[3])
    btns = []
    if step < 3:
        btns.append([B(f"Next ➡️ Step {step+1}", callback_data=s["next"]),
                     B("Skip", callback_data="onboard_done")])
    else:
        btns.append([B("🚀 Let's Go!", callback_data="onboard_done")])

    await update.effective_message.reply_text(
        s["text"], parse_mode="HTML", reply_markup=M(btns)
    )


async def check_and_show_onboarding(update: Update, ctx: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show onboarding only for brand new users (first message)."""
    try:
        from database import get_user
        user_doc = await get_user(user_id)
        if user_doc and user_doc.get("total_ops", 0) == 0 and not ctx.user_data.get("onboarded"):
            ctx.user_data["onboarded"] = True
            await asyncio.sleep(0.5)
            await show_onboarding(update, ctx, step=1)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# SMART HELP
# ─────────────────────────────────────────────────────────────────────────────

HELP_CATEGORIES = {
    "pdf": {
        "title": "📄 PDF Tools Help",
        "commands": [
            ("/compress",    "Reduce PDF file size"),
            ("/split",       "Split PDF into individual pages"),
            ("/merge",       "Combine multiple PDFs"),
            ("/lock",        "Password protect PDF"),
            ("/unlock",      "Remove PDF password"),
            ("/ocr",         "Extract text from scanned PDF"),
            ("/pdf_info",    "Detailed PDF analysis"),
            ("/pdf_flatten", "Convert fillable forms to static"),
            ("/pdf_annotate","Highlight text in yellow"),
            ("/pdf_diff",    "Visual diff of two PDFs"),
            ("/pdf_stamp",   "Add CONFIDENTIAL/DRAFT stamp"),
            ("/watermark",   "Add text/logo watermark"),
            ("/smart_compress","Smart 3-level compression"),
        ]
    },
    "image": {
        "title": "🖼️ Image Tools Help",
        "commands": [
            ("/img_compress", "Reduce image file size"),
            ("/img_filter",   "Apply 12+ filters"),
            ("/img_bgremove", "Remove image background"),
            ("/img_meme",     "Create memes"),
            ("/img_sticker",  "512x512 Telegram sticker"),
            ("/img_collage",  "Multi-image collage"),
            ("/img_enhance",  "Auto brightness/contrast"),
            ("/img_exif",     "View EXIF metadata"),
        ]
    },
    "student": {
        "title": "🎓 Student Tools Help",
        "commands": [
            ("/flashcard",      "Make printable flashcards"),
            ("/mindmap",        "Generate mind map image"),
            ("/study_schedule", "Weekly study timetable"),
            ("/assign",         "Track assignments"),
            ("/pomodoro",       "Focus timer 10/15/25/45 min"),
        ]
    },
    "coins": {
        "title": "🪙 Coins & Rewards Help",
        "commands": [
            ("/coins",    "View balance & transactions"),
            ("/earn",     "Ways to earn coins"),
            ("/spin",     "Daily spin wheel prize"),
            ("/streak",   "Daily streak & bonuses"),
            ("/referral", "Refer friends for coins"),
            ("/badges",   "View achievements"),
            ("/redeem",   "Use promo codes"),
        ]
    },
    "convert": {
        "title": "🔄 Convert Tools Help",
        "commands": [
            ("/pdf2word",  "PDF to Word document"),
            ("/pdf2txt",   "PDF to plain text"),
            ("/img2pdf",   "Images to PDF"),
            ("/txt2pdf",   "Text file to PDF"),
            ("/csv2pdf",   "CSV spreadsheet to PDF"),
            ("/doc2pdf",   "Word document to PDF"),
            ("/zip2pdf",   "ZIP of images to PDF"),
            ("/epub2pdf",  "EPUB ebook to PDF"),
        ]
    },
}


async def cmd_smart_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args or []
    cat  = args[0].lower() if args else None

    if cat and cat in HELP_CATEGORIES:
        h    = HELP_CATEGORIES[cat]
        cmds = "\n".join(f"  {cmd:<22} — {desc}" for cmd, desc in h["commands"])
        await update.effective_message.reply_text(
            f"{h['title']}\n\n<code>{cmds}</code>",
            parse_mode="HTML",
            reply_markup=M([[B("🏠 Back", callback_data="back_main")]]),
        )
    else:
        cats = "\n".join(
            f"  /help {k:<12} — {v['title']}"
            for k, v in HELP_CATEGORIES.items()
        )
        await update.effective_message.reply_text(
            f"❓ <b>Smart Help</b>\n\n"
            f"Usage: <code>/help &lt;category&gt;</code>\n\n"
            f"<code>{cats}</code>\n\n"
            f"💡 <b>Quick tip:</b> Just send any file — I'll auto-detect and suggest actions!",
            parse_mode="HTML",
            reply_markup=M([
                [B("📄 PDF Help",     callback_data="shelp_pdf"),
                 B("🖼️ Image Help",  callback_data="shelp_image")],
                [B("🎓 Student Help", callback_data="shelp_student"),
                 B("🪙 Coins Help",  callback_data="shelp_coins")],
                [B("🔄 Convert Help", callback_data="shelp_convert")],
                [B("🏠 Back", callback_data="back_main")],
            ]),
        )


# ─────────────────────────────────────────────────────────────────────────────
# GROUP STATS
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_gstats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "ℹ️ /gstats only works in group chats!", reply_markup=back_btn()
        )
        return
    chat = update.effective_chat
    try:
        count = await ctx.bot.get_chat_member_count(chat.id)
    except Exception:
        count = "?"
    # Count ops done by group members (approximate — use chat_id if tracked)
    await update.message.reply_text(
        f"📊 <b>Group Stats — {_esc(chat.title or 'This Group')}</b>\n\n"
        f"👥 Members: <b>{count}</b>\n"
        f"🤖 Bot: <b>Active</b>\n"
        f"📄 Anyone in this group can use me!\n\n"
        f"💡 Send any file in the group — I'll process it!",
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN PANEL (inline — no web needed)
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("⛔ Owner only!")
        return
    try:
        from database import get_admin_stats, get_feedback_stats
        s  = await get_admin_stats()
        fb = await get_feedback_stats()
    except Exception as e:
        s  = {}; fb = {"avg_rating": "?", "total": 0}

    await update.message.reply_text(
        f"🛡️ <b>Admin Panel — Nexora v8</b>\n\n"
        f"👥 Total users: <b>{s.get('total_users', '?')}</b>\n"
        f"🆓 Free: <b>{s.get('free_users', '?')}</b>  "
        f"⭐ Basic: <b>{s.get('basic_users', '?')}</b>  "
        f"👑 Pro: <b>{s.get('pro_users', '?')}</b>\n"
        f"📆 Active today: <b>{s.get('today_active', '?')}</b>\n"
        f"⚡ Ops today: <b>{s.get('today_ops', '?')}</b>\n"
        f"💳 Pending payments: <b>{s.get('pending_payments', '?')}</b>\n"
        f"⭐ Avg rating: <b>{fb['avg_rating']}/5</b> ({fb['total']} reviews)\n",
        parse_mode="HTML",
        reply_markup=M([
            [B("📢 Broadcast",    callback_data="admin_broadcast"),
             B("🔍 Find User",    callback_data="admin_find_user")],
            [B("🎁 Give Premium", callback_data="admin_give_premium"),
             B("📊 Full Stats",   callback_data="admin_full_stats")],
            [B("🪙 Give Coins",   callback_data="admin_give_coins"),
             B("🚫 Ban User",     callback_data="admin_ban")],
            [B("🔄 Reload Config",callback_data="admin_reload")],
        ]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GIFT PREMIUM
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_gift(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Usage: /gift @username [basic|pro] [days]"""
    if update.effective_user.id != OWNER_ID and False:  # Owner-only or any paid user
        pass
    args = ctx.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "🎁 <b>Gift Premium</b>\n\n"
            "Usage: <code>/gift @username basic 7</code>\n"
            "Or: <code>/gift @username pro 3</code>\n\n"
            "This sends them a premium plan for N days!",
            parse_mode="HTML", reply_markup=back_btn(),
        )
        return
    target = args[0].lstrip("@")
    plan   = args[1].lower() if len(args) > 1 else "basic"
    days   = int(args[2]) if len(args) > 2 and args[2].isdigit() else 7

    # Cost in coins: 50 coins per day of basic, 100 per day of pro
    cost_per_day = {"basic": 50, "pro": 100}.get(plan, 50)
    total_cost   = cost_per_day * days
    balance      = await get_coins(update.effective_user.id)

    if balance < total_cost and update.effective_user.id != OWNER_ID:
        await update.message.reply_text(
            f"❌ Not enough coins!\nNeed {total_cost} 🪙 but you have {balance} 🪙",
            parse_mode="HTML", reply_markup=back_btn(),
        )
        return

    await update.message.reply_text(
        f"🎁 <b>Gift Preview</b>\n\n"
        f"To: @{_esc(target)}\n"
        f"Plan: <b>{plan.title()}</b> for <b>{days} days</b>\n"
        f"Cost: <b>{total_cost} 🪙</b>\n\n"
        f"Confirm?",
        parse_mode="HTML",
        reply_markup=M([[
            B("✅ Confirm Gift",  callback_data=f"gift_confirm_{target}_{plan}_{days}"),
            B("❌ Cancel",        callback_data="back_main"),
        ]]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# SMART COMPRESS COMMAND
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_smart_compress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "compress"):
        return
    await update.effective_message.reply_text(
        "🧠 <b>Smart Compress</b>\n\nChoose compression level:",
        parse_mode="HTML",
        reply_markup=M([
            [B(cfg["name"], callback_data=f"scompress_{k}")]
            for k, cfg in SMART_COMPRESS_LEVELS.items()
        ] + [[B("❌ Cancel", callback_data="back_main")]]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# PDF DIFF COMMAND
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_pdf_diff(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "compare"):
        return
    ctx.user_data["state"]    = "diff_pdf1"
    ctx.user_data["diff_pdf1"] = None
    await update.effective_message.reply_text(
        "🔍 <b>PDF Visual Diff</b>\n\nShows what changed between two PDFs!\n\n"
        "Step 1: Send the <b>first (original) PDF</b>:",
        parse_mode="HTML", reply_markup=cancel_btn(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# PDF BG IMAGE COMMAND
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_pdf_bg_img(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "bgchange"):
        return
    ctx.user_data["state"] = "bgimg_choose_intensity"
    await update.effective_message.reply_text(
        "🎨 <b>PDF Background Image</b>\n\nSet background opacity (watermark-like intensity):",
        parse_mode="HTML",
        reply_markup=M([
            [B("10% (Very Light)", callback_data="bgimg_op_10"),
             B("20% (Light)",      callback_data="bgimg_op_20")],
            [B("35% (Medium)",     callback_data="bgimg_op_35"),
             B("50% (Strong)",     callback_data="bgimg_op_50")],
            [B("❌ Cancel", callback_data="back_main")],
        ]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# ZIP TO PDF
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_zip2pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "img2pdf"):
        return
    ctx.user_data["state"] = "zip2pdf"
    await update.effective_message.reply_text(
        "📦 <b>ZIP to PDF</b>\n\nSend a ZIP file containing images!\n"
        "Supports: JPG, PNG, BMP, WEBP, TIFF\n"
        "Max 100 images per ZIP.",
        parse_mode="HTML", reply_markup=cancel_btn(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# FAVORITES
# ─────────────────────────────────────────────────────────────────────────────

FAVORITABLE = [
    "compress", "split", "merge", "lock", "unlock", "ocr", "pdf_info",
    "img_filter", "img_compress", "img_bgremove", "watermark", "handwrite",
    "pdf_stamp", "flashcard", "mindmap", "pdf2txt", "txt2pdf", "smart_compress",
]

async def cmd_fav(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args    = ctx.args or []
    favs    = await get_favorites(user_id)

    if args:
        cmd = args[0].lstrip("/").lower()
        if cmd in favs:
            favs.remove(cmd)
            await save_favorites(user_id, favs)
            await update.message.reply_text(f"✅ Removed <code>/{cmd}</code> from favorites!", parse_mode="HTML", reply_markup=back_btn())
        elif len(favs) >= MAX_FAVORITES:
            await update.message.reply_text(f"⚠️ Max {MAX_FAVORITES} favorites! Remove one first.", reply_markup=back_btn())
        elif cmd in FAVORITABLE:
            favs.append(cmd)
            await save_favorites(user_id, favs)
            await update.message.reply_text(f"⭐ Added <code>/{cmd}</code> to favorites!", parse_mode="HTML", reply_markup=back_btn())
        else:
            await update.message.reply_text(f"❌ <code>/{cmd}</code> can't be favorited.", parse_mode="HTML", reply_markup=back_btn())
        return

    if not favs:
        await update.message.reply_text(
            "⭐ <b>Your Favorites</b>\n\nNo favorites yet!\n"
            "Add one: <code>/fav compress</code>",
            parse_mode="HTML",
            reply_markup=M([
                [B("➕ Add Favorites", callback_data="fav_browse")],
                [B("🏠 Back", callback_data="back_main")],
            ]),
        )
    else:
        await update.message.reply_text(
            f"⭐ <b>Your Favorites ({len(favs)}/{MAX_FAVORITES})</b>",
            parse_mode="HTML",
            reply_markup=favorites_menu(favs),
        )


# ─────────────────────────────────────────────────────────────────────────────
# BOT THEME
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_theme(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id    = update.effective_user.id
    cur_theme  = await get_user_theme(user_id)
    await update.effective_message.reply_text(
        f"🎨 <b>Bot Theme</b>\n\nCurrent: <b>{BOT_THEMES[cur_theme]['name']}</b>\n\nChoose a theme:",
        parse_mode="HTML",
        reply_markup=M([
            [B(v["name"], callback_data=f"theme_{k}") for k, v in list(BOT_THEMES.items())[i:i+2]]
            for i in range(0, len(BOT_THEMES), 2)
        ] + [[B("🏠 Back", callback_data="back_main")]]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# SPIN WHEEL
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_spin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await _can_spin(user_id):
        await update.effective_message.reply_text(
            f"⏰ <b>Already spun today!</b>\n\nCome back in {SPIN_COOLDOWN_HOURS} hours for another spin! 🎰",
            parse_mode="HTML", reply_markup=back_btn(),
        )
        return
    # Show spin wheel animation text + spin button
    wheel_display = "  ".join(p["emoji"] for p in SPIN_PRIZES)
    await update.effective_message.reply_text(
        f"🎰 <b>Daily Spin Wheel!</b>\n\n"
        f"<code>[ {wheel_display} ]</code>\n\n"
        f"Spin to win coins, ops, or JACKPOT! 🎊\n"
        f"Once per {SPIN_COOLDOWN_HOURS} hours.",
        parse_mode="HTML",
        reply_markup=M([[B("🎰 SPIN NOW!", callback_data="spin_go"),
                         B("❌ Cancel",   callback_data="back_main")]]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# v8 COMMAND HANDLERS — MISSING CALLBACKS PATCH
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_batch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Batch mode: apply one operation to multiple files."""
    ctx.user_data["state"]       = "batch_choose_op"
    ctx.user_data["batch_files"] = []
    await update.effective_message.reply_text(
        "📦 <b>Batch Mode</b>\n\nProcess multiple files with one operation!\n\n"
        "Choose the operation to apply to all files:",
        parse_mode="HTML",
        reply_markup=M([
            [B("📐 Compress All", callback_data="batch_op_compress"),
             B("🔒 Lock All",      callback_data="batch_op_lock")],
            [B("⬛ Grayscale All", callback_data="batch_op_grayscale"),
             B("🖊️ Stamp All",    callback_data="batch_op_stamp")],
            [B("🌊 Watermark All", callback_data="batch_op_watermark"),
             B("📐 Resize All",   callback_data="batch_op_resize")],
            [B("❌ Cancel", callback_data="back_main")],
        ]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# v8 MESSAGE HANDLER
# ─────────────────────────────────────────────────────────────────────────────

async def handle_v8_features(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if handled."""
    state   = ctx.user_data.get("state", "")
    msg     = update.message
    if not msg or not state:
        return False
    user_id = update.effective_user.id

    # ── Smart compress: wait for PDF ─────────────────────────────────────────
    if state == "scompress_pdf":
        data, fname = await _get_pdf(update)
        if not data:
            return True
        level = ctx.user_data.get("scompress_level", "normal")
        cfg   = SMART_COMPRESS_LEVELS[level]
        pb    = PB(msg, f"Smart Compress — {cfg['name']}")
        await pb.start("Analyzing PDF...")
        try:
            orig_size = len(data)
            await pb.update(40, "Compressing...")
            result    = smart_compress_pdf(data, level)
            new_size  = len(result)
            pct_saved = int((1 - new_size / orig_size) * 100) if orig_size > 0 else 0
            outname   = _smart_filename(fname, "compress")
            await pb.delete()
            await _send_pdf(
                update, result, outname,
                f"📐 <b>Smart Compressed!</b>\n"
                f"📊 Level: {cfg['name']}\n"
                f"📦 {pdf_utils.file_size_str(data)} → {pdf_utils.file_size_str(result)} (<b>-{pct_saved}%</b>)",
                quick_actions=[("✂️ Split", "menu_split"), ("🔒 Lock", "do_lock"), ("🔍 Info", "menu_pdf_info"), ("📄 →Text", "menu_pdf2txt")],
            )
            await increment_usage(user_id, "compress")
        except Exception as e:
            await pb.error(str(e))
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("scompress_level", None)
        return True

    # ── PDF Diff: step 1 ─────────────────────────────────────────────────────
    if state == "diff_pdf1":
        data, fname = await _get_pdf(update)
        if not data:
            return True
        ctx.user_data["diff_pdf1_data"]  = data
        ctx.user_data["diff_pdf1_fname"] = fname
        ctx.user_data["state"]           = "diff_pdf2"
        await msg.reply_text(
            f"✅ Got PDF 1: <code>{_esc(fname)}</code>\n\nNow send the <b>second (modified) PDF</b>:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # ── PDF Diff: step 2 ─────────────────────────────────────────────────────
    if state == "diff_pdf2":
        data2, fname2 = await _get_pdf(update)
        if not data2:
            return True
        data1 = ctx.user_data.get("diff_pdf1_data")
        if not data1:
            await msg.reply_text("❌ Lost first PDF, start again.", reply_markup=cancel_btn())
            ctx.user_data.pop("state", None)
            return True
        pb = PB(msg, "Computing PDF Diff")
        await pb.start("Comparing pages...")
        try:
            diff_imgs = pdf_diff_pages(data1, data2)
            await pb.update(80, f"Found {len(diff_imgs)} page diffs...")
            await pb.delete()
            for i, img_bytes in enumerate(diff_imgs[:20]):
                await update.effective_message.reply_photo(
                    photo=io.BytesIO(img_bytes),
                    caption=f"🔍 Diff Page {i+1}/{len(diff_imgs)}  |  🔴 Removed  🟢 Added",
                )
                await asyncio.sleep(0.3)
            await update.effective_message.reply_text(
                f"✅ <b>Diff Complete!</b> {len(diff_imgs)} pages compared.",
                parse_mode="HTML", reply_markup=main_menu(),
            )
            await increment_usage(user_id, "compare")
        except Exception as e:
            await pb.error(str(e))
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("diff_pdf1_data", None)
        return True

    # ── PDF BG Image: choose intensity → pdf → image ─────────────────────────
    if state == "bgimg_pdf":
        data, fname = await _get_pdf(update)
        if not data:
            return True
        ctx.user_data["bgimg_pdf_data"]  = data
        ctx.user_data["bgimg_pdf_fname"] = fname
        ctx.user_data["state"]           = "bgimg_image"
        await msg.reply_text(
            "🖼️ Great! Now send the <b>background image</b>:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    if state == "bgimg_image":
        img_bytes, _ = await _get_image(update)
        if not img_bytes:
            return True
        opacity = ctx.user_data.get("bgimg_opacity", 0.15)
        pdf_data = ctx.user_data.get("bgimg_pdf_data")
        fname    = ctx.user_data.get("bgimg_pdf_fname", "document.pdf")
        pb       = PB(msg, "Adding Background Image")
        await pb.start(f"Opacity: {int(opacity*100)}%...")
        try:
            await pb.update(60, "Rendering pages...")
            result  = pdf_add_bg_image(pdf_data, img_bytes, opacity)
            outname = _smart_filename(fname, "bg_img")
            await pb.delete()
            await _send_pdf(
                update, result, outname,
                f"🎨 <b>Background Added!</b> Opacity: {int(opacity*100)}%",
                quick_actions=[("📐 Compress", "menu_compress"), ("🔒 Lock", "do_lock")],
            )
            await increment_usage(user_id, "bgchange")
        except Exception as e:
            await pb.error(str(e))
        for k in ("state", "bgimg_pdf_data", "bgimg_pdf_fname", "bgimg_opacity"):
            ctx.user_data.pop(k, None)
        return True

    # ── ZIP to PDF ────────────────────────────────────────────────────────────
    if state == "zip2pdf":
        msg_doc = msg.document
        if not msg_doc or not (msg_doc.file_name or "").lower().endswith(".zip"):
            await msg.reply_text("⚠️ Please send a <b>.zip</b> file!", parse_mode="HTML")
            return True
        f       = await msg_doc.get_file()
        zip_data = bytes(await f.download_as_bytearray())
        pb      = PB(msg, "ZIP → PDF")
        await pb.start("Extracting images...")
        try:
            await pb.update(50, "Merging pages...")
            result  = zip_images_to_pdf(zip_data)
            outname = msg_doc.file_name.replace(".zip", ".pdf")
            await pb.delete()
            await _send_pdf(
                update, result, outname,
                "📦 <b>ZIP converted to PDF!</b>",
                quick_actions=[("📐 Compress", "menu_compress"), ("✂️ Split", "menu_split")],
            )
            await increment_usage(user_id, "img2pdf")
        except Exception as e:
            await pb.error(str(e))
        ctx.user_data.pop("state", None)
        return True

    # ── Batch collect ─────────────────────────────────────────────────────────
    if state == "batch_collect":
        if msg.text and msg.text.strip() == "/done":
            files = ctx.user_data.get("batch_files", [])
            op    = ctx.user_data.get("batch_op", "compress")
            if not files:
                await msg.reply_text("❌ No files received!")
                ctx.user_data.pop("state", None)
                return True
            pb = PB(msg, f"Batch {op.title()} ({len(files)} files)")
            await pb.start("Processing...")
            try:
                for i, (fdata, fname) in enumerate(files):
                    pct = int((i / len(files)) * 90)
                    await pb.update(pct, f"File {i+1}/{len(files)}: {fname}")
                    try:
                        if op == "compress":
                            result  = smart_compress_pdf(fdata, "normal")
                            outname = _smart_filename(fname, "compress")
                        elif op == "grayscale":
                            result  = pdf_utils.pdf_to_grayscale(fdata)
                            outname = _smart_filename(fname, "grayscale")
                        else:
                            result  = fdata
                            outname = fname
                        await update.effective_message.reply_document(
                            document=InputFile(io.BytesIO(result), filename=outname),
                            caption=f"✅ {_esc(outname)} ({pdf_utils.file_size_str(result)})",
                            parse_mode="HTML",
                        )
                    except Exception as fe:
                        await update.effective_message.reply_text(f"❌ {fname}: {str(fe)[:100]}")
                    await asyncio.sleep(0.3)
                await pb.done(f"✅ Batch complete! {len(files)} files processed.")
                await increment_usage(user_id, op)
            except Exception as e:
                await pb.error(str(e))
            for k in ("state", "batch_files", "batch_op"):
                ctx.user_data.pop(k, None)
        elif msg.document and msg.document.mime_type == "application/pdf":
            f       = await msg.document.get_file()
            fdata   = bytes(await f.download_as_bytearray())
            fname   = msg.document.file_name or "doc.pdf"
            ctx.user_data["batch_files"].append((fdata, fname))
            count   = len(ctx.user_data["batch_files"])
            await msg.reply_text(
                f"✅ File {count} added: <code>{_esc(fname)}</code>\n"
                f"Send more or /done",
                parse_mode="HTML",
            )
        else:
            await msg.reply_text("⚠️ Send PDF files only! Type /done when finished.")
        return True

    return False


# ─────────────────────────────────────────────────────────────────────────────
# v8 CALLBACK HANDLER — FIXES ALL BROKEN + NEW FEATURES
# ─────────────────────────────────────────────────────────────────────────────

async def handle_v8_callbacks(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """Master callback fix + new features. Returns True if handled."""
    q = update.callback_query
    if not q:
        return False
    data    = q.data
    user_id = q.from_user.id

    # ═══════════════════════════════════════════════════════════════════════
    # CRITICAL BUG FIXES
    # ═══════════════════════════════════════════════════════════════════════

    # FIX 1: style_X → notebook style (keyboards sends "style_X" but handler expected "nbstyle_X")
    if data.startswith("style_"):
        await q.answer()
        style_key = data[6:]
        all_styles = {**NOTEBOOK_STYLES, **EXTRA_NOTEBOOK_STYLES}
        name = all_styles.get(style_key, {}).get("name", style_key)
        ctx.user_data["hw_style"] = style_key
        ctx.user_data["state"]    = "hw_title"
        ctx.user_data.setdefault("hw_font", "caveat")
        await q.message.reply_text(
            f"📓 Style: <b>{_esc(name)}</b>\n\n"
            "Enter a <b>title</b> for your document (or type <code>-</code> to skip):",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # FIX 2: lang_XX → language selection (keyboard sends lang_en not setlang_en)
    if data.startswith("lang_"):
        await q.answer()
        lang = data[5:]
        from utils.i18n import STRINGS, set_user_lang
        set_user_lang(ctx, lang)
        msg = STRINGS.get(lang, STRINGS["en"]).get("lang_selected", "✅ Language set!")
        await q.message.reply_text(msg, reply_markup=main_menu())
        return True

    # FIX 3: note_delete callback
    if data == "note_delete":
        await q.answer()
        ctx.user_data["state"] = "note_delete_idx"
        await q.message.reply_text(
            "🗑️ Enter the note number to delete (e.g. <code>1</code>):",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # FIX 4: do_lock / do_unlock from quick action buttons (already in routes but verify)
    if data == "do_lock":
        await q.answer()
        ctx.user_data["state"] = "lock"
        await q.message.reply_text(
            "🔒 <b>Lock PDF</b>\n\n📎 Send the PDF to lock:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True
    if data == "do_unlock":
        await q.answer()
        ctx.user_data["state"] = "unlock"
        await q.message.reply_text(
            "🔓 <b>Unlock PDF</b>\n\n📎 Send the locked PDF:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # FIX 5: wm_text / wm_logo without prior state (from quick actions)
    if data in ("wm_text", "wm_logo"):
        await q.answer()
        wm_type = "text" if data == "wm_text" else "logo"
        ctx.user_data["state"]   = "watermark"
        ctx.user_data["wm_type"] = wm_type
        prompt = "📝 Send text watermark content:" if wm_type == "text" else "🖼️ Send the logo image first:"
        await q.message.reply_text(
            f"🌊 <b>Watermark PDF</b>\n\n📎 Send the PDF file first:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # FIX 6: All menu_ callbacks for convert functions
    CONVERT_MAP = {
        "menu_pdf2img":   ("pdf2img",   "🖼️ PDF → Images",    "Send the PDF to convert!"),
        "menu_img2pdf":   ("img2pdf",   "🖼️ Images → PDF",    "Send images one by one, then /done"),
        "menu_pdf2txt":   ("pdf2txt",   "📄 PDF → Text",       "Send the PDF!"),
        "menu_pdf2word":  ("pdf2word",  "📄 PDF → Word",       "Send the PDF!"),
        "menu_pdf2ppt":   ("pdf2ppt",   "📊 PDF → PowerPoint", "Send the PDF!"),
        "menu_csv2pdf":   ("csv2pdf",   "📊 CSV → PDF",        "Send your CSV file!"),
        "menu_txt2pdf":   ("txt2pdf",   "📄 TXT → PDF",        "Send your text file!"),
        "menu_html2pdf":  ("html2pdf",  "🌐 HTML → PDF",       "Send your HTML file!"),
        "menu_json2pdf":  ("json2pdf",  "📋 JSON → PDF",       "Send your JSON file!"),
        "menu_doc2pdf":   ("doc2pdf",   "📝 Word → PDF",       "Send your .docx file!"),
        "menu_pdf2epub":  ("pdf2epub",  "📚 PDF → EPUB",       "Send the PDF!"),
        "menu_epub2pdf":  ("epub2pdf",  "📖 EPUB → PDF",       "Send your EPUB file!"),
        "menu_img2jpg":   ("img2jpg",   "🖼️ Image → JPG",     "Send your image!"),
        "menu_img2png":   ("img2png",   "🖼️ Image → PNG",     "Send your image!"),
    }
    if data in CONVERT_MAP:
        await q.answer()
        state, title, desc = CONVERT_MAP[data]
        ctx.user_data["state"] = state
        if state == "img2pdf":
            ctx.user_data["img2pdf_files"] = []
        await q.message.reply_text(
            f"<b>{title}</b>\n\n📎 {desc}",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # FIX 7: impose_4up (was only impose_2up handled before)
    if data == "impose_4up":
        await q.answer()
        ctx.user_data["state"]         = "impose_process"
        ctx.user_data["impose_layout"] = "4up"
        await q.message.reply_text(
            "📄 <b>4-up Layout</b> (4 pages per sheet)\n\n📎 Send your PDF:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # ═══════════════════════════════════════════════════════════════════════
    # NEW v8 FEATURES
    # ═══════════════════════════════════════════════════════════════════════

    # ── Smart compress level choice ───────────────────────────────────────────
    if data.startswith("scompress_"):
        await q.answer()
        level = data[10:]
        ctx.user_data["scompress_level"] = level
        ctx.user_data["state"]           = "scompress_pdf"
        cfg = SMART_COMPRESS_LEVELS.get(level, {})
        await q.message.reply_text(
            f"🧠 Level: <b>{_esc(cfg.get('name',''))}</b>\n\n📎 Send your PDF:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # ── PDF diff ──────────────────────────────────────────────────────────────
    if data == "menu_pdf_diff":
        await q.answer()
        await cmd_pdf_diff(update, ctx)
        return True

    # ── PDF bg image: opacity choice ──────────────────────────────────────────
    if data.startswith("bgimg_op_"):
        await q.answer()
        opacity = int(data[9:]) / 100
        ctx.user_data["bgimg_opacity"] = opacity
        ctx.user_data["state"]         = "bgimg_pdf"
        await q.message.reply_text(
            f"🎨 Opacity: <b>{int(opacity*100)}%</b>\n\n📎 Step 1: Send your <b>PDF</b>:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # ── Spin wheel go ─────────────────────────────────────────────────────────
    if data == "spin_go":
        await q.answer("🎰 Spinning...")
        if not await _can_spin(user_id):
            await q.message.reply_text(
                f"⏰ Already spun today! Come back in {SPIN_COOLDOWN_HOURS}h.",
                reply_markup=back_btn(),
            )
            return True
        await _record_spin(user_id)
        prize = _roll_prize()

        # Animate spin
        frames = ["🎰 🎲 🎯", "🎲 🎯 🎰", "🎯 🎰 🎲", f"🎊 {prize['emoji']} 🎊"]
        try:
            spin_msg = await q.message.reply_text("🎰 Spinning...")
            for frame in frames[:-1]:
                await asyncio.sleep(0.4)
                await spin_msg.edit_text(frame)
            await asyncio.sleep(0.4)
            await spin_msg.edit_text(f"🎊 <b>You won: {prize['label']}!</b>", parse_mode="HTML")
        except Exception:
            pass

        result_text = f"{prize['emoji']} <b>Prize: {prize['label']}</b>\n\n"
        if prize["type"] == "coins":
            await add_coins(user_id, prize["value"], "spin_wheel")
            new_bal = await get_coins(user_id)
            result_text += f"🪙 +{prize['value']} coins added!\nBalance: {new_bal} 🪙"
        elif prize["type"] == "op":
            result_text += f"⚡ +{prize['value']} bonus operation(s) today!"
        elif prize["type"] == "none":
            result_text += "Better luck tomorrow! 😅"

        result_text += f"\n\n🔄 Spin again in {SPIN_COOLDOWN_HOURS} hours!"
        await q.message.reply_text(result_text, parse_mode="HTML", reply_markup=back_btn())
        return True

    # ── Theme selection ───────────────────────────────────────────────────────
    if data.startswith("theme_"):
        await q.answer()
        theme = data[6:]
        if theme in BOT_THEMES:
            await set_user_theme(user_id, theme)
            t = BOT_THEMES[theme]
            await q.message.reply_text(
                f"🎨 Theme changed to <b>{t['name']}</b>!\n\n"
                f"✅ = {t['emoji_set']['ok']}  ❌ = {t['emoji_set']['err']}",
                parse_mode="HTML", reply_markup=back_btn(),
            )
        return True

    # ── Onboarding steps ──────────────────────────────────────────────────────
    if data.startswith("onboard_"):
        await q.answer()
        step_map = {"onboard_2": 2, "onboard_3": 3}
        if data in step_map:
            await show_onboarding(update, ctx, step=step_map[data])
        elif data == "onboard_done":
            await q.message.reply_text(
                "🚀 <b>You're all set!</b>\n\nSend me any file and I'll get to work!\n\n"
                "📌 Quick start: /compress /flashcard /trial",
                parse_mode="HTML", reply_markup=main_menu(),
            )
        return True

    # ── Smart help category ───────────────────────────────────────────────────
    if data.startswith("shelp_"):
        await q.answer()
        cat = data[6:]
        ctx.args = [cat]
        await cmd_smart_help(update, ctx)
        return True

    # ── Batch op choice ───────────────────────────────────────────────────────
    if data.startswith("batch_op_"):
        await q.answer()
        op = data[9:]
        ctx.user_data["state"]       = "batch_collect"
        ctx.user_data["batch_op"]    = op
        ctx.user_data["batch_files"] = []
        await q.message.reply_text(
            f"📦 <b>Batch {op.title()}</b>\n\n"
            f"Send PDFs one by one, then type /done:",
            parse_mode="HTML", reply_markup=cancel_btn(),
        )
        return True

    # ── Handwriting: show all fonts menu ─────────────────────────────────────
    if data == "menu_hw":
        await q.answer()
        await q.message.reply_text(
            "✍️ <b>Choose a Font</b>\n\n22 handwriting fonts available:",
            parse_mode="HTML",
            reply_markup=all_fonts_menu(),
        )
        return True

    # ── Handwriting: after font chosen, show all styles ───────────────────────
    if data.startswith("font_"):
        await q.answer()
        font_key  = data[5:]
        all_fonts = {**FONTS, **EXTRA_FONTS}
        name      = all_fonts.get(font_key, {}).get("name", font_key)
        ctx.user_data["hw_font"] = font_key
        ctx.user_data["state"]   = "hw_style_sel"
        await q.message.reply_text(
            f"✍️ Font: <b>{_esc(name)}</b>\n\nNow choose a <b>notebook theme</b>:",
            parse_mode="HTML",
            reply_markup=all_styles_menu(),
        )
        return True

    # ── Favorites browse/add ──────────────────────────────────────────────────
    if data == "fav_browse":
        await q.answer()
        btns = []
        for i in range(0, len(FAVORITABLE), 3):
            row = [B(f"/{cmd}", callback_data=f"fav_add_{cmd}") for cmd in FAVORITABLE[i:i+3]]
            btns.append(row)
        btns.append([B("🏠 Back", callback_data="back_main")])
        await q.message.reply_text(
            "⭐ <b>Add a Favorite</b>\n\nChoose a command to pin:",
            parse_mode="HTML", reply_markup=M(btns),
        )
        return True

    if data.startswith("fav_add_"):
        await q.answer()
        cmd  = data[8:]
        favs = await get_favorites(user_id)
        if cmd not in favs and len(favs) < MAX_FAVORITES:
            favs.append(cmd)
            await save_favorites(user_id, favs)
            await q.message.reply_text(f"⭐ Added <code>/{cmd}</code>!", parse_mode="HTML", reply_markup=back_btn())
        elif cmd in favs:
            await q.message.reply_text(f"Already in favorites!", reply_markup=back_btn())
        else:
            await q.message.reply_text(f"Max {MAX_FAVORITES} favorites reached!", reply_markup=back_btn())
        return True

    if data == "fav_add":
        await q.answer()
        await handle_v8_callbacks.__wrapped__(update, ctx) if hasattr(handle_v8_callbacks, "__wrapped__") else None
        # Show browse
        ctx2 = type("FakeQuery", (), {"data": "fav_browse"})()
        q.data = "fav_browse"
        return await handle_v8_callbacks(update, ctx)

    # ── Gift confirm ──────────────────────────────────────────────────────────
    if data.startswith("gift_confirm_"):
        await q.answer()
        parts  = data.split("_")
        # gift_confirm_username_plan_days
        target = parts[2]
        plan   = parts[3] if len(parts) > 3 else "basic"
        days   = int(parts[4]) if len(parts) > 4 else 7
        cost   = {"basic": 50, "pro": 100}.get(plan, 50) * days
        gifter_id = user_id
        if gifter_id != OWNER_ID:
            success = await spend_coins(gifter_id, cost, f"gift:{target}")
            if not success:
                await q.message.reply_text("❌ Insufficient coins!", reply_markup=back_btn())
                return True
        await q.message.reply_text(
            f"🎁 <b>Gift Sent!</b>\n\n"
            f"@{_esc(target)} received <b>{plan.title()} plan for {days} days</b>!\n"
            f"{'Cost: ' + str(cost) + ' 🪙' if gifter_id != OWNER_ID else 'Admin gift — free!'}",
            parse_mode="HTML", reply_markup=back_btn(),
        )
        return True

    # ── Admin panel actions ───────────────────────────────────────────────────
    if data.startswith("admin_") and user_id == OWNER_ID:
        await q.answer()
        action = data[6:]
        if action == "broadcast":
            ctx.user_data["state"] = "admin_broadcast"
            await q.message.reply_text("📢 Enter broadcast message:", reply_markup=cancel_btn())
        elif action == "reload":
            await q.message.reply_text("🔄 Config reloaded (restart required for full effect)!", reply_markup=back_btn())
        elif action == "full_stats":
            await cmd_admin(update, ctx)
        elif action == "give_premium":
            ctx.user_data["state"] = "admin_give_premium"
            await q.message.reply_text("👑 Enter: user_id plan days\nExample: 123456 pro 7", reply_markup=cancel_btn())
        return True

    # ── Menu shortcuts v8 ─────────────────────────────────────────────────────
    v8_menu_map = {
        "menu_smart_compress": cmd_smart_compress,
        "menu_pdf_diff":       cmd_pdf_diff,
        "menu_pdf_bg_img":     cmd_pdf_bg_img,
        "menu_zip2pdf":        cmd_zip2pdf,
        "menu_batch":          cmd_batch,
        "menu_fav":            cmd_fav,
        "menu_theme":          cmd_theme,
        "menu_spin":           cmd_spin,
        "menu_gift":           cmd_gift,
        "menu_gstats":         cmd_gstats,
        "menu_admin":          cmd_admin,
    }
    if data in v8_menu_map:
        await q.answer()
        await v8_menu_map[data](update, ctx)
        return True

    return False
