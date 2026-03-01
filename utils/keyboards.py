"""
Keyboards — Beautiful inline UI with emoji decoration.
Note: Telegram does NOT support custom button colors for regular bots.
We use rich emoji + symbols to create visual hierarchy.
"""
from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as M
from config import FONTS, BASIC_LABEL, PRO_LABEL

def main_menu():
    return M([
        [B("╔══ 📄 PDF TOOLS ══╗", callback_data="noop")],
        [B("📐 Compress",  callback_data="menu_compress"),
         B("✂️ Split",      callback_data="menu_split"),
         B("🔗 Merge",     callback_data="menu_merge")],
        [B("╔══ 🔐 SECURITY ══╗", callback_data="noop")],
        [B("🔒 Lock PDF",   callback_data="do_lock"),
         B("🔓 Unlock PDF", callback_data="do_unlock"),
         B("🧩 Repair",     callback_data="menu_repair")],
        [B("╔══ 🎨 VISUAL ══╗", callback_data="noop")],
        [B("🌊 Watermark",  callback_data="menu_watermark"),
         B("🌙 Dark Mode",  callback_data="menu_dark"),
         B("🎨 BG Color",   callback_data="menu_bg")],
        [B("╔══ 🔄 CONVERT ══╗", callback_data="noop")],
        [B("🖼️ PDF→Imgs",  callback_data="menu_pdf2img"),
         B("🖼️ Imgs→PDF",  callback_data="menu_img2pdf"),
         B("📊 PDF→Excel", callback_data="menu_excel")],
        [B("╔══ ✨ CREATIVE ══╗", callback_data="noop")],
        [B("✍️ Handwriting",  callback_data="menu_hw"),
         B("🔢 Page Nos",    callback_data="menu_pageno"),
         B("📝 Add Text",    callback_data="menu_addtext")],
        [B("╔══ 🔍 EXTRACT ══╗", callback_data="noop")],
        [B("👁️ OCR Text",    callback_data="menu_ocr"),
         B("📋 Metadata",    callback_data="menu_meta"),
         B("🔖 Extract Pgs", callback_data="menu_extract")],
        [B("╔══ ⚙️ MORE TOOLS ══╗", callback_data="noop")],
        [B("🔄 Rotate PDF",  callback_data="menu_rotate"),
         B("📏 Resize PDF",  callback_data="menu_resize"),
         B("🗂️ Add Footer",  callback_data="menu_footer")],
        [B("╔══ 👤 ACCOUNT ══╗", callback_data="noop")],
        [B("👑 Premium Plans", callback_data="menu_premium"),
         B("📊 My Account",   callback_data="menu_account")],
        [B("❓ Help & All Commands", callback_data="menu_help")],
    ])

def font_menu():
    rows = [[B("┌─ ✍️ CHOOSE HANDWRITING FONT ─┐", callback_data="noop")]]
    items = list(FONTS.items())
    for i in range(0, len(items), 2):
        row = []
        for key, val in items[i:i+2]:
            row.append(B(val["name"], callback_data=f"font_{key}"))
        rows.append(row)
    rows.append([B("🔙 Back to Menu", callback_data="back_main")])
    return M(rows)

def watermark_menu():
    return M([
        [B("┌─── 🌊 WATERMARK OPTIONS ───┐", callback_data="noop")],
        [B("📝 Text Watermark",            callback_data="wm_text")],
        [B("🖼️ Logo / Image Watermark",   callback_data="wm_logo")],
        [B("👻 Invisible Watermark",       callback_data="wm_invisible")],
        [B("🔙 Back", callback_data="back_main")],
    ])

def page_no_style_menu():
    return M([
        [B("┌─── 🔢 PAGE NUMBER STYLE ───┐", callback_data="noop")],
        [B("① Arabic · 1, 2, 3",           callback_data="pn_arabic"),
         B("Ⅰ Roman · I, II, III",          callback_data="pn_roman")],
        [B("📄 Page 1 of N",               callback_data="pn_total"),
         B("❙ Dash · — 1 —",               callback_data="pn_dash")],
        [B("🔙 Back", callback_data="back_main")],
    ])

def bg_color_menu():
    return M([
        [B("┌─── 🎨 BACKGROUND THEME ───┐", callback_data="noop")],
        [B("⬛ Pitch Black",  callback_data="bg_dark"),
         B("🔷 Navy Blue",   callback_data="bg_navy")],
        [B("🟩 Forest Green",callback_data="bg_green"),
         B("🟣 Deep Purple", callback_data="bg_purple")],
        [B("🟡 Warm Cream",  callback_data="bg_cream"),
         B("🟤 Dark Brown",  callback_data="bg_brown")],
        [B("🔴 Deep Red",    callback_data="bg_red"),
         B("🩵 Slate Blue",  callback_data="bg_slate")],
        [B("🔙 Back", callback_data="back_main")],
    ])

def premium_menu():
    return M([
        [B("┌──── 💎 PREMIUM PLANS ────┐", callback_data="noop")],
        [B(f"⭐ {BASIC_LABEL}", callback_data="buy_basic")],
        [B(f"👑 {PRO_LABEL}",   callback_data="buy_pro")],
        [B("🔙 Back to Menu", callback_data="back_main")],
    ])

def rotate_menu():
    return M([
        [B("┌─── 🔄 ROTATE PAGES ───┐", callback_data="noop")],
        [B("↩️ 90° Left",   callback_data="rot_90l"),
         B("↪️ 90° Right",  callback_data="rot_90r")],
        [B("🔃 180° Flip",  callback_data="rot_180"),
         B("🔄 Auto-Fix",   callback_data="rot_auto")],
        [B("🔙 Back", callback_data="back_main")],
    ])

def cancel_btn():
    return M([[B("❌ Cancel · Return to Menu", callback_data="back_main")]])

def back_btn():
    return M([[B("🏠 Main Menu", callback_data="back_main")]])

def confirm_payment_menu(plan: str):
    return M([
        [B("📸 Send Payment Screenshot", callback_data=f"pay_ss_{plan}")],
        [B("🔙 Cancel", callback_data="back_main")],
    ])

def pdf_tools_menu():
    return M([
        [B("📐 Compress",  callback_data="do_compress"),
         B("✂️ Split",     callback_data="do_split"),
         B("🔗 Merge",     callback_data="do_merge")],
        [B("🖼️ To Images", callback_data="do_pdf2img"),
         B("📊 To Excel",  callback_data="do_excel"),
         B("🔢 Page Nos",  callback_data="do_pageno")],
        [B("🔙 Back", callback_data="back_main")],
    ])
