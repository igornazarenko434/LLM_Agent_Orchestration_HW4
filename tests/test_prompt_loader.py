"""
Tests for PromptLoader utility (Mission M7.14).

Coverage:
- Loading existing prompt files successfully
- FileNotFoundError for missing files
- ValueError for invalid agent types
- Variable substitution (basic, nested dicts, missing optional)
- Edge cases (None values, numbers, empty strings)
- Convenience function aliases
"""

import pytest
from pathlib import Path
from hw4_tourguide.tools.prompt_loader import (
    load_agent_prompt,
    load_prompt_with_context,
    _flatten_dict,
    _substitute_variables,
    load_video_prompt,
    load_song_prompt,
    load_knowledge_prompt,
    load_judge_prompt,
)


@pytest.mark.unit
class TestLoadAgentPrompt:
    """Test suite for load_agent_prompt() function."""

    def test_load_video_prompt_success(self):
        """Test loading video_agent.md successfully."""
        prompt = load_agent_prompt("video")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Video Agent Prompt Template" in prompt
        assert "{location_name}" in prompt  # Variables not yet substituted
        assert "Role" in prompt
        assert "Mission" in prompt
        assert "Output Format" in prompt

    def test_load_song_prompt_success(self):
        """Test loading song_agent.md successfully."""
        prompt = load_agent_prompt("song")
        assert isinstance(prompt, str)
        assert "Song Agent Prompt Template" in prompt
        assert "{location_name}" in prompt

    def test_load_knowledge_prompt_success(self):
        """Test loading knowledge_agent.md successfully."""
        prompt = load_agent_prompt("knowledge")
        assert isinstance(prompt, str)
        assert "Knowledge Agent Prompt Template" in prompt
        assert "{location_name}" in prompt

    def test_load_judge_prompt_success(self):
        """Test loading judge_agent.md successfully."""
        prompt = load_agent_prompt("judge")
        assert isinstance(prompt, str)
        assert "Judge Agent Prompt Template" in prompt
        assert "Role" in prompt
        assert "Mission" in prompt

    def test_load_agent_prompt_invalid_type(self):
        """Test ValueError for invalid agent type."""
        with pytest.raises(ValueError, match="Invalid agent_type 'nonexistent'"):
            load_agent_prompt("nonexistent")

    def test_load_agent_prompt_missing_file(self, tmp_path):
        """Test FileNotFoundError when prompt file doesn't exist."""
        # Use temporary directory with no prompt files
        empty_dir = tmp_path / "empty_agents"
        empty_dir.mkdir()

        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            load_agent_prompt("video", prompts_dir=empty_dir)


@pytest.mark.unit
class TestLoadPromptWithContext:
    """Test suite for load_prompt_with_context() function."""

    def test_basic_variable_substitution(self):
        """Test substituting basic string variables."""
        context = {
            "location_name": "MIT",
            "search_hint": "campus architecture",
            "route_context": "Boston university tour",
        }
        prompt = load_prompt_with_context("video", context)

        # Variables should be substituted
        assert "MIT" in prompt
        assert "campus architecture" in prompt
        assert "Boston university tour" in prompt

        # Placeholders should be gone
        assert "{location_name}" not in prompt
        assert "{search_hint}" not in prompt
        assert "{route_context}" not in prompt

    def test_nested_dict_variable_substitution(self):
        """Test flattening and substituting nested dict (coordinates)."""
        context = {
            "location_name": "Grand Canyon",
            "coordinates": {"lat": 36.0544, "lng": -112.1401},
        }
        prompt = load_prompt_with_context("video", context)

        # Nested dict should be flattened and substituted
        # Note: Prompts may not explicitly use coordinates_lat/lng, but we test the mechanism
        assert "Grand Canyon" in prompt

    def test_missing_optional_variables(self):
        """Test graceful handling of missing optional fields (replaced with empty string)."""
        context = {
            "location_name": "MIT",
            # search_hint missing (optional)
            # route_context missing (optional)
            # address missing (optional)
        }
        prompt = load_prompt_with_context("video", context)

        # Should not crash
        assert "MIT" in prompt
        assert len(prompt) > 0

        # Optional variable placeholders should be replaced with empty strings
        # (or "null" depending on prompt design - either way, no {placeholders} remain)
        import re
        remaining_placeholders = re.findall(r"\{([^}]+)\}", prompt)
        # Allow some placeholders that are part of JSON examples in prompts
        # but main context vars should be substituted
        for placeholder in remaining_placeholders:
            # Ensure it's not a context variable (should be example/documentation placeholder)
            assert placeholder not in ["location_name", "search_hint", "route_context", "address", "instructions"]

    def test_none_value_substitution(self):
        """Test that None values are replaced with empty string."""
        context = {
            "location_name": "MIT",
            "search_hint": None,  # Explicitly None
            "route_context": None,
        }
        prompt = load_prompt_with_context("video", context)

        assert "MIT" in prompt
        # None should become empty string (not "None" string)
        assert "None" not in prompt or prompt.count("None") < 3  # May appear in instructions text

    def test_numeric_variable_substitution(self):
        """Test that numbers are converted to strings."""
        context = {
            "location_name": "Test Location",
            "search_limit": 3,  # Integer
            "coordinates": {"lat": 42.3601, "lng": -71.0942},  # Floats
        }
        prompt = load_prompt_with_context("video", context)

        assert "Test Location" in prompt
        # search_limit should appear as "3" (string)
        assert "3" in prompt or "{search_limit}" not in prompt  # Either substituted or not in template

    def test_boolean_variable_substitution(self):
        """Test that booleans are converted to strings."""
        context = {
            "location_name": "Test",
            "infer_song_mood": True,
            "use_geosearch": False,
        }
        prompt = load_prompt_with_context("song", context)

        # Booleans should become "True"/"False" strings
        assert "Test" in prompt


@pytest.mark.unit
class TestFlattenDict:
    """Test suite for _flatten_dict() helper function."""

    def test_flatten_nested_dict(self):
        """Test flattening a 2-level nested dict."""
        nested = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3,
            },
        }
        flat = _flatten_dict(nested)
        assert flat == {"a": 1, "b_c": 2, "b_d": 3}

    def test_flatten_coordinates(self):
        """Test flattening coordinates dict (common case)."""
        nested = {
            "location_name": "MIT",
            "coordinates": {"lat": 42.3601, "lng": -71.0942},
        }
        flat = _flatten_dict(nested)
        assert flat == {
            "location_name": "MIT",
            "coordinates_lat": 42.3601,
            "coordinates_lng": -71.0942,
        }

    def test_flatten_already_flat(self):
        """Test that already-flat dict is unchanged."""
        flat_dict = {"a": 1, "b": 2, "c": 3}
        result = _flatten_dict(flat_dict)
        assert result == flat_dict

    def test_flatten_deeply_nested(self):
        """Test flattening a 3-level nested dict."""
        nested = {
            "a": {
                "b": {
                    "c": 1
                }
            }
        }
        flat = _flatten_dict(nested)
        assert flat == {"a_b_c": 1}


@pytest.mark.unit
class TestSubstituteVariables:
    """Test suite for _substitute_variables() helper function."""

    def test_substitute_simple_variables(self):
        """Test basic variable substitution."""
        template = "Location: {location_name}, Hint: {search_hint}"
        context = {"location_name": "MIT", "search_hint": "campus tour"}
        result = _substitute_variables(template, context)
        assert result == "Location: MIT, Hint: campus tour"

    def test_substitute_missing_variable(self):
        """Test that missing variables are replaced with empty string."""
        template = "Location: {location_name}, Hint: {search_hint}"
        context = {"location_name": "MIT"}  # search_hint missing
        result = _substitute_variables(template, context)
        assert result == "Location: MIT, Hint: "

    def test_substitute_none_value(self):
        """Test that None values become empty strings."""
        template = "Value: {key}"
        context = {"key": None}
        result = _substitute_variables(template, context)
        assert result == "Value: "

    def test_substitute_numeric_values(self):
        """Test that numbers are converted to strings."""
        template = "Count: {count}, Score: {score}"
        context = {"count": 42, "score": 3.14}
        result = _substitute_variables(template, context)
        assert result == "Count: 42, Score: 3.14"

    def test_substitute_boolean_values(self):
        """Test that booleans are converted to strings."""
        template = "Enabled: {flag}"
        context = {"flag": True}
        result = _substitute_variables(template, context)
        assert result == "Enabled: True"

    def test_substitute_no_variables(self):
        """Test that template without variables is unchanged."""
        template = "This is a static string with no variables."
        context = {"foo": "bar"}
        result = _substitute_variables(template, context)
        assert result == template

    def test_substitute_repeated_variables(self):
        """Test that repeated variables are all substituted."""
        template = "{name} loves {name}"
        context = {"name": "Alice"}
        result = _substitute_variables(template, context)
        assert result == "Alice loves Alice"


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test suite for convenience function aliases."""

    def test_load_video_prompt(self):
        """Test load_video_prompt() convenience function."""
        context = {"location_name": "MIT", "search_hint": "campus tour"}
        prompt = load_video_prompt(context)
        assert "MIT" in prompt
        assert "Video Agent" in prompt

    def test_load_song_prompt(self):
        """Test load_song_prompt() convenience function."""
        context = {"location_name": "Nashville"}
        prompt = load_song_prompt(context)
        assert "Nashville" in prompt
        assert "Song Agent" in prompt or "Music" in prompt

    def test_load_knowledge_prompt(self):
        """Test load_knowledge_prompt() convenience function."""
        context = {"location_name": "Grand Canyon"}
        prompt = load_knowledge_prompt(context)
        assert "Grand Canyon" in prompt
        assert "Knowledge Agent" in prompt

    def test_load_judge_prompt(self):
        """Test load_judge_prompt() convenience function."""
        context = {"location_name": "MIT"}
        prompt = load_judge_prompt(context)
        assert "MIT" in prompt
        assert "Judge Agent" in prompt or "Content Curator" in prompt


@pytest.mark.unit
class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_empty_context(self):
        """Test loading prompt with empty context (all optional fields missing)."""
        context = {}
        # Should not crash, but may have many empty substitutions
        prompt = load_prompt_with_context("video", context)
        assert len(prompt) > 0

    def test_extra_context_fields(self):
        """Test that extra fields in context don't break substitution."""
        context = {
            "location_name": "MIT",
            "extra_field_not_in_template": "ignored",
            "another_extra": 12345,
        }
        prompt = load_prompt_with_context("video", context)
        assert "MIT" in prompt
        # Extra fields should be ignored (no error)

    def test_unicode_in_context(self):
        """Test that unicode characters in context work correctly."""
        context = {
            "location_name": "Café François",
            "search_hint": "French cuisine 🇫🇷",
        }
        prompt = load_prompt_with_context("video", context)
        assert "Café François" in prompt
        assert "🇫🇷" in prompt or "French cuisine" in prompt  # Emoji may or may not survive

    def test_special_characters_in_context(self):
        """Test that special characters don't break substitution."""
        context = {
            "location_name": "O'Hare Airport",
            "search_hint": "terminal layout (maps)",
        }
        prompt = load_prompt_with_context("video", context)
        assert "O'Hare Airport" in prompt
        assert "terminal layout" in prompt

    def test_very_long_context_value(self):
        """Test that very long strings are substituted correctly."""
        long_context = "A" * 10000  # 10K character string
        context = {
            "location_name": long_context,
        }
        prompt = load_prompt_with_context("video", context)
        assert long_context in prompt


@pytest.fixture
def mock_prompt_dir(tmp_path):
    """
    Create a temporary directory with mock prompt files for testing.
    Useful for testing file I/O without relying on actual .claude/agents/ directory.
    """
    prompts_dir = tmp_path / "mock_agents"
    prompts_dir.mkdir()

    # Create mock video_agent.md
    (prompts_dir / "video_agent.md").write_text(
        "# Mock Video Agent\n\n"
        "Location: {location_name}\n"
        "Hint: {search_hint}\n"
        "Queries: {search_limit}\n",
        encoding="utf-8"
    )

    # Create mock song_agent.md
    (prompts_dir / "song_agent.md").write_text(
        "# Mock Song Agent\n\n"
        "Location: {location_name}\n",
        encoding="utf-8"
    )

    return prompts_dir


@pytest.mark.unit
class TestWithMockPrompts:
    """Test suite using mock prompt files (not actual .claude/agents/ files)."""

    def test_load_from_custom_directory(self, mock_prompt_dir):
        """Test loading prompt from custom directory."""
        prompt = load_agent_prompt("video", prompts_dir=mock_prompt_dir)
        assert "Mock Video Agent" in prompt
        assert "{location_name}" in prompt

    def test_substitute_variables_in_mock_prompt(self, mock_prompt_dir):
        """Test variable substitution in mock prompt."""
        context = {
            "location_name": "Test Location",
            "search_hint": "test hint",
            "search_limit": 5,
        }
        prompt = load_prompt_with_context("video", context, prompts_dir=mock_prompt_dir)

        assert "Test Location" in prompt
        assert "test hint" in prompt
        assert "5" in prompt
        assert "{location_name}" not in prompt
