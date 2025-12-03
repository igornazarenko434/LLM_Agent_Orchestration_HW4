# Product Requirements Document – Route Enrichment Tour-Guide System

## 1. Context & Strategy
- **Project Name:** Route Enrichment Tour-Guide System
- **Vision:** Enrich every driving step with curated media and knowledge using a production-style autonomous agent platform.
- **Category:** Multi-agent orchestration platform with multi-threaded scheduler, orchestrator, agents, and judge.
- **Problem Statement:** Following `HW4_Project_Mission.md`, we must simulate a mini production system that ingests a Google Maps route, streams each location via a scheduler, runs parallel content agents (video, song, knowledge), judges their outputs, and emits logged, reproducible artifacts.
- **Success Definition:** Instructor can `pip install .`, run `python -m hw4_tourguide`, observe logged scheduler/orchestrator/agent activity, and inspect structured outputs proving concurrency, cost control, and modular design.
- **Target Grade:** 95 (Outstanding Excellence band).

## 2. Stakeholders & Personas
### Stakeholders
1. **Instructor/Grader:** Needs rubric-aligned package and verification evidence.
2. **Student Dev Team:** Executes missions and maintains progress tracker.
3. **Daily Drivers / Commuters:** Benefit from enriched drive experiences.
4. **Professional Tour Guides / Content Curators:** Use exports for client tours.
5. **Google Maps Platform Compliance Team:** Ensures API usage stays within free tier.
6. **QA & Operations Reviewer:** Requires observability and recovery evidence.

### Personas
- **Moshe Buzaglos – Bored Commuter:** Wants relevant media per commute; verified by CLI demo logs showing route-specific picks.
- **Danit Griner – Tour Design Strategist:** Needs exportable summaries with rationale; verified by output artifacts and README guidance.

## 3. Goals & KPIs (verification commands included)
| # | Category | Claim | Evidence Artifact | Verification Command | Expected Output | Location |
|---|----------|-------|-------------------|----------------------|-----------------|----------|
| 1 | KPI-1 | Package installable via pip | Installation log, help output | `pip install . && python -m hw4_tourguide --help` | Package installs without errors, help text displays CLI options | Installation matrix step 3 |
| 2 | KPI-2 | Config centralized in YAML | settings.yaml file | `wc -l config/settings.yaml && grep -R -n "os.environ" src/` | ≥20 lines in YAML, zero hard-coded env lookups | Section 11, M3.1 |
| 3 | KPI-3 | Google Maps reliability | Live + cached run logs | `python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode live --output output/live_run_kpi3.json && python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode cached --output output/cached_run_kpi3.json && ls output/live_run_kpi3.json output/cached_run_kpi3.json` | Both commands exit 0, output/live_run_kpi3.json and output/cached_run_kpi3.json are created. | Section 7, M7.1 |
| 4 | KPI-4 | Scheduler cadence accuracy | Interval check script output | `python scripts/check_scheduler_interval.py output/*_Boston_MA_to_MIT/logs/system.log` | `Script reports "All scheduler intervals are within X.Xs +/-0.2s." and exits with code 0.` | Section 13, M7.2 |
| 5 | KPI-5 | Agent concurrency | Concurrency test output | `pytest tests/test_concurrency.py -m concurrency -v` | `Test passes, asserting overlapping agent execution within test logs.` | M7.11, tests/ |
| 6 | KPI-6 | Search/fetch cost control | Metrics JSON, check script output | `python scripts/check_api_usage.py output/*_Boston_MA_to_MIT/logs/metrics.json` | `Script output confirms "Google Maps API calls: 0 (Expected <= 0 for cached run context)." and "LLM Query Generation calls: X (Reasonable for typical run)."` | M5, docs/cost_analysis.md |
| 7 | KPI-7 | Judge scoring completeness | Final route JSON | `jq '.[].judge.overall_score' output/*_Boston_MA_to_MIT/final_route.json | wc -l` | `4 (matching the number of steps in the demo route)` | M7.7, output/ |
| 8 | KPI-8 | Logging coverage | System log file | `grep -E "Scheduler|Orchestrator|Agent|Judge|Error" output/*_Boston_MA_to_MIT/logs/system.log | wc -l` | `≥50 structured log entries per run` | M3.2, logs/ |
| 9 | KPI-9 | CLI execution success | Exit code, output artifacts | `python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode cached --output output/my_kpi_demo.json && echo $? && ls output/my_kpi_demo.{json,md,csv}` | `0 (exit code) is printed, and output/my_kpi_demo.json, .md, .csv are listed.` | M7.9, output/ |
| 10 | KPI-10 | Test coverage | Coverage report | `pytest --cov=hw4_tourguide --cov-report=term` | `≥85% line coverage` | M4.2, htmlcov/ |
| 11 | KPI-11 | Retry/backoff logic | Resilience test log | `pytest tests/test_resilience.py -k retry -v` | `Tests pass, log shows 3 retry attempts with backoff` | M7.12, logs/ |
| 12 | KPI-12 | README completeness | README validation script | `python scripts/check_readme.py README.md` | `Script reports "README.md check completed successfully"` | M8.3, README.md |
| 13 | KPI-13 | Cost transparency | Cost analysis doc | `ls docs/cost_analysis.md && grep -c "^|" docs/cost_analysis.md` | `Doc exists with ≥2 tables (API calls, token usage)` | M8.2 |
| 14 | KPI-14 | System Readiness (Preflight) | Preflight script output | `python scripts/preflight.py` | `Preflight checklist passes all stages: Build, Config, Tests (>85% cov), Git Health, and Runtime Verification (Scheduler/API Checks). Final Verdict: ✅ READY FOR FLIGHT!` | M9.1 |

## 4. Requirements
### Functional Requirements
1. **FR-001 Route Retrieval:** Live + cached Google Maps Directions API with transaction IDs per step.
2. **FR-002 Scheduler:** Dedicated thread emits steps at configured interval into a queue.
3. **FR-003 Orchestrator:** Worker threads consume queue items, spawn agents, await futures, and aggregate results.
4. **FR-004 Video Agent:** Search→fetch pipeline retrieving relevant YouTube metadata; logs decisions.
5. **FR-005 Song Agent:** Similar pipeline targeting audio content with cost-aware query depth.
6. **FR-006 Knowledge Agent:** Fetches articles/facts, extracts summaries with citations.
7. **FR-007 Judge Agent:** Scores agent outputs using LLM (primary) with heuristic fallback, returns rationale.
8. **FR-008 Output Writer:** Persists JSON + human-friendly reports, enabling persona exports.
9. **FR-009 CLI Interface:** `python -m hw4_tourguide` exposes from/to, config, mode, log level, output path.
10. **FR-010 Packaging Configuration:** `pyproject.toml` defines build dependencies and wheel inclusions; `MANIFEST.in` ensures source distributions include config, prompts, docs, tests, and scripts.

### Non-Functional Requirements (ISO/IEC 25010)
1. **Reliability:** Recover from agent failures with retries/backoff.
2. **Performance/Efficiency:** Scheduler overhead <0.5s; agents run concurrently, configurable thread pool.
3. **Usability:** README + CLI help, quick-start instructions, troubleshooting guide.
4. **Security:** `.env` secrets only; logs redact keys; HTTPS for external calls.
5. **Maintainability:** Core modules range from 150-600 LOC with clear abstractions; type hints and docstrings used throughout; modular design with separated concerns (agents, tools, config, orchestration).
6. **Portability:** macOS/Linux compatible, no absolute paths, relative config.
7. **Observability:** Structured logging with rotation and log level control via config.
8. **Configurability:** YAML-driven parameters, CLI overrides, no hard-coded thresholds.
9. **Scalability/Extensibility:** Agent registry + route provider abstraction for future modules.

### User Stories (linked to personas/stakeholders)
| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| US-001 | **As Moshe** (bored commuter), I want enriched content for each route step so that my daily commute becomes engaging | **AC1:** Run `python -m hw4_tourguide --from "Home" --to "Work" --mode cached`<br>**AC2:** Output JSON contains ≥1 video, song, and knowledge item per step<br>**AC3:** Each item has metadata (title, URL, description, judge score)<br>**AC4:** Logs show scheduler emitting steps at configured interval<br>**AC5:** Total execution time <5 minutes for 10-step route |
| US-002 | **As Danit** (tour strategist), I need exportable summaries with rationale so that I can plan client tours | **AC1:** CLI `--output` flag generates 3 files: JSON, Markdown, CSV<br>**AC2:** Markdown report includes judge rationale per location<br>**AC3:** CSV has columns: location, video_title, song_title, article_title, judge_score<br>**AC4:** README section "Exporting Results" documents export workflow<br>**AC5:** Files readable in Excel/Obsidian/text editor without corruption |
| US-003 | **As Instructor**, I need reproducible installation so that I can grade the project quickly | **AC1:** `pip install .` completes in <2 minutes on clean venv<br>**AC2:** `python -m hw4_tourguide --help` shows CLI options<br>**AC3:** README Installation Matrix has 10+ steps with verification commands<br>**AC4:** `pip check` validates dependencies<br>**AC5:** No manual PATH/environment setup required |
| US-004 | **As Maps Compliance Team**, we need cost control so that free tier quotas aren't exceeded | **AC1:** `logs/metrics.json` tracks API call counts per run<br>**AC2:** Live mode uses optimized Google Maps calls (Directions + 1 Geocode per step)<br>**AC3:** Cached mode uses 0 Google Maps calls<br>**AC4:** docs/cost_analysis.md shows 90%+ cost reduction via caching<br>**AC5:** Config allows setting max API calls per agent |
| US-005 | **As QA/Ops**, we need retry logic and comprehensive logs so that we can diagnose failures | **AC1:** Retry tests (`tests/test_resilience.py`) pass with 3 retry attempts<br>**AC2:** Logs show exponential backoff (1s, 2s, 4s) on API failures<br>**AC3:** System continues on single agent failure (graceful degradation)<br>**AC4:** Logs include Transaction IDs for tracing requests<br>**AC5:** README Troubleshooting section documents 5+ common errors with solutions |
| US-006 | **As Dev Team**, we need mission tracking so that we coordinate work and track progress | **AC1:** Missions file has 40 missions with Definition of Done<br>**AC2:** PROGRESS_TRACKER.md shows status of all missions<br>**AC3:** README links to Missions and Progress Tracker<br>**AC4:** `.claude` file updated after each mission completion<br>**AC5:** Git history shows ≥15 commits with conventional messages |

## 5. Scope, Dependencies, Assumptions, Constraints
- **In Scope:** Live/cached routing, scheduler/orchestrator/agents/judge, logging, CLI, tests, documentation, cost metrics, file-based outputs.
- **Out of Scope:** GUIs/web apps, persistent databases, streaming media playback, payment systems, multi-user servers.
- **Dependencies:** Python 3.10.19 or higher (3.11+ recommended), Google Maps API (Directions & Geocoding), YouTube/Spotify APIs, DuckDuckGo/Wikipedia APIs, LLM APIs (OpenAI/Anthropic/Gemini) or mock, `requests`, standard concurrency libs.
- **Assumptions:** Internet available for live runs; cached mode for offline; instructor on macOS/Linux; free tiers sufficient; `.env` configured with necessary API keys (Google, Spotify, LLM).
- **Constraints:** Single MacBook; minimize API/LLM calls; configuration-driven; no paid infrastructure; multi-threading only.

## 6. Architecture & Module Overview
- **Route Provider Layer:** `RouteProvider` interface with Google Maps implementation + cached file provider. Cached mode looks for a file named by SHA1 hash (first 12 chars) of `"<origin>-<destination>"`; the Boston→MIT demo ships as `data/routes/demo_boston_mit.json` and is used when no slug match is found. Dropping a single `.json` in `data/routes/` also works as a fallback for offline demos; cached mode forces stub agents even if keys are present.
- **Scheduler:** Threaded timer reading config interval, pushing tasks to `queue.Queue` with logging hooks, stamping `emit_timestamp`, writing `01_scheduler_queue.json` checkpoints.
- **Orchestrator:** Main loop consuming queue, spawning worker threads or `ThreadPoolExecutor` per location.
- **Agents:** Independent modules implementing `AgentResult` contract; use search→fetch separation and shared tooling. Each agent now uses injected clients (with default offline stubs) plus ranking, retries, logging, circuit breaker protection, metrics recording (api_calls + latencies), and checkpoints for search (`02_agent_search_*.json`) and fetch (`03_agent_fetch_*.json`). Config flags `use_live`/`mock_mode` control live vs stub; cached mode forces stubs even if keys are present; fallbacks if keys are missing.
- **Search/Fetch Tool Layer:** Shared `SearchTool`/`FetchTool` modules wrap provider clients with standardized timeouts, logging, and result limiting; agents remain responsible for retries/backoff/CB/metrics but delegate raw search/fetch calls to these tools for consistency.
- **LLM Scoring Abstraction:** Optional `llm_client` factory (Claude/OpenAI/Gemini/Ollama/Mock) with timeouts/retries/backoff, prompt-length, and token guards; auto priority (when configured) is Claude > OpenAI > Gemini > Ollama (factory default `llama3.1:8b`, class default `llama3`) > Mock; `use_llm=true` by default; Judge defaults to LLM scoring and falls back gracefully to heuristics when LLM unavailable or fails.
- **Judge LLM Prompting:** Judge loads markdown template (`.claude/agents/judge_agent.md`) via `PromptLoader.load_prompt_with_context`, injects sanitized agent metadata and task context, and parses LLM rationale/choice with heuristic fallback.
- **Agent LLM Query Generation:** When `agents.use_llm_for_queries=true` (default), Video/Song/Knowledge load their markdown prompts, call the shared LLM client to generate JSON `{queries: [...]}`, log metrics/latency, and fall back to heuristic queries on any LLM error.
- **Resilience & Backoff:** Route provider and agents use retries/backoff with circuit breakers; resilience tests validate retry timing, circuit transitions, graceful degradation, and checkpoint handling.
- **Validation & Determinism:** Warn-level schema validation (agent/judge) with malformed agent results dropped before judge; outputs sorted by step_number for repeatable CSV/JSON/MD.
- **Deterministic Outputs:** Output writer sorts steps by `step_number` before emitting JSON/Markdown/CSV for reproducible ordering.
- **Judge:** Consumes agent outputs, calculates heuristic + optional LLM similarity score; writes decision object.
- **Output Module:** Writes JSON contract + Markdown summary, triggers persona-specific exports.
- **Config Loader:** Parses `config/settings.yaml`, merges CLI flags, loads `.env` secrets.
- **Logging Layer:** Configurable format, file rotation, event tagging for KPI verification.
- **Metrics Layer:** Separate `MetricsCollector` aggregates API call counts, latencies, and queue depth into `logs/metrics.json` for cost/performance tracking.

## 6.4 Agent Intelligence Layer (New in v1.3)
- **Concept:** Decouples agent logic (Python code) from prompt engineering (Markdown).
- **Components:**
  - **Markdown Prompts:** Located in `.claude/agents/`, defining Role, Mission, Context, and Output Format for each agent.
  - **PromptLoader:** Utility to load templates and inject runtime variables (`{location_name}`, `{search_hint}`).
  - **LLM Client:** Unified interface for Claude/OpenAI/Gemini with failover and budget guards.
- **Workflow:** Agents load prompts -> Substitute context -> Query LLM -> Parse JSON queries -> Execute search.
- **Fallback:** If LLM fails or is disabled, agents revert to heuristic string concatenation (legacy logic).

## 6a. Architecture Decision Records (ADRs)

This section documents key architectural decisions, alternatives considered, trade-offs, and rationale. Full ADR register available at `docs/architecture/adr_register.md`.

### **ADR-001: Python 3.10.19+ as Implementation Language**
- **Status:** Accepted
- **Context:** Need modern language with strong ecosystem for networking, threading, data processing, and testing
- **Decision:** Use Python 3.10.19+ (3.11.x recommended for development)
- **Alternatives Considered:**
  - **Alternative A (Python 3.9):** Broader compatibility but lacks newer performance improvements and syntax features (e.g., improved error messages, faster CPython)
  - **Alternative B (Node.js/TypeScript):** Excellent async/await support but instructor examples use Python; steeper learning curve for thread-based concurrency
  - **Alternative C (Go):** Superior concurrency primitives (goroutines) but less familiar ecosystem for data science/notebooks; harder to prototype agents
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Rich ecosystem (pytest, requests, pyyaml, jupyter), instructor familiarity, fast prototyping, strong typing with type hints
  - ❌ **Cons:** GIL limits CPU-bound parallelism (but I/O-bound agents not affected), requires venv management, slower than compiled languages
- **Rationale:** Aligns with instructor examples, course focus, and enables rapid agent development with mature libraries
- **Related Missions:** M2.0 (package setup), M4.1 (pytest framework)

### **ADR-002: Threading (not AsyncIO) for Concurrency**
- **Status:** Accepted
- **Context:** Need concurrent execution for scheduler, orchestrator, and agents; multiple approaches available in Python
- **Decision:** Use `threading.Thread` for scheduler, `ThreadPoolExecutor` for orchestrator workers, standard `queue.Queue` for task passing
- **Alternatives Considered:**
  - **Alternative A (AsyncIO):** Modern Python approach with `async`/`await`, efficient for I/O-bound tasks, single-threaded event loop
  - **Alternative B (Multiprocessing):** True parallelism via separate processes, bypasses GIL, suitable for CPU-intensive work
  - **Alternative C (Celery):** Distributed task queue with worker management, battle-tested for production systems
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Simpler mental model than async/await (synchronous function calls), matches instructor examples (HW4 spec mentions threads), standard library only (no extra deps), straightforward debugging
  - ❌ **Cons:** Not as "modern" as AsyncIO, can't leverage async HTTP libraries (e.g., httpx), thread overhead higher than coroutines, GIL limits CPU parallelism (not an issue for I/O agents)
- **Rationale:** Instructor spec explicitly mentions "multi-threaded" system; threading sufficient for I/O-bound agents (YouTube/Wikipedia calls); simpler to reason about than async state machines
- **Related Missions:** M7.2 (Scheduler thread), M7.3 (Orchestrator ThreadPoolExecutor), M7.11 (concurrency tests)
- **References:** HW4_Project_Mission.md Section 2.3 (multi-threaded requirement)

### **ADR-003: Google Maps API with Aggressive Caching Strategy**
- **Status:** Accepted
- **Context:** Need real route data but free tier limited to 2,500 requests/month; development requires frequent runs
- **Decision:** Implement `RouteProvider` abstraction with two backends: (1) Live Google Maps Directions API, (2) Cached file provider reading `data/routes/*.json`
- **Alternatives Considered:**
  - **Alternative A (MapBox API):** Comparable free tier, different data format; requires learning new API
  - **Alternative B (OpenStreetMap Nominatim):** Fully open-source, no API key required, but geocoding-only (not full routing with steps)
  - **Alternative C (Hard-coded mock routes):** No API dependency, but unrealistic and wouldn't demonstrate API integration
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Caching enables unlimited dev/test runs without API costs; abstraction allows swapping providers; live mode proves real API integration
  - ❌ **Cons:** Cached data may become stale; need to manage cache files; two code paths to maintain (live + cached)
- **Rationale:** Protects free tier quota while maintaining realism; instructor can run cached demos without own API key; demonstrates good software practice (caching, abstraction)
- **Implementation:** `--mode [live|cached]` CLI flag; `data/routes/` directory with pre-fetched routes; transaction IDs link cached files to route requests
- **Related Missions:** M7.1 (Route Provider), M3 (config for API keys), M9.3 (live + cached demo runs)
- **Cost Impact:** Live mode: $0.005/request × 3 calls = $0.015 per demo; Cached mode: $0 per demo

### **ADR-004: Search+Fetch Separation for Agent Architecture**
- **Status:** Accepted
- **Context:** Agents need external data (YouTube videos, Spotify songs, Wikipedia articles); unclear whether to fetch all candidates or single result
- **Decision:** Each agent implements two-phase pipeline: (1) **Search** - query API, return list of candidate IDs (limit 3), (2) **Fetch** - retrieve full metadata for selected candidate(s)
- **Alternatives Considered:**
  - **Alternative A (Direct fetch):** Agent immediately fetches full data for first search result; simpler code, one API call per location
  - **Alternative B (Fetch all candidates):** Search returns IDs, then fetch metadata for all 3 candidates; allows judge to compare multiple options
  - **Alternative C (Streaming search):** Fetch candidates lazily (generator pattern) until judge satisfied; complex state management
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Modularity enables testing search/fetch independently; cost control (fetch only selected items); flexibility for judge to request more data; clear logging (separate SEARCH and FETCH log entries)
  - ❌ **Cons:** Two API calls instead of one (search + fetch); more code complexity; need to design candidate selection logic
- **Rationale:** Separation makes cost/quality trade-offs explicit; enables future optimizations (cache search results, smart candidate ranking); aligns with instructor's emphasis on "search" and "enrichment" as distinct steps
- **Implementation:** Base `Agent` class with abstract `search()` and `fetch()` methods; subclasses override for specific APIs; `search()` returns `List[CandidateID]`, `fetch(id)` returns `MediaMetadata`
- **Related Missions:** M7.4 (Video Agent), M7.5 (Song Agent), M7.6 (Knowledge Agent), M5 (cost tracking)
- **Example:** VideoAgent.search("MIT campus") → ["video_123", "video_456", "video_789"] → VideoAgent.fetch("video_123") → {title, channel, duration, ...}

### **ADR-005: YAML Configuration with CLI Overrides**
- **Status:** Accepted
- **Context:** Many tunable parameters (scheduler interval, agent query limits, API endpoints, log levels, output paths); need balance between flexibility and ease of use
- **Decision:** Centralize all parameters in `config/settings.yaml`; allow CLI flags to override specific values for single-run experiments; load secrets from `.env` file
- **Alternatives Considered:**
  - **Alternative A (Environment variables only):** 12-factor app pattern, no config files; harder to document, difficult to manage 20+ params as env vars
  - **Alternative B (Command-line flags only):** Maximum explicitness, no hidden state; impractical for 20+ parameters, verbose commands
  - **Alternative C (Python config.py module):** Code-based config with Python expressions; less accessible to non-programmers, requires restart to change
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Single source of truth (YAML file); CLI overrides enable quick experiments without editing files; human-readable format with inline comments; versionable config (commit settings.yaml to repo)
  - ❌ **Cons:** Two places to check for param values (YAML + CLI); need precedence rules (CLI > YAML > defaults); YAML parsing adds dependency
- **Rationale:** Power users edit YAML once, quick users override via CLI; instructor can tweak config without code changes; follows best practices for 12-factor apps (config separate from code)
- **Implementation:** Priority order: CLI flags > `config/settings.yaml` > default values in code; ConfigLoader class merges sources; `--config` flag allows custom YAML path
- **Related Missions:** M3 (Config & Security), M3.1 (YAML schema), M7.9 (CLI argument parsing)
- **Example:** `python -m hw4_tourguide --mode cached --log-level DEBUG` overrides `settings.yaml` but keeps other params unchanged

### **ADR-006: Structured Logging with Python `logging` Module**
- **Status:** Accepted
- **Context:** Need observability for scheduler/orchestrator/agent activity; logs must prove concurrency, cadence, cost control for grading
- **Decision:** Use Python standard library `logging` with custom format `TIMESTAMP | LEVEL | MODULE | EVENT_TAG | MESSAGE`; write to `logs/system.log` with rotation; event tags: Scheduler, Orchestrator, Agent, Judge, Error, API_Call, Config
- **Alternatives Considered:**
  - **Alternative A (Print statements):** Simplest approach, writes to stdout; not structured, no log levels, hard to filter, mixes with normal output
  - **Alternative B (Third-party logger - loguru):** Modern API, colored output, simpler configuration; adds dependency, unfamiliar to instructor
  - **Alternative C (JSON logs):** Machine-readable, easy to parse; harder for humans to read during development, requires jq for inspection
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Standard library (no dependency), configurable levels (DEBUG/INFO/WARNING/ERROR), rotation prevents disk bloat, structured format enables grep filtering, familiar to instructor
  - ❌ **Cons:** Verbose API (need logger.info(...) instead of print(...)), requires setup boilerplate, less modern than loguru
- **Rationale:** Meets observability NFR; log format enables KPI verification commands (e.g., `grep "Scheduler" logs/system.log | wc -l`); rotation prevents log files from filling disk
- **Implementation:** `src/hw4_tourguide/logger.py` sets up RotatingFileHandler (10MB per file, 5 backups); `--log-level` CLI flag overrides config; event tags injected via custom formatter
- **Related Missions:** M3.2 (logging infrastructure), M7.2-7.7 (agent logging), M8.4 (log evidence for docs)
- **Verification:** KPI #8 requires ≥50 log entries per run; `grep -E "Scheduler|Orchestrator|Agent|Judge|Error" logs/system.log | wc -l`

### **ADR-007: ThreadPoolExecutor for Orchestrator Workers**
- **Status:** Accepted
- **Context:** Orchestrator needs to spawn concurrent workers to process route steps; each worker coordinates 3 agents + judge; must be scalable and testable
- **Decision:** Use `concurrent.futures.ThreadPoolExecutor` with configurable `max_workers` (default 5); submit worker jobs as futures; main loop waits for all futures before shutdown
- **Alternatives Considered:**
  - **Alternative A (Manual thread management):** Spawn `threading.Thread` per worker, manage lifecycle manually; more control but error-prone (thread leaks)
  - **Alternative B (Thread pool via queue.Queue + daemon threads):** Custom pool implementation; educational but reinvents wheel, harder to debug
  - **Alternative C (ProcessPoolExecutor):** True parallelism via multiprocessing; overkill for I/O-bound agents, harder to pass objects between processes (pickle overhead)
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Standard library solution, automatic thread lifecycle management, futures API simplifies error handling (`future.result(timeout)`), easy to test (can mock executor)
  - ❌ **Cons:** Less control than manual threads, futures add slight abstraction overhead, need to understand executor shutdown semantics
- **Rationale:** ThreadPoolExecutor is production-grade pattern; automatic cleanup prevents thread leaks; futures API allows graceful shutdown (wait for in-flight work); instructor familiar with pattern
- **Implementation:** Orchestrator spawns executor on startup with `max_workers` from config; each queue task submitted via `executor.submit(worker_fn, task)`; main loop calls `executor.shutdown(wait=True)` on exit
- **Related Missions:** M7.3 (Orchestrator & Worker Threads), M7.11 (concurrency verification), M7.12 (resilience to worker failures)
- **Configuration:** `orchestrator.max_workers: 5` in `config/settings.yaml`; allows scaling to handle more route steps concurrently

### **ADR-008: Transaction ID (TID) Propagation** [NEW - 2024-11-22]
- **Status:** Accepted
- **Context:** Multi-threaded system with concurrent agent processing requires correlation of logs across threads, end-to-end request tracing, and debugging capability for race conditions
- **Decision:** Every operation carries a Transaction ID (TID) from route fetch to final output; TID format: `{timestamp}_{uuid4().hex[:8]}`; passed through all components; logged in every message
- **Alternatives Considered:**
  - **Alternative A (No correlation IDs):** Simpler code, no parameter passing; but can't correlate logs across threads, debugging nightmares, can't trace specific requests
  - **Alternative B (Thread-local storage):** No explicit parameter passing, automatic context; but magic behavior (implicit), harder to test, doesn't work with ThreadPoolExecutor (thread reuse)
  - **Alternative C (Correlation via timestamps):** No extra IDs, use timestamps; but ambiguous (multiple requests same second), fragile, not unique
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Distributed tracing (correlate logs across all threads), debuggability (filter logs by TID), observability (checkpoint files organized by TID), audit trail (full trace per request), testing (verify interactions via TID)
  - ❌ **Cons:** Slight overhead (+8 bytes per log entry), must pass TID through all function calls (parameter pollution)
- **Rationale:** TID propagation essential for production systems; multi-threaded logging without correlation is useless; debugging race conditions requires request tracing; minimal overhead for massive observability gain; industry standard pattern (OpenTelemetry, Zipkin)
- **Implementation:** Generate at route fetch: `tid = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"`;  propagate as parameter; log in every message; create checkpoint directory per TID
- **Related Missions:** M7.1 (TID generation), M7.2-7.7 (TID propagation), M7.11 (TID correlation in tests)

### **ADR-009: File-Based Checkpoints at Every Stage** [NEW - 2024-11-22]
- **Status:** Accepted
- **Context:** Complex pipeline (route → schedule → agents → judge → output) makes debugging hard; need to inspect intermediate state, replay from mid-pipeline, verify component outputs independently
- **Decision:** Each pipeline stage writes intermediate results to `output/checkpoints/{TID}/`; files: `00_route.json`, `01_scheduler_queue.json`, `02_agent_search_{type}.json`, `03_agent_fetch_{type}.json`, `04_judge_decision.json`, `05_final_output.json`
- **Alternatives Considered:**
  - **Alternative A (No checkpoints, logs only):** No disk I/O overhead, simpler code; but can't replay pipeline, can't inspect intermediate state, debugging requires printf-style log reading
  - **Alternative B (In-memory checkpoints):** Faster (no disk I/O), still enables replay; but lost on crash, not persistent, can't inspect between runs
  - **Alternative C (Database storage):** Queryable, structured, persistent; but over-engineering, requires DB setup, not file-based
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Replay capability (restart from any checkpoint), debugging (inspect intermediate state), audit trail (full trace of decisions), testing (verify component outputs against expected files), observability (see exactly what each component produced)
  - ❌ **Cons:** Disk I/O overhead (~50ms total per route), disk space (~500KB per route), management (need pruning strategy for old checkpoints)
- **Rationale:** Checkpoints invaluable for debugging complex pipelines; replay from mid-pipeline speeds development (don't re-run slow API calls); golden file testing verifies component contracts; audit trail proves system behavior (grading evidence); disk I/O overhead negligible vs API latency (100-500ms); can disable via config for performance testing
- **Implementation:** CheckpointManager writes/reads JSON files; auto-prune checkpoints >7 days old; configurable enable/disable
- **Related Missions:** M7.1-7.8 (write checkpoints), M7.10 (verify checkpoint files), M8.1 (read checkpoints for metrics)

### **ADR-010: Circuit Breaker for External APIs** [NEW - 2024-11-22]
- **Status:** Accepted
- **Context:** External APIs (Google Maps, YouTube, Spotify, Wikipedia) may fail (timeouts, rate limits, server errors); retrying failed API repeatedly wastes time and quota; need fail-fast when API down
- **Decision:** Implement circuit breaker pattern for all external API calls; 3 states: CLOSED (normal), OPEN (failing, no calls), HALF_OPEN (testing recovery); failure threshold: 5 consecutive failures → OPEN; timeout: 60s in OPEN → HALF_OPEN; success in HALF_OPEN → CLOSED
- **Alternatives Considered:**
  - **Alternative A (Retry logic only):** Simpler, handles transient failures; but wastes time on persistent failures, no fail-fast, eats API quota
  - **Alternative B (Manual disable flag):** Simple implementation (user sets flag if API down); but requires manual intervention, not automatic, poor UX
  - **Alternative C (Rate limiter only):** Prevents quota exhaustion; but doesn't handle failures, different problem domain
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Fail fast (stop hitting failing API immediately), auto-recovery (automatically test API health after timeout), resilience (prevent cascading failures), observability (circuit state logged), graceful degradation (fallback to cached/mock data when circuit OPEN)
  - ❌ **Cons:** Added complexity (state machine to maintain), configuration (tune failure threshold and timeout), false opens (transient blips may open circuit)
- **Rationale:** Circuit breakers are production-grade resilience pattern; prevent wasting time on failing APIs; automatic recovery testing (no manual intervention); graceful degradation (use cached data when API down); standard pattern (Hystrix, resilience4j); minimal overhead (state machine check <1ms)
- **Implementation:** CircuitBreaker class wraps API calls; state machine (CLOSED/OPEN/HALF_OPEN); log state transitions; configurable thresholds
- **Related Missions:** M7.1 (wrap Google Maps), M7.4-7.6 (wrap agent APIs), M7.12 (resilience tests)

### **ADR-011: Metrics Aggregator (Separate from Logging)** [NEW - 2024-11-22]
- **Status:** Accepted
- **Context:** Need to track performance metrics (API call counts, latencies, queue depth, worker utilization) for cost analysis and performance optimization; logs are for debugging, metrics are for monitoring; mixing them degrades both
- **Decision:** Separate metrics collection from logging; implement MetricsCollector that aggregates counters (API calls), timers (latencies), gauges (queue depth); writes to `logs/metrics.json` (live updates); thread-safe via `threading.Lock`
- **Alternatives Considered:**
  - **Alternative A (Metrics in logs):** Single system, simpler, no extra code; but pollutes logs with metrics, hard to extract, not queryable, poor performance (string parsing)
  - **Alternative B (Third-party metrics like Prometheus):** Industry standard, powerful querying, dashboards; but over-engineering, requires server, not file-based, adds dependency
  - **Alternative C (No metrics):** Simplest, zero overhead; but can't track API costs, can't measure performance, fails cost control requirement (KPI #6)
- **Consequences (Trade-offs):**
  - ✅ **Pros:** Separation of concerns (logs for debugging, metrics for monitoring), performance (JSON easier to parse than log files), queryable (jq queries), live updates (metrics updated real-time), cost tracking (API call counts for KPI #6), research (latencies/queue depth for M8.1)
  - ❌ **Cons:** Separate system to maintain, thread-safety needs locking (slight overhead), not real-time monitoring (just file watching)
- **Rationale:** Separate metrics aggregator is best practice; logs and metrics serve different audiences (devs vs ops); JSON metrics easier to query than log parsing; enables cost tracking (required for KPI #6); supports research analysis (M8.1: performance studies); standard pattern (Prometheus, StatsD separate from logging)
- **Implementation:** MetricsCollector with thread-safe increment/record/set methods; write to JSON file; counters (API calls), timers (latencies), gauges (queue depth); query with jq
- **Related Missions:** M5 (metrics collection framework), M7.1-7.7 (metrics recording), M8.1 (metrics consumption for research), M8.2 (cost analysis from metrics)

### **ADR-012: LLM Client Abstraction (Priority, Budget Guards)** [NEW - 2025-11-24]
- **Status:** Accepted
- **Context:** Judge can optionally use LLM scoring. We need a unified, cost-aware interface with provider priority, budget/timeout/backoff guards, prompt redaction, and heuristic fallback.
- **Decision:** Support providers via factory: **Claude > OpenAI > Gemini > Ollama > Mock**. Enforce prompt-length guards (`llm_max_tokens`) and optional budget guards. Default `use_llm=true`.
- **Consequences:** Unified interface; safe defaults; fails safe to heuristics.
- **Implementation:** `src/hw4_tourguide/tools/llm_client.py`

### **ADR-013: Agent Intelligence via Markdown-Defined LLM Prompts** [NEW - 2024-11-26]
- **Status:** Accepted
- **Context:** Agents currently use simple heuristics. We want semantic understanding for query generation while maintaining control.
- **Decision:** Implement **markdown-defined agent prompts** (`.claude/agents/*.md`) with `PromptLoader` utility.
- **Consequences:** Rapid iteration (no code changes for prompts); semantic intelligence; fallback safety to heuristics.
- **Implementation:** `src/hw4_tourguide/tools/prompt_loader.py`, `base_agent.py` integration.

## 7. Delivery Plan & Timeline
| Milestone | Due | Description | Evidence |
|-----------|-----|-------------|----------|
| M1 | Nov 26 | Architecture package, repo scaffold, PRD draft | PRD commit, repo tree |
| M2 | Nov 29 | Scheduler/orchestrator, route provider, logging | `pytest tests/test_scheduler.py`, logs |
| M3 | Dec 1 | Agents + judge, output pipeline | `pytest tests/test_agents.py`, sample output |
| M4 | Dec 4 | Packaging, CLI, tests, docs, preflight | `pip install .`, `python -m hw4_tourguide`, `pytest --cov` |

## 8. Installation & Verification Matrix
| Step | Action | Command | Expected Result | Recovery |
|------|--------|---------|-----------------|----------|
| 1 | Clone repo | `git clone https://github.com/igornazarenko434/LLM_Agent_Orchestration_HW4.git && cd LLM_Agent_Orchestration_HW4` | Workspace matches GitHub; `src/hw4_tourguide` visible | Check network/URL, retry clone |
| 2 | Check Python | `python3 --version` | "Python 3.10.19+" | Install Python 3.10.19+ (3.11+ recommended) |
| 3 | Create venv | `python -m venv .venv && source .venv/bin/activate` | Prompt shows `(.venv)` | Re-run with correct Python |
| 4 | Install package | `pip install .` | Package metadata printed | Inspect `pyproject.toml` |
| 5 | Verify config | `ls config/settings.yaml` | File listed | Copy template from repo |
| 6 | Copy env | `cp .env.example .env` | `.env` created | Edit `.env` manually |
| 7 | Create dirs | `mkdir -p output data/routes` | Dirs exist | Check permissions |
| 8 | Check Deps | `pip check` | "No broken requirements found" | Install missing deps |
| 9 | Run tests | `pytest` | All tests pass, coverage summary | Use `pytest -k` to isolate |
|10 | Live run | `python -m hw4_tourguide --from "A" --to "B" --mode live` | Logs + output JSON | Switch to cached mode |
|11 | Cached run | `python -m hw4_tourguide --from "A" --to "B" --mode cached` | Reuses stored route | Ensure cached file exists |

**Packaging Notes:**
- **`pyproject.toml`:** Defines project metadata and runtime assets (config/routes) included in the **Wheel** for end-users.
- **`MANIFEST.in`:** Defines inclusion rules for the **Source Distribution** (sdist), ensuring developers get docs, tests, and scripts.
- **Portability:** The system supports both repository-based execution (hot-reloading config) and installed library execution (using bundled fallbacks).

## 9. Risks & Mitigations
| Risk | Impact | Prob. | Mitigation |
|------|--------|-------|------------|
| Google Maps quota exhaustion | High | Medium | Cached mode default, metrics logging, fallback route |
| Concurrency bugs | High | Medium | Thread-safe queue, futures, dedicated tests & logs |
| LLM/search cost spike | Medium | Medium | Mock mode, config toggles, reliance on free sources |
| Packaging failure | Medium | Low | Preflight script, clean install tests, README matrix |
| Logging overhead | Low | Medium | Configurable log levels, rotation, sample size checks |

## 10. Data, Integrations, Extensibility
- **Data Contracts:** JSON schemas for scheduler tasks, agent outputs, judge decisions, final route file stored under `docs/contracts/`.
- **Integrations:** Google Maps (Directions/Geocoding), YouTube, Spotify, Wikipedia, DuckDuckGo, LLM APIs (OpenAI/Anthropic/Gemini); all go through typed clients with retries.
- **Extensibility:** Agent registry in config; base classes documented; route provider abstraction for future APIs.

## 11. Configuration & Security
- Centralized YAML config controlling scheduler cadence, agent params, search limits, logging, LLM mode, output paths.
- `.env.example` documents secrets; `.env` loaded via `python-dotenv` or custom loader.
- Secrets never logged; HTTP requests use HTTPS; timeouts & retries enforced.
- File permissions for logs/output limited to user; CLI flags override config for experimentation.

## 12. Testing & QA Strategy

### Test Categories & Coverage Targets
| Category | Files | Target Coverage | Key Tests | Markers |
|----------|-------|-----------------|-----------|---------|
| Unit Tests | `tests/test_*.py` | ≥85% | Config, Logging, Agents, Output | `unit` |
| Integration Tests | `tests/test_integration.py` | ≥80% | Full pipeline (cached mode) | `integration` |
| Concurrency Tests | `tests/test_concurrency.py` | N/A | Agent overlap, queue thread-safety | `concurrency` |
| Resilience Tests | `tests/test_resilience.py` | N/A | Retry, timeout, circuit breaker | `resilience` |
| CLI Tests | `tests/test_cli.py` | ≥70% | Argument parsing, exit codes | `unit` |
| **LLM Tests** | `tests/test_llm.py` | ≥85% | Provider factory, budget guards | `unit` |

### ISO/IEC 25010 Reliability Verification
The testing strategy explicitly targets key reliability characteristics, matching the `README.md` quality standards:
1.  **Fault Tolerance:** Verified by `tests/test_circuit_breaker.py` and `tests/test_resilience.py`. Ensures the system fails fast (Circuit Open) during outages and gracefully degrades.
2.  **Recoverability:** Verified by `tests/test_file_interface.py` (checkpoints) and `tests/test_resilience.py` (backoff). Ensures resumption from intermediate states and recovery from transient errors.
3.  **Maturity:** Verified by high coverage (~87%) across core logic (`test_orchestrator.py`, `test_scheduler.py`) and error handling (`test_route_provider_errors.py`).
4.  **Availability:** Verified by `tests/test_concurrency.py`. Ensures the system remains responsive and processes tasks in parallel under load.

### Edge Cases & Test Data Strategy
**Edge Case Tests** (≥5 scenarios per module):
1. **Config Loader Edge Cases:**
   - Missing `config/settings.yaml` → fallback to package defaults (Verified by `test_config_loader.py`).
   - Invalid YAML syntax or types → ConfigError with fallback (Verified by `test_config_loader.py`).
   - Missing required env vars → fallback to cached/mock mode.

2. **Route Provider Edge Cases:**
   - Invalid from/to addresses → API error handling (Verified by `test_route_provider_errors.py`).
   - Empty route (0 steps) or Quota Exceeded → Graceful exit (Verified by `test_route_provider_errors.py`).
   - Missing cache file → Fallback to packaged demo route.

3. **LLM & Agent Edge Cases:**
   - **Token Limit/Context Window:** Agent budget guards prevent overflow; fallback to heuristics (Verified by `test_llm.py`).
   - **Malformed JSON:** LLM returns text/markdown instead of JSON → Defensive parsing strategies (Verified by `test_json_extraction.py`).
   - **Empty Results:** Search returns 0 candidates → Agent returns "unavailable" status without crashing (Verified by `test_base_agent.py`).
   - **Secondary Source Fallback:** Primary API fails → Switch to backup (e.g., SongAgent uses YouTube if Spotify fails) (Verified by `test_agent_secondary.py`).

4. **Judge Edge Cases:**
   - All agents fail → Judge scores 0 with rationale "No content available" (Verified by `test_judge.py`).
   - LLM Timeout/Failure → Fallback to heuristic-only scoring (Verified by `test_judge.py`).

5. **Resilience & Concurrency Edge Cases:**
   - **Circuit Breaker:** Transitions from CLOSED → OPEN → HALF_OPEN → CLOSED on failures/successes (Verified by `test_circuit_breaker.py`).
   - **Worker Failure:** One worker thread crashes → Orchestrator catches exception, logs error, and continues others (Verified by `test_concurrency.py`).

### Test Data Sources
- **Cached Routes:** `data/routes/demo_boston_mit.json` (shipped in package for offline testing).
- **Programmatic Stubs:** Mock clients defined in `tests/` (e.g., `StubVideoClient`, `StubSongClient`) to simulate API responses and failures (`fail_once=True`).
- **Fixtures:** `tests/conftest.py` provides shared mocks, configuration, and sample route data.

### Verification Scripts
- `scripts/preflight.py` - Comprehensive system readiness check (Build, Tests, Git, Runtime).
- `scripts/check_readme.py` - Validates README structure.
- `scripts/check_scheduler_interval.py` - Verifies scheduler timing accuracy.
- `scripts/check_api_usage.py` - Verifies API call counts and cost limits.
- `scripts/diagnose_llm_query_generation.py` - Validates LLM query generation logic.
- Manual verification via `grep` (logs), `jq` (metrics/output), and `pytest` as defined in Goals & KPIs.

### CI/CD Readiness
- Tests run in <2 minutes (using cached routes, mocked APIs)
- Coverage report generated: `htmlcov/index.html`
- Exit code 0 if all tests pass, 1 if any fail
- Optional lint checks: `ruff check src/` (if time permits)

## 13. Research & Analysis Plan

### Study 1: Orchestration Efficiency & Concurrency

**Objective:** Measure parallelism, queue depth, and system throughput to validate multi-threaded architecture (ADR-002, ADR-007).

**Parameters to Sweep:**
- `orchestrator.max_workers`: [1, 3, 5, 10] workers
- `scheduler.interval`: [0.5s, 1.0s, 2.0s, 5.0s]
- Route length: [2, 5, 10, 20] steps

**Data Collection:**
- Scheduler: Log `queue_depth` after each emit (current queue size)
- Orchestrator: Log `worker_active_count` on each dispatch
- Agents: Log `start_timestamp`, `end_timestamp` per agent call
- System: Total run time, throughput (steps/second)

**Metrics & Formulas:**
```
Agent Overlap Ratio = (sum of overlapping time windows) / (total agent execution time)
                    = Σ overlap(agent_i, agent_j) / Σ duration(agent_k)

Queue Utilization = average(queue_depth) / max_queue_size

Throughput = route_steps / total_run_time  (steps/second)

Speedup = T_sequential / T_parallel  (ideal: ≈ num_agents = 3)
```

**Visualizations:**
1. **Gantt Chart:** Timeline showing scheduler emits, orchestrator dispatches, and agent execution (color-coded by agent type)
2. **Line Plot:** Queue depth over time with scheduler emits marked
3. **Bar Chart:** Total run time vs `max_workers` (5 routes × 4 worker configs)
4. **Heatmap:** Agent overlap matrix (Video×Song, Video×Knowledge, Song×Knowledge)

**Expected Results:** `max_workers=5` optimal for 3 agents; queue depth <3 most of time; agent overlap ≥60% proves concurrency.

---

### Study 2: Cost Analysis & API Usage Tracking

**Objective:** Quantify API costs and validate caching strategy (ADR-003) reduces costs by 90%+.

**Parameters:**
- Mode: [live, cached]
- Route length: [2, 5, 10] steps
- Runs: 5 repetitions per configuration

**Data Collection (logs/metrics.json):**
```json
{
  "api_calls": {
    "google_maps": {"count": X, "cost_per_call": 0.005, "total_cost": Y},
    "youtube": {"count": X, "cost_per_call": 0.0, "total_cost": 0.0},
    "wikipedia": {"count": X, "cost_per_call": 0.0, "total_cost": 0.0},
    "llm_tokens": {"prompt": X, "completion": Y, "cost_per_1k": 0.002, "total_cost": Z}
  }
}
```

**Formulas:**
```
Cost Savings = (Cost_live - Cost_cached) / Cost_live × 100%

Expected: Cost_live = 0.005 × 3 calls = $0.015 per route
         Cost_cached = $0.00
         Savings = 100%

API Call Density = total_api_calls / route_steps  (calls per step)

Token Efficiency = useful_output_chars / total_tokens  (if LLM used)
```

**Visualizations:**
1. **Stacked Bar Chart:** API call counts by type (Maps/YouTube/Wikipedia/LLM) for live vs cached
2. **Line Plot:** Cumulative cost over 100 route runs (live vs cached modes)
3. **Pie Chart:** Cost breakdown by API source in live mode
4. **Table:** Cost projections for 10/100/1000 routes

**Target:** Cache reduces Maps API calls to 0; total live cost <$0.02/route; cached cost $0.00.

---

### Study 3: Judge LLM Impact Analysis

**Objective:** Compare heuristic-only vs LLM-assisted judge scoring to justify LLM cost.

**Parameters:**
- Judge mode: [heuristic_only, llm_assisted]
- Routes: 5 different routes (Boston-MIT, Cambridge-Harvard, etc.)
- Runs: 3 repetitions per configuration

**Metrics:**
- **Score Variance:** Standard deviation of judge scores across runs
- **Rationale Quality:** Character count + keyword richness (presence of "relevant", "quality", "diversity")
- **Human Agreement:** Manual review of 10 judge decisions, rate 1-5 for "helpfulness"
- **Cost:** Total LLM tokens used × $0.002/1k tokens

**Formulas:**
```
Score Stability = 1 - (stdev(scores) / mean(scores))

Rationale Quality Score = char_count × keyword_match_count / 100

Cost per Decision = (prompt_tokens + completion_tokens) / 1000 × 0.002
```

**Visualizations:**
1. **Box Plot:** Judge score distributions (heuristic vs LLM) across 5 routes
2. **Scatter Plot:** Score variance vs rationale quality (X=variance, Y=quality, color=mode)
3. **Bar Chart:** Human agreement ratings (1-5 scale) for heuristic vs LLM
4. **Table:** Cost-benefit analysis (LLM cost vs quality gain)

**Expected Results:** LLM reduces score variance by 20%; rationale 2× longer; cost <$0.01/route; justify if quality gain matters.

---

### Study 4: Parameter Sensitivity Analysis

**Objective:** Identify optimal configuration parameters and validate system robustness to config changes.

**Parameters to Sweep:**
| Parameter | Values | Expected Impact |
|-----------|--------|-----------------|
| `scheduler.interval` | [0.5, 1.0, 2.0, 5.0] s | Lower = faster but more queue contention |
| `orchestrator.max_workers` | [1, 3, 5, 10] | Higher = more parallelism but diminishing returns |
| `agent.search_limit` | [1, 3, 5] | Higher = better choices but more API calls |
| `judge.heuristic_weight` | [0.3, 0.5, 0.7] | Balance heuristic vs LLM scoring |
| `agent.timeout` | [5, 10, 30] s | Higher = fewer timeouts but slower |

**Analysis Method:**
For each parameter, vary it while keeping others constant. Measure:
- **Performance:** Total run time, throughput (steps/second)
- **Quality:** Judge scores, agent success rate (non-timeout %)
- **Cost:** Total API calls, LLM tokens

**Formulas:**
```
Sensitivity = Δ Metric / Δ Parameter

Example: If max_workers increases from 3→5 and run_time decreases from 60s→45s:
  Sensitivity = (45-60) / (5-3) = -7.5 s/worker  (negative = faster)

Optimal Parameter = argmax(Quality / Cost)
```

**Visualizations:**
1. **Line Plot:** Run time vs `scheduler.interval` (with confidence intervals from 5 runs)
2. **Line Plot:** Agent success rate vs `agent.timeout`
3. **Heatmap:** Quality score for all combinations of `max_workers` × `search_limit`
4. **Pareto Front:** Cost vs Quality scatter plot (identify optimal trade-off points)

**Deliverables:** Recommended config values in `config/settings.yaml` based on analysis; document trade-offs in `docs/analysis/parameter_sensitivity.md`.

---

### Notebook Structure (`docs/analysis/results.ipynb`)

**Cell 1:** Imports & Setup
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path
```

**Cell 2:** Load Data
```python
# Load metrics from multiple runs
metrics = [json.load(open(f"logs/run_{i}_metrics.json")) for i in range(5)]
df = pd.DataFrame(metrics)
```

**Cell 3:** Study 1 - Orchestration Efficiency (+ LaTeX formulas)
**Cell 4:** Study 1 - Visualizations (Gantt, queue depth, speedup)
**Cell 5:** Study 2 - Cost Analysis (+ LaTeX formulas)
**Cell 6:** Study 2 - Visualizations (cost breakdown, savings)
**Cell 7:** Study 3 - Judge LLM Impact (+ LaTeX formulas)
**Cell 8:** Study 3 - Visualizations (box plots, scatter)
**Cell 9:** Study 4 - Parameter Sensitivity (+ LaTeX formulas)
**Cell 10:** Study 4 - Visualizations (line plots, heatmap, Pareto front)
**Cell 11:** Conclusions & Recommendations

**LaTeX Formulas (≥2 required):**
```latex
\text{Agent Overlap Ratio} = \frac{\sum_{i \neq j} \text{overlap}(t_i, t_j)}{\sum_{k} \text{duration}(t_k)}

\text{Cost Savings} = \frac{\text{Cost}_{\text{live}} - \text{Cost}_{\text{cached}}}{\text{Cost}_{\text{live}}} \times 100\%

\text{Speedup} = \frac{T_{\text{sequential}}}{T_{\text{parallel}}}

\text{Throughput} = \frac{\text{route steps}}{\text{total run time}} \quad \text{(steps/s)}
```

**Plot Types (≥4 required):**
1. **Bar Charts:** API call counts, run times, cost comparisons
2. **Line Plots:** Queue depth over time, cumulative costs, parameter sensitivity curves
3. **Scatter Plots:** Score variance vs quality, Pareto fronts (cost vs quality)
4. **Heatmaps:** Agent overlap matrix, parameter combination quality scores
5. **Box Plots:** Judge score distributions across modes

**Statistical Analysis:**
- Mean, median, standard deviation for all metrics
- 95% confidence intervals on performance measurements (from 5 runs)
- Correlation analysis: `scheduler.interval` vs `throughput`, `max_workers` vs `speedup`
- Hypothesis testing: "LLM judge scores significantly different from heuristic?" (t-test, p<0.05)

## 14. Documentation & Deliverables
- `README.md` (≥15 sections) acting as a full user manual: overview, install matrix, env setup, CLI flags, configuration guide, troubleshooting, contribution guidelines, license/credits, UX heuristics summary, screenshots/log samples, and grading checklist.
- `PRD_Route_Enrichment_Tour_Guide_System.md` (this document) with evidence matrix.
- `Missions_Route_Enrichment_Tour_Guide_System.md` detailing mission steps, definitions of done, quality gates.
- `PROGRESS_TRACKER.md` for execution tracking.
- `docs/architecture/` with C4 diagrams (Context/Container/Component/Deployment) and ADR register.
- `docs/api_reference.md` describing every public CLI/JSON contract per Microsoft REST/ISO guidelines.
- `docs/analysis/results.ipynb` (or markdown export) capturing research experiments, LaTeX formulas, and plots.
- `docs/cost_analysis.md` presenting token/API usage tables plus optimization strategies.
- `docs/ux/heuristics.md` documenting UX heuristics and CLI usability principles applied to the system with terminal output evidence.
- `data/routes//demo_boston_mit.json` demo route for offline cache testing.
- `docs/prompt_log/` (prompt journal) documenting significant LLM prompts and iterations.
- `.claude` knowledge base storing key decisions and context.

## 14a. CLI Usability Principles – Applied to Tour-Guide System

This section documents CLI usability principles for the Route Enrichment Tour-Guide System, demonstrating usability best practices for command-line interfaces.

| # | Principle | Application to Tour-Guide System | Evidence / Implementation | CLI/Output Example |
|---|-----------|----------------------------------|---------------------------|---------------------|
| 1 | **Clear Help Text** | Comprehensive `--help` with examples and descriptions for every flag | Help text includes usage patterns, option descriptions, and example commands | `--help` output:<br>`--from FROM  Starting location (e.g., "Boston, MA")`<br>`--to TO      Destination (e.g., "Cambridge, MA")`<br>`--mode MODE  Run mode: live or cached (default: cached)` |
| 2 | **Intuitive Commands** | Standard POSIX conventions for flags (`--from`, `--to`, `--mode`, `--help`); no cryptic abbreviations | All flags use descriptive long-form names with optional short forms where standard (`-h` for help, `-v` for version) | Uses `--mode cached` not `-m c`; follows GNU/POSIX patterns |
| 3 | **Helpful Error Messages** | Specific errors with suggested fixes and recovery steps | Error messages explain what failed, why it failed, and how to fix it; include references to documentation | `ConfigError: Missing 'scheduler.interval' in config/settings.yaml`<br>`→ Solution: Add 'scheduler.interval: 2.0' or see docs/api_reference.md` |
| 4 | **Consistent Flags** | Standard flags across all commands (`-h/--help`, `-v/--version`, `--verbose`, `--log-level`) | All flags follow industry conventions; consistent naming patterns | `--help`, `--version`, `--log-level DEBUG`, `--output path/to/file.json` |
| 5 | **Progress Indicators** | Real-time log streaming... | Structured logs display system state... | Logs: `...INFO | Scheduler | EMIT...`<br>`...INFO | Orchestrator | DISPATCH...` |
| 6 | **Graceful Interruption** | Checkpoints save progress at every step... | Intermediate JSON files written to `output/checkpoints/`; resume possible from last step | User presses Ctrl+C → Checkpoints exist on disk for partial route |
| 7 | **Configuration Flexibility** | YAML config for power users... | Config file supports all parameters... | Power user: edits `config/settings.yaml`... |
| 8 | **Minimal Terminal Clutter** | Logs saved to files by default... | Stdout: structured INFO logs... | Terminal: `2024-11-28... | INFO | Scheduler...` |

**Evidence Files:**
- `docs/ux/heuristics.md` - Full UX heuristics and CLI usability documentation with terminal output examples
- `docs/screenshots/` - Terminal captures showing help text, error messages, progress indicators, graceful interruption
- `README.md` - Sections: CLI Usage (Principle #1-4), Troubleshooting (Principle #3), Configuration (Principle #7)
- `logs/system.log` - Demonstrates Principle #5 (progress indicators) with structured, timestamped events
- `python -m hw4_tourguide --help` - Demonstrates Principle #1 (clear help text) with comprehensive option documentation

## 15. Evidence Matrix

This matrix maps every KPI, Functional Requirement, Non-Functional Requirement, User Story, and Quality Gate to concrete verification evidence.

| # | Category | Claim | Evidence Artifact | Verification Command | Expected Output | Location |
|---|----------|-------|-------------------|----------------------|-----------------|----------|
| 1 | KPI-1 | Package installable via pip | Installation log, help output | `pip install . && python -m hw4_tourguide --help` | Package installs without errors, help text displays CLI options | Installation matrix step 3 |
| 2 | KPI-2 | Config centralized in YAML | settings.yaml file | `wc -l config/settings.yaml && grep -R -n "os.environ" src/` | ≥20 lines in YAML, zero hard-coded env lookups | Section 11, M3.1 |
| 3 | KPI-3 | Google Maps reliability | Live + cached run logs | `python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode live --output output/live_run_kpi3.json && python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode cached --output output/cached_run_kpi3.json && ls output/live_run_kpi3.json output/cached_run_kpi3.json` | Both commands exit 0, output/live_run_kpi3.json and output/cached_run_kpi3.json are created. | Section 7, M7.1 |
| 4 | KPI-4 | Scheduler cadence accuracy | Interval check script output | `python scripts/check_scheduler_interval.py output/*_Boston_MA_to_MIT/logs/system.log` | `Script reports "All scheduler intervals are within X.Xs +/-0.2s." and exits with code 0.` | Section 13, M7.2 |
| 5 | KPI-5 | Agent concurrency | Concurrency test output | `pytest tests/test_concurrency.py -m concurrency -v` | `Test passes, asserting overlapping agent execution within test logs.` | M7.11, tests/ |
| 6 | KPI-6 | Search/fetch cost control | Metrics JSON, check script output | `python scripts/check_api_usage.py output/*_Boston_MA_to_MIT/logs/metrics.json` | `Script output confirms "Google Maps API calls: 0 (Expected <= 0 for cached run context)." and "LLM Query Generation calls: X (Reasonable for typical run)."` | M5, docs/cost_analysis.md |
| 7 | KPI-7 | Judge scoring completeness | Final route JSON | `jq '.[].judge.overall_score' output/*_Boston_MA_to_MIT/final_route.json | wc -l` | `4 (matching the number of steps in the demo route)` | M7.7, output/ |
| 8 | KPI-8 | Logging coverage | System log file | `grep -E "Scheduler|Orchestrator|Agent|Judge|Error" output/*_Boston_MA_to_MIT/logs/system.log | wc -l` | `≥50 structured log entries per run` | M3.2, logs/ |
| 9 | KPI-9 | CLI execution success | Exit code, output artifacts | `python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode cached --output output/my_kpi_demo.json && echo $? && ls output/my_kpi_demo.{json,md,csv}` | `0 (exit code) is printed, and output/my_kpi_demo.json, .md, .csv are listed.` | M7.9, output/ |
| 10 | KPI-10 | Test coverage | Coverage report | `pytest --cov=hw4_tourguide --cov-report=term` | `≥85% line coverage` | M4.2, htmlcov/ |
| 11 | KPI-11 | Retry/backoff logic | Resilience test log | `pytest tests/test_resilience.py -k retry -v` | `Tests pass, log shows 3 retry attempts with backoff` | M7.12, logs/ |
| 12 | KPI-12 | README completeness | README validation script | `python scripts/check_readme.py README.md` | `Script reports "README.md check completed successfully"` | M8.3, README.md |
| 13 | KPI-13 | Cost transparency | Cost analysis doc | `ls docs/cost_analysis.md && grep -c "^|" docs/cost_analysis.md` | `Doc exists with ≥2 tables (API calls, token usage)` | M8.2 |
| 14 | KPI-14 | System Readiness (Preflight) | Preflight script output | `python scripts/preflight.py` | `Preflight checklist passes all stages: Build, Config, Tests (>85% cov), Git Health, and Runtime Verification (Scheduler/API Checks). Final Verdict: ✅ READY FOR FLIGHT!` | M9.1 |
| 15 | FR-001 | Route retrieval (live+cached) | Route provider tests, JSON output | `python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode live --output output/live_run_fr1.json && python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode cached --output output/cached_run_fr1.json && ls output/live_run_fr1.json output/cached_run_fr1.json && jq '.[0].metadata.transaction_id' output/live_run_fr1.json` | Both commands exit 0; output/live_run_fr1.json and output/cached_run_fr1.json exist; a transaction ID is present in the live run's JSON. | M7.1 |
| 16 | FR-002 | Scheduler thread + queue | Scheduler tests, log entries | `pytest tests/test_scheduler.py -v` | Tests pass, confirming scheduler emits tasks at configured intervals. | M7.2 |
| 17 | FR-003 | Orchestrator worker threads | Orchestrator tests, worker logs | `pytest tests/test_orchestrator.py -v` | Tests pass, confirming orchestrator uses ThreadPoolExecutor for worker dispatch. | M7.3 |
| 18 | FR-004 | Video Agent search→fetch | Agent tests, YouTube API logs | `pytest tests/test_video_agent.py -v` | Tests pass, confirming VideoAgent's search and fetch pipeline. | M7.4 |
| 19 | FR-005 | Song Agent search→fetch | Agent tests, Spotify API logs | `pytest tests/test_song_agent.py -v` | Tests pass, confirming SongAgent's search and fetch pipeline. | M7.5 |
| 20 | FR-006 | Knowledge Agent search→fetch | Agent tests, Wikipedia API logs | `pytest tests/test_knowledge_agent.py -v` | Tests pass, confirming KnowledgeAgent's search and fetch pipeline. | M7.6 |
| 21 | FR-007 | Judge scoring + rationale | Judge tests, output JSON | `pytest tests/test_judge.py -v && jq '.[0].judge.rationale' output/*_Boston_MA_to_MIT/final_route.json` | Tests pass, judge rationale is present in the final output JSON. | M7.7 |
| 22 | FR-008 | Output writer (JSON+reports) | Output tests, file existence | `pytest tests/test_output_writer.py -v && ls output/*_Boston_MA_to_MIT/final_route.{json,md,csv}` | Tests pass, output JSON, Markdown, and CSV files exist in the run-specific directory. | M7.8 |
| 23 | FR-009 | CLI interface | CLI tests, help output | `python -m hw4_tourguide --help` | Help text shows all flags correctly (--from, --to, --mode, etc.) | M7.9 |
| 24 | NFR-1 | Reliability (retries) | Resilience test results | `pytest tests/test_resilience.py -v` | All resilience tests pass, confirming retry/backoff logic and graceful degradation. | M7.12 |
| 25 | NFR-2 | Performance (scheduler overhead) | Scheduler interval check | `python scripts/check_scheduler_interval.py output/*_Boston_MA_to_MIT/logs/system.log` | `Script reports that actual intervals are within tolerance (e.g., +/-0.2s of expected 2.0s).` | M7.2 |
| 26 | NFR-3 | Usability (README + help) | README file, CLI help | `python scripts/check_readme.py README.md && python -m hw4_tourguide --help` | `Script reports "README.md check completed successfully", and CLI help text displays correctly.` | M8.3 |
| 27 | NFR-4 | Security (secrets redacted) | Log file inspection | `grep -E "API_KEY|CLIENT_SECRET|password" output/*_Boston_MA_to_MIT/logs/system.log | grep -v "Masked: \*\*\*\*" ` | `No plaintext API keys, all sensitive info is masked (e.g., 'Masked: ****...last4') or absent.` | M3 |
| 28 | NFR-5 | Maintainability (modular design) | Module line counts | `find src/ -name "*.py" -exec wc -l {} \; | awk '{print $1}' | sort -nr | head -n 5` | `Manual code review confirms Python modules (150-600 LOC) have clear abstractions, type hints, and docstrings with separated concerns.` | Code review |
| 29 | NFR-6 | Portability (macOS/Linux) | Cross-platform test | `grep -R -E "/Users|/home" src/` | `No hardcoded absolute paths found; conceptual check confirms relative paths and cross-platform compatibility.` | CI logs |
| 30 | NFR-7 | Observability (structured logs) | Log format validation | `head -n 5 output/*_Boston_MA_to_MIT/logs/system.log` | `Log entries display the expected format: "TIMESTAMP | LEVEL | MODULE | EVENT_TAG | MESSAGE".` | M3.2 |
| 31 | NFR-8 | Configurability (YAML params) | Config file + loader tests | `grep -c ":" config/settings.yaml && pytest tests/test_config_loader.py` | `≥20 params, loader tests pass` | M3, M3.1 |
| 32 | NFR-9 | Extensibility (agent registry) | Config structure | `grep -E "^\s+video:|^\s+song:|^\s+knowledge:" config/settings.yaml | wc -l` | `Output shows 3, confirming video, song, and knowledge agents are configurable.` | Section 10, M3.1 |
| 33 | US-001 | Moshe enriched commute | Demo run output | `python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode cached --output output/us1_demo.json && jq '.[0].agents | keys' output/*_Boston_MA_to_MIT/final_route.json` | `Output JSON shows video/song/knowledge per step (e.g., keys "video", "song", "knowledge" present).` | M9.3 |
| 34 | US-002 | Danit exportable summaries | CSV + Markdown files | `python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode cached --output output/us2_demo.json && ls output/*_Boston_MA_to_MIT/final_route.{json,md,csv}` | `Output JSON, Markdown, and CSV files exist in the run-specific directory.` | M7.8 |
| 35 | US-003 | Instructor reproducible install | Preflight script output | `python scripts/preflight.py` | `Preflight check "Dependencies Build/Install" is ✅` | Section 8 |
| 36 | US-004 | Maps compliance cost control | Metrics file, cost analysis doc | `python scripts/check_api_usage.py output/*_Boston_MA_to_MIT/logs/metrics.json` | `Script output confirms Google Maps calls <= 0 for cached mode.` | M5, M8.2 |
| 37 | US-005 | QA/Ops retries & logs | Resilience tests, log snippets | `pytest tests/test_resilience.py -v && grep -E "RETRY|CircuitBreaker" output/*_Boston_MA_to_MIT/logs/system.log | wc -l` | `Resilience tests pass, and log shows retry/circuit breaker events.` | M7.12 |
| 38 | US-006 | Dev team mission tracking | Missions & Progress Tracker existence | `ls Missions_Route_Enrichment_Tour_Guide_System.md PROGRESS_TRACKER.md` | `Both files exist and are readable.` | M0 |
| 39 | QG-1 | Architecture Ready | Preflight script output | `python scripts/preflight.py` | `Preflight check "Documentation Files Exist" is ✅ and "Config Files Exist" is ✅.` | M1, M2.0-2.2 |
| 40 | QG-2 | Foundation Secure & Observable | Config + logging tests | `pytest tests/test_config_loader.py tests/test_logging.py` | Tests pass, secrets redacted, logs structured | M3, M3.1, M3.2 |
| 41 | QG-3 | Testing Foundation Verified | Test framework + coverage | `pytest --cov=hw4_tourguide` | Coverage ≥85% | M4.1, M4.2 |
| 42 | QG-4 | Core Implementation Complete | All feature tests | `pytest tests/test_*.py -v` | All tests pass | M7.1-7.12 |
| 43 | QG-5 | Submission Ready | Preflight script | `python scripts/preflight.py` | All checks ✅, exit code 0 | M9.1 |
| 44 | M7.14 | Agent Prompt Infrastructure | Prompt loader tests | `pytest tests/test_prompt_loader.py -v` | Tests pass, templates loaded | M7.14 |
| 45 | M7.15 | LLM Query Generation | Agent LLM tests | `pytest tests/test_agent_llm_queries.py -v` | LLM generates queries, fallback works | M7.15 |
| 46 | M7.16 | Judge LLM Scoring | Judge tests | `pytest tests/test_judge.py -k llm -v` | Judge uses markdown prompt | M7.16 |

**Evidence Artifact Locations:**
- `output/` - Final route JSON, Markdown summaries, CSV exports, demo runs
- `tests/` - All test modules with unit, integration, concurrency, resilience tests
- `docs/` - Architecture diagrams, cost analysis, research notebook, UX heuristics
- `scripts/` - Verification scripts (check_scheduler_interval.py, check_api_usage.py, check_readme.py, preflight.py)

## 16. Quality Gates (per Kickoff v2.1)
1. **QG1 Architecture Ready:** PRD + ADRs approved before coding.
2. **QG2 Scheduler/Orchestrator Functional:** Pass scheduler tests + logging proof.
3. **QG3 Agents & Judge Verified:** Unit tests + sample outputs, cost metrics recorded.
4. **QG4 Packaging & Preflight:** `pip install .`, preflight success, README matrix validated.
5. **QG5 Final Demo:** Live + cached run outputs archived; research plots generated; documentation cross-checked.

## 17. Submission Guideline Alignment
- Final checklist to ensure README, architecture doc, API reference, prompt log, results notebook, cost tables, UX evidence, **ISO/IEC 25010 quality assessment (8 characteristics - mandatory for 90+ scores)**, and tests all match `software_submission_guidelines.pdf`.
- All configuration separated (`config/settings.yaml`, `.env.example`), no secrets in code, `.gitignore` updated.
- Unit/integration tests plus edge-case handling deliver ≥85% coverage with documented expected outputs.
- Visualization assets, screenshots, and architecture diagrams stored in `docs/` and referenced from README/PRD.
- **Git history** should contain meaningful commits (feat:, fix:, docs:, test:, refactor:) with no secrets in history and `.gitignore` properly configured; exact commit count is not required.

--- 
*Prepared by Kickoff Agent v2.1 for HW4 Route Enrichment Tour-Guide System.*
