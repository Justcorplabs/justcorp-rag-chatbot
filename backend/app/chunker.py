from typing import List, Dict


def split_text_into_chunks(
    text: str,
    document_id: str,
    filename: str,
    chunk_size: int = 900,
    overlap: int = 150,
) -> List[Dict]:
    """
    Split extracted text into overlapping chunks.

    Why chunking matters:
    - Large documents are too big to send to an LLM directly.
    - RAG works by searching smaller chunks.
    - Overlap helps preserve context between chunks.

    Args:
        text: Cleaned document text.
        document_id: Unique ID for the uploaded document.
        filename: Original uploaded filename.
        chunk_size: Approximate number of characters per chunk.
        overlap: Number of characters repeated between chunks.

    Returns:
        A list of chunk dictionaries with text and metadata.
    """

    if not text or not text.strip():
        return []

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks = []
    start = 0
    chunk_number = 1
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(
                {
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_number": chunk_number,
                    "text": chunk_text,
                }
            )
            chunk_number += 1

        start = end - overlap

    return chunks