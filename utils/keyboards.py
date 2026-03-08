"""
keyboards.py v6.0 — Beautiful, categorized menus
Better UX: sectioned menus, emoji-rich, clean layout
"""
from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as M
from config import FONTS, BASIC_LABEL, PRO_LABEL, NOTEBOOK_STYLES, OCR_LANGUAGES, IMAGE_FILTERS
from config import STAMP_PRESETS, QUOTE_THEMES, BCARD_THEMES, FLYER_THEMES


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MENU — compact, sectioned
# ─────────────────────────────────────────────────────────────────────────────

def main_menu():
    return M([
        [B("━━━━━━ 📄 PDF TOOLS ━━━━━━", callback_data="noop")],
        [B("📐 Compress",  callback_data="menu_compress"),
         B("✂️ Split",     callback_data="menu_split"),
         B("🔗 Merge",     callback_data="menu_merge")],
        [B("🧩 Repair",    callback_data="menu_repair"),
         B("⬛ Redact",    callback_data="menu_redact"),
         B("📐 Deskew",    callback_data="menu_deskew")],
        [B("📄 →Text",     callback_data="menu_pdf2txt"),
         B("🌐 Optimize",  callback_data="menu_linearize"),
         B("🖼️ Preview",   callback_data="menu_thumbnail")],
        [B("🔍 Deep Info", callback_data="menu_pdf_info"),
         B("📋 Impose",    callback_data="menu_impose"),
         B("🔃 Reverse",   callback_data="menu_reverse")],
        [B("🔖 Bookmarks", callback_data="menu_pdf_bookmark"),
         B("📊 Word Count",callback_data="menu_pdf_word_count"),
         B("🔢 Headers",   callback_data="menu_pdf_header")],
        [B("⬛ Grayscale", callback_data="menu_pdf_grayscale"),
         B("🖼️ Extract Imgs", callback_data="menu_pdf_extract_imgs"),
         B("🗑️ Strip Meta", callback_data="menu_pdf_remove_meta")],

        [B("━━━━━━ 🖊️ STAMP & SIGN ━━━━━━", callback_data="noop")],
        [B("🖊️ Add Stamp", callback_data="menu_pdf_stamp"),
         B("✍️ Sign PDF",  callback_data="menu_pdf_sign"),
         B("✏️ Edit Meta", callback_data="menu_metadata_edit")],

        [B("━━━━━━ 🔐 SECURITY ━━━━━━", callback_data="noop")],
        [B("🔒 Lock",       callback_data="do_lock"),
         B("🔓 Unlock",     callback_data="do_unlock"),
         B("🔐 Pwd Check",  callback_data="menu_pwd_strength")],
        [B("🔓 Pwd Crack 👑", callback_data="menu_pwd_crack"),
         B("🔒 Hash",       callback_data="menu_hash"),
         B("🕵️ Steg",       callback_data="menu_steg")],
        [B("🧹 Strip EXIF", callback_data="menu_img_remove_exif")],

        [B("━━━━━━ 🎨 VISUAL PDF ━━━━━━", callback_data="noop")],
        [B("🌙 Dark Mode",  callback_data="menu_dark"),
         B("🌊 Watermark", callback_data="menu_watermark"),
         B("🎨 BG Color",  callback_data="menu_bg")],
        [B("🔄 Rotate",    callback_data="menu_rotate"),
         B("📏 Resize A4", callback_data="menu_resize"),
         B("🔍 Compare",   callback_data="menu_compare")],

        [B("━━━━━━ 🔄 PDF CONVERT ━━━━━━", callback_data="noop")],
        [B("🖼️ PDF→Imgs",   callback_data="menu_pdf2img"),
         B("🖼️ Imgs→PDF",   callback_data="menu_img2pdf"),
         B("📊 →Excel",     callback_data="menu_excel")],
        [B("📄 →Word",      callback_data="menu_pdf2word"),
         B("📊 →PPT 👑",   callback_data="menu_pdf2ppt"),
         B("📚 →EPUB ⭐",  callback_data="menu_pdf2epub")],
        [B("📖 EPUB→PDF",  callback_data="menu_epub2pdf"),
         B("📝 Word→PDF",  callback_data="menu_doc2pdf")],

        [B("━━━━━━ 🖼️ IMAGE TOOLS ━━━━━━", callback_data="noop")],
        [B("📦 Compress",  callback_data="menu_img_compress"),
         B("📏 Resize",    callback_data="menu_img_resize"),
         B("✂️ Crop",      callback_data="menu_img_crop")],
        [B("🎨 Filters",   callback_data="menu_img_filter"),
         B("📝 Add Text",  callback_data="menu_img_text"),
         B("✂️ Remove BG ⭐", callback_data="menu_img_bgremove")],
        [B("🖼️ →JPG",      callback_data="menu_img2jpg"),
         B("🖼️ →PNG",      callback_data="menu_img2png"),
         B("✨ Enhance",   callback_data="menu_img_enhance")],
        [B("🖼️ Collage",   callback_data="menu_img_collage"),
         B("😂 Meme",      callback_data="menu_img_meme"),
         B("🎭 Sticker",   callback_data="menu_img_sticker")],
        [B("🔄 Flip",      callback_data="menu_img_flip"),
         B("🖼️ Border",    callback_data="menu_img_border"),
         B("⭕ Rounded",   callback_data="menu_img_round")],
        [B("📷 EXIF Info", callback_data="menu_img_exif"),
         B("🔤 ASCII Art", callback_data="menu_img_ascii")],

        [B("━━━━━━ 📋 DOC CONVERT ━━━━━━", callback_data="noop")],
        [B("📊 CSV→PDF",   callback_data="menu_csv2pdf"),
         B("📄 TXT→PDF",   callback_data="menu_txt2pdf"),
         B("🌐 HTML→PDF",  callback_data="menu_html2pdf")],
        [B("📋 JSON→PDF",  callback_data="menu_json2pdf")],

        [B("━━━━━━ ✨ CREATIVE ━━━━━━", callback_data="noop")],
        [B("✍️ Handwriting", callback_data="menu_hw"),
         B("🔢 Page Nos",  callback_data="menu_pageno"),
         B("🔲 QR Code",   callback_data="menu_qr")],
        [B("💬 Quote Card", callback_data="menu_quote_card"),
         B("🎂 Birthday Card", callback_data="menu_birthday_card"),
         B("💼 Business Card", callback_data="menu_business_card")],
        [B("📅 Calendar",  callback_data="menu_calendar"),
         B("🧾 Invoice",   callback_data="menu_invoice"),
         B("📋 Resume",    callback_data="menu_resume")],
        [B("🏆 Certificate", callback_data="menu_certificate"),
         B("🎨 Poster",    callback_data="menu_poster"),
         B("📢 Flyer",     callback_data="menu_flyer")],
        [B("🗓️ Timetable", callback_data="menu_timetable")],

        [B("━━━━━━ 📊 SMART TOOLS ━━━━━━", callback_data="noop")],
        [B("👁️ OCR Text",   callback_data="menu_ocr"),
         B("📋 Metadata",  callback_data="menu_meta"),
         B("📝 Add Text",  callback_data="menu_addtext")],
        [B("🗂️ Footer",    callback_data="menu_footer"),
         B("✂️ Crop Margins", callback_data="menu_crop"),
         B("🔖 Extract Pgs", callback_data="menu_extract")],
        [B("🗑️ Del Pages", callback_data="menu_delete_pages"),
         B("🔀 Reorder",   callback_data="menu_reorder")],

        [B("━━━━━━ 🛠️ UTILITIES ━━━━━━", callback_data="noop")],
        [B("📦 ZIP",       callback_data="menu_zip"),
         B("📂 Unzip",     callback_data="menu_unzip"),
         B("ℹ️ File Info", callback_data="menu_fileinfo")],
        [B("📷 Scan QR",   callback_data="menu_qrcode_scan"),
         B("📊 Barcode",   callback_data="menu_barcode")],

        [B("━━━━━━ 📱 MY SPACE ━━━━━━", callback_data="noop")],
        [B("⏰ Reminders", callback_data="menu_remind"),
         B("📒 Notes",     callback_data="menu_notes"),
         B("📂 History",   callback_data="menu_history")],
        [B("⭐ Feedback",  callback_data="menu_feedback"),
         B("👥 Refer & Earn", callback_data="menu_referral"),
         B("🔥 My Streak", callback_data="menu_streak")],

        [B("━━━━━━ 👤 ACCOUNT ━━━━━━", callback_data="noop")],
        [B("👤 Account",   callback_data="menu_account"),
         B("📊 Dashboard", callback_data="menu_dashboard"),
         B("💎 Premium",   callback_data="menu_premium")],
        [B("🌍 Language",  callback_data="menu_lang"),
         B("❓ Help",      callback_data="menu_help")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY SUB-MENUS — compact per category
# ─────────────────────────────────────────────────────────────────────────────

def pdf_tools_menu():
    return M([
        [B("📐 Compress",    callback_data="menu_compress"),
         B("✂️ Split",       callback_data="menu_split"),
         B("🔗 Merge",       callback_data="menu_merge")],
        [B("🧩 Repair",      callback_data="menu_repair"),
         B("⬛ Redact",      callback_data="menu_redact"),
         B("📐 Deskew",      callback_data="menu_deskew")],
        [B("📄 →Text",       callback_data="menu_pdf2txt"),
         B("🌐 Optimize",    callback_data="menu_linearize"),
         B("🖼️ Preview",     callback_data="menu_thumbnail")],
        [B("🔍 Deep Info",   callback_data="menu_pdf_info"),
         B("⬛ Grayscale",   callback_data="menu_pdf_grayscale"),
         B("🖊️ Stamp",       callback_data="menu_pdf_stamp")],
        [B("📊 Word Count",  callback_data="menu_pdf_word_count"),
         B("🔢 Headers",     callback_data="menu_pdf_header"),
         B("🖼️ Extract Imgs",callback_data="menu_pdf_extract_imgs")],
        [B("🏠 Main Menu",   callback_data="back_main")],
    ])


def image_tools_menu():
    return M([
        [B("📦 Compress",    callback_data="menu_img_compress"),
         B("📏 Resize",      callback_data="menu_img_resize"),
         B("✂️ Crop",        callback_data="menu_img_crop")],
        [B("🎨 Filters",     callback_data="menu_img_filter"),
         B("📝 Add Text",    callback_data="menu_img_text"),
         B("✂️ Remove BG ⭐",callback_data="menu_img_bgremove")],
        [B("🖼️ Collage",     callback_data="menu_img_collage"),
         B("😂 Meme",        callback_data="menu_img_meme"),
         B("🎭 Sticker",     callback_data="menu_img_sticker")],
        [B("🔄 Flip",        callback_data="menu_img_flip"),
         B("🖼️ Border",      callback_data="menu_img_border"),
         B("⭕ Round",       callback_data="menu_img_round")],
        [B("✨ Enhance",     callback_data="menu_img_enhance"),
         B("📷 EXIF",        callback_data="menu_img_exif"),
         B("🔤 ASCII",       callback_data="menu_img_ascii")],
        [B("🏠 Main Menu",   callback_data="back_main")],
    ])


def creative_menu():
    return M([
        [B("💬 Quote Card",   callback_data="menu_quote_card"),
         B("🎂 Birthday Card",callback_data="menu_birthday_card")],
        [B("💼 Business Card",callback_data="menu_business_card"),
         B("📢 Flyer",        callback_data="menu_flyer")],
        [B("🧾 Invoice",      callback_data="menu_invoice"),
         B("📋 Resume",       callback_data="menu_resume")],
        [B("🏆 Certificate",  callback_data="menu_certificate"),
         B("🎨 Poster",       callback_data="menu_poster")],
        [B("📅 Calendar",     callback_data="menu_calendar"),
         B("🗓️ Timetable",    callback_data="menu_timetable")],
        [B("🏠 Main Menu",    callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────

def back_btn():
    return M([[B("🏠 Main Menu", callback_data="back_main")]])


def cancel_btn():
    return M([[B("❌ Cancel", callback_data="back_main")]])


def back_or_cancel():
    return M([[
        B("⬅️ Back",   callback_data="back_main"),
        B("❌ Cancel", callback_data="back_main"),
    ]])


# ─────────────────────────────────────────────────────────────────────────────
# STAMP MENU
# ─────────────────────────────────────────────────────────────────────────────

def stamp_menu():
    from config import STAMP_PRESETS
    rows = []
    for i in range(0, len(STAMP_PRESETS), 2):
        row = []
        for label, color in STAMP_PRESETS[i:i+2]:
            safe_label = label.split(" ", 1)[-1] if " " in label else label
            row.append(B(label, callback_data=f"stamp_{safe_label.replace(' ', '_')}"))
        rows.append(row)
    rows.append([B("✏️ Custom Text", callback_data="stamp_custom")])
    rows.append([B("🏠 Back", callback_data="back_main")])
    return M(rows)


# ─────────────────────────────────────────────────────────────────────────────
# QUOTE CARD THEMES
# ─────────────────────────────────────────────────────────────────────────────

def quote_theme_menu():
    return M([
        [B("🌙 Dark",   callback_data="quote_dark"),
         B("☀️ Light",  callback_data="quote_light")],
        [B("🌅 Sunset", callback_data="quote_sunset"),
         B("🌊 Ocean",  callback_data="quote_ocean")],
        [B("🌿 Forest", callback_data="quote_forest"),
         B("🌹 Rose",   callback_data="quote_rose")],
        [B("🏠 Back",   callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS CARD THEMES
# ─────────────────────────────────────────────────────────────────────────────

def bcard_theme_menu():
    return M([
        [B("⬜ Minimal", callback_data="bcard_minimal"),
         B("🌙 Dark",    callback_data="bcard_dark")],
        [B("🥇 Gold",    callback_data="bcard_gold"),
         B("🔵 Blue",    callback_data="bcard_blue")],
        [B("🏠 Back",    callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# FLYER THEMES
# ─────────────────────────────────────────────────────────────────────────────

def flyer_theme_menu():
    return M([
        [B("🎉 Event",   callback_data="flyer_event"),
         B("🛒 Sale",    callback_data="flyer_sale")],
        [B("🎸 Concert", callback_data="flyer_concert"),
         B("🪟 Clean",   callback_data="flyer_clean")],
        [B("🏠 Back",    callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# IMAGE FILTER MENU (expanded v6)
# ─────────────────────────────────────────────────────────────────────────────

def img_filter_menu():
    items = list(IMAGE_FILTERS.items())
    rows  = [[B(v, callback_data=f"imgf_{k}") for k, v in items[i:i+3]]
             for i in range(0, len(items), 3)]
    rows.append([B("🏠 Back", callback_data="back_main")])
    return M(rows)


# ─────────────────────────────────────────────────────────────────────────────
# IMAGE FLIP MENU
# ─────────────────────────────────────────────────────────────────────────────

def img_flip_menu():
    return M([
        [B("↔️ Horizontal", callback_data="flip_horizontal"),
         B("↕️ Vertical",   callback_data="flip_vertical")],
        [B("🏠 Back",       callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# IMAGE BORDER COLORS
# ─────────────────────────────────────────────────────────────────────────────

def img_border_menu():
    return M([
        [B("⬜ White",  callback_data="border_white"),
         B("⬛ Black",  callback_data="border_black"),
         B("🔴 Red",    callback_data="border_red")],
        [B("🔵 Blue",   callback_data="border_blue"),
         B("🟡 Yellow", callback_data="border_yellow"),
         B("🟢 Green",  callback_data="border_green")],
        [B("🌸 Pink",   callback_data="border_pink"),
         B("🟠 Orange", callback_data="border_orange")],
        [B("🏠 Back",   callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# COLLAGE LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

def collage_layout_menu():
    return M([
        [B("📋 2 Columns",  callback_data="collage_2"),
         B("📋 3 Columns",  callback_data="collage_3")],
        [B("📋 4 Columns",  callback_data="collage_4")],
        [B("🏠 Back",       callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# FEEDBACK MENU
# ─────────────────────────────────────────────────────────────────────────────

def feedback_menu():
    return M([
        [B("⭐ 1",  callback_data="fb_1"),
         B("⭐⭐ 2", callback_data="fb_2"),
         B("⭐⭐⭐ 3", callback_data="fb_3")],
        [B("⭐⭐⭐⭐ 4",  callback_data="fb_4"),
         B("⭐⭐⭐⭐⭐ 5", callback_data="fb_5")],
        [B("🏠 Back",    callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# NOTES MENU
# ─────────────────────────────────────────────────────────────────────────────

def notes_menu():
    return M([
        [B("📝 Add Note",    callback_data="note_add"),
         B("📋 View Notes",  callback_data="note_view")],
        [B("🗑️ Delete Note", callback_data="note_delete")],
        [B("🏠 Back",        callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# OTHER EXISTING MENUS
# ─────────────────────────────────────────────────────────────────────────────

def font_menu():
    rows = []
    items = list(FONTS.items())
    for i in range(0, len(items), 2):
        row = [B(v["name"], callback_data=f"font_{k}") for k, v in items[i:i+2]]
        rows.append(row)
    rows.append([B("🏠 Back", callback_data="back_main")])
    return M(rows)


def notebook_style_menu():
    rows = []
    items = list(NOTEBOOK_STYLES.items())
    for i in range(0, len(items), 2):
        row = [B(v["name"], callback_data=f"style_{k}") for k, v in items[i:i+2]]
        rows.append(row)
    rows.append([B("🏠 Back", callback_data="back_main")])
    return M(rows)


def watermark_menu():
    return M([
        [B("📝 Text Watermark", callback_data="wm_text"),
         B("🖼️ Logo Watermark", callback_data="wm_logo")],
        [B("🏠 Back", callback_data="back_main")],
    ])


def page_no_style_menu():
    return M([
        [B("1, 2, 3 (Arabic)", callback_data="pn_arabic"),
         B("I, II, III (Roman)", callback_data="pn_roman")],
        [B("🏠 Back", callback_data="back_main")],
    ])


def bg_color_menu():
    return M([
        [B("🟡 Yellow",  callback_data="bg_yellow"),
         B("🟢 Green",   callback_data="bg_green"),
         B("🔵 Blue",    callback_data="bg_blue")],
        [B("🩷 Pink",    callback_data="bg_pink"),
         B("🌙 Dark",    callback_data="bg_dark"),
         B("⬜ White",   callback_data="bg_white")],
        [B("🏠 Back",    callback_data="back_main")],
    ])


def rotate_menu():
    return M([
        [B("↻ 90°",   callback_data="rot_90"),
         B("↺ 180°",  callback_data="rot_180"),
         B("↻ 270°",  callback_data="rot_270")],
        [B("🏠 Back", callback_data="back_main")],
    ])


def ocr_language_menu():
    rows = []
    items = list(OCR_LANGUAGES.items())
    for i in range(0, len(items), 2):
        row = [B(v["name"], callback_data=f"ocr_{k}") for k, v in items[i:i+2]]
        rows.append(row)
    rows.append([B("🏠 Back", callback_data="back_main")])
    return M(rows)


def language_menu():
    return M([
        [B("🇬🇧 English",  callback_data="lang_en"),
         B("🇮🇳 Hindi",    callback_data="lang_hi")],
        [B("🇪🇸 Spanish",  callback_data="lang_es"),
         B("🇫🇷 French",   callback_data="lang_fr")],
        [B("🏠 Back",       callback_data="back_main")],
    ])


def premium_menu():
    return M([
        [B(f"⭐ {BASIC_LABEL}", callback_data="buy_basic")],
        [B(f"👑 {PRO_LABEL}",   callback_data="buy_pro")],
        [B("🏠 Back",           callback_data="back_main")],
    ])


def confirm_payment_menu(plan: str):
    return M([
        [B("📸 Send Payment Screenshot", callback_data=f"pay_ss_{plan}")],
        [B("🏠 Back", callback_data="back_main")],
    ])


def impose_menu():
    return M([
        [B("📄 2-up (2 per sheet)", callback_data="impose_2up"),
         B("📄 4-up (4 per sheet)", callback_data="impose_4up")],
        [B("🏠 Back", callback_data="back_main")],
    ])


def steg_menu():
    return M([
        [B("🙈 Hide Message",  callback_data="steg_hide"),
         B("👁️ Reveal Message", callback_data="steg_reveal")],
        [B("🏠 Back", callback_data="back_main")],
    ])


def poster_theme_menu():
    return M([
        [B("🌙 Dark",      callback_data="poster_dark"),
         B("☀️ Light",     callback_data="poster_light")],
        [B("🔴 Red",       callback_data="poster_red"),
         B("🟢 Green",     callback_data="poster_green")],
        [B("🌈 Gradient",  callback_data="poster_gradient")],
        [B("🏠 Back",      callback_data="back_main")],
    ])
