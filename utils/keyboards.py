"""
Keyboards v4.1 — Full UI/UX Upgrade
- Cleaner section headers
- Better button grouping
- New: reverse, compare, dashboard shortcuts
- Fixed duplicate buttons
"""
from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as M
from config import FONTS, BASIC_LABEL, PRO_LABEL, NOTEBOOK_STYLES, OCR_LANGUAGES


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MENU — Redesigned v4.1
# ─────────────────────────────────────────────────────────────────────────────
def main_menu():
    return M([
        # ── PDF Tools ─────────────────────────────────────────────────────────
        [B("━━━ 📄 PDF TOOLS ━━━", callback_data="noop")],
        [B("📐 Compress", callback_data="menu_compress"),
         B("✂️ Split",     callback_data="menu_split"),
         B("🔗 Merge",    callback_data="menu_merge")],
        [B("🧩 Repair",   callback_data="menu_repair"),
         B("✂️ Crop",     callback_data="menu_crop"),
         B("🔃 Reverse",  callback_data="menu_reverse")],

        # ── Security ──────────────────────────────────────────────────────────
        [B("━━━ 🔐 SECURITY ━━━", callback_data="noop")],
        [B("🔒 Lock PDF",  callback_data="do_lock"),
         B("🔓 Unlock PDF",callback_data="do_unlock")],

        # ── Visual ────────────────────────────────────────────────────────────
        [B("━━━ 🎨 VISUAL ━━━", callback_data="noop")],
        [B("🌙 Dark Mode",  callback_data="menu_dark"),
         B("🌊 Watermark",  callback_data="menu_watermark"),
         B("🎨 BG Color",   callback_data="menu_bg")],
        [B("🔄 Rotate",     callback_data="menu_rotate"),
         B("📏 Resize A4",  callback_data="menu_resize")],

        # ── Convert ───────────────────────────────────────────────────────────
        [B("━━━ 🔄 CONVERT ━━━", callback_data="noop")],
        [B("🖼️ PDF→Imgs",   callback_data="menu_pdf2img"),
         B("🖼️ Imgs→PDF",   callback_data="menu_img2pdf"),
         B("📊 PDF→Excel",  callback_data="menu_excel")],
        [B("📄 PDF→Word",   callback_data="menu_pdf2word"),
         B("📊 PDF→PPT 👑", callback_data="menu_pdf2ppt")],

        # ── Creative ──────────────────────────────────────────────────────────
        [B("━━━ ✨ CREATIVE ━━━", callback_data="noop")],
        [B("✍️ Handwriting",  callback_data="menu_hw"),
         B("🔢 Page Nos",    callback_data="menu_pageno"),
         B("🔲 QR Code",     callback_data="menu_qr")],
        [B("📝 Add Text",    callback_data="menu_addtext"),
         B("🗂️ Footer",      callback_data="menu_footer")],

        # ── Pages ─────────────────────────────────────────────────────────────
        [B("━━━ 📐 PAGES ━━━", callback_data="noop")],
        [B("🔖 Extract",     callback_data="menu_extract"),
         B("🗑️ Delete Pgs",  callback_data="menu_delete_pages"),
         B("🔀 Reorder",     callback_data="menu_reorder")],

        # ── Extract & Smart ───────────────────────────────────────────────────
        [B("━━━ 🔍 SMART TOOLS ━━━", callback_data="noop")],
        [B("👁️ OCR Text",    callback_data="menu_ocr"),
         B("📋 Metadata",    callback_data="menu_meta"),
         B("🔍 Compare",     callback_data="menu_compare")],

        # ── Account ───────────────────────────────────────────────────────────
        [B("━━━ 👤 ACCOUNT ━━━", callback_data="noop")],
        [B("👤 Account",     callback_data="menu_account"),
         B("📊 Dashboard",   callback_data="menu_dashboard"),
         B("💎 Premium",     callback_data="menu_premium")],
        [B("🌍 Language",    callback_data="menu_lang"),
         B("❓ Help",        callback_data="menu_help")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# NAVIGATION BUTTONS
# ─────────────────────────────────────────────────────────────────────────────
def back_btn():
    return M([[B("🏠 Main Menu", callback_data="back_main")]])

def cancel_btn():
    return M([[B("❌ Cancel", callback_data="back_main")]])

def back_and_cancel():
    return M([[
        B("🔙 Back", callback_data="back_main"),
        B("❌ Cancel", callback_data="back_main"),
    ]])


# ─────────────────────────────────────────────────────────────────────────────
# FONT MENU — 14 fonts, 2 per row
# ─────────────────────────────────────────────────────────────────────────────
def font_menu():
    rows = []
    items = list(FONTS.items())
    for i in range(0, len(items), 2):
        row = []
        for key, info in items[i:i+2]:
            row.append(B(info["name"], callback_data=f"font_{key}"))
        rows.append(row)
    rows.append([B("❌ Cancel", callback_data="back_main")])
    return M(rows)


# ─────────────────────────────────────────────────────────────────────────────
# NOTEBOOK STYLE MENU — 8 styles, 2 per row
# ─────────────────────────────────────────────────────────────────────────────
def notebook_style_menu():
    rows = []
    items = list(NOTEBOOK_STYLES.items())
    for i in range(0, len(items), 2):
        row = []
        for key, info in items[i:i+2]:
            row.append(B(info["name"], callback_data=f"nbstyle_{key}"))
        rows.append(row)
    rows.append([B("❌ Cancel", callback_data="back_main")])
    return M(rows)


# ─────────────────────────────────────────────────────────────────────────────
# OCR LANGUAGE MENU — 10 languages, 2 per row
# ─────────────────────────────────────────────────────────────────────────────
def ocr_language_menu():
    rows = []
    items = list(OCR_LANGUAGES.items())
    for i in range(0, len(items), 2):
        row = []
        for key, info in items[i:i+2]:
            row.append(B(info["name"], callback_data=f"ocrlang_{key}"))
        rows.append(row)
    rows.append([B("❌ Cancel", callback_data="back_main")])
    return M(rows)


# ─────────────────────────────────────────────────────────────────────────────
# WATERMARK MENU
# ─────────────────────────────────────────────────────────────────────────────
def watermark_menu():
    return M([
        [B("📝 Text Watermark",      callback_data="wm_text")],
        [B("🖼️ Logo/Image Watermark", callback_data="wm_logo")],
        [B("👻 Invisible Watermark",  callback_data="wm_invisible")],
        [B("❌ Cancel",              callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# PAGE NUMBER STYLE MENU
# ─────────────────────────────────────────────────────────────────────────────
def page_no_style_menu():
    return M([
        [B("1 · 2 · 3  (Arabic)",   callback_data="pn_arabic"),
         B("i · ii · iii (Roman)",  callback_data="pn_roman")],
        [B("Page 1 of N",           callback_data="pn_of_n"),
         B("─ 1 ─  (Fancy)",        callback_data="pn_fancy")],
        [B("❌ Cancel",             callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUND COLOR MENU
# ─────────────────────────────────────────────────────────────────────────────
def bg_color_menu():
    return M([
        [B("🌙 Dark / Black",    callback_data="bg_dark"),
         B("🌿 Green Night",     callback_data="bg_green")],
        [B("📘 Blue Night",      callback_data="bg_blue"),
         B("🟤 Sepia / Warm",    callback_data="bg_sepia")],
        [B("🩷 Soft Pink",       callback_data="bg_pink"),
         B("🤍 Pure White",      callback_data="bg_white")],
        [B("❌ Cancel",         callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# ROTATE MENU
# ─────────────────────────────────────────────────────────────────────────────
def rotate_menu():
    return M([
        [B("↩️ 90° Left",   callback_data="rot_90l"),
         B("↪️ 90° Right",  callback_data="rot_90r")],
        [B("🔃 180° Flip",  callback_data="rot_180"),
         B("🤖 Auto Fix",   callback_data="rot_auto")],
        [B("❌ Cancel",     callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE MENU — 6 languages
# ─────────────────────────────────────────────────────────────────────────────
def language_menu():
    return M([
        [B("🇬🇧 English",   callback_data="setlang_en"),
         B("🇮🇳 Hindi",     callback_data="setlang_hi")],
        [B("🇮🇳 Bhojpuri",  callback_data="setlang_bh"),
         B("🇪🇸 Español",   callback_data="setlang_es")],
        [B("🇫🇷 Français",  callback_data="setlang_fr"),
         B("🇰🇷 한국어",    callback_data="setlang_ko")],
        [B("❌ Cancel",     callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# CONFIRM PAYMENT MENU  ← FIX: was missing, caused ImportError
# ─────────────────────────────────────────────────────────────────────────────
def confirm_payment_menu(plan: str = "basic"):
    return M([
        [B("📸 Send Payment Screenshot", callback_data=f"pay_ss_{plan}")],
        [B("🏠 Main Menu",               callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# PREMIUM MENU
# ─────────────────────────────────────────────────────────────────────────────
def premium_menu():
    return M([
        [B(f"⭐ Buy {BASIC_LABEL}", callback_data="buy_basic")],
        [B(f"👑 Buy {PRO_LABEL}",   callback_data="buy_pro")],
        [B("🏠 Main Menu",          callback_data="back_main")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD SHORTCUT (inline in account messages)
# ─────────────────────────────────────────────────────────────────────────────
def account_menu():
    return M([
        [B("📊 My Dashboard", callback_data="menu_dashboard"),
         B("💎 Upgrade",      callback_data="menu_premium")],
        [B("🏠 Main Menu",    callback_data="back_main")],
    ])
