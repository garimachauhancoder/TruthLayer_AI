"""Multi-provider AI client supporting Gemini Developer API and Vertex AI."""

import json
import logging
import os
from google import genai
from google.genai import types
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def get_vertex_client() -> genai.Client | None:
    """Creates a Vertex AI client using service account credentials."""
    # 1. Check for local credentials file
    for creds_file in ["vertex_creds.json", "vertex_credentials.json", "service_account.json"]:
        if os.path.exists(creds_file):
            try:
                with open(creds_file, "r", encoding="utf-8") as f:
                    creds_data = json.load(f)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_data,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                return genai.Client(
                    vertexai=True,
                    project=creds_data.get("project_id", "ml-odio"),
                    location=os.getenv("VERTEX_LOCATION", "us-central1"),
                    credentials=credentials,
                )
            except Exception as exc:
                logger.warning(f"Could not load Vertex AI credentials from {creds_file}: {exc}")

    # 2. Check GOOGLE_APPLICATION_CREDENTIALS environment variable
    app_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if app_creds and os.path.exists(app_creds):
        try:
            with open(app_creds, "r", encoding="utf-8") as f:
                creds_data = json.load(f)
            credentials = service_account.Credentials.from_service_account_info(
                creds_data,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            return genai.Client(
                vertexai=True,
                project=creds_data.get("project_id", "ml-odio"),
                location=os.getenv("VERTEX_LOCATION", "us-central1"),
                credentials=credentials,
            )
        except Exception as exc:
            logger.warning(f"Could not initialize Vertex AI from GOOGLE_APPLICATION_CREDENTIALS: {exc}")

    return None


def get_gemini_api_client(gemini_api_key: str = "") -> genai.Client | None:
    """Creates a Gemini Developer API client using the provided or environment key with v1beta."""
    cleaned_key = (gemini_api_key or "").strip().strip("'\"")
    if not cleaned_key:
        cleaned_key = (os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")).strip().strip("'\"")

    if cleaned_key:
        try:
            return genai.Client(
                api_key=cleaned_key,
                http_options=types.HttpOptions(api_version="v1beta"),
            )
        except Exception as exc:
            logger.warning(f"Could not initialize Gemini API client: {exc}")
            return None
    return None


def generate_content_with_fallback(
    prompt: str,
    gemini_api_key: str = "",
    model_name: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    system_instruction: str = ""
) -> tuple[str, str]:
    """
    Uses the Gemini Developer API when a key is configured, then tries Vertex AI.
    Supports Developer/System instructions seamlessly on both engines.

    Returns:
        tuple (response_text, provider_name)
    """
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction if system_instruction else None
    )

    cleaned_key = (gemini_api_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")).strip().strip("'\"")

    # Prefer the configured Gemini key; local Vertex credentials may belong to
    # another project and should not silently take precedence.
    gemini_client = get_gemini_api_client(cleaned_key)
    gemini_error = None
    if gemini_client:
        try:
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            return response.text or "", "Gemini API"
        except Exception as exc:
            gemini_error = exc
            logger.warning(f"Gemini API request failed, trying Vertex AI: {exc}")

    vertex_client = get_vertex_client()
    if vertex_client:
        try:
            response = vertex_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            return response.text or "", "Vertex AI"
        except Exception as vertex_err:
            logger.error(f"Vertex AI request also failed: {vertex_err}")
            if gemini_error:
                raise RuntimeError(
                    f"AI generation failed on Gemini API and Vertex AI. Gemini: {gemini_error}; Vertex: {vertex_err}"
                ) from vertex_err
            raise RuntimeError(f"AI generation failed on Vertex AI: {vertex_err}") from vertex_err

    if gemini_error:
        raise RuntimeError(f"Gemini API request failed: {gemini_error}") from gemini_error

    raise RuntimeError("No valid AI credentials found. Please provide Vertex credentials or GEMINI_API_KEY.")
