import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── ENV Variables ───────────────────────────────────────────────────────────
BOT_TOKEN      = os.environ["BOT_TOKEN"]
GROK_API_KEY   = os.environ["GROK_API_KEY"]
OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "xuoqui_xin").lstrip("@")
OWNER_ID       = int(os.environ.get("OWNER_ID", "6518065496"))  # ← Hardcoded + ENV override

GROK_API_URL   = "https://api.x.ai/v1/chat/completions"
GROK_MODEL     = os.environ.get("GROK_MODEL", "grok-3-latest")

# ─── Owner Check (ID ya Username dono se) ────────────────────────────────────
def is_owner(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    # User ID se check (most reliable)
    if user.id == OWNER_ID:
        return True
    # Username se check (fallback)
    if user.username and user.username.lower() == OWNER_USERNAME.lower():
        return True
    return False

def owner_only(func):
    """Decorator: sirf owner ke liye"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_owner(update):
            logger.warning(f"Access denied for user: id={update.effective_user.id}, username=@{update.effective_user.username}")
            await update.message.reply_text(
                "⛔ *Access Denied!*\n\nYe bot sirf owner ke liye hai.",
                parse_mode="Markdown"
            )
            return
        return await func(update, context)
    return wrapper

# ─── Grok AI Call ────────────────────────────────────────────────────────────
def ask_grok(prompt: str, system_prompt: str = None) -> str:
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": GROK_MODEL,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.7
    }

    try:
        res = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.Timeout:
        return "⏳ Grok ne reply dene mein bohot time liya. Phir try karo!"
    except requests.exceptions.HTTPError as e:
        logger.error(f"Grok HTTP Error: {e}")
        return f"❌ Grok API Error: {res.status_code} - {res.text}"
    except Exception as e:
        logger.error(f"Grok Error: {e}")
        return "❌ Kuch gadbad ho gayi Grok se baat karte waqt."

# ─── Inline Keyboard Helper ──────────────────────────────────────────────────
def main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🤖 Ask Grok", callback_data="ask_grok"),
            InlineKeyboardButton("📊 Status",   callback_data="status"),
        ],
        [
            InlineKeyboardButton("ℹ️ Help",     callback_data="help"),
            InlineKeyboardButton("👤 Owner",    url=f"https://t.me/{OWNER_USERNAME}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# ─── /start ──────────────────────────────────────────────────────────────────
@owner_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👋 *Salam {user.first_name}!*\n\n"
        f"Main hoon *Grok AI Bot* 🤖\n"
        f"Powered by `{GROK_MODEL}`\n\n"
        f"Neeche se koi option chuno ya seedha message karo!"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

# ─── /ask ─────────────────────────────────────────────────────────────────────
@owner_only
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("❗ Usage: `/ask <tumhara sawaal>`", parse_mode="Markdown")
        return

    await update.message.chat.send_action("typing")
    response = ask_grok(query)
    await update.message.reply_text(f"🤖 *Grok ka Jawab:*\n\n{response}", parse_mode="Markdown")

# ─── /imagine ────────────────────────────────────────────────────────────────
@owner_only
async def imagine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❗ Usage: `/imagine <description>`", parse_mode="Markdown")
        return

    await update.message.chat.send_action("typing")
    result = ask_grok(
        prompt,
        system_prompt="You are a creative image description AI. Describe vivid, detailed imagery based on user prompts."
    )
    await update.message.reply_text(f"🎨 *Grok ki Imagination:*\n\n{result}", parse_mode="Markdown")

# ─── /clear ──────────────────────────────────────────────────────────────────
@owner_only
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🗑️ *Context clear ho gaya!*", parse_mode="Markdown")

# ─── /status ─────────────────────────────────────────────────────────────────
@owner_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test = ask_grok("Reply with only: OK")
    grok_status = "✅ Online" if "OK" in test.upper() else f"⚠️ {test}"
    text = (
        f"📊 *Bot Status*\n\n"
        f"🤖 Bot: ✅ Running\n"
        f"🧠 Grok API: {grok_status}\n"
        f"👤 Owner: @{OWNER_USERNAME}\n"
        f"🆔 Owner ID: `{OWNER_ID}`\n"
        f"🔧 Model: `{GROK_MODEL}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─── /help ───────────────────────────────────────────────────────────────────
@owner_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Commands List:*\n\n"
        "▸ `/start` — Bot start karo\n"
        "▸ `/ask <sawaal>` — Grok se poochho\n"
        "▸ `/imagine <desc>` — Creative response lo\n"
        "▸ `/status` — Bot + API status dekho\n"
        "▸ `/clear` — Context clear karo\n"
        "▸ `/help` — Ye message\n\n"
        "💬 Ya seedha message karo, Grok reply karega!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─── Free Text Message (Owner only) ──────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔ Access Denied.")
        return

    user_text = update.message.text
    await update.message.chat.send_action("typing")
    response = ask_grok(user_text)
    await update.message.reply_text(f"🤖 {response}")

# ─── Callback Query Handler ───────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    if user.id != OWNER_ID and (not user.username or user.username.lower() != OWNER_USERNAME.lower()):
        await query.message.reply_text("⛔ Access Denied.")
        return

    data = query.data

    if data == "ask_grok":
        await query.message.reply_text(
            "💬 Apna sawaal type karo aur bhejo — Grok jawab dega!",
            parse_mode="Markdown"
        )

    elif data == "status":
        test = ask_grok("Reply with only: OK")
        grok_status = "✅ Online" if "OK" in test.upper() else "⚠️ Issue"
        await query.message.reply_text(
            f"📊 *Status*\n\n🤖 Bot: ✅\n🧠 Grok: {grok_status}\n🔧 Model: `{GROK_MODEL}`",
            parse_mode="Markdown"
        )

    elif data == "help":
        text = (
            "📖 *Commands:*\n\n"
            "▸ `/ask <sawaal>` — Grok se poochho\n"
            "▸ `/imagine <desc>` — Creative response\n"
            "▸ `/status` — API status\n"
            "▸ `/clear` — Context clear\n\n"
            "Ya seedha message karo!"
        )
        await query.message.reply_text(text, parse_mode="Markdown")
