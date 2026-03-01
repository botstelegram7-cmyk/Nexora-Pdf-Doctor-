import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import OWNER_ID, BASIC_LABEL, PRO_LABEL, BASIC_PRICE, PRO_PRICE, UPI_ID, UPI_QR_URL
from database import set_premium, get_plan, save_payment_request, ensure_user, get_user
from utils.keyboards import premium_menu, confirm_payment_menu, back_btn
from utils.decorators import owner_only


async def premium_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    plan = await get_plan(user.id)
    data = await get_user(user.id)
    expiry = "N/A"
    if data:
        e = data.get("plan_expiry")
        if e and e != "None":
            expiry = e[:10]

    plan_emoji = {"free": "🆓", "basic": "⭐", "pro": "👑"}.get(plan, "🆓")
    text = (
        "💎 <b>Premium Plans</b>\n\n"
        "╔══════════════════════╗\n"
        f"║  {plan_emoji} Current: <b>{plan.capitalize()}</b>  ║\n"
        f"║  📅 Expires: <code>{expiry}</code>    ║\n"
        "╠══════════════════════╣\n"
        f"║  ⭐ <b>Basic — {BASIC_PRICE}/month</b>   ║\n"
        "║    ✅ Unlimited operations  ║\n"
        "║    ✅ All PDF tools         ║\n"
        "║    ✅ Priority processing   ║\n"
        "╠══════════════════════╣\n"
        f"║  👑 <b>Pro — {PRO_PRICE}/year</b>      ║\n"
        "║    ✅ Everything in Basic   ║\n"
        "║    ✅ Valid 1 full year      ║\n"
        "║    ✅ New features first     ║\n"
        "╚══════════════════════╝\n\n"
        "👇 <b>Select a plan to pay:</b>"
    )
    await update.effective_message.reply_text(
        text, parse_mode="HTML", reply_markup=premium_menu()
    )


async def buy_plan_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("💎 Loading payment details...", show_alert=False)
    plan  = "basic" if query.data == "buy_basic" else "pro"
    price = BASIC_PRICE if plan == "basic" else PRO_PRICE
    duration = "1 Month" if plan == "basic" else "1 Year (Best Value!)"
    label = BASIC_LABEL if plan == "basic" else PRO_LABEL

    text = (
        f"💳 <b>Payment Details</b>\n\n"
        f"╔══════════════════════╗\n"
        f"║  📦 Plan: <b>{label}</b>\n"
        f"║  💰 Amount: <b>{price}</b>\n"
        f"║  ⏳ Duration: <b>{duration}</b>\n"
        f"╚══════════════════════╝\n\n"
    )

    if UPI_ID:
        text += f"📲 <b>UPI ID:</b>\n<code>{UPI_ID}</code>\n\n"

    text += (
        "📋 <b>How to pay:</b>\n"
        f"  1️⃣ Open any UPI app (GPay/PhonePe/Paytm)\n"
        f"  2️⃣ Pay <b>{price}</b> to the UPI ID above\n"
        f"  3️⃣ Take screenshot of payment success\n"
        f"  4️⃣ Tap button below &amp; send the screenshot\n\n"
        "⚡ <b>Activation within minutes!</b>"
    )

    ctx.user_data["pending_plan"] = plan

    if UPI_QR_URL:
        try:
            await query.message.reply_photo(
                photo=UPI_QR_URL, caption=text,
                parse_mode="HTML", reply_markup=confirm_payment_menu(plan)
            )
            return
        except Exception:
            pass

    await query.message.reply_text(text, parse_mode="HTML", reply_markup=confirm_payment_menu(plan))


async def pay_screenshot_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("📸 Ready! Send your screenshot now.", show_alert=True)
    plan = query.data.replace("pay_ss_", "")
    ctx.user_data["awaiting_payment_ss"] = plan

    await query.message.reply_text(
        "📸 <b>Send your payment screenshot now!</b>\n\n"
        "Just send the image directly in this chat.\n"
        "Our team will verify and activate your plan within minutes! ⚡",
        parse_mode="HTML",
        reply_markup=back_btn()
    )


async def handle_payment_screenshot(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    if "awaiting_payment_ss" not in ctx.user_data:
        return False

    plan    = ctx.user_data.pop("awaiting_payment_ss")
    user    = update.effective_user
    file_id = update.message.photo[-1].file_id

    await save_payment_request(user.id, plan, file_id)

    price   = "₹99" if plan == "basic" else "₹249"
    caption = (
        f"💳 <b>New Payment Request!</b>\n\n"
        f"👤 User: <a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📱 Username: @{user.username or 'N/A'}\n"
        f"📦 Plan: <b>{plan.capitalize()}</b>\n"
        f"💰 Amount: <b>{price}</b>\n\n"
        f"✅ To approve:\n"
        f"<code>/givepremium {user.id} {plan}</code>"
    )

    try:
        await ctx.bot.send_photo(
            chat_id=OWNER_ID, photo=file_id,
            caption=caption, parse_mode="HTML"
        )
    except Exception:
        pass

    await update.message.reply_text(
        "✅ <b>Screenshot received!</b>\n\n"
        "🔍 Our team will verify your payment.\n"
        "⚡ Premium will be activated <b>within minutes!</b>\n\n"
        "You'll get a notification once it's done! 🎉",
        parse_mode="HTML",
        reply_markup=back_btn()
    )
    return True


@owner_only
async def grant_premium_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Usage: /givepremium <user_id> basic|pro"""
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ <b>Usage:</b>\n"
            "<code>/givepremium &lt;user_id&gt; basic</code>\n"
            "<code>/givepremium &lt;user_id&gt; pro</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(args[0])
        plan_type = args[1].lower()
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!", parse_mode="HTML")
        return

    if plan_type not in ("basic", "pro"):
        await update.message.reply_text(
            "❌ Plan must be <code>basic</code> or <code>pro</code>", parse_mode="HTML"
        )
        return

    now = datetime.datetime.now()
    expiry = now + datetime.timedelta(days=30 if plan_type == "basic" else 365)

    await ensure_user(target_id, "Unknown", "")
    await set_premium(target_id, plan_type, expiry)

    plan_emoji = "⭐" if plan_type == "basic" else "👑"
    duration   = "1 Month" if plan_type == "basic" else "1 Year"

    # Confirm to owner
    await update.message.reply_text(
        f"✅ <b>Premium Granted!</b>\n\n"
        f"{plan_emoji} Plan: <b>{plan_type.capitalize()}</b>\n"
        f"👤 User ID: <code>{target_id}</code>\n"
        f"⏳ Duration: <b>{duration}</b>\n"
        f"📅 Expires: <code>{expiry.strftime('%Y-%m-%d')}</code>",
        parse_mode="HTML"
    )

    # Notify the user with their new plan details
    try:
        await ctx.bot.send_message(
            chat_id=target_id,
            text=(
                f"🎉 <b>Your Premium is Active!</b>\n\n"
                f"╔══════════════════════╗\n"
                f"║  {plan_emoji} Plan: <b>{plan_type.capitalize()}</b>       ║\n"
                f"║  📅 Expires: <code>{expiry.strftime('%d %B %Y')}</code> ║\n"
                f"║  ✅ Status: <b>ACTIVE</b>        ║\n"
                f"╚══════════════════════╝\n\n"
                f"🚀 You now have <b>unlimited operations</b>!\n"
                f"Use /account to see your updated profile.\n\n"
                f"Enjoy PDF Doctor Bot! 💎"
            ),
            parse_mode="HTML",
            reply_markup=back_btn()
        )
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Could not notify user (they may not have started the bot): {e}",
            parse_mode="HTML"
        )
