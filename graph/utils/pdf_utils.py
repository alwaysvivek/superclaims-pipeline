"""PDF to image conversion utilities."""

import base64
from contextlib import contextmanager
import pymupdf


@contextmanager
def _open_pdf(pdf_filepath: str):
    """Context manager to safely open and close a PyMuPDF document."""
    doc = pymupdf.open(pdf_filepath)
    try:
        yield doc
    finally:
        doc.close()


def _render_page(page, matrix) -> bytes:
    """Render a single page to PNG bytes, downscaling if over 4 MB (Groq limit)."""
    pix = page.get_pixmap(matrix=matrix)
    img_bytes = pix.tobytes("png")

    if len(img_bytes) > 4 * 1024 * 1024:
        lower_matrix = pymupdf.Matrix(150 / 72, 150 / 72)
        pix = page.get_pixmap(matrix=lower_matrix)
        img_bytes = pix.tobytes("png")

    return img_bytes


def get_total_pages(pdf_filepath: str) -> int:
    """Get the total number of pages in the PDF without loading images."""
    with _open_pdf(pdf_filepath) as doc:
        return len(doc)


def extract_thumbnails(pdf_filepath: str) -> list[str]:
    """Extract all pages as low-res thumbnails for UI."""
    thumb_matrix = pymupdf.Matrix(30 / 72, 30 / 72)

    with _open_pdf(pdf_filepath) as doc:
        return [
            base64.b64encode(doc.load_page(i).get_pixmap(matrix=thumb_matrix).tobytes("png")).decode("utf-8")
            for i in range(len(doc))
        ]


def extract_specific_pages(pdf_filepath: str, page_indices: list[int], dpi: int = 200) -> list[str]:
    """Extract specific pages as high-res base64 images exactly when needed."""
    matrix = pymupdf.Matrix(dpi / 72, dpi / 72)

    with _open_pdf(pdf_filepath) as doc:
        images = []
        for idx in page_indices:
            if 0 <= idx < len(doc):
                img_bytes = _render_page(doc.load_page(idx), matrix)
                images.append(base64.b64encode(img_bytes).decode("utf-8"))
        return images

