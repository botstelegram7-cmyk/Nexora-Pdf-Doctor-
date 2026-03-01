"""
PDF utility functions — all heavy lifting happens here.
Fixed: compress, OCR layout, new features.
"""
import io, os, tempfile, subprocess
import fitz  # PyMuPDF
import pikepdf
from PIL import Image, ImageDraw, ImageFont, ImageOps
from config import FONTS
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ─────────────────────────────────────────────────────────────────────────────
# COMPRESS  (Fixed — tries multiple strategies, returns smallest)
# ─────────────────────────────────────────────────────────────────────────────
def compress_pdf(data: bytes) -> bytes:
    results = []

    # Strategy 1: PyMuPDF garbage+deflate
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            buf = io.BytesIO()
            doc.save(buf, garbage=4, deflate=True, deflate_images=True,
                     deflate_fonts=True, clean=True)
            results.append(buf.getvalue())
    except Exception:
        pass

    # Strategy 2: pikepdf with compression
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            buf = io.BytesIO()
            pdf.save(buf, compress_streams=True, stream_decode_level=pikepdf.StreamDecodeLevel.generalized)
            results.append(buf.getvalue())
    except Exception:
        pass

    # Strategy 3: Image-downscale (for image-heavy PDFs)
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            for page in doc:
                for img in page.get_images(full=True):
                    xref = img[0]
                    base = doc.extract_image(xref)
                    pil_img = Image.open(io.BytesIO(base["image"]))
                    if pil_img.width > 1500 or pil_img.height > 1500:
                        pil_img.thumbnail((1500, 1500), Image.LANCZOS)
                    out_buf = io.BytesIO()
                    pil_img.save(out_buf, format="JPEG", quality=75, optimize=True)
                    doc.update_stream(xref, out_buf.getvalue())
            buf = io.BytesIO()
            doc.save(buf, garbage=3, deflate=True, clean=True)
            results.append(buf.getvalue())
    except Exception:
        pass

    if not results:
        return data

    # Return the smallest result that is <= original size
    best = min(results, key=len)
    return best if len(best) < len(data) else data


# ─────────────────────────────────────────────────────────────────────────────
# SPLIT
# ─────────────────────────────────────────────────────────────────────────────
def split_pdf_all(data: bytes) -> list:
    with fitz.open(stream=data, filetype="pdf") as doc:
        results = []
        for i in range(len(doc)):
            out = fitz.open()
            out.insert_pdf(doc, from_page=i, to_page=i)
            buf = io.BytesIO()
            out.save(buf)
            results.append(buf.getvalue())
        return results

def split_pdf_range(data: bytes, ranges: str) -> list:
    """ranges: '1-3' or '1,3,5' or '2-' """
    with fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
        pages = _parse_range(ranges, total)
        out = fitz.open()
        for p in pages:
            out.insert_pdf(doc, from_page=p, to_page=p)
        buf = io.BytesIO()
        out.save(buf)
        return [buf.getvalue()]


# ─────────────────────────────────────────────────────────────────────────────
# MERGE
# ─────────────────────────────────────────────────────────────────────────────
def merge_pdfs(pdfs: list) -> bytes:
    out = fitz.open()
    for data in pdfs:
        with fitz.open(stream=data, filetype="pdf") as doc:
            out.insert_pdf(doc)
    buf = io.BytesIO()
    out.save(buf)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# PDF ↔ IMAGES
# ─────────────────────────────────────────────────────────────────────────────
def pdf_to_images(data: bytes, dpi: int = 150) -> list:
    images = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            images.append(pix.tobytes("png"))
    return images

def images_to_pdf(image_bytes_list: list) -> bytes:
    import img2pdf
    return img2pdf.convert(image_bytes_list)


# ─────────────────────────────────────────────────────────────────────────────
# LOCK / UNLOCK
# ─────────────────────────────────────────────────────────────────────────────
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
        raise ValueError("Wrong password! Please try again.")


# ─────────────────────────────────────────────────────────────────────────────
# REPAIR
# ─────────────────────────────────────────────────────────────────────────────
def repair_pdf(data: bytes) -> bytes:
    try:
        with pikepdf.open(io.BytesIO(data), suppress_warnings=True) as pdf:
            buf = io.BytesIO()
            pdf.save(buf)
            return buf.getvalue()
    except Exception:
        with fitz.open(stream=data, filetype="pdf") as doc:
            buf = io.BytesIO()
            doc.save(buf, garbage=3, clean=True)
            return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# WATERMARK
# ─────────────────────────────────────────────────────────────────────────────
def watermark_text(data: bytes, text: str, opacity: float = 0.25, invisible: bool = False) -> bytes:
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            w, h = page.rect.width, page.rect.height
            color  = (1, 1, 1) if invisible else (0.75, 0.1, 0.1)
            alpha  = 0.01 if invisible else opacity
            fsize  = max(24, min(w, h) // 7)
            # Center diagonal watermark
            page.insert_text(
                (w * 0.08, h * 0.55),
                text,
                fontsize=fsize,
                color=color,
                fill_opacity=alpha,
                rotate=45,
                overlay=True,
            )
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

def watermark_image(pdf_data: bytes, img_data: bytes) -> bytes:
    with fitz.open(stream=pdf_data, filetype="pdf") as doc:
        for page in doc:
            w, h  = page.rect.width, page.rect.height
            lw, lh = w * 0.3, h * 0.15
            rect  = fitz.Rect(w/2 - lw/2, h/2 - lh/2, w/2 + lw/2, h/2 + lh/2)
            page.insert_image(rect, stream=img_data, overlay=True)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# DARK MODE / BG CHANGER (image-based for reliability)
# ─────────────────────────────────────────────────────────────────────────────
BG_COLORS = {
    "bg_dark":   (15,   15,   15),
    "bg_navy":   (10,   25,   60),
    "bg_green":  (15,   35,   15),
    "bg_purple": (35,   10,   50),
    "bg_cream":  (255,  250,  220),
    "bg_brown":  (40,   20,   10),
    "bg_red":    (50,   8,    8),
    "bg_slate":  (30,   40,   60),
}

def change_bg(data: bytes, bg_key: str) -> bytes:
    bg = BG_COLORS.get(bg_key, (15, 15, 15))
    is_dark = sum(bg) < 400

    with fitz.open(stream=data, filetype="pdf") as doc:
        out = fitz.open()
        for page in doc:
            mat = fitz.Matrix(1.5, 1.5)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            bg_layer = Image.new("RGB", img.size, bg)

            if is_dark:
                gray = img.convert("L")
                inv  = ImageOps.invert(gray)
                inv_rgb = inv.convert("RGB")
                # Blend inverted content with bg
                blended = Image.blend(bg_layer, inv_rgb, alpha=0.85)
            else:
                # Light bg: keep original image, composite over bg
                blended = Image.blend(bg_layer, img, alpha=0.9)

            buf = io.BytesIO()
            blended.save(buf, "JPEG", quality=90)
            buf.seek(0)

            new_page = out.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, stream=buf.read())

        result = io.BytesIO()
        out.save(result)
        return result.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE NUMBERS
# ─────────────────────────────────────────────────────────────────────────────
def add_page_numbers(data: bytes, style: str = "pn_arabic") -> bytes:
    with fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
        for i, page in enumerate(doc):
            n = i + 1
            if style == "pn_arabic":   txt = str(n)
            elif style == "pn_roman":  txt = _to_roman(n)
            elif style == "pn_total":  txt = f"Page {n} of {total}"
            elif style == "pn_dash":   txt = f"— {n} —"
            else:                      txt = str(n)
            w = page.rect.width
            h = page.rect.height
            page.insert_text(
                (w / 2 - len(txt) * 3, h - 18),
                txt, fontsize=10, color=(0.35, 0.35, 0.35),
            )
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# ADD CUSTOM FOOTER
# ─────────────────────────────────────────────────────────────────────────────
def add_footer(data: bytes, footer_text: str) -> bytes:
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            w = page.rect.width
            h = page.rect.height
            page.draw_line(
                fitz.Point(30, h - 25),
                fitz.Point(w - 30, h - 25),
                color=(0.7, 0.7, 0.7), width=0.5
            )
            page.insert_text(
                (30, h - 10), footer_text,
                fontsize=8, color=(0.4, 0.4, 0.4)
            )
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# ADD TEXT TO PDF
# ─────────────────────────────────────────────────────────────────────────────
def add_text_to_pdf(data: bytes, text: str, page_num: int = 0,
                     x: float = 50, y: float = 50,
                     fontsize: int = 14, color: tuple = (0, 0, 0)) -> bytes:
    with fitz.open(stream=data, filetype="pdf") as doc:
        if page_num < len(doc):
            page = doc[page_num]
            page.insert_text(
                (x, y), text,
                fontsize=fontsize, color=color, overlay=True
            )
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# ROTATE PDF
# ─────────────────────────────────────────────────────────────────────────────
def rotate_pdf(data: bytes, angle: int) -> bytes:
    """angle: 90, -90, 180"""
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            page.set_rotation((page.rotation + angle) % 360)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

def auto_rotate_pdf(data: bytes) -> bytes:
    """Detect and fix incorrect orientations"""
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            w, h = page.rect.width, page.rect.height
            if w > h and page.rotation == 0:
                page.set_rotation(90)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# RESIZE / RESCALE PDF
# ─────────────────────────────────────────────────────────────────────────────
def resize_pdf_to_a4(data: bytes) -> bytes:
    """Rescale all pages to A4"""
    a4_w, a4_h = 595, 842  # A4 in points
    with fitz.open(stream=data, filetype="pdf") as doc:
        out = fitz.open()
        for page in doc:
            new_page = out.new_page(width=a4_w, height=a4_h)
            new_page.show_pdf_page(new_page.rect, doc, page.number)
        buf = io.BytesIO()
        out.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT SPECIFIC PAGES
# ─────────────────────────────────────────────────────────────────────────────
def extract_pages(data: bytes, page_range: str) -> bytes:
    with fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
        pages = _parse_range(page_range, total)
        out = fitz.open()
        for p in pages:
            out.insert_pdf(doc, from_page=p, to_page=p)
        buf = io.BytesIO()
        out.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# METADATA
# ─────────────────────────────────────────────────────────────────────────────
def get_metadata(data: bytes) -> dict:
    with fitz.open(stream=data, filetype="pdf") as doc:
        meta = doc.metadata
        return {
            "title":    meta.get("title", "—"),
            "author":   meta.get("author", "—"),
            "subject":  meta.get("subject", "—"),
            "creator":  meta.get("creator", "—"),
            "pages":    len(doc),
            "size":     file_size_str(data),
            "encrypted": doc.is_encrypted,
            "format":   meta.get("format", "—"),
        }


# ─────────────────────────────────────────────────────────────────────────────
# HANDWRITING STYLE PDF
# ─────────────────────────────────────────────────────────────────────────────
def create_handwritten_pdf(text: str, font_key: str) -> bytes:
    from utils.font_loader import get_font_path
    font_path = get_font_path(font_key)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Register font
    font_name = "Helvetica"
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont(font_key, font_path))
            font_name = font_key
        except Exception:
            pass

    def draw_page_lines(c):
        c.setStrokeColorRGB(0.75, 0.88, 1.0)
        c.setLineWidth(0.4)
        for y in range(int(h) - 75, 35, -28):
            c.line(40, y, w - 40, y)
        # Left margin line
        c.setStrokeColorRGB(1.0, 0.75, 0.75)
        c.setLineWidth(0.6)
        c.line(70, h - 75, 70, 35)

    draw_page_lines(c)
    c.setFont(font_name, 17)
    c.setFillColorRGB(0.05, 0.05, 0.3)

    # Word wrap
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            test = (line + " " + word).strip()
            if c.stringWidth(test, font_name, 17) < w - 120:
                line = test
            else:
                lines.append(line)
                line = word
        lines.append(line)

    y_pos = h - 78
    for line in lines:
        if y_pos < 45:
            c.showPage()
            draw_page_lines(c)
            c.setFont(font_name, 17)
            c.setFillColorRGB(0.05, 0.05, 0.3)
            y_pos = h - 78
        c.drawString(78, y_pos, line)
        y_pos -= 28

    c.save()
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# PDF → EXCEL
# ─────────────────────────────────────────────────────────────────────────────
def pdf_to_excel(data: bytes) -> bytes:
    import pdfplumber
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    wb.remove(wb.active)

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for i, page in enumerate(pdf.pages):
            ws = wb.create_sheet(title=f"Page {i+1}")
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row_idx, row in enumerate(table):
                        ws.append([cell or "" for cell in row])
                        if row_idx == 0:
                            for cell in ws[ws.max_row]:
                                cell.font = Font(bold=True)
                                cell.fill = PatternFill("solid", fgColor="D0E8FF")
            else:
                text = page.extract_text() or ""
                for row in text.split("\n"):
                    ws.append([row])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# OCR — LAYOUT PRESERVING (Fixed!)
# ─────────────────────────────────────────────────────────────────────────────
def ocr_image(data: bytes) -> str:
    try:
        import pytesseract
        img = Image.open(io.BytesIO(data))
        # PSM 6: uniform block of text (preserves layout)
        config = "--psm 6 --oem 3"
        text = pytesseract.image_to_string(img, config=config, lang="eng+hin")
        return text.strip() or "⚠️ No text detected in this image."
    except Exception as e:
        return f"⚠️ OCR Error: {e}"

def ocr_pdf(data: bytes) -> str:
    """Layout-preserving text extraction from PDF"""
    try:
        import pytesseract
        with fitz.open(stream=data, filetype="pdf") as doc:
            all_pages = []
            for i, page in enumerate(doc):
                # Try native text first
                blocks = page.get_text("blocks")
                if blocks:
                    # Sort blocks top-to-bottom, left-to-right
                    blocks.sort(key=lambda b: (round(b[1] / 20) * 20, b[0]))
                    lines = [b[4].strip() for b in blocks if b[4].strip()]
                    native_text = "\n".join(lines)
                    if len(native_text.strip()) > 30:
                        all_pages.append(f"[Page {i+1}]\n{native_text}")
                        continue

                # OCR fallback for image-based pages
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                config = "--psm 6 --oem 3"
                text = pytesseract.image_to_string(img, config=config, lang="eng+hin")
                all_pages.append(f"[Page {i+1}]\n{text.strip()}")

            return "\n\n" + "─" * 40 + "\n\n".join(all_pages)
    except Exception as e:
        return f"⚠️ Error: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _parse_range(s: str, total: int) -> list:
    pages = set()
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            a = int(a) - 1 if a.strip() else 0
            b = int(b) - 1 if b.strip() else total - 1
            pages.update(range(a, b + 1))
        elif part:
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
    return f"{kb/1024:.2f} MB" if kb > 1024 else f"{kb:.1f} KB"
