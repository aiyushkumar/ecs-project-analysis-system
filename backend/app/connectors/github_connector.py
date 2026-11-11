import base64
import logging
import re
import urllib.parse
from typing import Any
import httpx

from backend.app.connectors.base import BaseSourceConnector, NormalizedSource
from backend.app.core.config import settings
from backend.app.models.schemas import SourceCategory

logger = logging.getLogger(__name__)

class GitHubConnector(BaseSourceConnector):
    """
    Connects to official GitHub REST API to find open-source repositories matching
    project keywords, title, architecture, or code patterns.
    """
    _cache: dict[str, list[NormalizedSource]] = {}

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ECS-Project-Analysis-System/1.0"
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    async def search(self, queries: list[str], max_results: int = 8) -> list[NormalizedSource]:
        sources: list[NormalizedSource] = []
        seen_urls = set()

        # Check cache first
        for q in queries:
            if q in self._cache:
                return self._cache[q][:max_results]

        async with httpx.AsyncClient(timeout=10.0, headers=self.headers) as client:
            for query in queries[:4]:
                clean_q = re.sub(r'[\r\n\t]+', ' ', str(query)).strip()
                clean_q = re.sub(r'\s+', ' ', clean_q)
                if not clean_q or len(clean_q) < 4:
                    continue
                if clean_q in self._cache:
                    return self._cache[clean_q][:max_results]
                
                try:
                    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(clean_q)}&sort=stars&order=desc&per_page=5"
                    resp = await client.get(url)
                    
                    if resp.status_code == 403:
                        logger.warning("GitHub API rate limit exceeded. Skipping remaining GitHub queries.")
                        break
                    
                    if resp.status_code != 200:
                        continue
                    
                    data = resp.json()
                    items = data.get("items", [])
                    
                    for item in items:
                        repo_url = item.get("html_url")
                        if not repo_url or repo_url in seen_urls:
                            continue
                        seen_urls.add(repo_url)

                        full_name = item.get("full_name", "")
                        owner = item.get("owner", {}).get("login", "Unknown")
                        desc = item.get("description") or ""
                        topics = " ".join(item.get("topics", []))
                        
                        evidence = []
                        if desc:
                            evidence.append(desc)
                        if topics:
                            evidence.append(f"Repository topics: {topics}")
                        
                        # Optionally fetch repo README snippet if available
                        readme_url = f"https://api.github.com/repos/{full_name}/readme"
                        try:
                            readme_resp = await client.get(readme_url)
                            if readme_resp.status_code == 200:
                                r_data = readme_resp.json()
                                content_b64 = r_data.get("content", "")
                                if content_b64:
                                    decoded = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                                    # Take first 1000 characters of README as evidence
                                    evidence.append(decoded[:1000])
                        except Exception as e:
                            logger.debug(f"Could not fetch readme for {full_name}: {e}")

                        source_id = f"gh_{item.get('id')}"
                        sources.append(NormalizedSource(
                            source_id=source_id,
                            title=f"GitHub: {full_name}",
                            category=SourceCategory.GITHUB,
                            url=repo_url,
                            author_or_owner=owner,
                            publication_or_repo=full_name,
                            evidence_passages=evidence,
                            metadata={"stars": item.get("stargazers_count", 0), "language": item.get("language")}
                        ))

                        if len(sources) >= max_results:
                            for q in queries:
                                self._cache[q] = sources
                            return sources
                            
                except Exception as e:
                    logger.error(f"Error querying GitHub API for '{clean_q}': {e}")

        for q in queries:
            self._cache[q] = sources
        return sources
