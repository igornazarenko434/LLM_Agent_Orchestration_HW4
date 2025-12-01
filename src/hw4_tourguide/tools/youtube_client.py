"""
Lightweight YouTube Data API v3 client for VideoAgent.
Uses API key (no OAuth), supports search + video details fetch with minimal fields.
"""

from typing import Dict, Any, List, Optional
import requests
import time

from hw4_tourguide.logger import get_logger


class YouTubeClient:
    def __init__(self, api_key: str, timeout: float = 10.0):
        self.api_key = api_key
        self.timeout = timeout
        self.api_logger = get_logger("api")

    def search_videos(self, query: str, limit: int = 3, location: Optional[Dict[str, float]] = None, radius_km: Optional[float] = None, step_number: Optional[int] = None) -> List[Dict[str, Any]]:
        log_extra = {"event_tag": "API_Call", "api_name": "YouTube", "method": "search", "step": step_number}
        step_info = f" | Step {step_number}" if step_number is not None else ""
        self.api_logger.info(
            f"API_Call{step_info} | API: YouTube Search | Query: \"{query[:60]}\" | Max Results: {limit}",
            extra=log_extra
        )

        try:
            start = time.time()
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": min(limit, 5),
                "key": self.api_key,
                "safeSearch": "none",
            }
            if location and radius_km:
                params["location"] = f"{location.get('lat')},{location.get('lng')}"
                params["locationRadius"] = f"{radius_km}km"
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            results = []
            for item in items:
                vid = item.get("id", {}).get("videoId")
                if not vid:
                    continue
                snippet = item.get("snippet", {})
                results.append(
                    {
                        "id": vid,
                        "title": snippet.get("title"),
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "channel": snippet.get("channelTitle"),
                        "published_at": snippet.get("publishedAt"),
                    }
                )

            elapsed_ms = (time.time() - start) * 1000
            self.api_logger.info(
                f"API_Success | API: YouTube Search | Results: {len(results)} | Time: {elapsed_ms:.0f}ms | "
                f"Quota: ~{len(results) * 100} units",
                extra={**log_extra, "event_tag": "API_Success", "results_count": len(results), "quota_cost": len(results) * 100}
            )
            return results

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else "Unknown"
            reason = exc.response.reason if exc.response else str(exc)
            self.api_logger.warning(
                f"API_Failure | API: YouTube Search | Error: HTTPError {status_code} | "
                f"Reason: {reason}",
                extra={**log_extra, "event_tag": "API_Failure", "error_type": "HTTPError"}
            )
            raise
        except Exception as exc:
            self.api_logger.warning(
                f"API_Failure | API: YouTube Search | Error: {type(exc).__name__}: {str(exc)[:100]}",
                extra={**log_extra, "event_tag": "API_Failure", "error_type": type(exc).__name__}
            )
            raise

    def fetch_video(self, video_id: str, step_number: Optional[int] = None) -> Dict[str, Any]:
        log_extra = {"event_tag": "API_Call", "api_name": "YouTube", "method": "fetch", "step": step_number}
        step_info = f" | Step {step_number}" if step_number is not None else ""
        self.api_logger.info(
            f"API_Call{step_info} | API: YouTube Fetch | Video ID: {video_id}",
            extra=log_extra
        )

        try:
            start = time.time()
            params = {
                "part": "snippet,contentDetails,statistics",
                "id": video_id,
                "key": self.api_key,
            }
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            if not items:
                raise RuntimeError("No video metadata returned")
            item = items[0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            details = {
                "id": video_id,
                "title": snippet.get("title"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "channel": snippet.get("channelTitle"),
                "description": snippet.get("description"),
                "published_at": snippet.get("publishedAt"),
                "duration": item.get("contentDetails", {}).get("duration"),
                "view_count": int(stats.get("viewCount", 0)) if stats.get("viewCount") else None,
            }

            elapsed_ms = (time.time() - start) * 1000
            self.api_logger.info(
                f"API_Success | API: YouTube Fetch | Video: \"{details.get('title', 'N/A')[:50]}\" | "
                f"Time: {elapsed_ms:.0f}ms | Quota: ~1 unit",
                extra={**log_extra, "event_tag": "API_Success", "api_name": "YouTube"}
            )
            return details

        except Exception as exc:
            self.api_logger.warning(
                f"API_Failure | API: YouTube Fetch | Video ID: {video_id} | Error: {type(exc).__name__}: {str(exc)[:100]}",
                extra={**log_extra, "event_tag": "API_Failure", "api_name": "YouTube", "error_type": type(exc).__name__}
            )
            raise
