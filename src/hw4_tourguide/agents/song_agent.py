"""
SongAgent implementation (Mission M7.5).

Searches track candidates via an injected client (or optional secondary source),
then ranks by relevance/popularity/recency, fetches the selected track metadata,
and writes checkpoints for search/fetch stages using BaseAgent facilities.

Clients are injected to allow real APIs (e.g., Spotify) or offline stubs in tests.
"""

from typing import Any, Dict, List, Optional, Protocol
from datetime import datetime
import time

from hw4_tourguide.agents.base_agent import BaseAgent
from hw4_tourguide.tools.search import SearchTool
from hw4_tourguide.tools.fetch import FetchTool


class SongClient(Protocol):
    """Minimal client interface for search/fetch to keep SongAgent decoupled."""

    def search_tracks(self, query: str, limit: int) -> List[Dict[str, Any]]:
        ...

    def fetch_track(self, track_id: str) -> Dict[str, Any]:
        ...


class _DefaultSongClient:
    """Offline-friendly stub client."""

    def search_tracks(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
        ts = datetime.utcnow().isoformat()
        return [
            {
                "id": f"track_{i}",
                "title": f"Song {i} about {query}",
                "artist": "Stub Artist",
                "album": "Stub Album",
                "duration_ms": 180000,
                "preview_url": f"https://example.com/preview_{i}.mp3",
                "url": f"https://example.com/track/{i}",
                "popularity": 90 - i,
                "released_at": ts,
            }
            for i in range(limit)
        ]

    def fetch_track(self, track_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "id": track_id,
            "title": f"Title for {track_id}",
            "artist": "Stub Artist",
            "album": "Stub Album",
            "duration_ms": 200000,
            "preview_url": f"https://example.com/preview_{track_id}.mp3",
            "url": f"https://example.com/track/{track_id}",
        }


class SongAgent(BaseAgent):
    agent_type = "song"

    def __init__(
        self,
        config: Dict[str, Any],
        checkpoint_writer=None,
        metrics=None,
        circuit_breaker=None,
        mock_mode: bool = False,
        client: Optional[SongClient] = None,
        secondary_client: Optional[SongClient] = None,
        search_tool: Optional[SearchTool] = None,
        fetch_tool: Optional[FetchTool] = None,
        llm_client=None,
    ) -> None:
        # Smart client selection: 
        # 1. If primary (Spotify) exists, use it.
        # 2. If primary missing but secondary (YouTube) exists, promote secondary to primary.
        # 3. If both missing, use Stub.
        if client:
            self.client = client
            self.secondary_client = secondary_client
        elif secondary_client:
            self.client = secondary_client
            self.secondary_client = None # We promoted it, so don't use it twice
        else:
            self.client = _DefaultSongClient()
            self.secondary_client = None

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
        results = self.search_tool.search_tracks(self.client, query=query, limit=limit, step_number=step_number)
        # optional secondary source for broader coverage (e.g., YouTube)
        if use_secondary and self.secondary_client:
            secondary = self.search_tool.search_tracks(self.secondary_client, query=query, limit=limit, step_number=step_number)
            results.extend(secondary)
        self._record_latency("agent.song.search_ms", start)
        # Increment per-source counters
        primary_source = getattr(self.client, "provider_name", self.client.__class__.__name__).lower()
        if "spotify" in primary_source:
            self._increment_counter("api_calls.spotify")
        elif "youtube" in primary_source or "yt" in primary_source:
            self._increment_counter("api_calls.youtube")
        else:
            self._increment_counter("api_calls.song")
        if self.config.get("use_secondary_source") and self.secondary_client:
            sec_source = getattr(self.secondary_client, "provider_name", self.secondary_client.__class__.__name__).lower()
            if "spotify" in sec_source:
                self._increment_counter("api_calls.spotify")
            elif "youtube" in sec_source or "yt" in sec_source:
                self._increment_counter("api_calls.youtube")
            else:
                self._increment_counter("api_calls.song")
        self.logger.info(
            f"SEARCH | Query: \"{query}\" | Results: {len(results)}",
            extra={"event_tag": "Agent"},
        )
        return results

    def fetch(self, candidate: Dict[str, Any], task: Dict[str, Any], step_number: Optional[int] = None) -> Dict[str, Any]:
        tid = candidate.get("id")
        start = time.monotonic()
        details = self.fetch_tool.fetch_track(self.client, track_id=tid, step_number=step_number)
        self._record_latency("agent.song.fetch_ms", start)
        source = candidate.get("source") or getattr(self.client, "provider_name", self.client.__class__.__name__)
        if source and "spotify" in source.lower():
            self._increment_counter("api_calls.spotify")
        elif source and ("youtube" in source.lower() or "yt" in source.lower()):
            self._increment_counter("api_calls.youtube")
        else:
            self._increment_counter("api_calls.song")
        self.logger.info(
            f"FETCH | Selected: {tid} | Reason: ranked top",
            extra={"event_tag": "Agent"},
        )
        details.setdefault("title", f"Song for {task.get('location_name')}")
        details.setdefault("url", f"https://example.com/track/{tid}")
        details.setdefault("source", candidate.get("source", "primary"))
        return details

    def _rank_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank by relevance to address/search_hint/instructions plus popularity/recency."""

        def score(cand: Dict[str, Any]) -> float:
            title = (cand.get("title") or "").lower()
            rel_terms = [q.lower() for q in self._queries]
            relevance = sum(1 for t in rel_terms if t in title)
            popularity = cand.get("popularity") or cand.get("view_count") or 0
            released = cand.get("released_at") or cand.get("published_at")
            recency = 1 if released else 0
            return (relevance * 10) + (recency * 2) + (popularity / 100)

        return sorted(candidates, key=score, reverse=True)

    def _build_queries(self, task: Dict[str, Any]) -> List[str]:
        queries = super()._build_queries(task)
        # Optional mood/genre inference
        if self.config.get("infer_song_mood"):
            hint = f"{task.get('search_hint', '')} {task.get('route_context', '')} {task.get('instructions', '')}".lower()
            moods = []
            if any(k in hint for k in ["relax", "chill", "coast", "beach"]):
                moods.append("chill acoustic")
            if any(k in hint for k in ["party", "nightlife", "club"]):
                moods.append("dance electronic")
            if any(k in hint for k in ["historic", "museum", "culture"]):
                moods.append("classical instrumental")
            queries.extend(moods)
        # Dedup
        seen = set()
        uniq = []
        for q in queries:
            q = q.strip()
            if q and q not in seen:
                seen.add(q)
                uniq.append(q)
        return uniq
