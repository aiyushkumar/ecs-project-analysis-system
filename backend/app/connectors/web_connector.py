import logging
from duckduckgo_search import DDGS
import httpx

from backend.app.connectors.base import BaseSourceConnector, NormalizedSource
from backend.app.core.config import settings
from backend.app.models.schemas import SourceCategory

logger = logging.getLogger(__name__)

class WebSearchConnector(BaseSourceConnector):
    """
    Connects to public web search (DuckDuckGo or self-hosted SearXNG)
    to discover internet sources, documentation, and technical articles.
    """
    _cache: dict[str, list[NormalizedSource]] = {}

    async def search(self, queries: list[str], max_results: int = 10) -> list[NormalizedSource]:
        sources: list[NormalizedSource] = []
        seen_urls = set()

        for q in queries:
            if q in self._cache:
                return self._cache[q][:max_results]

        # If SearXNG is configured, use it first
        if settings.SEARXNG_URL:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    for q in queries[:2]:
                        resp = await client.get(
                            f"{settings.SEARXNG_URL}/search",
                            params={"q": q, "format": "json"}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            for r in data.get("results", []):
                                url = r.get("url")
                                if not url or url in seen_urls:
                                    continue
                                seen_urls.add(url)
                                sources.append(NormalizedSource(
                                    source_id=f"web_{len(sources)}",
                                    title=r.get("title", "Internet Web Page"),
                                    category=SourceCategory.INTERNET,
                                    url=url,
                                    author_or_owner=r.get("engine", "Web"),
                                    publication_or_repo=url.split("/")[2] if "//" in url else "Internet",
                                    evidence_passages=[r.get("content", "")]
                                ))
            except Exception as e:
                logger.debug(f"SearXNG query error: {e}")

        # Fallback to DuckDuckGo search
        if len(sources) < max_results:
            try:
                with DDGS() as ddgs:
                    for query in queries[:3]:
                        clean_q = query.strip()
                        if not clean_q or len(clean_q) < 5:
                            continue
                        
                        try:
                            results = list(ddgs.text(clean_q, max_results=4))
                            for r in results:
                                url = r.get("href")
                                if not url or url in seen_urls:
                                    continue
                                seen_urls.add(url)
                                
                                title = r.get("title") or "Web Source"
                                body = r.get("body") or ""
                                domain = url.split("/")[2] if "//" in url else "Web"
                                
                                # Check if it's researchgate.net or academic site
                                category = SourceCategory.INTERNET
                                if "researchgate.net" in url:
                                    category = SourceCategory.PUBLICATIONS

                                sources.append(NormalizedSource(
                                    source_id=f"web_{len(sources)}",
                                    title=title,
                                    category=category,
                                    url=url,
                                    author_or_owner=domain,
                                    publication_or_repo=domain,
                                    evidence_passages=[body] if body else [title]
                                ))
                                
                                if len(sources) >= max_results:
                                    for q in queries:
                                        self._cache[q] = sources
                                    return sources
                        except Exception as e:
                            logger.debug(f"DDGS query error for '{clean_q}': {e}")
            except Exception as e:
                logger.warning(f"Web search connector encountered issue: {e}")

        for q in queries:
            self._cache[q] = sources[:max_results]
        return sources[:max_results]
