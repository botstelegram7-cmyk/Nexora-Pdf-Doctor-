"""
Keyboards v5.0 — Full UI/UX with all new features
"""
from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as M
from config import FONTS, BASIC_LABEL, PRO_LABEL, NOTEBOOK_STYLES, OCR_LANGUAGES, IMAGE_FILTERS


def main_menu():
    return M([
        # ── PDF Tools ─────────────────────────────────────────────────────────
        [B("━━━ 📄 PDF TOOLS ━━━", callback_data="noop")],
        [B("📐 Compress",  callback_data="menu_compress"),
         B("✂️ Split",      callback_data="menu_split"),
         B("🔗 Merge",     callback_data="menu_merge")],
        [B("🧩 Repair",    callback_data="menu_repair"),
         B("✂️ Crop",      callback_data="menu_crop"),
         B("🔃 Reverse",   callback_data="menu_reverse")],
        [B("📄 PDF→Text",  callback_data="menu_pdf2txt"),
         B("🌐 Optimize",  callback_data="menu_linearize"),
         B("🖼️ Preview",   callback_data="menu_thumbnail")],
        [B("🔍 PDF Info",  callback_data="menu_pdf_info"),
         B("⬛ Redact",    callback_data="menu_redact"),
         B("📋 Impose",    callback_data="menu_impose")],
        [B("📐 Deskew",    callback_data="menu_deskew"),
         B("🔍 Compare",   callback_data="menu_compare")],

        # ── Security ──────────────────────────────────────────────────────────
        [B("━━━ 🔐 SECURITY ━━━", callback_data="noop")],
        [B("🔒 Lock PDF",   callback_data="do_lock"),
         B("🔓 Unlock PDF", callback_data="do_unlock")],
        [B("🔐 Pwd Strength", callback_data="menu_pwd_strength"),
         B("🔓 Pwd Crack 👑", callback_data="menu_pwd_crack")],
        [B("🔒 Hash Check",  callback_data="menu_hash"),
         B("✍️ Sign PDF",    callback_data="menu_pdf_sign"),
         B("🕵️ Steganography", callback_data="menu_steg")],

        # ── Visual ────────────────────────────────────────────────────────────
        [B("━━━ 🎨 VISUAL ━━━", callback_data="noop")],
        [B("🌙 Dark Mode",   callback_data="menu_dark"),
         B("🌊 Watermark",   callback_data="menu_watermark"),
         B("🎨 BG Color",    callback_data="menu_bg")],
        [B("🔄 Rotate",      callback_data="menu_rotate"),
         B("📏 Resize A4",   callback_data="menu_resize"),
         B("✏️ Metadata Edit", callback_data="menu_metadata_edit")],

        # ── Convert PDF ───────────────────────────────────────────────────────
        [B("━━━ 🔄 CONVERT PDF ━━━", callback_data="noop")],
        [B("🖼️ PDF→Imgs",    callback_data="menu_pdf2img"),
         B("🖼️ Imgs→PDF",    callback_data="menu_img2pdf"),
         B("📊 PDF→Excel",   callback_data="menu_excel")],
        [B("📄 PDF→Word",    callback_data="menu_pdf2word"),
         B("📊 PDF→PPT 👑",  callback_data="menu_pdf2ppt"),
         B("📚 PDF→EPUB ⭐", callback_data="menu_pdf2epub")],
        [B("📖 EPUB→PDF",    callback_data="menu_epub2pdf"),
         B("📝 Word→PDF",    callback_data="menu_doc2pdf")],

        # ── Image Tools ───────────────────────────────────────────────────────
        [B("━━━ 🖼️ IMAGE TOOLS ━━━", callback_data="noop")],
        [B("📦 Compress",    callback_data="menu_img_compress"),
         B("📏 Resize",      callback_data="menu_img_resize"),
         B("✂️ Crop",        callback_data="menu_img_crop")],
        [B("🎨 Filters",     callback_data="menu_img_filter"),
         B("📝 Add Text",    callback_data="menu_img_text"),
         B("✂️ Remove BG ⭐",callback_data="menu_img_bgremove")],
        [B("🖼️ →JPG",        callback_data="menu_img2jpg"),
         B("🖼️ →PNG",        callback_data="menu_img2png")],

        # ── Document Convert ──────────────────────────────────────────────────
        [B("━━━ 📋 DOC CONVERT ━━━", callback_data="noop")],
        [B("📊 CSV→PDF",     callback_data="menu_csv2pdf"),
         B("📄 TXT→PDF",     callback_data="menu_txt2pdf"),
         B("🌐 HTML→PDF",    callback_data="menu_html2pdf")],
        [B("📋 JSON→PDF",    callback_data="menu_json2pdf")],

        # ── Creative ──────────────────────────────────────────────────────────
        [B("━━━ ✨ CREATIVE ━━━", callback_data="noop")],
        [B("✍️ Handwriting",  callback_data="menu_hw"),
         B("🔢 Page Nos",    callback_data="menu_pageno"),
         B("🔲 QR Code",     callback_data="menu_qr")],
        [B("📝 Add Text",    callback_data="menu_addtext"),
         B("🗂️ Footer",      callback_data="menu_footer")],
        [B("🎨 Poster",      callback_data="menu_poster"),
         B("📅 Calendar",    callback_data="menu_calendar"),
         B("🧾 Invoice",     callback_data="menu_invoice")],
        [B("📋 Resume",      callback_data="menu_resume"),
         B("🏆 Certificate", callback_data="menu_certificate")],

        # ── Pages ─────────────────────────────────────────────────────────────
        [B("━━━ 📐 PAGES ━━━", callback_data="noop")],
        [B("🔖 Extract",     callback_data="menu_extract"),
         B("🗑️ Delete Pgs",  callback_data="menu_delete_pages"),
         B("🔀 Reorder",     callback_data="menu_reorder")],

        # ── Utilities ─────────────────────────────────────────────────────────
        [B("━━━ 🛠️ UTILITIES ━━━", callback_data="noop")],
        [B("📦 ZIP",         callback_data="menu_zip"),
         B("📂 Unzip",       callback_data="menu_unzip"),
         B("ℹ️ File Info",   callback_data="menu_fileinfo")],
        [B("📷 Scan QR",     callback_data="menu_qrcode_scan"),
         B("📊 Barcode",     callback_data="menu_barcode")],

        # ── Smart Tools ───────────────────────────────────────────────────────
        [B("━━━ 🔍 SMART TOOLS ━━━", callback_data="noop")],
        [B("👁️ OCR Text",    callback_data="menu_ocr"),
         B("📋 Metadata",    callback_data="menu_meta")],

        # ── UX ────────────────────────────────────────────────────────────────
        [B("━━━ 📱 MY TOOLS ━━━", callback_data="noop")],
        [B("⏰ Reminders",   callback_data="menu_remind"),
         B("📒 Notes",       callback_data="menu_notes"),
         B("📂 History",     callback_data="menu_history")],

        # ── Account ───────────────────────────────────────────────────────────
        [B("━━━ 👤 ACCOUNT ━━━", callback_data="noop")],
        [B("👤 Account",     callback_data="menu_account"),
         B("📊 Dashboard",   callback_data="menu_dashboard"),
         B("💎 Premium",     callback_data="menu_premium")],
        [B("🌍 Language",    callback_data="menu_lang"),
         B("❓ Help",        callback_data="menu_help")],
    ])


def back_btn():
    return M([[B("🏠 Main Menu", callback_data="back_main")]])

def cancel_btn():
    return M([[B("❌ Cancel", callback_data="back_main")]])

def font_menu():
    from config import FONTS
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
        [B("🏠 Back", callback_data="back_main")]
    ])

def page_no_style_menu():
    return M([
        [B("1, 2, 3 (Arabic)", callback_data="pn_arabic"),
         B("I, II, III (Roman)", callback_data="pn_roman")],
        [B("🏠 Back", callback_data="back_main")]
    ])

def bg_color_menu():
    return M([
        [B("🟡 Yellow",  callback_data="bg_yellow"),
         B("🟢 Green",   callback_data="bg_green"),
         B("🔵 Blue",    callback_data="bg_blue")],
        [B("🩷 Pink",    callback_data="bg_pink"),
         B("🌙 Dark",    callback_data="bg_dark"),
         B("⬜ White",   callback_data="bg_white")],
        [B("🏠 Back", callback_data="back_main")]
    ])

def rotate_menu():
    return M([
        [B("↻ 90°",   callback_data="rot_90"),
         B("↺ 180°",  callback_data="rot_180"),
         B("↻ 270°",  callback_data="rot_270")],
        [B("🏠 Back", callback_data="back_main")]
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
        [B("🏠 Back", callback_data="back_main")]
    ])

def premium_menu():
    return M([
        [B(f"⭐ {BASIC_LABEL}", callback_data="buy_basic")],
        [B(f"👑 {PRO_LABEL}",   callback_data="buy_pro")],
        [B("🏠 Back", callback_data="back_main")]
    ])

def confirm_payment_menu(plan: str):
    return M([
        [B("📸 Send Payment Screenshot", callback_data=f"pay_ss_{plan}")],
        [B("🏠 Back", callback_data="back_main")]
    ])
