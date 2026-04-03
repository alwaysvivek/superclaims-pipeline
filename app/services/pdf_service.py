import fitz
import pytesseract
from PIL import Image
import io
from typing import List, Dict, Any
from app.models.state import PageModel

class PDFProcessor:
    @staticmethod
    def process_pdf(file_bytes: bytes) -> List[PageModel]:
        """Converts PDF bytes to a list of OCR extracted texts."""
        pages = []
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            extracted_text = pytesseract.image_to_string(img)
            pages.append({
                "page_number": page_num + 1,
                "extracted_text": extracted_text,
                "page_type": None
            })
        return pages
