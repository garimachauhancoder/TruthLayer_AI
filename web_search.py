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
        source_details: list[dict] | None = None,
        error: str = ""
    ):
        self.query = query
        self.context = context
        self.sources = sources
        self.results = results
        self.source_details = source_details or []
        self.error = error

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "context": self.context,
            "sources": self.sources,
            "results": self.results,
            "source_details": self.source_details,
            "error": self.error,
        }


def search_web_for_claim(
    claim_text: str,
    tavily_api_key: str = "",
    max_results: int = 5,
    search_depth: str = "basic"
) -> SearchResult:
    """
    Searches the live web from both supporting and contradicting angles.

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

        queries = [
            ("supporting", claim_text),
            ("contradicting", f"{claim_text} false inaccurate contradicted debunked"),
        ]
        raw_results = []
        for angle, query in queries:
            response = client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=False,
                include_raw_content=False,
            )
            for item in response.get("results", []):
                raw_results.append({**item, "evidence_angle": angle, "search_query": query})
        if not raw_results:
            return SearchResult(
                query=claim_text,
                context="No live web search results were found for this claim.",
                sources=[],
                results=[],
                error=""
            )

        sources = []
        source_details = []
        context_parts = []

        for idx, item in enumerate(raw_results, start=1):
            title = item.get("title", "Untitled Source")
            url = item.get("url", "").strip()
            content = item.get("content", "").strip()
            published_date = item.get("published_date") or item.get("publishedDate") or ""

            if url and url not in sources:
                sources.append(url)
                source_details.append({
                    "title": title,
                    "url": url,
                    "published_date": published_date,
                    "evidence_angles": [item.get("evidence_angle", "supporting")],
                    "search_query": item.get("search_query", claim_text),
                    "excerpt": content,
                })
            elif url:
                existing = next(detail for detail in source_details if detail["url"] == url)
                angle = item.get("evidence_angle", "supporting")
                if angle not in existing["evidence_angles"]:
                    existing["evidence_angles"].append(angle)
                if not existing.get("published_date") and published_date:
                    existing["published_date"] = published_date

            context_parts.append(
                f"[{idx}] Search angle: {item.get('evidence_angle', 'supporting')}\n"
                f"Source: {title} ({url})\n"
                f"Publication date: {published_date or 'Not provided by search result'}\n"
                f"Excerpt: {content}"
            )

        context_str = "\n\n".join(context_parts)

        return SearchResult(
            query=claim_text,
            context=context_str,
            sources=sources,
            results=raw_results,
            source_details=source_details,
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
