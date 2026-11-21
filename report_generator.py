"""Generate a compact, paginated PDF fact-check report."""

import os
import textwrap
import unicodedata

import pymupdf


def _plain_text(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join(text.encode("ascii", "replace").decode("ascii").split())


def generate_factcheck_pdf(results: list[dict], document_name: str) -> bytes:
    """Build a PDF report with claim verdicts and the retrieved evidence."""
    doc = pymupdf.open()
    page = None
    y = 0
    margin = 48
    max_y = 792
    line_height = 13

    def new_page():
        nonlocal page, y
        page = doc.new_page(width=595, height=842)
        y = 48
        page.insert_text((margin, y), "TRUTHLAYER AI | FACT-CHECK REPORT", fontsize=16, fontname="hebo", color=(0.08, 0.16, 0.28))
        y += 24
        for line in textwrap.wrap(_plain_text(document_name), width=86) or ["Document"]:
            page.insert_text((margin, y), line, fontsize=10, fontname="helv", color=(0.25, 0.3, 0.38))
            y += line_height
        y += 10

    def write(text, *, size=10, bold=False, color=(0.12, 0.16, 0.22), indent=0):
        nonlocal page, y
        cleaned = _plain_text(text)
        lines = textwrap.wrap(cleaned, width=max(24, 94 - indent), break_long_words=True, break_on_hyphens=False) or [""]
        font = "hebo" if bold else "helv"
        for line in lines:
            if page is None or y > max_y:
                new_page()
            page.insert_text((margin + indent, y), line, fontsize=size, fontname=font, color=color)
            y += max(line_height, size + 3)

    new_page()
    for idx, item in enumerate(results, start=1):
        if y > max_y - 120:
            new_page()
        status = _plain_text(item.get("status", "Unknown"))
        status_color = {
            "False": (0.72, 0.12, 0.12),
            "Inaccurate": (0.66, 0.39, 0.02),
            "Verified": (0.08, 0.43, 0.25),
        }.get(status, (0.3, 0.35, 0.4))
        write(f"Claim {idx} | {status} | PDF page {item.get('page', 'unknown')}", size=13, bold=True, color=status_color)
        write("Original sentence:", bold=True)
        write(item.get("original_sentence") or item.get("claim", ""), indent=12)
        write("Claim checked:", bold=True)
        write(item.get("claim", ""), indent=12)
        correction = item.get("correct_fact")
        if correction and correction != "N/A":
            write("Corrected fact:", bold=True)
            write(correction, indent=12)
        write("Verification:", bold=True)
        write(item.get("explanation") or "No explanation provided.", indent=12)
        if item.get("search_warnings"):
            write("Search warnings:", bold=True)
            write("; ".join(item["search_warnings"]), indent=12)

        details_by_url = {
            source.get("url"): source
            for source in item.get("source_details", [])
            if source.get("url")
        }
        source_urls = item.get("sources", [])
        if not source_urls and details_by_url:
            source_urls = list(details_by_url)
        write("Evidence and sources:", bold=True)
        if source_urls:
            for source_idx, url in enumerate(source_urls, start=1):
                detail = details_by_url.get(url, {})
                title = detail.get("title") or url
                published = detail.get("published_date") or "Publication date not provided"
                angles = " + ".join(detail.get("evidence_angles", []))
                prefix = f"{source_idx}. {title} | {published}"
                if angles:
                    prefix += f" | {angles} search"
                write(prefix, indent=12)
                write(f"URL: {url}", indent=24)
                excerpt = detail.get("excerpt")
                if excerpt:
                    write(f"Evidence excerpt: {excerpt}", indent=24)
        else:
            write("No source URLs were returned.", indent=12)
        y += 8

    pdf_bytes = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return pdf_bytes


def report_filename(document_name: str, extension: str) -> str:
    """Return a safe report filename based on the source document."""
    stem = os.path.splitext(os.path.basename(document_name or "document"))[0]
    safe_stem = "".join(char if char.isalnum() or char in "-_" else "_" for char in stem).strip("_") or "document"
    return f"truthlayer_report_{safe_stem}.{extension.lstrip('.')}"
