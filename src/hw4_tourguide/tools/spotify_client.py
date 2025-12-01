"""
Lightweight Spotify Web API client for SongAgent (Client Credentials flow).
Supports search and track fetch. Token is cached in-memory.
"""

import time
from typing import Dict, Any, List, Optional
import requests
from requests.auth import HTTPBasicAuth

from hw4_tourguide.logger import get_logger


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str, timeout: float = 10.0):
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0
        self.api_logger = get_logger("api")

    def _ensure_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expiry:
            return self._token
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=HTTPBasicAuth(self.client_id, self.client_secret),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = now + int(data.get("expires_in", 3600)) - 60  # refresh 1m early
        return self._token

    def search_tracks(self, query: str, limit: int = 3, step_number: Optional[int] = None) -> List[Dict[str, Any]]:
        log_extra = {"event_tag": "API_Call", "api_name": "Spotify", "method": "search", "step": step_number}
        step_info = f" | Step {step_number}" if step_number is not None else ""
        self.api_logger.info(
            f"API_Call{step_info} | API: Spotify Search | Query: \"{query[:60]}\" | Max Results: {limit}",
            extra=log_extra
        )

        try:
            start = time.time()
            token = self._ensure_token()
            headers = {"Authorization": f"Bearer {token}"}
            params = {"q": query, "type": "track", "limit": min(limit, 5)}
            resp = requests.get(
                "https://api.spotify.com/v1/search",
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            tracks = data.get("tracks", {}).get("items", [])
            results = []
            for t in tracks:
                results.append(
                    {
                        "id": t.get("id"),
                        "title": t.get("name"),
                        "artist": ", ".join(a.get("name", "") for a in t.get("artists", [])),
                        "album": t.get("album", {}).get("name"),
                        "duration_ms": t.get("duration_ms"),
                        "preview_url": t.get("preview_url"),
                        "url": t.get("external_urls", {}).get("spotify"),
                        "popularity": t.get("popularity"),
                        "released_at": t.get("album", {}).get("release_date"),
                        "source": "spotify",
                    }
                )

            elapsed_ms = (time.time() - start) * 1000
            self.api_logger.info(
                f"API_Success | API: Spotify Search | Results: {len(results)} | Time: {elapsed_ms:.0f}ms",
                extra={**log_extra, "event_tag": "API_Success", "results_count": len(results)}
            )
            return results

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else "Unknown"
            reason = exc.response.reason if exc.response else str(exc)
            self.api_logger.warning(
                f"API_Failure | API: Spotify Search | Error: HTTPError {status_code} | "
                f"Reason: {reason}",
                extra={**log_extra, "event_tag": "API_Failure", "error_type": "HTTPError"}
            )
            raise
        except Exception as exc:
            self.api_logger.warning(
                f"API_Failure | API: Spotify Search | Error: {type(exc).__name__}: {str(exc)[:100]}",
                extra={**log_extra, "event_tag": "API_Failure", "error_type": type(exc).__name__}
            )
            raise

    def fetch_track(self, track_id: str, step_number: Optional[int] = None) -> Dict[str, Any]:
        log_extra = {"event_tag": "API_Call", "api_name": "Spotify", "method": "fetch", "step": step_number}
        step_info = f" | Step {step_number}" if step_number is not None else ""
        self.api_logger.info(
            f"API_Call{step_info} | API: Spotify Fetch | Track ID: {track_id}",
            extra=log_extra
        )

        try:
            start = time.time()
            token = self._ensure_token()
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(
                f"https://api.spotify.com/v1/tracks/{track_id}",
                headers=headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            t = resp.json()
            details = {
                "id": t.get("id"),
                "title": t.get("name"),
                "artist": ", ".join(a.get("name", "") for a in t.get("artists", [])),
                "album": t.get("album", {}).get("name"),
                "duration_ms": t.get("duration_ms"),
                "preview_url": t.get("preview_url"),
                "url": t.get("external_urls", {}).get("spotify"),
                "popularity": t.get("popularity"),
                "released_at": t.get("album", {}).get("release_date"),
                "source": "spotify",
                "genre": ", ".join(t.get("album", {}).get("genres", [])) if t.get("album", {}) else None,
            }

            elapsed_ms = (time.time() - start) * 1000
            self.api_logger.info(
                f"API_Success | API: Spotify Fetch | Track: \"{details.get('title', 'N/A')[:50]}\" | "
                f"Time: {elapsed_ms:.0f}ms",
                extra={**log_extra, "event_tag": "API_Success"}
            )
            return details

        except Exception as exc:
            self.api_logger.warning(
                f"API_Failure | API: Spotify Fetch | Track ID: {track_id} | Error: {type(exc).__name__}: {str(exc)[:100]}",
                extra={**log_extra, "event_tag": "API_Failure", "error_type": type(exc).__name__}
            )
            raise
