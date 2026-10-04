import os, io
import fitz
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract

def extract_docx(path):
    doc=Document(path); parts=[]
    for p in doc.paragraphs:
        if p.text.strip(): parts.append(p.text.strip())
    for table in doc.tables:
        for row in table.rows:
            cells=[c.text.strip() for c in row.cells]
            if any(cells): parts.append(" | ".join(cells))
    return "\n".join(parts)

def ocr_image(image): return pytesseract.image_to_string(image, lang="eng")

def extract_pdf(path):
    parts=[]
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t=page.extract_text(x_tolerance=2,y_tolerance=3) or ""
                if t.strip(): parts.append(t)
    except Exception: pass
    text="\n".join(parts).strip()
    if len(text)<150:
        out=[]; doc=fitz.open(path)
        for page in doc:
            pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
            img=Image.open(io.BytesIO(pix.tobytes("png")))
            out.append(ocr_image(img))
        doc.close(); return "\n".join(out).strip(),True
    return text,False

def extract_text(path):
    ext=os.path.splitext(path)[1].lower()
    if ext==".pdf": return extract_pdf(path)
    if ext==".docx": return extract_docx(path),False
    if ext in {".jpg",".jpeg",".png",".webp"}: return ocr_image(Image.open(path)),True
    if ext==".doc": raise ValueError("Old .doc files are not supported directly. Convert .doc to .docx or PDF.")
    raise ValueError("Unsupported file type.")
