"""Module for executing live web search using Tavily API."""

import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from tavily import TavilyClient


def _canonical_url(url: str) -> str:
    """Remove fragments and common tracking parameters for duplicate detection."""
    try:
        parts = urlsplit(url)
        query = [
            (key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not key.lower().startswith("utm_")
            and key.lower() not in {"fbclid", "gclid", "mc_cid", "mc_eid", "mibextid", "ref", "source"}
        ]
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))
    except Exception:
        return url


def _published_date(item: dict) -> str:
    """Read publication metadata only when the search provider supplies it."""
    for key in ("published_date", "publishedDate", "date_published", "published_at"):
        value = item.get(key)
        if value:
            return str(value).strip()
    return ""


class SearchResult:
    """Structured container for Tavily search results."""

    def __init__(
        self,
        query: str,
        context: str,
        sources: list[str],
        results: list[dict],
        source_details: list[dict] | None = None,
        warnings: list[str] | None = None,
        error: str = ""
    ):
        self.query = query
        self.context = context
        self.sources = sources
        self.results = results
        self.source_details = source_details or []
        self.warnings = warnings or []
        self.error = error

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "context": self.context,
            "sources": self.sources,
            "results": self.results,
            "source_details": self.source_details,
            "warnings": self.warnings,
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
        query_errors = []
        for angle, query in queries:
            angle_results = []
            for topic in ("general", "news"):
                try:
                    response = client.search(
                        query=query,
                        topic=topic,
                        search_depth=search_depth,
                        max_results=max_results,
                        include_answer=False,
                        include_raw_content=False,
                    )
                    topic_results = response.get("results", [])
                    angle_results.extend(
                        {**item, "evidence_angle": angle, "search_query": query, "search_topic": topic}
                        for item in topic_results
                    )
                    if topic == "general" and topic_results and all(
                        _published_date(item) for item in topic_results
                    ):
                        break
                except Exception as exc:
                    query_errors.append(f"{angle.title()} {topic} search failed: {exc}")
            raw_results.extend(angle_results)
        if not raw_results:
            return SearchResult(
                query=claim_text,
                context="No live web search results were found for this claim.",
                sources=[],
                results=[],
                error="; ".join(query_errors) if query_errors else ""
            )

        sources = []
        source_details = []
        context_parts = []

        for idx, item in enumerate(raw_results, start=1):
            title = item.get("title", "Untitled Source")
            url = item.get("url", "").strip()
            content = item.get("content", "").strip()
            published_date = _published_date(item)

            if url and url not in sources:
                sources.append(url)
                source_details.append({
                    "title": title,
                    "url": url,
                    "published_date": published_date,
                    "evidence_angles": [item.get("evidence_angle", "supporting")],
                    "search_topics": [item.get("search_topic", "general")],
                    "search_query": item.get("search_query", claim_text),
                    "excerpt": content,
                })
            elif url:
                existing = next(detail for detail in source_details if detail["url"] == url)
                angle = item.get("evidence_angle", "supporting")
                if angle not in existing["evidence_angles"]:
                    existing["evidence_angles"].append(angle)
                topic = item.get("search_topic", "general")
                if topic not in existing["search_topics"]:
                    existing["search_topics"].append(topic)
                if not existing.get("published_date") and published_date:
                    existing["published_date"] = published_date

            context_parts.append(
                f"[{idx}] Search angle: {item.get('evidence_angle', 'supporting')}\n"
                f"Search topic: {item.get('search_topic', 'general')}\n"
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
            warnings=query_errors,
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


def search_web_query(
    query: str,
    tavily_api_key: str = "",
    max_results: int = 8,
) -> SearchResult:
    """Run a user-entered web search against general web and recent news results."""
    cleaned_key = (tavily_api_key or os.getenv("TAVILY_API_KEY", "")).strip().strip("'\"")
    clean_query = (query or "").strip()
    if not clean_query:
        return SearchResult(query=clean_query, context="", sources=[], results=[], error="Enter a search query.")
    if not cleaned_key:
        return SearchResult(
            query=clean_query,
            context="",
            sources=[],
            results=[],
            error="Tavily API key is missing. Add TAVILY_API_KEY to the project .env file to search the web.",
        )

    client = TavilyClient(api_key=cleaned_key)
    results = []
    errors = []
    for topic in ("general", "news"):
        try:
            response = client.search(
                query=clean_query,
                topic=topic,
                search_depth="advanced",
                max_results=max_results,
                include_answer=False,
                include_raw_content=False,
            )
            results.extend({**item, "search_topic": topic} for item in response.get("results", []))
        except Exception as exc:
            errors.append(f"{topic.title()} search failed: {exc}")

    if not results:
        return SearchResult(
            query=clean_query,
            context="",
            sources=[],
            results=[],
            error="; ".join(errors) if errors else "No live web results were found.",
        )

    unique_results = []
    by_url = {}
    for item in results:
        url = (item.get("url") or "").strip()
        if not url:
            continue
        canonical_url = _canonical_url(url)
        if canonical_url in by_url:
            existing = by_url[canonical_url]
            date_value = _published_date(item)
            if not existing.get("published_date") and date_value:
                existing["published_date"] = date_value
            if item["search_topic"] not in existing["search_topics"]:
                existing["search_topics"].append(item["search_topic"])
            continue
        normalized = {**item, "search_topics": [item["search_topic"]]}
        by_url[canonical_url] = normalized
        unique_results.append(normalized)
    unique_results = unique_results[:max_results]

    details = []
    context_parts = []
    for idx, item in enumerate(unique_results, start=1):
        title = item.get("title") or "Untitled Source"
        url = item["url"]
        excerpt = (item.get("content") or "").strip()
        published_date = _published_date(item)
        details.append({
            "title": title,
            "url": url,
            "published_date": published_date,
            "search_topics": item["search_topics"],
            "excerpt": excerpt,
        })
        context_parts.append(
            f"[{idx}] {title} ({url})\n"
            f"Publication date: {published_date or 'Not provided by search result'}\n"
            f"Search topic: {' + '.join(item['search_topics'])}\n"
            f"Excerpt: {excerpt}"
        )
    return SearchResult(
        query=clean_query,
        context="\n\n".join(context_parts),
        sources=[item["url"] for item in details],
        results=unique_results,
        source_details=details,
        warnings=errors,
    )
