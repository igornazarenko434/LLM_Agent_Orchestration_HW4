"""
Lightweight Wikipedia + DuckDuckGo client for KnowledgeAgent.
Uses keyless APIs: MediaWiki search + extracts; DuckDuckGo Instant Answer as fallback.
"""

from typing import Dict, Any, List, Optional
import requests
import time

from hw4_tourguide.logger import get_logger


class WikipediaClient:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.api_logger = get_logger("api")

    def search_articles(self, query: str, limit: int = 3, step_number: Optional[int] = None) -> List[Dict[str, Any]]:
        log_extra = {"event_tag": "API_Call", "api_name": "Wikipedia", "method": "search", "step": step_number}
        step_info = f" | Step {step_number}" if step_number is not None else ""
        self.api_logger.info(
            f"API_Call{step_info} | API: Wikipedia Search | Query: \"{query[:60]}\" | Max Results: {limit}",
            extra=log_extra
        )

        try:
            start = time.time()
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": min(limit, 10),
            }
            headers = {"User-Agent": "hw4_tourguide/1.0 (student project)"}
            resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params=params,
                timeout=self.timeout,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("query", {}).get("search", []):
                pageid = item.get("pageid")
                title = item.get("title")
                if not pageid or not title:
                    continue
                results.append(
                    {
                        "id": str(pageid),
                        "title": title,
                        "url": f"https://en.wikipedia.org/?curid={pageid}",
                        "snippet": item.get("snippet"),
                        "source": "wikipedia",
                    }
                )

            elapsed_ms = (time.time() - start) * 1000
            self.api_logger.info(
                f"API_Success | API: Wikipedia Search | Results: {len(results)} | Time: {elapsed_ms:.0f}ms",
                extra={**log_extra, "event_tag": "API_Success", "results_count": len(results)}
            )
            return results

        except requests.exceptions.HTTPError as exc:
            self.api_logger.warning(
                f"API_Failure | API: Wikipedia Search | Error: HTTPError {exc.response.status_code}",
                extra={**log_extra, "event_tag": "API_Failure", "error_type": "HTTPError"}
            )
            raise
        except Exception as exc:
            self.api_logger.warning(
                f"API_Failure | API: Wikipedia Search | Error: {type(exc).__name__}: {str(exc)[:100]}",
                extra={**log_extra, "event_tag": "API_Failure", "error_type": type(exc).__name__}
            )
            raise

    def fetch_article(self, article_id: str, step_number: Optional[int] = None) -> Dict[str, Any]:
        log_extra = {"event_tag": "API_Call", "api_name": "Wikipedia", "method": "fetch", "step": step_number}
        step_info = f" | Step {step_number}" if step_number is not None else ""
        self.api_logger.info(
            f"API_Call{step_info} | API: Wikipedia Fetch | Article ID: {article_id}",
            extra=log_extra
        )

        try:
            start = time.time()
            params = {
                "action": "query",
                "prop": "extracts|info",
                "pageids": article_id,
                "format": "json",
                "exintro": 1,
                "explaintext": 1,
                "inprop": "url",
            }
            headers = {"User-Agent": "hw4_tourguide/1.0 (student project)"}
            resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params=params,
                timeout=self.timeout,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            page = pages.get(str(article_id)) or next(iter(pages.values()), {})
            extract = page.get("extract") or ""
            details = {
                "id": str(article_id),
                "title": page.get("title"),
                "url": page.get("fullurl") or f"https://en.wikipedia.org/?curid={article_id}",
                "summary": extract,
                "snippet": extract[:500] if extract else "",
                "citations": [],
                "source": "wikipedia",
            }

            elapsed_ms = (time.time() - start) * 1000
            self.api_logger.info(
                f"API_Success | API: Wikipedia Fetch | Article: \"{details.get('title', 'N/A')[:50]}\" | "
                f"Time: {elapsed_ms:.0f}ms",
                extra={**log_extra, "event_tag": "API_Success"}
            )
            return details

        except Exception as exc:
            self.api_logger.warning(
                f"API_Failure | API: Wikipedia Fetch | Article ID: {article_id} | Error: {type(exc).__name__}: {str(exc)[:100]}",
                extra={**log_extra, "event_tag": "API_Failure", "error_type": type(exc).__name__}
            )
            raise


class DuckDuckGoClient:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.api_logger = get_logger("api")

    def search_articles(self, query: str, limit: int = 3, step_number: Optional[int] = None) -> List[Dict[str, Any]]:
        log_extra = {"event_tag": "API_Call", "api_name": "DuckDuckGo", "method": "search", "step": step_number}
        step_info = f" | Step {step_number}" if step_number is not None else ""
        self.api_logger.info(
            f"API_Call{step_info} | API: DuckDuckGo Search | Query: \"{query[:60]}\" | Max Results: {limit}",
            extra=log_extra
        )

        try:
            start = time.time()
            # DDG Instant Answer returns a single best result; we wrap it as a list.
            params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
            headers = {"User-Agent": "hw4_tourguide/1.0 (student project)"}
            resp = requests.get("https://api.duckduckgo.com/", params=params, timeout=self.timeout, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            results: List[Dict[str, Any]] = []
            if data.get("AbstractURL"):
                results.append(
                    {
                        "id": data.get("AbstractURL"),
                        "title": data.get("Heading"),
                        "url": data.get("AbstractURL"),
                        "snippet": data.get("AbstractText"),
                        "source": "duckduckgo",
                    }
                )
            for topic in data.get("RelatedTopics", [])[: max(limit - len(results), 0)]:
                if isinstance(topic, dict) and topic.get("FirstURL"):
                    results.append(
                        {
                            "id": topic.get("FirstURL"),
                            "title": topic.get("Text"),
                            "url": topic.get("FirstURL"),
                            "snippet": topic.get("Text"),
                            "source": "duckduckgo",
                        }
                    )

            elapsed_ms = (time.time() - start) * 1000
            self.api_logger.info(
                f"API_Success | API: DuckDuckGo Search | Results: {len(results)} | Time: {elapsed_ms:.0f}ms",
                extra={**log_extra, "event_tag": "API_Success", "results_count": len(results)}
            )
            return results

        except Exception as exc:
            self.api_logger.warning(
                f"API_Failure | API: DuckDuckGo Search | Error: {type(exc).__name__}: {str(exc)[:100]}",
                extra={**log_extra, "event_tag": "API_Failure", "error_type": type(exc).__name__}
            )
            raise

    def fetch_article(self, article_id: str, step_number: Optional[int] = None) -> Dict[str, Any]:
        # For DDG, fetch is effectively the same as search result
        log_extra = {"event_tag": "API_Call", "api_name": "DuckDuckGo", "method": "fetch", "step": step_number}
        step_info = f" | Step {step_number}" if step_number is not None else ""
        self.api_logger.info(
            f"API_Call{step_info} | API: DuckDuckGo Fetch | Article ID: {article_id}",
            extra=log_extra
        )

        return {
            "id": article_id,
            "title": article_id,
            "url": article_id,
            "summary": "",
            "snippet": "",  # Add snippet field for judge compatibility
            "citations": [],
            "source": "duckduckgo",
        }
