"""
PDF feature handlers — state machine via ctx.user_data["state"]
All parse_mode switched to HTML. New features: rotate, resize, footer, addtext, metadata, extract.
"""
import io, random
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from utils.keyboards import (
    main_menu, back_btn, cancel_btn, font_menu, watermark_menu,
    page_no_style_menu, bg_color_menu, rotate_menu, back_btn
)
from utils import pdf_utils
from config import REACTIONS

# ── States ───────────────────────────────────────────────────────────────────
S = {
    "compress","split","merge","lock","lock_pass","unlock","unlock_pass",
    "watermark","wm_text","wm_logo_img","dark","pageno","excel","repair",
    "pdf2img","img2pdf","bg","hw_text","ocr","rotate","resize","addtext",
    "addtext_input","footer","footer_input","extract","extract_range","meta",
}

def _set_state(ctx, state, **kw):
    ctx.user_data["state"] = state
    ctx.user_data.update(kw)

def _clear(ctx):
    ctx.user_data.clear()

async def _react(update):
    try:
        from telegram import ReactionTypeEmoji
        await update.message.set_reaction([ReactionTypeEmoji(random.choice(REACTIONS))])
    except Exception:
        pass

async def _send_pdf(update, data: bytes, filename: str, caption: str = ""):
    size = pdf_utils.file_size_str(data)
    cap  = caption or f"✅ Done! <b>({size})</b>"
    await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap, parse_mode="HTML", reply_markup=main_menu()
    )

async def _send_file(update, data: bytes, filename: str, caption: str = ""):
    size = pdf_utils.file_size_str(data)
    cap  = caption or f"✅ Done! <b>({size})</b>"
    await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap, parse_mode="HTML", reply_markup=main_menu()
    )

async def _err(update, text: str):
    await update.effective_message.reply_text(
        f"❌ <b>Error:</b> {text}", parse_mode="HTML", reply_markup=back_btn()
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
        await q.message.edit_reply_markup(reply_markup=None)
        await q.message.reply_text(
            "🏠 <b>Main Menu</b> — Choose a tool:",
            parse_mode="HTML", reply_markup=main_menu()
        )
        return

    await q.answer()

    # Font selection
    if data.startswith("font_"):
        await _font_selected(update, ctx, data[5:])
        return

    # Rotation angles
    if data.startswith("rot_"):
        await _handle_rotate(update, ctx, data)
        return

    # Watermark
    if data in ("wm_text", "wm_logo", "wm_invisible"):
        wm_map = {"wm_text": "text", "wm_logo": "logo", "wm_invisible": "invisible"}
        _set_state(ctx, "watermark", wm_type=wm_map[data])
        await q.message.reply_text(
            "📎 <b>Send the PDF file first:</b>", parse_mode="HTML", reply_markup=cancel_btn()
        )
        return

    # Page number styles
    if data.startswith("pn_"):
        _set_state(ctx, "pageno", pn_style=data)
        await q.message.reply_text(
            "📎 <b>Now send the PDF file:</b>", parse_mode="HTML", reply_markup=cancel_btn()
        )
        return

    # BG colors
    if data.startswith("bg_"):
        _set_state(ctx, "bg", bg_color=data)
        await q.message.reply_text(
            "📎 <b>Now send the PDF file:</b>", parse_mode="HTML", reply_markup=cancel_btn()
        )
        return

    # Payment
    if data.startswith("buy_"):
        from handlers.premium_handler import buy_plan_callback
        await buy_plan_callback(update, ctx)
        return

    if data.startswith("pay_ss_"):
        from handlers.premium_handler import pay_screenshot_callback
        await pay_screenshot_callback(update, ctx)
        return

    # Menu routes
    routes = {
        "menu_compress":  (_prompt, "compress",  "📐 Compress PDF",      "Send the PDF to compress!"),
        "menu_split":     (_prompt, "split",      "✂️ Split PDF",          "Send the PDF to split into pages!"),
        "menu_merge":     (_prompt_merge, None, None, None),
        "menu_repair":    (_prompt, "repair",     "🧩 Repair PDF",        "Send the corrupted PDF!"),
        "menu_dark":      (_prompt, "dark",       "🌙 Dark Mode",         "Send the PDF to convert!"),
        "menu_excel":     (_prompt, "excel",      "📊 PDF → Excel",       "Send the PDF with tables!"),
        "menu_pdf2img":   (_prompt, "pdf2img",    "🖼️ PDF → Images",     "Send the PDF to convert!"),
        "menu_img2pdf":   (_prompt_img2pdf, None, None, None),
        "menu_watermark": (_menu_wm, None, None, None),
        "menu_bg":        (_menu_bg_color, None, None, None),
        "menu_pageno":    (_menu_pageno, None, None, None),
        "menu_rotate":    (_menu_rotate, None, None, None),
        "menu_resize":    (_prompt, "resize",     "📏 Resize to A4",      "Send the PDF to resize!"),
        "menu_hw":        (_menu_font, None, None, None),
        "menu_ocr":       (_prompt, "ocr",        "👁️ OCR Extract",      "Send an image or PDF!"),
        "menu_addtext":   (_prompt, "addtext",    "📝 Add Text to PDF",   "Send the PDF file!"),
        "menu_footer":    (_prompt, "footer",     "🗂️ Add Footer",        "Send the PDF file!"),
        "menu_extract":   (_prompt, "extract",    "🔖 Extract Pages",     "Send the PDF file!"),
        "menu_meta":      (_prompt, "meta",       "📋 PDF Metadata",      "Send the PDF file!"),
        "menu_account":   (_menu_account, None, None, None),
        "menu_premium":   (_menu_premium, None, None, None),
        "menu_help":      (_menu_help, None, None, None),
        "do_lock":        (_prompt, "lock",       "🔒 Lock PDF",          "Send the PDF to password-protect!"),
        "do_unlock":      (_prompt, "unlock",     "🔓 Unlock PDF",        "Send the locked PDF!"),
        "do_compress":    (_prompt, "compress",   "📐 Compress",          "Send the PDF to compress!"),
        "do_split":       (_prompt, "split",      "✂️ Split",              "Send the PDF to split!"),
        "do_merge":       (_prompt_merge, None, None, None),
        "do_pdf2img":     (_prompt, "pdf2img",    "🖼️ PDF→Images",       "Send the PDF!"),
        "do_excel":       (_prompt, "excel",      "📊 PDF→Excel",         "Send the PDF!"),
        "do_pageno":      (_menu_pageno, None, None, None),
    }

    handler_info = routes.get(data)
    if handler_info:
        fn = handler_info[0]
        if fn == _prompt:
            await _prompt(update, ctx, handler_info[1], handler_info[2], handler_info[3])
        else:
            await fn(update, ctx)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER PROMPT FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
async def _prompt(update, ctx, state, title, desc):
    _set_state(ctx, state)
    q = update.callback_query
    await q.message.reply_text(
        f"<b>{title}</b>\n\n📎 {desc}", parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _prompt_merge(update, ctx):
    _set_state(ctx, "merge")
    ctx.user_data["merge_files"] = []
    q = update.callback_query
    await q.message.reply_text(
        "🔗 <b>Merge PDFs</b>\n\nSend PDFs one by one.\nWhen done, send <code>/done</code>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _prompt_img2pdf(update, ctx):
    _set_state(ctx, "img2pdf")
    ctx.user_data["images"] = []
    q = update.callback_query
    await q.message.reply_text(
        "🖼️ <b>Images → PDF</b>\n\nSend images one by one.\nWhen done, send <code>/done</code>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _menu_wm(update, ctx):
    await update.callback_query.message.reply_text(
        "🌊 <b>Watermark Type:</b>", parse_mode="HTML", reply_markup=watermark_menu()
    )

async def _menu_bg_color(update, ctx):
    await update.callback_query.message.reply_text(
        "🎨 <b>Choose Background Theme:</b>", parse_mode="HTML", reply_markup=bg_color_menu()
    )

async def _menu_pageno(update, ctx):
    await update.callback_query.message.reply_text(
        "🔢 <b>Choose Page Number Style:</b>", parse_mode="HTML", reply_markup=page_no_style_menu()
    )

async def _menu_rotate(update, ctx):
    _set_state(ctx, "rotate")
    await update.callback_query.message.reply_text(
        "🔄 <b>Rotate PDF</b>\n\nFirst send the PDF file, then choose angle!",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _menu_font(update, ctx):
    await update.callback_query.message.reply_text(
        "✍️ <b>Choose Handwriting Font:</b>", parse_mode="HTML", reply_markup=font_menu()
    )

async def _font_selected(update, ctx, font_key):
    from config import FONTS
    font_name = FONTS.get(font_key, {}).get("name", "Unknown")
    _set_state(ctx, "hw_text", hw_font=font_key)
    await update.callback_query.message.reply_text(
        f"✅ Font: <b>{font_name}</b>\n\n✍️ Now <b>type your text</b> to convert to handwriting:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _handle_rotate(update, ctx, data):
    angle_map = {"rot_90r": 90, "rot_90l": -90, "rot_180": 180}
    if data == "rot_auto":
        ctx.user_data["rotate_angle"] = "auto"
    else:
        ctx.user_data["rotate_angle"] = angle_map.get(data, 90)
    await update.callback_query.message.reply_text(
        "📎 <b>Now send the PDF to rotate:</b>", parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _menu_account(update, ctx):
    from handlers.start_handler import account_cmd
    await account_cmd(update, ctx)

async def _menu_premium(update, ctx):
    from handlers.premium_handler import premium_cmd
    await premium_cmd(update, ctx)

async def _menu_help(update, ctx):
    from handlers.start_handler import help_cmd
    await help_cmd(update, ctx)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MESSAGE HANDLER
# ─────────────────────────────────────────────────────────────────────────────
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg   = update.message
    state = ctx.user_data.get("state")

    # Payment screenshot
    if msg.photo:
        from handlers.premium_handler import handle_payment_screenshot
        handled = await handle_payment_screenshot(update, ctx)
        if handled:
            return

    if not state:
        return

    # /done command
    if msg.text and msg.text.strip().lower() in ("/done", "done"):
        await _handle_done(update, ctx, state)
        return

    await _react(update)

    dispatch = {
        "compress":     _do_compress,
        "split":        _do_split,
        "merge":        _do_merge_collect,
        "lock":         _do_lock_pdf,
        "lock_pass":    _do_lock_pass,
        "unlock":       _do_unlock_pdf,
        "unlock_pass":  _do_unlock_pass,
        "watermark":    _do_watermark,
        "wm_text":      _do_wm_text,
        "wm_logo_img":  _do_wm_logo,
        "dark":         _do_dark,
        "pageno":       _do_pageno,
        "excel":        _do_excel,
        "repair":       _do_repair,
        "pdf2img":      _do_pdf2img,
        "img2pdf":      _do_img2pdf_collect,
        "bg":           _do_bg,
        "hw_text":      _do_handwrite,
        "ocr":          _do_ocr,
        "rotate":       _do_rotate_collect,
        "resize":       _do_resize,
        "addtext":      _do_addtext_pdf,
        "addtext_input":_do_addtext_input,
        "footer":       _do_footer_pdf,
        "footer_input": _do_footer_input,
        "extract":      _do_extract_pdf,
        "extract_range":_do_extract_range,
        "meta":         _do_meta,
    }

    fn = dispatch.get(state)
    if fn:
        await fn(update, ctx)


async def _handle_done(update, ctx, state):
    if state == "merge":
        files = ctx.user_data.get("merge_files", [])
        if len(files) < 2:
            await update.message.reply_text("⚠️ Send at least 2 PDFs!", reply_markup=cancel_btn())
            return
        mw = await update.message.reply_text("⏳ Merging PDFs...")
        try:
            result = pdf_utils.merge_pdfs(files)
            _clear(ctx)
            await mw.delete()
            await _send_pdf(update, result, "merged.pdf",
                            f"✅ <b>Merged {len(files)} PDFs!</b> ({pdf_utils.file_size_str(result)})")
        except Exception as e:
            await mw.delete(); await _err(update, str(e))

    elif state == "img2pdf":
        images = ctx.user_data.get("images", [])
        if not images:
            await update.message.reply_text("⚠️ Send at least 1 image!", reply_markup=cancel_btn())
            return
        mw = await update.message.reply_text("⏳ Converting images to PDF...")
        try:
            result = pdf_utils.images_to_pdf(images)
            _clear(ctx)
            await mw.delete()
            await _send_pdf(update, result, "images.pdf",
                            f"✅ <b>{len(images)} images → PDF!</b> ({pdf_utils.file_size_str(result)})")
        except Exception as e:
            await mw.delete(); await _err(update, str(e))


# ── Operations ───────────────────────────────────────────────────────────────

async def _do_compress(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    orig = pdf_utils.file_size_str(data)
    mw = await update.message.reply_text("⏳ Compressing PDF... trying multiple strategies!")
    try:
        result = pdf_utils.compress_pdf(data)
        new_s  = pdf_utils.file_size_str(result)
        saved  = round((1 - len(result)/len(data)) * 100, 1)
        _clear(ctx)
        await mw.delete()
        cap = (f"📐 <b>Compression Complete!</b>\n\n"
               f"📊 Before: <code>{orig}</code>\n"
               f"📉 After:  <code>{new_s}</code>\n"
               f"💾 Saved:  <b>{saved}%</b>")
        await _send_pdf(update, result, "compressed.pdf", cap)
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_split(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    mw = await update.message.reply_text("⏳ Splitting PDF pages...")
    try:
        pages = pdf_utils.split_pdf_all(data)
        _clear(ctx)
        await mw.delete()
        send_n = min(len(pages), 20)
        for i, pd in enumerate(pages[:send_n], 1):
            await update.message.reply_document(
                document=InputFile(io.BytesIO(pd), filename=f"page_{i:02d}.pdf"),
                caption=f"📄 Page {i} / {len(pages)}"
            )
        note = f" ⚠️ First 20 shown (total: {len(pages)})" if len(pages) > 20 else ""
        await update.message.reply_text(
            f"✅ <b>Split complete!</b>{note}", parse_mode="HTML", reply_markup=main_menu()
        )
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_merge_collect(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["merge_files"].append(data)
    n = len(ctx.user_data["merge_files"])
    await update.message.reply_text(
        f"✅ PDF <b>#{n}</b> received! Send more or <code>/done</code> to merge.",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_lock_pdf(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["lock_pdf"] = data
    _set_state(ctx, "lock_pass")
    await update.message.reply_text(
        "🔒 PDF received! Now <b>type a password</b>:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_lock_pass(update, ctx):
    if not update.message.text: return
    password = update.message.text.strip()
    mw = await update.message.reply_text("⏳ Locking PDF...")
    try:
        result = pdf_utils.lock_pdf(ctx.user_data["lock_pdf"], password)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "locked.pdf",
                        f"🔒 <b>PDF locked!</b>\n🔑 Password: <code>{password}</code>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_unlock_pdf(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["unlock_pdf"] = data
    _set_state(ctx, "unlock_pass")
    await update.message.reply_text(
        "🔑 PDF received! <b>Type the password</b> (or type a dot <code>.</code> if none):",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_unlock_pass(update, ctx):
    if not update.message.text: return
    password = update.message.text.strip()
    if password == ".": password = ""
    mw = await update.message.reply_text("⏳ Unlocking PDF...")
    try:
        result = pdf_utils.unlock_pdf(ctx.user_data["unlock_pdf"], password)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "unlocked.pdf", "🔓 <b>PDF unlocked!</b> Password removed.")
    except ValueError as e:
        await mw.delete(); await _err(update, str(e))
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_watermark(update, ctx):
    wm_type = ctx.user_data.get("wm_type", "text")
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["wm_pdf"] = data
    if wm_type == "logo":
        _set_state(ctx, "wm_logo_img", wm_type="logo", wm_pdf=data)
        await update.message.reply_text(
            "🖼️ <b>Now send your logo/image:</b>", parse_mode="HTML", reply_markup=cancel_btn()
        )
    else:
        _set_state(ctx, "wm_text", wm_type=wm_type, wm_pdf=data)
        label = "Invisible watermark" if wm_type == "invisible" else "Watermark"
        await update.message.reply_text(
            f"📝 <b>Type the {label} text:</b>", parse_mode="HTML", reply_markup=cancel_btn()
        )

async def _do_wm_text(update, ctx):
    if not update.message.text: return
    text = update.message.text.strip()
    invisible = ctx.user_data.get("wm_type") == "invisible"
    mw = await update.message.reply_text("⏳ Adding watermark...")
    try:
        result = pdf_utils.watermark_text(ctx.user_data["wm_pdf"], text, invisible=invisible)
        _clear(ctx)
        await mw.delete()
        icon = "👻" if invisible else "🌊"
        await _send_pdf(update, result, "watermarked.pdf",
                        f"{icon} <b>Watermark added!</b>\nText: <code>{text}</code>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_wm_logo(update, ctx):
    img_data = None
    if update.message.photo:
        f = await update.message.photo[-1].get_file()
        img_data = bytes(await f.download_as_bytearray())
    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        f = await update.message.document.get_file()
        img_data = bytes(await f.download_as_bytearray())
    if not img_data:
        await update.message.reply_text("⚠️ Send an image!", reply_markup=cancel_btn())
        return
    mw = await update.message.reply_text("⏳ Adding logo watermark...")
    try:
        result = pdf_utils.watermark_image(ctx.user_data["wm_pdf"], img_data)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "watermarked.pdf", "🖼️ <b>Logo watermark added!</b>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_dark(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    mw = await update.message.reply_text("⏳ Converting to dark mode... (may take a moment ⏱️)")
    try:
        result = pdf_utils.change_bg(data, "bg_dark")
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "dark_mode.pdf", "🌙 <b>Dark Mode PDF ready!</b>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_pageno(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    style = ctx.user_data.get("pn_style", "pn_arabic")
    mw = await update.message.reply_text("⏳ Adding page numbers...")
    try:
        result = pdf_utils.add_page_numbers(data, style)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "numbered.pdf", "🔢 <b>Page numbers added!</b>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_excel(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    mw = await update.message.reply_text("⏳ Extracting tables and converting to Excel...")
    try:
        result = pdf_utils.pdf_to_excel(data)
        _clear(ctx)
        await mw.delete()
        await _send_file(update, result, "extracted.xlsx", "📊 <b>PDF → Excel done!</b>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_repair(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    mw = await update.message.reply_text("⏳ Attempting PDF repair... 🧩")
    try:
        result = pdf_utils.repair_pdf(data)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "repaired.pdf", "🧩 <b>PDF repaired!</b>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_pdf2img(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    mw = await update.message.reply_text("⏳ Converting PDF to images...")
    try:
        images = pdf_utils.pdf_to_images(data)
        _clear(ctx)
        await mw.delete()
        for i, img in enumerate(images[:15], 1):
            await update.message.reply_photo(photo=io.BytesIO(img), caption=f"🖼️ Page {i}/{len(images)}")
        note = f" (first 15 of {len(images)})" if len(images) > 15 else ""
        await update.message.reply_text(
            f"✅ <b>Converted{note}!</b>", parse_mode="HTML", reply_markup=main_menu()
        )
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_img2pdf_collect(update, ctx):
    img_data = None
    if update.message.photo:
        f = await update.message.photo[-1].get_file()
        img_data = bytes(await f.download_as_bytearray())
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith("image/"):
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
    data = await _get_pdf(update)
    if not data: return
    color = ctx.user_data.get("bg_color", "bg_dark")
    mw = await update.message.reply_text("⏳ Applying background theme... ⏱️")
    try:
        result = pdf_utils.change_bg(data, color)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "bg_changed.pdf", "🎨 <b>Background applied!</b>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_handwrite(update, ctx):
    if not update.message.text:
        await update.message.reply_text("⚠️ Please type your text!", reply_markup=cancel_btn())
        return
    text     = update.message.text.strip()
    font_key = ctx.user_data.get("hw_font", "caveat")
    from config import FONTS
    font_name = FONTS.get(font_key, {}).get("name", "Default")
    mw = await update.message.reply_text(f"⏳ Creating handwritten PDF with {font_name}...")
    try:
        result = pdf_utils.create_handwritten_pdf(text, font_key)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "handwritten.pdf",
                        f"✍️ <b>Handwritten PDF!</b>\nFont: {font_name}")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_ocr(update, ctx):
    mw = await update.message.reply_text("⏳ Extracting text with OCR... 👁️")
    try:
        data = None
        if update.message.photo:
            f    = await update.message.photo[-1].get_file()
            data = bytes(await f.download_as_bytearray())
            text = pdf_utils.ocr_image(data)
        elif update.message.document:
            f    = await update.message.document.get_file()
            data = bytes(await f.download_as_bytearray())
            if update.message.document.mime_type == "application/pdf":
                text = pdf_utils.ocr_pdf(data)
            else:
                text = pdf_utils.ocr_image(data)
        else:
            await mw.delete()
            await update.message.reply_text("⚠️ Send an image or PDF!", reply_markup=cancel_btn())
            return

        _clear(ctx)
        await mw.delete()

        if len(text) > 3800:
            await update.message.reply_document(
                document=InputFile(io.BytesIO(text.encode("utf-8")), filename="extracted.txt"),
                caption="👁️ <b>OCR Complete!</b> Text saved to file.",
                parse_mode="HTML", reply_markup=main_menu()
            )
        else:
            await update.message.reply_text(
                f"👁️ <b>Extracted Text:</b>\n\n<pre>{text}</pre>",
                parse_mode="HTML", reply_markup=main_menu()
            )
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_rotate_collect(update, ctx):
    # If no angle set yet, show rotate menu
    if "rotate_angle" not in ctx.user_data:
        data = await _get_pdf(update)
        if not data: return
        ctx.user_data["rotate_pdf"] = data
        await update.message.reply_text(
            "🔄 <b>Choose rotation angle:</b>", parse_mode="HTML", reply_markup=rotate_menu()
        )
        return
    # Angle already set, process
    data = ctx.user_data.get("rotate_pdf") or await _get_pdf(update)
    if not data: return
    angle = ctx.user_data.get("rotate_angle", 90)
    mw = await update.message.reply_text("⏳ Rotating PDF...")
    try:
        if angle == "auto":
            result = pdf_utils.auto_rotate_pdf(data)
        else:
            result = pdf_utils.rotate_pdf(data, angle)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "rotated.pdf", f"🔄 <b>PDF rotated!</b>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_resize(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    mw = await update.message.reply_text("⏳ Resizing to A4...")
    try:
        result = pdf_utils.resize_pdf_to_a4(data)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "a4_resized.pdf", "📏 <b>Resized to A4!</b>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_addtext_pdf(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["addtext_pdf"] = data
    _set_state(ctx, "addtext_input", addtext_pdf=data)
    await update.message.reply_text(
        "📝 <b>PDF received!</b>\n\nNow type the text you want to add:\n"
        "<i>(It will be added to the first page at top)</i>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_addtext_input(update, ctx):
    if not update.message.text: return
    text = update.message.text.strip()
    mw = await update.message.reply_text("⏳ Adding text to PDF...")
    try:
        result = pdf_utils.add_text_to_pdf(ctx.user_data["addtext_pdf"], text)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "text_added.pdf", "📝 <b>Text added to PDF!</b>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_footer_pdf(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    ctx.user_data["footer_pdf"] = data
    _set_state(ctx, "footer_input", footer_pdf=data)
    await update.message.reply_text(
        "🗂️ <b>PDF received!</b>\n\nType the <b>footer text</b> to add to all pages:",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_footer_input(update, ctx):
    if not update.message.text: return
    text = update.message.text.strip()
    mw = await update.message.reply_text("⏳ Adding footer...")
    try:
        result = pdf_utils.add_footer(ctx.user_data["footer_pdf"], text)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "footer_added.pdf", f"🗂️ <b>Footer added!</b>\nText: <code>{text}</code>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_extract_pdf(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    import fitz
    with fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
    ctx.user_data["extract_pdf"] = data
    _set_state(ctx, "extract_range", extract_pdf=data)
    await update.message.reply_text(
        f"🔖 <b>PDF has {total} pages.</b>\n\n"
        f"Type the page range to extract:\n"
        f"  • Single: <code>3</code>\n"
        f"  • Range: <code>2-5</code>\n"
        f"  • Multiple: <code>1,3,5-7</code>",
        parse_mode="HTML", reply_markup=cancel_btn()
    )

async def _do_extract_range(update, ctx):
    if not update.message.text: return
    page_range = update.message.text.strip()
    mw = await update.message.reply_text("⏳ Extracting pages...")
    try:
        result = pdf_utils.extract_pages(ctx.user_data["extract_pdf"], page_range)
        _clear(ctx)
        await mw.delete()
        await _send_pdf(update, result, "extracted_pages.pdf",
                        f"🔖 <b>Pages extracted!</b>\nRange: <code>{page_range}</code>")
    except Exception as e:
        await mw.delete(); await _err(update, str(e))

async def _do_meta(update, ctx):
    data = await _get_pdf(update)
    if not data: return
    mw = await update.message.reply_text("⏳ Reading PDF metadata...")
    try:
        meta = pdf_utils.get_metadata(data)
        _clear(ctx)
        await mw.delete()
        text = (
            "📋 <b>PDF Metadata</b>\n\n"
            f"╔══════════════════════╗\n"
            f"║ 📄 <b>Title:</b>   {meta['title']}\n"
            f"║ 👤 <b>Author:</b>  {meta['author']}\n"
            f"║ 📝 <b>Subject:</b> {meta['subject']}\n"
            f"║ 🛠️ <b>Creator:</b> {meta['creator']}\n"
            f"╠══════════════════════╣\n"
            f"║ 📑 <b>Pages:</b>   {meta['pages']}\n"
            f"║ 📦 <b>Size:</b>    {meta['size']}\n"
            f"║ 🔐 <b>Encrypted:</b> {'Yes' if meta['encrypted'] else 'No'}\n"
            f"╚══════════════════════╝"
        )
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_menu())
    except Exception as e:
        await mw.delete(); await _err(update, str(e))


# ── Direct command handlers ───────────────────────────────────────────────────
async def cmd_compress(u, c):  _set_state(c, "compress");     await u.message.reply_text("📐 Send the PDF to compress!", reply_markup=cancel_btn())
async def cmd_split(u, c):     _set_state(c, "split");        await u.message.reply_text("✂️ Send the PDF to split!", reply_markup=cancel_btn())
async def cmd_merge(u, c):     _set_state(c, "merge"); c.user_data["merge_files"] = []; await u.message.reply_text("🔗 Send PDFs one by one, then /done", reply_markup=cancel_btn())
async def cmd_lock(u, c):      _set_state(c, "lock");         await u.message.reply_text("🔒 Send the PDF to lock!", reply_markup=cancel_btn())
async def cmd_unlock(u, c):    _set_state(c, "unlock");       await u.message.reply_text("🔓 Send the locked PDF!", reply_markup=cancel_btn())
async def cmd_repair(u, c):    _set_state(c, "repair");       await u.message.reply_text("🧩 Send the corrupted PDF!", reply_markup=cancel_btn())
async def cmd_watermark(u, c):                                 await u.message.reply_text("🌊 Choose watermark type:", reply_markup=watermark_menu())
async def cmd_darkmode(u, c):  _set_state(c, "dark");         await u.message.reply_text("🌙 Send the PDF!", reply_markup=cancel_btn())
async def cmd_pagenos(u, c):                                   await u.message.reply_text("🔢 Choose style:", reply_markup=page_no_style_menu())
async def cmd_pdf2img(u, c):   _set_state(c, "pdf2img");      await u.message.reply_text("🖼️ Send the PDF!", reply_markup=cancel_btn())
async def cmd_img2pdf(u, c):   _set_state(c, "img2pdf"); c.user_data["images"] = []; await u.message.reply_text("🖼️ Send images, then /done", reply_markup=cancel_btn())
async def cmd_excel(u, c):     _set_state(c, "excel");        await u.message.reply_text("📊 Send the PDF!", reply_markup=cancel_btn())
async def cmd_bgchange(u, c):                                  await u.message.reply_text("🎨 Choose background:", reply_markup=bg_color_menu())
async def cmd_handwrite(u, c):                                 await u.message.reply_text("✍️ Choose a font:", reply_markup=font_menu())
async def cmd_ocr(u, c):       _set_state(c, "ocr");          await u.message.reply_text("👁️ Send image or PDF!", reply_markup=cancel_btn())
async def cmd_rotate(u, c):    _set_state(c, "rotate");       await u.message.reply_text("🔄 Send the PDF to rotate!", reply_markup=cancel_btn())
async def cmd_resize(u, c):    _set_state(c, "resize");       await u.message.reply_text("📏 Send the PDF to resize to A4!", reply_markup=cancel_btn())
async def cmd_addtext(u, c):   _set_state(c, "addtext");      await u.message.reply_text("📝 Send the PDF!", reply_markup=cancel_btn())
async def cmd_footer(u, c):    _set_state(c, "footer");       await u.message.reply_text("🗂️ Send the PDF!", reply_markup=cancel_btn())
async def cmd_extract(u, c):   _set_state(c, "extract");      await u.message.reply_text("🔖 Send the PDF!", reply_markup=cancel_btn())
async def cmd_metadata(u, c):  _set_state(c, "meta");         await u.message.reply_text("📋 Send the PDF!", reply_markup=cancel_btn())
