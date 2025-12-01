"""
VideoAgent implementation (Mission M7.4).

Searches for candidate videos via an injected client, ranks by relevance/view
count/recency, fetches the selected video's metadata, and writes checkpoints for
search/fetch stages. Uses BaseAgent for retries, query expansion, metrics, and
checkpoint handling.
"""

from typing import Any, Dict, List, Optional
import time

from hw4_tourguide.agents.base_agent import BaseAgent
from hw4_tourguide.tools.youtube_client import YouTubeClient
from hw4_tourguide.tools.search import SearchTool
from hw4_tourguide.tools.fetch import FetchTool


class _DefaultVideoClient:
    """Offline-friendly stub client."""

    def search_videos(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
        return [
            {
                "id": f"video_{i}",
                "title": f"Video {i} about {query}",
                "url": f"https://example.com/video/{i}",
                "view_count": 100 - i,
                "published_at": None,
            }
            for i in range(limit)
        ]

    def fetch_video(self, video_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "id": video_id,
            "title": f"Title for {video_id}",
            "url": f"https://example.com/watch/{video_id}",
            "description": f"Description for {video_id}",
            "channel": "Stub Channel",
            "view_count": 1000,
            "published_at": None,
        }


class VideoAgent(BaseAgent):
    agent_type = "video"

    def __init__(
        self,
        config: Dict[str, Any],
        checkpoint_writer=None,
        metrics=None,
        circuit_breaker=None,
        mock_mode: bool = False,
        client: Optional[Any] = None,
        search_tool: Optional[SearchTool] = None,
        fetch_tool: Optional[FetchTool] = None,
        llm_client=None,
    ) -> None:
        self.client = client or _DefaultVideoClient()
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
        location = task.get("coordinates") if self.config.get("use_geosearch", True) else None
        radius = self.config.get("geosearch_radius_km", None)
        results = self.search_tool.search_videos(self.client, query=query, limit=limit, location=location, radius_km=radius, step_number=step_number)
        self._record_latency("agent.video.search_ms", start)
        provider = getattr(self.client, "provider_name", self.client.__class__.__name__).lower()
        if "youtube" in provider or "yt" in provider:
            self._increment_counter("api_calls.youtube")
        else:
            self._increment_counter("api_calls.video")
        return results

    def fetch(self, candidate: Dict[str, Any], task: Dict[str, Any], step_number: Optional[int] = None) -> Dict[str, Any]:
        vid = candidate.get("id")
        start = time.monotonic()
        details = self.fetch_tool.fetch_video(self.client, video_id=vid, step_number=step_number)
        self._record_latency("agent.video.fetch_ms", start)
        provider = candidate.get("source") or getattr(self.client, "provider_name", self.client.__class__.__name__)
        if provider and ("youtube" in provider.lower() or "yt" in provider.lower()):
            self._increment_counter("api_calls.youtube")
        else:
            self._increment_counter("api_calls.video")
        self.logger.info(
            f"FETCH | Selected: {vid} | Reason: ranked top",
            extra={"event_tag": "Agent"},
        )
        # Ensure core fields exist
        details.setdefault("id", vid)
        details.setdefault("url", f"https://example.com/watch/{vid}")
        details.setdefault("title", f"Video for {task.get('location_name')}")
        # Carry duration if available from candidate
        if "duration_seconds" not in details and candidate.get("duration_seconds"):
            details["duration_seconds"] = candidate.get("duration_seconds")
        return details

    def _rank_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank by relevance to query terms (incl. instructions), then view_count, then recency."""

        def score(cand: Dict[str, Any]) -> float:
            title = (cand.get("title") or "").lower()
            rel_terms = [q.lower() for q in self._queries]
            relevance = sum(1 for t in rel_terms if t in title)
            duration_score = 0
            min_d = self.config.get("min_duration_seconds")
            max_d = self.config.get("max_duration_seconds")
            dur = cand.get("duration_seconds") or 0
            if min_d and dur < min_d:
                return -1
            if max_d and dur > max_d:
                return -1
            if dur:
                duration_score = 1  # slight bonus for having a duration
            views = cand.get("view_count") or 0
            recency = 1 if cand.get("published_at") else 0
            return (relevance * 10) + (views / 1000) + recency + duration_score

        return sorted(candidates, key=score, reverse=True)
