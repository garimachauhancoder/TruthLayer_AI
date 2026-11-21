"""Module for extracting checkable factual claims using the Gemini API."""

import json
import os
import re
from ai_client import generate_content_with_fallback, DEFAULT_MODEL
from pdf_processor import format_pages_for_llm

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
4. Keep the claim concise, self-contained, and faithful to the document context.

Return ONLY a valid JSON list of objects matching this exact structure:
[
  {
    "claim": "<concise, self-contained factual claim>",
    "category": "statistic | date | financial | technical | factual_statement",
    "page": <integer page number where this claim was found>
  }
]"""


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
    document_text = format_pages_for_llm(pages)
    if not document_text.strip():
        raise ValueError("No text available to extract claims from.")

    user_prompt = f"""DOCUMENT TO ANALYZE:
{document_text}

---
INSTRUCTIONS:
From the document above, extract up to {max_claims} of the most prominent, specific checkable factual claims.
Remember to return ONLY the valid JSON list."""

    response_text, provider_used = generate_content_with_fallback(
        prompt=user_prompt,
        gemini_api_key=gemini_api_key,
        model_name=model_name,
        temperature=0.2,
        system_instruction=EXTRACTION_SYSTEM_PROMPT
    )

    raw_claims = _parse_json_list(response_text or "")

    # Validate and clean up extracted claims
    sanitized_claims = []
    for item in raw_claims:
        if isinstance(item, dict) and "claim" in item and item["claim"].strip():
            page_val = item.get("page", 1)
            try:
                page_num = int(page_val)
            except (ValueError, TypeError):
                page_num = 1

            sanitized_claims.append({
                "claim": item["claim"].strip(),
                "category": str(item.get("category", "factual_statement")),
                "page": page_num
            })

    return sanitized_claims[:max_claims]
