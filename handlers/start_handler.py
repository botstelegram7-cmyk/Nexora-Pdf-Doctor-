"""
Start Handler v4.1 — Upgraded UI/UX + fixed reactions.

REACTION FIX: Telegram Bot API allows setting reactions BUT:
  - Only specific emoji are valid reaction types (not all emoji)
  - Some bots can only set 1 reaction per message
  - We try 1 valid emoji, silent fallback if it fails
  - We cycle through different reactions for variety
"""
import random, html
from telegram import Update
from telegram.ext import ContextTypes
from config import BOT_VERSION, GITHUB, REACTIONS, OWNER_ID
from database import ensure_user, get_plan, get_usage, get_user
from utils.keyboards import main_menu, back_btn, premium_menu

# ── Valid Telegram reaction emoji (Bot API 7.0 approved list) ────────────────
# Only these specific emoji work as reactions — others silently fail!
VALID_REACTIONS = [
    "👍","👎","❤","🔥","🥰","👏","😁","🤔","🤯","😱",
    "🎉","🤩","🙏","👌","🕊","🤝","🫡","🏆","❤‍🔥","🌚",
    "⚡","🍓","🎊","🥺","😍","🌟","🤣","💯","🙈","💋",
]

def _esc(text: str) -> str:
    return html.escape(str(text))

async def _react(update: Update):
    """
    Send a single VALID reaction emoji.
    Telegram bots can only set 1 reaction (not multiple).
    We pick randomly from the approved list for variety.
    """
    if not update.message:
        return
    try:
        from telegram import ReactionTypeEmoji
        emoji = random.choice(VALID_REACTIONS)
        await update.message.set_reaction([ReactionTypeEmoji(emoji)])
    except Exception:
        pass   # Always silent — reactions are decorative


async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Handle referral link: /start ref_12345
    ref_id = None
    if ctx.args:
        arg = ctx.args[0]
        if arg.startswith("ref_"):
            try:
                ref_id = int(arg[4:])
                if ref_id == user.id:
                    ref_id = None  # Can't refer yourself
            except ValueError:
                pass

    await ensure_user(user.id, user.full_name, user.username or "", referrer_id=ref_id)
    await _react(update)

    plan  = await get_plan(user.id)
    usage = await get_usage(user.id)

    from config import FEATURE_LIMITS, FREE_DAILY_LIMIT
    plan_badge = {
        "free":  "🆓 Free",
        "basic": "⭐ Basic",
        "pro":   "👑 Pro",
    }.get(plan, "🆓 Free")

    remaining = "∞" if plan != "free" else str(max(0, FREE_DAILY_LIMIT - usage))
    prog_bar  = _usage_bar(usage, FREE_DAILY_LIMIT if plan == "free" else 999)

    # Show referral bonus message
    ref_bonus = ""
    if ref_id:
        ref_bonus = "\n🎁 <b>Referral bonus applied!</b> Welcome gift activated.\n"

    welcome_msgs = [
        f"Namaste <b>{_esc(user.first_name)}</b>! 🙏",
        f"Welcome back <b>{_esc(user.first_name)}</b>! 🚀",
        f"Hey <b>{_esc(user.first_name)}</b>, ready to work? ⚡",
        f"<b>{_esc(user.first_name)}</b> aa gaye! Let's go! 🔥",
    ]

    text = (
        f"{'🆕 ' if ref_id else ''}{random.choice(welcome_msgs)}\n"
        f"{ref_bonus}\n"
        f"┌─────────────────────────┐\n"
        f"│  🤖  <b>NEXORA PDF DOCTOR</b>  │\n"
        f"│     <b>v{BOT_VERSION}</b> — All-in-One PDF Bot │\n"
        f"└─────────────────────────┘\n\n"
        f"<b>📊 Your Account</b>\n"
        f"├ 👤 {_esc(user.full_name)}\n"
        f"├ 🎖️ Plan: <b>{plan_badge}</b>\n"
        f"├ 📈 Today: <b>{usage}</b> ops used\n"
        f"├ 🎯 Remaining: <b>{remaining}</b>\n"
        f"└ {prog_bar}\n\n"
        f"<b>🛠️ 35+ Tools Available:</b>\n"
        f"  📄 <b>PDF</b>: Compress · Split · Merge · Repair\n"
        f"  🔐 <b>Security</b>: Lock · Unlock · Redact\n"
        f"  🎨 <b>Visual</b>: Dark Mode · Watermark · BG Color\n"
        f"  🔄 <b>Convert</b>: Word · PPT · Excel · Images\n"
        f"  ✍️ <b>Creative</b>: Handwriting · 8 Notebook Styles\n"
        f"  🔍 <b>Extract</b>: OCR (10 langs) · Metadata\n"
        f"  📐 <b>Pages</b>: Delete · Reorder · Reverse · Compare\n\n"
        f"👇 <b>Tap any button below to start!</b>"
    )

    from config import START_IMAGE
    kb = main_menu()
    if START_IMAGE:
        try:
            await update.message.reply_photo(photo=START_IMAGE, caption=text, parse_mode="HTML", reply_markup=kb)
            return
        except Exception:
            pass
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


def _usage_bar(used: int, total: int) -> str:
    """Compact usage progress bar."""
    if total >= 999:
        return "📊 Usage: ∞ Unlimited"
    pct    = min(used / total, 1.0)
    filled = round(pct * 8)
    bar    = "█" * filled + "░" * (8 - filled)
    return f"[{bar}] {used}/{total}"


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 <b>NEXORA PDF DOCTOR — Command Reference</b>\n\n"

        "┌── 📄 <b>PDF TOOLS</b>\n"
        "│  /compress — Shrink file size\n"
        "│  /split    — Split into pages\n"
        "│  /merge    — Combine multiple PDFs\n"
        "│  /repair   — Fix corrupted PDFs\n"
        "│  /crop     — Auto-crop white margins\n"
        "│  /reverse  — Flip page order\n"
        "│  /compare  — Diff two PDFs\n"
        "└──\n\n"

        "┌── 🔐 <b>SECURITY</b>\n"
        "│  /lock     — Password protect\n"
        "│  /unlock   — Remove password\n"
        "└──\n\n"

        "┌── 🎨 <b>VISUAL</b>\n"
        "│  /darkmode  — Dark theme PDF\n"
        "│  /watermark — Text/logo watermark\n"
        "│  /bgchange  — Change background color\n"
        "│  /rotate    — Rotate pages\n"
        "│  /resize    — Resize to A4\n"
        "└──\n\n"

        "┌── 🔄 <b>CONVERT</b>\n"
        "│  /pdf2word — PDF → Word DOCX\n"
        "│  /pdf2ppt  — PDF → PowerPoint ⭐\n"
        "│  /pdf2img  — PDF → Images\n"
        "│  /img2pdf  — Images → PDF\n"
        "│  /excel    — PDF → Excel\n"
        "└──\n\n"

        "┌── ✨ <b>CREATIVE</b>\n"
        "│  /handwrite — Handwritten PDF (14 fonts!)\n"
        "│  /pagenos   — Add page numbers\n"
        "│  /addtext   — Add custom text\n"
        "│  /footer    — Add footer\n"
        "│  /qr        — Generate QR code\n"
        "└──\n\n"

        "┌── 📐 <b>PAGES</b>\n"
        "│  /extract      — Extract page range\n"
        "│  /delete_pages — Remove pages\n"
        "│  /reorder      — Reorder pages\n"
        "│  /reverse      — Reverse order\n"
        "└──\n\n"

        "┌── 🔍 <b>EXTRACT</b>\n"
        "│  /ocr      — Extract text (10 languages)\n"
        "│  /metadata — View PDF info\n"
        "└──\n\n"

        "┌── 👤 <b>ACCOUNT</b>\n"
        "│  /account   — Profile & plan\n"
        "│  /dashboard — Usage stats\n"
        "│  /premium   — Upgrade plan\n"
        "│  /lang      — Change language\n"
        "└──\n\n"

        "┌── 💎 <b>PLANS</b>\n"
        "│  🆓 Free:  5 ops/day (limited features)\n"
        "│  ⭐ Basic: Unlimited ops (most features)\n"
        "│  👑 Pro:   Everything + PDF→PPT + 1 year\n"
        "└──\n\n"
        f"🤖 <b>v{BOT_VERSION}</b> · <code>{GITHUB}</code>"
    )
    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())


async def account_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    plan  = await get_plan(user.id)
    usage = await get_usage(user.id)
    data  = await get_user(user.id)

    from config import FREE_DAILY_LIMIT, FEATURE_LIMITS

    expiry = joined = "—"
    total_ops = 0
    if data:
        raw = data.get("plan_expiry")
        if raw and raw != "None":
            expiry = str(raw)[:10]
        raw = data.get("joined_at", "")
        if raw:
            joined = str(raw)[:10]
        total_ops = data.get("total_ops", 0)

    plan_info = {
        "free":  ("🆓", "Free",  "#"),
        "basic": ("⭐", "Basic", "Unlimited"),
        "pro":   ("👑", "Pro",   "Unlimited"),
    }.get(plan, ("🆓", "Free", "#"))

    remaining = "∞" if plan != "free" else str(max(0, FREE_DAILY_LIMIT - usage))
    prog = _usage_bar(usage, FREE_DAILY_LIMIT if plan == "free" else 999)
    username = _esc(f"@{user.username}") if user.username else "—"

    # Per-feature limits summary
    limits_text = ""
    sample = [("compress","📐"), ("ocr","👁️"), ("handwrite","✍️"), ("pdf2ppt","📊")]
    for feat, icon in sample:
        lim = FEATURE_LIMITS.get(feat, {}).get(plan)
        val = "∞" if lim is None else ("🔒 Pro only" if lim == 0 else str(lim))
        limits_text += f"│  {icon} {feat.title()}: <b>{val}</b>/day\n"

    text = (
        f"👤 <b>Account Profile</b>\n\n"
        f"┌─────────────────────────┐\n"
        f"│  🆔 <code>{user.id}</code>\n"
        f"│  👤 {_esc(user.full_name)}\n"
        f"│  📱 {username}\n"
        f"│  📅 Joined: {joined}\n"
        f"└─────────────────────────┘\n\n"
        f"┌── 💎 <b>PLAN STATUS</b>\n"
        f"│  {plan_info[0]} Plan: <b>{plan_info[1]}</b>\n"
        f"│  📅 Expires: {expiry}\n"
        f"│  ⚡ All-time: <b>{total_ops}</b> operations\n"
        f"│  📊 Today: <b>{usage}</b> · {remaining} left\n"
        f"│  {prog}\n"
        f"└──\n\n"
        f"┌── 📈 <b>FEATURE LIMITS (today)</b>\n"
        f"{limits_text}"
        f"└──\n\n"
    )

    if plan == "free":
        text += (
            "💡 <b>Upgrade to unlock more:</b>\n"
            "  ⭐ Basic — ₹99/month — Unlimited ops\n"
            "  👑 Pro — ₹249/year — Everything!\n"
            "Use /premium to upgrade."
        )
    else:
        text += f"✅ <b>Enjoying {plan_info[1]} plan!</b> Keep creating 🚀"

    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())
