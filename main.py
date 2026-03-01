"""
PDF Doctor Bot v2.0 — Main entry point
GitHub: @SerenaXdev
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

# ── Import handlers ──────────────────────────────────────────────────────────
from handlers.start_handler  import start_cmd, help_cmd, account_cmd
from handlers.premium_handler import (
    premium_cmd, grant_premium_cmd,
    buy_plan_callback, pay_screenshot_callback
)
from handlers.pdf_handler import (
    menu_callback, handle_message,
    cmd_compress, cmd_split, cmd_merge,
    cmd_lock, cmd_unlock, cmd_repair,
    cmd_watermark, cmd_darkmode, cmd_pagenos,
    cmd_pdf2img, cmd_img2pdf, cmd_excel,
    cmd_bgchange, cmd_handwrite, cmd_ocr,
    cmd_rotate, cmd_resize, cmd_addtext,
    cmd_footer, cmd_extract, cmd_metadata,
)

BOT_COMMANDS = [
    BotCommand("start",     "🏠 Main Menu"),
    BotCommand("help",      "❓ Help & All Commands"),
    BotCommand("account",   "👤 My Account & Plan"),
    BotCommand("premium",   "💎 Premium Plans"),
    BotCommand("compress",  "📐 Compress PDF"),
    BotCommand("split",     "✂️ Split PDF"),
    BotCommand("merge",     "🔗 Merge PDFs"),
    BotCommand("lock",      "🔒 Lock PDF"),
    BotCommand("unlock",    "🔓 Unlock PDF"),
    BotCommand("repair",    "🧩 Repair Corrupted PDF"),
    BotCommand("watermark", "🌊 Add Watermark"),
    BotCommand("darkmode",  "🌙 Dark Mode"),
    BotCommand("pagenos",   "🔢 Add Page Numbers"),
    BotCommand("pdf2img",   "🖼️ PDF to Images"),
    BotCommand("img2pdf",   "🖼️ Images to PDF"),
    BotCommand("excel",     "📊 PDF to Excel"),
    BotCommand("bgchange",  "🎨 BG Color Changer"),
    BotCommand("handwrite", "✍️ Handwritten PDF"),
    BotCommand("ocr",       "👁️ OCR Extract Text"),
    BotCommand("rotate",    "🔄 Rotate PDF"),
    BotCommand("resize",    "📏 Resize to A4"),
    BotCommand("addtext",   "📝 Add Text to PDF"),
    BotCommand("footer",    "🗂️ Add Footer"),
    BotCommand("extract",   "🔖 Extract Pages"),
    BotCommand("metadata",  "📋 View PDF Metadata"),
]


# ── Global error handler ─────────────────────────────────────────────────────
async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=ctx.error)
    err_msg = str(ctx.error)

    if update and isinstance(update, Update):
        msg = update.effective_message
        if msg:
            try:
                await msg.reply_text(
                    f"⚠️ <b>An error occurred!</b>\n\n"
                    f"<code>{err_msg[:200]}</code>\n\n"
                    "Please try again or use /start",
                    parse_mode="HTML"
                )
            except Exception:
                pass

    # Notify owner
    if OWNER_ID:
        try:
            tb = "".join(traceback.format_exception(type(ctx.error), ctx.error, ctx.error.__traceback__))
            await ctx.bot.send_message(
                chat_id=OWNER_ID,
                text=f"🚨 <b>Bot Error!</b>\n\n<pre>{tb[:3000]}</pre>",
                parse_mode="HTML"
            )
        except Exception:
            pass


# ── Owner broadcast command ──────────────────────────────────────────────────
async def broadcast_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from config import OWNER_ID as OID
    if update.effective_user.id != OID:
        return
    if not ctx.args:
        await update.message.reply_text(
            "Usage: <code>/broadcast your message here</code>", parse_mode="HTML"
        )
        return
    text = " ".join(ctx.args)
    from database import get_all_users
    users = await get_all_users()
    sent = 0
    failed = 0
    for u in users:
        try:
            await ctx.bot.send_message(chat_id=u["user_id"], text=f"📢 <b>Announcement:</b>\n\n{text}", parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await update.message.reply_text(
        f"📢 <b>Broadcast done!</b>\n✅ Sent: {sent}\n❌ Failed: {failed}", parse_mode="HTML"
    )


# ── Owner stats command ──────────────────────────────────────────────────────
async def stats_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from config import OWNER_ID as OID
    if update.effective_user.id != OID:
        return
    from database import get_all_users
    users = await get_all_users()
    total = len(users)
    plans = {"free": 0, "basic": 0, "pro": 0}
    for u in users:
        p = u.get("plan", "free")
        plans[p] = plans.get(p, 0) + 1

    await update.message.reply_text(
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👥 Total Users: <b>{total}</b>\n"
        f"🆓 Free: <b>{plans['free']}</b>\n"
        f"⭐ Basic: <b>{plans['basic']}</b>\n"
        f"👑 Pro: <b>{plans['pro']}</b>",
        parse_mode="HTML"
    )


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    # ── Core commands ────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",       start_cmd))
    app.add_handler(CommandHandler("help",        help_cmd))
    app.add_handler(CommandHandler("account",     account_cmd))
    app.add_handler(CommandHandler("premium",     premium_cmd))

    # ── PDF commands ─────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("compress",    cmd_compress))
    app.add_handler(CommandHandler("split",       cmd_split))
    app.add_handler(CommandHandler("merge",       cmd_merge))
    app.add_handler(CommandHandler("lock",        cmd_lock))
    app.add_handler(CommandHandler("unlock",      cmd_unlock))
    app.add_handler(CommandHandler("repair",      cmd_repair))
    app.add_handler(CommandHandler("watermark",   cmd_watermark))
    app.add_handler(CommandHandler("darkmode",    cmd_darkmode))
    app.add_handler(CommandHandler("pagenos",     cmd_pagenos))
    app.add_handler(CommandHandler("pdf2img",     cmd_pdf2img))
    app.add_handler(CommandHandler("img2pdf",     cmd_img2pdf))
    app.add_handler(CommandHandler("excel",       cmd_excel))
    app.add_handler(CommandHandler("bgchange",    cmd_bgchange))
    app.add_handler(CommandHandler("handwrite",   cmd_handwrite))
    app.add_handler(CommandHandler("ocr",         cmd_ocr))
    app.add_handler(CommandHandler("rotate",      cmd_rotate))
    app.add_handler(CommandHandler("resize",      cmd_resize))
    app.add_handler(CommandHandler("addtext",     cmd_addtext))
    app.add_handler(CommandHandler("footer",      cmd_footer))
    app.add_handler(CommandHandler("extract",     cmd_extract))
    app.add_handler(CommandHandler("metadata",    cmd_metadata))

    # ── Owner-only commands ──────────────────────────────────────────────────
    app.add_handler(CommandHandler("givepremium", grant_premium_cmd))
    app.add_handler(CommandHandler("broadcast",   broadcast_cmd))
    app.add_handler(CommandHandler("stats",       stats_cmd))

    # ── Callback queries ─────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(buy_plan_callback,       pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(pay_screenshot_callback, pattern="^pay_ss_"))
    app.add_handler(CallbackQueryHandler(menu_callback))

    # ── Messages ─────────────────────────────────────────────────────────────
    app.add_handler(MessageHandler(
        (filters.Document.ALL | filters.PHOTO | filters.TEXT) & ~filters.COMMAND,
        handle_message
    ))

    # ── Error handler ────────────────────────────────────────────────────────
    app.add_error_handler(error_handler)

    return app


# ── Aiohttp web server (Render health checks) ────────────────────────────────
async def health(request):
    return web.Response(text="🤖 PDF Doctor Bot v2.0 — Running!", status=200)

async def run_web_server():
    wa = web.Application()
    wa.router.add_get("/", health)
    wa.router.add_get("/health", health)
    runner = web.AppRunner(wa)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Web server on port {PORT}")


# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return

    # Download fonts at startup
    logger.info("⬇️  Downloading handwriting fonts...")
    try:
        from utils.font_loader import download_fonts
        download_fonts()
    except Exception as e:
        logger.warning(f"Font download issue: {e}")

    tg_app = build_app()

    # Set commands
    async with tg_app:
        try:
            await tg_app.bot.set_my_commands(BOT_COMMANDS)
            logger.info("✅ Bot commands set")
        except Exception as e:
            logger.warning(f"Could not set commands: {e}")

    # Start web server + bot
    await run_web_server()

    logger.info("🚀 Starting PDF Doctor Bot v2.0...")
    async with tg_app:
        await tg_app.start()
        await tg_app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        logger.info("✅ Bot is LIVE! @SerenaXdev")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
