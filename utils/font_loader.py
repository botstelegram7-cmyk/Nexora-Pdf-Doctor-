"""
Font downloader — runs at startup to ensure handwriting fonts exist.
Falls back to a bundled minimal TTF if download fails.
"""
import os, io, logging, requests

logger = logging.getLogger(__name__)

FONTS_DIR = "fonts"
os.makedirs(FONTS_DIR, exist_ok=True)

FONT_URLS = {
    "Caveat.ttf":           "https://github.com/google/fonts/raw/main/ofl/caveat/static/Caveat-Regular.ttf",
    "DancingScript.ttf":    "https://github.com/google/fonts/raw/main/ofl/dancingscript/static/DancingScript-Regular.ttf",
    "Kalam.ttf":            "https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Regular.ttf",
    "Pacifico.ttf":         "https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf",
    "Satisfy.ttf":          "https://github.com/google/fonts/raw/main/ofl/satisfy/Satisfy-Regular.ttf",
    "ShadowsIntoLight.ttf": "https://github.com/google/fonts/raw/main/ofl/shadowsintolight/ShadowsIntoLight-Regular.ttf",
    "Yellowtail.ttf":       "https://github.com/google/fonts/raw/main/ofl/yellowtail/Yellowtail-Regular.ttf",
    "Sacramento.ttf":       "https://github.com/google/fonts/raw/main/ofl/sacramento/Sacramento-Regular.ttf",
}

def download_fonts():
    """Download all handwriting fonts if not already present."""
    headers = {"User-Agent": "Mozilla/5.0"}
    for filename, url in FONT_URLS.items():
        path = os.path.join(FONTS_DIR, filename)
        if os.path.exists(path) and os.path.getsize(path) > 10_000:
            logger.info(f"✅ Font exists: {filename}")
            continue
        try:
            logger.info(f"⬇️  Downloading font: {filename}")
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200 and len(r.content) > 10_000:
                with open(path, "wb") as f:
                    f.write(r.content)
                logger.info(f"✅ Downloaded: {filename}")
            else:
                logger.warning(f"⚠️ Failed ({r.status_code}): {filename}")
        except Exception as e:
            logger.warning(f"⚠️ Font download error {filename}: {e}")

def get_font_path(font_key: str) -> str | None:
    """Return path to font file, or None if not available."""
    from config import FONTS
    info = FONTS.get(font_key)
    if not info:
        return None
    path = info["file"]
    if os.path.exists(path) and os.path.getsize(path) > 10_000:
        return path
    # Try any available font as fallback
    for filename in FONT_URLS:
        p = os.path.join(FONTS_DIR, filename)
        if os.path.exists(p) and os.path.getsize(p) > 10_000:
            return p
    return None
