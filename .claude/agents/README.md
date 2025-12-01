# Agent Prompt System - Route Enrichment Tour-Guide

**Version**: 1.0
**Mission**: M7.14 - Agent Prompt Infrastructure (LLM Intelligence Layer - Foundation)
**Architecture Decision Record**: ADR-013 "Agent Intelligence via Markdown-Defined LLM Prompts"

---

## Overview

This directory contains **markdown-defined prompt templates** for the Route Enrichment Tour-Guide System's intelligent agents. These prompts enable agents to use Large Language Models (LLMs) for context-aware query generation and content evaluation, while maintaining cost control and fallback mechanisms.

### What Problem Does This Solve?

**Before** (Heuristic-only agents):
- Agents generated search queries by simple string concatenation: `f"{location_name} {search_hint}"`
- Limited understanding of geographic context, user intent, or content optimization
- No adaptation to location type (landmark vs. neighborhood vs. natural feature)
- Hard-coded ranking rules with no semantic understanding

**After** (LLM-powered agents):
- Agents generate intelligent, contextaware queries tailored to location type and route context
- Deep understanding of music-location connections, knowledge authority sources, video discovery optimization
- Adaptive query strategies based on available context fields
- Semantic reasoning about content relevance and quality

**Key Principle**: LLM intelligence is **optional and fallback-protected**. If LLM fails or is disabled, agents revert to heuristic query generation seamlessly.

---

## Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                     Task from Orchestrator                  │
│  {location_name, search_hint, route_context, instructions} │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  BaseAgent.run()    │
         └─────────┬───────────┘
                   │
                   ▼
     ┌─────────────────────────────┐
     │  _build_queries(task)       │◄────┐
     │  Try LLM, fallback heuristic│     │
     └─────────┬───────────────────┘     │
               │                          │
        ┌──────▼──────┐          ┌───────┴────────┐
        │  LLM Path   │          │ Heuristic Path │
        └──────┬──────┘          └───────┬────────┘
               │                          │
               ▼                          │
  ┌──────────────────────────┐           │
  │ PromptLoader             │           │
  │ .load_prompt_with_context│           │
  │  (agent_type, task)      │           │
  └──────────┬───────────────┘           │
             │                            │
             ▼                            │
  ┌────────────────────────┐             │
  │ .claude/agents/        │             │
  │  video_agent.md        │             │
  │  (Template Variables)  │             │
  └──────────┬─────────────┘             │
             │                            │
             ▼                            │
  ┌──────────────────────┐               │
  │ Substitute Variables │               │
  │ {location_name} →    │               │
  │  "Grand Canyon"      │               │
  └──────────┬───────────┘               │
             │                            │
             ▼                            │
  ┌──────────────────────┐               │
  │ LLMClient.query()    │               │
  │ (with timeout 10s)   │               │
  └──────────┬───────────┘               │
             │                            │
      ┌──────▼──────────┐                │
      │  Success?       │                │
      └──────┬──────────┘                │
             │                            │
        ┌────▼───┐                       │
        │  Yes   │                       │
        └────┬───┘                       │
             │                            │
             ▼                            │
  ┌───────────────────────┐              │
  │ Parse JSON Response:  │              │
  │ {"queries": [...],    │              │
  │  "reasoning": "..."}  │              │
  └───────────┬───────────┘              │
              │                           │
         ┌────▼──────────┐      ┌────────▼────────┐
         │  Return       │      │  Exception or   │
         │  Queries List │      │  LLM Disabled   │
         └────┬──────────┘      └────────┬────────┘
              │                           │
              └───────────┬───────────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │ Agent.search()      │
                │ (use queries)       │
                └─────────────────────┘
```

---

## Files in This Directory

| File | Purpose | When Used |
|------|---------|-----------|
| **video_agent.md** | YouTube content discovery prompt | VideoAgent._build_queries_with_llm() |
| **song_agent.md** | Music/audio content discovery prompt | SongAgent._build_queries_with_llm() |
| **knowledge_agent.md** | Encyclopedic/factual content discovery prompt | KnowledgeAgent._build_queries_with_llm() |
| **judge_agent.md** | Content evaluation and selection prompt | Judge._llm_score() |
| **README.md** (this file) | System documentation | Developer reference |

---

## Template Variable System

### Core Concept
Prompts contain **placeholder variables** in `{curly_braces}` that are substituted with task context at runtime. This allows prompts to remain static (version-controlled) while adapting to dynamic route data.

### Available Variables

All prompts can access these task fields:

| Variable | Type | Example Value | Always Available? |
|----------|------|---------------|-------------------|
| **`{location_name}`** | string | "MIT", "Grand Canyon" | ✅ Yes (required) |
| **`{address}`** | string | "77 Massachusetts Ave, Cambridge, MA" | ⚠️ Optional |
| **`{search_hint}`** | string | "campus architecture", "scenic overlook" | ⚠️ Optional |
| **`{route_context}`** | string | "Boston university tour", "SW national parks" | ⚠️ Optional |
| **`{instructions}`** | string | "Turn right onto Main St toward..." | ⚠️ Optional |
| **`{coordinates.lat}`** | number | 42.3601 | ✅ Yes |
| **`{coordinates.lng}`** | number | -71.0942 | ✅ Yes |

Configuration parameters (also available):

| Variable | Type | Example Value | Agent-Specific |
|----------|------|---------------|----------------|
| **`{search_limit}`** | integer | 3 | All agents |
| **`{min_duration_seconds}`** | integer/null | 120 or null | Video only |
| **`{max_duration_seconds}`** | integer/null | 600 or null | Video only |
| **`{infer_song_mood}`** | boolean | true/false | Song only |
| **`{boost_authority_domains}`** | boolean | true/false | Knowledge only |

### Variable Substitution Example

**Template** (video_agent.md):
```markdown
Generate search queries to find YouTube videos for {location_name}.
Location type: landmark
Search hint: {search_hint}
Maximum queries: {search_limit}
```

**Task Data**:
```json
{
  "location_name": "Golden Gate Bridge",
  "search_hint": "scenic views",
  "search_limit": 3
}
```

**Substituted Prompt**:
```
Generate search queries to find YouTube videos for Golden Gate Bridge.
Location type: landmark
Search hint: scenic views
Maximum queries: 3
```

### Handling Missing Optional Variables

When optional variables are null/missing:
- **PromptLoader** substitutes empty string `""` or "null"
- **Prompts** include conditional instructions: "use when available", "if provided"
- **Agents** gracefully handle missing context (e.g., "No search_hint provided, infer from location_name")

**Example**:
```markdown
### Optional Context
- search_hint: {search_hint} (use if provided, otherwise infer from location type)
```

If `search_hint` is null → prompt says "(use if provided, otherwise infer...)"
Agent LLM reasoning: "No explicit hint, so inferred 'bridge engineering' from location_name 'Golden Gate Bridge'"

---

## Prompt Design Principles

### 1. Role-Mission-Context-Skills-Process-Constraints Pattern

Every prompt follows this structure (inspired by CrewAI/LangGraph best practices):

- **Role**: Who is the agent? (establishes expertise and perspective)
- **Mission**: What is the agent trying to accomplish?
- **Context**: What information is available? (inputs)
- **Skills**: What can the agent do? (capabilities)
- **Process**: Step-by-step workflow (systematic approach)
- **Constraints**: Limits and best practices (cost, safety, quality)
- **Output Format**: Exact JSON structure required

### 2. Examples Drive Behavior

Each prompt includes **3-5 concrete examples** showing:
- Input task context (location_name, search_hint, etc.)
- Expected output (JSON queries + reasoning)
- Reasoning patterns (how to think about the problem)

Why? LLMs learn patterns from examples more effectively than abstract instructions.

### 3. Cost Awareness Baked In

Every prompt emphasizes:
- **Query count limits**: "Generate exactly {search_limit} queries (default: 3)"
- **Timeout awareness**: "Must complete within 10 seconds"
- **Precision over quantity**: "Each query must be distinct and high-value"
- **Ranking optimization**: "Your queries will be ranked by relevance/popularity/authority"

### 4. Fallback-Friendly Design

Prompts are designed so heuristic fallbacks work seamlessly:
- Query strategies documented in prompts **match** heuristic logic patterns
- LLM adds intelligence (semantic understanding) but doesn't introduce new strategies
- Failure modes gracefully degrade: LLM → heuristic → empty query list → unavailable result

### 5. Output Format Enforcement

All prompts demand:
```json
{
  "queries": ["query1", "query2", "query3"],
  "reasoning": "1-2 sentence explanation"
}
```

**No markdown code blocks**, no prose, no explanations outside JSON.
Why? Easy to parse, no ambiguity, fails fast if malformed.

---

## Integration Points

### In Agent Code (`base_agent.py`)

```python
def _build_queries(self, task: Dict) -> List[str]:
    """
    Try LLM-powered query generation first, fallback to heuristics.
    """
    if self.llm_client and self.config.get("use_llm_for_queries"):
        try:
            return self._build_queries_with_llm(task)
        except Exception as exc:
            self.logger.warning(f"LLM query gen failed: {exc}, fallback to heuristic")
            self._metrics.increment_counter("llm_fallback.query_generation")
    return self._build_queries_heuristic(task)  # Existing logic

def _build_queries_with_llm(self, task: Dict) -> List[str]:
    """
    Load prompt template, substitute variables, query LLM, parse response.
    """
    from hw4_tourguide.tools.prompt_loader import load_prompt_with_context

    # Load and substitute prompt
    prompt = load_prompt_with_context(self.agent_type, task)

    # Query LLM with timeout
    response = self.llm_client.query(prompt)

    # Parse JSON response
    data = json.loads(response["text"])
    queries = data["queries"]
    reasoning = data.get("reasoning", "")

    # Log reasoning
    self.logger.info(f"LLM generated {len(queries)} queries | {reasoning[:100]}")

    return queries
```

### In Configuration (`config/settings.yaml`)

```yaml
agents:
  use_llm_for_queries: true          # Enable LLM query generation
  llm_fallback: true                  # Fallback to heuristics if LLM fails
  llm_query_timeout: 10.0             # Max seconds for LLM call
  llm_max_prompt_chars: 4000          # Truncate prompts for cost control

  video:
    prompt_file: ".claude/agents/video_agent.md"  # Path to template
  song:
    prompt_file: ".claude/agents/song_agent.md"
  knowledge:
    prompt_file: ".claude/agents/knowledge_agent.md"

judge:
  use_llm: false                      # Judge LLM scoring (separate from agent queries)
  llm_provider: "mock"                # "ollama", "openai", "claude", "mock"
```

### In PromptLoader (`tools/prompt_loader.py`)

```python
def load_agent_prompt(agent_type: str) -> str:
    """
    Load raw markdown template for agent.

    Args:
        agent_type: "video", "song", "knowledge", or "judge"

    Returns:
        Raw markdown template content

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    path = Path(f".claude/agents/{agent_type}_agent.md")
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_prompt_with_context(agent_type: str, context: Dict) -> str:
    """
    Load prompt template and substitute variables with task context.

    Args:
        agent_type: "video", "song", "knowledge", or "judge"
        context: Task dictionary with location_name, search_hint, etc.

    Returns:
        Prompt with {variables} substituted

    Example:
        context = {"location_name": "MIT", "search_hint": "campus tour"}
        prompt = load_prompt_with_context("video", context)
        # "{location_name}" → "MIT" in template
    """
    template = load_agent_prompt(agent_type)

    # Flatten nested dicts (coordinates.lat → coordinates_lat for simple substitution)
    flat_context = _flatten_dict(context)

    # Substitute variables (handle missing keys gracefully)
    for key, value in flat_context.items():
        placeholder = "{" + key + "}"
        template = template.replace(placeholder, str(value) if value is not None else "")

    return template
```

---

## Testing Strategy

### Unit Tests (`tests/test_prompt_loader.py`)

```python
def test_load_agent_prompt_success():
    """Test loading existing prompt file."""
    prompt = load_agent_prompt("video")
    assert "Video Agent Prompt Template" in prompt
    assert "{location_name}" in prompt

def test_load_agent_prompt_missing_file():
    """Test FileNotFoundError for non-existent agent."""
    with pytest.raises(FileNotFoundError):
        load_agent_prompt("nonexistent_agent")

def test_load_prompt_with_context_substitution():
    """Test variable substitution."""
    context = {
        "location_name": "MIT",
        "search_hint": "campus tour",
        "search_limit": 3
    }
    prompt = load_prompt_with_context("video", context)
    assert "MIT" in prompt
    assert "campus tour" in prompt
    assert "{location_name}" not in prompt  # Variables replaced

def test_load_prompt_with_missing_optional_fields():
    """Test graceful handling of null/missing fields."""
    context = {
        "location_name": "MIT",
        "search_hint": None,  # Missing optional
        "route_context": None
    }
    prompt = load_prompt_with_context("video", context)
    assert "MIT" in prompt
    # Should not crash, substitutes empty string for nulls
```

### Integration Tests (in `tests/test_*_agent.py`)

```python
def test_video_agent_with_llm(mock_llm_client):
    """Test VideoAgent query generation with mocked LLM."""
    mock_llm_client.query.return_value = {
        "text": '{"queries": ["MIT campus tour", "MIT architecture"], "reasoning": "..."}'
    }

    config = {"use_llm_for_queries": True, "search_limit": 2}
    agent = VideoAgent(config, llm_client=mock_llm_client)

    task = {"location_name": "MIT", "search_hint": "architecture"}
    queries = agent._build_queries(task)

    assert queries == ["MIT campus tour", "MIT architecture"]
    assert mock_llm_client.query.called

def test_video_agent_llm_fallback(mock_llm_client):
    """Test fallback to heuristics when LLM fails."""
    mock_llm_client.query.side_effect = Exception("LLM timeout")

    config = {"use_llm_for_queries": True, "llm_fallback": True}
    agent = VideoAgent(config, llm_client=mock_llm_client)

    task = {"location_name": "MIT"}
    queries = agent._build_queries(task)  # Should not crash

    assert len(queries) > 0  # Heuristic fallback worked
    assert "MIT" in queries[0]
```

---

## Cost & Performance Considerations

### Cost per Query Generation

Typical prompt size: **3,000-4,000 characters** (after variable substitution)

**Token Estimates**:
- Prompt: ~1,000 tokens (input)
- Response: ~100 tokens (output - JSON with 3 queries + reasoning)
- Total: ~1,100 tokens per location

**Pricing (as of 2024)**:
- **Claude Haiku**: $0.00025/1K input, $0.00125/1K output → **$0.00038 per location**
- **GPT-3.5-turbo**: $0.0005/1K input, $0.0015/1K output → **$0.00065 per location**
- **Ollama (local)**: **$0.00 per location** (self-hosted, one-time hardware cost)

**10-step route cost**: $0.0038 (Claude Haiku) to $0.0065 (GPT-3.5) → **< $0.01 per route**

### Performance

- **LLM latency**: 1-3 seconds per query generation (network + inference)
- **Heuristic fallback**: <10ms (instant, no API call)
- **Timeout**: 10 seconds (configurable, prevents hanging)

**Optimization Strategies**:
- **Parallel LLM calls**: All 3 agents call LLM concurrently (orchestrator ThreadPoolExecutor)
- **Prompt caching** (future): Cache prompts for repeated location types
- **Batch LLM queries** (future): Send 3 agent prompts in single API call

---

## Troubleshooting

### Problem: "LLM query gen failed: timeout"

**Cause**: LLM took longer than 10 seconds
**Solution**: Check `llm_query_timeout` in config, increase if needed (up to 30s)
**Fallback**: Agent automatically uses heuristic queries (logged as warning)

### Problem: "LLM returned malformed JSON"

**Cause**: LLM didn't follow output format instructions
**Solution**: Prompt engineering issue - add more examples or stricter format instructions
**Fallback**: Agent catches JSON parse error, falls back to heuristics

### Problem: "FileNotFoundError: Prompt file not found"

**Cause**: `.claude/agents/video_agent.md` missing
**Solution**: Verify directory structure: `ls .claude/agents/*.md` should show 4 files
**Recovery**: Re-run M7.14 setup or restore from repository

### Problem: "LLM always uses heuristic fallback"

**Cause**: `use_llm_for_queries: false` in config, or llm_client=None
**Solution**: Check `config/settings.yaml` has `use_llm_for_queries: true` and LLM provider configured

---

## Extending the System

### Adding a New Agent Type

1. **Create prompt file**: `.claude/agents/[new_agent]_agent.md` following template structure
2. **Define template variables**: Document required/optional fields in prompt
3. **Add agent class**: Extend `BaseAgent`, implement `search()` and `fetch()`
4. **Implement LLM integration**: Use `_build_queries_with_llm()` pattern
5. **Add tests**: Unit tests for prompt loading, integration tests for LLM + fallback
6. **Update config**: Add agent section to `config/settings.yaml`

### Customizing Prompt Behavior

**Approach 1: Edit markdown files directly** (recommended)
- Prompts are version-controlled, reviewable, non-code changes
- No code changes needed, hot-swappable

**Approach 2: Add new template variables**
- Extend task schema with new fields
- Add variables to prompt templates: `{new_field}`
- PromptLoader automatically substitutes any task field

**Approach 3: Multi-prompt strategies**
- Store multiple prompts: `video_agent_landmarks.md`, `video_agent_cities.md`
- Agent selects prompt based on location type at runtime

---

## References

- **ADR-013**: Architecture Decision Record for this system
- **Mission M7.14**: Original requirements and Definition of Done
- **Mission M7.15**: Integration of prompts into agent code (next phase)
- **CrewAI Documentation**: https://docs.crewai.com/ (pattern inspiration)
- **LangGraph Prompt Management**: https://langchain-ai.github.io/langgraph/ (template design)

---

**Last Updated**: 2024-11-26
**Author**: Route Enrichment Tour-Guide Team
**License**: MIT (internal project)
