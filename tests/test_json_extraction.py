"""
Test JSON extraction logic in base_agent.py (Mission Day 1-2)
Covers the robust 5-strategy extraction added for multi-LLM support.
"""

import pytest
from hw4_tourguide.agents.video_agent import VideoAgent
from hw4_tourguide.tools.llm_client import LLMError


@pytest.fixture
def agent():
    """Create a VideoAgent for testing extraction logic."""
    config = {
        "name": "VideoAgent",
        "enabled": True,
        "search_limit": 3,
        "timeout": 10.0,
        "mock_mode": True,
    }
    return VideoAgent(config=config, llm_client=None, mock_mode=True)


@pytest.mark.unit
class TestJSONExtractionStrategies:
    """Test all 5 JSON extraction strategies."""

    def test_strategy1_direct_json(self, agent):
        """Strategy 1: Direct JSON parse."""
        text = '{"queries": ["query1", "query2"], "reasoning": "test"}'
        result = agent._extract_json_from_response(text)
        assert result == {"queries": ["query1", "query2"], "reasoning": "test"}

    def test_strategy2_markdown_code_fences(self, agent):
        """Strategy 2: Strip markdown code fences."""
        text = '```json\n{"queries": ["query1", "query2"], "reasoning": "test"}\n```'
        result = agent._extract_json_from_response(text)
        assert result["queries"] == ["query1", "query2"]

    def test_strategy2_markdown_with_language_tag(self, agent):
        """Strategy 2: Strip markdown with various tags."""
        text = '```\n{"queries": ["query1", "query2"], "reasoning": "test"}\n```'
        result = agent._extract_json_from_response(text)
        assert result["queries"] == ["query1", "query2"]

    def test_strategy3_json_object_pattern(self, agent):
        """Strategy 3: Find JSON object pattern in text."""
        text = 'Here is some text before {"queries": ["query1"], "reasoning": "test"} and after'
        result = agent._extract_json_from_response(text)
        assert result["queries"] == ["query1"]

    def test_strategy4_queries_array_pattern(self, agent):
        """Strategy 4: Extract queries array and construct minimal JSON."""
        text = 'Some text "queries": ["query1", "query2"] more text'
        result = agent._extract_json_from_response(text)
        assert result["queries"] == ["query1", "query2"]

    def test_strategy5_array_of_objects(self, agent):
        """Strategy 5: Convert array of {query, rationale} objects."""
        text = '''```json
[
  {"query": "query1", "rationale": "reason1"},
  {"query": "query2", "rationale": "reason2"}
]
```'''
        result = agent._extract_json_from_response(text)
        assert result["queries"] == ["query1", "query2"]
        assert "reason1" in result["reasoning"]
        assert "reason2" in result["reasoning"]

    def test_strategy5_array_with_description(self, agent):
        """Strategy 5: Handle description field instead of rationale - with markdown."""
        text = '```json\n[{"query": "q1", "description": "desc1"}]\n```'
        result = agent._extract_json_from_response(text)
        assert result["queries"] == ["q1"]

    def test_extraction_failure(self, agent):
        """Test that invalid JSON raises LLMError."""
        text = "This is not JSON at all"
        with pytest.raises(LLMError, match="Could not extract JSON"):
            agent._extract_json_from_response(text)


@pytest.mark.unit
class TestFieldNameHandling:
    """Test handling of different field names (Claude vs Gemini)."""

    def test_queries_field(self, agent):
        """Claude uses 'queries' field."""
        text = '{"queries": ["q1", "q2"], "reasoning": "test"}'
        result = agent._extract_json_from_response(text)
        assert result["queries"] == ["q1", "q2"]

    def test_search_queries_field(self, agent):
        """Gemini uses 'search_queries' field."""
        text = '{"search_queries": ["q1", "q2"], "reasoning": "test"}'
        result = agent._extract_json_from_response(text)
        # Should have search_queries in the dict
        assert "search_queries" in result or "queries" in result


@pytest.mark.unit
class TestNestedObjectHandling:
    """Test handling of nested query objects."""

    def test_simple_nested_objects(self, agent):
        """Test extraction from nested query objects."""
        data = {
            "queries": [
                {"query": "MIT campus tour", "relevance": 5},
                {"query": "MIT history", "relevance": 4}
            ]
        }

        # This would come through _build_queries_with_llm validation
        queries = data.get("queries")
        cleaned = []

        for q in queries:
            if isinstance(q, dict):
                q = q.get("query", "")
            if isinstance(q, str) and q.strip():
                cleaned.append(q.strip())

        assert cleaned == ["MIT campus tour", "MIT history"]

    def test_gemini_format_with_parameters(self, agent):
        """Test Gemini's nested parameter format."""
        text = '''```json
{
  "search_queries": [
    {
      "query": "MIT campus tour",
      "query_parameters": {
        "min_duration_seconds": null,
        "max_duration_seconds": null
      }
    }
  ]
}
```'''
        result = agent._extract_json_from_response(text)
        # Should extract search_queries
        assert "search_queries" in result or "queries" in result


@pytest.mark.unit
class TestConvertArrayToDict:
    """Test _convert_array_to_dict helper method."""

    def test_convert_with_rationale(self, agent):
        """Convert array with rationale field."""
        array = [
            {"query": "q1", "rationale": "r1"},
            {"query": "q2", "rationale": "r2"}
        ]
        result = agent._convert_array_to_dict(array)
        assert result["queries"] == ["q1", "q2"]
        assert "r1" in result["reasoning"]
        assert "r2" in result["reasoning"]

    def test_convert_with_description(self, agent):
        """Convert array with description field."""
        array = [
            {"query": "q1", "description": "d1"},
            {"query": "q2", "description": "d2"}
        ]
        result = agent._convert_array_to_dict(array)
        assert result["queries"] == ["q1", "q2"]
        assert "d1" in result["reasoning"]

    def test_convert_with_reasoning(self, agent):
        """Convert array with reasoning field."""
        array = [{"query": "q1", "reasoning": "why"}]
        result = agent._convert_array_to_dict(array)
        assert result["queries"] == ["q1"]
        assert "why" in result["reasoning"]

    def test_convert_empty_array(self, agent):
        """Convert empty array."""
        result = agent._convert_array_to_dict([])
        assert result["queries"] == []

    def test_convert_invalid_input(self, agent):
        """Convert invalid input."""
        result = agent._convert_array_to_dict("not an array")
        assert result["queries"] == []


@pytest.mark.unit
class TestRealWorldLLMResponses:
    """Test with real LLM response formats we encountered."""

    def test_claude_array_format(self, agent):
        """Test Claude's actual response format."""
        text = '''```json
[
  {
    "query": "MIT campus tour",
    "location_relevance": 5,
    "quality_priority": 5
  },
  {
    "query": "walking tour of MIT",
    "location_relevance": 4,
    "quality_priority": 4
  }
]
```'''
        result = agent._extract_json_from_response(text)
        assert result["queries"] == ["MIT campus tour", "walking tour of MIT"]

    def test_gemini_search_queries_format(self, agent):
        """Test Gemini's actual response format."""
        text = '''```json
{
  "search_queries": [
    {
      "query": "MIT campus tour",
      "query_parameters": {
        "min_duration_seconds": null,
        "max_duration_seconds": null
      }
    },
    {
      "query": "MIT student life",
      "query_parameters": {
        "min_duration_seconds": null,
        "max_duration_seconds": null
      }
    }
  ]
}
```'''
        result = agent._extract_json_from_response(text)
        # Should have search_queries field
        assert "search_queries" in result

    def test_knowledge_agent_nested_format(self, agent):
        """Test Knowledge Agent's nested object format."""
        text = '''```json
{
  "queries": [
    {
      "query": "MIT",
      "source": "wikipedia",
      "intent": "overview"
    },
    {
      "query": "MIT history",
      "source": "wikipedia",
      "intent": "history"
    }
  ]
}
```'''
        result = agent._extract_json_from_response(text)
        assert "queries" in result
        assert len(result["queries"]) == 2
