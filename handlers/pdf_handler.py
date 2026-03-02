"""
PDF Handler v4.0
Fixes: OCR HTML entity crash, multi-reactions (3-5 at once), progress bars,
       delete buttons after send, memory purge after send, per-feature limits.
New: /reverse, /pdf_compare, /dashboard
"""
import io, random, asyncio, gc, html
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from utils.keyboards import (
    main_menu, back_btn, cancel_btn, font_menu, watermark_menu,
    page_no_style_menu, bg_color_menu, rotate_menu,
    ocr_language_menu, notebook_style_menu, language_menu
)
from utils import pdf_utils
from utils.i18n import t, set_user_lang
from utils.progress import make_progress
from utils.cache import delete_buttons_later
from config import REACTIONS, REACTION_COUNT, DELETE_BUTTONS_AFTER_SEC
from database import check_feature_limit, increment_usage, get_user_dashboard, get_plan, get_usage

# ── States ────────────────────────────────────────────────────────────────────
S = {
    "compress","split","merge","lock","lock_pass","unlock","unlock_pass",
    "watermark","wm_text","wm_logo_img","dark","pageno","excel","repair",
    "pdf2img","img2pdf","bg","hw_font_sel","hw_style_sel","hw_text","ocr",
    "rotate","resize","addtext","addtext_input","footer","footer_input",
    "extract","extract_range","meta",
    "pdf2word","pdf2ppt","crop","qr",
    "delete_pages","delete_pages_range","reorder","reorder_input",
    "reverse","pdf_compare","pdf_compare_2",
}

def _set_state(ctx, state, **kw):
    ctx.user_data["state"] = state
    ctx.user_data.update(kw)

def _clear(ctx):
    lang = ctx.user_data.get("lang", "en")
    ctx.user_data.clear()
    ctx.user_data["lang"] = lang

def _esc(text: str) -> str:
    """Escape HTML entities — CRITICAL for OCR output with Hindi/Arabic text."""
    return html.escape(str(text))

# ── Multi-Reaction ─────────────────────────────────────────────────────────────
async def _react(update, count: int = None):  # FIXED v4.1
    """
    FIXED: Telegram bots can only set 1 reaction per message.
    Using only valid Bot API approved reaction emoji.
    """
    if not update.message:
        return
    # Only these emoji work as bot reactions in Telegram Bot API 7.0+
    VALID = [
        "👍","👎","❤","🔥","🥰","👏","😁","🤔","🤯","😱",
        "🎉","🤩","🙏","👌","🏆","⚡","💯","🌟","🎊","🥺",
    ]
    try:
        from telegram import ReactionTypeEmoji
        emoji = random.choice(VALID)
        await update.message.set_reaction([ReactionTypeEmoji(emoji)])
    except Exception:
        pass  # Always silent — reactions are decorative only

# ── Send helpers with auto-button-delete and memory purge ─────────────────────
async def _send_pdf(update, data: bytes, filename: str, caption: str = ""):
    size = pdf_utils.file_size_str(data)
    cap  = caption or f"✅ Done! <b>({size})</b>"
    sent = await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap, parse_mode="HTML", reply_markup=main_menu()
    )
    # Schedule button removal after delay
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    # Purge data from memory immediately
    del data
    gc.collect()
    return sent

async def _send_file(update, data: bytes, filename: str, caption: str = ""):
    size = pdf_utils.file_size_str(data)
    cap  = caption or f"✅ Done! <b>({size})</b>"
    sent = await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap, parse_mode="HTML", reply_markup=main_menu()
    )
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    del data
    gc.collect()
    return sent

async def _send_photo(update, data: bytes, caption: str = ""):
    sent = await update.effective_message.reply_photo(
        photo=io.BytesIO(data), caption=caption, parse_mode="HTML",
        reply_markup=main_menu()
    )
    asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
    del data
    gc.collect()
    return sent

async def _err(update, text: str):
    await update.effective_message.reply_text(
        f"❌ <b>Error:</b> {_esc(text[:300])}", parse_mode="HTML", reply_markup=back_btn()
    )

async def _get_pdf(update) -> bytes | None:
    msg = update.message
    if msg.document and msg.document.mime_type == "application/pdf":
        f = await msg.document.get_file()
        return bytes(await f.download_as_bytearray())
    await update.message.reply_text(
        "⚠️ Please send a <b>PDF file</b>!", parse_mode="HTML", reply_markup=cancel_btn()
    )
    return None

async def _check_limit(update, ctx, feature: str) -> bool:
    """Check per-feature limit. Returns True if allowed."""
    user_id = update.effective_user.id
    ok, reason = await check_feature_limit(user_id, feature)
    if not ok:
        await update.effective_message.reply_text(
            reason, parse_mode="HTML", reply_markup=back_btn()
        )
    return ok


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CALLBACK ROUTER
# ─────────────────────────────────────────────────────────────────────────────
async def menu_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data

    if data == "noop":
        await q.answer()
        return

    if data == "back_main":
        await q.answer()
        _clear(ctx)
        try:
            await q.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await q.message.reply_text(
            "🏠 <b>Main Menu</b> — Choose a tool:",
            parse_mode="HTML", reply_markup=main_menu()
        )
        return

    await q.answer()

    # Language
    if data.startswith("setlang_"):
        lang = data[8:]
        set_user_lang(ctx, lang)
        from utils.i18n import STRINGS
        msg = STRINGS.get(lang, STRINGS["en"]).get("lang_selected", "✅ Language set!")
        await q.message.reply_text(msg, reply_markup=main_menu())
        return

    if data.startswith("font_"):
        await _font_selected(update, ctx, data[5:])
        return
    if data.startswith("nbstyle_"):
        await _nbstyle_selected(update, ctx, data[8:])
        return
    if data.startswith("ocrlang_"):
        await _ocrlang_selected(update, ctx, data[8:])
        return
    if data.startswith("rot_"):
        await _handle_rotate(update, ctx, data)
        return
    if data in ("wm_text", "wm_logo", "wm_invisible"):
        wm_map = {"wm_text": "text", "wm_logo": "logo", "wm_invisible": "invisible"}
        _set_state(ctx, "watermark", wm_type=wm_map[data])
        await q.message.reply_text("📎 <b>Send the PDF file first:</b>", parse_mode="HTML", reply_markup=cancel_btn())
        return
    if data.startswith("pn_"):
        _set_state(ctx, "pageno", pn_style=data)
        await q.message.reply_text("📎 <b>Now send the PDF file:</b>", parse_mode="HTML", reply_markup=cancel_btn())
        return
    if data.startswith("bg_"):
        _set_state(ctx, "bg", bg_color=data)
        await q.message.reply_text("📎 <b>Now send the PDF file:</b>", parse_mode="HTML", reply_markup=cancel_btn())
        return
    if data.startswith("buy_"):
        from handlers.premium_handler import buy_plan_callback
        await buy_plan_callback(update, ctx); return
    if data.startswith("pay_ss_"):
        from handlers.premium_handler import pay_screenshot_callback
        await pay_screenshot_callback(update, ctx); return

    routes = {
        "menu_compress":      (_prompt, "compress",      "📐 Compress PDF",       "Send the PDF to compress!"),
        "menu_split":         (_prompt, "split",         "✂️ Split PDF",           "Send the PDF to split!"),
        "menu_merge":         (_prompt_merge, None, None, None),
        "menu_repair":        (_prompt, "repair",        "🧩 Repair PDF",         "Send the corrupted PDF!"),
        "menu_dark":          (_prompt, "dark",          "🌙 Dark Mode",          "Send the PDF!"),
        "menu_excel":         (_prompt, "excel",         "📊 PDF → Excel",        "Send the PDF!"),
        "menu_pdf2img":       (_prompt, "pdf2img",       "🖼️ PDF → Images",      "Send the PDF!"),
        "menu_img2pdf":       (_prompt_img2pdf, None, None, None),
        "menu_watermark":     (_menu_wm, None, None, None),
        "menu_bg":            (_menu_bg_color, None, None, None),
        "menu_pageno":        (_menu_pageno, None, None, None),
        "menu_rotate":        (_menu_rotate, None, None, None),
        "menu_resize":        (_prompt, "resize",        "📏 Resize to A4",       "Send the PDF!"),
        "menu_hw":            (_menu_font, None, None, None),
        "menu_ocr":           (_menu_ocr_lang, None, None, None),
        "menu_addtext":       (_prompt, "addtext",       "📝 Add Text",           "Send the PDF!"),
        "menu_footer":        (_prompt, "footer",        "🗂️ Add Footer",         "Send the PDF!"),
        "menu_extract":       (_prompt, "extract",       "🔖 Extract Pages",      "Send the PDF!"),
        "menu_meta":          (_prompt, "meta",          "📋 PDF Metadata",       "Send the PDF!"),
        "menu_pdf2word":      (_prompt, "pdf2word",      "📄 PDF → Word",         "Send the PDF!"),
        "menu_pdf2ppt":       (_prompt, "pdf2ppt",       "📊 PDF → PowerPoint",   "Send the PDF!"),
        "menu_crop":          (_prompt, "crop",          "✂️ Crop Margins",        "Send the PDF!"),
        "menu_qr":            (_menu_qr, None, None, None),
        "menu_delete_pages":  (_prompt, "delete_pages",  "🗑️ Delete Pages",       "Send the PDF!"),
        "menu_reorder":       (_prompt, "reorder",       "🔀 Reorder Pages",      "Send the PDF!"),
        "menu_reverse":       (_prompt, "reverse",       "🔃 Reverse Pages",      "Send the PDF!"),
        "menu_compare":       (_prompt_compare, None, None, None),
        "menu_account":       (_menu_account, None, None, None),
        "menu_dashboard":     (_menu_dashboard, None, None, None),
        "menu_premium":       (_menu_premium, None, None, None),
        "menu_help":          (_menu_help, None, None, None),
        "menu_lang":          (_menu_lang, None, None, None),
        "do_lock":   (_prompt, "lock",    "🔒 Lock PDF",    "Send the PDF!"),
        "do_unlock": (_prompt, "unlock",  "🔓 Unlock PDF",  "Send the locked PDF!"),
        "do_compress":(_prompt,"compress","📐 Compress",    "Send the PDF!"),
        "do_split":  (_prompt, "split",   "✂️ Split",        "Send the PDF!"),
        "do_merge":  (_prompt_merge, None, None, None),
        "do_pdf2img":(_prompt, "pdf2img", "🖼️ PDF→Images",  "Send the PDF!"),
        "do_excel":  (_prompt, "excel",   "📊 PDF→Excel",   "Send the PDF!"),
        "do_pageno": (_menu_pageno, None, None, None),
    }

    info = routes.get(data)
    if info:
        fn = info[0]
        if fn == _prompt:
            await _prompt(update, ctx, info[1], info[2], info[3])
        else:
            await fn(update, ctx)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER PROMPTS
# ─────────────────────────────────────────────────────────────────────────────
async def _prompt(update, ctx, state, title, desc):
    _set_state(ctx, state)
    await update.callback_query.message.reply_text(
        f"<b>{title}</b>\n\n📎 {desc}", parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _prompt_merge(update, ctx):
    _set_state(ctx, "merge"); ctx.user_data["merge_files"] = []
    await update.callback_query.message.reply_text(
        "🔗 <b>Merge PDFs</b>\n\nSend PDFs one by one, then <code>/done</code>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _prompt_img2pdf(update, ctx):
    _set_state(ctx, "img2pdf"); ctx.user_data["images"] = []
    await update.callback_query.message.reply_text(
        "🖼️ <b>Images → PDF</b>\n\nSend images one by one, then <code>/done</code>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _prompt_compare(update, ctx):
    _set_state(ctx, "pdf_compare"); ctx.user_data["compare_files"] = []
    await update.callback_query.message.reply_text(
        "🔍 <b>PDF Compare</b>\n\nSend <b>first PDF</b>:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _menu_wm(update, ctx):
    await update.callback_query.message.reply_text("🌊 <b>Watermark Type:</b>", parse_mode="HTML", reply_markup=watermark_menu())
async def _menu_bg_color(update, ctx):
    await update.callback_query.message.reply_text("🎨 <b>Choose Background:</b>", parse_mode="HTML", reply_markup=bg_color_menu())
async def _menu_pageno(update, ctx):
    await update.callback_query.message.reply_text("🔢 <b>Page Number Style:</b>", parse_mode="HTML", reply_markup=page_no_style_menu())
async def _menu_rotate(update, ctx):
    _set_state(ctx, "rotate")
    await update.callback_query.message.reply_text("🔄 <b>Rotate PDF</b>\n\nSend the PDF first!", parse_mode="HTML", reply_markup=cancel_btn())
async def _menu_font(update, ctx):
    await update.callback_query.message.reply_text("✍️ <b>Choose Font:</b>", parse_mode="HTML", reply_markup=font_menu())
async def _menu_ocr_lang(update, ctx):
    await update.callback_query.message.reply_text(
        "🌐 <b>Select Document Language:</b>\n<i>Better accuracy with correct language!</i>",
        parse_mode="HTML", reply_markup=ocr_language_menu()
    )
async def _menu_qr(update, ctx):
    _set_state(ctx, "qr")
    await update.callback_query.message.reply_text("🔲 <b>QR Code</b>\n\nType text or URL:", parse_mode="HTML", reply_markup=cancel_btn())
async def _menu_lang(update, ctx):
    await update.callback_query.message.reply_text("🌍 <b>Choose Language:</b>", parse_mode="HTML", reply_markup=language_menu())
async def _menu_account(update, ctx):
    from handlers.start_handler import account_cmd; await account_cmd(update, ctx)
async def _menu_dashboard(update, ctx):
    # Simulate a real update for dashboard
    class _FakeUpdate:
        effective_user = update.callback_query.from_user
        message = update.callback_query.message
    await cmd_dashboard(_FakeUpdate(), None)
async def _menu_premium(update, ctx):
    from handlers.premium_handler import premium_cmd; await premium_cmd(update, ctx)
async def _menu_help(update, ctx):
    from handlers.start_handler import help_cmd; await help_cmd(update, ctx)

async def _font_selected(update, ctx, font_key):
    from config import FONTS
    name = FONTS.get(font_key, {}).get("name", "?")
    _set_state(ctx, "hw_style_sel", hw_font=font_key)
    await update.callback_query.message.reply_text(
        f"✅ Font: <b>{name}</b>\n\n📓 Now choose <b>Notebook Style</b>:",
        parse_mode="HTML", reply_markup=notebook_style_menu()
    )

async def _nbstyle_selected(update, ctx, style_key):
    from config import NOTEBOOK_STYLES
    name = NOTEBOOK_STYLES.get(style_key, {}).get("name", "?")
    ctx.user_data["hw_style"] = style_key
    _set_state(ctx, "hw_text", hw_font=ctx.user_data.get("hw_font", "caveat"), hw_style=style_key)
    await update.callback_query.message.reply_text(
        f"✅ Style: <b>{name}</b>\n\n✍️ Now <b>type your text</b>:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _ocrlang_selected(update, ctx, lang_key):
    from config import OCR_LANGUAGES
    name = OCR_LANGUAGES.get(lang_key, {}).get("name", "?")
    _set_state(ctx, "ocr", ocr_lang=lang_key)
    await update.callback_query.message.reply_text(
        f"✅ Language: <b>{name}</b>\n\n👁️ Now send your <b>image or PDF</b>:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _handle_rotate(update, ctx, data):
    angle_map = {"rot_90r": 90, "rot_90l": -90, "rot_180": 180}
    ctx.user_data["rotate_angle"] = "auto" if data == "rot_auto" else angle_map.get(data, 90)
    await update.callback_query.message.reply_text(
        "📎 <b>Now send the PDF to rotate:</b>", parse_mode="HTML", reply_markup=cancel_btn()
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MESSAGE HANDLER
# ─────────────────────────────────────────────────────────────────────────────
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg   = update.message
    state = ctx.user_data.get("state")

    if msg.photo:
        from handlers.premium_handler import handle_payment_screenshot
        if await handle_payment_screenshot(update, ctx):
            return

    if not state:
        return

    if msg.text and msg.text.strip().lower() in ("/done", "done"):
        await _handle_done(update, ctx, state); return

    await _react(update)

    dispatch = {
        "compress": _do_compress, "split": _do_split,
        "merge": _do_merge_collect, "lock": _do_lock_pdf, "lock_pass": _do_lock_pass,
        "unlock": _do_unlock_pdf, "unlock_pass": _do_unlock_pass,
        "watermark": _do_watermark, "wm_text": _do_wm_text, "wm_logo_img": _do_wm_logo,
        "dark": _do_dark, "pageno": _do_pageno, "excel": _do_excel,
        "repair": _do_repair, "pdf2img": _do_pdf2img, "img2pdf": _do_img2pdf_collect,
        "bg": _do_bg, "hw_text": _do_handwrite, "ocr": _do_ocr,
        "rotate": _do_rotate_collect, "resize": _do_resize,
        "addtext": _do_addtext_pdf, "addtext_input": _do_addtext_input,
        "footer": _do_footer_pdf, "footer_input": _do_footer_input,
        "extract": _do_extract_pdf, "extract_range": _do_extract_range,
        "meta": _do_meta,
        "pdf2word": _do_pdf2word, "pdf2ppt": _do_pdf2ppt,
        "crop": _do_crop, "qr": _do_qr,
        "delete_pages": _do_delete_pages_pdf, "delete_pages_range": _do_delete_pages_range,
        "reorder": _do_reorder_pdf, "reorder_input": _do_reorder_input,
        "reverse": _do_reverse,
        "pdf_compare": _do_compare_first, "pdf_compare_2": _do_compare_second,
    }
    fn = dispatch.get(state)
    if fn:
        await fn(update, ctx)


async def _handle_done(update, ctx, state):
    if state == "merge":
        files = ctx.user_data.get("merge_files", [])
        if len(files) < 2:
            await update.message.reply_text("⚠️ Send at least 2 PDFs!", reply_markup=cancel_btn()); return
        pg = await make_progress(update, "Merging PDFs")
        try:
            await pg.update(30, "Reading files...")
            result = pdf_utils.merge_pdfs(files)
            await pg.update(90, "Finalizing...")
            _clear(ctx)
            await pg.delete()
            await _send_pdf(update, result, "merged.pdf",
                            f"✅ <b>Merged {len(files)} PDFs!</b> ({pdf_utils.file_size_str(result)})")
            del files, result; gc.collect()
        except Exception as e:
            await pg.fail(str(e)); await _err(update, str(e))

    elif state == "img2pdf":
        images = ctx.user_data.get("images", [])
        if not images:
            await update.message.reply_text("⚠️ Send at least 1 image!", reply_markup=cancel_btn()); return
        pg = await make_progress(update, "Images → PDF")
        try:
            await pg.update(40, "Converting images...")
            result = pdf_utils.images_to_pdf(images)
            await pg.update(90, "Saving...")
            _clear(ctx)
            await pg.delete()
            await _send_pdf(update, result, "images.pdf",
                            f"✅ <b>{len(images)} images → PDF!</b> ({pdf_utils.file_size_str(result)})")
            del images, result; gc.collect()
        except Exception as e:
            await pg.fail(str(e)); await _err(update, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

async def _do_compress(update, ctx):
    if not await _check_limit(update, ctx, "compress"): return
    data = await _get_pdf(update)
    if not data: return
    orig = pdf_utils.file_size_str(data)
    pg = await make_progress(update, "Compressing PDF")
    try:
        await pg.update(20, "Strategy 1: Stream compression...")
        result = pdf_utils.compress_pdf(data)
        await pg.update(80, "Comparing results...")
        saved = round((1 - len(result)/len(data)) * 100, 1)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "compress")
        cap = (f"📐 <b>Compression Complete!</b>\n\n"
               f"📊 Before: <code>{orig}</code>\n"
               f"📉 After:  <code>{pdf_utils.file_size_str(result)}</code>\n"
               f"💾 Saved:  <b>{saved}%</b>")
        await _send_pdf(update, result, "compressed.pdf", cap)
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_split(update, ctx):
    if not await _check_limit(update, ctx, "split"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "Splitting PDF")
    try:
        await pg.update(30, "Reading pages...")
        pages = pdf_utils.split_pdf_all(data)
        await pg.update(70, f"Sending {min(len(pages),20)} pages...")
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "split")
        for i, pd in enumerate(pages[:20], 1):
            await update.message.reply_document(
                document=InputFile(io.BytesIO(pd), filename=f"page_{i:02d}.pdf"),
                caption=f"📄 Page {i} / {len(pages)}"
            )
        note = f" ⚠️ First 20 shown (total: {len(pages)})" if len(pages) > 20 else ""
        await update.message.reply_text(f"✅ <b>Split complete!</b>{note}", parse_mode="HTML", reply_markup=main_menu())
        del data, pages; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_merge_collect(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["merge_files"].append(data)
    n = len(ctx.user_data["merge_files"])
    await update.message.reply_text(
        f"✅ PDF <b>#{n}</b> received! Send more or <code>/done</code>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_lock_pdf(update, ctx):
    if not await _check_limit(update, ctx, "lock"): return
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["lock_pdf"] = data
    _set_state(ctx, "lock_pass")
    await update.message.reply_text("🔒 PDF received! Now type a <b>password</b>:", parse_mode="HTML", reply_markup=cancel_btn())

async def _do_lock_pass(update, ctx):
    if not update.message.text: return
    password = update.message.text.strip()
    pg = await make_progress(update, "Locking PDF")
    try:
        await pg.update(50, "Encrypting...")
        result = pdf_utils.lock_pdf(ctx.user_data["lock_pdf"], password)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "lock")
        await _send_pdf(update, result, "locked.pdf", f"🔒 <b>PDF locked!</b>\n🔑 Password: <code>{_esc(password)}</code>")
        del result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_unlock_pdf(update, ctx):
    if not await _check_limit(update, ctx, "unlock"): return
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["unlock_pdf"] = data
    _set_state(ctx, "unlock_pass")
    await update.message.reply_text("🔑 Type the password (or <code>.</code> for none):", parse_mode="HTML", reply_markup=cancel_btn())

async def _do_unlock_pass(update, ctx):
    if not update.message.text: return
    password = update.message.text.strip()
    if password == ".": password = ""
    pg = await make_progress(update, "Unlocking PDF")
    try:
        await pg.update(50, "Removing encryption...")
        result = pdf_utils.unlock_pdf(ctx.user_data["unlock_pdf"], password)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "unlock")
        await _send_pdf(update, result, "unlocked.pdf", "🔓 <b>PDF unlocked!</b>")
        del result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_watermark(update, ctx):
    wm_type = ctx.user_data.get("wm_type", "text")
    if not await _check_limit(update, ctx, "watermark"): return
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["wm_pdf"] = data
    if wm_type == "logo":
        _set_state(ctx, "wm_logo_img", wm_type="logo", wm_pdf=data)
        await update.message.reply_text("🖼️ <b>Now send your logo image:</b>", parse_mode="HTML", reply_markup=cancel_btn())
    else:
        _set_state(ctx, "wm_text", wm_type=wm_type, wm_pdf=data)
        label = "Invisible watermark text" if wm_type == "invisible" else "Watermark text"
        await update.message.reply_text(f"📝 <b>Type the {label}:</b>", parse_mode="HTML", reply_markup=cancel_btn())

async def _do_wm_text(update, ctx):
    if not update.message.text: return
    text = update.message.text.strip()
    invisible = ctx.user_data.get("wm_type") == "invisible"
    pg = await make_progress(update, "Adding Watermark")
    try:
        await pg.update(50, "Stamping pages...")
        result = pdf_utils.watermark_text(ctx.user_data["wm_pdf"], text, invisible=invisible)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "watermark")
        icon = "👻" if invisible else "🌊"
        await _send_pdf(update, result, "watermarked.pdf", f"{icon} <b>Watermark added!</b>\nText: <code>{_esc(text)}</code>")
        del result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_wm_logo(update, ctx):
    img_data = None
    if update.message.photo:
        f = await update.message.photo[-1].get_file()
        img_data = bytes(await f.download_as_bytearray())
    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        f = await update.message.document.get_file()
        img_data = bytes(await f.download_as_bytearray())
    if not img_data:
        await update.message.reply_text("⚠️ Send an image!", reply_markup=cancel_btn()); return
    pg = await make_progress(update, "Adding Logo Watermark")
    try:
        await pg.update(60, "Stamping logo...")
        result = pdf_utils.watermark_image(ctx.user_data["wm_pdf"], img_data)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "watermark")
        await _send_pdf(update, result, "watermarked.pdf", "🖼️ <b>Logo watermark added!</b>")
        del img_data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_dark(update, ctx):
    if not await _check_limit(update, ctx, "darkmode"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "Dark Mode Conversion")
    try:
        await pg.update(20, "Rendering pages..."); await asyncio.sleep(0.1)
        result = pdf_utils.change_bg(data, "bg_dark")
        await pg.update(90, "Finalizing...")
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "darkmode")
        await _send_pdf(update, result, "dark_mode.pdf", "🌙 <b>Dark Mode PDF ready!</b>")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_pageno(update, ctx):
    if not await _check_limit(update, ctx, "pagenos"): return
    data = await _get_pdf(update)
    if not data: return
    style = ctx.user_data.get("pn_style", "pn_arabic")
    pg = await make_progress(update, "Adding Page Numbers")
    try:
        await pg.update(50, "Numbering pages...")
        result = pdf_utils.add_page_numbers(data, style)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "pagenos")
        await _send_pdf(update, result, "numbered.pdf", "🔢 <b>Page numbers added!</b>")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_excel(update, ctx):
    if not await _check_limit(update, ctx, "excel"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "PDF → Excel")
    try:
        await pg.update(30, "Extracting tables...")
        result = pdf_utils.pdf_to_excel(data)
        await pg.update(85, "Building spreadsheet...")
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "excel")
        await _send_file(update, result, "extracted.xlsx", "📊 <b>PDF → Excel done!</b>")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_repair(update, ctx):
    if not await _check_limit(update, ctx, "repair"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "Repairing PDF")
    try:
        await pg.update(50, "Attempting repair...")
        result = pdf_utils.repair_pdf(data)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "repair")
        await _send_pdf(update, result, "repaired.pdf", "🧩 <b>PDF repaired!</b>")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_pdf2img(update, ctx):
    if not await _check_limit(update, ctx, "pdf2img"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "PDF → Images")
    try:
        await pg.update(30, "Rendering pages...")
        images = pdf_utils.pdf_to_images(data)
        await pg.update(70, f"Sending {min(len(images),15)} images...")
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "pdf2img")
        for i, img in enumerate(images[:15], 1):
            await update.message.reply_photo(photo=io.BytesIO(img), caption=f"🖼️ Page {i}/{len(images)}")
        note = f" (first 15 of {len(images)})" if len(images) > 15 else ""
        await update.message.reply_text(f"✅ <b>Converted{note}!</b>", parse_mode="HTML", reply_markup=main_menu())
        del data, images; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_img2pdf_collect(update, ctx):
    img_data = None
    if update.message.photo:
        f = await update.message.photo[-1].get_file()
        img_data = bytes(await f.download_as_bytearray())
    elif update.message.document and update.message.document.mime_type and \
         update.message.document.mime_type.startswith("image/"):
        f = await update.message.document.get_file()
        img_data = bytes(await f.download_as_bytearray())
    if img_data:
        ctx.user_data["images"].append(img_data)
        n = len(ctx.user_data["images"])
        await update.message.reply_text(
            f"✅ Image <b>#{n}</b> received! Send more or <code>/done</code>",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
    else:
        await update.message.reply_text("⚠️ Please send an <b>image</b>!", parse_mode="HTML")

async def _do_bg(update, ctx):
    if not await _check_limit(update, ctx, "bgchange"): return
    data = await _get_pdf(update)
    if not data: return
    color = ctx.user_data.get("bg_color", "bg_dark")
    pg = await make_progress(update, "Applying Background Theme")
    try:
        await pg.update(25, "Rendering pages...")
        result = pdf_utils.change_bg(data, color)
        await pg.update(90, "Saving...")
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "bgchange")
        await _send_pdf(update, result, "bg_changed.pdf", "🎨 <b>Background applied!</b>")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_handwrite(update, ctx):
    if not await _check_limit(update, ctx, "handwrite"): return
    if not update.message.text:
        await update.message.reply_text("⚠️ Please type your text!", reply_markup=cancel_btn()); return
    text      = update.message.text.strip()
    font_key  = ctx.user_data.get("hw_font", "caveat")
    style_key = ctx.user_data.get("hw_style", "classic_blue")
    from config import FONTS, NOTEBOOK_STYLES
    font_name  = FONTS.get(font_key, {}).get("name", "Default")
    style_name = NOTEBOOK_STYLES.get(style_key, {}).get("name", "Classic")
    pg = await make_progress(update, "Creating Handwritten PDF")
    try:
        await pg.update(40, f"Writing with {font_name}...")
        result = pdf_utils.create_handwritten_pdf(text, font_key, style_key)
        await pg.update(90, "Saving...")
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "handwrite")
        await _send_pdf(update, result, "handwritten.pdf",
                        f"✍️ <b>Handwritten PDF!</b>\n📝 Font: {font_name}\n📓 Style: {style_name}")
        del result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_ocr(update, ctx):
    """
    ⚠️ FIXED: OCR output is HTML-escaped before sending.
    Hindi/Arabic OCR text used to crash with 'unsupported start tag' error.
    """
    if not await _check_limit(update, ctx, "ocr"): return
    lang = ctx.user_data.get("ocr_lang", "eng+hin")
    from config import OCR_LANGUAGES
    lang_name = OCR_LANGUAGES.get(lang, {}).get("name", lang)
    pg = await make_progress(update, f"OCR — {lang_name}")
    try:
        data = None
        await pg.update(20, "Loading file...")
        if update.message.photo:
            f    = await update.message.photo[-1].get_file()
            data = bytes(await f.download_as_bytearray())
            await pg.update(60, "Running OCR on image...")
            text = pdf_utils.ocr_image(data, lang)
        elif update.message.document:
            f    = await update.message.document.get_file()
            data = bytes(await f.download_as_bytearray())
            await pg.update(50, "Analyzing PDF pages...")
            if update.message.document.mime_type == "application/pdf":
                text = pdf_utils.ocr_pdf(data, lang)
            else:
                text = pdf_utils.ocr_image(data, lang)
        else:
            await pg.delete()
            await update.message.reply_text("⚠️ Send an image or PDF!", reply_markup=cancel_btn())
            return

        await pg.update(90, "Preparing output...")
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "ocr")

        # ── CRITICAL FIX: escape the OCR text before sending as HTML ──
        safe_text = _esc(text)

        if len(safe_text) > 3500:
            # Send as .txt file — no HTML parsing issues
            await update.message.reply_document(
                document=InputFile(io.BytesIO(text.encode("utf-8")), filename="extracted.txt"),
                caption=f"👁️ <b>OCR Complete!</b>\nLanguage: {lang_name}\n<i>Text saved to file (too long for message)</i>",
                parse_mode="HTML", reply_markup=main_menu()
            )
        else:
            await update.message.reply_text(
                f"👁️ <b>OCR Complete ({lang_name})</b>\n\n<pre>{safe_text}</pre>",
                parse_mode="HTML", reply_markup=main_menu()
            )
        del data; gc.collect()
    except Exception as e:
        try:
            await pg.delete()
        except Exception:
            pass
        await _err(update, str(e))

async def _do_rotate_collect(update, ctx):
    if "rotate_angle" not in ctx.user_data:
        data = await _get_pdf(update)
        if not data: return
        ctx.user_data["rotate_pdf"] = data
        await update.message.reply_text("🔄 <b>Choose rotation angle:</b>", parse_mode="HTML", reply_markup=rotate_menu())
        return
    data  = ctx.user_data.get("rotate_pdf") or await _get_pdf(update)
    angle = ctx.user_data.get("rotate_angle", 90)
    pg = await make_progress(update, "Rotating PDF")
    try:
        await pg.update(50, f"Rotating {angle}°...")
        result = pdf_utils.auto_rotate_pdf(data) if angle == "auto" else pdf_utils.rotate_pdf(data, angle)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "rotate")
        await _send_pdf(update, result, "rotated.pdf", "🔄 <b>PDF rotated!</b>")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_resize(update, ctx):
    if not await _check_limit(update, ctx, "resize"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "Resizing to A4")
    try:
        await pg.update(50, "Rescaling pages...")
        result = pdf_utils.resize_pdf_to_a4(data)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "resize")
        await _send_pdf(update, result, "a4_resized.pdf", "📏 <b>Resized to A4!</b>")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_addtext_pdf(update, ctx):
    if not await _check_limit(update, ctx, "addtext"): return
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["addtext_pdf"] = data
    _set_state(ctx, "addtext_input", addtext_pdf=data)
    await update.message.reply_text(
        "📝 <b>PDF received!</b>\n\nType the text to add:\n<i>(added to first page, top)</i>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_addtext_input(update, ctx):
    if not update.message.text: return
    text = update.message.text.strip()
    pg = await make_progress(update, "Adding Text")
    try:
        await pg.update(50, "Inserting text...")
        result = pdf_utils.add_text_to_pdf(ctx.user_data["addtext_pdf"], text)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "addtext")
        await _send_pdf(update, result, "text_added.pdf", "📝 <b>Text added to PDF!</b>")
        del result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_footer_pdf(update, ctx):
    if not await _check_limit(update, ctx, "footer"): return
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["footer_pdf"] = data
    _set_state(ctx, "footer_input", footer_pdf=data)
    await update.message.reply_text("🗂️ <b>PDF received!</b>\n\nType the footer text:", parse_mode="HTML", reply_markup=cancel_btn())

async def _do_footer_input(update, ctx):
    if not update.message.text: return
    text = update.message.text.strip()
    pg = await make_progress(update, "Adding Footer")
    try:
        await pg.update(50, "Stamping all pages...")
        result = pdf_utils.add_footer(ctx.user_data["footer_pdf"], text)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "footer")
        await _send_pdf(update, result, "footer_added.pdf", f"🗂️ <b>Footer added!</b>\nText: <code>{_esc(text)}</code>")
        del result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_extract_pdf(update, ctx):
    if not await _check_limit(update, ctx, "extract"): return
    data = await _get_pdf(update)
    if not data: return
    import fitz as _fitz
    with _fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
    ctx.user_data["extract_pdf"] = data
    _set_state(ctx, "extract_range", extract_pdf=data)
    await update.message.reply_text(
        f"🔖 <b>PDF has {total} pages.</b>\n\nType pages to extract:\n"
        f"  • Single: <code>3</code>\n  • Range: <code>2-5</code>\n  • Multiple: <code>1,3,5-7</code>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_extract_range(update, ctx):
    if not update.message.text: return
    page_range = update.message.text.strip()
    pg = await make_progress(update, "Extracting Pages")
    try:
        await pg.update(50, "Extracting...")
        result = pdf_utils.extract_pages(ctx.user_data["extract_pdf"], page_range)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "extract")
        await _send_pdf(update, result, "extracted_pages.pdf",
                        f"🔖 <b>Pages extracted!</b>\nRange: <code>{_esc(page_range)}</code>")
        del result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_meta(update, ctx):
    if not await _check_limit(update, ctx, "metadata"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "Reading Metadata")
    try:
        await pg.update(60, "Parsing PDF headers...")
        meta = pdf_utils.get_metadata(data)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "metadata")
        text = (
            "📋 <b>PDF Metadata</b>\n\n"
            f"╔══════════════════════╗\n"
            f"║ 📄 <b>Title:</b>   {_esc(meta['title'])}\n"
            f"║ 👤 <b>Author:</b>  {_esc(meta['author'])}\n"
            f"║ 📝 <b>Subject:</b> {_esc(meta['subject'])}\n"
            f"║ 🛠️ <b>Creator:</b> {_esc(meta['creator'])}\n"
            f"╠══════════════════════╣\n"
            f"║ 📑 <b>Pages:</b>   {meta['pages']}\n"
            f"║ 📦 <b>Size:</b>    {meta['size']}\n"
            f"║ 🔐 <b>Encrypted:</b> {'Yes' if meta['encrypted'] else 'No'}\n"
            f"╚══════════════════════╝"
        )
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_menu())
        del data; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))


# ── NEW OPERATIONS ─────────────────────────────────────────────────────────────

async def _do_pdf2word(update, ctx):
    if not await _check_limit(update, ctx, "pdf2word"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "PDF → Word DOCX")
    try:
        await pg.update(20, "Parsing text & tables...")
        result = pdf_utils.pdf_to_word(data)
        await pg.update(85, "Building document...")
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "pdf2word")
        await _send_file(update, result, "converted.docx",
                         f"📄 <b>PDF → Word Complete!</b>\n({pdf_utils.file_size_str(result)})\n<i>Open in Word or Google Docs</i>")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_pdf2ppt(update, ctx):
    if not await _check_limit(update, ctx, "pdf2ppt"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "PDF → PowerPoint")
    try:
        await pg.update(20, "Rendering pages as slides...")
        result = pdf_utils.pdf_to_ppt(data)
        await pg.update(85, "Building presentation...")
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "pdf2ppt")
        await _send_file(update, result, "converted.pptx",
                         f"📊 <b>PDF → PowerPoint!</b>\n({pdf_utils.file_size_str(result)})\n<i>Each page = 1 slide</i>")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_crop(update, ctx):
    if not await _check_limit(update, ctx, "crop"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "Cropping Margins")
    try:
        await pg.update(40, "Detecting content area...")
        result = pdf_utils.crop_margins(data)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "crop")
        await _send_pdf(update, result, "cropped.pdf",
                        f"✂️ <b>Margins Cropped!</b>\n{pdf_utils.file_size_str(data)} → {pdf_utils.file_size_str(result)}")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_qr(update, ctx):
    if not await _check_limit(update, ctx, "qr"): return
    if not update.message.text:
        await update.message.reply_text("⚠️ Type text or URL!", reply_markup=cancel_btn()); return
    text = update.message.text.strip()
    pg = await make_progress(update, "Generating QR Code")
    try:
        await pg.update(60, "Encoding data...")
        qr_img = pdf_utils.generate_qr(text)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "qr")
        await _send_photo(update, qr_img,
                          f"🔲 <b>QR Code Generated!</b>\nContent: <code>{_esc(text[:100])}</code>")
        del qr_img; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_delete_pages_pdf(update, ctx):
    if not await _check_limit(update, ctx, "delete_pages"): return
    data = await _get_pdf(update)
    if not data: return
    import fitz as _fitz
    with _fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
    ctx.user_data["delete_pdf"] = data
    _set_state(ctx, "delete_pages_range", delete_pdf=data)
    await update.message.reply_text(
        f"🗑️ <b>PDF has {total} pages.</b>\n\nWhich pages to <b>delete</b>?\n"
        f"  • Single: <code>3</code>\n  • Range: <code>2-5</code>\n  • Multiple: <code>1,3,7-9</code>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_delete_pages_range(update, ctx):
    if not update.message.text: return
    page_range = update.message.text.strip()
    pg = await make_progress(update, "Deleting Pages")
    try:
        await pg.update(50, "Removing pages...")
        result = pdf_utils.delete_pages(ctx.user_data["delete_pdf"], page_range)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "delete_pages")
        await _send_pdf(update, result, "pages_deleted.pdf",
                        f"🗑️ <b>Pages deleted!</b>\nDeleted: <code>{_esc(page_range)}</code>")
        del result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_reorder_pdf(update, ctx):
    if not await _check_limit(update, ctx, "reorder"): return
    data = await _get_pdf(update)
    if not data: return
    import fitz as _fitz
    with _fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
    ctx.user_data["reorder_pdf"] = data
    _set_state(ctx, "reorder_input", reorder_pdf=data)
    await update.message.reply_text(
        f"🔀 <b>PDF has {total} pages.</b>\n\nType the new page order:\n"
        f"  • Simple: <code>3,1,2</code>\n  • Range: <code>1,3,2-4</code>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_reorder_input(update, ctx):
    if not update.message.text: return
    order_str = update.message.text.strip()
    pg = await make_progress(update, "Reordering Pages")
    try:
        await pg.update(50, "Rearranging...")
        result = pdf_utils.reorder_pages(ctx.user_data["reorder_pdf"], order_str)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "reorder")
        await _send_pdf(update, result, "reordered.pdf", f"🔀 <b>Pages reordered!</b>\nOrder: <code>{_esc(order_str)}</code>")
        del result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_reverse(update, ctx):
    """NEW: Reverse page order."""
    if not await _check_limit(update, ctx, "reverse"): return
    data = await _get_pdf(update)
    if not data: return
    pg = await make_progress(update, "Reversing Pages")
    try:
        await pg.update(50, "Flipping order...")
        result = pdf_utils.reverse_pages(data)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "reverse")
        await _send_pdf(update, result, "reversed.pdf", "🔃 <b>Pages reversed!</b> Last page is now first.")
        del data, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))

async def _do_compare_first(update, ctx):
    """NEW: PDF Compare — collect first PDF."""
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["compare_files"] = [data]
    _set_state(ctx, "pdf_compare_2")
    await update.message.reply_text(
        "✅ <b>First PDF received!</b>\n\nNow send the <b>second PDF</b> to compare:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_compare_second(update, ctx):
    """NEW: PDF Compare — collect second PDF and generate diff."""
    if not await _check_limit(update, ctx, "pdf_compare"): return
    data2 = await _get_pdf(update)
    if not data2: return
    files = ctx.user_data.get("compare_files", [])
    if not files:
        await _err(update, "Please start over with /compare"); return
    data1 = files[0]
    pg = await make_progress(update, "Comparing PDFs")
    try:
        await pg.update(20, "Extracting text from PDF 1...")
        await pg.update(50, "Extracting text from PDF 2...")
        await pg.update(75, "Highlighting differences...")
        result, summary = pdf_utils.compare_pdfs(data1, data2)
        _clear(ctx)
        await pg.delete()
        await increment_usage(update.effective_user.id, "pdf_compare")
        cap = (f"🔍 <b>PDF Comparison Complete!</b>\n\n"
               f"📄 Pages in PDF 1: <b>{summary['pages1']}</b>\n"
               f"📄 Pages in PDF 2: <b>{summary['pages2']}</b>\n"
               f"📝 Changed lines: <b>{summary['diff_lines']}</b>\n"
               f"➕ Added: <b>{summary['added']}</b> | ➖ Removed: <b>{summary['removed']}</b>")
        await _send_pdf(update, result, "comparison.pdf", cap)
        del data1, data2, result; gc.collect()
    except Exception as e:
        await pg.fail(str(e)); await _err(update, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD COMMAND  ── NEW
# ─────────────────────────────────────────────────────────────────────────────
async def cmd_dashboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user   = update.effective_user
    stats  = await get_user_dashboard(user.id)
    plan   = await get_plan(user.id)
    usage  = await get_usage(user.id)

    plan_emoji = {"free": "🆓", "basic": "⭐", "pro": "👑"}.get(plan, "🆓")

    # Top features used today
    features = sorted(stats["today_features"].items(), key=lambda x: x[1], reverse=True)
    feat_lines = "\n".join([f"  {'🥇' if i==0 else '🥈' if i==1 else '🥉'} {f.title()}: <b>{c}</b>" 
                            for i, (f, c) in enumerate(features[:5])]) if features else "  <i>None yet today</i>"

    text = (
        f"📊 <b>Your Dashboard</b>\n\n"
        f"╔══════════════════════════╗\n"
        f"║  {plan_emoji} Plan: <b>{plan.title()}</b>\n"
        f"║  🔢 Total All-Time: <b>{stats['total_ops']}</b> ops\n"
        f"║  📅 This Month: <b>{stats['month_total']}</b> ops\n"
        f"║  📆 Today: <b>{usage}</b> ops\n"
        f"╠══════════════════════════╣\n"
        f"║  🏆 <b>Top Features Today:</b>\n"
        f"{feat_lines}\n"
        f"╠══════════════════════════╣\n"
        f"║  🎁 Referrals: <b>{stats['ref_count']}</b> friends\n"
        f"║  🔗 Your link:\n"
        f"║  <code>t.me/{ctx.bot.username}?start=ref_{user.id}</code>\n"
        f"╚══════════════════════════╝\n\n"
        f"💡 <i>Refer friends to earn free Pro days!</i>"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())


# ─────────────────────────────────────────────────────────────────────────────
# GROUP REACTION HANDLER  ── NEW
# React to ALL messages in groups (PDF, video, sticker, emoji, chat — everything)
# ─────────────────────────────────────────────────────────────────────────────
async def handle_group_reaction(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    React to ALL group messages (PDF, video, sticker, text, emoji — everything).
    FIXED: Uses only 1 valid reaction emoji (bot API limitation).
    Configurable chance to avoid spam.
    """
    from config import GROUP_REACTIONS_ENABLED, GROUP_REACTION_CHANCE
    if not GROUP_REACTIONS_ENABLED:
        return
    if not update.message:
        return
    if random.random() > GROUP_REACTION_CHANCE:
        return
    VALID = [
        "👍","❤","🔥","🥰","👏","😁","🤯","😱","🎉","🤩",
        "🙏","👌","🏆","⚡","💯","🌟","🎊","🥺","😍","🤣",
    ]
    try:
        from telegram import ReactionTypeEmoji
        await update.message.set_reaction([ReactionTypeEmoji(random.choice(VALID))])
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# DIRECT COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────────────────────
async def cmd_compress(u, c):     _set_state(c, "compress");       await u.message.reply_text("📐 Send the PDF to compress!", reply_markup=cancel_btn())
async def cmd_split(u, c):        _set_state(c, "split");          await u.message.reply_text("✂️ Send the PDF to split!", reply_markup=cancel_btn())
async def cmd_merge(u, c):        _set_state(c, "merge"); c.user_data["merge_files"] = []; await u.message.reply_text("🔗 Send PDFs one by one, then /done", reply_markup=cancel_btn())
async def cmd_lock(u, c):         _set_state(c, "lock");           await u.message.reply_text("🔒 Send the PDF to lock!", reply_markup=cancel_btn())
async def cmd_unlock(u, c):       _set_state(c, "unlock");         await u.message.reply_text("🔓 Send the locked PDF!", reply_markup=cancel_btn())
async def cmd_repair(u, c):       _set_state(c, "repair");         await u.message.reply_text("🧩 Send the corrupted PDF!", reply_markup=cancel_btn())
async def cmd_watermark(u, c):                                      await u.message.reply_text("🌊 Choose watermark type:", reply_markup=watermark_menu())
async def cmd_darkmode(u, c):     _set_state(c, "dark");           await u.message.reply_text("🌙 Send the PDF!", reply_markup=cancel_btn())
async def cmd_pagenos(u, c):                                        await u.message.reply_text("🔢 Choose style:", reply_markup=page_no_style_menu())
async def cmd_pdf2img(u, c):      _set_state(c, "pdf2img");        await u.message.reply_text("🖼️ Send the PDF!", reply_markup=cancel_btn())
async def cmd_img2pdf(u, c):      _set_state(c, "img2pdf"); c.user_data["images"] = []; await u.message.reply_text("🖼️ Send images, then /done", reply_markup=cancel_btn())
async def cmd_excel(u, c):        _set_state(c, "excel");          await u.message.reply_text("📊 Send the PDF!", reply_markup=cancel_btn())
async def cmd_bgchange(u, c):                                       await u.message.reply_text("🎨 Choose background:", reply_markup=bg_color_menu())
async def cmd_handwrite(u, c):                                      await u.message.reply_text("✍️ Choose a font:", reply_markup=font_menu())
async def cmd_ocr(u, c):                                            await u.message.reply_text("🌐 Choose document language:", reply_markup=ocr_language_menu())
async def cmd_rotate(u, c):       _set_state(c, "rotate");         await u.message.reply_text("🔄 Send the PDF to rotate!", reply_markup=cancel_btn())
async def cmd_resize(u, c):       _set_state(c, "resize");         await u.message.reply_text("📏 Send the PDF to resize to A4!", reply_markup=cancel_btn())
async def cmd_addtext(u, c):      _set_state(c, "addtext");        await u.message.reply_text("📝 Send the PDF!", reply_markup=cancel_btn())
async def cmd_footer(u, c):       _set_state(c, "footer");         await u.message.reply_text("🗂️ Send the PDF!", reply_markup=cancel_btn())
async def cmd_extract(u, c):      _set_state(c, "extract");        await u.message.reply_text("🔖 Send the PDF!", reply_markup=cancel_btn())
async def cmd_metadata(u, c):     _set_state(c, "meta");           await u.message.reply_text("📋 Send the PDF!", reply_markup=cancel_btn())
async def cmd_pdf2word(u, c):     _set_state(c, "pdf2word");       await u.message.reply_text("📄 Send the PDF to convert to Word!", reply_markup=cancel_btn())
async def cmd_pdf2ppt(u, c):      _set_state(c, "pdf2ppt");        await u.message.reply_text("📊 Send the PDF to convert to PPT!", reply_markup=cancel_btn())
async def cmd_crop(u, c):         _set_state(c, "crop");           await u.message.reply_text("✂️ Send the PDF to crop margins!", reply_markup=cancel_btn())
async def cmd_qr(u, c):           _set_state(c, "qr");             await u.message.reply_text("🔲 Type text or URL for QR code:", reply_markup=cancel_btn())
async def cmd_delete_pages(u, c): _set_state(c, "delete_pages");   await u.message.reply_text("🗑️ Send the PDF to delete pages from!", reply_markup=cancel_btn())
async def cmd_reorder(u, c):      _set_state(c, "reorder");        await u.message.reply_text("🔀 Send the PDF to reorder pages!", reply_markup=cancel_btn())
async def cmd_lang(u, c):                                           await u.message.reply_text("🌍 Choose your language:", reply_markup=language_menu())
async def cmd_reverse(u, c):      _set_state(c, "reverse");        await u.message.reply_text("🔃 Send the PDF to reverse page order!", reply_markup=cancel_btn())
async def cmd_compare(u, c):      _set_state(c, "pdf_compare"); c.user_data["compare_files"] = []; await u.message.reply_text("🔍 Send the <b>first PDF</b>:", parse_mode="HTML", reply_markup=cancel_btn())
