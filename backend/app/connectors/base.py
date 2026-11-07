from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from backend.app.models.schemas import SourceCategory

@dataclass
class NormalizedSource:
    source_id: str
    title: str
    category: SourceCategory
    url: str
    author_or_owner: str = "Unknown"
    publication_or_repo: str = ""
    evidence_passages: list[str] = field(default_factory=list)
    retrieved_at: datetime = field(default_factory=datetime.utcnow)
    access_status: str = "accessible"
    metadata: dict[str, Any] = field(default_factory=dict)

class BaseSourceConnector(ABC):
    @abstractmethod
    async def search(self, queries: list[str], max_results: int = 10) -> list[NormalizedSource]:
        """
        Search external source using distinctive queries and return normalized sources.
        Must never invent fake sources or data.
        """
        pass
