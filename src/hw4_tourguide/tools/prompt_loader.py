"""
PromptLoader: Load and process markdown-defined agent prompts.

Mission M7.14 - Agent Prompt Infrastructure (LLM Intelligence Layer - Foundation)

This module provides utilities to:
1. Load raw markdown prompt templates from .claude/agents/
2. Substitute template variables ({location_name}, {search_hint}, etc.) with task context
3. Handle missing optional variables gracefully
4. Support all agent types (video, song, knowledge, judge)
"""

from pathlib import Path
from importlib import resources
from typing import Dict, Any, Optional


def load_agent_prompt(agent_type: str, prompts_dir: Optional[Path] = None) -> str:
    """
    Load raw markdown template for specified agent type.

    Args:
        agent_type: Agent identifier - "video", "song", "knowledge", or "judge"
        prompts_dir: Optional custom directory for prompts (for testing).
                     Defaults to .claude/agents/

    Returns:
        Raw markdown template content as string

    Raises:
        FileNotFoundError: If prompt file doesn't exist at expected path
        ValueError: If agent_type is invalid (not in supported list)

    Example:
        >>> prompt = load_agent_prompt("video")
        >>> "Video Agent Prompt Template" in prompt
        True
        >>> "{location_name}" in prompt  # Variables not yet substituted
        True
    """
    valid_agent_types = ["video", "song", "knowledge", "judge"]
    if agent_type not in valid_agent_types:
        raise ValueError(
            f"Invalid agent_type '{agent_type}'. Must be one of: {valid_agent_types}"
        )

    # Search order:
    # 1) Packaged prompts under hw4_tourguide/prompts/agents (ships in wheel)
    # 2) Repo-local .claude/agents when running from source tree
    search_bases = []
    if prompts_dir:
        search_bases.append(prompts_dir)
    else:
        try:
            search_bases.append(resources.files("hw4_tourguide.prompts.agents"))
        except Exception:
            pass
        project_root = Path(__file__).resolve().parents[3]
        search_bases.append(project_root / ".claude" / "agents")
        
        # Also check current working directory (useful when running tests)
        search_bases.append(Path.cwd() / ".claude" / "agents")

    filename = f"{agent_type}_agent.md"
    errors = []
    for base in search_bases:
        try:
            candidate = base / filename  # type: ignore[operator]
            if hasattr(candidate, "is_file") and candidate.is_file():  # Traversable or Path
                return candidate.read_text(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception as exc:
            errors.append(str(exc))

    raise FileNotFoundError(
        f"Prompt file not found: searched {', '.join(str(b) for b in search_bases)}\n"
        f"Agent type: {agent_type}\n"
        f"Errors: {errors}"
    )


def load_prompt_with_context(
    agent_type: str,
    context: Dict[str, Any],
    prompts_dir: Optional[Path] = None,
) -> str:
    """
    Load prompt template and substitute variables with task context.

    This function:
    1. Loads the raw markdown template for the agent
    2. Flattens nested dicts in context (coordinates.lat → "coordinates_lat")
    3. Substitutes all {variable} placeholders with context values
    4. Handles missing optional variables by replacing with empty string

    Args:
        agent_type: Agent identifier - "video", "song", "knowledge", or "judge"
        context: Task dictionary containing:
                 - location_name (required): string
                 - address (optional): string | None
                 - search_hint (optional): string | None
                 - route_context (optional): string | None
                 - instructions (optional): string | None
                 - coordinates (required): {lat: float, lng: float}
                 - search_limit (optional): int
                 - [agent-specific config params]
        prompts_dir: Optional custom directory for prompts (for testing)

    Returns:
        Prompt string with all {variables} substituted

    Raises:
        FileNotFoundError: If prompt file doesn't exist
        ValueError: If agent_type is invalid

    Example:
        >>> context = {
        ...     "location_name": "MIT",
        ...     "search_hint": "campus architecture",
        ...     "coordinates": {"lat": 42.3601, "lng": -71.0942},
        ...     "search_limit": 3
        ... }
        >>> prompt = load_prompt_with_context("video", context)
        >>> "MIT" in prompt
        True
        >>> "campus architecture" in prompt
        True
        >>> "{location_name}" in prompt  # Variables replaced
        False
    """
    # Load raw template
    template = load_agent_prompt(agent_type, prompts_dir)

    # Flatten nested dicts for simple string substitution
    # Example: {"coordinates": {"lat": 42.3, "lng": -71.0}} → {"coordinates_lat": 42.3, "coordinates_lng": -71.0}
    flat_context = _flatten_dict(context)

    # Substitute all template variables
    substituted = _substitute_variables(template, flat_context)

    return substituted


def _flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """
    Flatten nested dictionary into single-level dict with concatenated keys.

    Args:
        d: Dictionary to flatten (may contain nested dicts)
        parent_key: Prefix for keys (used in recursion)
        sep: Separator for concatenated keys (default: "_")

    Returns:
        Flattened dictionary

    Example:
        >>> _flatten_dict({"a": 1, "b": {"c": 2, "d": 3}})
        {'a': 1, 'b_c': 2, 'b_d': 3}
        >>> _flatten_dict({"coordinates": {"lat": 42.3, "lng": -71.0}})
        {'coordinates_lat': 42.3, 'coordinates_lng': -71.0}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            # Recursively flatten nested dicts
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _substitute_variables(template: str, context: Dict[str, Any]) -> str:
    """
    Substitute {variable} placeholders in template with context values.

    Handles:
    - Missing variables → replaced with empty string ""
    - None values → replaced with "null" string (for prompt clarity)
    - Non-string values → converted to string via str()

    Args:
        template: Markdown template with {variable} placeholders
        context: Flat dictionary of variable_name → value

    Returns:
        Template with all variables substituted

    Example:
        >>> template = "Location: {location_name}, Hint: {search_hint}"
        >>> context = {"location_name": "MIT", "search_hint": "campus tour"}
        >>> _substitute_variables(template, context)
        'Location: MIT, Hint: campus tour'

        >>> # Missing variable handled gracefully
        >>> context = {"location_name": "MIT"}  # search_hint missing
        >>> _substitute_variables(template, context)
        'Location: MIT, Hint: '
    """
    result = template

    # Find all {variable} patterns in template
    import re
    variable_pattern = re.compile(r"\{([^}]+)\}")
    variables_in_template = variable_pattern.findall(template)

    # Substitute each variable
    for var_name in variables_in_template:
        placeholder = "{" + var_name + "}"
        value = context.get(var_name)

        # Handle different value types
        if value is None:
            # Replace None with empty string (prompts handle missing optional fields)
            substituted_value = ""
        elif isinstance(value, (int, float, bool)):
            # Convert numbers/booleans to strings
            substituted_value = str(value)
        elif isinstance(value, str):
            # Use string as-is
            substituted_value = value
        else:
            # Fallback for lists, dicts, etc. (shouldn't happen with flattened context)
            substituted_value = str(value)

        result = result.replace(placeholder, substituted_value)

    return result


# Convenience function aliases for backward compatibility / readability
def load_video_prompt(context: Dict[str, Any]) -> str:
    """Load video agent prompt with context substitution."""
    return load_prompt_with_context("video", context)


def load_song_prompt(context: Dict[str, Any]) -> str:
    """Load song agent prompt with context substitution."""
    return load_prompt_with_context("song", context)


def load_knowledge_prompt(context: Dict[str, Any]) -> str:
    """Load knowledge agent prompt with context substitution."""
    return load_prompt_with_context("knowledge", context)


def load_judge_prompt(context: Dict[str, Any]) -> str:
    """Load judge agent prompt with context substitution."""
    return load_prompt_with_context("judge", context)
