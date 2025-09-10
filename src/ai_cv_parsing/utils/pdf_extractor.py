import fitz
from typing import Union

def extract_text_from_pdf(pdf_source: Union[str, bytes], page_number: int = 0) -> str:
    """
    Extract text from a validated PDF file.
    
    Args:
        pdf_source: Path to the PDF file or PDF content as bytes
        page_number: Page number to extract text from (default: 0 for first page)
    
    Returns:
        Extracted text as string
    """
    doc = fitz.open(stream=pdf_source if isinstance(pdf_source, bytes) else pdf_source)
    page = doc.load_page(page_number)
    text = page.get_text()
    doc.close()
    return text

def extract_text_with_details(pdf_path: str, page_number: int = 0) -> dict:
    """
    Extract text with detailed positioning data from a validated PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        page_number: Page number to extract text from (default: 0 for first page)
    
    Returns:
        Dictionary with detailed text positioning data
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)
    text_dict = page.get_text("dict")
    doc.close()
    return text_dict