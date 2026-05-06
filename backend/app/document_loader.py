from pathlib import Path
import fitz


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using PyMuPDF.

    Args:
        file_path: Path to the uploaded PDF file.

    Returns:
        Extracted text as a single string.
    """

    pdf_path = Path(file_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    text_parts = []

    with fitz.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            page_text = page.get_text("text")

            if page_text:
                text_parts.append(f"\n--- Page {page_number} ---\n")
                text_parts.append(page_text)

    extracted_text = "\n".join(text_parts).strip()

    return extracted_text


def clean_extracted_text(text: str) -> str:
    """
    Basic text cleaning for extracted PDF text.
    Keeps the cleaning simple for version 1.
    """

    if not text:
        return ""

    lines = text.splitlines()

    cleaned_lines = []

    for line in lines:
        clean_line = line.strip()

        if clean_line:
            cleaned_lines.append(clean_line)

    return "\n".join(cleaned_lines)