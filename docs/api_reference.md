# API Reference – Route Enrichment Tour-Guide System

This reference summarizes runtime configuration for the tour-guide pipeline. All parameters live in `config/settings.yaml`, can be overridden via CLI flags, and fall back to safe defaults in `ConfigLoader`.

## Configuration Priority
1. Code defaults (`ConfigLoader.DEFAULT_CONFIG`)
2. YAML (`config/settings.yaml`)
3. Environment variables (`.env`)
4. CLI overrides (e.g., `--mode live --log-level DEBUG`)

## Key Parameters

| Key | Default (code) | Valid / Notes |
| --- | --- | --- |
| `scheduler.interval` | `2.0` | Float `0.5-10.0` seconds |
| `orchestrator.max_workers` | `5` | Int `1-20` thread pool size |
| `agents.use_llm_for_queries` | `true` | Global toggle for agent LLM query gen |
| `agents.video.search_limit` | `3` | Int `1-10` candidates |
| `agents.llm_provider` | `auto` | `ollama`, `openai`, `claude`, `gemini`, `mock`, `auto` |
| `agents.llm_max_prompt_chars` | `5000` | Guardrail for query-gen prompts |
| `agents.llm_max_tokens` | `4000` | Max tokens for agent LLM query gen |
| `agents.llm_query_timeout` | `30.0` | Float `5.0-60.0` seconds |
| `agents.llm_retries` | `3` | Int `1-5` |
| `agents.llm_backoff` | `exponential` | `exponential` or `linear` |
| `agents.use_secondary_source` | `true` | Global secondary-source toggle (e.g., YouTube/DDG) |
| `agents.infer_song_mood` | `false` | Heuristic mood/genre inference for SongAgent |
| `agents.*.retry_backoff` | `exponential` | `exponential` or `linear` |
| `agents.*.use_live` / `mock_mode` | `true` / `false` | Live clients vs stubs per agent |
| `judge.scoring_mode` | `llm` | `heuristic`, `llm`, `hybrid` |
| `judge.use_llm` | `true` | Requires LLM key when true |
| `judge.llm_max_prompt_chars` | `6000` | Guardrail for judge prompt size |
| `judge.llm_max_tokens` | `12000` | Max tokens for judge call |
| `logging.level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `output.base_dir` | `output` | Root for per-run folders |
| `output.checkpoint_retention_days` | `7` | Int `0-30` (0 = keep forever) |
| `output.checkpoints_enabled` | `true` | Enable/disable writing checkpoints |
| `route_provider.mode` | `live` | `live` (Google Maps) or `cached` (local) |
| `route_provider.cache_dir` | `data/routes` | Folder for cached routes |
| `route_provider.api_timeout` | `20.0` | Float `5.0-30.0` seconds |
| `route_provider.api_retry_attempts` | `3` | Int `1-5` retries per call |
| `route_provider.max_steps` | `8` | Enforces cost/latency guardrail |
| `circuit_breaker.failure_threshold` | `5` | Int `3-10` failures before OPEN |
| `circuit_breaker.timeout` | `60.0` | Float `30.0-300.0` seconds |
| `metrics.enabled` | `true` | Toggle MetricsCollector |
| `metrics.file` | `logs/metrics.json` | Path for metrics output |
| `metrics.update_interval` | `5.0` | Float `1.0-30.0` seconds |

Additional keys are documented inline in `config/settings.yaml` (type, defaults, valid ranges).

## Example Configurations

### Live Mode (Google Maps + LLM Judge)
```yaml
route_provider:
  mode: live
  api_retry_attempts: 3
  api_timeout: 10.0
judge:
  use_llm: true
  llm_provider: claude
logging:
  level: INFO
```
Requires `.env` with `GOOGLE_MAPS_API_KEY` and the chosen LLM key (`ANTHROPIC_API_KEY` recommended; falls back to `OPENAI_API_KEY` / `GEMINI_API_KEY` if provider set accordingly).

### Cached Mode (Offline-Friendly)
```yaml
route_provider:
  mode: cached
  cache_dir: data/routes
judge:
  use_llm: false
logging:
  level: INFO
```

### Mock / Fast Test Mode
```yaml
agents:
  video: {use_live: false, mock_mode: true}
  song: {use_live: false, mock_mode: true}
  knowledge: {use_live: false, mock_mode: true, search_limit: 1}
logging:
  level: WARNING
output:
  checkpoints_enabled: false
metrics:
  enabled: false
```

### Debug Mode (Instrumentation Heavy)
```yaml
logging:
  level: DEBUG
  console_enabled: true
metrics:
  enabled: true
  update_interval: 2.0
output:
  checkpoints_enabled: true
```

## CLI Override Examples
- Run cached with debug logging: `python -m hw4_tourguide --mode cached --log-level DEBUG`
- Custom output path: `python -m hw4_tourguide --output output/custom_route.json`
- Point to a different config: `python -m hw4_tourguide --config configs/dev.yaml`
