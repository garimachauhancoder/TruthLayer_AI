"""Module for extracting checkable factual claims using the Gemini API."""

import json
import os
import re
import unicodedata
from ai_client import generate_content_with_fallback, DEFAULT_MODEL

EXTRACTION_SYSTEM_PROMPT = """You are an expert fact-checking analyst.
Your task is to identify and extract specific, checkable factual claims from the document provided.

Rules:
1. Focus strictly on:
   - Numerical statistics and percentages (e.g. "Global sales increased by 24%")
   - Dates, years, and historical timelines (e.g. "Founded in March 2012")
   - Financial figures, revenue, valuations, and market data
   - Technical specifications, scientific measurements, and scientific assertions
   - Objective factual statements that can be verified against live web data
2. Skip subjective opinions, value judgments, vague assertions, and rhetorical questions.
3. For each claim, you MUST accurately identify the original PAGE NUMBER where it appears based on the '--- PAGE X ---' headers.
4. For every claim, copy the complete original sentence verbatim into "original_sentence". Do not paraphrase, shorten, or correct this field.
5. Keep "claim" concise, self-contained, and faithful to the document context. It may be normalized for checking; "original_sentence" must remain exact.

Return ONLY a valid JSON list of objects matching this exact structure:
[
  {
    "claim": "<concise, self-contained factual claim>",
    "original_sentence": "<exact sentence copied from the document>",
    "category": "statistic | date | financial | technical | factual_statement",
    "page": <integer page number where this claim was found>
  }
]"""

MAX_CHUNK_CHARS = 30_000


def _normalized_text(text: str) -> str:
    """Normalize whitespace and Unicode for matching model quotations to PDF text."""
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _page_chunks(pages: list[dict], max_chars: int = MAX_CHUNK_CHARS) -> list[list[dict]]:
    """Split all page text into bounded chunks while retaining its original page number."""
    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_chars = 0
    for page in pages:
        page_number = page["page_number"]
        text = page["text"]
        if not text.strip():
            continue
        # Split oversized pages too, so no page is silently cut off.
        for start in range(0, len(text), max_chars):
            part = text[start:start + max_chars]
            piece = {"page_number": page_number, "text": part}
            piece_size = len(part) + 32
            if current and current_chars + piece_size > max_chars:
                chunks.append(current)
                current, current_chars = [], 0
            current.append(piece)
            current_chars += piece_size
    if current:
        chunks.append(current)
    return chunks


def _locate_original_sentence(sentence: str, reported_page: int, pages_by_number: dict[int, str]) -> int | None:
    """Return the page containing the verbatim sentence, correcting bad model page labels."""
    normalized_quote = _normalized_text(sentence)
    if not normalized_quote:
        return None
    if reported_page in pages_by_number and normalized_quote in _normalized_text(pages_by_number[reported_page]):
        return reported_page
    matches = [
        number for number, text in pages_by_number.items()
        if normalized_quote in _normalized_text(text)
    ]
    return matches[0] if len(matches) == 1 else None


def _parse_json_list(text: str) -> list[dict]:
    """Safely extracts and parses a JSON list from a model output string."""
    if not text:
        return []

    # 1. Match code blocks ```json ... ```
    code_match = re.search(r"```(?:json)?\s*([\[{].*?[\]}])\s*```", text, re.S)
    if code_match:
        try:
            parsed = json.loads(code_match.group(1))
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                for key in ["claims", "data", "results", "items"]:
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
        except Exception:
            pass

    # 2. Match standard array [...]
    list_match = re.search(r"(\[.*\])", text, re.S)
    if list_match:
        try:
            parsed = json.loads(list_match.group(1))
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    # 3. Match wrapped object {...}
    obj_match = re.search(r"(\{.*\})", text, re.S)
    if obj_match:
        try:
            parsed = json.loads(obj_match.group(1))
            if isinstance(parsed, dict):
                for key in ["claims", "data", "results", "items"]:
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
        except Exception:
            pass

    return []


def extract_claims(
    pages: list[dict],
    gemini_api_key: str = "",
    max_claims: int = 10,
    model_name: str = DEFAULT_MODEL
) -> list[dict]:
    """
    Extracts verifiable claims along with their source page numbers using the Gemini API.

    Args:
        pages: List of dictionaries with 'page_number' and 'text'.
        gemini_api_key: Gemini API key (used as fallback).
        max_claims: Maximum number of claims to extract (default: 10).
        model_name: AI model name.

    Returns:
        List of claim dicts: [{"claim": "...", "category": "...", "page": 1}, ...]
    """
    pages_by_number = {int(page["page_number"]): page["text"] for page in pages}
    chunks = _page_chunks(pages)
    if not chunks:
        raise ValueError("No text available to extract claims from.")

    sanitized_claims = []
    seen_sentences = set()
    for chunk in chunks:
        if len(sanitized_claims) >= max_claims:
            break
        document_text = "\n\n".join(
            f"--- PAGE {piece['page_number']} ---\n{piece['text']}" for piece in chunk
        )
        remaining = max_claims - len(sanitized_claims)
        user_prompt = f"""DOCUMENT TO ANALYZE:
{document_text}

---
INSTRUCTIONS:
From this section, extract up to {remaining} specific, checkable factual claims.
For each one, copy its complete original sentence exactly into "original_sentence" and report its page.
Remember to return ONLY the valid JSON list."""
        response_text, _provider_used = generate_content_with_fallback(
            prompt=user_prompt,
            gemini_api_key=gemini_api_key,
            model_name=model_name,
            temperature=0.2,
            system_instruction=EXTRACTION_SYSTEM_PROMPT
        )

        for item in _parse_json_list(response_text or ""):
            if not isinstance(item, dict):
                continue
            claim = item.get("claim")
            original_sentence = item.get("original_sentence") or item.get("source_sentence")
            if not isinstance(claim, str) or not claim.strip() or not isinstance(original_sentence, str):
                continue
            original_sentence = original_sentence.strip()
            try:
                reported_page = int(item.get("page"))
            except (ValueError, TypeError):
                reported_page = -1
            page_num = _locate_original_sentence(original_sentence, reported_page, pages_by_number)
            if page_num is None:
                continue
            sentence_key = _normalized_text(original_sentence)
            if sentence_key in seen_sentences:
                continue
            seen_sentences.add(sentence_key)
            sanitized_claims.append({
                "claim": claim.strip(),
                "original_sentence": original_sentence,
                "category": str(item.get("category", "factual_statement")),
                "page": page_num
            })
            if len(sanitized_claims) >= max_claims:
                break

    return sanitized_claims
