"""
Font Loader v3 — Downloads all handwriting fonts from Google Fonts
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)

FONT_URLS = {
    # Original fonts
    "Caveat.ttf":             "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf",
    "DancingScript.ttf":      "https://github.com/google/fonts/raw/main/ofl/dancingscript/DancingScript%5Bwght%5D.ttf",
    "Kalam.ttf":              "https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Regular.ttf",
    "Pacifico.ttf":           "https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf",
    "Satisfy.ttf":            "https://github.com/google/fonts/raw/main/ofl/satisfy/Satisfy-Regular.ttf",
    "ShadowsIntoLight.ttf":   "https://github.com/google/fonts/raw/main/ofl/shadowsintolight/ShadowsIntoLight-Regular.ttf",
    "Yellowtail.ttf":         "https://github.com/google/fonts/raw/main/ofl/yellowtail/Yellowtail-Regular.ttf",
    "Sacramento.ttf":         "https://github.com/google/fonts/raw/main/ofl/sacramento/Sacramento-Regular.ttf",
    # New fonts v3
    "AmaticSC.ttf":           "https://github.com/google/fonts/raw/main/ofl/amaticsc/AmaticSC-Regular.ttf",
    "IndieFlower.ttf":        "https://github.com/google/fonts/raw/main/ofl/indieflower/IndieFlower-Regular.ttf",
    "PatrickHand.ttf":        "https://github.com/google/fonts/raw/main/ofl/patrickhand/PatrickHand-Regular.ttf",
    "Mali.ttf":               "https://github.com/google/fonts/raw/main/ofl/mali/Mali-Regular.ttf",
    "Courgette.ttf":          "https://github.com/google/fonts/raw/main/ofl/courgette/Courgette-Regular.ttf",
    "PaytoneOne.ttf":         "https://github.com/google/fonts/raw/main/ofl/paytoneone/PaytoneOne-Regular.ttf",
}

FONTS_DIR = "fonts"

def download_fonts():
    os.makedirs(FONTS_DIR, exist_ok=True)
    for filename, url in FONT_URLS.items():
        fpath = os.path.join(FONTS_DIR, filename)
        if os.path.exists(fpath):
            continue
        try:
            logger.info(f"⬇️ Downloading {filename}...")
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                with open(fpath, "wb") as f:
                    f.write(r.content)
                logger.info(f"✅ {filename} downloaded")
            else:
                logger.warning(f"⚠️ Failed {filename}: {r.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Could not download {filename}: {e}")

def get_font_path(font_key: str) -> str | None:
    from config import FONTS
    font_info = FONTS.get(font_key)
    if not font_info:
        return None
    path = font_info["file"]
    if os.path.exists(path):
        return path
    return None
