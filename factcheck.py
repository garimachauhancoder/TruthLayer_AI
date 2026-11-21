"""Core logic: read PDF -> extract claims -> verify each claim with live web search via Gemini."""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pypdf import PdfReader

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_CLAIMS = 15
MAX_TEXT_CHARS = 30_000

EXTRACT_PROMPT = """You are a fact-checking assistant. From the document below, extract up to {n}
specific, checkable claims: statistics, percentages, dates, rankings, financial figures,
and technical figures. Skip opinions and vague statements.

Return ONLY a JSON list, no other text. Each item:
{{"claim": "<the claim, with enough context to be checked on its own>",
  "category": "stat | date | financial | technical | other"}}

DOCUMENT:
{text}"""

VERIFY_PROMPT = """Today's date is {today}. Fact-check this claim using Google web search.

CLAIM: {claim}

Search the live web (prefer official, primary or reputable sources) and decide:
- "Verified": the claim matches current, reliable data.
- "Inaccurate": the claim is partly right but outdated or the numbers are wrong.
- "False": no evidence supports it, or reliable sources clearly contradict it.

Return ONLY a JSON object, no other text:
{{"verdict": "Verified | Inaccurate | False",
  "correct_fact": "<the correct, current fact with numbers and year. Say 'N/A' if verified>",
  "explanation": "<1-2 sentences on why>",
  "sources": ["<url>", "<url>"]}}"""


def read_pdf(file) -> str:
    """Return all text from an uploaded PDF."""
    reader = PdfReader(file)
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _parse_json(text: str):
    """Pull the first JSON object/list out of a model reply."""
    # First attempt: if there's a markdown code block ```json ... ```
    code_block = re.search(r"```(?:json)?\s*([\[{].*?[\]}])\s*```", text, re.S)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except Exception:
            pass

    # Second attempt: find outermost [ ... ] or { ... }
    match = re.search(r"(\[.*\]|\{.*\})", text, re.S)
    if not match:
        raise ValueError(f"No JSON found in model reply: {text[:200]}")
    return json.loads(match.group(1))


def extract_claims(client: genai.Client, text: str) -> list[dict]:
    response = client.models.generate_content(
        model=MODEL,
        contents=EXTRACT_PROMPT.format(n=MAX_CLAIMS, text=text[:MAX_TEXT_CHARS]),
    )
    raw = _parse_json(response.text or "[]")
    if isinstance(raw, dict) and "claims" in raw:
        raw = raw["claims"]
    if not isinstance(raw, list):
        raise ValueError("Model did not return a list of claims")
    return raw[:MAX_CLAIMS]


def verify_claim(client: genai.Client, claim: dict) -> dict:
    """Verify one claim with Gemini's built-in Google Search grounding."""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=VERIFY_PROMPT.format(today=date.today().isoformat(), claim=claim["claim"]),
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )

        result = _parse_json(response.text or "{}")
        if result.get("verdict") not in ("Verified", "Inaccurate", "False"):
            result["verdict"] = "False"

        # Collect sources from JSON and grounding metadata
        sources = []
        if isinstance(result.get("sources"), list):
            sources.extend([s for s in result["sources"] if isinstance(s, str) and s.startswith("http")])

        # Grounding chunks from Google Search tool
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            grounding_meta = getattr(candidate, "grounding_metadata", None)
            if grounding_meta:
                chunks = getattr(grounding_meta, "grounding_chunks", None) or []
                for chunk in chunks:
                    web = getattr(chunk, "web", None)
                    uri = getattr(web, "uri", None) if web else None
                    if uri and uri not in sources:
                        sources.append(uri)

        result["sources"] = sources
    except Exception as e:  # keep going so one failure doesn't kill the report
        result = {
            "verdict": "Error",
            "correct_fact": "N/A",
            "explanation": f"Could not verify this claim: {e}",
            "sources": [],
        }
    return {**claim, **result}


def check_document(client: genai.Client, claims: list[dict]) -> list[dict]:
    """Verify all claims in parallel (keeps the app fast)."""
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(lambda c: verify_claim(client, c), claims))
