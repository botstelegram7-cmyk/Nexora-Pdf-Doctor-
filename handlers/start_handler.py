import random
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from config import START_IMAGE, OWNER_ID, FREE_DAILY_LIMIT, REACTIONS
from database import ensure_user, get_plan, get_usage
from utils.keyboards import main_menu, back_btn

WELCOME_EMOJIS = ["🔥","💎","🚀","⚡","🌟","🎉","👑","✨"]

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await ensure_user(user.id, user.full_name, user.username or "")

    plan  = await get_plan(user.id)
    usage = await get_usage(user.id)
    emoji = random.choice(WELCOME_EMOJIS)

    plan_badge = {
        "free":  "🆓 Free",
        "basic": "⭐ Basic",
        "pro":   "👑 Pro",
    }.get(plan, "🆓 Free")

    remaining = "∞" if plan != "free" else max(0, FREE_DAILY_LIMIT - usage)

    text = (
        f"{emoji} **Welcome, {user.first_name}!** {emoji}\n\n"
        f"🤖 I'm **PDF Doctor Bot** — your all-in-one PDF toolkit!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Your Account**\n"
        f"   • Plan: {plan_badge}\n"
        f"   • Today's uses left: **{remaining}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 **Available Tools:**\n"
        f"   📄 Compress · Split · Merge\n"
        f"   🔐 Lock · Unlock · Repair\n"
        f"   🌊 Watermark (Text/Logo/Invisible)\n"
        f"   🌙 Dark Mode · BG Changer\n"
        f"   📊 PDF→Excel · Page Numbers\n"
        f"   🖼️ PDF↔Images Converter\n"
        f"   ✍️ Handwritten Text (6 fonts!)\n"
        f"   🔍 OCR: Image/PDF→Text\n\n"
        f"👇 **Choose a tool to get started!**"
    )

    kb = main_menu()

    if START_IMAGE:
        try:
            await update.message.reply_photo(photo=START_IMAGE, caption=text,
                                             parse_mode="Markdown", reply_markup=kb)
            return
        except Exception:
            pass

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

    # Random reaction on start
    try:
        from telegram import ReactionTypeEmoji
        await update.message.set_reaction([ReactionTypeEmoji(random.choice(REACTIONS))])
    except Exception:
        pass


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "❓ **PDF Doctor Bot — Commands**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 **Basic Commands:**\n"
        "  /start — Main menu\n"
        "  /help — This help message\n"
        "  /account — My account info\n"
        "  /premium — View premium plans\n\n"
        "📄 **PDF Tools:**\n"
        "  /compress — Compress PDF size\n"
        "  /split — Split PDF pages\n"
        "  /merge — Merge multiple PDFs\n"
        "  /lock — Password protect PDF\n"
        "  /unlock — Remove PDF password\n"
        "  /repair — Fix corrupted PDF\n"
        "  /watermark — Add watermark\n"
        "  /darkmode — Dark mode PDF\n"
        "  /pagenos — Add page numbers\n"
        "  /pdf2img — PDF to Images\n"
        "  /img2pdf — Images to PDF\n"
        "  /excel — PDF to Excel\n"
        "  /bgchange — Change background\n\n"
        "✍️ **Creative:**\n"
        "  /handwrite — Handwritten style text\n\n"
        "🔍 **OCR:**\n"
        "  /ocr — Extract text from image/PDF\n\n"
        "💎 **Premium:**\n"
        "  /premium — View & buy plans\n"
        "  /account — Check your plan\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🆓 Free: **3 ops/day**\n"
        "⭐ Basic: **Unlimited** (₹99/month)\n"
        "👑 Pro: **Unlimited** (₹249/year)\n"
    )
    await update.effective_message.reply_text(text, parse_mode="Markdown", reply_markup=back_btn())


async def account_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    plan  = await get_plan(user.id)
    usage = await get_usage(user.id)
    from database import get_user
    data  = await get_user(user.id)
    expiry = data.get("plan_expiry", "N/A") if data else "N/A"

    plan_emoji = {"free": "🆓", "basic": "⭐", "pro": "👑"}.get(plan, "🆓")
    text = (
        f"👤 **Your Account**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 User ID: `{user.id}`\n"
        f"👤 Name: **{user.full_name}**\n"
        f"📱 Username: @{user.username or 'N/A'}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{plan_emoji} Plan: **{plan.capitalize()}**\n"
        f"📅 Expires: `{expiry[:10] if expiry and expiry != 'N/A' else 'N/A'}`\n"
        f"📊 Today's usage: **{usage}/{FREE_DAILY_LIMIT if plan == 'free' else '∞'}**\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    await update.effective_message.reply_text(text, parse_mode="Markdown", reply_markup=back_btn())
