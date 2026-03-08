"""
stats_card.py — Shareable user stats card generator
Produces a beautiful 800x450 image with user stats
"""
import io, datetime


def generate_stats_card(
    name: str,
    plan: str,
    total_ops: int,
    streak: int,
    coins: int,
    achievements: list,
    today_ops: int = 0,
    rank: str = "",
) -> bytes:
    from PIL import Image as PILImage, ImageDraw, ImageFont

    W, H = 800, 450

    # Theme by plan
    themes = {
        "free":  {"bg1": (15, 15, 35),  "bg2": (30, 30, 60),  "acc": (100, 120, 255), "badge": (80, 80, 130)},
        "basic": {"bg1": (15, 30, 50),  "bg2": (25, 50, 80),  "acc": (60, 160, 255),  "badge": (40, 100, 160)},
        "pro":   {"bg1": (30, 15, 10),  "bg2": (60, 30, 10),  "acc": (255, 180, 40),  "badge": (160, 100, 20)},
    }
    t   = themes.get(plan, themes["free"])
    acc = t["acc"]

    img  = PILImage.new("RGB", (W, H), t["bg1"])
    draw = ImageDraw.Draw(img)

    # ── Gradient background ──────────────────────────────────────────────────
    for y in range(H):
        ratio = y / H
        r = int(t["bg1"][0] + (t["bg2"][0] - t["bg1"][0]) * ratio)
        g = int(t["bg1"][1] + (t["bg2"][1] - t["bg1"][1]) * ratio)
        b = int(t["bg1"][2] + (t["bg2"][2] - t["bg1"][2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # ── Decorative circles (background) ─────────────────────────────────────
    for cx, cy, cr, alpha in [(650, 80, 120, 15), (100, 350, 80, 10), (750, 350, 60, 8)]:
        overlay = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
        od      = ImageDraw.Draw(overlay)
        od.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], fill=(*acc, alpha))
        img.paste(PILImage.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))
        draw = ImageDraw.Draw(img)

    # ── Top accent bar ───────────────────────────────────────────────────────
    draw.rectangle([0, 0, W, 5], fill=acc)

    # ── Load fonts ───────────────────────────────────────────────────────────
    try:
        font_path  = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_reg   = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        f_title    = ImageFont.truetype(font_path, 32)
        f_name     = ImageFont.truetype(font_path, 28)
        f_label    = ImageFont.truetype(font_reg,  14)
        f_value    = ImageFont.truetype(font_path, 36)
        f_small    = ImageFont.truetype(font_reg,  12)
        f_badge    = ImageFont.truetype(font_path, 20)
        f_plan     = ImageFont.truetype(font_path, 15)
    except Exception:
        f_title = f_name = f_label = f_value = f_small = f_badge = f_plan = ImageFont.load_default()

    # ── Plan badge ───────────────────────────────────────────────────────────
    plan_labels = {"free": "🆓 FREE", "basic": "⭐ BASIC", "pro": "👑 PRO"}
    plan_text   = plan_labels.get(plan, "FREE")
    pbbox       = draw.textbbox((0, 0), plan_text, font=f_plan)
    pw          = pbbox[2] - pbbox[0] + 20
    draw.rounded_rectangle([W-pw-25, 18, W-25, 45], radius=8, fill=t["badge"])
    draw.text((W-pw-15, 21), plan_text, font=f_plan, fill=acc)

    # ── Bot name ─────────────────────────────────────────────────────────────
    draw.text((30, 18), "⚡ NEXORA PDF DOCTOR", font=f_plan, fill=acc)

    # ── User name ────────────────────────────────────────────────────────────
    draw.text((30, 55), name[:28], font=f_name, fill=(255, 255, 255))

    # ── Horizontal divider ───────────────────────────────────────────────────
    draw.line([(30, 100), (W-30, 100)], fill=(*acc, 80), width=1)

    # ── Stats grid ───────────────────────────────────────────────────────────
    stats = [
        ("📄", "Total Files",   f"{total_ops:,}",   30,  130),
        ("🔥", "Day Streak",    f"{streak}",         210, 130),
        ("🪙", "Coins",         f"{coins:,}",        390, 130),
        ("⚡", "Today",         f"{today_ops}",      570, 130),
    ]
    for icon, label, value, x, y in stats:
        # Card bg
        draw.rounded_rectangle([x, y, x+165, y+110], radius=12,
                                fill=(255, 255, 255, 15) if False else (255, 255, 255))
        draw.rounded_rectangle([x, y, x+165, y+110], radius=12,
                                fill=(30, 30, 60) if plan == "free" else (20, 40, 70))
        draw.rounded_rectangle([x, y, x+165, y+5],   radius=0, fill=acc)
        # Icon + label
        draw.text((x+12, y+14), f"{icon} {label}", font=f_label, fill=(180, 190, 220))
        # Value
        vbbox = draw.textbbox((0, 0), value, font=f_value)
        vw    = vbbox[2] - vbbox[0]
        draw.text((x + (165-vw)//2, y+42), value, font=f_value, fill=(255, 255, 255))

    # ── Achievements row ─────────────────────────────────────────────────────
    earned = [a for a in achievements if a.get("earned")]
    draw.text((30, 260), "🏅 Achievements", font=f_label, fill=(180, 190, 220))
    if earned:
        for i, badge in enumerate(earned[:8]):
            bx = 30 + i * 85
            draw.rounded_rectangle([bx, 280, bx+78, 340], radius=10,
                                   fill=t["badge"])
            draw.text((bx+8,  285), badge["emoji"], font=f_badge, fill=(255,255,255))
            bname = badge["name"][:8]
            draw.text((bx+5,  312), bname, font=f_small, fill=(200,210,240))
    else:
        draw.text((30, 285), "No badges yet — start processing files!", font=f_small,
                  fill=(120, 130, 160))

    # ── Progress bar (toward next milestone) ─────────────────────────────────
    milestones = [1, 10, 50, 100, 500]
    next_ms    = next((m for m in milestones if m > total_ops), milestones[-1])
    prev_ms    = max((m for m in milestones if m <= total_ops), default=0)
    progress   = (total_ops - prev_ms) / max(next_ms - prev_ms, 1)
    progress   = min(1.0, progress)
    bar_w      = W - 60
    draw.text((30, 355), f"Next milestone: {next_ms} files", font=f_small, fill=(150,160,200))
    draw.rounded_rectangle([30, 372, 30+bar_w, 390], radius=8, fill=(40, 40, 70))
    if progress > 0:
        draw.rounded_rectangle([30, 372, 30+int(bar_w*progress), 390], radius=8, fill=acc)
    draw.text((30, 395), f"{total_ops}/{next_ms} files • {int(progress*100)}% to next badge",
              font=f_small, fill=(120,130,160))

    # ── Footer ───────────────────────────────────────────────────────────────
    date_str = datetime.date.today().strftime("%d %b %Y")
    draw.text((30, 425), f"Generated on {date_str}", font=f_small, fill=(80, 90, 120))
    footer = "@SerenaXdev • Nexora PDF Doctor"
    fbbox  = draw.textbbox((0, 0), footer, font=f_small)
    draw.text((W - fbbox[2] + fbbox[0] - 30, 425), footer, font=f_small, fill=(80,90,120))

    # ── Bottom accent bar ────────────────────────────────────────────────────
    draw.rectangle([0, H-4, W, H], fill=acc)

    buf = io.BytesIO()
    img.save(buf, "PNG", quality=95)
    return buf.getvalue()
