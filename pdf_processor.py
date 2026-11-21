"""Module for extracting text from PDF files using PyMuPDF."""

import pymupdf


class PDFProcessingError(Exception):
    """Custom exception raised when PDF text extraction or parsing fails."""
    pass


def extract_text_from_pdf(pdf_file) -> list[dict]:
    """
    Extracts text page-by-page from an uploaded PDF file or binary stream using PyMuPDF.

    Args:
        pdf_file: An uploaded file-like object (e.g. Streamlit's UploadedFile) or bytes.

    Returns:
        List of dictionaries with 'page_number' (1-indexed) and 'text' content.

    Raises:
        PDFProcessingError: If the document is unreadable, corrupted, or has no extractable text.
    """
    if pdf_file is None:
        raise PDFProcessingError("No PDF file was provided.")

    try:
        # Retrieve bytes from file-like object or binary data
        if hasattr(pdf_file, "getvalue"):
            file_bytes = pdf_file.getvalue()
        elif hasattr(pdf_file, "read"):
            file_bytes = pdf_file.read()
        elif isinstance(pdf_file, (bytes, bytearray)):
            file_bytes = pdf_file
        else:
            raise PDFProcessingError("Unsupported PDF file format. Please upload a valid .pdf file.")

        if not file_bytes or len(file_bytes) == 0:
            raise PDFProcessingError("The uploaded PDF file is empty (0 bytes).")

        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except PDFProcessingError:
        raise
    except Exception as exc:
        raise PDFProcessingError(f"Failed to open or parse the PDF document: {exc}")

    if len(doc) == 0:
        raise PDFProcessingError("The PDF document does not contain any pages.")

    pages = []
    total_extracted_characters = 0

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_text = page.get_text().strip()
        pages.append({
            "page_number": page_idx + 1,
            "text": page_text
        })
        total_extracted_characters += len(page_text)

    # Scanned documents / image-only PDFs will yield 0 extracted characters
    if total_extracted_characters == 0:
        raise PDFProcessingError(
            "No extractable text was found in this PDF. It appears to be an image-only scan or empty document."
        )

    return pages


def format_pages_for_llm(pages: list[dict], max_chars: int = 40_000) -> str:
    """
    Formats page-by-page text with explicit page markers for LLM claim extraction.

    Args:
        pages: List of dictionaries with 'page_number' and 'text'.
        max_chars: Maximum character limit to keep model processing fast and cost-effective.

    Returns:
        Formatted string containing text annotated with page headers.
    """
    formatted_chunks = []
    current_length = 0

    for page_info in pages:
        page_text = page_info["text"]
        if not page_text:
            continue

        chunk = f"--- PAGE {page_info['page_number']} ---\n{page_text}\n\n"
        if current_length + len(chunk) > max_chars:
            allowed = max_chars - current_length
            if allowed > 100:
                formatted_chunks.append(chunk[:allowed] + "\n[Content truncated for processing limits]\n")
            break

        formatted_chunks.append(chunk)
        current_length += len(chunk)

    return "".join(formatted_chunks).strip()
