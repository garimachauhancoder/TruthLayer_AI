"""Module for verifying claims against Tavily search evidence using the Gemini API."""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from ai_client import generate_content_with_fallback, DEFAULT_MODEL
from web_search import search_web_for_claim

VERIFICATION_SYSTEM_PROMPT = """You are a rigorous, impartial fact-checking judge.
You will evaluate a specific factual claim against live web search results and source URLs collected from the Tavily search engine.

Your objective is to evaluate the claim strictly against the provided search evidence.

Rules for classification:
- "Verified": The available reliable evidence clearly supports the claim.
- "Inaccurate": The claim contains incorrect figures, outdated statistics, or conflicting details.
- "False": The available evidence directly contradicts the claim or demonstrates that it is false.
- "Insufficient Evidence": The search results do not provide enough specific, verifiable facts to definitively prove or disprove the claim. DO NOT label a claim False merely because evidence is missing or inconclusive.

CRITICAL INSTRUCTIONS ON SOURCES:
- Search evidence includes separate supporting and contradicting search angles. Consider both; a search angle alone is not proof.
- Use publication dates when available to judge whether evidence is current. Treat missing dates as unknown; do not invent them.
- Only cite URLs that appear in the provided search evidence.
- NEVER invent, extrapolate, or hallucinate URLs.
- If evidence is insufficient, leave the sources list empty [].

Return ONLY a valid JSON object matching this exact structure:
{
  "status": "Verified | Inaccurate | False | Insufficient Evidence",
  "explanation": "<1-3 clear sentences explaining the rationale based strictly on the search results>",
  "correct_fact": "<If Inaccurate or False, state the accurate, current fact with numbers/dates. If Verified or Insufficient Evidence, state 'N/A'>",
  "sources": ["<exact URL from search evidence>", ...]
}"""


def _parse_verification_json(text: str) -> dict:
    """Extracts and parses the verification JSON object."""
    if not text:
        return {}

    code_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except Exception:
            pass

    obj_match = re.search(r"(\{.*\})", text, re.S)
    if obj_match:
        try:
            return json.loads(obj_match.group(1))
        except Exception:
            pass

    return {}


def verify_single_claim(
    claim_item: dict,
    gemini_api_key: str = "",
    tavily_api_key: str = "",
    model_name: str = DEFAULT_MODEL
) -> dict:
    """
    Performs live web search with Tavily and verifies a single claim with the Gemini API.

    Args:
        claim_item: Dictionary containing 'claim', 'page', and 'category'.
        gemini_api_key: Gemini API key for fallback.
        tavily_api_key: Tavily API key for web search.
        model_name: Model name.

    Returns:
        Dictionary containing claim details, verification status, explanation,
        correct fact, and validated sources.
    """
    claim_text = claim_item["claim"]
    original_sentence = claim_item.get("original_sentence", claim_text)
    page_num = claim_item.get("page", 1)
    category = claim_item.get("category", "factual_statement")

    cleaned_tavily_key = (tavily_api_key or "").strip().strip("'\"")

    # Step 1: Perform live search via Tavily
    search_result = search_web_for_claim(claim_text, tavily_api_key=cleaned_tavily_key)

    # Handle Tavily search failures
    if search_result.error:
        return {
            "claim": claim_text,
            "original_sentence": original_sentence,
            "page": page_num,
            "category": category,
            "status": "Insufficient Evidence",
            "explanation": f"Web search could not be completed: {search_result.error}",
            "correct_fact": "N/A",
            "sources": []
        }

    # Handle empty search results
    if not search_result.results or not search_result.context.strip():
        return {
            "claim": claim_text,
            "original_sentence": original_sentence,
            "page": page_num,
            "category": category,
            "status": "Insufficient Evidence",
            "explanation": "No relevant live web search results were found to verify or disprove this claim.",
            "correct_fact": "N/A",
            "sources": []
        }

    # Step 2: Query the Gemini API
    try:
        today_str = date.today().isoformat()

        user_content = f"""TODAY'S DATE: {today_str}

ORIGINAL CLAIM (From Page {page_num}):
"{claim_text}"

LIVE WEB SEARCH EVIDENCE (From Tavily):
{search_result.context}

SEARCH RESULT METADATA (including publication dates when provided):
{json.dumps(search_result.source_details, ensure_ascii=False, indent=2)}

AVAILABLE SOURCE URLS:
{json.dumps(search_result.sources, indent=2)}

SEARCH WARNINGS:
{json.dumps(search_result.warnings, ensure_ascii=False)}

---
EVALUATE AND RESPOND:
Return ONLY the JSON object with fields "status", "explanation", "correct_fact", and "sources"."""

        response_text, provider_used = generate_content_with_fallback(
            prompt=user_content,
            gemini_api_key=gemini_api_key,
            model_name=model_name,
            temperature=0.1,
            system_instruction=VERIFICATION_SYSTEM_PROMPT
        )

        verdict_data = _parse_verification_json(response_text or "")

        # Normalize status
        raw_status = verdict_data.get("status", "").strip()
        valid_statuses = ["Verified", "Inaccurate", "False", "Insufficient Evidence"]
        if raw_status not in valid_statuses:
            if "verif" in raw_status.lower():
                status = "Verified"
            elif "inaccur" in raw_status.lower():
                status = "Inaccurate"
            elif "false" in raw_status.lower():
                status = "False"
            else:
                status = "Insufficient Evidence"
        else:
            status = raw_status

        explanation = verdict_data.get("explanation", "").strip() or "Evaluated against live web search evidence."
        correct_fact = verdict_data.get("correct_fact", "N/A").strip()

        # Strict validation of sources: only retain URLs actually returned by Tavily
        raw_sources = verdict_data.get("sources", [])
        validated_sources = []
        if isinstance(raw_sources, list):
            for s in raw_sources:
                if isinstance(s, str) and s in search_result.sources and s not in validated_sources:
                    validated_sources.append(s)

        # Fall back to top search source if verified or contradicted but model missed citing it
        if not validated_sources and status in ["Verified", "Inaccurate", "False"] and search_result.sources:
            validated_sources = search_result.sources[:2]

        return {
            "claim": claim_text,
            "original_sentence": original_sentence,
            "page": page_num,
            "category": category,
            "status": status,
            "explanation": explanation,
            "correct_fact": correct_fact,
            "sources": validated_sources,
            "search_warnings": search_result.warnings,
            "source_details": [
                detail for detail in search_result.source_details
                if detail.get("url") in validated_sources
            ]
        }

    except Exception as exc:
        return {
            "claim": claim_text,
            "original_sentence": original_sentence,
            "page": page_num,
            "category": category,
            "status": "Insufficient Evidence",
            "explanation": f"Verification error encountered during analysis: {exc}",
            "correct_fact": "N/A",
            "sources": []
        }


def verify_claims_batch(
    claims: list[dict],
    gemini_api_key: str = "",
    tavily_api_key: str = "",
    max_workers: int = 3,
    model_name: str = DEFAULT_MODEL
) -> list[dict]:
    """
    Verifies a list of claims in parallel using ThreadPoolExecutor.

    Args:
        claims: List of claim dictionaries.
        gemini_api_key: Gemini API key for fallback.
        tavily_api_key: Tavily API key.
        max_workers: Maximum number of concurrent worker threads (default: 3).
        model_name: Model name.

    Returns:
        List of verified claim result dictionaries.
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(
            executor.map(
                lambda c: verify_single_claim(
                    c,
                    gemini_api_key=gemini_api_key,
                    tavily_api_key=tavily_api_key,
                    model_name=model_name
                ),
                claims
            )
        )
    return results
