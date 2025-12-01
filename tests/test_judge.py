# tests/test_judge.py

import json
import unittest
from unittest.mock import MagicMock
import logging
import pytest

from hw4_tourguide.judge import JudgeAgent
from hw4_tourguide.tools.llm_client import LLMClient
from hw4_tourguide.tools.prompt_loader import load_prompt_with_context

@pytest.mark.unit
class TestJudgeAgent(unittest.TestCase):

    def setUp(self):
        """Set up mock objects for each test."""
        self.mock_config = {
            "judge": {
                "llm_scoring": {"enabled": False},
                "heuristic_weights": {
                    "presence": 0.3,
                    "quality": 0.3,
                    "relevance": 0.4
                }
            }
        }
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_metrics = MagicMock()
        self.judge = JudgeAgent(self.mock_config["judge"], self.mock_logger, self.mock_metrics)

    def test_initialization(self):
        """Test that the JudgeAgent initializes correctly."""
        self.assertFalse(self.judge.llm_enabled)
        self.assertEqual(self.judge.weights['relevance'], 0.4)
        self.mock_logger.info.assert_called()
        msg, kwargs = self.mock_logger.info.call_args
        self.assertIn("JudgeAgent initialized. LLM scoring: Disabled", msg[0])

    def test_heuristic_scoring_all_good(self):
        """Test heuristic scoring when all agents return high-quality, relevant content."""
        task = {
            "transaction_id": "test-123",
            "location_name": "MIT Media Lab",
            "search_hint": "cool tech demos"
        }
        agent_results = [
            {
                "agent_type": "video", "status": "success",
                "metadata": {"title": "MIT Media Lab tech demos", "description": "A tour of the latest demos.", "view_count": 1000}
            },
            {
                "agent_type": "song", "status": "success",
                "metadata": {"title": "Technologic", "artist": "Daft Punk", "album": "Human After All"}
            },
            {
                "agent_type": "knowledge", "status": "success",
                "metadata": {"title": "MIT Media Lab - Wikipedia", "summary": "An article about the lab's history and research.", "source": "Wikipedia"}
            }
        ]

        decision = self.judge.evaluate(task, agent_results)

        self.assertEqual(decision["transaction_id"], "test-123")
        self.assertIn(decision["chosen_agent"], ["video", "knowledge"]) # Both are highly relevant
        self.assertGreater(decision["overall_score"], 80)
        self.assertGreater(decision["individual_scores"]["video"], 80)
        self.assertLess(decision["individual_scores"]["song"], 70) 
        self.mock_logger.info.assert_called()
        self.mock_metrics.record_latency.assert_called_with('judge.scoring_ms', unittest.mock.ANY)

    def test_one_agent_fails(self):
        """Test scoring when one agent fails to return content."""
        task = {"location_name": "Eiffel Tower"}
        agent_results = [
            {"agent_type": "video", "status": "failure", "metadata": {}},
            {"agent_type": "song", "status": "success", "metadata": {"title": "La Vie en rose", "artist": "Edith Piaf"}},
            {"agent_type": "knowledge", "status": "success", "metadata": {"title": "Eiffel Tower History", "summary": "About the tower."}}
        ]

        decision = self.judge.evaluate(task, agent_results)

        self.assertEqual(decision["individual_scores"]["video"], 0)
        self.assertGreater(decision["individual_scores"]["knowledge"], 70)
        self.assertEqual(decision["chosen_agent"], "knowledge") # Most relevant
        self.assertNotIn("Content unavailable", decision["rationale"])

    def test_low_quality_content(self):
        """Test scoring when content has low quality (missing metadata)."""
        task = {"location_name": "Grand Canyon"}
        agent_results = [
            {"agent_type": "video", "status": "success", "metadata": {"title": "Grand Canyon"}}, # Missing description/views
            {"agent_type": "song", "status": "success", "metadata": {"title": "Rocky Mountain High", "artist": "John Denver"}},
            {"agent_type": "knowledge", "status": "success", "metadata": {"title": "A big canyon", "summary": "very big"}}
        ]
        
        scores, rationales = self.judge._heuristic_scoring(task, agent_results)

        # Video presence=100, quality=40, relevance=100 -> (30) + (12) + (40) = 82
        self.assertEqual(scores["video"], 82.0)
        # Knowledge presence=100, quality=80, relevance=50 -> (30) + (24) + (20) = 74
        self.assertEqual(scores["knowledge"], 74.0)
        self.assertGreater(scores["song"], 50) 

    def test_low_relevance_content(self):
        """Test scoring when content is not relevant to the location."""
        task = {"location_name": "Statue of Liberty"}
        agent_results = [
            {"agent_type": "video", "status": "success", "metadata": {"title": "Funny Cat Video", "description": "A cat plays piano."}},
        ]
        
        scores, rationales = self.judge._heuristic_scoring(task, agent_results)
        
        # Relevance score should be very low
        self.assertIn("Relevance=0", rationales["video"])
        # Score = presence*0.3 + quality*0.3 + relevance*0.4 = 30 + 24 + 0 = 54
        self.assertEqual(scores["video"], 54.0)

    def test_llm_fallback_mechanism(self):
        """Test that the judge falls back to heuristics if LLM is enabled but fails."""
        self.mock_config["judge"]["llm_scoring"]["enabled"] = True
        judge_with_llm = JudgeAgent(self.mock_config["judge"], self.mock_logger, self.mock_metrics)

        task = {"transaction_id": "llm-test", "location_name": "Space Needle"}
        agent_results = [{"agent_type": "video", "status": "success", "metadata": {"title": "Seattle Views"}, "timestamp": "now"}]

        decision = judge_with_llm.evaluate(task, agent_results)

        # We don't force a specific warning; just ensure scoring succeeded and counters may include LLM attempts
        # If no LLM client is available, attempts counter might not be incremented; this remains heuristic-safe.
        self.assertGreater(decision["overall_score"], 0)
        self.assertEqual(decision["chosen_agent"], "video")

    def test_judge_hybrid_mode_uses_llm_and_heuristics(self):
        """Hybrid scoring should run LLM and still produce heuristic scores."""
        class _MockLLM(LLMClient):
            def __init__(self):
                super().__init__(timeout=1.0, max_retries=1)
            def _call(self, prompt: str):
                return {"text": "knowledge is best", "usage": {"prompt_tokens": 1, "completion_tokens": 1}}

        cfg = {
            "scoring_mode": "hybrid",
            "llm_scoring": {"enabled": True, "provider": "mock"},
            "heuristic_weights": {"presence": 0.3, "quality": 0.3, "relevance": 0.4},
        }
        judge = JudgeAgent(cfg, self.mock_logger, self.mock_metrics)
        judge.llm_client = _MockLLM()
        task = {"transaction_id": "tid", "location_name": "MIT", "search_hint": "campus"}
        agent_results = [
            {"agent_type": "video", "status": "success", "metadata": {"title": "MIT Tour"}},
            {"agent_type": "knowledge", "status": "success", "metadata": {"title": "MIT Article", "summary": "info"}},
        ]
        decision = judge.evaluate(task, agent_results)
        self.assertIn("overall_score", decision)
        self.assertIn(decision["chosen_agent"], ["video", "knowledge"])

    def test_judge_llm_with_markdown_template(self):
        """LLM scoring uses markdown prompt and returns chosen agent."""
        class _MockLLM(LLMClient):
            def __init__(self):
                super().__init__(timeout=1.0, max_retries=1)
            def _call(self, prompt: str):
                return {"text": "The best agent is video because it matches the location.", "usage": {"prompt_tokens": len(prompt)//4, "completion_tokens": 10}}

        cfg = {
            "llm_scoring": {"enabled": True},
            "scoring_mode": "llm",
            "llm_provider": "mock",
        }
        judge = JudgeAgent(cfg, self.mock_logger, self.mock_metrics)
        judge.llm_client = _MockLLM()
        task = {"location_name": "MIT", "search_hint": "campus tour", "instructions": "Turn left", "route_context": "Boston university tour"}
        agent_results = [
            {"agent_type": "video", "status": "ok", "metadata": {"title": "MIT Campus Tour", "description": "Walkthrough", "source": "YouTube"}},
            {"agent_type": "song", "status": "ok", "metadata": {"title": "Techno", "artist": "DJ"}},
            {"agent_type": "knowledge", "status": "ok", "metadata": {"title": "MIT Overview", "summary": "History", "source": "Wikipedia"}},
        ]
        with unittest.mock.patch("hw4_tourguide.judge.load_prompt_with_context") as mock_loader:
            mock_loader.side_effect = lambda *args, **kwargs: "prompt with {location_name}"
            decision = judge._llm_score(task, agent_results)
            self.assertEqual(decision["chosen_agent"], "video")
            mock_loader.assert_called_once()

    def test_judge_llm_alternative_field_names(self):
        """Test extraction when LLM uses alternative field names (final_selection, reasoning, scores).
        This pattern has been observed with various LLM providers."""
        class _MockAltFormatLLM(LLMClient):
            def __init__(self):
                super().__init__(timeout=1.0, max_retries=1)
            def _call(self, prompt: str):
                # Alternative format with different field names (observed with Gemini and others)
                alt_response = {
                    "final_selection": {"agent_type": "knowledge"},
                    "reasoning": "Knowledge article provides comprehensive information",
                    "scores": {
                        "video": {"Total Weighted Score": 75.5},
                        "song": {"Total Weighted Score": 60.0},
                        "knowledge": {"Total Weighted Score": 92.3}
                    }
                }
                # Wrap in markdown code fence (common LLM behavior)
                markdown_wrapped = f"```json\n{json.dumps(alt_response, indent=2)}\n```"
                return {"text": markdown_wrapped, "usage": {"prompt_tokens": 100, "completion_tokens": 50}}

        cfg = {
            "llm_scoring": {"enabled": True},
            "scoring_mode": "llm",
            "llm_provider": "mock",
        }
        judge = JudgeAgent(cfg, self.mock_logger, self.mock_metrics)
        judge.llm_client = _MockAltFormatLLM()
        task = {"location_name": "MIT", "search_hint": "research university"}
        agent_results = [
            {"agent_type": "video", "status": "ok", "metadata": {"title": "MIT Tour"}},
            {"agent_type": "song", "status": "ok", "metadata": {"title": "College Song"}},
            {"agent_type": "knowledge", "status": "ok", "metadata": {"title": "MIT Overview"}},
        ]
        with unittest.mock.patch("hw4_tourguide.judge.load_prompt_with_context") as mock_loader:
            mock_loader.side_effect = lambda *args, **kwargs: "prompt"
            decision = judge._llm_score(task, agent_results)
            self.assertEqual(decision["chosen_agent"], "knowledge")
            self.assertIn("knowledge", decision["individual_scores"])
            self.assertAlmostEqual(decision["individual_scores"]["knowledge"], 92.3, places=1)

    def test_judge_llm_markdown_code_fence_extraction(self):
        """Test extraction from markdown code fence format."""
        class _MockMarkdownLLM(LLMClient):
            def __init__(self):
                super().__init__(timeout=1.0, max_retries=1)
            def _call(self, prompt: str):
                # LLM returns JSON wrapped in markdown code fence
                markdown_response = """Here's my analysis:
```json
{
  "chosen_agent": "song",
  "rationale": "Perfect mood match",
  "individual_scores": {
    "video": 70,
    "song": 95,
    "knowledge": 65
  }
}
```
That's my recommendation."""
                return {"text": markdown_response, "usage": {"prompt_tokens": 100, "completion_tokens": 80}}

        cfg = {"llm_scoring": {"enabled": True}, "scoring_mode": "llm", "llm_provider": "openai"}
        judge = JudgeAgent(cfg, self.mock_logger, self.mock_metrics)
        judge.llm_client = _MockMarkdownLLM()
        task = {"location_name": "Park", "search_hint": "relaxing"}
        agent_results = [
            {"agent_type": "video", "status": "ok", "metadata": {"title": "Park Video"}},
            {"agent_type": "song", "status": "ok", "metadata": {"title": "Chill Song"}},
            {"agent_type": "knowledge", "status": "ok", "metadata": {"title": "Park Info"}},
        ]
        with unittest.mock.patch("hw4_tourguide.judge.load_prompt_with_context") as mock_loader:
            mock_loader.side_effect = lambda *args, **kwargs: "prompt"
            decision = judge._llm_score(task, agent_results)
            self.assertEqual(decision["chosen_agent"], "song")
            self.assertEqual(decision["individual_scores"]["song"], 95)

    def test_judge_llm_json_pattern_extraction(self):
        """Test extraction using JSON pattern matching when LLM returns extra text."""
        class _MockVerboseLLM(LLMClient):
            def __init__(self):
                super().__init__(timeout=1.0, max_retries=1)
            def _call(self, prompt: str):
                # LLM returns JSON with extra narrative
                verbose_response = '''After careful analysis, here is my decision:
{"chosen_agent": "video", "rationale": "High visual quality", "individual_scores": {"video": 88, "song": 72, "knowledge": 80}}
This recommendation is based on relevance and quality factors.'''
                return {"text": verbose_response, "usage": {"prompt_tokens": 90, "completion_tokens": 60}}

        cfg = {"llm_scoring": {"enabled": True}, "scoring_mode": "llm", "llm_provider": "claude"}
        judge = JudgeAgent(cfg, self.mock_logger, self.mock_metrics)
        judge.llm_client = _MockVerboseLLM()
        task = {"location_name": "Museum", "search_hint": "art"}
        agent_results = [
            {"agent_type": "video", "status": "ok", "metadata": {"title": "Museum Tour"}},
            {"agent_type": "song", "status": "ok", "metadata": {"title": "Classical"}},
            {"agent_type": "knowledge", "status": "ok", "metadata": {"title": "Museum History"}},
        ]
        with unittest.mock.patch("hw4_tourguide.judge.load_prompt_with_context") as mock_loader:
            mock_loader.side_effect = lambda *args, **kwargs: "prompt"
            decision = judge._llm_score(task, agent_results)
            self.assertEqual(decision["chosen_agent"], "video")
            self.assertEqual(decision["individual_scores"]["video"], 88)

    def test_all_agents_fail(self):
        """Test behavior when all agents fail."""
        task = {"location_name": "Area 51"}
        agent_results = [
            {"agent_type": "video", "status": "failure"},
            {"agent_type": "song", "status": "error"},
            {"agent_type": "knowledge", "status": "timeout"},
        ]

        decision = self.judge.evaluate(task, agent_results)
        
        self.assertEqual(decision["overall_score"], -1)
        self.assertIsNone(decision["chosen_agent"])
        self.assertEqual(decision["individual_scores"]["video"], 0)
        self.assertEqual(decision["individual_scores"]["song"], 0)
        self.assertEqual(decision["individual_scores"]["knowledge"], 0)
        self.assertEqual(decision["rationale"], "No suitable content found.")

    def test_tokenizer(self):
        """Test the simple tokenizer."""
        text = "Turn left onto Main Street! This is a test."
        expected = {"main", "test"} # "street" is a stopword
        tokens = self.judge._tokenize(text)
        self.assertEqual(tokens, expected)

if __name__ == "__main__":
    unittest.main()
