from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from config import FONTS, BASIC_LABEL, PRO_LABEL

def main_menu():
    return Markup([
        [Btn("📄 PDF Tools", callback_data="menu_pdf"),
         Btn("🖼️ OCR / Extract", callback_data="menu_ocr")],
        [Btn("✍️ Handwriting PDF", callback_data="menu_hw"),
         Btn("🔐 Lock / Unlock", callback_data="menu_lock")],
        [Btn("🌊 Watermark", callback_data="menu_watermark"),
         Btn("🌙 Dark Mode", callback_data="menu_dark")],
        [Btn("📊 PDF → Excel", callback_data="menu_excel"),
         Btn("🔢 Page Numbers", callback_data="menu_pageno")],
        [Btn("🧩 Repair PDF", callback_data="menu_repair"),
         Btn("📐 Compress PDF", callback_data="menu_compress")],
        [Btn("✂️ Split PDF", callback_data="menu_split"),
         Btn("🔗 Merge PDFs", callback_data="menu_merge")],
        [Btn("🖼️ PDF→Images", callback_data="menu_pdf2img"),
         Btn("🖼️ Images→PDF", callback_data="menu_img2pdf")],
        [Btn("🎨 BG Changer", callback_data="menu_bg"),
         Btn("🔒 Add Password", callback_data="menu_addpass")],
        [Btn("💎 Premium Plans", callback_data="menu_premium"),
         Btn("ℹ️ My Account", callback_data="menu_account")],
        [Btn("❓ Help", callback_data="menu_help")],
    ])

def pdf_tools_menu():
    return Markup([
        [Btn("📐 Compress",  callback_data="do_compress"),
         Btn("✂️ Split",     callback_data="do_split")],
        [Btn("🔗 Merge",     callback_data="do_merge"),
         Btn("🖼️ To Images", callback_data="do_pdf2img")],
        [Btn("📊 To Excel",  callback_data="do_excel"),
         Btn("🔢 Page Nos",  callback_data="do_pageno")],
        [Btn("🔙 Back", callback_data="back_main")],
    ])

def font_menu():
    rows = []
    row = []
    for key, val in FONTS.items():
        row.append(Btn(val["name"], callback_data=f"font_{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([Btn("🔙 Cancel", callback_data="back_main")])
    return Markup(rows)

def watermark_menu():
    return Markup([
        [Btn("📝 Text Watermark",      callback_data="wm_text"),
         Btn("🖼️ Logo Watermark",     callback_data="wm_logo")],
        [Btn("👻 Invisible Watermark", callback_data="wm_invisible")],
        [Btn("🔙 Back", callback_data="back_main")],
    ])

def lock_menu():
    return Markup([
        [Btn("🔒 Lock PDF",   callback_data="do_lock"),
         Btn("🔓 Unlock PDF", callback_data="do_unlock")],
        [Btn("🔙 Back", callback_data="back_main")],
    ])

def page_no_style_menu():
    return Markup([
        [Btn("1, 2, 3...",         callback_data="pn_arabic"),
         Btn("I, II, III...",      callback_data="pn_roman")],
        [Btn("Page 1 of N",        callback_data="pn_total"),
         Btn("- 1 - , - 2 -",     callback_data="pn_dash")],
        [Btn("🔙 Back", callback_data="back_main")],
    ])

def bg_color_menu():
    return Markup([
        [Btn("🌙 Dark (Black)",    callback_data="bg_dark"),
         Btn("🌊 Navy Blue",       callback_data="bg_navy")],
        [Btn("🌿 Green",           callback_data="bg_green"),
         Btn("🟣 Purple",          callback_data="bg_purple")],
        [Btn("☀️ Cream",           callback_data="bg_cream"),
         Btn("🔴 Red",             callback_data="bg_red")],
        [Btn("🔙 Back", callback_data="back_main")],
    ])

def premium_menu():
    return Markup([
        [Btn(f"⭐ {BASIC_LABEL}", callback_data="buy_basic")],
        [Btn(f"👑 {PRO_LABEL}",  callback_data="buy_pro")],
        [Btn("🔙 Back", callback_data="back_main")],
    ])

def cancel_btn():
    return Markup([[Btn("❌ Cancel", callback_data="back_main")]])

def back_btn():
    return Markup([[Btn("🔙 Main Menu", callback_data="back_main")]])

def confirm_payment_menu(plan: str):
    return Markup([
        [Btn("📸 Send Payment Screenshot", callback_data=f"pay_ss_{plan}")],
        [Btn("🔙 Back", callback_data="back_main")],
    ])
