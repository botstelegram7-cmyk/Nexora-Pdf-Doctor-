"""
PDF utility functions — all heavy lifting happens here.
"""
import io, os, tempfile, re
import fitz  # PyMuPDF
import pikepdf
from PIL import Image, ImageDraw, ImageFont
from config import FONTS
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


# ────────────────────────────────────────────────────────────────────────────
# COMPRESS
# ────────────────────────────────────────────────────────────────────────────
def compress_pdf(data: bytes) -> bytes:
    with fitz.open(stream=data, filetype="pdf") as doc:
        buf = io.BytesIO()
        doc.save(buf, garbage=4, deflate=True, clean=True)
        return buf.getvalue()


# ────────────────────────────────────────────────────────────────────────────
# SPLIT
# ────────────────────────────────────────────────────────────────────────────
def split_pdf(data: bytes, page_range: str) -> list[bytes]:
    """page_range examples: '1-3', '1,2,5', '2-'"""
    with fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
        pages = _parse_range(page_range, total)
        results = []
        for p in pages:
            out = fitz.open()
            out.insert_pdf(doc, from_page=p, to_page=p)
            buf = io.BytesIO()
            out.save(buf)
            results.append(buf.getvalue())
        return results

def split_pdf_all(data: bytes) -> list[bytes]:
    with fitz.open(stream=data, filetype="pdf") as doc:
        results = []
        for i in range(len(doc)):
            out = fitz.open()
            out.insert_pdf(doc, from_page=i, to_page=i)
            buf = io.BytesIO()
            out.save(buf)
            results.append(buf.getvalue())
        return results


# ────────────────────────────────────────────────────────────────────────────
# MERGE
# ────────────────────────────────────────────────────────────────────────────
def merge_pdfs(pdfs: list[bytes]) -> bytes:
    out = fitz.open()
    for data in pdfs:
        with fitz.open(stream=data, filetype="pdf") as doc:
            out.insert_pdf(doc)
    buf = io.BytesIO()
    out.save(buf)
    return buf.getvalue()


# ────────────────────────────────────────────────────────────────────────────
# PDF → IMAGES
# ────────────────────────────────────────────────────────────────────────────
def pdf_to_images(data: bytes, dpi: int = 150) -> list[bytes]:
    images = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_data = pix.tobytes("png")
            images.append(img_data)
    return images


# ────────────────────────────────────────────────────────────────────────────
# IMAGES → PDF
# ────────────────────────────────────────────────────────────────────────────
def images_to_pdf(image_bytes_list: list[bytes]) -> bytes:
    import img2pdf
    return img2pdf.convert(image_bytes_list)


# ────────────────────────────────────────────────────────────────────────────
# LOCK / UNLOCK
# ────────────────────────────────────────────────────────────────────────────
def lock_pdf(data: bytes, password: str) -> bytes:
    with pikepdf.open(io.BytesIO(data)) as pdf:
        buf = io.BytesIO()
        pdf.save(buf, encryption=pikepdf.Encryption(owner=password, user=password, R=4))
        return buf.getvalue()

def unlock_pdf(data: bytes, password: str = "") -> bytes:
    try:
        with pikepdf.open(io.BytesIO(data), password=password) as pdf:
            buf = io.BytesIO()
            pdf.save(buf)
            return buf.getvalue()
    except pikepdf.PasswordError:
        raise ValueError("❌ Wrong password!")


# ────────────────────────────────────────────────────────────────────────────
# REPAIR
# ────────────────────────────────────────────────────────────────────────────
def repair_pdf(data: bytes) -> bytes:
    try:
        with pikepdf.open(io.BytesIO(data), suppress_warnings=True) as pdf:
            buf = io.BytesIO()
            pdf.save(buf)
            return buf.getvalue()
    except Exception:
        # Try with PyMuPDF as fallback
        with fitz.open(stream=data, filetype="pdf") as doc:
            buf = io.BytesIO()
            doc.save(buf, garbage=3, clean=True)
            return buf.getvalue()


# ────────────────────────────────────────────────────────────────────────────
# WATERMARK
# ────────────────────────────────────────────────────────────────────────────
def watermark_text(data: bytes, text: str, opacity: float = 0.3, invisible: bool = False) -> bytes:
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            w, h = page.rect.width, page.rect.height
            # diagonal watermark
            if invisible:
                color = (1, 1, 1)   # white = invisible on white bg
                opacity = 0.01
            else:
                color = (0.8, 0.1, 0.1)
            page.insert_text(
                (w * 0.1, h * 0.55),
                text,
                fontsize=max(20, min(w, h) // 8),
                color=color,
                fill_opacity=opacity,
                rotate=45,
                overlay=True,
            )
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

def watermark_image(pdf_data: bytes, img_data: bytes, opacity: float = 0.3) -> bytes:
    """Add image/logo watermark to each page"""
    with fitz.open(stream=pdf_data, filetype="pdf") as doc:
        # Save logo temp
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(img_data)
        tmp.close()
        logo_doc = fitz.open(tmp.name)
        logo_pdf_bytes = logo_doc.convert_to_pdf()
        logo_doc.close()
        os.unlink(tmp.name)

        for page in doc:
            w, h = page.rect.width, page.rect.height
            lw, lh = w * 0.3, h * 0.15
            rect = fitz.Rect(w/2 - lw/2, h/2 - lh/2, w/2 + lw/2, h/2 + lh/2)
            page.insert_image(rect, stream=img_data, overlay=True)

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ────────────────────────────────────────────────────────────────────────────
# DARK MODE
# ────────────────────────────────────────────────────────────────────────────
BG_COLORS = {
    "bg_dark":   (0,    0,    0),
    "bg_navy":   (0,    31,   63),
    "bg_green":  (19,   44,   19),
    "bg_purple": (44,   0,    60),
    "bg_cream":  (255,  253,  208),
    "bg_red":    (60,   10,   10),
}

def change_bg(data: bytes, bg_key: str) -> bytes:
    bg = BG_COLORS.get(bg_key, (0, 0, 0))
    r, g, b = [x / 255 for x in bg]
    # text color: white for dark bgs, black for cream
    tc = (1, 1, 1) if bg[0] + bg[1] + bg[2] < 400 else (0, 0, 0)

    images = pdf_to_images(data, dpi=150)
    colored_imgs = []
    for img_bytes in images:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        bg_img = Image.new("RGBA", img.size, (int(bg[0]), int(bg[1]), int(bg[2]), 255))
        # Invert white areas
        r_ch, g_ch, b_ch, a_ch = img.split()
        inv = Image.merge("RGBA", (
            ImageOps_invert(r_ch),
            ImageOps_invert(g_ch),
            ImageOps_invert(b_ch),
            a_ch
        ))
        bg_img.paste(inv, (0, 0), inv)
        buf = io.BytesIO()
        bg_img.convert("RGB").save(buf, format="PNG")
        colored_imgs.append(buf.getvalue())
    return images_to_pdf(colored_imgs)

def ImageOps_invert(ch):
    from PIL import ImageOps
    return ImageOps.invert(ch)


# ────────────────────────────────────────────────────────────────────────────
# PAGE NUMBERS
# ────────────────────────────────────────────────────────────────────────────
def add_page_numbers(data: bytes, style: str = "pn_arabic") -> bytes:
    with fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
        for i, page in enumerate(doc):
            n = i + 1
            if style == "pn_arabic":
                txt = str(n)
            elif style == "pn_roman":
                txt = _to_roman(n)
            elif style == "pn_total":
                txt = f"Page {n} of {total}"
            elif style == "pn_dash":
                txt = f"- {n} -"
            else:
                txt = str(n)
            w = page.rect.width
            h = page.rect.height
            page.insert_text(
                (w / 2 - 20, h - 20),
                txt,
                fontsize=10,
                color=(0.3, 0.3, 0.3),
            )
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ────────────────────────────────────────────────────────────────────────────
# HANDWRITING STYLE
# ────────────────────────────────────────────────────────────────────────────
def create_handwritten_pdf(text: str, font_key: str) -> bytes:
    font_info = FONTS.get(font_key, list(FONTS.values())[0])
    font_path = font_info["file"]

    # Check if font exists
    if not os.path.exists(font_path):
        font_path = None  # will use default

    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Register font if available
    font_name = "Helvetica"
    if font_path and os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont(font_key, font_path))
            font_name = font_key
        except Exception:
            pass

    c.setFont(font_name, 18)
    c.setFillColorRGB(0.05, 0.05, 0.4)

    # Draw lined paper background
    c.setStrokeColorRGB(0.7, 0.85, 1.0)
    c.setLineWidth(0.5)
    for y in range(int(h) - 80, 40, -30):
        c.line(40, y, w - 40, y)

    # Write text with word wrap
    lines = []
    words = text.split()
    line = ""
    max_chars = 55
    for word in words:
        if len(line) + len(word) + 1 <= max_chars:
            line += (" " if line else "") + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    y_pos = h - 80
    for line in lines:
        if y_pos < 60:
            c.showPage()
            c.setFont(font_name, 18)
            c.setFillColorRGB(0.05, 0.05, 0.4)
            # Re-draw lines on new page
            c.setStrokeColorRGB(0.7, 0.85, 1.0)
            c.setLineWidth(0.5)
            for yy in range(int(h) - 80, 40, -30):
                c.line(40, yy, w - 40, yy)
            y_pos = h - 80
        c.drawString(50, y_pos, line)
        y_pos -= 30

    c.save()
    return buf.getvalue()


# ────────────────────────────────────────────────────────────────────────────
# PDF → EXCEL
# ────────────────────────────────────────────────────────────────────────────
def pdf_to_excel(data: bytes) -> bytes:
    import pdfplumber
    from openpyxl import Workbook

    wb = Workbook()
    wb.remove(wb.active)  # remove default sheet

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for i, page in enumerate(pdf.pages):
            ws = wb.create_sheet(title=f"Page {i+1}")
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        ws.append([cell or "" for cell in row])
            else:
                # fallback: dump all text
                text = page.extract_text() or ""
                for row in text.split("\n"):
                    ws.append([row])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ────────────────────────────────────────────────────────────────────────────
# OCR (Image → Text)
# ────────────────────────────────────────────────────────────────────────────
def ocr_image(data: bytes) -> str:
    try:
        import pytesseract
        img = Image.open(io.BytesIO(data))
        text = pytesseract.image_to_string(img)
        return text.strip() or "⚠️ No text detected in this image."
    except Exception as e:
        return f"⚠️ OCR Error: {e}"

def ocr_pdf(data: bytes) -> str:
    """Extract text from PDF (native first, OCR fallback)"""
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            texts = []
            for page in doc:
                text = page.get_text().strip()
                if text:
                    texts.append(text)
                else:
                    # OCR the page image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("png")
                    texts.append(ocr_image(img_data))
            return "\n\n--- Page Break ---\n\n".join(texts)
    except Exception as e:
        return f"⚠️ Error: {e}"


# ────────────────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────────────────
def _parse_range(s: str, total: int) -> list[int]:
    pages = set()
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            a = int(a) - 1 if a else 0
            b = int(b) - 1 if b else total - 1
            pages.update(range(a, b + 1))
        else:
            pages.add(int(part) - 1)
    return sorted(p for p in pages if 0 <= p < total)

def _to_roman(n: int) -> str:
    vals = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),
            (50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    result = ""
    for v, s in vals:
        while n >= v:
            result += s
            n -= v
    return result

def file_size_str(data: bytes) -> str:
    kb = len(data) / 1024
    if kb > 1024:
        return f"{kb/1024:.2f} MB"
    return f"{kb:.1f} KB"
