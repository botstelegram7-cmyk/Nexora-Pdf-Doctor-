"""
New Features Handler v5.0
All new commands for Nexora PDF Doctor Bot
"""
import io, asyncio, html, gc, re, datetime
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from utils.keyboards import main_menu, back_btn, cancel_btn
from utils import pdf_utils
from utils.cache import delete_buttons_later
from config import DELETE_BUTTONS_AFTER_SEC, IMAGE_FILTERS
from database import (
    check_feature_limit, increment_usage, get_plan,
    save_note, get_notes,
    save_file_history, get_file_history,
    save_reminder, ensure_user,
)


def _esc(text: str) -> str:
    return html.escape(str(text))


async def _err(update, text: str):
    await update.effective_message.reply_text(
        f"❌ <b>Error:</b> {_esc(text[:300])}", parse_mode="HTML", reply_markup=back_btn()
    )


async def _send_pdf(update, data: bytes, filename: str, caption: str = ""):
    size = pdf_utils.file_size_str(data)
    cap  = caption or f"✅ Done! <b>({size})</b>"
    sent = await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap, parse_mode="HTML", reply_markup=main_menu()
    )
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    del data; gc.collect()
    return sent


async def _send_file(update, data: bytes, filename: str, caption: str = ""):
    size = pdf_utils.file_size_str(data)
    cap  = caption or f"✅ Done! <b>({size})</b>"
    sent = await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap, parse_mode="HTML", reply_markup=main_menu()
    )
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    del data; gc.collect()
    return sent


async def _send_photo(update, data: bytes, caption: str = ""):
    sent = await update.effective_message.reply_photo(
        photo=io.BytesIO(data), caption=caption, parse_mode="HTML",
        reply_markup=main_menu()
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


async def _check_limit(update, ctx, feature: str) -> bool:
    user_id = update.effective_user.id
    ok, reason = await check_feature_limit(user_id, feature)
    if not ok:
        await update.effective_message.reply_text(reason, parse_mode="HTML", reply_markup=back_btn())
    return ok


# =============================================================================
# COMMAND ENTRY POINTS
# =============================================================================

async def cmd_pdf2txt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "pdf2txt"):
        return
    ctx.user_data["state"] = "pdf2txt"
    await update.effective_message.reply_text(
        "📄 <b>PDF to Text</b>\n\nSend me a PDF and I'll extract all text as a .txt file!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_linearize(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "linearize"):
        return
    ctx.user_data["state"] = "linearize"
    await update.effective_message.reply_text(
        "🌐 <b>Linearize PDF</b>\n\nOptimizes PDF for fast web viewing!\nSend your PDF:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_thumbnail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "thumbnail"):
        return
    ctx.user_data["state"] = "thumbnail"
    await update.effective_message.reply_text(
        "🖼️ <b>PDF Thumbnail</b>\n\nSend a PDF and I'll show a preview of the first page!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_pdf_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "pdf_info"):
        return
    ctx.user_data["state"] = "pdf_info"
    await update.effective_message.reply_text(
        "🔍 <b>Deep PDF Analysis</b>\n\nSend a PDF for a full report: pages, fonts, images, words & more!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_redact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "redact"):
        return
    ctx.user_data["state"] = "redact_pdf"
    await update.effective_message.reply_text(
        "⬛ <b>Redact / Censor Text</b>\n\nSend me a PDF first!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_impose(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "impose"):
        return
    from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as Mk
    kb = Mk([
        [B("📄 2-up (2 pages/sheet)", callback_data="impose_2up"),
         B("📄 4-up (4 pages/sheet)", callback_data="impose_4up")],
        [B("🏠 Back", callback_data="back_main")]
    ])
    await update.effective_message.reply_text(
        "📋 <b>Page Imposition</b>\n\nPrint multiple pages on one sheet! Choose layout:",
        parse_mode="HTML", reply_markup=kb
    )


async def cmd_deskew(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "deskew"):
        return
    ctx.user_data["state"] = "deskew"
    await update.effective_message.reply_text(
        "📐 <b>Deskew PDF</b>\n\nFix crooked/tilted scanned pages!\nSend your PDF:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_pwd_strength(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["state"] = "pwd_strength"
    await update.effective_message.reply_text(
        "🔐 <b>Password Strength Checker</b>\n\nSend me a password to analyze its strength!\n\n"
        "⚠️ <i>Tip: Don't send your real important passwords here. Use test passwords only.</i>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_pwd_crack(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "pwd_crack"):
        return
    ctx.user_data["state"] = "pwd_crack"
    await update.effective_message.reply_text(
        "🔓 <b>PDF Password Cracker</b> 👑 <i>Pro Feature</i>\n\n"
        "⚠️ <b>Disclaimer:</b> Only works on very weak/simple passwords.\n"
        "Tries: common word list + numeric combos up to 6 digits.\n\n"
        "📤 Send your locked PDF:\n"
        "⏱️ <i>Max timeout: 60 seconds</i>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_metadata_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "metadata_edit"):
        return
    ctx.user_data["state"] = "meta_edit_pdf"
    await update.effective_message.reply_text(
        "✏️ <b>Edit PDF Metadata</b>\n\nSend the PDF you want to edit!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_img_compress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "img_compress"):
        return
    ctx.user_data["state"] = "img_compress"
    await update.effective_message.reply_text(
        "📦 <b>Image Compressor</b>\n\nSend an image to compress it!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_img_resize(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "img_resize"):
        return
    ctx.user_data["state"] = "img_resize"
    await update.effective_message.reply_text(
        "📏 <b>Image Resize</b>\n\nSend an image first!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_img_crop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "img_crop"):
        return
    ctx.user_data["state"] = "img_crop"
    await update.effective_message.reply_text(
        "✂️ <b>Image Crop</b>\n\nSend an image first!\n"
        "Then enter: <code>left top right bottom</code> (pixels)\n"
        "Example: <code>50 50 400 300</code>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_img_filter(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "img_filter"):
        return
    ctx.user_data["state"] = "img_filter"
    await update.effective_message.reply_text(
        "🎨 <b>Image Filters</b>\n\nSend an image and then choose a filter!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_img_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "img_text"):
        return
    ctx.user_data["state"] = "img_text"
    await update.effective_message.reply_text(
        "📝 <b>Text on Image</b>\n\nSend an image and I'll add custom text on it!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_img2jpg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "img2jpg"):
        return
    ctx.user_data["state"] = "img2jpg"
    await update.effective_message.reply_text(
        "🖼️ <b>Convert to JPG</b>\n\nSend any image (PNG, WEBP, BMP...) to convert!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_img2png(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "img2png"):
        return
    ctx.user_data["state"] = "img2png"
    await update.effective_message.reply_text(
        "🖼️ <b>Convert to PNG</b>\n\nSend any image to convert to PNG!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_img_bgremove(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "img_bgremove"):
        return
    ctx.user_data["state"] = "img_bgremove"
    await update.effective_message.reply_text(
        "✂️ <b>Background Remover</b> ⭐ <i>Basic+ Feature</i>\n\n"
        "Send an image and I'll remove the background!\n"
        "🤖 <i>Local AI model — no internet needed!</i>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_csv2pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "csv2pdf"):
        return
    ctx.user_data["state"] = "csv2pdf"
    await update.effective_message.reply_text(
        "📊 <b>CSV to PDF Table</b>\n\nSend a .csv file!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_txt2pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "txt2pdf"):
        return
    ctx.user_data["state"] = "txt2pdf"
    await update.effective_message.reply_text(
        "📄 <b>Text to PDF</b>\n\nSend a .txt file!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_html2pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "html2pdf"):
        return
    ctx.user_data["state"] = "html2pdf"
    await update.effective_message.reply_text(
        "🌐 <b>HTML to PDF</b>\n\nSend an .html file!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_json2pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "json2pdf"):
        return
    ctx.user_data["state"] = "json2pdf"
    await update.effective_message.reply_text(
        "📋 <b>JSON to PDF Report</b>\n\nSend a .json file!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_doc2pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "doc2pdf"):
        return
    ctx.user_data["state"] = "doc2pdf"
    await update.effective_message.reply_text(
        "📝 <b>Word to PDF</b>\n\nSend a .docx file!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_pdf2epub(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "pdf2epub"):
        return
    ctx.user_data["state"] = "pdf2epub"
    await update.effective_message.reply_text(
        "📚 <b>PDF to EPUB</b> ⭐ <i>Basic+ Feature</i>\n\nSend a PDF!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_epub2pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "epub2pdf"):
        return
    ctx.user_data["state"] = "epub2pdf"
    await update.effective_message.reply_text(
        "📖 <b>EPUB to PDF</b>\n\nSend an .epub file!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_hash(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "hash"):
        return
    ctx.user_data["state"] = "hash"
    await update.effective_message.reply_text(
        "🔒 <b>File Hash Checker</b>\n\nSend any file — I'll give MD5, SHA1 & SHA256!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_steganography(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "steganography"):
        return
    from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as Mk
    kb = Mk([
        [B("🙈 Hide a Message", callback_data="steg_hide"),
         B("👁️ Reveal Message", callback_data="steg_reveal")],
        [B("🏠 Back", callback_data="back_main")]
    ])
    await update.effective_message.reply_text(
        "🕵️ <b>Steganography</b>\n\nHide or reveal secret messages inside images!",
        parse_mode="HTML", reply_markup=kb
    )


async def cmd_pdf_sign(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "pdf_sign"):
        return
    ctx.user_data["state"] = "pdf_sign_pdf"
    await update.effective_message.reply_text(
        "✍️ <b>Digital Signature</b>\n\nStep 1: Send the PDF you want to sign!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_poster(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "poster"):
        return
    from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as Mk
    kb = Mk([
        [B("🌙 Dark",     callback_data="poster_dark"),
         B("☀️ Light",    callback_data="poster_light")],
        [B("🔴 Red",      callback_data="poster_red"),
         B("🟢 Green",    callback_data="poster_green")],
        [B("🌈 Gradient", callback_data="poster_gradient")],
        [B("🏠 Back",     callback_data="back_main")],
    ])
    await update.effective_message.reply_text(
        "🎨 <b>Poster Generator</b>\n\nChoose a theme:",
        parse_mode="HTML", reply_markup=kb
    )


async def cmd_calendar_pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "calendar_pdf"):
        return
    now = datetime.date.today()
    prog = await update.effective_message.reply_text("⏳ Generating calendar...")
    try:
        data = pdf_utils.create_calendar_pdf(now.year, now.month)
        await _send_pdf(update, data,
                        f"Calendar_{now.strftime('%B_%Y')}.pdf",
                        f"📅 <b>{now.strftime('%B %Y')} Calendar ready!</b>")
        await increment_usage(update.effective_user.id, "calendar_pdf")
    except Exception as e:
        await _err(update, str(e))
    finally:
        try:
            await prog.delete()
        except Exception:
            pass


async def cmd_invoice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "invoice"):
        return
    ctx.user_data["state"] = "invoice_name"
    ctx.user_data["invoice_items"] = []
    await update.effective_message.reply_text(
        "🧾 <b>Invoice Generator</b>\n\nStep 1: Enter client name:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_resume(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "resume"):
        return
    ctx.user_data["state"] = "resume_name"
    ctx.user_data["resume_data"] = {}
    await update.effective_message.reply_text(
        "📋 <b>Resume Builder</b>\n\nStep 1: What is your full name?",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_certificate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "certificate"):
        return
    ctx.user_data["state"] = "cert_name"
    await update.effective_message.reply_text(
        "🏆 <b>Certificate Generator</b>\n\nStep 1: Enter recipient's name:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_zip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "zip"):
        return
    ctx.user_data["state"] = "zip_collect"
    ctx.user_data["zip_files"] = []
    await update.effective_message.reply_text(
        "📦 <b>Create ZIP Archive</b>\n\n"
        "Send me files one by one.\nWhen done, send /done",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_unzip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "unzip"):
        return
    ctx.user_data["state"] = "unzip"
    await update.effective_message.reply_text(
        "📂 <b>Extract ZIP</b>\n\nSend a .zip file!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_fileinfo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "fileinfo"):
        return
    ctx.user_data["state"] = "fileinfo"
    await update.effective_message.reply_text(
        "ℹ️ <b>File Info</b>\n\nSend any file!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_qrcode_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "qrcode_scan"):
        return
    ctx.user_data["state"] = "qrcode_scan"
    await update.effective_message.reply_text(
        "📷 <b>QR Code Scanner</b>\n\nSend a QR code image!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_barcode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "barcode"):
        return
    ctx.user_data["state"] = "barcode"
    await update.effective_message.reply_text(
        "📊 <b>Barcode Generator</b>\n\nEnter text to encode in barcode:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )


async def cmd_remind(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "remind"):
        return
    await update.effective_message.reply_text(
        "⏰ <b>Set a Reminder</b>\n\n"
        "Usage: <code>/remind 30m Your message</code>\n\n"
        "Time formats:\n"
        "  <code>30m</code> = 30 minutes\n"
        "  <code>2h</code>  = 2 hours\n"
        "  <code>1d</code>  = 1 day\n\n"
        "Example: <code>/remind 1h Submit the report</code>",
        parse_mode="HTML", reply_markup=back_btn()
    )
    if ctx.args and len(ctx.args) >= 2:
        time_str = ctx.args[0].lower()
        message  = " ".join(ctx.args[1:])
        seconds  = 0
        m = re.match(r"(\d+)(m|h|d)", time_str)
        if m:
            val  = int(m.group(1))
            unit = m.group(2)
            if unit == "m":
                seconds = val * 60
            elif unit == "h":
                seconds = val * 3600
            elif unit == "d":
                seconds = val * 86400
        if seconds > 0:
            fire_at  = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            readable = f"{seconds//3600}h {(seconds%3600)//60}m" if seconds >= 3600 else f"{seconds//60}m"
            await save_reminder(update.effective_user.id, update.effective_chat.id, message, fire_at)
            await update.effective_message.reply_text(
                f"⏰ <b>Reminder set!</b>\n\n"
                f"📝 <i>{_esc(message)}</i>\n"
                f"⏱️ In: <b>{readable}</b>\n"
                f"🕐 At: <b>{fire_at.strftime('%H:%M, %d %b')}</b>",
                parse_mode="HTML", reply_markup=back_btn()
            )
            await increment_usage(update.effective_user.id, "remind")


async def cmd_notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "notes"):
        return
    from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as Mk
    kb = Mk([
        [B("📝 Add Note",   callback_data="note_add"),
         B("📋 View Notes", callback_data="note_view")],
        [B("🏠 Back", callback_data="back_main")]
    ])
    await update.effective_message.reply_text(
        "📒 <b>Personal Notes</b>\n\nSave and manage your notes!",
        parse_mode="HTML", reply_markup=kb
    )


async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _check_limit(update, ctx, "history"):
        return
    user_id = update.effective_user.id
    history = await get_file_history(user_id)
    if not history:
        await update.effective_message.reply_text(
            "📂 <b>File History</b>\n\nNo files processed yet!",
            parse_mode="HTML", reply_markup=back_btn()
        )
        return
    icons = {
        "compress": "📐", "split": "✂️", "merge": "🔗", "ocr": "👁️",
        "pdf2img": "🖼️", "img2pdf": "🖼️", "pdf2word": "📄",
        "excel": "📊", "handwrite": "✍️"
    }
    text = "📂 <b>Your Recent Files (Last 10)</b>\n\n"
    for i, h in enumerate(history, 1):
        icon  = icons.get(h.get("feature", ""), "📄")
        fname = _esc(h.get("filename", "unknown"))
        feat  = h.get("feature", "").title()
        size  = h.get("size_str", "")
        date  = str(h.get("created_at", ""))[:16]
        text += f"{i}. {icon} <b>{fname}</b>\n   🛠 {feat} • 📦 {size} • 🕐 {date}\n\n"
    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())


# =============================================================================
# MAIN MESSAGE HANDLER
# =============================================================================

async def handle_new_features(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if handled, False to pass to original handler."""
    state = ctx.user_data.get("state", "")
    msg   = update.message
    if not msg or not state:
        return False

    user_id = update.effective_user.id

    # ── PDF2TXT ──────────────────────────────────────────────────────────────
    if state == "pdf2txt":
        data = await _get_pdf(update)
        if not data:
            return True
        prog = await msg.reply_text("⏳ Extracting text...")
        try:
            text = pdf_utils.pdf_to_txt(data)
            await _send_file(update, text.encode("utf-8"), "extracted_text.txt",
                             f"📄 <b>Text extracted!</b> {len(text.split())} words")
            await increment_usage(user_id, "pdf2txt")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── LINEARIZE ────────────────────────────────────────────────────────────
    if state == "linearize":
        data = await _get_pdf(update)
        if not data:
            return True
        prog = await msg.reply_text("⏳ Optimizing...")
        try:
            result = pdf_utils.linearize_pdf(data)
            await _send_pdf(update, result, "web_optimized.pdf",
                            f"🌐 <b>Optimized!</b> {pdf_utils.file_size_str(data)} → {pdf_utils.file_size_str(result)}")
            await increment_usage(user_id, "linearize")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── THUMBNAIL ────────────────────────────────────────────────────────────
    if state == "thumbnail":
        data = await _get_pdf(update)
        if not data:
            return True
        prog = await msg.reply_text("⏳ Generating preview...")
        try:
            thumb = pdf_utils.pdf_thumbnail(data)
            await _send_photo(update, thumb, "🖼️ <b>PDF Preview (Page 1)</b>")
            await increment_usage(user_id, "thumbnail")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── PDF INFO ─────────────────────────────────────────────────────────────
    if state == "pdf_info":
        data = await _get_pdf(update)
        if not data:
            return True
        prog = await msg.reply_text("⏳ Analyzing PDF...")
        try:
            info     = pdf_utils.pdf_deep_info(data)
            enc      = "🔒 Yes" if info["encrypted"] else "🔓 No"
            fonts_str = ", ".join(info["font_list"]) if info["font_list"] else "—"
            text = (
                f"🔍 <b>Deep PDF Analysis</b>\n\n"
                f"📌 <b>Title:</b> {_esc(info['title'])}\n"
                f"👤 <b>Author:</b> {_esc(info['author'])}\n"
                f"📝 <b>Subject:</b> {_esc(info['subject'])}\n"
                f"🖥️ <b>Creator:</b> {_esc(info['creator'])}\n"
                f"⚙️ <b>Producer:</b> {_esc(info['producer'])}\n\n"
                f"━━━━━━━━━━━\n"
                f"📄 <b>Pages:</b> {info['pages']}\n"
                f"💾 <b>Size:</b> {info['size']}\n"
                f"🔐 <b>Encrypted:</b> {enc}\n"
                f"📋 <b>PDF Version:</b> {_esc(info['pdf_version'])}\n\n"
                f"━━━━━━━━━━━\n"
                f"🖼️ <b>Images:</b> {info['images']}\n"
                f"🔤 <b>Unique Fonts:</b> {info['fonts']}\n"
                f"📖 <b>Total Words:</b> {info['words']:,}\n"
                f"🔖 <b>Bookmarks:</b> {info['bookmarks']}\n"
                f"🔠 <b>Fonts:</b> <i>{_esc(fonts_str)}</i>\n\n"
                f"📅 <b>Created:</b> {_esc(info['created'])}\n"
                f"🔄 <b>Modified:</b> {_esc(info['modified'])}"
            )
            await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())
            await increment_usage(user_id, "pdf_info")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── REDACT STEP 1: get pdf ────────────────────────────────────────────────
    if state == "redact_pdf":
        data = await _get_pdf(update)
        if not data:
            return True
        ctx.user_data["redact_data"] = data
        ctx.user_data["state"]       = "redact_word"
        await msg.reply_text(
            "⬛ PDF received!\nNow enter the <b>word/phrase to redact</b>:",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # ── REDACT STEP 2: get word ───────────────────────────────────────────────
    if state == "redact_word":
        word = (msg.text or "").strip()
        if not word:
            await _err(update, "Enter a word to redact.")
            return True
        data = ctx.user_data.get("redact_data")
        if not data:
            await _err(update, "Session expired. Start again with /redact.")
            return True
        prog = await msg.reply_text(f"⏳ Redacting <b>{_esc(word)}</b>...", parse_mode="HTML")
        try:
            result, count = pdf_utils.redact_text(data, word)
            await _send_pdf(update, result, "redacted.pdf",
                            f"⬛ <b>Redacted!</b> Censored <b>{count}</b> occurrence(s) of \"{_esc(word)}\"")
            await increment_usage(user_id, "redact")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("redact_data", None)
        return True

    # ── IMPOSE ────────────────────────────────────────────────────────────────
    if state == "impose_process":
        data = await _get_pdf(update)
        if not data:
            return True
        layout = ctx.user_data.get("impose_layout", "2up")
        prog   = await msg.reply_text(f"⏳ Creating {layout} layout...")
        try:
            result = pdf_utils.impose_pdf(data, layout)
            await _send_pdf(update, result, f"imposed_{layout}.pdf",
                            f"📋 <b>{layout} layout done!</b>")
            await increment_usage(user_id, "impose")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("impose_layout", None)
        return True

    # ── DESKEW ────────────────────────────────────────────────────────────────
    if state == "deskew":
        data = await _get_pdf(update)
        if not data:
            return True
        prog = await msg.reply_text("⏳ Deskewing pages... please wait.")
        try:
            result = pdf_utils.deskew_pdf(data)
            await _send_pdf(update, result, "deskewed.pdf", "📐 <b>PDF deskewed!</b>")
            await increment_usage(user_id, "deskew")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── PASSWORD STRENGTH ─────────────────────────────────────────────────────
    if state == "pwd_strength":
        pwd = (msg.text or "").strip()
        if not pwd:
            await _err(update, "Please enter a password.")
            return True
        result   = pdf_utils.check_password_strength(pwd)
        tips_txt = "\n".join(f"  💡 {t}" for t in result["tips"]) or "  ✅ All checks passed!"
        issues   = "\n".join(f"  ⚠️ {i}" for i in result["issues"])
        text = (
            f"🔐 <b>Password Strength Report</b>\n\n"
            f"[{result['bar']}] {result['emoji']} <b>{result['level']}</b>\n\n"
            f"📊 <b>Analysis:</b>\n"
            f"  📏 Length: <b>{result['length']} chars</b>\n"
            f"  {'✅' if result['has_upper'] else '❌'} Uppercase\n"
            f"  {'✅' if result['has_lower'] else '❌'} Lowercase\n"
            f"  {'✅' if result['has_digit'] else '❌'} Numbers\n"
            f"  {'✅' if result['has_special'] else '❌'} Special chars\n\n"
        )
        if issues:
            text += f"🚨 <b>Issues:</b>\n{issues}\n\n"
        text += f"💡 <b>Tips:</b>\n{tips_txt}"
        await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())
        ctx.user_data.pop("state", None)
        return True

    # ── PASSWORD CRACK ────────────────────────────────────────────────────────
    if state == "pwd_crack":
        data = await _get_pdf(update)
        if not data:
            return True
        prog = await msg.reply_text(
            "🔓 <b>Cracking password...</b>\nTrying common words + numeric combos...\nPlease wait up to 60s!",
            parse_mode="HTML"
        )
        try:
            loop   = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, pdf_utils.crack_pdf_password, data)
            if result is None:
                await update.effective_message.reply_text(
                    "🔒 <b>Password not found</b>\n\nThe PDF uses a strong password.\n"
                    "💡 Use /unlock if you know the password.",
                    parse_mode="HTML", reply_markup=back_btn()
                )
            elif result == "":
                await update.effective_message.reply_text(
                    "✅ <b>This PDF is NOT password protected!</b>",
                    parse_mode="HTML", reply_markup=back_btn()
                )
            else:
                strength = pdf_utils.check_password_strength(result)
                await update.effective_message.reply_text(
                    f"🎉 <b>Password Found!</b>\n\n"
                    f"🔑 Password: <code>{_esc(result)}</code>\n"
                    f"📊 Strength: {strength['level']}\n\n"
                    f"💡 Use /unlock to decrypt with this password.",
                    parse_mode="HTML", reply_markup=back_btn()
                )
            await increment_usage(user_id, "pwd_crack")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── METADATA EDIT STEP 1 ──────────────────────────────────────────────────
    if state == "meta_edit_pdf":
        data = await _get_pdf(update)
        if not data:
            return True
        ctx.user_data["meta_edit_data"] = data
        ctx.user_data["state"]          = "meta_edit_fields"
        await msg.reply_text(
            "✏️ <b>Enter metadata to update:</b>\n\n"
            "Format (one per line):\n"
            "<code>title: My Title\nauthor: John Doe\nsubject: My Subject</code>",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # ── METADATA EDIT STEP 2 ──────────────────────────────────────────────────
    if state == "meta_edit_fields":
        fields = {}
        for line in (msg.text or "").split("\n"):
            if ":" in line:
                k, _, v = line.partition(":")
                k = k.strip().lower()
                v = v.strip()
                if k in ("title", "author", "subject") and v:
                    fields[k] = v
        if not fields:
            await _err(update, "No valid fields.\nUse:\ntitle: ...\nauthor: ...\nsubject: ...")
            return True
        data = ctx.user_data.get("meta_edit_data")
        prog = await msg.reply_text("⏳ Updating metadata...")
        try:
            result     = pdf_utils.edit_metadata(data, fields)
            fields_txt = "\n".join(f"  ✅ {k.title()}: <b>{_esc(v)}</b>" for k, v in fields.items())
            await _send_pdf(update, result, "updated_metadata.pdf",
                            f"📋 <b>Metadata updated!</b>\n\n{fields_txt}")
            await increment_usage(user_id, "metadata_edit")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("meta_edit_data", None)
        return True

    # ── IMAGE COMPRESS ────────────────────────────────────────────────────────
    if state == "img_compress":
        data = await _get_image(update)
        if not data:
            return True
        prog = await msg.reply_text("⏳ Compressing...")
        try:
            result  = pdf_utils.img_compress(data)
            saving  = round((1 - len(result) / len(data)) * 100, 1)
            await _send_file(update, result, "compressed.jpg",
                             f"📦 <b>Compressed!</b> {pdf_utils.file_size_str(data)} → {pdf_utils.file_size_str(result)} (saved {saving}%)")
            await increment_usage(user_id, "img_compress")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── IMAGE RESIZE STEP 1 ───────────────────────────────────────────────────
    if state == "img_resize":
        data = await _get_image(update)
        if not data:
            return True
        from PIL import Image as PILImage
        img = PILImage.open(io.BytesIO(data))
        ctx.user_data["img_resize_data"] = data
        ctx.user_data["state"]           = "img_resize_dims"
        await msg.reply_text(
            f"📏 Current: <b>{img.width}×{img.height}px</b>\n\n"
            "Enter new size: <code>width height</code>\nExample: <code>800 600</code>",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # ── IMAGE RESIZE STEP 2 ───────────────────────────────────────────────────
    if state == "img_resize_dims":
        parts = (msg.text or "").split()
        if len(parts) < 2:
            await _err(update, "Enter: width height\nExample: 800 600")
            return True
        try:
            w_new, h_new = int(parts[0]), int(parts[1])
        except ValueError:
            await _err(update, "Invalid numbers.")
            return True
        data = ctx.user_data.get("img_resize_data")
        prog = await msg.reply_text("⏳ Resizing...")
        try:
            result = pdf_utils.img_resize(data, w_new, h_new)
            await _send_file(update, result, "resized.png",
                             f"📏 <b>Resized to {w_new}×{h_new}px!</b>")
            await increment_usage(user_id, "img_resize")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("img_resize_data", None)
        return True

    # ── IMAGE CROP STEP 1 ─────────────────────────────────────────────────────
    if state == "img_crop":
        data = await _get_image(update)
        if not data:
            return True
        from PIL import Image as PILImage
        img = PILImage.open(io.BytesIO(data))
        ctx.user_data["img_crop_data"] = data
        ctx.user_data["state"]         = "img_crop_coords"
        await msg.reply_text(
            f"✂️ Size: <b>{img.width}×{img.height}px</b>\n\n"
            "Enter: <code>left top right bottom</code>\nExample: <code>50 50 400 300</code>",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # ── IMAGE CROP STEP 2 ─────────────────────────────────────────────────────
    if state == "img_crop_coords":
        parts = (msg.text or "").split()
        if len(parts) < 4:
            await _err(update, "Enter 4 numbers: left top right bottom")
            return True
        try:
            l, t, r, b = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
        except ValueError:
            await _err(update, "Invalid numbers.")
            return True
        data = ctx.user_data.get("img_crop_data")
        prog = await msg.reply_text("⏳ Cropping...")
        try:
            result = pdf_utils.img_crop(data, l, t, r, b)
            await _send_file(update, result, "cropped.png",
                             f"✂️ <b>Cropped!</b> Box: {l},{t},{r},{b}")
            await increment_usage(user_id, "img_crop")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("img_crop_data", None)
        return True

    # ── IMAGE FILTER STEP 1 ───────────────────────────────────────────────────
    if state == "img_filter":
        data = await _get_image(update)
        if not data:
            return True
        ctx.user_data["img_filter_data"] = data
        ctx.user_data["state"]           = "img_filter_choose"
        from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as Mk
        items = list(IMAGE_FILTERS.items())
        rows  = [[B(v, callback_data=f"imgf_{k}") for k, v in items[i:i+2]]
                 for i in range(0, len(items), 2)]
        rows.append([B("🏠 Back", callback_data="back_main")])
        await msg.reply_text("🎨 <b>Choose a filter:</b>", parse_mode="HTML", reply_markup=Mk(rows))
        return True

    # ── IMAGE TEXT STEP 1 ─────────────────────────────────────────────────────
    if state == "img_text":
        data = await _get_image(update)
        if not data:
            return True
        ctx.user_data["img_text_data"] = data
        ctx.user_data["state"]         = "img_text_input"
        await msg.reply_text(
            "📝 <b>Enter text to add:</b>\n\n"
            "Just text: <code>Hello World</code>\n"
            "With position: <code>top: Hello</code> or <code>bottom: Hello</code>",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # ── IMAGE TEXT STEP 2 ─────────────────────────────────────────────────────
    if state == "img_text_input":
        text_input = (msg.text or "").strip()
        if not text_input:
            await _err(update, "Enter some text.")
            return True
        position   = "center"
        if ":" in text_input:
            pos, _, rest = text_input.partition(":")
            if pos.strip() in ("center", "top", "bottom"):
                position   = pos.strip()
                text_input = rest.strip()
        data = ctx.user_data.get("img_text_data")
        prog = await msg.reply_text("⏳ Adding text...")
        try:
            result = pdf_utils.img_add_text(data, text_input, position=position)
            await _send_file(update, result, "text_overlay.jpg", "📝 <b>Text added!</b>")
            await increment_usage(user_id, "img_text")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("img_text_data", None)
        return True

    # ── IMG2JPG / IMG2PNG ─────────────────────────────────────────────────────
    if state in ("img2jpg", "img2png"):
        data = await _get_image(update)
        if not data:
            return True
        fmt  = "JPEG" if state == "img2jpg" else "PNG"
        ext  = "jpg"  if state == "img2jpg" else "png"
        prog = await msg.reply_text(f"⏳ Converting to {ext.upper()}...")
        try:
            result = pdf_utils.img_convert(data, fmt)
            await _send_file(update, result, f"converted.{ext}",
                             f"🖼️ <b>Converted to {ext.upper()}!</b>")
            await increment_usage(user_id, state)
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── IMG BG REMOVE ─────────────────────────────────────────────────────────
    if state == "img_bgremove":
        data = await _get_image(update)
        if not data:
            return True
        prog = await msg.reply_text("⏳ Removing background... (AI processing, 10-30s)")
        try:
            result = pdf_utils.img_remove_bg(data)
            await _send_file(update, result, "no_background.png", "✂️ <b>Background removed!</b>")
            await increment_usage(user_id, "img_bgremove")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── CSV2PDF ───────────────────────────────────────────────────────────────
    if state == "csv2pdf":
        if not msg.document:
            await _err(update, "Send a .csv file!")
            return True
        prog = await msg.reply_text("⏳ Converting CSV to PDF table...")
        try:
            f      = await msg.document.get_file()
            data   = bytes(await f.download_as_bytearray())
            result = pdf_utils.csv_to_pdf(data)
            await _send_pdf(update, result, "table.pdf", "📊 <b>CSV converted to PDF table!</b>")
            await increment_usage(user_id, "csv2pdf")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── TXT2PDF ───────────────────────────────────────────────────────────────
    if state == "txt2pdf":
        if not msg.document:
            await _err(update, "Send a .txt file!")
            return True
        prog = await msg.reply_text("⏳ Converting text to PDF...")
        try:
            f      = await msg.document.get_file()
            data   = bytes(await f.download_as_bytearray())
            result = pdf_utils.txt_to_pdf(data)
            await _send_pdf(update, result, "document.pdf", "📄 <b>Text converted to PDF!</b>")
            await increment_usage(user_id, "txt2pdf")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── HTML2PDF ──────────────────────────────────────────────────────────────
    if state == "html2pdf":
        if not msg.document:
            await _err(update, "Send an .html file!")
            return True
        prog = await msg.reply_text("⏳ Converting HTML to PDF...")
        try:
            f      = await msg.document.get_file()
            data   = bytes(await f.download_as_bytearray())
            result = pdf_utils.html_to_pdf(data.decode("utf-8", errors="replace"))
            await _send_pdf(update, result, "webpage.pdf", "🌐 <b>HTML converted to PDF!</b>")
            await increment_usage(user_id, "html2pdf")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── JSON2PDF ──────────────────────────────────────────────────────────────
    if state == "json2pdf":
        if not msg.document:
            await _err(update, "Send a .json file!")
            return True
        prog = await msg.reply_text("⏳ Generating JSON report PDF...")
        try:
            f      = await msg.document.get_file()
            data   = bytes(await f.download_as_bytearray())
            result = pdf_utils.json_to_pdf(data)
            await _send_pdf(update, result, "json_report.pdf", "📋 <b>JSON converted to PDF!</b>")
            await increment_usage(user_id, "json2pdf")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── DOC2PDF ───────────────────────────────────────────────────────────────
    if state == "doc2pdf":
        if not msg.document:
            await _err(update, "Send a .docx file!")
            return True
        prog = await msg.reply_text("⏳ Converting Word to PDF...")
        try:
            f      = await msg.document.get_file()
            data   = bytes(await f.download_as_bytearray())
            result = pdf_utils.doc_to_pdf(data)
            await _send_pdf(update, result, "converted.pdf", "📝 <b>Word doc converted to PDF!</b>")
            await increment_usage(user_id, "doc2pdf")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── PDF2EPUB ──────────────────────────────────────────────────────────────
    if state == "pdf2epub":
        data = await _get_pdf(update)
        if not data:
            return True
        prog = await msg.reply_text("⏳ Converting to EPUB...")
        try:
            result = pdf_utils.pdf_to_epub(data)
            await _send_file(update, result, "ebook.epub", "📚 <b>PDF converted to EPUB!</b>")
            await increment_usage(user_id, "pdf2epub")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── EPUB2PDF ──────────────────────────────────────────────────────────────
    if state == "epub2pdf":
        if not msg.document:
            await _err(update, "Send an .epub file!")
            return True
        prog = await msg.reply_text("⏳ Converting EPUB to PDF...")
        try:
            f      = await msg.document.get_file()
            data   = bytes(await f.download_as_bytearray())
            result = pdf_utils.epub_to_pdf(data)
            await _send_pdf(update, result, "converted.pdf", "📖 <b>EPUB converted to PDF!</b>")
            await increment_usage(user_id, "epub2pdf")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── HASH ──────────────────────────────────────────────────────────────────
    if state == "hash":
        if not (msg.document or msg.photo):
            await _err(update, "Send any file or image!")
            return True
        prog = await msg.reply_text("⏳ Computing hashes...")
        try:
            if msg.document:
                f        = await msg.document.get_file()
                data     = bytes(await f.download_as_bytearray())
                filename = msg.document.file_name or "file"
            else:
                f        = await msg.photo[-1].get_file()
                data     = bytes(await f.download_as_bytearray())
                filename = "photo.jpg"
            h    = pdf_utils.compute_hash(data)
            text = (
                f"🔒 <b>File Hash Report</b>\n\n"
                f"📄 <code>{_esc(filename)}</code>\n"
                f"💾 {h['size']} ({h['bytes']:,} bytes)\n\n"
                f"🔐 <b>MD5:</b>\n<code>{h['md5']}</code>\n\n"
                f"🔐 <b>SHA1:</b>\n<code>{h['sha1']}</code>\n\n"
                f"🔐 <b>SHA256:</b>\n<code>{h['sha256']}</code>"
            )
            await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())
            await increment_usage(user_id, "hash")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── STEG HIDE STEP 1: image ───────────────────────────────────────────────
    if state == "steg_hide_img":
        data = await _get_image(update)
        if not data:
            return True
        ctx.user_data["steg_img"] = data
        ctx.user_data["state"]    = "steg_hide_text"
        await msg.reply_text("🙈 Enter the <b>secret message</b> to hide:",
                             parse_mode="HTML", reply_markup=cancel_btn())
        return True

    # ── STEG HIDE STEP 2: text ────────────────────────────────────────────────
    if state == "steg_hide_text":
        secret = (msg.text or "").strip()
        if not secret:
            await _err(update, "Enter a message.")
            return True
        data = ctx.user_data.get("steg_img")
        prog = await msg.reply_text("⏳ Hiding message in image...")
        try:
            result = pdf_utils.steg_hide(data, secret)
            await _send_file(update, result, "secret_image.png",
                             "🙈 <b>Message hidden!</b>\nShare this image.\nRecipient can use /steganography → Reveal.")
            await increment_usage(user_id, "steganography")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("steg_img", None)
        return True

    # ── STEG REVEAL ───────────────────────────────────────────────────────────
    if state == "steg_reveal":
        data = await _get_image(update)
        if not data:
            return True
        prog = await msg.reply_text("⏳ Looking for hidden message...")
        try:
            secret = pdf_utils.steg_reveal(data)
            await update.effective_message.reply_text(
                f"👁️ <b>Hidden Message:</b>\n\n<i>{_esc(secret)}</i>",
                parse_mode="HTML", reply_markup=back_btn()
            )
            await increment_usage(user_id, "steganography")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── PDF SIGN STEP 1: pdf ──────────────────────────────────────────────────
    if state == "pdf_sign_pdf":
        data = await _get_pdf(update)
        if not data:
            return True
        ctx.user_data["sign_pdf"] = data
        ctx.user_data["state"]    = "pdf_sign_img"
        await msg.reply_text(
            "✍️ <b>Step 2:</b> Now send your <b>signature image</b> (PNG/JPG)!",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # ── PDF SIGN STEP 2: signature image ─────────────────────────────────────
    if state == "pdf_sign_img":
        sig_data = await _get_image(update)
        if not sig_data:
            return True
        data = ctx.user_data.get("sign_pdf")
        prog = await msg.reply_text("⏳ Adding signature...")
        try:
            result = pdf_utils.pdf_sign(data, sig_data)
            await _send_pdf(update, result, "signed.pdf", "✍️ <b>Signature added to PDF!</b>")
            await increment_usage(user_id, "pdf_sign")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("sign_pdf", None)
        return True

    # ── POSTER STEP: enter text ───────────────────────────────────────────────
    if state == "poster_input":
        text_input = (msg.text or "").strip()
        theme      = ctx.user_data.get("poster_theme", "dark")
        parts      = text_input.split("|")
        title_text = parts[0].strip()
        subtitle   = parts[1].strip() if len(parts) > 1 else ""
        if not title_text:
            await _err(update, "Enter a title.")
            return True
        prog = await msg.reply_text("⏳ Creating poster...")
        try:
            result = pdf_utils.create_poster(title_text, subtitle, theme)
            await _send_photo(update, result, "🎨 <b>Poster created!</b>")
            await increment_usage(user_id, "poster")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── INVOICE STEP 1: name ──────────────────────────────────────────────────
    if state == "invoice_name":
        ctx.user_data["invoice_name"] = (msg.text or "").strip()
        ctx.user_data["state"]        = "invoice_items"
        await msg.reply_text(
            "🧾 <b>Add items</b>\n\n"
            "Format: <code>Description, qty, price</code>\n"
            "Example: <code>Web Design, 1, 5000</code>\n\n"
            "Send one item per message.\nType <b>done</b> when finished.",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # ── INVOICE STEP 2: items ─────────────────────────────────────────────────
    if state == "invoice_items":
        text_input = (msg.text or "").strip()
        if text_input.lower() == "done":
            items = ctx.user_data.get("invoice_items", [])
            name  = ctx.user_data.get("invoice_name", "Client")
            if not items:
                await _err(update, "Add at least one item first!")
                return True
            prog = await msg.reply_text("⏳ Generating invoice...")
            try:
                result = pdf_utils.create_invoice(name, items)
                await _send_pdf(update, result, "invoice.pdf",
                                f"🧾 <b>Invoice ready for {_esc(name)}!</b> ({len(items)} items)")
                await increment_usage(user_id, "invoice")
            except Exception as e:
                await _err(update, str(e))
            finally:
                try:
                    await prog.delete()
                except Exception:
                    pass
            ctx.user_data.pop("state", None)
            ctx.user_data.pop("invoice_items", None)
            ctx.user_data.pop("invoice_name", None)
        else:
            parts = [p.strip() for p in text_input.split(",")]
            if len(parts) >= 3:
                try:
                    item = {"desc": parts[0], "qty": int(parts[1]), "price": float(parts[2])}
                    ctx.user_data.setdefault("invoice_items", []).append(item)
                    count = len(ctx.user_data.get("invoice_items", []))
                    await msg.reply_text(
                        f"✅ Item {count} added! Send more or type <b>done</b>.",
                        parse_mode="HTML"
                    )
                except ValueError:
                    await _err(update, "Format: Description, qty, price\nExample: Logo Design, 1, 2000")
            else:
                await _err(update, "Format: Description, qty, price")
        return True

    # ── RESUME STEPS ─────────────────────────────────────────────────────────
    if state == "resume_name":
        ctx.user_data["resume_data"]["name"] = (msg.text or "").strip()
        ctx.user_data["state"] = "resume_title"
        await msg.reply_text("📋 Your job title/profession:", reply_markup=cancel_btn())
        return True

    if state == "resume_title":
        ctx.user_data["resume_data"]["title"] = (msg.text or "").strip()
        ctx.user_data["state"] = "resume_email"
        await msg.reply_text("📋 Your email address:", reply_markup=cancel_btn())
        return True

    if state == "resume_email":
        ctx.user_data["resume_data"]["email"] = (msg.text or "").strip()
        ctx.user_data["state"] = "resume_phone"
        await msg.reply_text("📋 Your phone number:", reply_markup=cancel_btn())
        return True

    if state == "resume_phone":
        ctx.user_data["resume_data"]["phone"] = (msg.text or "").strip()
        ctx.user_data["state"] = "resume_summary"
        await msg.reply_text("📋 Brief summary (1-2 sentences about yourself):", reply_markup=cancel_btn())
        return True

    if state == "resume_summary":
        ctx.user_data["resume_data"]["summary"] = (msg.text or "").strip()
        ctx.user_data["state"] = "resume_skills"
        await msg.reply_text(
            "📋 Your skills (comma-separated):\nExample: Python, Excel, Photoshop",
            reply_markup=cancel_btn()
        )
        return True

    if state == "resume_skills":
        ctx.user_data["resume_data"]["skills"] = [s.strip() for s in (msg.text or "").split(",")]
        ctx.user_data["state"] = "resume_exp"
        await msg.reply_text(
            "📋 Work experience (one per line):\nFormat: Company — Role (Year)\nOr type <b>skip</b>",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    if state == "resume_exp":
        t = (msg.text or "").strip()
        if t.lower() != "skip":
            ctx.user_data["resume_data"]["experience"] = t.split("\n")
        ctx.user_data["state"] = "resume_edu"
        await msg.reply_text(
            "📋 Education (one per line):\nFormat: University — Degree (Year)\nOr type <b>skip</b>",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    if state == "resume_edu":
        t = (msg.text or "").strip()
        if t.lower() != "skip":
            ctx.user_data["resume_data"]["education"] = t.split("\n")
        prog = await msg.reply_text("⏳ Building your resume...")
        try:
            result = pdf_utils.create_resume(ctx.user_data["resume_data"])
            name   = ctx.user_data["resume_data"].get("name", "")
            await _send_pdf(update, result, "resume.pdf",
                            f"📋 <b>Resume ready for {_esc(name)}!</b>")
            await increment_usage(user_id, "resume")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("resume_data", None)
        return True

    # ── CERTIFICATE STEPS ─────────────────────────────────────────────────────
    if state == "cert_name":
        ctx.user_data["cert_name"] = (msg.text or "").strip()
        ctx.user_data["state"]     = "cert_course"
        await msg.reply_text("🏆 Enter the course/achievement name:", reply_markup=cancel_btn())
        return True

    if state == "cert_course":
        name   = ctx.user_data.get("cert_name", "")
        course = (msg.text or "").strip()
        prog   = await msg.reply_text("⏳ Generating certificate...")
        try:
            result = pdf_utils.create_certificate(name, course)
            await _send_pdf(update, result, "certificate.pdf",
                            f"🏆 <b>Certificate ready for {_esc(name)}!</b>")
            await increment_usage(user_id, "certificate")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("cert_name", None)
        return True

    # ── ZIP COLLECT ───────────────────────────────────────────────────────────
    if state == "zip_collect":
        if msg.document:
            f    = await msg.document.get_file()
            data = bytes(await f.download_as_bytearray())
            ctx.user_data.setdefault("zip_files", []).append((msg.document.file_name, data))
            count = len(ctx.user_data["zip_files"])
            await msg.reply_text(f"✅ File {count} added! Send more or /done")
        elif msg.text and msg.text.strip() == "/done":
            files = ctx.user_data.get("zip_files", [])
            if not files:
                await _err(update, "No files to zip!")
                return True
            prog = await msg.reply_text("⏳ Creating ZIP...")
            try:
                result = pdf_utils.create_zip(files)
                await _send_file(update, result, "archive.zip",
                                 f"📦 <b>ZIP created!</b> {len(files)} files packed")
                await increment_usage(user_id, "zip")
            except Exception as e:
                await _err(update, str(e))
            finally:
                try:
                    await prog.delete()
                except Exception:
                    pass
            ctx.user_data.pop("state", None)
            ctx.user_data.pop("zip_files", None)
        return True

    # ── UNZIP ─────────────────────────────────────────────────────────────────
    if state == "unzip":
        if not msg.document:
            await _err(update, "Send a .zip file!")
            return True
        prog = await msg.reply_text("⏳ Extracting ZIP...")
        try:
            f     = await msg.document.get_file()
            data  = bytes(await f.download_as_bytearray())
            files = pdf_utils.extract_zip(data)
            await msg.reply_text(f"📂 Found <b>{len(files)}</b> files. Sending...", parse_mode="HTML")
            for fname, fdata in files[:10]:
                await update.effective_message.reply_document(
                    document=InputFile(io.BytesIO(fdata), filename=fname),
                    caption=f"📄 {_esc(fname)} ({pdf_utils.file_size_str(fdata)})",
                    parse_mode="HTML"
                )
                await asyncio.sleep(0.5)
            await increment_usage(user_id, "unzip")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── FILE INFO ─────────────────────────────────────────────────────────────
    if state == "fileinfo":
        if not (msg.document or msg.photo):
            await _err(update, "Send any file or image!")
            return True
        prog = await msg.reply_text("⏳ Analyzing file...")
        try:
            if msg.document:
                f        = await msg.document.get_file()
                data     = bytes(await f.download_as_bytearray())
                filename = msg.document.file_name or "file"
            else:
                f        = await msg.photo[-1].get_file()
                data     = bytes(await f.download_as_bytearray())
                filename = "photo.jpg"
            info       = pdf_utils.get_file_info(data, filename)
            dims       = f"\n  📐 Dimensions: <b>{info.get('width')}×{info.get('height')}px</b>" if "width" in info else ""
            pages_info = f"\n  📄 Pages: <b>{info.get('pages')}</b>" if "pages" in info else ""
            text = (
                f"ℹ️ <b>File Information</b>\n\n"
                f"  📄 <code>{_esc(info['filename'])}</code>\n"
                f"  🏷️ Type: <b>{info['type']}</b> ({info['extension']})\n"
                f"  💾 Size: <b>{info['size']}</b> ({info['bytes']:,} bytes)\n"
                f"  🔐 MD5: <code>{info['md5']}</code>"
                f"{dims}{pages_info}"
            )
            await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())
            await increment_usage(user_id, "fileinfo")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── QR SCAN ───────────────────────────────────────────────────────────────
    if state == "qrcode_scan":
        data = await _get_image(update)
        if not data:
            return True
        prog = await msg.reply_text("⏳ Scanning QR code...")
        try:
            result = pdf_utils.scan_qr_code(data)
            await update.effective_message.reply_text(
                f"📷 <b>QR Code Decoded:</b>\n\n<code>{_esc(result)}</code>",
                parse_mode="HTML", reply_markup=back_btn()
            )
            await increment_usage(user_id, "qrcode_scan")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── BARCODE ───────────────────────────────────────────────────────────────
    if state == "barcode":
        text_input = (msg.text or "").strip()
        if not text_input:
            await _err(update, "Enter text for barcode.")
            return True
        prog = await msg.reply_text("⏳ Generating barcode...")
        try:
            result = pdf_utils.generate_barcode(text_input)
            await _send_file(update, result, "barcode.png",
                             f"📊 <b>Barcode generated!</b>\nData: <code>{_esc(text_input)}</code>")
            await increment_usage(user_id, "barcode")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        return True

    # ── NOTES ADD ─────────────────────────────────────────────────────────────
    if state == "note_add":
        text_input = (msg.text or "").strip()
        if not text_input:
            await _err(update, "Enter your note.")
            return True
        lines   = text_input.split("\n", 1)
        title   = lines[0][:50]
        content = lines[1] if len(lines) > 1 else lines[0]
        await save_note(user_id, title, content)
        await msg.reply_text(
            f"📝 <b>Note saved!</b>\n\n<b>{_esc(title)}</b>",
            parse_mode="HTML", reply_markup=back_btn()
        )
        await increment_usage(user_id, "notes")
        ctx.user_data.pop("state", None)
        return True

    return False


# =============================================================================
# CALLBACK HANDLER
# =============================================================================

async def handle_new_callbacks(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if handled."""
    q = update.callback_query
    if not q:
        return False
    data = q.data

    # ── Impose layout choice ──────────────────────────────────────────────────
    if data in ("impose_2up", "impose_4up"):
        await q.answer()
        layout = "2up" if data == "impose_2up" else "4up"
        ctx.user_data["state"]         = "impose_process"
        ctx.user_data["impose_layout"] = layout
        await q.message.reply_text(
            f"📋 <b>Layout: {layout}</b>\nNow send your PDF:",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # ── Image filter apply ────────────────────────────────────────────────────
    if data.startswith("imgf_"):
        await q.answer()
        filter_name = data[5:]
        img_data    = ctx.user_data.get("img_filter_data")
        if not img_data:
            await q.message.reply_text("⚠️ Session expired. Use /img_filter again.",
                                        reply_markup=back_btn())
            return True
        prog = await q.message.reply_text("⏳ Applying filter...")
        try:
            result       = pdf_utils.img_apply_filter(img_data, filter_name)
            filter_label = IMAGE_FILTERS.get(filter_name, filter_name)
            sent = await q.message.reply_document(
                document=InputFile(io.BytesIO(result), filename=f"{filter_name}.png"),
                caption=f"🎨 <b>Filter: {filter_label}</b>",
                parse_mode="HTML", reply_markup=main_menu()
            )
            asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
            await increment_usage(q.from_user.id, "img_filter")
        except Exception as e:
            await q.message.reply_text(f"❌ {str(e)[:200]}", reply_markup=back_btn())
        finally:
            try:
                await prog.delete()
            except Exception:
                pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("img_filter_data", None)
        return True

    # ── Steganography choices ─────────────────────────────────────────────────
    if data == "steg_hide":
        await q.answer()
        ctx.user_data["state"] = "steg_hide_img"
        await q.message.reply_text(
            "🙈 <b>Step 1:</b> Send the image to hide a message in:",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    if data == "steg_reveal":
        await q.answer()
        ctx.user_data["state"] = "steg_reveal"
        await q.message.reply_text(
            "👁️ Send the image to reveal the hidden message:",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # ── Poster theme ──────────────────────────────────────────────────────────
    if data.startswith("poster_"):
        await q.answer()
        theme = data.replace("poster_", "")
        ctx.user_data["state"]        = "poster_input"
        ctx.user_data["poster_theme"] = theme
        await q.message.reply_text(
            f"🎨 <b>Theme: {theme.title()}</b>\n\n"
            "Enter poster title:\n"
            "For subtitle too: <code>Title | Subtitle</code>",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # ── Notes callbacks ───────────────────────────────────────────────────────
    if data == "note_add":
        await q.answer()
        ctx.user_data["state"] = "note_add"
        await q.message.reply_text(
            "📝 <b>Add Note</b>\n\nFirst line = title, rest = content.\nType your note:",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    if data == "note_view":
        await q.answer()
        notes = await get_notes(q.from_user.id)
        if not notes:
            await q.message.reply_text("📒 No notes yet! Add one first.",
                                        reply_markup=back_btn())
            return True
        text = "📒 <b>Your Notes</b>\n\n"
        for i, n in enumerate(notes, 1):
            title   = _esc(n.get("title", "Note")[:40])
            content = _esc(n.get("content", "")[:80])
            date    = str(n.get("created_at", ""))[:10]
            text   += f"{i}. 📝 <b>{title}</b>\n   <i>{content}...</i>\n   🕐 {date}\n\n"
        await q.message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())
        return True

    # ── Menu shortcuts for new features ──────────────────────────────────────
    menu_map = {
        "menu_pdf2txt":      cmd_pdf2txt,
        "menu_linearize":    cmd_linearize,
        "menu_thumbnail":    cmd_thumbnail,
        "menu_pdf_info":     cmd_pdf_info,
        "menu_redact":       cmd_redact,
        "menu_impose":       cmd_impose,
        "menu_deskew":       cmd_deskew,
        "menu_pwd_strength": cmd_pwd_strength,
        "menu_pwd_crack":    cmd_pwd_crack,
        "menu_metadata_edit":cmd_metadata_edit,
        "menu_img_compress": cmd_img_compress,
        "menu_img_resize":   cmd_img_resize,
        "menu_img_crop":     cmd_img_crop,
        "menu_img_filter":   cmd_img_filter,
        "menu_img_text":     cmd_img_text,
        "menu_img2jpg":      cmd_img2jpg,
        "menu_img2png":      cmd_img2png,
        "menu_img_bgremove": cmd_img_bgremove,
        "menu_csv2pdf":      cmd_csv2pdf,
        "menu_txt2pdf":      cmd_txt2pdf,
        "menu_html2pdf":     cmd_html2pdf,
        "menu_json2pdf":     cmd_json2pdf,
        "menu_doc2pdf":      cmd_doc2pdf,
        "menu_pdf2epub":     cmd_pdf2epub,
        "menu_epub2pdf":     cmd_epub2pdf,
        "menu_hash":         cmd_hash,
        "menu_steg":         cmd_steganography,
        "menu_pdf_sign":     cmd_pdf_sign,
        "menu_poster":       cmd_poster,
        "menu_calendar":     cmd_calendar_pdf,
        "menu_invoice":      cmd_invoice,
        "menu_resume":       cmd_resume,
        "menu_certificate":  cmd_certificate,
        "menu_zip":          cmd_zip,
        "menu_unzip":        cmd_unzip,
        "menu_fileinfo":     cmd_fileinfo,
        "menu_qrcode_scan":  cmd_qrcode_scan,
        "menu_barcode":      cmd_barcode,
        "menu_remind":       cmd_remind,
        "menu_notes":        cmd_notes,
        "menu_history":      cmd_history,
    }
    if data in menu_map:
        await q.answer()
        await menu_map[data](update, ctx)
        return True

    return False
