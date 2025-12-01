"""
KnowledgeAgent implementation (Mission M7.6).

Searches article candidates via an injected client (with optional secondary
source), ranks by authority/relevance/recency, fetches the selected article
metadata, and writes checkpoints for search/fetch stages using BaseAgent
facilities.

Clients are injected to allow real APIs (e.g., Wikipedia/DuckDuckGo) or offline
stubs in tests.
"""

from typing import Any, Dict, List, Optional, Protocol
from datetime import datetime
import time

from hw4_tourguide.agents.base_agent import BaseAgent
from hw4_tourguide.tools.search import SearchTool
from hw4_tourguide.tools.fetch import FetchTool


class KnowledgeClient(Protocol):
    """Minimal client interface for search/fetch to keep KnowledgeAgent decoupled."""

    def search_articles(self, query: str, limit: int) -> List[Dict[str, Any]]:
        ...

    def fetch_article(self, article_id: str) -> Dict[str, Any]:
        ...


class _DefaultKnowledgeClient:
    """Offline-friendly stub client."""

    def search_articles(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
        ts = datetime.utcnow().isoformat()
        return [
            {
                "id": f"article_{i}",
                "title": f"Article {i} about {query}",
                "url": f"https://example.com/wiki/{i}",
                "source": "Stubpedia",
                "snippet": f"Snippet {i} for {query}",
                "published_at": ts,
            }
            for i in range(limit)
        ]

    def fetch_article(self, article_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "id": article_id,
            "title": f"Title for {article_id}",
            "url": f"https://example.com/wiki/{article_id}",
            "summary": f"Summary for {article_id}",
            "citations": [
                {
                    "title": f"Citation for {article_id}",
                    "url": f"https://example.com/src/{article_id}",
                    "excerpt": "Excerpt text",
                }
            ],
        }


class KnowledgeAgent(BaseAgent):
    agent_type = "knowledge"

    def __init__(
        self,
        config: Dict[str, Any],
        checkpoint_writer=None,
        metrics=None,
        circuit_breaker=None,
        mock_mode: bool = False,
        client: Optional[KnowledgeClient] = None,
        secondary_client: Optional[KnowledgeClient] = None,
        search_tool: Optional[SearchTool] = None,
        fetch_tool: Optional[FetchTool] = None,
        llm_client=None,
    ) -> None:
        self.client = client or _DefaultKnowledgeClient()
        self.secondary_client = secondary_client
        self.search_tool = search_tool or SearchTool(timeout=config.get("timeout", 10.0))
        self.fetch_tool = fetch_tool or FetchTool(timeout=config.get("timeout", 10.0))
        super().__init__(
            config=config,
            checkpoint_writer=checkpoint_writer,
            metrics=metrics,
            circuit_breaker=circuit_breaker,
            mock_mode=mock_mode,
            llm_client=llm_client,
        )

    def search(self, query: str, task: Dict[str, Any], step_number: Optional[int] = None) -> List[Dict[str, Any]]:
        limit = int(self.config.get("search_limit", 3))
        start = time.monotonic()
        use_secondary = self.config.get("use_secondary_source") or task.get("use_secondary_source") or task.get("agents.use_secondary_source")
        results = self.search_tool.search_articles(self.client, query=query, limit=limit, step_number=step_number)
        if use_secondary and self.secondary_client:
            results.extend(self.search_tool.search_articles(self.secondary_client, query=query, limit=limit, step_number=step_number))
        self._record_latency("agent.knowledge.search_ms", start)
        self._increment_counter("api_calls.wikipedia")
        self.logger.info(
            f"SEARCH | Query: \"{query}\" | Results: {len(results)}",
            extra={"event_tag": "Agent"},
        )
        return results

    def fetch(self, candidate: Dict[str, Any], task: Dict[str, Any], step_number: Optional[int] = None) -> Dict[str, Any]:
        aid = candidate.get("id")
        start = time.monotonic()
        details = self.fetch_tool.fetch_article(self.client, article_id=aid, step_number=step_number)
        self._record_latency("agent.knowledge.fetch_ms", start)
        self._increment_counter("api_calls.wikipedia")
        self.logger.info(
            f"FETCH | Selected: {aid} | Reason: ranked top",
            extra={"event_tag": "Agent"},
        )
        details.setdefault("title", f"Article for {task.get('location_name')}")
        details.setdefault("url", f"https://example.com/wiki/{aid}")
        details.setdefault("source", candidate.get("source", "primary"))
        # Basic citation extraction: ensure at least one citation entry
        if not details.get("citations"):
            details["citations"] = candidate.get("citations", [])
        if not details.get("citations"):
            details["citations"] = [
                {
                    "title": details.get("title", f"Citation for {aid}"),
                    "url": details.get("url", f"https://example.com/wiki/{aid}"),
                    "excerpt": candidate.get("snippet", ""),
                }
            ]
        return details

    def _rank_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank by authority (wikipedia/org), relevance (incl. instructions), then recency."""
        def score(cand: Dict[str, Any]) -> float:
            title = (cand.get("title") or "").lower()
            url = (cand.get("url") or "").lower()
            rel_terms = [q.lower() for q in self._queries]
            relevance = sum(1 for t in rel_terms if t in title or t in url)
            authority = 0
            if "wikipedia.org" in url or url.endswith(".gov") or url.endswith(".edu") or ".gov/" in url or ".edu/" in url:
                authority = 3
            recency = 1 if cand.get("published_at") else 0
            return (authority * 5) + (relevance * 10) + (recency * 2)

        return sorted(candidates, key=score, reverse=True)
