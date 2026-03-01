import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import OWNER_ID, BASIC_LABEL, PRO_LABEL, BASIC_PRICE, PRO_PRICE, UPI_ID, UPI_QR_URL
from database import set_premium, get_plan, save_payment_request, ensure_user
from utils.keyboards import premium_menu, confirm_payment_menu, back_btn
from utils.decorators import owner_only


async def premium_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    plan = await get_plan(update.effective_user.id)
    text = (
        "💎 **Premium Plans**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ **Basic — {BASIC_PRICE}/month**\n"
        f"   ✅ Unlimited operations/day\n"
        f"   ✅ All PDF tools\n"
        f"   ✅ Priority processing\n\n"
        f"👑 **Pro — {PRO_PRICE}/year**\n"
        f"   ✅ Everything in Basic\n"
        f"   ✅ 1 full year (best value!)\n"
        f"   ✅ Early access to new features\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Your current plan: **{plan.capitalize()}**\n\n"
        f"👇 Select a plan to proceed:"
    )
    await update.effective_message.reply_text(text, parse_mode="Markdown", reply_markup=premium_menu())


async def buy_plan_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = "basic" if query.data == "buy_basic" else "pro"
    price = BASIC_PRICE if plan == "basic" else PRO_PRICE
    duration = "1 Month" if plan == "basic" else "1 Year"
    label = BASIC_LABEL if plan == "basic" else PRO_LABEL

    text = (
        f"💳 **Payment Details**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Plan: **{label}**\n"
        f"💰 Amount: **{price}**\n"
        f"⏳ Duration: **{duration}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if UPI_ID:
        text += f"📲 **UPI ID:** `{UPI_ID}`\n\n"
    text += (
        f"📋 **Steps:**\n"
        f"1️⃣ Pay **{price}** via UPI\n"
        f"2️⃣ Take a screenshot of payment\n"
        f"3️⃣ Click the button below & send screenshot\n\n"
        f"✅ Premium will be activated within **minutes!**"
    )

    # Store pending plan in context
    ctx.user_data["pending_plan"] = plan

    if UPI_QR_URL:
        try:
            await query.message.reply_photo(photo=UPI_QR_URL, caption=text,
                                            parse_mode="Markdown",
                                            reply_markup=confirm_payment_menu(plan))
            return
        except Exception:
            pass

    await query.message.reply_text(text, parse_mode="Markdown", reply_markup=confirm_payment_menu(plan))


async def pay_screenshot_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data.replace("pay_ss_", "")
    ctx.user_data["awaiting_payment_ss"] = plan

    await query.message.reply_text(
        "📸 **Send your payment screenshot now!**\n\n"
        "Just send the image directly in this chat. "
        "Our team will verify and activate your plan shortly! ⚡",
        parse_mode="Markdown",
        reply_markup=back_btn()
    )


async def handle_payment_screenshot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Called when user sends a photo while awaiting payment SS"""
    if "awaiting_payment_ss" not in ctx.user_data:
        return False  # not expecting a payment screenshot

    plan = ctx.user_data.pop("awaiting_payment_ss")
    user = update.effective_user
    file_id = update.message.photo[-1].file_id

    await save_payment_request(user.id, plan, file_id)

    # Forward to owner
    caption = (
        f"💳 **New Payment Request!**\n\n"
        f"👤 User: [{user.full_name}](tg://user?id={user.id})\n"
        f"🆔 ID: `{user.id}`\n"
        f"📦 Plan: **{plan.capitalize()}**\n\n"
        f"To approve:\n"
        f"`/premium {user.id} {plan}`"
    )

    try:
        await ctx.bot.send_photo(chat_id=OWNER_ID, photo=file_id,
                                 caption=caption, parse_mode="Markdown")
    except Exception:
        pass

    await update.message.reply_text(
        "✅ **Screenshot received!**\n\n"
        "Our team will verify your payment and activate your premium plan shortly. "
        "You'll get a notification once it's activated! 🎉",
        parse_mode="Markdown",
        reply_markup=back_btn()
    )
    return True


@owner_only
async def grant_premium_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Usage: /premium <user_id> basic|pro"""
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/premium <user_id> basic` or `/premium <user_id> pro`",
            parse_mode="Markdown"
        )
        return

    try:
        target_id = int(args[0])
        plan_type = args[1].lower()
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")
        return

    if plan_type not in ("basic", "pro"):
        await update.message.reply_text("❌ Plan must be `basic` or `pro`", parse_mode="Markdown")
        return

    now = datetime.datetime.now()
    if plan_type == "basic":
        expiry = now + datetime.timedelta(days=30)
    else:  # pro
        expiry = now + datetime.timedelta(days=365)

    await ensure_user(target_id, "Unknown", "")
    await set_premium(target_id, plan_type, expiry)

    plan_emoji = "⭐" if plan_type == "basic" else "👑"
    duration = "1 Month" if plan_type == "basic" else "1 Year"

    await update.message.reply_text(
        f"✅ **Premium Granted!**\n\n"
        f"{plan_emoji} Plan: **{plan_type.capitalize()}**\n"
        f"👤 User ID: `{target_id}`\n"
        f"⏳ Duration: **{duration}**\n"
        f"📅 Expires: `{expiry.strftime('%Y-%m-%d')}`",
        parse_mode="Markdown"
    )

    # Notify user
    try:
        await ctx.bot.send_message(
            chat_id=target_id,
            text=(
                f"🎉 **Congratulations!**\n\n"
                f"{plan_emoji} Your **{plan_type.capitalize()} Plan** is now active!\n"
                f"📅 Valid till: **{expiry.strftime('%d %B %Y')}**\n\n"
                f"Enjoy unlimited PDF operations! 🚀"
            ),
            parse_mode="Markdown",
            reply_markup=back_btn()
        )
    except Exception:
        pass
