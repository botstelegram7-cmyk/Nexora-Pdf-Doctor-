import functools
from telegram import Update
from telegram.ext import ContextTypes
from database import get_plan, get_usage, increment_usage, ensure_user
from config import FREE_DAILY_LIMIT, REACTIONS
from utils.keyboards import back_btn
import random

async def _react(update: Update):
    """Add a random emoji reaction to user message"""
    try:
        from telegram import ReactionTypeEmoji
        emoji = random.choice(REACTIONS)
        await update.message.set_reaction([ReactionTypeEmoji(emoji)])
    except Exception:
        pass  # reactions may not be supported in all contexts

def pdf_feature(func):
    """Decorator: checks usage limit, reacts, increments counter"""
    @functools.wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        await ensure_user(user.id, user.full_name, user.username or "")

        plan  = await get_plan(user.id)
        usage = await get_usage(user.id)

        if plan == "free" and usage >= FREE_DAILY_LIMIT:
            await update.effective_message.reply_text(
                f"⚠️ **Daily Limit Reached!**\n\n"
                f"🆓 Free users get **{FREE_DAILY_LIMIT} operations/day**.\n"
                f"Upgrade to premium for unlimited access! 🚀",
                parse_mode="Markdown",
                reply_markup=back_btn()
            )
            return

        if update.message:
            await _react(update)

        await increment_usage(user.id)
        return await func(update, ctx, *args, **kwargs)
    return wrapper

def owner_only(func):
    @functools.wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from config import OWNER_ID
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("🚫 **Owner only command!**", parse_mode="Markdown")
            return
        return await func(update, ctx, *args, **kwargs)
    return wrapper
