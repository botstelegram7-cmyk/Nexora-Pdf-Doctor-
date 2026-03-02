"""
Nexora PDF Doctor Bot v4.0 — Main Entry Point
Fixes: Polling retry logic, connection timeouts.
New: Admin panel, group reactions, per-feature limits, dashboard.
"""
import asyncio, logging, traceback
from aiohttp import web
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from config import BOT_TOKEN, PORT, OWNER_ID

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Import all handlers ────────────────────────────────────────────────────────
from handlers.start_handler  import start_cmd, help_cmd, account_cmd
from handlers.premium_handler import (
    premium_cmd, grant_premium_cmd,
    buy_plan_callback, pay_screenshot_callback
)
from handlers.pdf_handler import (
    menu_callback, handle_message, handle_group_reaction,
    cmd_dashboard,
    cmd_compress, cmd_split, cmd_merge, cmd_lock, cmd_unlock, cmd_repair,
    cmd_watermark, cmd_darkmode, cmd_pagenos, cmd_pdf2img, cmd_img2pdf,
    cmd_excel, cmd_bgchange, cmd_handwrite, cmd_ocr, cmd_rotate, cmd_resize,
    cmd_addtext, cmd_footer, cmd_extract, cmd_metadata,
    cmd_pdf2word, cmd_pdf2ppt, cmd_crop, cmd_qr,
    cmd_delete_pages, cmd_reorder, cmd_lang, cmd_reverse, cmd_compare,
)
from handlers.admin_handler import admin_panel

BOT_COMMANDS = [
    BotCommand("start",        "🏠 Main Menu"),
    BotCommand("help",         "❓ Help & Commands"),
    BotCommand("account",      "👤 My Account"),
    BotCommand("dashboard",    "📊 My Stats Dashboard"),
    BotCommand("premium",      "💎 Premium Plans"),
    BotCommand("lang",         "🌍 Change Language"),
    BotCommand("compress",     "📐 Compress PDF"),
    BotCommand("split",        "✂️ Split PDF"),
    BotCommand("merge",        "🔗 Merge PDFs"),
    BotCommand("lock",         "🔒 Lock PDF"),
    BotCommand("unlock",       "🔓 Unlock PDF"),
    BotCommand("repair",       "🧩 Repair PDF"),
    BotCommand("watermark",    "🌊 Watermark"),
    BotCommand("darkmode",     "🌙 Dark Mode"),
    BotCommand("pagenos",      "🔢 Page Numbers"),
    BotCommand("bgchange",     "🎨 BG Color"),
    BotCommand("pdf2img",      "🖼️ PDF to Images"),
    BotCommand("img2pdf",      "🖼️ Images to PDF"),
    BotCommand("excel",        "📊 PDF to Excel"),
    BotCommand("pdf2word",     "📄 PDF to Word"),
    BotCommand("pdf2ppt",      "📊 PDF to PowerPoint"),
    BotCommand("handwrite",    "✍️ Handwritten PDF"),
    BotCommand("addtext",      "📝 Add Text"),
    BotCommand("footer",       "🗂️ Add Footer"),
    BotCommand("crop",         "✂️ Crop Margins"),
    BotCommand("qr",           "🔲 QR Code"),
    BotCommand("extract",      "🔖 Extract Pages"),
    BotCommand("delete_pages", "🗑️ Delete Pages"),
    BotCommand("reorder",      "🔀 Reorder Pages"),
    BotCommand("reverse",      "🔃 Reverse Pages"),
    BotCommand("compare",      "🔍 Compare 2 PDFs"),
    BotCommand("ocr",          "👁️ OCR Text"),
    BotCommand("rotate",       "🔄 Rotate"),
    BotCommand("resize",       "📏 Resize to A4"),
    BotCommand("metadata",     "📋 PDF Metadata"),
]


# ── Global error handler ──────────────────────────────────────────────────────
async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    err = ctx.error
    logger.error("Exception while handling update:", exc_info=err)

    # ── FIX: Handle network/polling errors gracefully ──
    import telegram.error as tg_err
    if isinstance(err, (tg_err.TimedOut, tg_err.NetworkError)):
        logger.warning(f"⚡ Network error (will retry): {err}")
        return  # PTB will auto-retry polling

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


# ── Owner broadcast ───────────────────────────────────────────────────────────
async def broadcast_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not ctx.args:
        await update.message.reply_text("Usage: /broadcast your message", parse_mode="HTML"); return
    text = " ".join(ctx.args)
    from database import get_all_users
    users = await get_all_users()
    sent = failed = 0
    for u in users:
        try:
            await ctx.bot.send_message(chat_id=u["user_id"], text=f"📢 <b>Announcement:</b>\n\n{text}", parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await update.message.reply_text(f"📢 <b>Broadcast done!</b>\n✅ Sent: {sent}\n❌ Failed: {failed}", parse_mode="HTML")


# ── Owner stats ───────────────────────────────────────────────────────────────
async def stats_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    from database import get_admin_stats
    s = await get_admin_stats()
    await update.message.reply_text(
        f"📊 <b>Bot Stats</b>\n\n"
        f"👥 Total: <b>{s['total_users']}</b>\n"
        f"🆓 Free: <b>{s['free_users']}</b>\n"
        f"⭐ Basic: <b>{s['basic_users']}</b>\n"
        f"👑 Pro: <b>{s['pro_users']}</b>\n"
        f"📆 Active Today: <b>{s['today_active']}</b>\n"
        f"⚡ Ops Today: <b>{s['today_ops']}</b>\n"
        f"💳 Pending Payments: <b>{s['pending_payments']}</b>",
        parse_mode="HTML"
    )


def build_app() -> Application:
    """
    ── FIX: Added connection_pool_size, connect_timeout, read_timeout ──
    These prevent the polling network loop error in Render logs.
    """
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
    app.add_handler(CommandHandler("start",        start_cmd))
    app.add_handler(CommandHandler("help",         help_cmd))
    app.add_handler(CommandHandler("account",      account_cmd))
    app.add_handler(CommandHandler("dashboard",    cmd_dashboard))
    app.add_handler(CommandHandler("premium",      premium_cmd))
    app.add_handler(CommandHandler("lang",         cmd_lang))

    # ── PDF commands ──────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("compress",     cmd_compress))
    app.add_handler(CommandHandler("split",        cmd_split))
    app.add_handler(CommandHandler("merge",        cmd_merge))
    app.add_handler(CommandHandler("lock",         cmd_lock))
    app.add_handler(CommandHandler("unlock",       cmd_unlock))
    app.add_handler(CommandHandler("repair",       cmd_repair))
    app.add_handler(CommandHandler("watermark",    cmd_watermark))
    app.add_handler(CommandHandler("darkmode",     cmd_darkmode))
    app.add_handler(CommandHandler("pagenos",      cmd_pagenos))
    app.add_handler(CommandHandler("pdf2img",      cmd_pdf2img))
    app.add_handler(CommandHandler("img2pdf",      cmd_img2pdf))
    app.add_handler(CommandHandler("excel",        cmd_excel))
    app.add_handler(CommandHandler("bgchange",     cmd_bgchange))
    app.add_handler(CommandHandler("handwrite",    cmd_handwrite))
    app.add_handler(CommandHandler("ocr",          cmd_ocr))
    app.add_handler(CommandHandler("rotate",       cmd_rotate))
    app.add_handler(CommandHandler("resize",       cmd_resize))
    app.add_handler(CommandHandler("addtext",      cmd_addtext))
    app.add_handler(CommandHandler("footer",       cmd_footer))
    app.add_handler(CommandHandler("extract",      cmd_extract))
    app.add_handler(CommandHandler("metadata",     cmd_metadata))
    app.add_handler(CommandHandler("pdf2word",     cmd_pdf2word))
    app.add_handler(CommandHandler("pdf2ppt",      cmd_pdf2ppt))
    app.add_handler(CommandHandler("crop",         cmd_crop))
    app.add_handler(CommandHandler("qr",           cmd_qr))
    app.add_handler(CommandHandler("delete_pages", cmd_delete_pages))
    app.add_handler(CommandHandler("reorder",      cmd_reorder))
    app.add_handler(CommandHandler("reverse",      cmd_reverse))
    app.add_handler(CommandHandler("compare",      cmd_compare))

    # ── Owner commands ────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("givepremium",  grant_premium_cmd))
    app.add_handler(CommandHandler("broadcast",    broadcast_cmd))
    app.add_handler(CommandHandler("stats",        stats_cmd))

    # ── Callbacks ─────────────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(buy_plan_callback,       pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(pay_screenshot_callback, pattern="^pay_ss_"))
    app.add_handler(CallbackQueryHandler(menu_callback))

    # ── Private messages ──────────────────────────────────────────────────────
    app.add_handler(MessageHandler(
        (filters.Document.ALL | filters.PHOTO | filters.TEXT) & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_message
    ))

    # ── Group/Channel ALL message reactor ─────────────────────────────────────
    # Reacts to EVERY message in groups: PDF, video, sticker, emoji, chat, etc.
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & ~filters.COMMAND,
        handle_group_reaction
    ))

    app.add_error_handler(error_handler)
    return app


# ── Aiohttp web server ────────────────────────────────────────────────────────
async def health(request):
    return web.Response(text="🤖 Nexora PDF Doctor Bot v4.0 — Running!", status=200)

async def run_web_server(bot_app):
    wa = web.Application()
    wa.router.add_get("/", health)
    wa.router.add_get("/health", health)
    wa.router.add_get("/admin", admin_panel)   # 🆕 Admin panel
    runner = web.AppRunner(wa)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Web server on port {PORT} | Admin: /admin?secret=YOUR_SECRET")


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

    logger.info("🚀 Starting Nexora PDF Doctor Bot v4.0...")
    async with tg_app:
        await tg_app.start()
        await tg_app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            # ── FIX: These prevent the polling retry error ──
            timeout=10,           # Long poll timeout
            read_timeout=15,
            write_timeout=15,
            connect_timeout=15,
            pool_timeout=15,
        )
        logger.info("✅ Nexora PDF Doctor v4.0 is LIVE!")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
