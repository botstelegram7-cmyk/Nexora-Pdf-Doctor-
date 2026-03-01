"""
PDF feature handlers — all operations in one place.
State machine via ctx.user_data["state"]
"""
import io, random
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from utils.keyboards import (
    main_menu, back_btn, cancel_btn, font_menu, watermark_menu,
    lock_menu, page_no_style_menu, bg_color_menu
)
from utils.decorators import pdf_feature
from utils import pdf_utils
from config import REACTIONS

# ── State constants ─────────────────────────────────────────────────────────
S_COMPRESS     = "compress"
S_SPLIT        = "split"
S_SPLIT_RANGE  = "split_range"
S_MERGE        = "merge"
S_MERGE_WAIT   = "merge_wait"
S_LOCK         = "lock"
S_LOCK_PASS    = "lock_pass"
S_UNLOCK       = "unlock"
S_UNLOCK_PASS  = "unlock_pass"
S_WATERMARK    = "watermark"
S_WM_TEXT      = "wm_text"
S_WM_LOGO_PDF  = "wm_logo_pdf"
S_WM_LOGO_IMG  = "wm_logo_img"
S_DARK         = "dark"
S_DARK_COLOR   = "dark_color"
S_PAGENO       = "pageno"
S_PAGENO_STYLE = "pageno_style"
S_PDF2IMG      = "pdf2img"
S_IMG2PDF      = "img2pdf"
S_EXCEL        = "excel"
S_REPAIR       = "repair"
S_BG           = "bg"
S_BG_COLOR     = "bg_color"
S_HANDWRITE    = "handwrite"
S_HW_FONT      = "hw_font"
S_HW_TEXT      = "hw_text"
S_OCR          = "ocr"


# ────────────────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────────────────
def _set_state(ctx, state, **kwargs):
    ctx.user_data["state"] = state
    ctx.user_data.update(kwargs)

def _clear_state(ctx):
    ctx.user_data.clear()

async def _react(update):
    try:
        from telegram import ReactionTypeEmoji
        await update.message.set_reaction([ReactionTypeEmoji(random.choice(REACTIONS))])
    except Exception:
        pass

async def _send_pdf(update, data: bytes, filename: str, caption: str = ""):
    size = pdf_utils.file_size_str(data)
    cap = caption or f"✅ Done! ({size})"
    await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

async def _send_file(update, data: bytes, filename: str, caption: str = ""):
    size = pdf_utils.file_size_str(data)
    cap = caption or f"✅ Done! ({size})"
    await update.effective_message.reply_document(
        document=InputFile(io.BytesIO(data), filename=filename),
        caption=cap,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

async def _error_reply(update, text: str):
    await update.effective_message.reply_text(
        f"❌ **Error:** {text}", parse_mode="Markdown", reply_markup=back_btn()
    )


# ────────────────────────────────────────────────────────────────────────────
# MENU CALLBACKS
# ────────────────────────────────────────────────────────────────────────────
async def menu_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data  = query.data
    await query.answer()

    # Back to main
    if data == "back_main":
        _clear_state(ctx)
        await query.message.edit_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "🏠 **Main Menu** — Choose a tool:", parse_mode="Markdown", reply_markup=main_menu()
        )
        return

    # Route menus
    handlers = {
        "menu_pdf":       _menu_pdf,
        "menu_ocr":       _menu_ocr,
        "menu_hw":        _menu_hw,
        "menu_lock":      _menu_lock,
        "menu_watermark": _menu_wm,
        "menu_dark":      _menu_dark,
        "menu_excel":     _menu_excel,
        "menu_pageno":    _menu_pageno,
        "menu_repair":    _menu_repair,
        "menu_compress":  _menu_compress,
        "menu_split":     _menu_split,
        "menu_merge":     _menu_merge,
        "menu_pdf2img":   _menu_pdf2img,
        "menu_img2pdf":   _menu_img2pdf,
        "menu_bg":        _menu_bg,
        "menu_addpass":   _menu_lock,
        "menu_account":   _menu_account,
        "menu_premium":   _menu_premium,
        "menu_help":      _menu_help,
        # do_ direct actions
        "do_compress":    _menu_compress,
        "do_split":       _menu_split,
        "do_merge":       _menu_merge,
        "do_pdf2img":     _menu_pdf2img,
        "do_excel":       _menu_excel,
        "do_pageno":      _menu_pageno,
        # lock
        "do_lock":        _menu_addpass,
        "do_unlock":      _menu_unlock,
        # watermark subs
        "wm_text":        _wm_text_prompt,
        "wm_logo":        _wm_logo_prompt,
        "wm_invisible":   _wm_invisible_prompt,
        # page number styles
        "pn_arabic":      lambda u, c: _set_pageno_style(u, c, "pn_arabic"),
        "pn_roman":       lambda u, c: _set_pageno_style(u, c, "pn_roman"),
        "pn_total":       lambda u, c: _set_pageno_style(u, c, "pn_total"),
        "pn_dash":        lambda u, c: _set_pageno_style(u, c, "pn_dash"),
        # bg colors
        "bg_dark":        lambda u, c: _set_bg_color(u, c, "bg_dark"),
        "bg_navy":        lambda u, c: _set_bg_color(u, c, "bg_navy"),
        "bg_green":       lambda u, c: _set_bg_color(u, c, "bg_green"),
        "bg_purple":      lambda u, c: _set_bg_color(u, c, "bg_purple"),
        "bg_cream":       lambda u, c: _set_bg_color(u, c, "bg_cream"),
        "bg_red":         lambda u, c: _set_bg_color(u, c, "bg_red"),
    }

    # Font selection
    if data.startswith("font_"):
        await _font_selected(update, ctx, data.replace("font_", ""))
        return

    fn = handlers.get(data)
    if fn:
        await fn(update, ctx)


# ── Sub menu prompts ─────────────────────────────────────────────────────────
async def _menu_compress(update, ctx):
    _set_state(ctx, S_COMPRESS)
    q = update.callback_query
    await q.message.reply_text(
        "📐 **Compress PDF**\n\nSend me the PDF file to compress! 📎",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_split(update, ctx):
    _set_state(ctx, S_SPLIT)
    q = update.callback_query
    await q.message.reply_text(
        "✂️ **Split PDF**\n\nSend me the PDF file! I'll split every page separately.",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_merge(update, ctx):
    _set_state(ctx, S_MERGE)
    ctx.user_data["merge_files"] = []
    q = update.callback_query
    await q.message.reply_text(
        "🔗 **Merge PDFs**\n\nSend PDFs one by one. When done, send `/done`.",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_lock(update, ctx):
    _set_state(ctx, S_LOCK)
    q = update.callback_query
    await q.message.reply_text(
        "🔒 **Lock PDF** (Add Password)\n\nSend me the PDF to lock!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_addpass(update, ctx):
    await _menu_lock(update, ctx)

async def _menu_unlock(update, ctx):
    _set_state(ctx, S_UNLOCK)
    q = update.callback_query
    await q.message.reply_text(
        "🔓 **Unlock PDF** (Remove Password)\n\nSend me the locked PDF!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_wm(update, ctx):
    q = update.callback_query
    await q.message.reply_text(
        "🌊 **Watermark**\n\nChoose watermark type:",
        parse_mode="Markdown", reply_markup=watermark_menu()
    )

async def _wm_text_prompt(update, ctx):
    _set_state(ctx, S_WATERMARK, wm_type="text")
    q = update.callback_query
    await q.message.reply_text(
        "📝 **Text Watermark**\n\nFirst, send the PDF file!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _wm_logo_prompt(update, ctx):
    _set_state(ctx, S_WATERMARK, wm_type="logo")
    q = update.callback_query
    await q.message.reply_text(
        "🖼️ **Logo Watermark**\n\nFirst, send the PDF file!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _wm_invisible_prompt(update, ctx):
    _set_state(ctx, S_WATERMARK, wm_type="invisible")
    q = update.callback_query
    await q.message.reply_text(
        "👻 **Invisible Watermark**\n\nFirst, send the PDF file!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_dark(update, ctx):
    _set_state(ctx, S_DARK)
    q = update.callback_query
    await q.message.reply_text(
        "🌙 **Dark Mode PDF**\n\nSend me the PDF!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_excel(update, ctx):
    _set_state(ctx, S_EXCEL)
    q = update.callback_query
    await q.message.reply_text(
        "📊 **PDF → Excel**\n\nSend me the PDF with tables!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_pageno(update, ctx):
    q = update.callback_query
    await q.message.reply_text(
        "🔢 **Add Page Numbers**\n\nChoose a page number style:",
        parse_mode="Markdown", reply_markup=page_no_style_menu()
    )

async def _set_pageno_style(update, ctx, style):
    _set_state(ctx, S_PAGENO, pn_style=style)
    q = update.callback_query
    await q.message.reply_text(
        "🔢 **Add Page Numbers**\n\nNow send me the PDF file!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_repair(update, ctx):
    _set_state(ctx, S_REPAIR)
    q = update.callback_query
    await q.message.reply_text(
        "🧩 **Repair PDF**\n\nSend me the corrupted PDF!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_pdf2img(update, ctx):
    _set_state(ctx, S_PDF2IMG)
    q = update.callback_query
    await q.message.reply_text(
        "🖼️ **PDF → Images**\n\nSend me the PDF!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_img2pdf(update, ctx):
    _set_state(ctx, S_IMG2PDF)
    ctx.user_data["images"] = []
    q = update.callback_query
    await q.message.reply_text(
        "🖼️ **Images → PDF**\n\nSend images one by one. When done, send `/done`.",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_bg(update, ctx):
    q = update.callback_query
    await q.message.reply_text(
        "🎨 **Background Changer**\n\nChoose a background color/theme:",
        parse_mode="Markdown", reply_markup=bg_color_menu()
    )

async def _set_bg_color(update, ctx, color):
    _set_state(ctx, S_BG, bg_color=color)
    q = update.callback_query
    await q.message.reply_text(
        "🎨 **Background Changer**\n\nNow send me the PDF file!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_hw(update, ctx):
    q = update.callback_query
    await q.message.reply_text(
        "✍️ **Handwritten Style PDF**\n\nChoose a font:",
        parse_mode="Markdown", reply_markup=font_menu()
    )

async def _font_selected(update, ctx, font_key):
    _set_state(ctx, S_HW_TEXT, hw_font=font_key)
    q = update.callback_query
    from config import FONTS
    font_name = FONTS.get(font_key, {}).get("name", "Unknown")
    await q.message.reply_text(
        f"✍️ Font selected: **{font_name}**\n\n"
        f"Now type the text you want to convert to handwriting:",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_ocr(update, ctx):
    _set_state(ctx, S_OCR)
    q = update.callback_query
    await q.message.reply_text(
        "🔍 **OCR — Extract Text**\n\nSend me an image or PDF to extract text from!",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _menu_account(update, ctx):
    from handlers.start_handler import account_cmd
    await account_cmd(update, ctx)

async def _menu_premium(update, ctx):
    from handlers.premium_handler import premium_cmd
    await premium_cmd(update, ctx)

async def _menu_pdf(update, ctx):
    q = update.callback_query
    from utils.keyboards import pdf_tools_menu
    await q.message.reply_text(
        "📄 **PDF Tools**\n\nChoose an operation:",
        parse_mode="Markdown", reply_markup=pdf_tools_menu()
    )

async def _menu_help(update, ctx):
    from handlers.start_handler import help_cmd
    await help_cmd(update, ctx)


# ────────────────────────────────────────────────────────────────────────────
# MESSAGE HANDLER — routes based on state
# ────────────────────────────────────────────────────────────────────────────
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Main message dispatcher"""
    msg   = update.message
    state = ctx.user_data.get("state")

    # Payment screenshot check (before state check)
    if msg.photo:
        from handlers.premium_handler import handle_payment_screenshot
        handled = await handle_payment_screenshot(update, ctx)
        if handled:
            return

    if not state:
        return  # Ignore random messages

    # /done command for multi-file ops
    if msg.text and msg.text.strip().lower() in ("/done", "done"):
        await _handle_done(update, ctx, state)
        return

    # Route by state
    await _react(update)

    if state == S_COMPRESS:          await _do_compress(update, ctx)
    elif state == S_SPLIT:           await _do_split(update, ctx)
    elif state == S_MERGE:           await _do_merge_collect(update, ctx)
    elif state == S_LOCK:            await _do_lock_pdf(update, ctx)
    elif state == S_LOCK_PASS:       await _do_lock_setpass(update, ctx)
    elif state == S_UNLOCK:          await _do_unlock_pdf(update, ctx)
    elif state == S_UNLOCK_PASS:     await _do_unlock_setpass(update, ctx)
    elif state == S_WATERMARK:       await _do_watermark(update, ctx)
    elif state == S_WM_TEXT:         await _do_wm_text(update, ctx)
    elif state == S_WM_LOGO_IMG:     await _do_wm_logo(update, ctx)
    elif state == S_DARK:            await _do_dark(update, ctx)
    elif state == S_PAGENO:          await _do_pageno(update, ctx)
    elif state == S_EXCEL:           await _do_excel(update, ctx)
    elif state == S_REPAIR:          await _do_repair(update, ctx)
    elif state == S_PDF2IMG:         await _do_pdf2img(update, ctx)
    elif state == S_IMG2PDF:         await _do_img2pdf_collect(update, ctx)
    elif state == S_BG:              await _do_bg(update, ctx)
    elif state == S_HW_TEXT:         await _do_handwrite(update, ctx)
    elif state == S_OCR:             await _do_ocr(update, ctx)


async def _handle_done(update, ctx, state):
    if state == S_MERGE:
        files = ctx.user_data.get("merge_files", [])
        if len(files) < 2:
            await update.message.reply_text("⚠️ Send at least 2 PDF files!", reply_markup=cancel_btn())
            return
        msg_w = await update.message.reply_text("⏳ Merging PDFs...")
        try:
            result = pdf_utils.merge_pdfs(files)
            _clear_state(ctx)
            await msg_w.delete()
            await _send_pdf(update, result, "merged.pdf", f"✅ **Merged {len(files)} PDFs!** ({pdf_utils.file_size_str(result)})")
        except Exception as e:
            await msg_w.delete()
            await _error_reply(update, str(e))

    elif state == S_IMG2PDF:
        images = ctx.user_data.get("images", [])
        if not images:
            await update.message.reply_text("⚠️ Send at least 1 image!", reply_markup=cancel_btn())
            return
        msg_w = await update.message.reply_text("⏳ Converting images to PDF...")
        try:
            result = pdf_utils.images_to_pdf(images)
            _clear_state(ctx)
            await msg_w.delete()
            await _send_pdf(update, result, "images.pdf", f"✅ **{len(images)} images → PDF!** ({pdf_utils.file_size_str(result)})")
        except Exception as e:
            await msg_w.delete()
            await _error_reply(update, str(e))


# ────────────────────────────────────────────────────────────────────────────
# OPERATIONS
# ────────────────────────────────────────────────────────────────────────────
async def _get_pdf_bytes(update) -> bytes | None:
    msg = update.message
    if msg.document and msg.document.mime_type == "application/pdf":
        f = await msg.document.get_file()
        return await f.download_as_bytearray()
    await update.message.reply_text("⚠️ Please send a **PDF file**!", parse_mode="Markdown")
    return None

async def _do_compress(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    orig_size = pdf_utils.file_size_str(bytes(data))
    msg_w = await update.message.reply_text("⏳ Compressing PDF...")
    try:
        result = pdf_utils.compress_pdf(bytes(data))
        new_size = pdf_utils.file_size_str(result)
        _clear_state(ctx)
        await msg_w.delete()
        await _send_pdf(update, result, "compressed.pdf",
                        f"✅ **Compressed!**\n📊 Before: {orig_size} → After: {new_size}")
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_split(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    msg_w = await update.message.reply_text("⏳ Splitting PDF... All pages will be sent!")
    try:
        pages = pdf_utils.split_pdf_all(bytes(data))
        _clear_state(ctx)
        await msg_w.delete()
        if len(pages) > 20:
            await update.message.reply_text(
                f"⚠️ PDF has {len(pages)} pages. Sending first 20 to avoid spam.",
                reply_markup=back_btn()
            )
            pages = pages[:20]
        for i, page_data in enumerate(pages, 1):
            await update.message.reply_document(
                document=InputFile(io.BytesIO(page_data), filename=f"page_{i}.pdf"),
                caption=f"📄 Page {i}/{len(pages)}"
            )
        await update.message.reply_text("✅ **All pages sent!**", parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_merge_collect(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    ctx.user_data["merge_files"].append(bytes(data))
    count = len(ctx.user_data["merge_files"])
    await update.message.reply_text(
        f"✅ PDF #{count} received! Send more or send `/done` to merge.",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _do_lock_pdf(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    ctx.user_data["lock_pdf"] = bytes(data)
    _set_state(ctx, S_LOCK_PASS, **{k: v for k, v in ctx.user_data.items() if k != "state"})
    await update.message.reply_text(
        "🔒 Now **type a password** to lock this PDF:",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _do_lock_setpass(update, ctx):
    password = update.message.text.strip()
    if not password:
        await update.message.reply_text("⚠️ Please enter a valid password!")
        return
    msg_w = await update.message.reply_text("⏳ Locking PDF...")
    try:
        result = pdf_utils.lock_pdf(ctx.user_data["lock_pdf"], password)
        _clear_state(ctx)
        await msg_w.delete()
        await _send_pdf(update, result, "locked.pdf", f"🔒 **PDF locked!** Password: `{password}`")
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_unlock_pdf(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    ctx.user_data["unlock_pdf"] = bytes(data)
    _set_state(ctx, S_UNLOCK_PASS, **{k: v for k, v in ctx.user_data.items() if k != "state"})
    await update.message.reply_text(
        "🔑 **Type the PDF password** (leave empty if no password):",
        parse_mode="Markdown", reply_markup=cancel_btn()
    )

async def _do_unlock_setpass(update, ctx):
    password = update.message.text.strip()
    msg_w = await update.message.reply_text("⏳ Unlocking PDF...")
    try:
        result = pdf_utils.unlock_pdf(ctx.user_data["unlock_pdf"], password)
        _clear_state(ctx)
        await msg_w.delete()
        await _send_pdf(update, result, "unlocked.pdf", "🔓 **PDF unlocked!** Password removed.")
    except ValueError as e:
        await msg_w.delete()
        await _error_reply(update, str(e))
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_watermark(update, ctx):
    wm_type = ctx.user_data.get("wm_type", "text")
    data = await _get_pdf_bytes(update)
    if not data:
        return
    ctx.user_data["wm_pdf"] = bytes(data)

    if wm_type == "text":
        _set_state(ctx, S_WM_TEXT, **{k: v for k, v in ctx.user_data.items() if k != "state"})
        await update.message.reply_text(
            "📝 **Type the watermark text:**", parse_mode="Markdown", reply_markup=cancel_btn()
        )
    elif wm_type == "logo":
        _set_state(ctx, S_WM_LOGO_PDF, **{k: v for k, v in ctx.user_data.items() if k != "state"})
        _set_state(ctx, S_WM_LOGO_IMG, **{k: v for k, v in ctx.user_data.items() if k != "state"})
        await update.message.reply_text(
            "🖼️ **Now send the logo image:**", parse_mode="Markdown", reply_markup=cancel_btn()
        )
    elif wm_type == "invisible":
        _set_state(ctx, S_WM_TEXT, invisible=True, **{k: v for k, v in ctx.user_data.items() if k != "state"})
        await update.message.reply_text(
            "👻 **Type invisible watermark text:**", parse_mode="Markdown", reply_markup=cancel_btn()
        )

async def _do_wm_text(update, ctx):
    if update.message.text:
        text = update.message.text.strip()
        invisible = ctx.user_data.get("invisible", False)
        msg_w = await update.message.reply_text("⏳ Adding watermark...")
        try:
            result = pdf_utils.watermark_text(ctx.user_data["wm_pdf"], text, invisible=invisible)
            _clear_state(ctx)
            await msg_w.delete()
            wm_label = "invisible" if invisible else "text"
            await _send_pdf(update, result, "watermarked.pdf",
                            f"{'👻' if invisible else '🌊'} **{wm_label.capitalize()} watermark added!**")
        except Exception as e:
            await msg_w.delete()
            await _error_reply(update, str(e))

async def _do_wm_logo(update, ctx):
    if update.message.photo or update.message.document:
        if update.message.photo:
            f = await update.message.photo[-1].get_file()
        else:
            f = await update.message.document.get_file()
        img_data = bytes(await f.download_as_bytearray())
        msg_w = await update.message.reply_text("⏳ Adding logo watermark...")
        try:
            result = pdf_utils.watermark_image(ctx.user_data["wm_pdf"], img_data)
            _clear_state(ctx)
            await msg_w.delete()
            await _send_pdf(update, result, "watermarked.pdf", "🖼️ **Logo watermark added!**")
        except Exception as e:
            await msg_w.delete()
            await _error_reply(update, str(e))
    else:
        await update.message.reply_text("⚠️ Send an image please!", reply_markup=cancel_btn())

async def _do_dark(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    msg_w = await update.message.reply_text("⏳ Converting to dark mode... (may take a moment)")
    try:
        result = pdf_utils.change_bg(bytes(data), "bg_dark")
        _clear_state(ctx)
        await msg_w.delete()
        await _send_pdf(update, result, "dark_mode.pdf", "🌙 **Dark mode PDF ready!**")
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_pageno(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    style = ctx.user_data.get("pn_style", "pn_arabic")
    msg_w = await update.message.reply_text("⏳ Adding page numbers...")
    try:
        result = pdf_utils.add_page_numbers(bytes(data), style)
        _clear_state(ctx)
        await msg_w.delete()
        await _send_pdf(update, result, "numbered.pdf", "🔢 **Page numbers added!**")
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_excel(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    msg_w = await update.message.reply_text("⏳ Converting PDF to Excel...")
    try:
        result = pdf_utils.pdf_to_excel(bytes(data))
        _clear_state(ctx)
        await msg_w.delete()
        await _send_file(update, result, "extracted.xlsx", "📊 **PDF → Excel done!**")
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_repair(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    msg_w = await update.message.reply_text("⏳ Attempting to repair PDF...")
    try:
        result = pdf_utils.repair_pdf(bytes(data))
        _clear_state(ctx)
        await msg_w.delete()
        await _send_pdf(update, result, "repaired.pdf", "🧩 **PDF repaired!**")
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_pdf2img(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    msg_w = await update.message.reply_text("⏳ Converting PDF to images...")
    try:
        images = pdf_utils.pdf_to_images(bytes(data))
        _clear_state(ctx)
        await msg_w.delete()
        send_count = min(len(images), 15)
        for i, img in enumerate(images[:send_count], 1):
            await update.message.reply_photo(photo=io.BytesIO(img), caption=f"🖼️ Page {i}/{len(images)}")
        await update.message.reply_text(
            f"✅ **{len(images)} pages converted!**" +
            (" (First 15 shown)" if len(images) > 15 else ""),
            parse_mode="Markdown", reply_markup=main_menu()
        )
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_img2pdf_collect(update, ctx):
    if update.message.photo:
        f = await update.message.photo[-1].get_file()
        data = bytes(await f.download_as_bytearray())
        ctx.user_data["images"].append(data)
        count = len(ctx.user_data["images"])
        await update.message.reply_text(
            f"✅ Image #{count} received! Send more or `/done`.",
            parse_mode="Markdown", reply_markup=cancel_btn()
        )
    elif update.message.document:
        doc = update.message.document
        if doc.mime_type and doc.mime_type.startswith("image/"):
            f = await doc.get_file()
            data = bytes(await f.download_as_bytearray())
            ctx.user_data["images"].append(data)
            count = len(ctx.user_data["images"])
            await update.message.reply_text(
                f"✅ Image #{count} received! Send more or `/done`.",
                parse_mode="Markdown", reply_markup=cancel_btn()
            )
        else:
            await update.message.reply_text("⚠️ Please send an **image**!", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Please send an **image**!", parse_mode="Markdown")

async def _do_bg(update, ctx):
    data = await _get_pdf_bytes(update)
    if not data:
        return
    color = ctx.user_data.get("bg_color", "bg_dark")
    msg_w = await update.message.reply_text("⏳ Changing background... (may take a moment)")
    try:
        result = pdf_utils.change_bg(bytes(data), color)
        _clear_state(ctx)
        await msg_w.delete()
        await _send_pdf(update, result, "bg_changed.pdf", "🎨 **Background changed!**")
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_handwrite(update, ctx):
    if not update.message.text:
        await update.message.reply_text("⚠️ Please type the text!", reply_markup=cancel_btn())
        return
    text = update.message.text.strip()
    font_key = ctx.user_data.get("hw_font", "caveat")
    msg_w = await update.message.reply_text("⏳ Creating handwritten PDF...")
    try:
        result = pdf_utils.create_handwritten_pdf(text, font_key)
        _clear_state(ctx)
        await msg_w.delete()
        await _send_pdf(update, result, "handwritten.pdf", "✍️ **Handwritten PDF ready!**")
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))

async def _do_ocr(update, ctx):
    msg_w = await update.message.reply_text("⏳ Extracting text...")
    try:
        if update.message.photo:
            f = await update.message.photo[-1].get_file()
            data = bytes(await f.download_as_bytearray())
            text = pdf_utils.ocr_image(data)
        elif update.message.document:
            doc = update.message.document
            f = await doc.get_file()
            data = bytes(await f.download_as_bytearray())
            if doc.mime_type == "application/pdf":
                text = pdf_utils.ocr_pdf(data)
            else:
                text = pdf_utils.ocr_image(data)
        else:
            await msg_w.delete()
            await update.message.reply_text("⚠️ Send an image or PDF!", reply_markup=cancel_btn())
            return

        _clear_state(ctx)
        await msg_w.delete()

        # Send as file if long
        if len(text) > 3500:
            txt_buf = io.BytesIO(text.encode("utf-8"))
            await update.message.reply_document(
                document=InputFile(txt_buf, filename="extracted_text.txt"),
                caption="🔍 **OCR complete!** Text extracted 📄",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        else:
            await update.message.reply_text(
                f"🔍 **Extracted Text:**\n\n```\n{text}\n```",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
    except Exception as e:
        await msg_w.delete()
        await _error_reply(update, str(e))


# ── Direct commands ───────────────────────────────────────────────────────────
async def cmd_compress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_COMPRESS)
    await update.message.reply_text("📐 Send me the PDF to compress!", reply_markup=cancel_btn())

async def cmd_split(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_SPLIT)
    await update.message.reply_text("✂️ Send me the PDF to split!", reply_markup=cancel_btn())

async def cmd_merge(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_MERGE)
    ctx.user_data["merge_files"] = []
    await update.message.reply_text("🔗 Send PDFs one by one, then `/done`.", reply_markup=cancel_btn())

async def cmd_lock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_LOCK)
    await update.message.reply_text("🔒 Send the PDF to lock!", reply_markup=cancel_btn())

async def cmd_unlock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_UNLOCK)
    await update.message.reply_text("🔓 Send the locked PDF!", reply_markup=cancel_btn())

async def cmd_repair(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_REPAIR)
    await update.message.reply_text("🧩 Send the corrupted PDF!", reply_markup=cancel_btn())

async def cmd_watermark(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌊 Choose watermark type:", reply_markup=watermark_menu())

async def cmd_darkmode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_DARK)
    await update.message.reply_text("🌙 Send the PDF for dark mode!", reply_markup=cancel_btn())

async def cmd_pagenos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔢 Choose page number style:", reply_markup=page_no_style_menu())

async def cmd_pdf2img(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_PDF2IMG)
    await update.message.reply_text("🖼️ Send the PDF to convert!", reply_markup=cancel_btn())

async def cmd_img2pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_IMG2PDF)
    ctx.user_data["images"] = []
    await update.message.reply_text("🖼️ Send images one by one, then `/done`.", reply_markup=cancel_btn())

async def cmd_excel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_EXCEL)
    await update.message.reply_text("📊 Send the PDF to convert to Excel!", reply_markup=cancel_btn())

async def cmd_bgchange(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎨 Choose background color:", reply_markup=bg_color_menu())

async def cmd_handwrite(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✍️ Choose a handwriting font:", reply_markup=font_menu())

async def cmd_ocr(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _set_state(ctx, S_OCR)
    await update.message.reply_text("🔍 Send an image or PDF for OCR!", reply_markup=cancel_btn())
