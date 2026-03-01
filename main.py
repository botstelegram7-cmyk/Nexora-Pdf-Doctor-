"""
PDF Doctor Bot — Main entry point
GitHub: @SerenaXdev
"""
import asyncio, logging, os
from aiohttp import web
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from config import BOT_TOKEN, PORT

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Import handlers ──────────────────────────────────────────────────────────
from handlers.start_handler import start_cmd, help_cmd, account_cmd
from handlers.pdf_handler import (
    menu_callback, handle_message,
    cmd_compress, cmd_split, cmd_merge, cmd_lock, cmd_unlock,
    cmd_repair, cmd_watermark, cmd_darkmode, cmd_pagenos,
    cmd_pdf2img, cmd_img2pdf, cmd_excel, cmd_bgchange,
    cmd_handwrite, cmd_ocr,
)
from handlers.premium_handler import (
    premium_cmd, grant_premium_cmd,
    buy_plan_callback, pay_screenshot_callback
)

BOT_COMMANDS = [
    BotCommand("start",     "🏠 Main Menu"),
    BotCommand("help",      "❓ Help & Commands"),
    BotCommand("account",   "👤 My Account"),
    BotCommand("premium",   "💎 Premium Plans"),
    BotCommand("compress",  "📐 Compress PDF"),
    BotCommand("split",     "✂️ Split PDF"),
    BotCommand("merge",     "🔗 Merge PDFs"),
    BotCommand("lock",      "🔒 Lock PDF"),
    BotCommand("unlock",    "🔓 Unlock PDF"),
    BotCommand("repair",    "🧩 Repair PDF"),
    BotCommand("watermark", "🌊 Add Watermark"),
    BotCommand("darkmode",  "🌙 Dark Mode"),
    BotCommand("pagenos",   "🔢 Page Numbers"),
    BotCommand("pdf2img",   "🖼️ PDF to Images"),
    BotCommand("img2pdf",   "🖼️ Images to PDF"),
    BotCommand("excel",     "📊 PDF to Excel"),
    BotCommand("bgchange",  "🎨 BG Changer"),
    BotCommand("handwrite", "✍️ Handwritten PDF"),
    BotCommand("ocr",       "🔍 OCR Extract Text"),
]

def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    # ── Command handlers ─────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",     start_cmd))
    app.add_handler(CommandHandler("help",      help_cmd))
    app.add_handler(CommandHandler("account",   account_cmd))
    app.add_handler(CommandHandler("premium",   premium_cmd))

    # PDF tool commands
    app.add_handler(CommandHandler("compress",  cmd_compress))
    app.add_handler(CommandHandler("split",     cmd_split))
    app.add_handler(CommandHandler("merge",     cmd_merge))
    app.add_handler(CommandHandler("lock",      cmd_lock))
    app.add_handler(CommandHandler("unlock",    cmd_unlock))
    app.add_handler(CommandHandler("repair",    cmd_repair))
    app.add_handler(CommandHandler("watermark", cmd_watermark))
    app.add_handler(CommandHandler("darkmode",  cmd_darkmode))
    app.add_handler(CommandHandler("pagenos",   cmd_pagenos))
    app.add_handler(CommandHandler("pdf2img",   cmd_pdf2img))
    app.add_handler(CommandHandler("img2pdf",   cmd_img2pdf))
    app.add_handler(CommandHandler("excel",     cmd_excel))
    app.add_handler(CommandHandler("bgchange",  cmd_bgchange))
    app.add_handler(CommandHandler("handwrite", cmd_handwrite))
    app.add_handler(CommandHandler("ocr",       cmd_ocr))

    # Owner premium grant  — takes priority
    app.add_handler(CommandHandler("givepremium", grant_premium_cmd))

    # ── Callback query handlers ──────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(buy_plan_callback,     pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(pay_screenshot_callback, pattern="^pay_ss_"))
    app.add_handler(CallbackQueryHandler(menu_callback))

    # ── Message handlers ─────────────────────────────────────────────────────
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    return app


# ── Aiohttp health check (for Render) ───────────────────────────────────────
async def health(request):
    return web.Response(text="🤖 PDF Doctor Bot is running!", status=200)

async def run_web_server():
    web_app = web.Application()
    web_app.router.add_get("/", health)
    web_app.router.add_get("/health", health)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Web server running on port {PORT}")


# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return

    tg_app = build_app()

    # Set bot commands
    async with tg_app:
        await tg_app.bot.set_my_commands(BOT_COMMANDS)

    # Run web server + bot concurrently
    await run_web_server()

    logger.info("🚀 Starting PDF Doctor Bot...")
    async with tg_app:
        await tg_app.start()
        await tg_app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        logger.info("✅ Bot is live!")
        # Keep running
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
