import logging
import urllib.parse
import xml.etree.ElementTree as ET
import httpx

from backend.app.connectors.base import BaseSourceConnector, NormalizedSource
from backend.app.core.config import settings
from backend.app.models.schemas import SourceCategory

logger = logging.getLogger(__name__)

class ScholarlyConnector(BaseSourceConnector):
    """
    Connects to open-access scholarly databases:
    - Crossref REST API
    - OpenAlex API
    - arXiv API
    """
    _cache: dict[str, list[NormalizedSource]] = {}

    def __init__(self):
        self.headers = {
            "User-Agent": f"ECS-Project-Analysis-System/1.0 (mailto:{settings.CROSSREF_MAILTO})"
        }

    async def search(self, queries: list[str], max_results: int = 15) -> list[NormalizedSource]:
        sources: list[NormalizedSource] = []
        seen_urls = set()

        for q in queries:
            if q in self._cache:
                return self._cache[q][:max_results]

        async with httpx.AsyncClient(timeout=10.0, headers=self.headers) as client:
            for query in queries[:3]:
                clean_q = query.strip()
                if not clean_q or len(clean_q) < 5:
                    continue
                if clean_q in self._cache:
                    return self._cache[clean_q][:max_results]

                # 1. Search Crossref API
                try:
                    params = {
                        "query": clean_q,
                        "rows": 4,
                        "mailto": settings.CROSSREF_MAILTO
                    }
                    resp = await client.get("https://api.crossref.org/works", params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("message", {}).get("items", [])
                        for item in items:
                            doi = item.get("DOI")
                            url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
                            if not url or url in seen_urls:
                                continue
                            seen_urls.add(url)

                            title_list = item.get("title", [])
                            title = title_list[0] if title_list else "Scholarly Publication"
                            
                            authors = []
                            for a in item.get("author", []):
                                authors.append(f"{a.get('given', '')} {a.get('family', '')}".strip())
                            author_str = ", ".join(authors[:3]) if authors else "Unknown"
                            
                            container = item.get("container-title", [])
                            pub_name = container[0] if container else "Crossref Publication"
                            abstract = item.get("abstract", "")
                            
                            evidence = []
                            if abstract:
                                # Strip JATS XML tags if present
                                clean_abstract = abstract.replace("<jats:p>", "").replace("</jats:p>", "")
                                evidence.append(clean_abstract[:1000])
                            else:
                                evidence.append(f"{title}. Published in {pub_name} ({author_str}).")

                            sources.append(NormalizedSource(
                                source_id=f"cr_{doi or len(sources)}",
                                title=title,
                                category=SourceCategory.CROSSREF,
                                url=url,
                                author_or_owner=author_str,
                                publication_or_repo=pub_name,
                                evidence_passages=evidence,
                                metadata={"doi": doi, "publisher": item.get("publisher")}
                            ))
                except Exception as e:
                    logger.debug(f"Crossref search error: {e}")

                # 2. Search OpenAlex API
                try:
                    oa_url = f"https://api.openalex.org/works?search={urllib.parse.quote(clean_q)}&per-page=3"
                    resp = await client.get(oa_url)
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("results", []):
                            doi = item.get("doi")
                            url = doi or item.get("id")
                            if not url or url in seen_urls:
                                continue
                            seen_urls.add(url)

                            title = item.get("title") or "OpenAlex Academic Work"
                            authors = [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])]
                            author_str = ", ".join(filter(None, authors[:3])) or "Unknown"
                            
                            sources.append(NormalizedSource(
                                source_id=f"oa_{item.get('id', '').split('/')[-1]}",
                                title=title,
                                category=SourceCategory.PUBLICATIONS,
                                url=url,
                                author_or_owner=author_str,
                                publication_or_repo=item.get("primary_location", {}).get("source", {}).get("display_name", "OpenAlex Open Access"),
                                evidence_passages=[f"{title}. Authors: {author_str}."]
                            ))
                except Exception as e:
                    logger.debug(f"OpenAlex search error: {e}")

                # 3. Search arXiv API
                try:
                    ar_url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(clean_q)}&max_results=3"
                    resp = await client.get(ar_url)
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.text)
                        ns = {"atom": "http://www.w3.org/2005/Atom"}
                        for entry in root.findall("atom:entry", ns):
                            id_elem = entry.find("atom:id", ns)
                            title_elem = entry.find("atom:title", ns)
                            summary_elem = entry.find("atom:summary", ns)
                            
                            paper_url = id_elem.text.strip() if id_elem is not None else None
                            if not paper_url or paper_url in seen_urls:
                                continue
                            seen_urls.add(paper_url)

                            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else "arXiv Preprint"
                            summary = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""
                            
                            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None]
                            author_str = ", ".join(authors[:3]) if authors else "Unknown"

                            sources.append(NormalizedSource(
                                source_id=f"arxiv_{paper_url.split('/')[-1]}",
                                title=f"arXiv: {title}",
                                category=SourceCategory.PUBLICATIONS,
                                url=paper_url,
                                author_or_owner=author_str,
                                publication_or_repo="arXiv.org Open Access e-Print Archive",
                                evidence_passages=[summary[:1000]] if summary else [title]
                            ))
                except Exception as e:
                    logger.debug(f"arXiv search error: {e}")

                if len(sources) >= max_results:
                    break

        for q in queries:
            self._cache[q] = sources[:max_results]
        return sources[:max_results]
