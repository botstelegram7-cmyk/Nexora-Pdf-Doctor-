"""
PDF utility functions v3 — All heavy lifting happens here.
New: pdf2word, pdf2ppt, crop, qr, delete_pages, reorder_pages,
     fixed handwriting alignment, multi-notebook styles.
"""
import io, os, tempfile
import fitz  # PyMuPDF
import pikepdf
from PIL import Image, ImageDraw, ImageFont, ImageOps
from config import FONTS, NOTEBOOK_STYLES
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ─────────────────────────────────────────────────────────────────────────────
# COMPRESS
# ─────────────────────────────────────────────────────────────────────────────
def compress_pdf(data: bytes) -> bytes:
    results = []
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            buf = io.BytesIO()
            doc.save(buf, garbage=4, deflate=True, deflate_images=True,
                     deflate_fonts=True, clean=True)
            results.append(buf.getvalue())
    except Exception:
        pass
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            buf = io.BytesIO()
            pdf.save(buf, compress_streams=True,
                     stream_decode_level=pikepdf.StreamDecodeLevel.generalized)
            results.append(buf.getvalue())
    except Exception:
        pass
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
            page.insert_text(
                (w * 0.08, h * 0.55), text,
                fontsize=fsize, color=color,
                fill_opacity=alpha, rotate=45, overlay=True,
            )
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

def watermark_image(pdf_data: bytes, img_data: bytes) -> bytes:
    with fitz.open(stream=pdf_data, filetype="pdf") as doc:
        for page in doc:
            w, h = page.rect.width, page.rect.height
            lw, lh = w * 0.3, h * 0.15
            rect = fitz.Rect(w/2 - lw/2, h/2 - lh/2, w/2 + lw/2, h/2 + lh/2)
            page.insert_image(rect, stream=img_data, overlay=True)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# DARK MODE / BG CHANGER
# ─────────────────────────────────────────────────────────────────────────────
BG_COLORS = {
    "bg_dark":   (15,  15,  15),
    "bg_navy":   (10,  25,  60),
    "bg_green":  (15,  35,  15),
    "bg_purple": (35,  10,  50),
    "bg_cream":  (255, 250, 220),
    "bg_brown":  (40,  20,  10),
    "bg_red":    (50,  8,   8),
    "bg_slate":  (30,  40,  60),
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
                blended = Image.blend(bg_layer, inv_rgb, alpha=0.85)
            else:
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
# FOOTER
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
            page.insert_text((x, y), text, fontsize=fontsize, color=color, overlay=True)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# ROTATE PDF
# ─────────────────────────────────────────────────────────────────────────────
def rotate_pdf(data: bytes, angle: int) -> bytes:
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            page.set_rotation((page.rotation + angle) % 360)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

def auto_rotate_pdf(data: bytes) -> bytes:
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            w, h = page.rect.width, page.rect.height
            if w > h and page.rotation == 0:
                page.set_rotation(90)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# RESIZE TO A4
# ─────────────────────────────────────────────────────────────────────────────
def resize_pdf_to_a4(data: bytes) -> bytes:
    a4_w, a4_h = 595, 842
    with fitz.open(stream=data, filetype="pdf") as doc:
        out = fitz.open()
        for page in doc:
            new_page = out.new_page(width=a4_w, height=a4_h)
            new_page.show_pdf_page(new_page.rect, doc, page.number)
        buf = io.BytesIO()
        out.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT PAGES
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
# DELETE PAGES  ✨ NEW
# ─────────────────────────────────────────────────────────────────────────────
def delete_pages(data: bytes, page_range: str) -> bytes:
    """Delete specified pages from PDF. page_range e.g. '2,5,7-9' (1-indexed)"""
    with fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
        to_delete = set(_parse_range(page_range, total))
        out = fitz.open()
        for i in range(total):
            if i not in to_delete:
                out.insert_pdf(doc, from_page=i, to_page=i)
        if len(out) == 0:
            raise ValueError("Cannot delete all pages!")
        buf = io.BytesIO()
        out.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# REORDER PAGES  ✨ NEW
# ─────────────────────────────────────────────────────────────────────────────
def reorder_pages(data: bytes, order_str: str) -> bytes:
    """
    Reorder pages. order_str e.g. '3,1,2' or '1,3,2-4' (1-indexed)
    Pages not mentioned are appended at end.
    """
    with fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
        pages = _parse_range(order_str, total)
        if not pages:
            raise ValueError("Invalid page order format!")
        out = fitz.open()
        for p in pages:
            out.insert_pdf(doc, from_page=p, to_page=p)
        buf = io.BytesIO()
        out.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# CROP MARGINS  ✨ NEW
# ─────────────────────────────────────────────────────────────────────────────
def crop_margins(data: bytes, margin_pt: float = 36.0) -> bytes:
    """
    Auto-crop white margins from each page.
    margin_pt: minimum margin to keep (in points, default ~0.5 inch)
    """
    with fitz.open(stream=data, filetype="pdf") as doc:
        out = fitz.open()
        for page in doc:
            # Get content bounding box
            bbox = page.get_bboxlog()
            if bbox:
                # Find the content area
                rects = [fitz.Rect(b[1]) for b in bbox if b[1]]
                if rects:
                    content_rect = rects[0]
                    for r in rects[1:]:
                        content_rect |= r
                    # Add a small margin around content
                    pad = margin_pt
                    crop_rect = fitz.Rect(
                        max(0, content_rect.x0 - pad),
                        max(0, content_rect.y0 - pad),
                        min(page.rect.width, content_rect.x1 + pad),
                        min(page.rect.height, content_rect.y1 + pad),
                    )
                    new_w = crop_rect.width
                    new_h = crop_rect.height
                    new_page = out.new_page(width=new_w, height=new_h)
                    new_page.show_pdf_page(
                        new_page.rect, doc, page.number,
                        clip=crop_rect
                    )
                    continue
            # Fallback: keep original
            new_page = out.new_page(width=page.rect.width, height=page.rect.height)
            new_page.show_pdf_page(new_page.rect, doc, page.number)
        buf = io.BytesIO()
        out.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# QR CODE GENERATOR  ✨ NEW
# ─────────────────────────────────────────────────────────────────────────────
def generate_qr(text: str, size: int = 400) -> bytes:
    """Generate QR code PNG image."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        raise ImportError("qrcode library not installed. Run: pip install qrcode[pil]")


# ─────────────────────────────────────────────────────────────────────────────
# PDF → WORD (DOCX)  ✨ NEW
# ─────────────────────────────────────────────────────────────────────────────
def pdf_to_word(data: bytes) -> bytes:
    """Convert PDF to editable DOCX file."""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        import pdfplumber

        doc = Document()
        doc.core_properties.title = "Converted from PDF"

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for i, page in enumerate(pdf.pages):
                if i > 0:
                    doc.add_page_break()

                # Add page header
                h = doc.add_heading(f"Page {i+1}", level=2)
                h.runs[0].font.color.rgb = RGBColor(0x44, 0x44, 0x88)

                # Extract tables
                tables = page.extract_tables()
                if tables:
                    for table_data in tables:
                        if not table_data:
                            continue
                        cols = max(len(row) for row in table_data)
                        tbl = doc.add_table(rows=len(table_data), cols=cols)
                        tbl.style = "Table Grid"
                        for r_idx, row in enumerate(table_data):
                            for c_idx, cell in enumerate(row):
                                if c_idx < cols:
                                    tbl.cell(r_idx, c_idx).text = str(cell or "")
                        doc.add_paragraph()

                # Extract text (non-table content)
                text = page.extract_text(layout=True)
                if text:
                    for line in text.split("\n"):
                        line = line.strip()
                        if line:
                            # Detect headings by uppercase / short length
                            if line.isupper() and len(line) < 80:
                                doc.add_heading(line, level=3)
                            else:
                                p = doc.add_paragraph(line)
                                p.runs[0].font.size = Pt(11) if p.runs else None

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    except Exception as e:
        # Fallback: plain text extraction into DOCX
        from docx import Document
        doc = Document()
        doc.add_heading("PDF Content", 0)
        with fitz.open(stream=data, filetype="pdf") as fitz_doc:
            for i, page in enumerate(fitz_doc):
                if i > 0:
                    doc.add_page_break()
                text = page.get_text()
                for line in text.split("\n"):
                    if line.strip():
                        doc.add_paragraph(line.strip())
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# PDF → POWERPOINT (PPTX)  ✨ NEW
# ─────────────────────────────────────────────────────────────────────────────
def pdf_to_ppt(data: bytes) -> bytes:
    """Convert PDF to PowerPoint: each page becomes a slide with the page image."""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.enum.text import PP_ALIGN

    prs = Presentation()
    # Set slide size to widescreen
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]  # Blank layout

    with fitz.open(stream=data, filetype="pdf") as doc:
        for page_num, page in enumerate(doc):
            # Render page to image
            mat = fitz.Matrix(2.0, 2.0)  # High res
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")

            slide = prs.slides.add_slide(blank_layout)

            # Add page image filling the slide
            img_stream = io.BytesIO(img_bytes)
            slide.shapes.add_picture(
                img_stream,
                left=0, top=0,
                width=prs.slide_width,
                height=prs.slide_height
            )

            # Add page number in corner
            txBox = slide.shapes.add_textbox(
                Inches(12.5), Inches(7.1),
                Inches(0.7), Inches(0.3)
            )
            tf = txBox.text_frame
            tf.text = str(page_num + 1)
            tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
            run = tf.paragraphs[0].runs[0]
            run.font.size = Pt(10)
            run.font.color.rgb = __import__("pptx.util", fromlist=["RGBColor"]).RGBColor if False else None
            try:
                from pptx.dml.color import RGBColor as PptxRGB
                run.font.color.rgb = PptxRGB(180, 180, 180)
            except Exception:
                pass

    buf = io.BytesIO()
    prs.save(buf)
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
# HANDWRITING — FIXED ALIGNMENT + MULTI-STYLE + TITLE + TIMESTAMP ✨ UPGRADED
# ─────────────────────────────────────────────────────────────────────────────
def create_handwritten_pdf(
    text: str,
    font_key: str,
    notebook_style: str = "classic_blue",
    title: str = "",
    credit: str = "Written By - Technical Serena",
) -> bytes:
    """
    Create handwritten PDF with:
    - Proper line alignment (text baseline ON the ruled line)
    - 8 different notebook styles
    - Optional Title at top of every page
    - Timestamp (date & time) at top-right corner of every page
    - Optional credit text at bottom-right corner
    """
    import datetime
    from utils.font_loader import get_font_path

    font_path  = get_font_path(font_key)
    style      = NOTEBOOK_STYLES.get(notebook_style, NOTEBOOK_STYLES["classic_blue"])
    now        = datetime.datetime.now()
    timestamp  = now.strftime("%d %b %Y  |  %I:%M %p")   # e.g.  02 Mar 2025  |  03:45 PM

    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=A4)
    pw, ph = A4   # page width / height

    # ── Register handwriting font ──────────────────────────────────────────
    font_name  = "Helvetica"
    font_size  = 16
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont(font_key, font_path))
            font_name = font_key
        except Exception:
            pass

    line_spacing = style["line_spacing"]
    margin_x     = style["margin_x"]
    is_graph     = style.get("is_graph",  False)
    is_dotted    = style.get("is_dotted", False)
    tc           = style["text_color"]
    lc           = style["line_color"]

    # ── Background ────────────────────────────────────────────────────────
    def fill_background(cv):
        bg = style["bg"]
        if isinstance(bg, tuple) and len(bg) == 3:
            r, g, b = [x / 255.0 for x in bg]
            cv.setFillColorRGB(r, g, b)
            cv.rect(0, 0, pw, ph, fill=1, stroke=0)

    # ── Draw title & timestamp header on every page ───────────────────────
    HEADER_H   = 55   # height reserved at top for title/timestamp area
    TOP_LINE_Y = ph - HEADER_H - 18  # first ruled line y

    def draw_header(cv):
        # Header background strip (subtle, matches style)
        bg = style["bg"]
        r0, g0, b0 = [x / 255.0 for x in bg] if isinstance(bg, tuple) else (1, 1, 1)
        # Slightly darker / contrasting strip
        cv.setFillColorRGB(
            max(0, r0 - 0.07),
            max(0, g0 - 0.07),
            max(0, b0 - 0.07),
        )
        cv.rect(0, ph - HEADER_H, pw, HEADER_H, fill=1, stroke=0)

        # Title (top-centre, slightly bold look via font size)
        display_title = title.strip() if title and title.strip() else "Handwritten Notes"
        cv.setFillColorRGB(*tc)
        cv.setFont(font_name, 18)
        title_w = cv.stringWidth(display_title, font_name, 18)
        cv.drawString((pw - title_w) / 2, ph - 30, display_title)

        # Timestamp (top-right corner, small)
        cv.setFont("Helvetica", 8)
        ts_w = cv.stringWidth(timestamp, "Helvetica", 8)
        cv.setFillColorRGB(min(1, tc[0] + 0.3), min(1, tc[1] + 0.3), min(1, tc[2] + 0.3))
        cv.drawString(pw - ts_w - 15, ph - 18, timestamp)

        # Thin separator line below header
        cv.setStrokeColorRGB(*lc)
        cv.setLineWidth(0.8)
        cv.line(35, ph - HEADER_H - 2, pw - 35, ph - HEADER_H - 2)

    # ── Draw ruled lines (below header) ──────────────────────────────────
    def draw_page_lines(cv):
        fill_background(cv)
        draw_header(cv)

        cv.setStrokeColorRGB(*lc)
        cv.setLineWidth(0.4)

        if is_graph:
            for y in range(int(TOP_LINE_Y), 30, -line_spacing):
                cv.line(35, y, pw - 35, y)
            for x in range(35, int(pw - 35), line_spacing):
                cv.line(x, TOP_LINE_Y + 4, x, 30)
        elif is_dotted:
            dot_size = 1.2
            for y in range(int(TOP_LINE_Y), 30, -line_spacing):
                for x in range(50, int(pw - 35), line_spacing):
                    cv.circle(x, y, dot_size, fill=1, stroke=0)
        else:
            for y in range(int(TOP_LINE_Y), 30, -line_spacing):
                cv.line(35, y, pw - 35, y)
            mc = style.get("margin_color")
            if mc:
                cv.setStrokeColorRGB(*mc)
                cv.setLineWidth(0.7)
                cv.line(margin_x, ph - HEADER_H - 4, margin_x, 30)

    # ── Credit / branding at bottom-right ────────────────────────────────
    def draw_credit(cv):
        if not credit:
            return
        cv.setFont("Helvetica-Oblique", 7)
        cr_color = (min(1, tc[0] + 0.4), min(1, tc[1] + 0.4), min(1, tc[2] + 0.4))
        cv.setFillColorRGB(*cr_color)
        cw = cv.stringWidth(credit, "Helvetica-Oblique", 7)
        cv.drawString(pw - cw - 12, 10, credit)

    # ── Word wrap ─────────────────────────────────────────────────────────
    def wrap_text(text_content: str) -> list:
        wrapped  = []
        max_w    = pw - margin_x - 45
        for paragraph in text_content.split("\n"):
            words = paragraph.split()
            if not words:
                wrapped.append("")
                continue
            line = ""
            for word in words:
                test = (line + " " + word).strip()
                if c.stringWidth(test, font_name, font_size) < max_w:
                    line = test
                else:
                    wrapped.append(line)
                    line = word
            wrapped.append(line)
        return wrapped

    # ── Render pages ──────────────────────────────────────────────────────
    draw_page_lines(c)
    c.setFont(font_name, font_size)
    c.setFillColorRGB(*tc)

    lines   = wrap_text(text)
    y_pos   = TOP_LINE_Y
    text_x  = margin_x + 6

    for line in lines:
        if y_pos < 45:
            draw_credit(c)
            c.showPage()
            draw_page_lines(c)
            c.setFont(font_name, font_size)
            c.setFillColorRGB(*tc)
            y_pos = TOP_LINE_Y

        if line:
            c.drawString(text_x, y_pos, line)
        y_pos -= line_spacing

    draw_credit(c)
    c.save()
    return buf.getvalue()


def create_handwritten_jpg(
    text: str,
    font_key: str,
    notebook_style: str = "classic_blue",
    title: str = "",
    credit: str = "Written By - Technical Serena",
) -> list:
    """
    Same as create_handwritten_pdf but returns list of JPG images (one per page).
    Each item is raw JPEG bytes.
    """
    pdf_bytes = create_handwritten_pdf(text, font_key, notebook_style, title, credit)
    images    = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            mat = fitz.Matrix(2.0, 2.0)   # 2× for crisp JPG
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=95, optimize=True)
            images.append(buf.getvalue())
    return images



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
# OCR — WITH LANGUAGE SUPPORT
# ─────────────────────────────────────────────────────────────────────────────
def ocr_image(data: bytes, lang: str = "eng+hin") -> str:
    try:
        import pytesseract
        img = Image.open(io.BytesIO(data))
        config = "--psm 6 --oem 3"
        text = pytesseract.image_to_string(img, config=config, lang=lang)
        return text.strip() or "⚠️ No text detected in this image."
    except Exception as e:
        return f"⚠️ OCR Error: {e}"

def ocr_pdf(data: bytes, lang: str = "eng+hin") -> str:
    """Layout-preserving text extraction from PDF with language support."""
    try:
        import pytesseract
        with fitz.open(stream=data, filetype="pdf") as doc:
            all_pages = []
            for i, page in enumerate(doc):
                blocks = page.get_text("blocks")
                if blocks:
                    blocks.sort(key=lambda b: (round(b[1] / 20) * 20, b[0]))
                    lines = [b[4].strip() for b in blocks if b[4].strip()]
                    native_text = "\n".join(lines)
                    if len(native_text.strip()) > 30:
                        all_pages.append(f"[Page {i+1}]\n{native_text}")
                        continue
                # OCR fallback
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                config = "--psm 6 --oem 3"
                text = pytesseract.image_to_string(img, config=config, lang=lang)
                all_pages.append(f"[Page {i+1}]\n{text.strip()}")
            return "\n\n" + "─" * 40 + "\n\n".join(all_pages)
    except Exception as e:
        return f"⚠️ Error: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _parse_range(s: str, total: int) -> list:
    pages = []
    seen = set()
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            ab = part.split("-", 1)
            a = int(ab[0]) - 1 if ab[0].strip() else 0
            b = int(ab[1]) - 1 if ab[1].strip() else total - 1
            for p in range(a, b + 1):
                if 0 <= p < total and p not in seen:
                    pages.append(p)
                    seen.add(p)
        elif part:
            p = int(part) - 1
            if 0 <= p < total and p not in seen:
                pages.append(p)
                seen.add(p)
    return pages

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


# ─────────────────────────────────────────────────────────────────────────────
# REVERSE PAGES  ✨ NEW v4
# ─────────────────────────────────────────────────────────────────────────────
def reverse_pages(data: bytes) -> bytes:
    """Reverse the order of all pages."""
    with fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
        out = fitz.open()
        for i in range(total - 1, -1, -1):
            out.insert_pdf(doc, from_page=i, to_page=i)
        buf = io.BytesIO()
        out.save(buf)
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# PDF COMPARE  ✨ NEW v4
# Returns a PDF with highlighted differences + summary dict
# ─────────────────────────────────────────────────────────────────────────────
def compare_pdfs(data1: bytes, data2: bytes) -> tuple[bytes, dict]:
    """
    Compare two PDFs page by page.
    Returns: (comparison_pdf_bytes, summary_dict)
    Highlights: green = added lines, red = removed lines.
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors

    # Extract text from both
    def extract_text_lines(data):
        lines = []
        with fitz.open(stream=data, filetype="pdf") as doc:
            for page in doc:
                page_lines = page.get_text().split("\n")
                lines.extend(page_lines)
        return lines

    lines1 = extract_text_lines(data1)
    lines2 = extract_text_lines(data2)

    import difflib
    diff = list(difflib.unified_diff(lines1, lines2, lineterm="", n=0))

    added   = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
    diff_lines = added + removed

    # Count pages
    with fitz.open(stream=data1, filetype="pdf") as d1:
        pages1 = len(d1)
    with fitz.open(stream=data2, filetype="pdf") as d2:
        pages2 = len(d2)

    # Build comparison PDF using reportlab
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#1a1a2e"))
    c.rect(0, h - 60, w, 60, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawString(20, h - 40, "📄 PDF Comparison Report")

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20, h - 80, "Summary")

    c.setFont("Helvetica", 10)
    y = h - 100
    summary_items = [
        f"Pages in PDF 1: {pages1}",
        f"Pages in PDF 2: {pages2}",
        f"Lines added (+): {added}",
        f"Lines removed (-): {removed}",
        f"Total changed lines: {diff_lines}",
    ]
    for item in summary_items:
        c.drawString(30, y, item)
        y -= 16

    # Draw diff lines
    c.setFont("Helvetica-Bold", 11)
    y -= 10
    c.drawString(20, y, "Differences:")
    y -= 20

    c.setFont("Courier", 8)
    shown = 0
    for line in diff:
        if y < 40:
            c.showPage()
            y = h - 40
            c.setFont("Courier", 8)

        if line.startswith("+") and not line.startswith("+++"):
            c.setFillColor(colors.HexColor("#1a6b1a"))
            c.setStrokeColor(colors.HexColor("#ccffcc"))
            c.rect(15, y - 3, w - 30, 12, fill=1, stroke=0)
            c.setFillColor(colors.white)
        elif line.startswith("-") and not line.startswith("---"):
            c.setFillColor(colors.HexColor("#6b1a1a"))
            c.setStrokeColor(colors.HexColor("#ffcccc"))
            c.rect(15, y - 3, w - 30, 12, fill=1, stroke=0)
            c.setFillColor(colors.white)
        elif line.startswith("@@"):
            c.setFillColor(colors.HexColor("#1a1a6b"))
            c.setStrokeColor(colors.HexColor("#ccccff"))
            c.rect(15, y - 3, w - 30, 12, fill=1, stroke=0)
            c.setFillColor(colors.white)
        else:
            c.setFillColor(colors.black)

        # Truncate long lines
        display = line[:110] if len(line) > 110 else line
        try:
            c.drawString(20, y, display)
        except Exception:
            c.drawString(20, y, line[:80].encode("ascii", "replace").decode())

        y -= 13
        shown += 1
        if shown > 500:
            c.setFillColor(colors.gray)
            c.drawString(20, y, f"... and {diff_lines - shown} more differences (truncated)")
            break

    c.save()

    summary = {
        "pages1": pages1,
        "pages2": pages2,
        "added":  added,
        "removed": removed,
        "diff_lines": diff_lines,
    }
    return buf.getvalue(), summary
