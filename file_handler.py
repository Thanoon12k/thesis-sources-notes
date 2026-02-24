"""
file_handler.py — PDF/DOCX file handling utilities.
"""

import os
import sys
import subprocess


def open_file_external(path):
    """Open a file with the system's default application."""
    if not path or not os.path.isfile(path):
        return False
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False


def preview_pdf_page(path, page_number=0, zoom=2.0):
    """
    Render a single PDF page as a PIL Image.
    Returns a PIL.Image or None on failure.
    """
    try:
        import fitz  # PyMuPDF
        from PIL import Image
        import io

        doc = fitz.open(path)
        if page_number >= len(doc):
            page_number = len(doc) - 1
        page = doc.load_page(page_number)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        doc.close()
        return Image.open(io.BytesIO(img_data))
    except Exception:
        return None


def get_pdf_page_count(path):
    """Return the number of pages in a PDF file."""
    try:
        import fitz
        doc = fitz.open(path)
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 0


def extract_text_from_docx(path):
    """Extract all text from a .docx file."""
    try:
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def get_file_type(path):
    """Determine file type from extension."""
    if not path:
        return None
    ext = os.path.splitext(path)[1].lower()
    type_map = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "doc",
        ".txt": "txt",
        ".rtf": "rtf",
    }
    return type_map.get(ext, "other")


def get_supported_file_types():
    """Return file dialog filter tuples for supported document types."""
    return [
        ("All Supported", "*.pdf;*.docx;*.doc;*.txt"),
        ("PDF Files", "*.pdf"),
        ("Word Documents", "*.docx;*.doc"),
        ("Text Files", "*.txt"),
        ("All Files", "*.*"),
    ]


def get_supported_image_types():
    """Return file dialog filter tuples for supported image types."""
    return [
        ("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp"),
        ("PNG", "*.png"),
        ("JPEG", "*.jpg;*.jpeg"),
        ("All Files", "*.*"),
    ]
