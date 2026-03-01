import random
from telegram import Update
from telegram.ext import ContextTypes
from config import START_IMAGE, OWNER_ID, FREE_DAILY_LIMIT, REACTIONS, BOT_VERSION, GITHUB
from database import ensure_user, get_plan, get_usage, get_user
from utils.keyboards import main_menu, back_btn, premium_menu

WELCOME_EMOJIS = ["🔥","💎","🚀","⚡","🌟","🎉","👑","✨","🎊","🤩"]

def _esc(text: str) -> str:
    """Escape HTML special chars"""
    return str(text).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

async def _react(update: Update):
    try:
        from telegram import ReactionTypeEmoji
        emoji = random.choice(REACTIONS)
        await update.message.set_reaction([ReactionTypeEmoji(emoji)])
    except Exception:
        pass


async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await ensure_user(user.id, user.full_name, user.username or "")

    plan  = await get_plan(user.id)
    usage = await get_usage(user.id)
    e1    = random.choice(WELCOME_EMOJIS)
    e2    = random.choice(WELCOME_EMOJIS)

    plan_badge = {
        "free":  "🆓 <b>Free</b>",
        "basic": "⭐ <b>Basic</b>",
        "pro":   "👑 <b>Pro</b>",
    }.get(plan, "🆓 <b>Free</b>")

    remaining = "∞ Unlimited" if plan != "free" else f"{max(0, FREE_DAILY_LIMIT - usage)}/{FREE_DAILY_LIMIT}"

    text = (
        f"{e1} <b>Welcome, {_esc(user.first_name)}!</b> {e2}\n\n"
        f"🤖 I am <b>PDF Doctor Bot</b> — your all-in-one PDF powerhouse!\n\n"
        f"╔══════════════════════╗\n"
        f"║  👤 <b>YOUR ACCOUNT</b>        ║\n"
        f"╠══════════════════════╣\n"
        f"║  Plan : {plan_badge}\n"
        f"║  Uses : <code>{remaining}</code> today\n"
        f"╚══════════════════════╝\n\n"
        f"<b>🛠️ What I can do:</b>\n"
        f"  📄 Compress · Split · Merge\n"
        f"  🔐 Lock · Unlock · Repair\n"
        f"  🌊 Watermark · Dark Mode · BG\n"
        f"  📊 PDF→Excel · Page Numbers\n"
        f"  🖼️ PDF↔Images Converter\n"
        f"  ✍️ Handwritten PDF (8 fonts!)\n"
        f"  👁️ OCR: Extract Text from Image\n"
        f"  🔄 Rotate · Resize · Add Text\n"
        f"  📋 Metadata Viewer · Footer\n\n"
        f"👇 <b>Choose a tool below to start!</b>"
    )

    kb = main_menu()

    if update.message:
        await _react(update)

    if START_IMAGE:
        try:
            await update.message.reply_photo(
                photo=START_IMAGE, caption=text,
                parse_mode="HTML", reply_markup=kb
            )
            return
        except Exception:
            pass

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "❓ <b>PDF Doctor Bot — All Commands</b>\n\n"
        "╔══════════════════════╗\n"
        "║  📋 BASIC COMMANDS        ║\n"
        "╠══════════════════════╣\n"
        "║  /start — Main menu       ║\n"
        "║  /help — This message     ║\n"
        "║  /account — My account    ║\n"
        "║  /premium — View plans    ║\n"
        "╚══════════════════════╝\n\n"
        "<b>📄 PDF Tools:</b>\n"
        "  /compress — Shrink PDF size\n"
        "  /split — Split into pages\n"
        "  /merge — Merge multiple PDFs\n"
        "  /lock — Set password\n"
        "  /unlock — Remove password\n"
        "  /repair — Fix corrupted PDF\n\n"
        "<b>🎨 Visual:</b>\n"
        "  /watermark — Add watermark\n"
        "  /darkmode — Dark theme\n"
        "  /bgchange — Change background\n"
        "  /rotate — Rotate pages\n"
        "  /resize — Resize pages\n\n"
        "<b>🔄 Convert:</b>\n"
        "  /pdf2img — PDF to images\n"
        "  /img2pdf — Images to PDF\n"
        "  /excel — PDF to Excel\n\n"
        "<b>✨ Creative:</b>\n"
        "  /handwrite — Handwritten style\n"
        "  /pagenos — Add page numbers\n"
        "  /addtext — Add text to PDF\n"
        "  /footer — Add custom footer\n\n"
        "<b>🔍 Extract:</b>\n"
        "  /ocr — Extract text (OCR)\n"
        "  /metadata — View PDF info\n"
        "  /extract — Extract pages\n\n"
        "╔══════════════════════╗\n"
        f"║  🆓 Free: <b>3 ops/day</b>        ║\n"
        f"║  ⭐ Basic: <b>∞ Unlimited</b>      ║\n"
        f"║  👑 Pro: <b>∞ + 1 Year</b>        ║\n"
        "╚══════════════════════╝\n\n"
        f"🛠️ v{BOT_VERSION} · Made by <code>{GITHUB}</code>"
    )
    await update.effective_message.reply_text(
        text, parse_mode="HTML", reply_markup=back_btn()
    )


async def account_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    plan  = await get_plan(user.id)
    usage = await get_usage(user.id)
    data  = await get_user(user.id)

    expiry = "N/A"
    joined = "N/A"
    if data:
        expiry_raw = data.get("plan_expiry")
        if expiry_raw and expiry_raw != "None":
            try:
                expiry = expiry_raw[:10]
            except Exception:
                expiry = "N/A"
        joined_raw = data.get("joined_at", "")
        if joined_raw:
            try:
                joined = joined_raw[:10]
            except Exception:
                joined = "N/A"

    plan_emoji = {"free": "🆓", "basic": "⭐", "pro": "👑"}.get(plan, "🆓")
    plan_name  = {"free": "Free", "basic": "Basic", "pro": "Pro"}.get(plan, "Free")
    remaining  = "∞" if plan != "free" else str(max(0, FREE_DAILY_LIMIT - usage))
    username   = _esc(f"@{user.username}") if user.username else "Not set"

    text = (
        f"👤 <b>Your Account Info</b>\n\n"
        f"╔══════════════════════╗\n"
        f"║  🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"║  👤 <b>Name:</b> {_esc(user.full_name)}\n"
        f"║  📱 <b>Username:</b> {username}\n"
        f"║  📅 <b>Joined:</b> {joined}\n"
        f"╠══════════════════════╣\n"
        f"║  {plan_emoji} <b>Plan:</b> {plan_name}\n"
        f"║  📅 <b>Expires:</b> {expiry}\n"
        f"║  📊 <b>Today:</b> {usage} used · {remaining} left\n"
        f"╚══════════════════════╝\n\n"
    )

    if plan == "free":
        text += (
            "💡 <b>Upgrade to Premium</b> for unlimited operations!\n"
            "Use /premium to view plans."
        )
    else:
        text += f"✅ <b>Enjoy your {plan_name} plan!</b>"

    await update.effective_message.reply_text(
        text, parse_mode="HTML", reply_markup=back_btn()
    )
