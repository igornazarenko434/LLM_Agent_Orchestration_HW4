"""
BaseAgent: shared run/search/fetch wrapper with retries, circuit breaker, metrics, and checkpoints.
Concrete agents override `search` and `fetch`.
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable

from hw4_tourguide.logger import get_logger
from hw4_tourguide.file_interface import CheckpointWriter
from hw4_tourguide.tools.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from hw4_tourguide.tools.metrics_collector import MetricsCollector
from hw4_tourguide.tools.llm_client import LLMClient, LLMError
from hw4_tourguide.tools.prompt_loader import load_prompt_with_context


class BaseAgent:
    agent_type: str = "base"

    def __init__(
        self,
        config: Dict[str, Any],
        checkpoint_writer: Optional[CheckpointWriter] = None,
        metrics: Optional[Any] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        mock_mode: bool = False,
        sleep_fn: Callable[[float], None] = time.sleep,
        llm_client: Optional[LLMClient] = None,
   ) -> None:
        self.config = config
        self.checkpoint_writer = checkpoint_writer
        self.metrics = metrics
        self.circuit_breaker = circuit_breaker
        self.mock_mode = mock_mode
        self.sleep_fn = sleep_fn
        self.logger = get_logger(f"agent.{self.agent_type}")
        self.llm_client = llm_client
        # cache task context for ranking hooks
        self._task_context: Dict[str, Any] = {}
        self._queries: List[str] = []
        self._search_calls = 0
        self._metrics = metrics
        self._breaker_enabled = circuit_breaker is not None

    # --- Hooks for concrete agents ---
    def search(self, query: str, task: Dict[str, Any], step_number: Optional[int] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def fetch(self, candidate: Dict[str, Any], task: Dict[str, Any], step_number: Optional[int] = None) -> Dict[str, Any]:
        raise NotImplementedError

    # --- Public entrypoint ---
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        run_start = time.time()
        tid = task.get("transaction_id", "unknown_tid")
        step = task.get("step_number", "?")

        # Log input details
        self.logger.info(
            f"Agent_Input | TID: {tid} | Step {step} | Location: {task.get('location_name', 'N/A')} | "
            f"Search Hint: {task.get('search_hint', 'N/A')[:50]} | Route Context: {task.get('route_context', 'N/A')[:30]}",
            extra={"event_tag": "Agent_Input", "transaction_id": tid, "step": step}
        )

        self._task_context = task
        self._queries = self._build_queries(task)

        # Log query generation
        query_mode = "LLM" if (self.config.get("use_llm_for_queries") and self.llm_client) else "Heuristic"
        self.logger.info(
            f"Agent_Queries | TID: {tid} | Mode: {query_mode} | Count: {len(self._queries)} | Queries: {self._queries}",
            extra={"event_tag": "Agent_Queries", "query_mode": query_mode, "query_count": len(self._queries)}
        )

        search_candidates_map: Dict[str, Any] = {}
        for idx, query in enumerate(self._queries, 1):
            # Note: self.search is a hook implemented by concrete agent subclasses
            if self._exceeds_search_cap():
                self.logger.warning(
                    f"Agent_SearchCap | TID: {tid} | {self.agent_type.title()} search cap reached at query {idx}/{len(self._queries)}",
                    extra={"event_tag": "Agent_SearchCap"},
                )
                break

            search_start = time.time()
            candidates = self._with_retries(
                "search",
                lambda step_number=None, q=query: self.search(q, task, step_number=step_number),
                task_context=task # Pass task context
            )
            search_time_ms = (time.time() - search_start) * 1000

            # Log search results
            cand_count = len(candidates) if candidates else 0
            self.logger.info(
                f"Agent_Search | TID: {tid} | Query {idx}/{len(self._queries)}: \"{query[:60]}\" | "
                f"Found: {cand_count} candidates | Time: {search_time_ms:.0f}ms",
                extra={"event_tag": "Agent_Search", "candidates_found": cand_count, "search_time_ms": search_time_ms}
            )

            if candidates:
                for cand in candidates:
                    # Use a unique key to deduplicate candidates across query variants
                    key = cand.get("id") or cand.get("url")
                    if key and key not in search_candidates_map:
                        search_candidates_map[key] = cand

        search_candidates = list(search_candidates_map.values())
        total_unique = len(search_candidates)

        self._write_checkpoint(tid, f"02_agent_search_{self.agent_type}_step_{step}.json", search_candidates)

        if search_candidates is None or len(search_candidates) == 0:
            self.logger.warning(
                f"Agent_NoResults | TID: {tid} | Step {step} | No candidates found after {len(self._queries)} queries",
                extra={"event_tag": "Agent_NoResults"}
            )
            return self._result_unavailable(
                task,
                reason="No candidates found",
            )

        # Log candidate selection
        selected = self.select_candidate(search_candidates)
        selected_title = selected.get("title", selected.get("name", "unknown"))
        self.logger.info(
            f"Agent_Select | TID: {tid} | Selected: \"{selected_title[:60]}\" from {total_unique} candidates",
            extra={"event_tag": "Agent_Select", "total_candidates": total_unique}
        )

        # Log fetch attempt
        fetch_start = time.time()
        fetch_payload = self._with_retries(
            "fetch",
            lambda step_number=None: self.fetch(selected, task, step_number=step_number),
            task_context=task # Pass task context
        )
        fetch_time_ms = (time.time() - fetch_start) * 1000

        if fetch_payload is None:
            self.logger.error(
                f"Agent_FetchFailed | TID: {tid} | Failed to fetch: \"{selected_title[:60]}\" | Time: {fetch_time_ms:.0f}ms",
                extra={"event_tag": "Agent_FetchFailed", "fetch_time_ms": fetch_time_ms}
            )
            return self._result_unavailable(
                task,
                reason="Failed to fetch candidate",
            )

        self.logger.info(
            f"Agent_Fetch | TID: {tid} | Success: \"{selected_title[:60]}\" | Time: {fetch_time_ms:.0f}ms",
            extra={"event_tag": "Agent_Fetch", "fetch_time_ms": fetch_time_ms, "status": "success"}
        )

        self._write_checkpoint(tid, f"03_agent_fetch_{self.agent_type}_step_{step}.json", fetch_payload)

        now = datetime.now(timezone.utc).isoformat()
        reasoning = fetch_payload.get("reasoning") or f"{self.agent_type.title()} content selected for {task.get('location_name')}"
        result = {
            "agent_type": self.agent_type,
            "status": "ok",
            "metadata": fetch_payload,
            "reasoning": reasoning,
            "timestamp": now,
            "error": None,
        }

        # Log completion
        total_time_ms = (time.time() - run_start) * 1000
        self.logger.info(
            f"Agent_Complete | TID: {tid} | Status: ok | Total Time: {total_time_ms:.0f}ms | "
            f"Queries: {len(self._queries)} | Candidates: {total_unique} | Selected: \"{selected_title[:40]}\"",
            extra={"event_tag": "Agent_Complete", "status": "ok", "total_time_ms": total_time_ms}
        )

        return result

    # --- Helpers ---
    def select_candidate(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        ranked = self._rank_candidates(candidates)
        return ranked[0]

    def _rank_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Default: keep original order
        return candidates

    def _convert_array_to_dict(self, array_data: list) -> Dict[str, Any]:
        """
        Convert array of query objects OR strings to expected dict format.
        Handles formats like:
        - ["query1", "query2", ...]
        - [{"query": "...", "rationale": "..."}, ...]
        """
        if not isinstance(array_data, list):
            return {"queries": [], "reasoning": "Invalid format"}

        queries = []
        reasoning_parts = []

        for item in array_data:
            if isinstance(item, str):
                # Handle plain string queries
                if item.strip():
                    queries.append(item.strip())
            elif isinstance(item, dict):
                # Extract query string
                query = item.get("query", "")
                if query:
                    queries.append(query)
                # Extract reasoning/rationale/description/explanation/quality_reflection
                reason = item.get("rationale") or item.get("reasoning") or item.get("description") or item.get("explanation") or item.get("quality_reflection") or ""
                if reason:
                    reasoning_parts.append(reason)

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Converted from array format"
        return {"queries": queries, "reasoning": reasoning}

    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response, handling markdown code fences and explanatory text.
        Tries multiple strategies to be resilient to various LLM response formats.
        """
        import re

        # Strategy 1: Try direct JSON parse
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return self._convert_array_to_dict(data)
            return data
        except json.JSONDecodeError:
            pass

        # Strategy 2: Strip markdown code fences (```json ... ```)
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line if it's ```json or ```
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

            try:
                result = json.loads(cleaned)
                # If result is a list (array format), convert to dict
                if isinstance(result, list):
                    return self._convert_array_to_dict(result)
                return result
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find JSON array pattern (first [ to matching ])
        array_match = re.search(r'\[[^\[\]]*(?:\{[^\[\]]*\}[^\[\]]*)*\]', text, re.DOTALL)
        if array_match:
            try:
                result = json.loads(array_match.group(0))
                if isinstance(result, list):
                    return self._convert_array_to_dict(result)
                return result
            except json.JSONDecodeError:
                pass

        # Strategy 4: Find JSON object pattern (first { to matching })
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        # Strategy 5: Look for "queries": [...] pattern and construct minimal JSON
        queries_match = re.search(r'"queries"\s*:\s*\[(.*?)\]', text, re.DOTALL)
        if queries_match:
            try:
                # Extract just the queries array and construct a minimal JSON
                queries_str = queries_match.group(0)
                minimal_json = "{" + queries_str + ', "reasoning": "extracted from unstructured response"}'
                return json.loads(minimal_json)
            except json.JSONDecodeError:
                pass

        # Strategy 6: Handle array of {query, rationale} objects (Claude sometimes returns this)
        # Example: [{"query": "...", "rationale": "..."}, ...]
        # Convert to {"queries": [...], "reasoning": "..."}
        array_match = re.search(r'\[\s*\{[^\[\]]*"query"[^\[\]]*\}[^\[\]]*\]', text, re.DOTALL)
        if array_match:
            try:
                array_data = json.loads(array_match.group(0))
                if isinstance(array_data, list) and all(isinstance(item, dict) and "query" in item for item in array_data):
                    # Convert to expected format
                    queries = [item["query"] for item in array_data]
                    reasoning = "; ".join(item.get("rationale", item.get("reasoning", "")) for item in array_data if item.get("rationale") or item.get("reasoning"))
                    return {"queries": queries, "reasoning": reasoning or "Converted from array format"}
            except json.JSONDecodeError:
                pass

        # All strategies failed
        raise LLMError(f"Could not extract JSON from LLM response. Response preview: {text[:200]}")

    def _build_queries(self, task: Dict[str, Any]) -> List[str]:
        """
        Build search queries. Try LLM path first (config + client), fall back to heuristics.
        """
        use_llm = bool(self.config.get("use_llm_for_queries")) and self.llm_client is not None
        if use_llm:
            try:
                return self._build_queries_with_llm(task)
            except Exception as exc:
                step = task.get('step_number', 'unknown')
                self.logger.warning(
                    f"{self.agent_type.title()} LLM query gen failed | Step {step} | Error: {exc} | Falling back to heuristic",
                    extra={"event_tag": "Agent"},
                )
                self._increment_counter("llm_fallback.query_generation")
        return self._build_queries_heuristic(task)

    def _build_queries_heuristic(self, task: Dict[str, Any]) -> List[str]:
        """
        Lightweight query expansion (no LLM): generate distinct, targeted variants.
        Strategy:
        1. Specific: "{location}, {context}" (e.g. "Huberman St, Tel Aviv")
        2. Activity: "{location} {keyword}" (e.g. "Huberman St walking tour")
        3. Broad: "{context} {keyword}" (e.g. "Tel Aviv walking tour")
        """
        location = task.get("location_name") or ""
        context = task.get("route_context") or ""
        
        # Determine keyword based on agent type
        keyword = ""
        if self.agent_type == "video":
            keyword = "walking tour"
        elif self.agent_type == "song":
            keyword = "music"
        elif self.agent_type == "knowledge":
            keyword = "history"

        variants = []
        
        # 1. Specific Entity (Best for Knowledge/Maps)
        if location and context:
            variants.append(f"{location}, {context}")
        elif location:
            variants.append(location)

        # 2. Activity/Topic (Best for Video/Song)
        if location and keyword:
            variants.append(f"{location} {keyword}")

        # 3. Broad Context (Fallback for when location is too specific)
        if context and keyword:
            variants.append(f"{context} {keyword}")
        elif context:
            variants.append(context)

        # Deduplicate while preserving order
        seen = set()
        uniq = []
        for q in variants:
            q = q.strip()
            if q and q not in seen:
                seen.add(q)
                uniq.append(q)
        
        # Fallback if nothing generated
        return uniq or [location or context or "travel guide"]

    def _build_queries_with_llm(self, task: Dict[str, Any]) -> List[str]:
        """
        Use LLM prompt + JSON response to generate search queries.
        Expected JSON shape: {"queries": ["q1", "q2"], "reasoning": "..."}
        """
        if not self.llm_client:
            raise LLMError("LLM client unavailable")

        start = time.monotonic()
        ctx = dict(task)
        ctx.setdefault("search_limit", self.config.get("search_limit"))
        prompt = load_prompt_with_context(self.agent_type, ctx)
        llm_resp = self.llm_client.query(prompt)
        duration_ms = (time.monotonic() - start) * 1000
        self._record_latency("llm.query_generation_ms", start)
        self._record_latency(f"agent.{self.agent_type}.llm_query_ms", start)
        self._increment_counter("llm_calls.query_generation")

        text = llm_resp.get("text") if isinstance(llm_resp, dict) else None
        if not text:
            raise LLMError("LLM response missing text")

        # Try to extract JSON from response (handles LLMs that add explanatory text)
        try:
            parsed = self._extract_json_from_response(text)
        except Exception as e:
            # Log the raw LLM response for debugging
            self.logger.error(
                f"LLM JSON extraction failed for {task.get('location_name')} | error={str(e)} | raw_response={text[:500]}",
                extra={"event_tag": "Agent_LLM_Parse_Error"},
            )
            raise

        # Handle different field names (Gemini uses "search_queries", others use "queries")
        queries = None
        if isinstance(parsed, dict):
            queries = parsed.get("queries") or parsed.get("search_queries")

        if not queries or not isinstance(queries, list):
            # Log the parsed structure and raw response for debugging
            self.logger.error(
                f"LLM response missing valid queries list for {task.get('location_name')} | parsed_type={type(parsed).__name__} | parsed_keys={list(parsed.keys()) if isinstance(parsed, dict) else 'N/A'} | queries_type={type(queries).__name__ if queries else 'None'} | raw_response={text[:500]}",
                extra={"event_tag": "Agent_LLM_Validation_Error"},
            )
            raise LLMError("LLM response missing 'queries' or 'search_queries' list")

        # Deduplicate, trim, and enforce search_limit
        seen = set()
        cleaned: List[str] = []
        limit = int(self.config.get("search_limit", len(queries)))
        for q in queries:
            # Handle both string queries and object queries like {"query": "...", ...}
            if isinstance(q, dict):
                q = q.get("query", "")
            if not isinstance(q, str):
                continue
            q = q.strip()
            if not q or q in seen:
                continue
            cleaned.append(q)
            seen.add(q)
            if len(cleaned) >= limit:
                break

        if not cleaned:
            raise LLMError("LLM returned no usable queries")

        self.logger.info(
            f"LLM query generation for {task.get('location_name')} | tid={task.get('transaction_id')} | queries={len(cleaned)} | ms={duration_ms:.1f}",
            extra={"event_tag": "Agent"},
        )

        # DEBUG: Log actual queries generated by LLM
        queries_str = " | ".join(f'"{q}"' for q in cleaned)
        step = task.get('step_number', 'unknown')
        self.logger.info(
            f"Agent_LLM_Queries | {self.agent_type} | Step {step} | location={task.get('location_name')} | "
            f"source=LLM | queries=[{queries_str}]",
            extra={"event_tag": "Agent_LLM_Queries"}
        )

        return cleaned

    def _with_retries(self, phase: str, func: Callable[..., Any], task_context: Optional[Dict[str, Any]] = None) -> Any:
        attempts = int(self.config.get("retry_attempts", 1))
        backoff = self.config.get("retry_backoff", "exponential")
        timeout = float(self.config.get("timeout", 10.0))
        
        step_number = task_context.get("step_number") if task_context else None
        log_extra = {"event_tag": "Agent", "step": step_number, "transaction_id": task_context.get("transaction_id")}

        for attempt in range(attempts):
            start = time.monotonic()
            try:
                # Modify func to accept step_number if it needs it, or use lambda to wrap
                if self.circuit_breaker:
                    # func might be a lambda. If func takes step_number, we need to pass it.
                    # This requires func to be designed to accept it.
                    result = self.circuit_breaker.call(lambda: func(step_number=step_number))
                else:
                    result = func(step_number=step_number)
                self._record_latency(f"agent.{self.agent_type}.{phase}_ms", start)
                if phase == "search":
                    self._search_calls += 1
                self._increment_counter(f"api_calls.{self.agent_type}")
                return result
            except CircuitBreakerOpenError:
                self.logger.warning(
                    f"Circuit open for {self.agent_type}, phase={phase}",
                    extra=log_extra,
                )
                return None
            except Exception as exc:
                self.logger.warning(
                    f"{self.agent_type.title()} {phase} failed (attempt {attempt+1}/{attempts}): {exc}",
                    extra=log_extra,
                )
                if attempt == attempts - 1:
                    return None
                delay = self._compute_backoff(backoff, attempt, timeout)
                self.sleep_fn(delay)
        return None

    def _compute_backoff(self, mode: str, attempt: int, timeout: float) -> float:
        if mode == "linear":
            return min(timeout, 1.0 * (attempt + 1))
        # exponential default
        return min(timeout, 0.5 * (2 ** attempt))

    def _write_checkpoint(self, transaction_id: str, filename: str, payload: Any) -> None:
        if not self.checkpoint_writer:
            return
        try:
            self.checkpoint_writer.write(transaction_id, filename, payload)
        except Exception:
            # Avoid failing the agent on checkpoint errors
            self.logger.warning(
                f"Failed to write checkpoint {filename} for {transaction_id}",
                extra={"event_tag": "Agent"},
            )

    def _result_unavailable(self, task: Dict[str, Any], reason: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "agent_type": self.agent_type,
            "status": "unavailable",
            "metadata": {"title": "", "url": "", "reason": reason},
            "reasoning": reason,
            "timestamp": now,
            "error": reason,
        }

    def _increment_counter(self, name: str) -> None:
        if not self._metrics:
            return
        try:
            self._metrics.increment_counter(name)
        except Exception:
            pass

    def _record_latency(self, name: str, start_monotonic: float) -> None:
        if not self._metrics:
            return
        try:
            duration_ms = (time.monotonic() - start_monotonic) * 1000
            self._metrics.record_latency(name, duration_ms)
        except Exception:
            pass

    def _exceeds_search_cap(self) -> bool:
        cap = self.config.get("max_search_calls_per_run")
        if cap is None:
            return False
        try:
            return self._search_calls >= int(cap)
        except Exception:
            return False
