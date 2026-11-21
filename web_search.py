"""Module for executing live web search using Tavily API."""

import os
from tavily import TavilyClient


class SearchResult:
    """Structured container for Tavily search results."""

    def __init__(
        self,
        query: str,
        context: str,
        sources: list[str],
        results: list[dict],
        error: str = ""
    ):
        self.query = query
        self.context = context
        self.sources = sources
        self.results = results
        self.error = error

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "context": self.context,
            "sources": self.sources,
            "results": self.results,
            "error": self.error,
        }


def search_web_for_claim(
    claim_text: str,
    tavily_api_key: str = "",
    max_results: int = 5,
    search_depth: str = "basic"
) -> SearchResult:
    """
    Searches the live web using the Tavily API for evidence regarding a claim.

    Args:
        claim_text: The factual claim statement to search.
        tavily_api_key: Tavily API key (optional; defaults to TAVILY_API_KEY environment variable).
        max_results: Maximum number of search results to retrieve (default: 5).
        search_depth: Tavily search depth ('basic' or 'advanced').

    Returns:
        SearchResult containing textual context, unique source URLs, raw hits, and any error.
    """
    cleaned_key = (tavily_api_key or os.getenv("TAVILY_API_KEY", "")).strip().strip("'\"")
    if not cleaned_key:
        return SearchResult(
            query=claim_text,
            context="",
            sources=[],
            results=[],
            error="Tavily API key is missing. Please provide a valid Tavily API key in .env or the sidebar."
        )

    try:
        client = TavilyClient(api_key=cleaned_key)

        response = client.search(
            query=claim_text,
            search_depth=search_depth,
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )

        raw_results = response.get("results", [])
        if not raw_results:
            return SearchResult(
                query=claim_text,
                context="No live web search results were found for this claim.",
                sources=[],
                results=[],
                error=""
            )

        sources = []
        context_parts = []

        for idx, item in enumerate(raw_results, start=1):
            title = item.get("title", "Untitled Source")
            url = item.get("url", "").strip()
            content = item.get("content", "").strip()

            if url and url not in sources:
                sources.append(url)

            context_parts.append(f"[{idx}] Source: {title} ({url})\nExcerpt: {content}")

        context_str = "\n\n".join(context_parts)

        return SearchResult(
            query=claim_text,
            context=context_str,
            sources=sources,
            results=raw_results,
            error=""
        )

    except Exception as exc:
        return SearchResult(
            query=claim_text,
            context="",
            sources=[],
            results=[],
            error=f"Tavily search error: {exc}"
        )
