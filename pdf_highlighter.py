"""Create annotated PDF copies for claims classified as problematic."""

import re
import unicodedata

import pymupdf


PROBLEM_STATUSES = {"False", "Inaccurate"}
STATUS_COLORS = {
    "False": (0.92, 0.12, 0.12),
    "Inaccurate": (1.0, 0.68, 0.05),
}


def _tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.findall(r"[^\W_]+(?:['’][^\W_]+)*", normalized, flags=re.UNICODE)


def _find_sentence_rects(page: pymupdf.Page, sentence: str) -> list[pymupdf.Rect]:
    """Locate a sentence by matching its words to the PDF text layer."""
    wanted = _tokens(sentence)
    if not wanted:
        return []

    # Match the same default reading order used by pdf_processor.extract_text_from_pdf.
    words = page.get_text("words")
    page_tokens: list[str] = []
    token_rects: list[pymupdf.Rect] = []
    for word in words:
        for token in _tokens(word[4]):
            page_tokens.append(token)
            token_rects.append(pymupdf.Rect(word[:4]))

    width = len(wanted)
    for start in range(len(page_tokens) - width + 1):
        if page_tokens[start:start + width] == wanted:
            return token_rects[start:start + width]
    return []


def annotate_problematic_claims(pdf_bytes: bytes, results: list[dict]) -> tuple[bytes, dict]:
    """Highlight False and Inaccurate claim sentences and return PDF bytes plus summary."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    details: list[dict] = []
    unmatched: list[dict] = []
    marked_pages: set[int] = set()

    for claim_number, result in enumerate(results, start=1):
        status = result.get("status")
        if status not in PROBLEM_STATUSES:
            continue

        page_number = result.get("page")
        try:
            page_index = int(page_number) - 1
        except (TypeError, ValueError):
            page_index = -1
        if page_index < 0 or page_index >= len(doc):
            unmatched.append({"claim_number": claim_number, "page": page_number, "reason": "Invalid PDF page number"})
            continue

        original_sentence = result.get("original_sentence") or result.get("claim", "")
        page = doc[page_index]
        rects = _find_sentence_rects(page, original_sentence)
        if not rects:
            unmatched.append({"claim_number": claim_number, "page": page_number, "reason": "Sentence did not match text on this page"})
            continue

        annotation = page.add_highlight_annot(rects)
        annotation.set_colors(stroke=STATUS_COLORS[status])
        annotation.set_opacity(0.35)
        annotation.set_info({
            "title": f"TruthLayer AI — {status}",
            "content": f"Claim #{claim_number} · Page {page_number}\n{result.get('claim', original_sentence)}",
        })
        annotation.update()

        marked_pages.add(page_number)
        details.append({
            "claim_number": claim_number,
            "page": page_number,
            "status": status,
            "claim": result.get("claim", original_sentence),
            "original_sentence": original_sentence,
        })

    output = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return output, {
        "details": details,
        "unmatched": unmatched,
        "pages": sorted(marked_pages),
    }


def render_pdf_page(pdf_bytes: bytes, page_number: int, scale: float = 1.5) -> bytes:
    """Render one one-indexed PDF page as PNG for inline review."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[int(page_number) - 1]
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        return pixmap.tobytes("png")
    finally:
        doc.close()
