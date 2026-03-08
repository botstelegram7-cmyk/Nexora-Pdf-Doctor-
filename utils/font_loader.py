"""
Font Loader v4.1 — FIXED: No 'requests' dependency at all.
Uses ONLY Python built-ins: urllib.request + ssl.
"""
import os, logging, urllib.request, urllib.error, ssl

logger = logging.getLogger(__name__)
FONTS_DIR = "fonts"

FONT_URLS = {
    "Caveat.ttf":           "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf",
    "DancingScript.ttf":    "https://github.com/google/fonts/raw/main/ofl/dancingscript/DancingScript%5Bwght%5D.ttf",
    "Kalam.ttf":            "https://fonts.gstatic.com/s/kalam/v16/YA9Qr0Wd4kDdMtD6GgLLmA.ttf",
    "Pacifico.ttf":         "https://fonts.gstatic.com/s/pacifico/v22/FwZY7-Qmy14u9lezJ96A4sijpFu_.ttf",
    "Satisfy.ttf":          "https://fonts.gstatic.com/s/satisfy/v21/rP2Hp2yn6lkG50LoOZSCHBeHFl0kOwk.ttf",
    "ShadowsIntoLight.ttf": "https://fonts.gstatic.com/s/shadowsintolight/v19/UqyNK9UOIntux_czAvDQx_ZcHqZXBNQDcsr55A.ttf",
    "Yellowtail.ttf":       "https://fonts.gstatic.com/s/yellowtail/v22/OZpGg_pnoDtINPfRIlLotlzNitn3hA.ttf",
    "Sacramento.ttf":       "https://fonts.gstatic.com/s/sacramento/v15/buEzpo6gcdjy0EiZMBUG4CMf_f5Iai0.ttf",
    "AmaticSC.ttf":         "https://fonts.gstatic.com/s/amaticsc/v26/TUZyzwprpvBS1izr_vOECuSf.ttf",
    "IndieFlower.ttf":      "https://fonts.gstatic.com/s/indieflower/v21/m8JVjfNVeKWVnh3QMuKkFcZlbkGG1dqEfw.ttf",
    "PatrickHand.ttf":      "https://fonts.gstatic.com/s/patrickhand/v23/LDI1apSQOAYtSuYWp8ZweqbHMoB8p3tGpA.ttf",
    "Mali.ttf":             "https://fonts.gstatic.com/s/mali/v10/N0bX2SRONuN4QOLlKlRaJdbWgdY.ttf",
    "Courgette.ttf":        "https://fonts.gstatic.com/s/courgette/v17/wEO_EBrAnc9BLjLQAUkFUfeACwCPrA.ttf",
    "PaytoneOne.ttf":       "https://fonts.gstatic.com/s/paytoneone/v23/0nksC9P7MfYHj2oFtYm2ChTjgPvNiA.ttf",
}

def _dl(url: str, dest: str) -> bool:
    headers = {"User-Agent": "Mozilla/5.0 FontBot/1.0"}
    for verify_ssl in (True, False):
        try:
            req = urllib.request.Request(url, headers=headers)
            if verify_ssl:
                resp = urllib.request.urlopen(req, timeout=25)
            else:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                resp = urllib.request.urlopen(req, context=ctx, timeout=25)
            with resp:
                data = resp.read()
            if len(data) > 1000:
                os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(data)
                return True
        except Exception as e:
            logger.debug(f"Download attempt failed ({url}): {e}")
    return False

def download_fonts():
    os.makedirs(FONTS_DIR, exist_ok=True)
    ok = fail = skip = 0
    for fname, url in FONT_URLS.items():
        fpath = os.path.join(FONTS_DIR, fname)
        if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
            skip += 1; continue
        logger.info(f"⬇️  {fname}...")
        if _dl(url, fpath):
            logger.info(f"✅ {fname} ({os.path.getsize(fpath)//1024} KB)")
            ok += 1
        else:
            logger.warning(f"⚠️  {fname} failed — Helvetica fallback will be used")
            fail += 1
    logger.info(f"🔤 Fonts: {ok} downloaded · {skip} cached · {fail} failed")

def get_font_path(font_key: str) -> str | None:
    from config import FONTS
    info = FONTS.get(font_key)
    if not info: return None
    path = info["file"]
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    fname = os.path.basename(path)
    url   = FONT_URLS.get(fname)
    if url:
        os.makedirs(FONTS_DIR, exist_ok=True)
        if _dl(url, path): return path
    logger.warning(f"Font '{font_key}' unavailable — using Helvetica")
    return None

def download_extra_fonts():
    """Download v8 extra handwriting fonts."""
    from config import EXTRA_FONT_URLS
    FONTS_DIR = "fonts"
    os.makedirs(FONTS_DIR, exist_ok=True)
    ok = skip = fail = 0
    for fname, url in EXTRA_FONT_URLS.items():
        fpath = os.path.join(FONTS_DIR, fname)
        if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
            skip += 1; continue
        logger.info(f"⬇️  Extra font: {fname}...")
        if _dl(url, fpath):
            ok += 1
        else:
            fail += 1
    logger.info(f"🔤 Extra fonts: {ok} downloaded · {skip} cached · {fail} failed")

def get_extra_font_path(font_key: str) -> str | None:
    """Get path for extra v8 fonts."""
    from config import EXTRA_FONTS, EXTRA_FONT_URLS
    info = EXTRA_FONTS.get(font_key)
    if not info: return None
    path  = info["file"]
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    fname = os.path.basename(path)
    url   = EXTRA_FONT_URLS.get(fname)
    if url:
        os.makedirs(FONTS_DIR, exist_ok=True)
        if _dl(url, path): return path
    return None

def get_any_font_path(font_key: str) -> str | None:
    """Check both original and extra fonts."""
    path = get_font_path(font_key)
    if path: return path
    return get_extra_font_path(font_key)
