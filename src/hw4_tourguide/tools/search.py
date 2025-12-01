"""
SearchTool module (Mission M7.7c).
Provides thin wrappers around provider clients for the search phase with
timeout enforcement and structured logging. Agents remain responsible for
retries/backoff/circuit breaker/metrics.
"""

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any, Dict, List, Optional

from hw4_tourguide.logger import get_logger


class SearchTool:
    def __init__(self, timeout: float = 10.0, logger_name: str = "search") -> None:
        self.timeout = timeout
        self.logger = get_logger(logger_name)

    def search_videos(self, client: Any, query: str, limit: int = 3, location: Optional[Dict[str, float]] = None, radius_km: Optional[float] = None, step_number: Optional[int] = None) -> List[Dict[str, Any]]:
        def _call():
            try:
                return client.search_videos(query=query, limit=limit, location=location, radius_km=radius_km, step_number=step_number)
            except TypeError:
                return client.search_videos(query=query, limit=limit) # Fallback for clients not updated yet

        return self._run_with_timeout(
            _call,
            provider="video",
            query=query,
            step_number=step_number
        )

    def search_tracks(self, client: Any, query: str, limit: int = 3, step_number: Optional[int] = None) -> List[Dict[str, Any]]:
        def _call():
            try:
                return client.search_tracks(query=query, limit=limit, step_number=step_number)
            except TypeError:
                return client.search_tracks(query=query, limit=limit)

        return self._run_with_timeout(
            _call,
            provider="song",
            query=query,
            step_number=step_number
        )

    def search_articles(self, client: Any, query: str, limit: int = 3, step_number: Optional[int] = None) -> List[Dict[str, Any]]:
        def _call():
            try:
                return client.search_articles(query=query, limit=limit, step_number=step_number)
            except TypeError:
                return client.search_articles(query=query, limit=limit)

        return self._run_with_timeout(
            _call,
            provider="knowledge",
            query=query,
            step_number=step_number
        )

    def _run_with_timeout(self, func, provider: str, query: str, step_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Execute func with timeout; log query and result count."""
        start = time.time()
        log_extra = {"event_tag": "Agent", "step": step_number}
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(func)
                results = future.result(timeout=self.timeout)
        except FuturesTimeout:
            self.logger.warning(
                f"SEARCH TIMEOUT | provider={provider} | query=\"{query}\" | timeout={self.timeout}s",
                extra=log_extra,
            )
            raise TimeoutError(f"Search timeout for provider={provider}")
        except Exception as exc:
            self.logger.warning(
                f"SEARCH ERROR | provider={provider} | query=\"{query}\" | error={exc}",
                extra=log_extra,
            )
            raise

        count = len(results) if isinstance(results, list) else 0
        self.logger.info(
            f"SEARCH | provider={provider} | query=\"{query}\" | results={count} | ms={(time.time()-start)*1000:.1f}",
            extra=log_extra,
        )
        # Enforce limit defensively
        try:
            limit = int(limit)
        except Exception:
            limit = 3
        return results[:limit] if isinstance(results, list) else []
