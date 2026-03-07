"""
Nexora PDF Doctor Bot v5.0 — Main Entry Point
New: 40+ new features, bulk processing, scheduled deletion, reminder system,
     improved broadcast rate limiting, file size validation.
"""
import asyncio, logging, traceback
from aiohttp import web
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from config import BOT_TOKEN, PORT, OWNER_ID, MAX_FILE_SIZE_MB, BROADCAST_DELAY_SEC, BROADCAST_BATCH

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from handlers.start_handler   import start_cmd, help_cmd, account_cmd
from handlers.premium_handler import (
    premium_cmd, grant_premium_cmd, buy_plan_callback, pay_screenshot_callback
)
from handlers.pdf_handler import (
    menu_callback, handle_message, handle_group_reaction, cmd_dashboard,
    cmd_compress, cmd_split, cmd_merge, cmd_lock, cmd_unlock, cmd_repair,
    cmd_watermark, cmd_darkmode, cmd_pagenos, cmd_pdf2img, cmd_img2pdf,
    cmd_excel, cmd_bgchange, cmd_handwrite, cmd_ocr, cmd_rotate, cmd_resize,
    cmd_addtext, cmd_footer, cmd_extract, cmd_metadata,
    cmd_pdf2word, cmd_pdf2ppt, cmd_crop, cmd_qr,
    cmd_delete_pages, cmd_reorder, cmd_lang, cmd_reverse, cmd_compare,
)
from handlers.new_features_handler import (
    # PDF tools
    cmd_pdf2txt, cmd_linearize, cmd_thumbnail, cmd_pdf_info,
    cmd_redact, cmd_impose, cmd_deskew, cmd_pwd_strength, cmd_pwd_crack,
    cmd_metadata_edit,
    # Image tools
    cmd_img_compress, cmd_img_resize, cmd_img_crop, cmd_img_filter,
    cmd_img_text, cmd_img2jpg, cmd_img2png, cmd_img_bgremove,
    # Doc converters
    cmd_csv2pdf, cmd_txt2pdf, cmd_html2pdf, cmd_json2pdf,
    cmd_doc2pdf, cmd_pdf2epub, cmd_epub2pdf,
    # Security
    cmd_hash, cmd_steganography, cmd_pdf_sign,
    # Creative
    cmd_poster, cmd_calendar_pdf, cmd_invoice, cmd_resume, cmd_certificate,
    # Utility
    cmd_zip, cmd_unzip, cmd_fileinfo, cmd_qrcode_scan, cmd_barcode,
    # UX
    cmd_remind, cmd_notes, cmd_history,
    # Handlers
    handle_new_features, handle_new_callbacks,
)
from handlers.admin_handler import admin_panel

BOT_COMMANDS = [
    BotCommand("start",        "🏠 Main Menu"),
    BotCommand("help",         "❓ Help & Commands"),
    BotCommand("account",      "👤 My Account"),
    BotCommand("dashboard",    "📊 My Stats Dashboard"),
    BotCommand("premium",      "💎 Premium Plans"),
    BotCommand("lang",         "🌍 Change Language"),
    # PDF Tools
    BotCommand("compress",     "📐 Compress PDF"),
    BotCommand("split",        "✂️ Split PDF"),
    BotCommand("merge",        "🔗 Merge PDFs"),
    BotCommand("lock",         "🔒 Lock PDF"),
    BotCommand("unlock",       "🔓 Unlock PDF"),
    BotCommand("repair",       "🧩 Repair PDF"),
    BotCommand("pdf2txt",      "📄 PDF to Text"),
    BotCommand("linearize",    "🌐 Web Optimize PDF"),
    BotCommand("thumbnail",    "🖼️ PDF Preview"),
    BotCommand("pdf_info",     "🔍 Deep PDF Analysis"),
    BotCommand("redact",       "⬛ Redact/Censor Text"),
    BotCommand("impose",       "📋 2-up/4-up Layout"),
    BotCommand("deskew",       "📐 Fix Crooked Scan"),
    BotCommand("pwd_strength", "🔐 Password Strength"),
    BotCommand("pwd_crack",    "🔓 PDF Password Crack 👑"),
    BotCommand("metadata_edit","✏️ Edit PDF Metadata"),
    # Visual
    BotCommand("watermark",    "🌊 Watermark"),
    BotCommand("darkmode",     "🌙 Dark Mode"),
    BotCommand("pagenos",      "🔢 Page Numbers"),
    BotCommand("bgchange",     "🎨 BG Color"),
    BotCommand("rotate",       "🔄 Rotate"),
    BotCommand("resize",       "📏 Resize to A4"),
    # Convert PDF
    BotCommand("pdf2img",      "🖼️ PDF to Images"),
    BotCommand("img2pdf",      "🖼️ Images to PDF"),
    BotCommand("excel",        "📊 PDF to Excel"),
    BotCommand("pdf2word",     "📄 PDF to Word"),
    BotCommand("pdf2ppt",      "📊 PDF to PPT 👑"),
    BotCommand("pdf2epub",     "📚 PDF to EPUB ⭐"),
    BotCommand("epub2pdf",     "📖 EPUB to PDF"),
    BotCommand("doc2pdf",      "📝 Word to PDF"),
    # Image Tools
    BotCommand("img_compress", "📦 Compress Image"),
    BotCommand("img_resize",   "📏 Resize Image"),
    BotCommand("img_crop",     "✂️ Crop Image"),
    BotCommand("img_filter",   "🎨 Image Filters"),
    BotCommand("img_text",     "📝 Text on Image"),
    BotCommand("img2jpg",      "🖼️ Convert to JPG"),
    BotCommand("img2png",      "🖼️ Convert to PNG"),
    BotCommand("img_bgremove", "✂️ Remove BG ⭐"),
    # Doc Converters
    BotCommand("csv2pdf",      "📊 CSV to PDF"),
    BotCommand("txt2pdf",      "📄 Text to PDF"),
    BotCommand("html2pdf",     "🌐 HTML to PDF"),
    BotCommand("json2pdf",     "📋 JSON to PDF"),
    # Security
    BotCommand("hash",         "🔒 File Hash Check"),
    BotCommand("steganography","🕵️ Hide/Reveal Messages"),
    BotCommand("pdf_sign",     "✍️ Digital Signature"),
    # Creative
    BotCommand("poster",       "🎨 Poster Generator"),
    BotCommand("calendar_pdf", "📅 Monthly Calendar"),
    BotCommand("invoice",      "🧾 Invoice Generator"),
    BotCommand("resume",       "📋 Resume Builder"),
    BotCommand("certificate",  "🏆 Certificate Generator"),
    # Utility
    BotCommand("zip",          "📦 Create ZIP"),
    BotCommand("unzip",        "📂 Extract ZIP"),
    BotCommand("fileinfo",     "ℹ️ File Information"),
    BotCommand("qrcode_scan",  "📷 Scan QR Code"),
    BotCommand("barcode",      "📊 Generate Barcode"),
    # Pages
    BotCommand("extract",      "🔖 Extract Pages"),
    BotCommand("delete_pages", "🗑️ Delete Pages"),
    BotCommand("reorder",      "🔀 Reorder Pages"),
    BotCommand("reverse",      "🔃 Reverse Pages"),
    BotCommand("compare",      "🔍 Compare PDFs"),
    # Smart Tools
    BotCommand("ocr",          "👁️ OCR Text"),
    BotCommand("metadata",     "📋 View Metadata"),
    BotCommand("handwrite",    "✍️ Handwritten PDF"),
    BotCommand("addtext",      "📝 Add Text"),
    BotCommand("footer",       "🗂️ Add Footer"),
    BotCommand("crop",         "✂️ Crop Margins"),
    BotCommand("qr",           "🔲 QR Code"),
    # UX
    BotCommand("remind",       "⏰ Set Reminder"),
    BotCommand("notes",        "📒 Personal Notes"),
    BotCommand("history",      "📂 File History"),
]


# ── File size validation middleware ──────────────────────────────────────────

async def check_file_size(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if file is within limits, False if rejected."""
    msg = update.message
    if not msg: return True

    file_size = 0
    if msg.document:
        file_size = msg.document.file_size or 0
    elif msg.photo:
        file_size = msg.photo[-1].file_size or 0

    if file_size == 0: return True

    from database import get_plan
    plan = await get_plan(update.effective_user.id)
    max_mb = MAX_FILE_SIZE_MB.get(plan, 20)
    max_bytes = max_mb * 1024 * 1024

    if file_size > max_bytes:
        actual_mb = round(file_size / 1024 / 1024, 1)
        plan_limits = "\n".join(
            f"  {'✅' if p == plan else '•'} {p.title()}: {mb}MB"
            for p, mb in MAX_FILE_SIZE_MB.items()
        )
        await msg.reply_text(
            f"⚠️ <b>File Too Large!</b>\n\n"
            f"📦 Your file: <b>{actual_mb}MB</b>\n"
            f"🚫 Your limit: <b>{max_mb}MB</b> ({plan.title()} plan)\n\n"
            f"📊 <b>Size limits by plan:</b>\n{plan_limits}\n\n"
            f"💎 Upgrade for larger files → /premium",
            parse_mode="HTML"
        )
        return False
    return True


# ── Unified message handler ──────────────────────────────────────────────────

async def unified_message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Routes to new features handler first, then original."""
    from database import ensure_user
    user = update.effective_user
    await ensure_user(user.id, user.full_name, user.username or "")

    # File size check
    if not await check_file_size(update, ctx):
        return

    # Try new features first
    handled = await handle_new_features(update, ctx)
    if not handled:
        # Fall back to original handler
        await handle_message(update, ctx)


async def unified_callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Routes callbacks."""
    handled = await handle_new_callbacks(update, ctx)
    if not handled:
        await menu_callback(update, ctx)


# ── Global error handler ─────────────────────────────────────────────────────

async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    err = ctx.error
    logger.error("Exception while handling update:", exc_info=err)
    import telegram.error as tg_err
    if isinstance(err, (tg_err.TimedOut, tg_err.NetworkError)):
        logger.warning(f"⚡ Network error (will retry): {err}")
        return
    err_msg = str(err)[:200]
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"⚠️ <b>An error occurred!</b>\n\n<code>{err_msg}</code>\n\nPlease try again or use /start",
                parse_mode="HTML"
            )
        except Exception:
            pass
    if OWNER_ID:
        try:
            tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            await ctx.bot.send_message(
                chat_id=OWNER_ID,
                text=f"🚨 <b>Bot Error!</b>\n\n<pre>{tb[:3000]}</pre>",
                parse_mode="HTML"
            )
        except Exception:
            pass


# ── Broadcast (rate-limited) ─────────────────────────────────────────────────

async def broadcast_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not ctx.args:
        await update.message.reply_text("Usage: /broadcast your message"); return
    text = " ".join(ctx.args)
    from database import get_all_users
    users = await get_all_users()
    sent = failed = 0
    total = len(users)
    prog_msg = await update.message.reply_text(f"📢 Broadcasting to {total} users...")
    for i, u in enumerate(users):
        try:
            await ctx.bot.send_message(
                chat_id=u["user_id"],
                text=f"📢 <b>Announcement:</b>\n\n{text}",
                parse_mode="HTML"
            )
            sent += 1
        except Exception:
            failed += 1
        # ── RATE LIMITING FIX: 0.35s delay (was 0.05s — too fast!) ──
        await asyncio.sleep(BROADCAST_DELAY_SEC)
        # Update progress every 25 messages
        if (i + 1) % BROADCAST_BATCH == 0:
            try:
                await prog_msg.edit_text(
                    f"📢 Broadcasting... {i+1}/{total}\n✅ {sent} | ❌ {failed}"
                )
            except Exception:
                pass
    await prog_msg.edit_text(
        f"📢 <b>Broadcast Done!</b>\n✅ Sent: {sent}\n❌ Failed: {failed}",
        parse_mode="HTML"
    )


# ── Stats ─────────────────────────────────────────────────────────────────────

async def stats_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    from database import get_admin_stats
    s = await get_admin_stats()
    await update.message.reply_text(
        f"📊 <b>Bot Stats — v5.0</b>\n\n"
        f"👥 Total: <b>{s['total_users']}</b>\n"
        f"🆓 Free: <b>{s['free_users']}</b>\n"
        f"⭐ Basic: <b>{s['basic_users']}</b>\n"
        f"👑 Pro: <b>{s['pro_users']}</b>\n"
        f"📆 Active Today: <b>{s['today_active']}</b>\n"
        f"⚡ Ops Today: <b>{s['today_ops']}</b>\n"
        f"💳 Pending Payments: <b>{s['pending_payments']}</b>",
        parse_mode="HTML"
    )


# ── Reminder Scheduler ────────────────────────────────────────────────────────

async def reminder_scheduler(bot):
    """Background task: check and fire due reminders every 30 seconds."""
    from database import get_due_reminders, mark_reminder_done
    while True:
        try:
            reminders = await get_due_reminders()
            for r in reminders:
                try:
                    await bot.send_message(
                        chat_id=r["chat_id"],
                        text=f"⏰ <b>Reminder!</b>\n\n📝 {r['message']}",
                        parse_mode="HTML"
                    )
                    await mark_reminder_done(r["id"])
                except Exception as e:
                    logger.warning(f"Reminder failed: {e}")
        except Exception as e:
            logger.error(f"Reminder scheduler error: {e}")
        await asyncio.sleep(30)


# ── Scheduled File Deletion ────────────────────────────────────────────────────

async def handle_scheduled_deletion(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """User can request auto-delete for their file after processing."""
    # This is handled via bot callback on the sent file message
    pass


def build_app() -> Application:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(60)
        .pool_timeout(30)
        .build()
    )

    # ── Core ──────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",         start_cmd))
    app.add_handler(CommandHandler("help",          help_cmd))
    app.add_handler(CommandHandler("account",       account_cmd))
    app.add_handler(CommandHandler("dashboard",     cmd_dashboard))
    app.add_handler(CommandHandler("premium",       premium_cmd))
    app.add_handler(CommandHandler("lang",          cmd_lang))

    # ── Original PDF commands ─────────────────────────────────────────────────
    app.add_handler(CommandHandler("compress",      cmd_compress))
    app.add_handler(CommandHandler("split",         cmd_split))
    app.add_handler(CommandHandler("merge",         cmd_merge))
    app.add_handler(CommandHandler("lock",          cmd_lock))
    app.add_handler(CommandHandler("unlock",        cmd_unlock))
    app.add_handler(CommandHandler("repair",        cmd_repair))
    app.add_handler(CommandHandler("watermark",     cmd_watermark))
    app.add_handler(CommandHandler("darkmode",      cmd_darkmode))
    app.add_handler(CommandHandler("pagenos",       cmd_pagenos))
    app.add_handler(CommandHandler("pdf2img",       cmd_pdf2img))
    app.add_handler(CommandHandler("img2pdf",       cmd_img2pdf))
    app.add_handler(CommandHandler("excel",         cmd_excel))
    app.add_handler(CommandHandler("bgchange",      cmd_bgchange))
    app.add_handler(CommandHandler("handwrite",     cmd_handwrite))
    app.add_handler(CommandHandler("ocr",           cmd_ocr))
    app.add_handler(CommandHandler("rotate",        cmd_rotate))
    app.add_handler(CommandHandler("resize",        cmd_resize))
    app.add_handler(CommandHandler("addtext",       cmd_addtext))
    app.add_handler(CommandHandler("footer",        cmd_footer))
    app.add_handler(CommandHandler("extract",       cmd_extract))
    app.add_handler(CommandHandler("metadata",      cmd_metadata))
    app.add_handler(CommandHandler("pdf2word",      cmd_pdf2word))
    app.add_handler(CommandHandler("pdf2ppt",       cmd_pdf2ppt))
    app.add_handler(CommandHandler("crop",          cmd_crop))
    app.add_handler(CommandHandler("qr",            cmd_qr))
    app.add_handler(CommandHandler("delete_pages",  cmd_delete_pages))
    app.add_handler(CommandHandler("reorder",       cmd_reorder))
    app.add_handler(CommandHandler("reverse",       cmd_reverse))
    app.add_handler(CommandHandler("compare",       cmd_compare))

    # ── NEW v5: PDF Tools ─────────────────────────────────────────────────────
    app.add_handler(CommandHandler("pdf2txt",       cmd_pdf2txt))
    app.add_handler(CommandHandler("linearize",     cmd_linearize))
    app.add_handler(CommandHandler("thumbnail",     cmd_thumbnail))
    app.add_handler(CommandHandler("pdf_info",      cmd_pdf_info))
    app.add_handler(CommandHandler("redact",        cmd_redact))
    app.add_handler(CommandHandler("impose",        cmd_impose))
    app.add_handler(CommandHandler("deskew",        cmd_deskew))
    app.add_handler(CommandHandler("pwd_strength",  cmd_pwd_strength))
    app.add_handler(CommandHandler("pwd_crack",     cmd_pwd_crack))
    app.add_handler(CommandHandler("metadata_edit", cmd_metadata_edit))

    # ── NEW v5: Image Tools ───────────────────────────────────────────────────
    app.add_handler(CommandHandler("img_compress",  cmd_img_compress))
    app.add_handler(CommandHandler("img_resize",    cmd_img_resize))
    app.add_handler(CommandHandler("img_crop",      cmd_img_crop))
    app.add_handler(CommandHandler("img_filter",    cmd_img_filter))
    app.add_handler(CommandHandler("img_text",      cmd_img_text))
    app.add_handler(CommandHandler("img2jpg",       cmd_img2jpg))
    app.add_handler(CommandHandler("img2png",       cmd_img2png))
    app.add_handler(CommandHandler("img_bgremove",  cmd_img_bgremove))

    # ── NEW v5: Document Converters ───────────────────────────────────────────
    app.add_handler(CommandHandler("csv2pdf",       cmd_csv2pdf))
    app.add_handler(CommandHandler("txt2pdf",       cmd_txt2pdf))
    app.add_handler(CommandHandler("html2pdf",      cmd_html2pdf))
    app.add_handler(CommandHandler("json2pdf",      cmd_json2pdf))
    app.add_handler(CommandHandler("doc2pdf",       cmd_doc2pdf))
    app.add_handler(CommandHandler("pdf2epub",      cmd_pdf2epub))
    app.add_handler(CommandHandler("epub2pdf",      cmd_epub2pdf))

    # ── NEW v5: Security ──────────────────────────────────────────────────────
    app.add_handler(CommandHandler("hash",          cmd_hash))
    app.add_handler(CommandHandler("steganography", cmd_steganography))
    app.add_handler(CommandHandler("pdf_sign",      cmd_pdf_sign))

    # ── NEW v5: Creative ──────────────────────────────────────────────────────
    app.add_handler(CommandHandler("poster",        cmd_poster))
    app.add_handler(CommandHandler("calendar_pdf",  cmd_calendar_pdf))
    app.add_handler(CommandHandler("invoice",       cmd_invoice))
    app.add_handler(CommandHandler("resume",        cmd_resume))
    app.add_handler(CommandHandler("certificate",   cmd_certificate))

    # ── NEW v5: Utility ───────────────────────────────────────────────────────
    app.add_handler(CommandHandler("zip",           cmd_zip))
    app.add_handler(CommandHandler("unzip",         cmd_unzip))
    app.add_handler(CommandHandler("fileinfo",      cmd_fileinfo))
    app.add_handler(CommandHandler("qrcode_scan",   cmd_qrcode_scan))
    app.add_handler(CommandHandler("barcode",       cmd_barcode))

    # ── NEW v5: UX ────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("remind",        cmd_remind))
    app.add_handler(CommandHandler("notes",         cmd_notes))
    app.add_handler(CommandHandler("history",       cmd_history))

    # ── Owner commands ────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("givepremium",   grant_premium_cmd))
    app.add_handler(CommandHandler("broadcast",     broadcast_cmd))
    app.add_handler(CommandHandler("stats",         stats_cmd))

    # ── Callbacks ─────────────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(buy_plan_callback,       pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(pay_screenshot_callback, pattern="^pay_ss_"))
    app.add_handler(CallbackQueryHandler(unified_callback_handler))

    # ── Private messages ──────────────────────────────────────────────────────
    app.add_handler(MessageHandler(
        (filters.Document.ALL | filters.PHOTO | filters.TEXT) & ~filters.COMMAND & filters.ChatType.PRIVATE,
        unified_message_handler
    ))

    # ── Group reactor ─────────────────────────────────────────────────────────
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & ~filters.COMMAND,
        handle_group_reaction
    ))

    app.add_error_handler(error_handler)
    return app


# ── Aiohttp web server ─────────────────────────────────────────────────────────

async def health(request):
    return web.Response(text="🤖 Nexora PDF Doctor Bot v5.0 — Running!", status=200)

async def run_web_server(bot_app):
    wa = web.Application()
    wa.router.add_get("/", health)
    wa.router.add_get("/health", health)
    wa.router.add_get("/admin", admin_panel)
    runner = web.AppRunner(wa)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Web server on port {PORT}")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!"); return

    logger.info("⬇️  Downloading fonts...")
    try:
        from utils.font_loader import download_fonts
        download_fonts()
    except Exception as e:
        logger.warning(f"Font issue: {e}")

    tg_app = build_app()

    async with tg_app:
        try:
            await tg_app.bot.set_my_commands(BOT_COMMANDS)
            logger.info("✅ Bot commands set")
        except Exception as e:
            logger.warning(f"Commands error: {e}")

    await run_web_server(tg_app)

    logger.info("🚀 Starting Nexora PDF Doctor Bot v5.0...")
    async with tg_app:
        await tg_app.start()

        # Start reminder scheduler background task
        asyncio.create_task(reminder_scheduler(tg_app.bot))
        logger.info("⏰ Reminder scheduler started")

        await tg_app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            timeout=10,
            read_timeout=15,
            write_timeout=15,
            connect_timeout=15,
            pool_timeout=15,
        )
        logger.info("✅ Nexora PDF Doctor v5.0 is LIVE!")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
