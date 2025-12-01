# src/hw4_tourguide/judge.py

import logging
import time
import re
from typing import Dict, Any, List, Optional

from hw4_tourguide.logger import get_logger
from hw4_tourguide.tools.llm_client import llm_factory, LLMClient, LLMError
from hw4_tourguide.tools.prompt_loader import load_prompt_with_context

# A simple set of English stop words for relevance scoring.
# In a production system, a library like NLTK or SpaCy would be used.
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if", "in", 
    "into", "is", "it", "no", "not", "of", "on", "or", "such", "that", "the", 
    "their", "then", "there", "these", "they", "this", "to", "was", "will", 
    "with", "from", "turn", "left", "right", "onto", "road", "street", "ave",
    "avenue", "blvd", "boulevard", "dr", "drive", "ln", "lane", "rd", "st"
}

class JudgeAgent:
    """
    The JudgeAgent evaluates the content fetched by worker agents and selects the best one.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger, metrics_collector: Optional[Any] = None, secrets_fn: Optional[Any] = None):
        """
        Initializes the JudgeAgent.

        Args:
            config: The configuration dictionary for the judge agent.
            logger: The logger instance.
            metrics_collector: The metrics collector instance for tracking performance.
        """
        self.config = config
        self.logger = logger
        self.metrics_collector = metrics_collector
        self.secrets_fn = secrets_fn or (lambda key: None)

        # Config normalization: accept either legacy judge.* keys or nested llm_scoring/heuristic_weights
        self.scoring_mode = (self.config.get("scoring_mode") or "heuristic").lower()
        llm_config = self.config.get("llm_scoring", {})
        if not llm_config:
            llm_config = {
                "enabled": bool(self.config.get("use_llm", False)),
                "provider": self.config.get("llm_provider", "mock"),
                "timeout": self.config.get("llm_timeout", 30.0),
                "fallback": self.config.get("llm_fallback", True),
                "max_prompt_chars": self.config.get("llm_max_prompt_chars", 4000),
                "max_tokens": self.config.get("llm_max_tokens", None),
            }
        self.llm_enabled = llm_config.get("enabled", False)
        self.llm_max_prompt_chars = int(llm_config.get("max_prompt_chars", 4000))
        self.llm_max_tokens = llm_config.get("max_tokens", None)
        self.llm_tokens_used = 0

        self.weights = self.config.get(
            "heuristic_weights",
            {"presence": 0.3, "quality": 0.3, "relevance": 0.4},
        )
        self.llm_client: Optional[LLMClient] = None
        if self.llm_enabled or self.scoring_mode in {"llm", "hybrid"}:
            try:
                self.llm_client = llm_factory(self.config, self.secrets_fn)
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning(
                    f"LLM factory failed: {exc}; falling back to heuristics",
                    extra={"event_tag": "Judge"},
                )
                self.llm_client = None
        self.logger.info(
            f"JudgeAgent initialized. LLM scoring: {'Enabled' if self.llm_enabled else 'Disabled'}",
            extra={"event_tag": "Judge"},
        )

    def evaluate(self, task: Dict[str, Any], agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates the results from worker agents and returns the judge's decision.

        Args:
            task: The original task dictionary containing location context.
            agent_results: A list of result dictionaries from the worker agents.

        Returns:
            A dictionary containing the judge's decision.
        """
        start_time = time.time()
        transaction_id = task.get('transaction_id', 'unknown')
        step = task.get('step_number', '?')

        # Log input: Agent results summary
        agent_summary = ", ".join(
            f"{r.get('agent_type', '?')}({r.get('status', 'unknown')})"
            for r in agent_results
        )
        self.logger.info(
            f"Judge_Input | TID: {transaction_id} | Step {step} | Agents: {agent_summary}",
            extra={"event_tag": "Judge_Input", "transaction_id": transaction_id, "step": step}
        )

        # Log scoring mode
        self.logger.info(
            f"Judge_Mode | TID: {transaction_id} | Scoring: {self.scoring_mode} | "
            f"LLM: {'enabled' if self.llm_client else 'disabled'}",
            extra={"event_tag": "Judge_Mode", "scoring_mode": self.scoring_mode}
        )

        if self.metrics_collector:
            self.metrics_collector.increment_counter("judge.evals")

        # Always calculate heuristic scores as baseline/fallback
        heuristic_start = time.time()
        heuristic_scores, heuristic_rationales = self._heuristic_scoring(task, agent_results)
        heuristic_time_ms = (time.time() - heuristic_start) * 1000

        # Log heuristic scores
        heuristic_summary = ", ".join(f"{agent}: {score:.1f}" for agent, score in heuristic_scores.items())
        self.logger.info(
            f"Judge_Heuristic | TID: {transaction_id} | Scores: {heuristic_summary} | Time: {heuristic_time_ms:.0f}ms",
            extra={"event_tag": "Judge_Heuristic", "heuristic_scores": heuristic_scores}
        )

        # Default to heuristic
        scores = heuristic_scores
        rationales = heuristic_rationales
        llm_result = None

        # Try LLM scoring if configured
        if self.llm_client and self.scoring_mode in {"llm", "hybrid"}:
            if self.metrics_collector:
                self.metrics_collector.increment_counter("judge.llm_calls_attempted")

            self.logger.info(
                f"Judge_LLM_Call | TID: {transaction_id} | Attempting LLM scoring",
                extra={"event_tag": "Judge_LLM_Call"}
            )

            try:
                llm_start = time.time()
                llm_result = self._llm_score(task, agent_results)
                llm_time_ms = (time.time() - llm_start) * 1000

                if self.metrics_collector:
                    self.metrics_collector.increment_counter("judge.llm_calls_success")

                self.logger.info(
                    f"Judge_LLM_Response | TID: {transaction_id} | Status: SUCCESS | Time: {llm_time_ms:.0f}ms",
                    extra={"event_tag": "Judge_LLM_Response", "llm_time_ms": llm_time_ms, "status": "success"}
                )

                # Use LLM scores if available and mode is "llm" or "hybrid"
                if llm_result.get("individual_scores"):
                    llm_scores_summary = ", ".join(
                        f"{agent}: {score:.1f}" for agent, score in llm_result["individual_scores"].items()
                    )
                    self.logger.info(
                        f"Judge_LLM_Scores | TID: {transaction_id} | Scores: {llm_scores_summary}",
                        extra={"event_tag": "Judge_LLM_Scores", "llm_scores": llm_result["individual_scores"]}
                    )

                    if self.scoring_mode == "llm":
                        # Pure LLM mode: use LLM scores
                        scores = llm_result["individual_scores"]
                        self.logger.info(
                            f"Judge_Scoring | TID: {transaction_id} | Using LLM scores only",
                            extra={"event_tag": "Judge_Scoring"}
                        )
                    elif self.scoring_mode == "hybrid":
                        # Hybrid mode: average heuristic and LLM scores
                        hybrid_scores = {}
                        for agent_type in heuristic_scores:
                            h_score = heuristic_scores.get(agent_type, 0)
                            l_score = llm_result["individual_scores"].get(agent_type, 0)
                            hybrid_scores[agent_type] = (h_score + l_score) / 2.0
                        scores = hybrid_scores

                        hybrid_summary = ", ".join(
                            f"{agent}: {score:.1f}(H:{heuristic_scores.get(agent, 0):.1f}+L:{llm_result['individual_scores'].get(agent, 0):.1f})"
                            for agent, score in hybrid_scores.items()
                        )
                        self.logger.info(
                            f"Judge_Hybrid | TID: {transaction_id} | Scores: {hybrid_summary}",
                            extra={"event_tag": "Judge_Hybrid", "hybrid_scores": hybrid_scores}
                        )

                # Use LLM rationale if available
                if llm_result.get("rationale"):
                    # Store LLM rationale for all agents
                    for agent_type in scores:
                        rationales[agent_type] = llm_result["rationale"]

            except Exception as exc:
                llm_time_ms = (time.time() - llm_start) * 1000 if 'llm_start' in locals() else 0
                self.logger.warning(
                    f"Judge_LLM_Failure | TID: {transaction_id} | Error: {str(exc)[:100]} | "
                    f"Time: {llm_time_ms:.0f}ms | Fallback: heuristic",
                    extra={"event_tag": "Judge_LLM_Failure", "error": str(exc)[:200]}
                )
                if self.metrics_collector:
                    self.metrics_collector.increment_counter("judge.llm_calls_failure")
        elif (self.llm_enabled or self.scoring_mode in {"llm", "hybrid"}) and not self.llm_client:
            # Config requested LLM but none available -> warn once
            self.logger.warning(
                f"TID: {transaction_id} | LLM scoring requested (mode={self.scoring_mode}) but client unavailable; using heuristics.",
                extra={"event_tag": "Judge"},
            )

        # Select best agent based on scores (heuristic or LLM)
        best_agent = None
        highest_score = -1
        for agent_type, score in scores.items():
            if score > highest_score:
                highest_score = score
                best_agent = agent_type

        # If no agent scored meaningfully, signal a failure.
        if highest_score <= 0:
            highest_score = -1
            best_agent = None

        decision = {
            "transaction_id": transaction_id,
            "overall_score": highest_score,
            "chosen_agent": best_agent,
            "individual_scores": scores,
            "rationale": rationales.get(best_agent, "No suitable content found."),
            "per_agent_rationales": rationales,
            "timestamp": time.time()
        }

        # Add the chosen content to the decision
        chosen_content = next((res for res in agent_results if res.get("agent_type") == best_agent), None)
        if chosen_content and chosen_content.get("status") in {"ok", "success"} and chosen_content.get("metadata"):
            decision["chosen_content"] = chosen_content["metadata"]
        else:
            decision["chosen_content"] = {}

        # Metrics: per-agent choice distribution
        if self.metrics_collector and best_agent:
            self.metrics_collector.increment_counter(f"judge.choice.{best_agent}")

        # Calculate margin over second-best
        sorted_scores = sorted(scores.values(), reverse=True)
        second_best_score = sorted_scores[1] if len(sorted_scores) > 1 else 0
        margin = highest_score - second_best_score

        # Log final decision with margin
        self.logger.info(
            f"Judge_Decision | TID: {transaction_id} | CHOSEN: {best_agent} ({highest_score:.1f}) | "
            f"Margin: +{margin:.1f} over second | All Scores: {', '.join(f'{a}:{s:.1f}' for a,s in scores.items())}",
            extra={"event_tag": "Judge_Decision", "chosen_agent": best_agent, "margin": margin}
        )

        if self.metrics_collector:
            duration_ms = (time.time() - start_time) * 1000
            self.metrics_collector.record_latency("judge.scoring_ms", duration_ms)

        # Write checkpoint with step number to avoid overwriting
        # We manually invoke the writer here if available (passed via some mechanism or we rely on orchestrator?)
        # The orchestrator calls checkpoint_writer separately for judge output usually, but let's check base class.
        # Actually, JudgeAgent doesn't inherit BaseAgent and doesn't have a checkpoint_writer field in __init__ currently?
        # Let's check the Orchestrator. Orchestrator calls judge.evaluate, then writes the checkpoint itself.
        # Ah, I need to check orchestrator.py.

        # Log overall completion
        total_time_ms = (time.time() - start_time) * 1000
        self.logger.info(
            f"Judge_Complete | TID: {transaction_id} | Step {step} | Total Time: {total_time_ms:.0f}ms | "
            f"Mode: {self.scoring_mode} | Chosen: {best_agent}",
            extra={"event_tag": "Judge_Complete", "total_time_ms": total_time_ms}
        )

        return decision

    def _heuristic_scoring(self, task: Dict[str, Any], agent_results: List[Dict[str, Any]]) -> (Dict[str, float], Dict[str, str]):
        """
        Calculates scores for each agent result based on heuristics.
        """
        scores = {}
        rationales = {}
        self._validate_agent_results(agent_results)
        
        search_context_str = f"{task.get('location_name', '')} {task.get('search_hint', '')} {task.get('instructions', '')}"
        search_context_tokens = self._tokenize(search_context_str)

        for result in agent_results:
            agent_type = result.get('agent_type', 'unknown')
            
            # 1. Presence Score: accept "ok" or "success"
            status = (result.get("status") or "").lower()
            presence_score = 100.0 if status in {"ok", "success"} and result.get("metadata") else 0.0
            
            if presence_score == 0:
                scores[agent_type] = 0.0
                rationales[agent_type] = "Content unavailable or agent failed."
                continue

            metadata = result.get('metadata', {})
            
            # 2. Quality Score
            quality_score = self._calculate_quality_score(agent_type, metadata)

            # 3. Relevance Score
            content_context_str = f"{metadata.get('title', '')} {metadata.get('description', '')} {metadata.get('tags', '')}"
            content_tokens = self._tokenize(content_context_str)
            relevance_score = self._calculate_relevance_score(search_context_tokens, content_tokens)

            # Final Weighted Score
            final_score = (presence_score * self.weights['presence'] +
                           quality_score * self.weights['quality'] +
                           relevance_score * self.weights['relevance'])
            
            scores[agent_type] = final_score
            rationales[agent_type] = f"Heuristic score breakdown: Presence={presence_score:.0f}, Quality={quality_score:.0f}, Relevance={relevance_score:.0f}."

        return scores, rationales
        
    def _calculate_quality_score(self, agent_type: str, metadata: Dict[str, Any]) -> float:
        """Calculates a quality score based on metadata completeness."""
        score = 0.0
        if agent_type == 'video':
            if metadata.get('title'): score += 40
            if metadata.get('description'): score += 40
            if metadata.get('view_count'): score += 20
        elif agent_type == 'song':
            if metadata.get('title'): score += 40
            if metadata.get('artist'): score += 40
            if metadata.get('album'): score += 20
        elif agent_type == 'knowledge':
            if metadata.get('title'): score += 30
            if metadata.get('summary') or metadata.get('content'): score += 50
            if metadata.get('source'): score += 20
        return score

    def _calculate_relevance_score(self, search_tokens: set, content_tokens: set) -> float:
        """Calculates a relevance score based on keyword overlap."""
        if not search_tokens or not content_tokens:
            return 0.0
        
        # Find intersection of important keywords
        overlap = search_tokens.intersection(content_tokens)
        
        # Score is the percentage of search context words found in the content
        score = (len(overlap) / len(search_tokens)) * 100
        return min(score, 100.0)

    def _tokenize(self, text: str) -> set:
        """A simple tokenizer that converts text to a set of lowercase words, removing stop words."""
        if not text:
            return set()
        # Remove non-alphanumeric characters and split by space
        words = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower()).split()
        return {word for word in words if word not in STOP_WORDS and len(word) > 1}

    def _validate_agent_results(self, agent_results: List[Dict[str, Any]]) -> None:
        """
        Lightweight validation against the agent result contract (required keys only).
        Logs warnings instead of raising to avoid breaking pipeline.
        """
        required_fields = {"agent_type", "status", "metadata", "timestamp"}
        for res in agent_results:
            missing = [f for f in required_fields if f not in res]
            if missing:
                self.logger.warning(
                    f"Agent result missing fields {missing}: {res.get('agent_type', 'unknown')}",
                    extra={"event_tag": "Judge"},
                )
            if not isinstance(res.get("metadata", {}), dict):
                self.logger.warning(
                    f"Agent result metadata not dict: {res.get('agent_type', 'unknown')}",
                    extra={"event_tag": "Judge"},
                )

    def _llm_score(self, task: Dict[str, Any], agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use LLM to score/rank agent outputs. Returns rationale, chosen agent, and individual scores.
        Loads markdown prompt template and substitutes task/agent context.

        Returns:
            {
                "rationale": str,
                "chosen_agent": str,
                "individual_scores": {agent_type: score, ...}
            }
        """
        if not self.llm_client:
            raise LLMError("LLM client not configured")
        sanitized_results = []
        for res in agent_results:
            md = res.get("metadata", {}) if isinstance(res, dict) else {}
            sanitized_results.append(
                {
                    "agent_type": res.get("agent_type"),
                    "title": md.get("title") or "",
                    "description": md.get("description") or md.get("summary") or "",
                    "artist": md.get("artist") or "",
                    "source": md.get("source") or "",
                    "url": md.get("url") or "",
                }
            )
        ctx = {
            "location_name": task.get("location_name"),
            "search_hint": task.get("search_hint", ""),
            "instructions": task.get("instructions", ""),
            "route_context": task.get("route_context", ""),
            "agent_results": sanitized_results,
        }
        prompt = load_prompt_with_context("judge", ctx)
        if len(prompt) > self.llm_max_prompt_chars:
            prompt = prompt[: self.llm_max_prompt_chars]
        llm_response = self.llm_client.query(prompt)
        text = llm_response.get("text", "")
        transaction_id = task.get('transaction_id', 'unknown')

        # Extract JSON from LLM response using same robust strategies as agents
        import json
        import re

        llm_result = {
            "rationale": text[:200] if len(text) > 200 else text,  # Default fallback
            "chosen_agent": None,
            "individual_scores": {}
        }

        # Strategy 1: Try direct JSON parse
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                llm_result["chosen_agent"] = parsed.get("chosen_agent")
                llm_result["rationale"] = parsed.get("rationale", text[:200])
                llm_result["individual_scores"] = parsed.get("individual_scores", {})
                return llm_result
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
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    # Standard format: {"chosen_agent": "video", "rationale": "...", "individual_scores": {...}}
                    if "chosen_agent" in parsed:
                        llm_result["chosen_agent"] = parsed.get("chosen_agent")
                        llm_result["rationale"] = parsed.get("rationale", text[:200])
                        llm_result["individual_scores"] = parsed.get("individual_scores", {})
                        self.logger.debug("Strategy 2: Extracted from standard JSON format")
                        return llm_result

                    # Gemini's alternative format: {"final_selection": {"agent_type": "..."}, "reasoning": "...", "scores": {...}}
                    elif "final_selection" in parsed or "scores" in parsed:
                        # Extract chosen_agent from final_selection.agent_type
                        if "final_selection" in parsed and isinstance(parsed["final_selection"], dict):
                            llm_result["chosen_agent"] = parsed["final_selection"].get("agent_type")

                        # Extract rationale from reasoning field
                        llm_result["rationale"] = parsed.get("reasoning", text[:200])

                        # Extract individual scores from scores.{agent}.Total Weighted Score
                        if "scores" in parsed and isinstance(parsed["scores"], dict):
                            llm_result["individual_scores"] = {}
                            for agent_type, score_data in parsed["scores"].items():
                                if isinstance(score_data, dict):
                                    # Look for Total Weighted Score or other numeric fields
                                    if "Total Weighted Score" in score_data:
                                        llm_result["individual_scores"][agent_type] = float(score_data["Total Weighted Score"])
                                    else:
                                        # Fallback: use first numeric value found
                                        for key, val in score_data.items():
                                            if isinstance(val, (int, float)):
                                                llm_result["individual_scores"][agent_type] = float(val)
                                                break
                                elif isinstance(score_data, (int, float)):
                                    llm_result["individual_scores"][agent_type] = float(score_data)

                        self.logger.debug(f"Strategy 2: Extracted from Gemini's alternative JSON format: chosen={llm_result['chosen_agent']}, scores={llm_result['individual_scores']}")
                        return llm_result
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find JSON object pattern (first { to matching })
        # More sophisticated regex to handle nested objects
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    llm_result["chosen_agent"] = parsed.get("chosen_agent")
                    llm_result["rationale"] = parsed.get("rationale", text[:200])
                    llm_result["individual_scores"] = parsed.get("individual_scores", {})
                    return llm_result
            except json.JSONDecodeError:
                pass

        # Strategy 4: Look for specific patterns and extract values
        # Extract chosen_agent
        chosen_match = re.search(r'"chosen_agent"\s*:\s*"(video|song|knowledge)"', text, re.IGNORECASE)
        if chosen_match:
            llm_result["chosen_agent"] = chosen_match.group(1).lower()

        # Extract rationale
        rationale_match = re.search(r'"rationale"\s*:\s*"([^"]+)"', text, re.DOTALL)
        if rationale_match:
            llm_result["rationale"] = rationale_match.group(1)

        # Extract individual_scores object
        scores_match = re.search(r'"individual_scores"\s*:\s*(\{[^}]+\})', text, re.DOTALL)
        if scores_match:
            try:
                llm_result["individual_scores"] = json.loads(scores_match.group(1))
            except json.JSONDecodeError:
                # Try to extract scores manually
                video_score = re.search(r'"video"\s*:\s*(\d+(?:\.\d+)?)', text)
                song_score = re.search(r'"song"\s*:\s*(\d+(?:\.\d+)?)', text)
                knowledge_score = re.search(r'"knowledge"\s*:\s*(\d+(?:\.\d+)?)', text)
                if video_score or song_score or knowledge_score:
                    llm_result["individual_scores"] = {}
                    if video_score:
                        llm_result["individual_scores"]["video"] = float(video_score.group(1))
                    if song_score:
                        llm_result["individual_scores"]["song"] = float(song_score.group(1))
                    if knowledge_score:
                        llm_result["individual_scores"]["knowledge"] = float(knowledge_score.group(1))

        # Strategy 5: Extract from Gemini's narrative format (NEW - handles Gemini's non-JSON response)
        # Gemini often returns: "**Agent Type**: `video`" and "**Score**: 100/100"
        if not llm_result["chosen_agent"]:
            # Look for **Agent Type**: pattern
            agent_type_match = re.search(r'\*\*Agent Type\*\*:\s*`?(video|song|knowledge)`?', text, re.IGNORECASE)
            if agent_type_match:
                llm_result["chosen_agent"] = agent_type_match.group(1).lower()
                self.logger.debug(f"Strategy 5: Extracted chosen_agent from narrative: {llm_result['chosen_agent']}")

        # Extract numerical scores from narrative (e.g., "**1. Video...**Score**: 100/100")
        if not llm_result["individual_scores"]:
            video_score_match = re.search(r'\*\*1\.\s*Video.*?\*\*Score\*\*:\s*(\d+)/100', text, re.DOTALL | re.IGNORECASE)
            song_score_match = re.search(r'\*\*2\.\s*Song.*?\*\*Score\*\*:\s*(\d+)/100', text, re.DOTALL | re.IGNORECASE)
            knowledge_score_match = re.search(r'\*\*2\.\s*Knowledge.*?\*\*Score\*\*:\s*(\d+)/100', text, re.DOTALL | re.IGNORECASE)

            # Try alternative numbering (Knowledge might be #3)
            if not knowledge_score_match:
                knowledge_score_match = re.search(r'\*\*3\.\s*Knowledge.*?\*\*Score\*\*:\s*(\d+)/100', text, re.DOTALL | re.IGNORECASE)

            if video_score_match or song_score_match or knowledge_score_match:
                llm_result["individual_scores"] = {}
                if video_score_match:
                    llm_result["individual_scores"]["video"] = float(video_score_match.group(1))
                if song_score_match:
                    llm_result["individual_scores"]["song"] = float(song_score_match.group(1))
                if knowledge_score_match:
                    llm_result["individual_scores"]["knowledge"] = float(knowledge_score_match.group(1))
                self.logger.debug(f"Strategy 5: Extracted scores from narrative: {llm_result['individual_scores']}")

        # If we got at least chosen_agent or scores, return partial result
        if llm_result["chosen_agent"] or llm_result["individual_scores"]:
            return llm_result

        # Final fallback: Look for agent mention in text
        for candidate in ("video", "song", "knowledge"):
            if candidate in text.lower():
                llm_result["chosen_agent"] = candidate
                break

        llm_result["rationale"] = text[:200] if len(text) > 200 else text

        # DEBUG: Log parsed LLM scoring result
        step = task.get('step_number', 'unknown')
        scores_str = ", ".join(f"{k}:{v:.1f}" for k, v in llm_result.get("individual_scores", {}).items())
        self.logger.info(
            f"Judge_LLM_ParsedScores | TID: {transaction_id} | Step {step} | location={task.get('location_name')} | "
            f"source=LLM | chosen_agent={llm_result.get('chosen_agent')} | scores=[{scores_str}]",
            extra={"event_tag": "Judge_LLM_ParsedScores"}
        )

        return llm_result
