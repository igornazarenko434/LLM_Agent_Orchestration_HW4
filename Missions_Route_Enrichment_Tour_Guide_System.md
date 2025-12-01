# Missions – Route Enrichment Tour-Guide System

**Project:** Route Enrichment Tour-Guide System
**Package Name:** `hw4_tourguide`
**Target Grade:** 95 (Outstanding Excellence)
**Due Date:** December 4, 2024

---

## Mission Structure Overview

This document contains **47 missions** organized into **8 phases** with **6 quality gates**. Each mission includes:
- **Objective**: Clear goal aligned with rubric requirements
- **Rubric Focus**: Which grading category this mission supports
- **Definition of Done (DoD)**: 3-5 specific completion criteria
- **Self-Verify Command**: Exact command to prove completion
- **Expected Evidence**: What the verification should show
- **Time Estimate**: Expected effort (S=Small 1-2h, M=Medium 2-4h, L=Large 4-8h, XL=8-16h)
- **Status**: [✓] Completed, [→] In Progress, [✓] Completed, [⚠] Blocked

---

## Phase 0: Intake & Kickoff

### **M0 – Project Intake & Kickoff Agent Interview**
- **Objective**: Complete Kickoff Agent v2.2 interview to establish project foundation, stakeholders, requirements, and documentation expectations
- **Rubric Focus**: Documentation & Planning (15%), Requirements Analysis (10%)
- **Definition of Done**:
  1. All 13 interview sections (A-M) completed with zero _TBD_ placeholders
  2. `interview_summary.md` captures ≥12 KPIs, ≥9 FRs, ≥9 NFRs, ≥6 User Stories
  3. Stakeholders (6), Personas (2), Timeline (4 milestones), Risks (5) documented
  4. PRD, Missions, Progress Tracker, .claude files generated from interview
- **Self-Verify Command**: `ls interview_summary.md PRD_*.md Missions_*.md PROGRESS_TRACKER.md .claude && grep -c "^## " PRD_*.md`
- **Expected Evidence**: 4 files exist and are complete: PRD (19 sections), Missions (40+ missions), Progress Tracker (7 categories), .claude (10 sections), interview_summary (all decisions captured)
- **Time Estimate**: M (2-4h)
- **Status**: [✓] Completed
- **Dependencies**: None (kickoff mission)
- **Blocks**: M1

---

## Phase 1: Planning & Architecture (Due Nov 26)

### **M1 – PRD Finalization with Evidence Matrix**
- **Objective**: Finalize PRD with complete Evidence Matrix (≥30 entries), Nielsen's 10 Heuristics table, and ADR register (≥7 decisions)
- **Rubric Focus**: Documentation & Planning (15%), Requirements Analysis (10%)
- **Definition of Done**:
  1. Evidence Matrix table with ≥30 entries (KPIs, FRs, NFRs, User Stories mapped to verification commands)
  2. CLI Usability Principles table (8 principles) documented with terminal output examples
  3. ADR register with ≥7 decisions (alternatives, trade-offs, rationale documented)
  4. Installation & Verification Matrix with ≥10 steps (command, expected result, recovery)
  5. All 17 sections complete (Context, Stakeholders, Goals, Requirements, Scope, Architecture, Timeline, Risks, Data, Config, Testing, Research, Documentation, Evidence Matrix, Quality Gates, Submission Alignment)
  6. `.claude` updated (Section 5: Mission M1 completion)
- **Self-Verify Command**: `grep -c "| ADR-" PRD_*.md && grep -c "^| [0-9]" PRD_*.md | head -3`
- **Expected Evidence**: ADR count ≥7, Evidence Matrix rows ≥30, Nielsen's rows = 10
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: M0
- **Blocks**: GATE 1, M2.0, M2.1, M2.2

### **M2.0 – Package Scaffold & Pyproject Configuration**
- **Objective**: Create pip-installable Python package structure with pyproject.toml, src/hw4_tourguide/, and entry point
- **Rubric Focus**: Packaging & Installation (10%), Code Quality (15%)
- **Definition of Done**:
  1. Package structure: `src/hw4_tourguide/__init__.py`, `__main__.py`, `pyproject.toml`, `setup.py` (if needed)
  2. Entry point configured: `python -m hw4_tourguide` callable
  3. Dependencies specified in pyproject.toml (requests, pyyaml, python-dotenv, pytest, pytest-cov)
  4. `pip install .` succeeds in clean venv without errors
  5. Package metadata (name, version, author, description) set
  6. `.claude` updated (Section 5: Mission M2.0 completion)
- **Self-Verify Command**: `python -m venv test_venv && source test_venv/bin/activate && pip install . && python -m hw4_tourguide --help`
- **Expected Evidence**: Help text displayed with CLI options; exit code 0
- **Time Estimate**: S (1-2h)
- **Status**: [✓] Completed
- **Dependencies**: GATE 1
- **Blocks**: M2.1, M4.1, M7.0-M7.12

### **M2.1 – Repository Structure & Directories**
- **Objective**: Create complete directory tree for config, logs, output, data, tests, docs, scripts
- **Rubric Focus**: Code Organization (part of 15%), Documentation (15%)
- **Definition of Done**:
  1. Directories created: `config/`, `logs/`, `output/`, `data/routes/`, `tests/`, `docs/`, `scripts/`
  2. `.gitignore` configured (covers `.env`, `logs/`, `output/`, `__pycache__/`, `.venv/`, `*.pyc`)
  3. `.env.example` created with required keys documented (GOOGLE_MAPS_API_KEY, YOUTUBE_API_KEY, etc.)
  4. `README.md` skeleton with 15+ section headers (Overview, Features, Installation, Usage, Configuration, Testing, Troubleshooting, Architecture, API Reference, Research, UX Heuristics, Contributing, License, Credits, Screenshots)
  5. All directories have `.gitkeep` or initial placeholder files
  6. `.claude` updated (Section 5: Mission M2.1 completion)
- **Self-Verify Command**: `tree -L 2 -a | grep -E "config|logs|output|data|tests|docs|scripts|\.env\.example|\.gitignore"`
- **Expected Evidence**: All 7 directories listed, `.env.example` and `.gitignore` present
- **Time Estimate**: S (1h)
- **Status**: [✓] Completed
- **Dependencies**: M2.0
- **Blocks**: M2.2, M3

### **M2.2 – Architecture Documentation Package**
- **Objective**: Create architecture documentation with C4 diagrams (Context/Container/Component/Deployment) and ADR register
- **Rubric Focus**: Documentation & Planning (15%), Architecture Design (10%)
- **Definition of Done**:
  1. `docs/architecture/c4_diagrams.md` with 4 C4 levels (Context, Container, Component, Deployment)
  2. `docs/architecture/adr_register.md` listing all 7+ ADRs with status, date, context, decision, consequences
  3. ADR-001 through ADR-007 documented: Python 3.11+, Threading vs AsyncIO, Google Maps caching, Search+Fetch separation, YAML config, Structured logging, ThreadPoolExecutor
  4. Component diagram shows: RouteProvider→Scheduler→Orchestrator→Agents(Video/Song/Knowledge)→Judge→Output
  5. Deployment diagram shows single MacBook with config/logs/output file interactions
  6. `.claude` updated (Section 5: Mission M2.2 completion)
- **Self-Verify Command**: `ls docs/architecture/ && grep -c "## ADR-" docs/architecture/adr_register.md`
- **Expected Evidence**: c4_diagrams.md and adr_register.md exist, ADR count ≥7
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: M2.1
- **Blocks**: M5, M6, GATE 2

### **GATE 1 – Architecture Ready**
- **Criteria**: M1 + M2.0 + M2.1 + M2.2 complete; PRD approved; package installable; directory structure valid
- **Verification**: `pip install . && python -m hw4_tourguide --help && ls docs/architecture/`
- **Blocker Recovery**: If fails, revisit incomplete missions before proceeding to Phase 2
- **Status**: [✓] Completed

---

## Phase 2: Foundation (Config, Logging, Security) (Due Nov 29)

### **M3 – Configuration & Security Layer**
- **Objective**: Implement centralized config loader with YAML, CLI overrides, `.env` secrets, and validation
- **Rubric Focus**: Code Quality (15%), Security (5%), Configurability (part of NFRs)
- **Definition of Done**:
  1. `config/settings.yaml` created with ≥20 parameters (scheduler interval, agent configs, API endpoints, log settings, output paths)
  2. `src/hw4_tourguide/config_loader.py` implements ConfigLoader class reading YAML + `.env` + CLI overrides
  3. Secret redaction in logs: API keys masked as `****...last4chars`
  4. Config validation: missing required keys trigger fallback to cached/mock mode with warnings
  5. Unit test `tests/test_config_loader.py` covers YAML parsing, CLI override priority, secret redaction
  6. `.claude` updated (Section 5: Mission M3 completion)
- **Self-Verify Command**: `wc -l config/settings.yaml && pytest tests/test_config_loader.py -v`
- **Expected Evidence**: settings.yaml ≥20 lines, config tests pass, secrets redacted in log output
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: GATE 1, M2.1
- **Blocks**: M3.1

### **M3.1 – YAML Configuration Schema**
- **Objective**: Define and document complete YAML configuration schema with defaults and validation rules
- **Rubric Focus**: Documentation (15%), Configurability (NFR-8)
- **Definition of Done**:
  1. `config/settings.yaml` includes sections: `scheduler`, `orchestrator`, `agents` (video/song/knowledge), `judge`, `logging`, `output`, `route_provider`
  2. Each parameter documented with inline comments (type, default, valid range)
  3. `docs/api_reference.md` Configuration section lists all parameters with descriptions
  4. Example configurations for common scenarios (live mode, cached mode, mock mode, debug mode)
  5. Validation schema (JSON Schema or dataclass with validators) implemented
  6. `.claude` updated (Section 5: Mission M3.1 completion)
- **Self-Verify Command**: `grep -E "^  [a-z_]+:" config/settings.yaml | wc -l`
- **Expected Evidence**: ≥20 unique parameter keys in YAML
- **Time Estimate**: S (1-2h)
- **Status**: [✓] Completed
- **Dependencies**: M3
- **Blocks**: M3.2, M7.1-M7.6

### **M3.2 – Logging Infrastructure**
- **Objective**: Implement structured logging system with rotation, configurable levels, and event tagging
- **Rubric Focus**: Code Quality (15%), Observability (NFR-7), Testing (10%)
- **Definition of Done**:
  1. `src/hw4_tourguide/logger.py` sets up Python `logging` with RotatingFileHandler (10MB per file, 5 backups)
  2. Log format: `TIMESTAMP | LEVEL | MODULE | EVENT_TAG | MESSAGE`
  3. Event tags implemented: `Scheduler`, `Orchestrator`, `Agent`, `Judge`, `Error`, `API_Call`, `Config`
  4. Log level controllable via config and CLI flag `--log-level [DEBUG|INFO|WARNING|ERROR]`
  5. Unit test `tests/test_logging.py` verifies log file creation, rotation, level filtering, tag presence
  6. `.claude` updated (Section 5: Mission M3.2 completion)
- **Self-Verify Command**: `pytest tests/test_logging.py -v && grep -E "Scheduler|Orchestrator|Agent|Judge" logs/test_system.log | wc -l`
- **Expected Evidence**: Logging tests pass, log file contains ≥4 event tag types
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: M3.1
- **Blocks**: M7.2, M7.3, GATE 2

### **GATE 2 – Foundation Secure & Observable**
- **Criteria**: M3 + M3.1 + M3.2 complete; config loads without errors; logs show structured events; secrets redacted
- **Verification**: `python -m hw4_tourguide --config config/settings.yaml --log-level DEBUG --mode cached --help && tail -20 logs/system.log`
- **Blocker Recovery**: If logs missing event tags or secrets exposed, fix before Phase 3

---

## Phase 3: Testing Framework (Due Nov 29)

### **M4.1 – Test Framework & Mocking Setup**
- **Objective**: Configure pytest with coverage, fixtures, and mocks for external APIs (Google Maps, YouTube, Wikipedia)
- **Rubric Focus**: Testing (10%), Code Quality (15%)
- **Definition of Done**:
  1. `pytest.ini` or `pyproject.toml` [tool.pytest] configured with coverage settings
  2. `tests/conftest.py` provides shared fixtures: mock_config, mock_api_responses, sample_route_data
  3. Mock implementations for RouteProvider, YouTube API, Wikipedia API in `tests/mocks/`
  4. Coverage target set to ≥85% with `pytest-cov`
  5. `tests/test_sample.py` demonstrates fixture usage and passes
  6. `.claude` updated (Section 5: Mission M4.1 completion)
- **Self-Verify Command**: `pytest tests/test_sample.py -v --cov=hw4_tourguide --cov-report=term-missing`
- **Expected Evidence**: Tests pass, coverage report shows ≥85% (or baseline established)
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: M2.0, GATE 1
- **Blocks**: M4.2, M7.1-M7.12

### M4.2 – Unit Tests for Core Modules
- **Objective**: Write unit tests for config_loader, logger, and utility modules with ≥85% line coverage
- **Rubric Focus**: Testing (10%), Code Quality (15%)
- **Definition of Done**:
  1. `tests/test_config_loader.py` covers YAML parsing, CLI overrides, secret redaction, validation failures (≥5 test cases)
  2. `tests/test_logging.py` covers log setup, event tagging, level filtering, rotation (≥4 test cases)
  3. `tests/test_utils.py` covers helper functions (if any): retry logic, rate limiting, string formatting
  4. All tests pass with ≥85% coverage for tested modules
  5. CI/CD-ready: tests run in <30 seconds
  6. `.claude` updated (Section 5: Mission M4.2 completion)
- **Self-Verify Command**: `pytest tests/test_config_loader.py tests/test_logging.py tests/test_utils.py -v --cov=hw4_tourguide.config_loader --cov=hw4_tourguide.logger --cov-report=term`
- **Expected Evidence**: All tests pass, coverage ≥85% per module
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: M4.1
- **Blocks**: GATE 3

### **M4.3 – Packaging Configuration (MANIFEST.in)**
- **Objective**: Create `MANIFEST.in` to ensure non-code files (config, prompts) are included in source distribution
- **Rubric Focus**: Packaging & Installation (10%), Code Quality (15%)
- **Definition of Done**:
  1. `MANIFEST.in` created in project root
  2. Includes `config/settings.yaml`, `.env.example`
  3. Includes `.claude/agents/*.md` (agent prompts)
  4. `pip install .` (or build) results in a package containing these files
  5. `.claude` updated (Section 5: Mission M4.3 completion)
- **Self-Verify Command**: `check-manifest --create && pip install . && ls $(python -c "import site; print(site.getsitepackages()[0])")/hw4_tourguide_config_check_placeholder` (conceptual check)
- **Expected Evidence**: MANIFEST.in exists, package installs with config files
- **Time Estimate**: S (1h)
- **Status**: [x] Done
- **Dependencies**: M2.0
- **Blocks**: GATE 3

### **GATE 3 – Testing Foundation Verified**
- **Criteria**: M4.1 + M4.2 complete; pytest runs successfully; coverage baseline ≥85% for core modules
- **Verification**: `pytest --cov=hw4_tourguide --cov-report=html && open htmlcov/index.html`
- **Blocker Recovery**: If coverage <85%, identify untested branches and add cases before Phase 4

---

## Phase 4: Research & Documentation Setup (Due Nov 29-30)

### **M5 – Research Plan & Cost Analysis Framework**
- **Objective**: Define research studies, create cost tracking infrastructure, and set up results notebook
- **Rubric Focus**: Research & Analysis (10%), Documentation (15%)
- **Definition of Done**:
  1. `docs/research_plan.md` documents 4 studies: orchestration efficiency, cost analysis, judge LLM impact, results visualization
  2. `docs/cost_analysis.md` template created with sections: API call tracking, token usage, live vs cached comparison, optimization strategies
  3. `logs/metrics.json` structure defined for API call counts (Maps, YouTube, Wikipedia, LLM) per run
  4. `docs/analysis/results.ipynb` created with sections for each study, LaTeX formula placeholders, plot stubs (bar/line/scatter/heatmap)
  5. Cost tracking integrated into agents: log every API call with timestamp, endpoint, cost estimate
  6. `.claude` updated (Section 5: Mission M5 completion)
- **Self-Verify Command**: `ls docs/research_plan.md docs/cost_analysis.md docs/analysis/results.ipynb logs/metrics.json`
- **Expected Evidence**: 4 files exist, results.ipynb has ≥4 plot cell stubs
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: M2.2, GATE 2
- **Blocks**: M8.1
 - **Notes:** Templates only; actual studies and populated tables/plots occur in M8.1 (research execution) and M8.2 (cost documentation) once the pipeline is running.

### **M6 – UX Heuristics & API Reference Documentation**
- **Objective**: Document Nielsen's 10 Heuristics applied to CLI/outputs and create comprehensive API reference
- **Rubric Focus**: Documentation (15%), Usability (NFR-3)
- **Definition of Done**:
  1. `docs/ux/heuristics.md` maps each of Nielsen's 10 heuristics to CLI features with evidence (screenshots/log excerpts)
  2. Heuristic #1 (Visibility): Show scheduler/orchestrator logs streaming in real-time
  3. Heuristic #9 (Error recovery): Document retry logic, fallback modes, troubleshooting guide
  4. `docs/api_reference.md` documents CLI commands, JSON contracts (scheduler task, agent result, judge decision, final route), exit codes
 5. `.claude` updated (Section 5: Mission M6 completion)
 6. **Recommended sequencing:** Perform after core pipeline (post-GATE 4) so heuristics/screenshots use real artifacts
- **Self-Verify Command**: `grep -c "### Heuristic" docs/ux/heuristics.md && ls -d docs/contracts/`
- **Expected Evidence**: 10 heuristic sections, contracts directory exists
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: GATE 4 (pipeline complete), M2.2
- **Blocks**: M8.3 (README polish can reference heuristics)

### **M6.1 – JSON Schema Definition (Data Contracts)**
- **Objective**: Create JSON schemas for all data contracts to ensure consistent structure across scheduler, agents, judge, and output modules
- **Rubric Focus**: Code Quality (15%), Documentation (15%), Submission Guidelines (Section 3.4)
- **Definition of Done**:
  1. Directory created: `docs/contracts/` to host schemas
  1. `docs/contracts/task_schema.json` defines scheduler task structure: `{transaction_id, step_number, location_name, coordinates {lat, lng}, instructions, timestamp}`
  2. `docs/contracts/agent_result_schema.json` defines agent output structure: `{agent_type, status, metadata {title, url, description, score}, reasoning, timestamp, error?}`
  3. `docs/contracts/judge_decision_schema.json` defines judge output structure: `{transaction_id, overall_score, individual_scores {video, song, knowledge}, rationale, timestamp}`
  4. `docs/contracts/route_schema.json` defines final route output: `[{step_number, location, agents {video, song, knowledge}, judge, timestamp}]`
  5. All schemas are valid JSON and include: `$schema`, `type`, `properties`, `required` fields per JSON Schema Draft-07
  6. `.claude` updated (Section 5: Mission M6.1 completion)
- **Self-Verify Command**: `ls docs/contracts/*.json | wc -l && jq empty docs/contracts/*.json && echo "Valid JSON"`
- **Expected Evidence**: 4 JSON files exist, all parse as valid JSON (jq succeeds)
- **Time Estimate**: S (1h)
- **Status**: [✓] Completed
- **Dependencies**: M2.2 (architecture context), M3.1 (config structure)
- **Blocks**: M7.8 (Output Writer needs schemas), M7.10 (Integration tests need schemas)

---

## Phase 5: Implementation (Core Features) (Due Nov 30 - Dec 2)

### **M7.0 – Walking Skeleton (Stub Pipeline)**
- **Objective**: Build minimal end-to-end pipeline using stub providers/agents to validate threading, queues, CLI, and outputs early
- **Rubric Focus**: Functional Requirements (20%), Concurrency (NFR-2), Code Quality (15%)
- **Definition of Done**:
  1. Stub route provider returns fixed 3-step route (no external APIs) wired through scheduler → queue → orchestrator
  2. Stub agents (video/song/knowledge) return canned results concurrently; judge returns deterministic score without LLM
  3. CLI command `python -m hw4_tourguide --mode cached --output output/skeleton_route.json` runs end-to-end with logs and output files
  4. Logs show overlapping agent execution (timestamps) and queue consumption; system exits cleanly
  5. `.claude` updated (Section 5: Mission M7.0 completion)
- **Self-Verify Command**: `python -m hw4_tourguide --mode cached --output output/skeleton_route.json && grep -E "Scheduler|Orchestrator|Agent|Judge" logs/system.log | head -20`
- **Expected Evidence**: Cached skeleton run succeeds, output file written, logs show concurrent agents
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: M2.0, M3.1, M3.2, M4.1
- **Blocks**: M7.1, M7.2 (foundation confidence), M7.3

### **M7.1 – Route Provider Implementation**
- **Objective**: Implement RouteProvider abstraction with live Google Maps API and cached file provider
- **Rubric Focus**: Functional Requirements (20%), Code Quality (15%)
- **Definition of Done**:
  1. `src/hw4_tourguide/route_provider.py` defines `RouteProvider` abstract base class with `get_route(from, to)` method
  2. `GoogleMapsProvider` implements live API calls with retry/backoff logic (3 attempts, exponential backoff)
  3. `CachedRouteProvider` reads from `data/routes/*.json` files with transaction ID matching
  4. Route result includes: task list (one dict per step with transaction_id, step_number, location_name, coordinates, instructions, timestamp, optional search_hint/address/route_context), plus metadata (distance, duration, timestamp, route_context)
  5. Unit tests `tests/test_route_provider.py` cover live API (mocked), cached file loading, error handling (invalid API key, missing file)
  6. `.claude` updated (Section 5: Mission M7.1 completion)
  7. **NEW (ADR-009):** Route Provider writes checkpoint file `output/checkpoints/{TID}/00_route.json` with raw Google Maps API response (includes route steps, metadata, timestamp)
  8. **NEW (ADR-010):** Google Maps API calls wrapped in circuit breaker (from M7.7e); circuit opens after 5 consecutive failures, preventing quota waste
  9. **NEW (ADR-011):** Metrics tracked: `MetricsCollector.increment_counter('api_calls.google_maps')`, `MetricsCollector.record_latency('route_provider.fetch_ms', duration)`
- **Self-Verify Command**: `pytest tests/test_route_provider.py -v && python -m hw4_tourguide --from "Boston" --to "MIT" --mode cached && ls output/checkpoints/*/00_route.json`
- **Expected Evidence**: Tests pass, cached mode CLI run succeeds, checkpoint file created
- **Time Estimate**: L (4-6h)
- **Status**: [✓] Completed
- **Dependencies**: M2.0, M3.1, M4.1, M6.1, M7.0
- **Blocks**: M7.2, M7.9, M7.10, M7.12

### **M7.1a – Publish Sample Cached Routes (Offline Ready)
  **Note:** Added demo cached route (Boston, MA → MIT) with full fields (search_hint, route_context, instructions, coords) at data/routes/demo_boston_mit.json**
- **Objective**: Provide two real cached routes (from live Google Maps captures) so graders can run cached mode without an API key.
- **Rubric Focus**: Functional Requirements (offline usability), Documentation & Testing
- **Definition of Done**:
  1. Two JSON files under `data/routes/` (e.g., `sample_israel.json`, `sample_us.json`) with ≥3 steps, including `location_name`, `instructions` (HTML-stripped), `coordinates`, `search_hint`, `route_context`, metadata.
  2. README/Missions note updated with example `--from/--to` pairs for these cached samples.
  3. Verification command documented that runs cached mode against a sample file (no API key) and produces output/checkpoints.
- **Self-Verify Command**: `python -m hw4_tourguide --from "<origin>" --to "<destination>" --mode cached --output output/demo_cached_sample.json`
- **Expected Evidence**: Cached run completes using the sample file; output/checkpoint written; no live API needed.
- **Time Estimate**: S (1-2h)
- **Status**: [✓] Completed
- **Dependencies**: M7.1
- **Blocks**: None

### **M7.2 – Scheduler Implementation**
- **Objective**: Implement dedicated scheduler thread that emits route steps into queue at configured intervals
- **Rubric Focus**: Functional Requirements (20%), Concurrency (part of NFR-2)
- **Definition of Done**:
  1. `src/hw4_tourguide/scheduler.py` implements `Scheduler` class with dedicated thread using `threading.Thread`
  2. Scheduler reads interval from config (default 2.0s), pushes tasks to `queue.Queue` with timestamped logs
  3. Each task object contains: transaction_id, step_number, location_name, coordinates, timestamp (from provider), emit_timestamp (from scheduler)
  4. Scheduler logs: `Scheduler | EMIT | Step X/Y: LocationName (TID: abc123)`
  5. Unit test `tests/test_scheduler.py` verifies interval accuracy ±0.2s, queue population, graceful shutdown
  6. `.claude` updated (Section 5: Mission M7.2 completion)
  7. **NEW (ADR-009):** Scheduler writes checkpoint file `output/checkpoints/{TID}/01_scheduler_queue.json` with all emitted tasks (array of task objects with transaction_id, step_number, location_name, coordinates, timestamp)
  8. **NEW (ADR-011):** Metrics tracked: `MetricsCollector.increment_counter('scheduler.tasks_emitted')`, `MetricsCollector.set_gauge('queue.depth', queue.qsize())` on each emit
- **Self-Verify Command**: `pytest tests/test_scheduler.py -v && python scripts/check_scheduler_interval.py logs/system.log && ls output/checkpoints/*/01_scheduler_queue.json`
- **Expected Evidence**: Tests pass, interval check script reports accuracy within ±0.2s, checkpoint file created
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: M7.1, M3.2, M4.1, M6.1, M7.7a (checkpoint writer), M7.7f (metrics)
- **Blocks**: M7.3, M7.9, M7.10, M7.11

### **M7.3 – Orchestrator & Worker Threads**
- **Objective**: Implement orchestrator that consumes queue, spawns worker threads/futures, and coordinates agents+judge with robust error handling
- **Rubric Focus**: Functional Requirements (20%), Concurrency (NFR-2), Code Quality (15%), Reliability (NFR-1)
- **Definition of Done**:
  1. `src/hw4_tourguide/orchestrator.py` implements `Orchestrator` class using `ThreadPoolExecutor` (configurable worker count)
  2. Orchestrator consumes tasks from queue in main loop, submits worker jobs as futures
  3. Each worker job: calls all 3 agents (Video/Song/Knowledge) concurrently, collects results, calls judge, aggregates output
  4. Orchestrator logs: `Orchestrator | DISPATCH | TID: abc123, Workers: 3/10 active`
  5. **Worker Exception Handling**: Orchestrator wraps `future.result()` in try/except block; if worker raises exception, logs error with TID and continues processing queue (no cascade failure): `Orchestrator | ERROR | TID: abc123 | Worker failed: <exception> | Continuing...`
  6. **Graceful Degradation**: If agent returns None/error after retries, worker marks agent result as `{"status": "unavailable", "reason": "timeout"}` in output and continues (partial results OK); judge scores available agents only
  7. **Metrics:** Record queue depth and active worker gauges via `MetricsCollector.set_gauge(...)` each dispatch/loop
  8. Unit test `tests/test_orchestrator.py` verifies queue consumption, worker spawning, concurrent agent calls (timestamped logs show overlap), and `test_orchestrator_worker_exception()` verifies exception handling
  9. `.claude` updated (Section 5: Mission M7.3 completion)
- **Self-Verify Command**: `pytest tests/test_orchestrator.py -v && grep "Orchestrator | DISPATCH" logs/system.log | wc -l && grep "Orchestrator | ERROR" logs/system.log`
- **Expected Evidence**: Tests pass (including exception handling test), logs show ≥5 worker dispatches, error logs present for failure scenarios
- **Time Estimate**: L+ (7-10h)
- **Status**: [✓] Completed
- **Dependencies**: M7.2, M7.4, M7.5, M7.6, M7.7, M3.2, M4.1, M6.1, M7.7f (metrics)
- **Blocks**: M7.9, M7.10, M7.11

### **M7.4 – Video Agent Implementation**
- **Objective**: Implement Video Agent with search→fetch pipeline for YouTube metadata
- **Rubric Focus**: Functional Requirements (20%), Search+Fetch Separation (ADR-004)
- **Definition of Done**:
  1. `src/hw4_tourguide/agents/video_agent.py` implements `VideoAgent` class with `search()` and `fetch()` methods plus a `run()` wrapper that builds queries from task fields (`location_name`, `address`, `search_hint`, `route_context`) and returns objects that satisfy `docs/contracts/agent_result_schema.json`.
  2. Search phase: query YouTube API (or mock/offline fixture when no API key or `mock_mode=true`) with location keywords, return list of video IDs (limit 3, pulled from config `agents.video.search_limit`).
  3. Fetch phase: retrieve metadata for selected video (title, channel, duration, thumbnail URL, view count) using the search result; retries/backoff and circuit breaker applied to all outbound calls.
  4. Agent logs decision rationale: `VideoAgent | SEARCH | Query: "MIT campus tour" | Results: 3 videos` and `VideoAgent | FETCH | Selected: video_id_123 | Reason: highest views + recent`
  5. Agent writes checkpoints with search candidates and final fetch payload (see ADR-009) and redacts API keys in logs.
  6. Unit test `tests/test_video_agent.py` covers search (mocked API/offline fixture), fetch, cost tracking (query count logged to metrics.json), checkpoint writing, and circuit breaker invocation.
  7. `.claude` updated (Section 5: Mission M7.4 completion)
  8. **NEW (ADR-009):** Video Agent writes checkpoint files: `output/checkpoints/{TID}/02_agent_search_video.json` after search phase (list of candidate video IDs with metadata), `output/checkpoints/{TID}/03_agent_fetch_video.json` after fetch phase (selected video full metadata)
  9. **NEW (ADR-010):** YouTube API calls wrapped in circuit breaker; circuit opens after 5 consecutive failures
  10. **NEW (ADR-011):** Metrics tracked: `MetricsCollector.increment_counter('api_calls.youtube')`, `MetricsCollector.record_latency('agent.video.search_ms', duration)`, `MetricsCollector.record_latency('agent.video.fetch_ms', duration)`
- **Self-Verify Command**: `pytest tests/test_video_agent.py -v && jq '.api_calls.youtube' logs/metrics.json && ls output/checkpoints/*/02_agent_search_video.json output/checkpoints/*/03_agent_fetch_video.json`
- **Expected Evidence**: Tests pass, metrics.json shows YouTube call count ≤3 per location, checkpoint files created
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: M3.1, M4.1, M6.1, M7.7a (checkpoint), M7.7c (search+fetch), M7.7e (circuit breaker), M7.7f (metrics)
- **Blocks**: M7.3, M7.10, M7.11, M7.12

### **M7.5 – Song Agent Implementation**
- **Objective**: Implement Song Agent with search→fetch pipeline for audio/music metadata
- **Rubric Focus**: Functional Requirements (20%), Search+Fetch Separation (ADR-004)
- **Definition of Done**:
  1. `src/hw4_tourguide/agents/song_agent.py` implements `SongAgent` class with `search()` and `fetch()` methods plus a `run()` wrapper that builds queries from task fields (`location_name`, `address`, `search_hint`, `route_context`) and returns objects that satisfy `docs/contracts/agent_result_schema.json`.
  2. Search phase: query primary music API (or mock/offline fixture when no credentials or `mock_mode=true`) with location-related keywords; optional secondary YouTube search behind config flag for free coverage; return list of track IDs (limit 3 via config `agents.song.search_limit`).
  3. Fetch phase: retrieve metadata for selected track (title, artist, album, duration, preview URL) with retries/backoff and circuit breaker protection.
  4. Agent logs decision rationale similar to Video Agent and redacts secrets; uses search_hint/address to favor location-relevant content.
  5. Unit test `tests/test_song_agent.py` covers search, fetch, cost tracking, checkpoint writing, and circuit breaker integration (mocked).
  6. `.claude` updated (Section 5: Mission M7.5 completion)
  7. **NEW (ADR-009):** Song Agent writes checkpoint files:
     - `output/checkpoints/{TID}/02_agent_search_song.json` after search phase (list of candidate track IDs with metadata)
     - `output/checkpoints/{TID}/03_agent_fetch_song.json` after fetch phase (selected track full metadata)
  8. **NEW (ADR-010):** Spotify/Music API calls wrapped in circuit breaker; circuit opens after 5 consecutive failures
  9. **NEW (ADR-011):** Metrics tracked: `MetricsCollector.increment_counter('api_calls.spotify')`, `MetricsCollector.record_latency('agent.song.search_ms', duration)`, `MetricsCollector.record_latency('agent.song.fetch_ms', duration)`
  10. **UPDATED:** Unit test covers checkpoint file writing and circuit breaker integration
- **Self-Verify Command**: `pytest tests/test_song_agent.py -v && jq '.api_calls.spotify' logs/metrics.json && ls output/checkpoints/*/02_agent_search_song.json output/checkpoints/*/03_agent_fetch_song.json`
- **Status**: [✓] Completed
- **Dependencies**: M3.1, M4.1, M6.1, M7.7a (checkpoint), M7.7c (search+fetch), M7.7e (circuit breaker), M7.7f (metrics)
- **Blocks**: M7.3, M7.10, M7.11, M7.12

### **M7.6 – Knowledge Agent Implementation**
- **Objective**: Implement Knowledge Agent with search→fetch pipeline for web articles/facts
- **Rubric Focus**: Functional Requirements (20%), Search+Fetch Separation (ADR-004)
- **Definition of Done**:
  1. `src/hw4_tourguide/agents/knowledge_agent.py` implements `KnowledgeAgent` class with `search()` and `fetch()` methods plus a `run()` wrapper that builds queries from task fields (`location_name`, `address`, `search_hint`, `route_context`) and returns objects that satisfy `docs/contracts/agent_result_schema.json`.
  2. Search phase: query Wikipedia plus optional DuckDuckGo secondary source (behind config flag) or mock/offline fixture when `mock_mode=true` or network unavailable with location name and route context, return list of article URLs (limit 3 via config `agents.knowledge.search_limit`).
  3. Fetch phase: retrieve article snippet/summary, extract citations (URL, title, excerpt) with retries/backoff and circuit breaker protection.
  4. Agent logs decision rationale: `KnowledgeAgent | SEARCH | Query: "MIT history" | Results: 3 articles` and `KnowledgeAgent | FETCH | Selected: wiki_article | Reason: authoritative source`
  5. Unit test `tests/test_knowledge_agent.py` covers search, fetch, cost tracking, checkpoint writing, and circuit breaker integration (mocked/offline).
  6. `.claude` updated (Section 5: Mission M7.6 completion)
  7. **NEW (ADR-009):** Knowledge Agent writes checkpoint files:
     - `output/checkpoints/{TID}/02_agent_search_knowledge.json` after search phase (list of article URLs with metadata)
     - `output/checkpoints/{TID}/03_agent_fetch_knowledge.json` after fetch phase (selected article snippet/summary with citations)
  8. **NEW (ADR-010):** Wikipedia/DuckDuckGo API calls wrapped in circuit breaker; circuit opens after 5 consecutive failures
  9. **NEW (ADR-011):** Metrics tracked: `MetricsCollector.increment_counter('api_calls.wikipedia')`, `MetricsCollector.record_latency('agent.knowledge.search_ms', duration)`, `MetricsCollector.record_latency('agent.knowledge.fetch_ms', duration)`
  10. **UPDATED:** Unit test covers checkpoint file writing and circuit breaker integration
- **Immediate Validation Step (before proceeding):** `PYTHONPATH=src .venv/bin/python -m pytest tests/test_video_agent.py tests/test_song_agent.py tests/test_knowledge_agent.py --override-ini addopts=`
- **Hands-on Check (before Judge):** Run a cached route through scheduler+orchestrator to inspect agent outputs: `python -m hw4_tourguide --mode cached --from "Reichman University" --to "Herzliya HaKeren" --output output/agent_only.json` then open `output/agent_only.json` and `output/checkpoints/*/02_agent_search_*.json` to review what each agent found.
- **Self-Verify Command**: `pytest tests/test_knowledge_agent.py -v && jq '.api_calls.wikipedia' logs/metrics.json && ls output/checkpoints/*/02_agent_search_knowledge.json output/checkpoints/*/03_agent_fetch_knowledge.json`
- **Expected Evidence**: Tests pass, metrics.json shows Wikipedia call count ≤3 per location, checkpoint files created
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: M3.1, M4.1, M6.1, M7.7a (checkpoint), M7.7c (search+fetch), M7.7e (circuit breaker), M7.7f (metrics)
- **Blocks**: M7.3, M7.10, M7.11, M7.12

### **M7.7 – Judge Agent Implementation**
- **Objective**: Implement Judge Agent that scores agent outputs using heuristics and optional LLM
- **Rubric Focus**: Functional Requirements (20%), Code Quality (15%)
- **Definition of Done**:
  1. `src/hw4_tourguide/judge.py` implements `JudgeAgent` class with `evaluate()` method that consumes normalized agent results (per `agent_result_schema.json`) and preserves task metadata (`transaction_id`, `step_number`, `emit_timestamp`) for tracing.
  2. Heuristic scoring: relevance (does content match location/search_hint/address?), quality (metadata completeness), diversity (different types of media); honors missing agents by marking them unavailable rather than failing.
  3. Optional LLM scoring: if enabled in config, call ChatGPT/Claude CLI to rate agent outputs (0-100 scale) with rationale; disabled by default to avoid cost, with mock path for tests/offline runs.
  4. Judge logs: `Judge | SCORE | TID: abc123 | Overall: 85, Video: 90, Song: 80, Knowledge: 85` and returns result object: overall_score (0-100), individual_scores {video, song, knowledge}, rationale (text explanation), timestamp
  5. Test file `tests/test_judge.py` covers heuristic scoring (no LLM), LLM scoring (mocked), edge cases (missing agent data), LLM fallback behavior, and checkpoint writing.
  6. If LLM scoring fails (timeout/API error), fall back to heuristic-only scoring and log warning: `Judge | FALLBACK | TID: abc123 | LLM unavailable, using heuristics only`
  7. `.claude` updated (Section 5: Mission M7.7 completion)
  8. **NEW (ADR-009):** Judge writes checkpoint file `output/checkpoints/{TID}/04_judge_decision.json` with scoring results (overall_score, individual_scores, rationale, timestamp)
  9. **NEW (ADR-011):** Metrics tracked: `MetricsCollector.record_latency('judge.scoring_ms', duration)`, `MetricsCollector.increment_counter('judge.llm_calls')` (if LLM used)
- **Self-Verify Command**: `pytest tests/test_judge.py -v && jq '.[0].judge.overall_score' output/final_route.json && ls output/checkpoints/*/04_judge_decision.json`
- **Expected Evidence**: Tests pass, JSON output shows judge scores for all locations, checkpoint files created with scoring results
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: M4.1, M6.1, M7.7a (checkpoint), M7.7f (metrics)
- **Blocks**: M7.3, M7.7b, M7.8, M7.10

### **M7.7a – File-Based Interfaces + Checkpoint Writer (ADR-009)**
- **Objective**: Implement file-based interface module for JSON contracts, data exchange, and checkpoint management
- **Rubric Focus**: Structure (15pts), Code Quality (15%), Architecture (ADR-009)
- **Definition of Done**:
  1. `src/hw4_tourguide/file_interface.py` implements FileInterface module with JSON read/write utilities
  2. JSON file operations for data/routes/*.json (cached routes) and output/*.json (final results)
  3. Schema validation against JSON contracts from M6.1 (task_schema, agent_result_schema, judge_decision_schema, route_schema)
  4. **NEW:** `CheckpointWriter` class for writing/reading checkpoint files to `output/checkpoints/{TID}/`
  5. **NEW:** Checkpoint numbering: `00_route.json`, `01_scheduler_queue.json`, `02_agent_search_{agent}.json`, `03_agent_fetch_{agent}.json`, `04_judge_decision.json`, `05_final_output.json`
  6. **NEW:** Methods: `write_checkpoint(tid, stage, data)`, `read_checkpoint(tid, stage)`, `list_checkpoints(tid)`, `cleanup_old_checkpoints(retention_days)`
  7. **NEW:** Checkpoint retention: Auto-delete checkpoints older than `config.output.checkpoint_retention_days` (default 7 days)
  8. Error handling for missing files, invalid JSON, schema violations
  9. Test file `tests/test_file_interface.py` covers JSON validation, checkpoint writing/reading, edge cases (malformed JSON, missing required fields), file not found scenarios, checkpoint retention cleanup
  10. `.claude` updated (Section 5: Mission M7.7a completion)
- **Self-Verify Command**: `pytest tests/test_file_interface.py -v && ls data/routes/*.json output/*.json output/checkpoints/*/`
- **Expected Evidence**: Tests pass, JSON files valid against schemas, checkpoint files created with correct numbering
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: M6.1, M3.1
- **Blocks**: M7.1, M7.2, M7.4, M7.5, M7.6, M7.7, M7.8

### **M7.7b – LLM Abstraction Layer**
- **Objective**: Implement LLM client abstraction to support multiple LLM backends (Ollama, OpenAI, Claude, Mock)
- **Rubric Focus**: Structure (15pts), Code Quality (15%)
- **Definition of Done**:
  1. `src/hw4_tourguide/tools/llm_client.py` implements abstract `LLMClient` base class with `query()` method
  2. Concrete implementations: `OllamaClient`, `OpenAIClient`, `ClaudeClient`, `MockLLMClient`
  3. Factory pattern with config-driven selection (`config.llm.provider: [ollama|openai|claude|mock]`)
  4. Timeout handling (configurable, default 30s), retry logic (3 attempts with exponential backoff: 1s, 2s, 4s)
  5. Error propagation and logging (log LLM provider, prompt length, response length, latency)
  6. Test file `tests/test_llm.py` covers timeout scenarios, retry logic, fallback to mock on failure, all provider implementations
  7. `.claude` updated (Section 5: Mission M7.7b completion)
- **Status**: [✓] Completed
- **Self-Verify Command**: `pytest tests/test_llm.py -v && grep "LLMClient" src/hw4_tourguide/tools/llm_client.py`
- **Expected Evidence**: Tests pass, abstraction layer supports config-driven provider selection
- **Time Estimate**: M (3-4h)
- **Dependencies**: M3.1, M4.1
- **Blocks**: M7.7

### **M7.7c – Search+Fetch Tools**
- **Objective**: Implement search and fetch tool modules with separation of concerns (ADR-004)
- **Rubric Focus**: Structure (15pts), Code Quality (15%)
- **Definition of Done**:
  1. `src/hw4_tourguide/tools/search.py` implements SearchTool module with query methods for YouTube, Spotify, Wikipedia APIs
  2. `src/hw4_tourguide/tools/fetch.py` implements FetchTool module with metadata retrieval for selected content IDs
  3. Search returns list of candidate IDs (limit 3), Fetch retrieves full metadata for one ID
  4. Cost tracking: log every search/fetch call with API endpoint, query, result count, timestamp
  5. Timeout handling (10s per call) and error logging
  6. Test file `tests/test_search_fetch.py` covers timeout scenarios, API mocking, search result limiting, fetch metadata structure
  7. `.claude` updated (Section 5: Mission M7.7c completion)
- **Status**: [✓] Completed
- **Self-Verify Command**: `pytest tests/test_search_fetch.py -v && ls src/hw4_tourguide/tools/search.py src/hw4_tourguide/tools/fetch.py`
- **Expected Evidence**: Tests pass, search and fetch tools are separate modules
- **Time Estimate**: M (2-3h)
- **Dependencies**: M3.2, M4.1
- **Blocks**: M7.4, M7.5, M7.6

### **M7.7d – Concurrency Implementation**
- **Objective**: Implement scheduler thread and orchestrator with ThreadPoolExecutor (ADR-002, ADR-007)
- **Rubric Focus**: Structure (15pts), Code Quality (15%), Concurrency (NFR-2)
- **Definition of Done**:
  1. `src/hw4_tourguide/scheduler.py` uses `threading.Thread` for scheduler with dedicated thread emitting tasks at configured interval
  2. `src/hw4_tourguide/orchestrator.py` uses `concurrent.futures.ThreadPoolExecutor` with configurable `max_workers` (default 5)
  3. Communication via `queue.Queue` (thread-safe) for task passing from scheduler to orchestrator
  4. Supports stub tasks/route data (from M7.0) so threading can be validated before live providers land
  5. Exception handling on `future.result()` - orchestrator catches worker exceptions, logs error with TID, continues processing (no cascade failure)
  6. Logging with Thread IDs and Transaction IDs (TID) for traceability
  7. Test file `tests/test_concurrency.py` covers overlapping agent execution, queue thread-safety, worker exception handling, graceful shutdown
  8. `.claude` updated (Section 5: Mission M7.7d completion)
- **Status**: [✓] Completed
- **Self-Verify Command**: `pytest tests/test_concurrency.py -v && grep "ThreadPoolExecutor" src/hw4_tourguide/orchestrator.py`
- **Expected Evidence**: Tests pass, concurrency primitives correctly implemented
- **Time Estimate**: L (3-4h)
- **Dependencies**: M3.2, M4.1, M3.1, M7.0 (can run with stub tasks before M7.1/M7.2)
- **Blocks**: M7.3, M7.11

### **M7.7e – Circuit Breaker for External APIs (ADR-010)**
- **Objective**: Implement circuit breaker pattern to prevent cascading failures when external APIs fail persistently
- **Rubric Focus**: Code Quality (15%), Reliability (NFR-1), Architecture (ADR-010)
- **Definition of Done**:
  1. `src/hw4_tourguide/tools/circuit_breaker.py` implements `CircuitBreaker` class with 3-state machine (CLOSED, OPEN, HALF_OPEN)
  2. State transitions: CLOSED →(failures ≥ threshold)→ OPEN →(timeout elapsed)→ HALF_OPEN →(success)→ CLOSED or (failure)→ OPEN
  3. Configurable failure threshold (default 5 from `config.circuit_breaker.failure_threshold`) and timeout (default 60s from `config.circuit_breaker.timeout`)
  4. Thread-safe implementation using `threading.Lock` for state access
  5. Logging: `CircuitBreaker | OPEN | API: youtube | Reason: 5 consecutive failures`, `CircuitBreaker | HALF_OPEN | API: youtube | Attempting recovery`, `CircuitBreaker | CLOSED | API: youtube | Recovery successful`
  6. `call(func, *args, **kwargs)` method wraps API calls; raises `CircuitBreakerOpenError` when circuit is OPEN
  7. Test file `tests/test_circuit_breaker.py` covers state transitions (CLOSED→OPEN after threshold failures, OPEN→HALF_OPEN after timeout, HALF_OPEN→CLOSED on success, HALF_OPEN→OPEN on failure), thread safety, configuration loading
  8. `.claude` updated (Section 5: Mission M7.7e completion)
- **Self-Verify Command**: `pytest tests/test_circuit_breaker.py -v && grep "class CircuitBreaker" src/hw4_tourguide/tools/circuit_breaker.py`
- **Expected Evidence**: Tests pass, circuit breaker state machine correctly implemented, logs show state transitions
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: M3.1 (config), M3.2 (logging), M4.1 (testing framework)
- **Blocks**: M7.1, M7.4, M7.5, M7.6 (agents should wrap API calls in circuit breaker)

### **M7.7f – Metrics Aggregator (ADR-011)**
- **Objective**: Implement centralized metrics collection separate from logging for performance monitoring and cost tracking
- **Rubric Focus**: Code Quality (15%), Observability (NFR-7), Architecture (ADR-011)
- **Definition of Done**:
  1. `src/hw4_tourguide/tools/metrics_collector.py` implements `MetricsCollector` class (singleton pattern)
  2. Thread-safe metrics storage using `threading.Lock`
  3. Methods: `increment_counter(name, value=1)`, `record_latency(name, duration_ms)`, `set_gauge(name, value)`, `get_all_metrics() -> dict`
  4. Metrics structure: `{"counters": {"api_calls.google_maps": 3, "api_calls.youtube": 9}, "gauges": {"queue.depth": 2, "threads.active": 5}, "latencies": {"agent.video.search_ms": [120, 135, 98]}}`
  5. Auto-flush to `logs/metrics.json` every `config.metrics.update_interval` seconds (default 5s) using background thread
  6. Graceful shutdown: `flush()` method writes final metrics on program exit
  7. Test file `tests/test_metrics_collector.py` covers counter increment, latency recording, gauge setting, thread safety (concurrent updates), auto-flush behavior, JSON serialization
  8. `.claude` updated (Section 5: Mission M7.7f completion)
- **Self-Verify Command**: `pytest tests/test_metrics_collector.py -v && grep "class MetricsCollector" src/hw4_tourguide/tools/metrics_collector.py`
- **Expected Evidence**: Tests pass, metrics correctly aggregated, logs/metrics.json written with expected structure
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: M3.1 (config), M3.2 (logging), M4.1 (testing framework)
- **Blocks**: M7.1, M7.2, M7.3, M7.4, M7.5, M7.6 (all components should update metrics)

### **M7.8 – Output Writer & Report Generation**
- **Objective**: Implement output module that writes JSON contract + Markdown/CSV summaries for persona exports
- **Rubric Focus**: Functional Requirements (20%), User Stories (US-002)
- **Definition of Done**:
  1. `src/hw4_tourguide/output_writer.py` implements `OutputWriter` class with `write_json()` and `write_report()` methods
  2. JSON output follows schema: array of route steps, each with location, agents {video, song, knowledge}, judge {score, rationale}
  3. Markdown report: human-friendly summary with section per location, embedded links to media, judge verdict
  4. CSV export: tabular format for tour guides (columns: location, video_title, song_title, article_title, judge_score)
  5. Test file `tests/test_output_writer.py` validates JSON schema compliance, Markdown generation, CSV export
  6. `.claude` updated (Section 5: Mission M7.8 completion)
  7. **NEW (ADR-009):** Output Writer writes checkpoint file `output/checkpoints/{TID}/05_final_output.json` with complete aggregated route (all steps, agents, judge results)
  8. **NEW (ADR-009):** Checkpoint serves as audit trail; can be used to regenerate Markdown/CSV reports without re-running agents
- **Self-Verify Command**: `pytest tests/test_output_writer.py -v && ls output/final_route.json output/summary.md output/tour_export.csv output/checkpoints/*/05_final_output.json`
- **Expected Evidence**: Tests pass, all 3 output files generated, checkpoint file created with complete route data
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: M6.1, M7.7, M7.7a (checkpoint), M4.1
- **Blocks**: M7.9, M7.10

### **M7.9 – CLI Interface & Argument Parsing**
- **Status**: [✓] Completed
- **Objective**: Implement `__main__.py` CLI with argparse for from/to, mode, config, log-level, output flags
- **Rubric Focus**: Functional Requirements (20%), Usability (NFR-3)
- **Definition of Done**:
  1. `src/hw4_tourguide/__main__.py` uses `argparse` with options: `--from`, `--to`, `--mode [live|cached]`, `--config`, `--log-level`, `--output`
  2. Help text (`--help`) displays all options with descriptions and examples
  3. CLI orchestrates full pipeline: load config → get route → start scheduler → start orchestrator → wait for completion → write output → exit
  4. Exit codes: 0 (success), 1 (config error), 2 (API error), 3 (no results)
  5. Test file `tests/test_cli.py` (or integration test) runs full pipeline with cached route
  6. `.claude` updated (Section 5: Mission M7.9 completion)
- **Self-Verify Command**: `python -m hw4_tourguide --help && python -m hw4_tourguide --from "Boston" --to "MIT" --mode cached --output output/test_route.json`
- **Expected Evidence**: Help displayed correctly, cached run exits with code 0 and output file created
- **Time Estimate**: M (2-3h)
- **Dependencies**: M7.1, M7.2, M7.3, M7.8, M4.1
- **Blocks**: M7.10

### **M7.10 – Integration Tests (End-to-End Pipeline)**
- **Status**: [✓] Completed
- **Objective**: Write integration tests that run full pipeline with cached route data
- **Rubric Focus**: Testing (10%), Code Quality (15%)
- **Definition of Done**:
  1. `tests/test_integration.py` contains `test_full_pipeline_cached_mode()` that runs entire system with sample route
  2. Test verifies: route loaded → scheduler emits tasks → orchestrator dispatches workers → agents return results → judge scores → output files written
  3. Test assertions: output JSON exists, has correct number of steps, all steps have judge scores, log file contains expected event tags
  4. Test runs in <60 seconds (using cached route, mocked external APIs)
  5. Coverage for integration test ≥80% (ensures main code paths exercised)
  6. `.claude` updated (Section 5: Mission M7.10 completion)
- **Self-Verify Command**: `pytest tests/test_integration.py -v --cov=hw4_tourguide --cov-report=term`
- **Expected Evidence**: Integration test passes, coverage report shows ≥80% overall
- **Time Estimate**: L (4-5h)
- **Dependencies**: M7.1, M7.2, M7.3, M7.4, M7.5, M7.6, M7.7, M7.7a, M7.7b, M7.7c, M7.7d, M7.8, M7.9, M4.1
- **Blocks**: GATE 4

### **M7.11 – Concurrency Verification Tests**
- **Objective**: Write tests that prove agents execute concurrently (overlapping timestamps in logs)
- **Rubric Focus**: Testing (10%), Concurrency (NFR-2), KPI #5
- **Definition of Done**:
  1. `tests/test_concurrency.py` contains `test_multi_agent_overlap()` that spawns Video/Song/Knowledge agents simultaneously
  2. Test captures start/end timestamps for each agent using mock delays (e.g., 0.5s sleep per agent)
  3. Test assertion: at least 2 agents have overlapping execution windows (start_time_A < end_time_B and start_time_B < end_time_A)
  4. Log inspection: timestamps in system.log show overlapping agent activity
  5. Test passes consistently (no race conditions, thread-safe queue usage)
  6. `.claude` updated (Section 5: Mission M7.11 completion)
- **Self-Verify Command**: `pytest tests/test_concurrency.py -v && grep -E "VideoAgent|SongAgent|KnowledgeAgent" logs/system.log | head -20`
- **Expected Evidence**: Test passes, logs show interleaved agent events (not strictly sequential)
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: M7.2, M7.3, M7.4, M7.5, M7.6, M7.7d, M4.1
- **Blocks**: GATE 4

### M7.12 – Resilience & Retry Tests
- **Objective**: Write tests that verify retry/backoff logic for API failures
- **Rubric Focus**: Testing (10%), Reliability (NFR-1), KPI #11
- **Definition of Done**:
  1. `tests/test_resilience.py` contains tests for network failures, API rate limits, timeout errors
  2. Test `test_route_provider_retry()`: mock API failure (ConnectionError) → verify 3 retry attempts with exponential backoff
  3. Test `test_agent_timeout()`: mock slow API response → verify timeout exception after 10s, fallback to empty result
  4. Test `test_graceful_degradation()`: if Video Agent fails → verify system continues with Song/Knowledge results, marks video as unavailable
  5. All resilience tests pass, log shows retry attempts and backoff delays
  6. `.claude` updated (Section 5: Mission M7.12 completion)
  7. **NEW (ADR-010):** Test `test_circuit_breaker_opens_after_threshold()`: Mock API to fail 5 times, verify circuit breaker opens, verify subsequent calls rejected with `CircuitBreakerOpenError`
  8. **NEW (ADR-010):** Test `test_circuit_breaker_half_open_recovery()`: Verify circuit transitions OPEN → HALF_OPEN after timeout, then HALF_OPEN → CLOSED on successful API call
  9. **NEW (ADR-009):** Test `test_checkpoint_recovery()`: Verify pipeline can resume from checkpoint file (e.g., read `02_agent_search_video.json` and continue from fetch phase)
- **Self-Verify Command**: `pytest tests/test_resilience.py -k retry -v && pytest tests/test_resilience.py -k circuit_breaker -v && grep "RETRY\\|CircuitBreaker" logs/system.log | wc -l`
- **Expected Evidence**: Retry tests pass, circuit breaker tests pass, checkpoint recovery test passes, log shows retry and circuit breaker state transitions
- **Time Estimate**: M (3-4h) [increased to 4-5h due to circuit breaker and checkpoint tests]
- **Status**: [✓] Completed
- **Dependencies**: M7.1, M7.4, M7.5, M7.6, M7.7a (checkpoint), M7.7c, M7.7e (circuit breaker), M4.1
- **Blocks**: M7.14

### M7.14 – Agent Prompt Infrastructure (LLM Intelligence Layer - Foundation)
- **Objective**: Create markdown-based agent definition system for LLM-guided query generation and candidate selection
- **Rubric Focus**: Architecture (10%), Code Quality (15%), Documentation (15%)
- **Definition of Done**:
  1. Directory `.claude/agents/` created with 4 markdown files: `video_agent.md`, `song_agent.md`, `knowledge_agent.md`, `judge_agent.md`
  2. Each markdown defines: **Role** (expert identity), **Mission** (what to find), **Context** (input fields available), **Skills** (what agent can do), **Process** (workflow steps), **Constraints** (limits: duration, search cap, budget), **Output Format** (JSON structure with queries/reasoning)
  3. `.claude/agents/README.md` explains prompt structure, template variables (location_name, search_hint, instructions, route_context), and how agents use prompts
  4. `src/hw4_tourguide/tools/prompt_loader.py` implemented with methods:
     - `load_agent_prompt(agent_type: str) -> str` - Load raw markdown template
     - `load_prompt_with_context(agent_type: str, context: Dict) -> str` - Load + substitute variables
  5. Prompt templates include placeholders: `{location_name}`, `{search_hint}`, `{instructions}`, `{route_context}`, `{search_limit}`, `{min_duration}`, `{max_duration}`
  6. Test file `tests/test_prompt_loader.py` covers:
     - Loading existing prompt files (success case)
     - Handling missing file (FileNotFoundError raised)
     - Template variable substitution (context dict → formatted prompt)
     - Invalid markdown handling (malformed file)
  7. Documentation: Add ADR-013 "Agent Intelligence via Markdown-Defined LLM Prompts" to `docs/architecture/adr_register.md` with context (heuristic limitations), decision (separate prompts from code), alternatives (hardcoded prompts, fine-tuned models), consequences (easy iteration, cost control, observable), rationale (industry standard pattern), cost analysis ($0.001 per location)
  8. `.claude` updated (Section 5: Mission M7.14 completion)
- **Self-Verify Command**: `ls .claude/agents/*.md | wc -l && pytest tests/test_prompt_loader.py -v && python -c "from hw4_tourguide.tools.prompt_loader import load_agent_prompt; print(load_agent_prompt('video')[:100])"`
- **Expected Evidence**: 5 markdown files exist (4 agents + README), PromptLoader tests pass (100% coverage), Prompt loads successfully with first 100 chars displayed, ADR-013 documented
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: M7.7b (LLM client already exists), M4.1 (test framework)
- **Blocks**: M7.15

### **M7.15 – LLM-Based Query Generation for Agents**
- **Objective**: Enable agents to use LLM for intelligent, context-aware query generation with fallback to heuristics
- **Rubric Focus**: Functional Requirements (20%), Code Quality (15%), Architecture (ADR-013)
- **Definition of Done**:
  1. `BaseAgent.__init__` accepts new parameter: `llm_client: Optional[LLMClient] = None`
  2. `BaseAgent._build_queries_with_llm(task: Dict) -> List[str]` method implemented:
     - Loads agent prompt from markdown via `PromptLoader.load_prompt_with_context(self.agent_type, task)`
     - Substitutes task context variables: location_name, search_hint, instructions, route_context, search_limit
     - Calls `llm_client.query(prompt)` with timeout (config `agents.llm_query_timeout`, default 10.0s) and retries (3 attempts, exponential backoff)
     - Parses JSON response to extract queries list: `{"queries": ["query1", "query2"], "reasoning": "..."}`
     - Logs: `"LLM query generation for {location_name} | time={duration_ms}ms"` with event_tag "Agent" and transaction_id
     - Increments metric: `MetricsCollector.increment_counter('llm_calls.query_generation')`
     - Records latency: `MetricsCollector.record_latency('llm.query_generation_ms', duration_ms)`
     - Returns: List[str] of queries
  3. `BaseAgent._build_queries()` modified to try LLM first with fallback:
     ```python
     def _build_queries(self, task: Dict) -> List[str]:
         if self.llm_client and self.config.get("use_llm_for_queries"):
             try:
                 return self._build_queries_with_llm(task)
             except Exception as exc:
                 self.logger.warning(f"LLM query gen failed: {exc}, fallback to heuristic", extra={"event_tag": "Agent"})
                 self._metrics.increment_counter("llm_fallback.query_generation")
         return self._build_queries_heuristic(task)  # Existing concatenation logic
     ```
  4. Rename current `_build_queries()` to `_build_queries_heuristic()` (preserve existing logic as fallback)
  5. `VideoAgent`, `SongAgent`, `KnowledgeAgent` `__init__` updated:
     - Accept `llm_client` parameter
     - Pass to BaseAgent constructor
     - No other changes (interface stays identical)
  6. Config updated in `config/settings.yaml`:
     ```yaml
     agents:
       use_llm_for_queries: true           # Enable LLM query generation
       use_llm_for_selection: false        # Phase 2 feature (not implemented)
       llm_fallback: true                  # Fallback to heuristics if LLM fails
       llm_query_timeout: 10.0             # Timeout for query generation (seconds)
       llm_max_prompt_chars: 4000          # Max prompt length (cost control)
       video:
         prompt_file: ".claude/agents/video_agent.md"
       song:
         prompt_file: ".claude/agents/song_agent.md"
       knowledge:
         prompt_file: ".claude/agents/knowledge_agent.md"
     ```
  7. Tests in `tests/test_llm_query_generation.py`:
     - `test_llm_query_generation_success()`: Mock LLM returns queries → verify parsed correctly
     - `test_llm_query_generation_timeout()`: Mock LLM timeout → verify fallback to heuristic
     - `test_llm_query_generation_malformed()`: Mock LLM returns invalid JSON → verify fallback
     - `test_llm_disabled_via_config()`: Config flag `use_llm_for_queries: false` → verify LLM not called
     - `test_no_llm_client_provided()`: No llm_client → verify uses heuristic
  8. Update existing agent tests:
     - `tests/test_video_agent.py`: Add `test_video_agent_with_llm()` with mocked LLM client
     - `tests/test_song_agent.py`: Add `test_song_agent_with_llm()` with mocked LLM client
     - `tests/test_knowledge_agent.py`: Add `test_knowledge_agent_with_llm()` with mocked LLM client
  9. Logging verification:
     - LLM calls logged: `"LLM generated {N} queries | time={duration_ms}ms"` with event_tag "Agent"
     - Prompts redacted in logs (log length, not full 4K chars)
     - LLM responses logged (summary: query count, not full JSON)
     - Fallback logged: `"LLM query gen failed: {exc} | fallback=heuristic"`
  10. Metrics verification:
      - `llm_calls.query_generation` counter increments per LLM call
      - `llm_fallback.query_generation` counter increments on fallback
      - `llm.query_generation_ms` latency recorded
  11. `.claude` updated (Section 5: Mission M7.15 completion)
- **Files Created**:
  - `tests/test_llm_query_generation.py`
- **Files Modified**:
  - `src/hw4_tourguide/agents/base_agent.py` (add ~80 lines: llm_client param, _build_queries_with_llm method, modify _build_queries)
  - `src/hw4_tourguide/agents/video_agent.py` (add llm_client parameter to __init__)
  - `src/hw4_tourguide/agents/song_agent.py` (add llm_client parameter to __init__)
  - `src/hw4_tourguide/agents/knowledge_agent.py` (add llm_client parameter to __init__)
  - `config/settings.yaml` (add agents.use_llm_for_queries and related flags)
  - `tests/test_video_agent.py` (add 1 test case with LLM)
  - `tests/test_song_agent.py` (add 1 test case with LLM)
  - `tests/test_knowledge_agent.py` (add 1 test case with LLM)
- **Self-Verify Command**: `pytest tests/test_llm_query_generation.py -v && pytest tests/test_video_agent.py -k llm -v && grep "use_llm_for_queries" config/settings.yaml && python -m hw4_tourguide --mode cached --from "Boston" --to "MIT" --output output/llm_test.json && grep "LLM generated\\|fallback" logs/system.log | wc -l`
- **Expected Evidence**: All tests pass (new + updated agent tests), config flag present, cached run succeeds with/without LLM, logs show "LLM generated N queries" or "fallback to heuristic", metrics show `llm_calls.query_generation` counter
- **Time Estimate**: L (5-7h)
- **Status**: [ ] Not Started
- **Dependencies**: M7.14 (prompt infrastructure), M7.7b (LLM client), M7.7f (metrics), M7.4-M7.6 (agents implemented)
- **Blocks**: M7.16, GATE 4a

### M7.16 – Enhanced Judge Prompt with Markdown Template
- **Objective**: Replace hardcoded judge LLM prompt with markdown-defined template while preserving existing fallback behavior
- **Rubric Focus**: Functional Requirements (20%), Code Quality (15%), Architecture (ADR-013)
- **Definition of Done**:
  1. `.claude/agents/judge_agent.md` enhanced with detailed scoring criteria:
     - **Role**: "Expert content curator and quality assessor for driving route enrichment"
     - **Mission**: "Evaluate agent outputs and select the best content for each location"
     - **Scoring Criteria**: Relevance (matches location context), Quality (metadata completeness), Diversity (variety across route)
     - **Input Format**: Task context (location, hint, instructions) + agent results (video, song, knowledge with metadata)
     - **Output Format**: JSON with `{"chosen_agent": "video|song|knowledge", "rationale": "explanation", "individual_scores": {"video": 0-100, "song": 0-100, "knowledge": 0-100}}`
  2. `judge.py._llm_score()` method modified (lines 263-293):
     - Load prompt template: `PromptLoader.load_prompt_with_context("judge", context)`
     - Context includes: task (location_name, search_hint, instructions), agent_results (sanitized: agent_type, metadata.title, metadata.description, metadata.source)
     - Keep existing response parsing (lines 287-293): extract chosen agent from LLM text
     - Keep existing error handling (catch exceptions, return None → fallback to heuristic)
  3. Judge prompt markdown includes:
     - **Context Variables**: `{location_name}`, `{search_hint}`, `{instructions}`, `{video_title}`, `{video_desc}`, `{song_title}`, `{song_artist}`, `{knowledge_title}`, `{knowledge_summary}`
     - **Constraints**: "Respond in 2-3 sentences max", "Choose one agent type", "Provide specific reasoning"
  4. Test in `tests/test_judge.py`:
     - Existing LLM tests (lines 100+) still pass (verify no regressions)
     - Add `test_judge_llm_with_markdown_template()`: Mock LLM client → verify prompt loaded from markdown → verify response parsed correctly
     - Verify prompt contains task context (location_name, agent metadata)
  5. Config unchanged (judge already has `use_llm`, `llm_provider`, `llm_scoring` flags from ADR-012)
  6. Logging: No changes (judge already logs LLM calls with event_tag "Judge")
  7. `.claude` updated (Section 5: Mission M7.16 completion)
- **Files Created**: None (judge_agent.md created in M7.14)
- **Files Modified**:
  - `.claude/agents/judge_agent.md` (enhance from M7.14 stub to full prompt with scoring criteria)
  - `src/hw4_tourguide/judge.py` (modify ~15 lines in `_llm_score()` method to load markdown template)
  - `tests/test_judge.py` (add 1 test case: `test_judge_llm_with_markdown_template()`)
- **Self-Verify Command**: `pytest tests/test_judge.py -k llm -v && python -m hw4_tourguide --mode cached --from "Boston" --to "MIT" --output output/judge_llm_test.json && grep "Judge.*LLM" logs/system.log`
- **Expected Evidence**: Judge tests pass (including new markdown template test), cached run succeeds, logs show judge using LLM or fallback to heuristic, judge decision includes rationale
- **Time Estimate**: M (2-3h)
- **Status**: [✓] Completed
- **Dependencies**: M7.14 (judge_agent.md created), M7.15 (LLM query generation pattern established), M7.7 (judge implemented)
- **Blocks**: M8.5 (documentation), GATE 4a

### **M7.17 – Coverage Elevation for Core & LLM Paths**
- **Objective**: Raise coverage to ≥85% by exercising untested CLI/LLM/live-provider/judge paths while keeping functionality unchanged.
- **Rubric Focus**: Testing (10%), Code Quality (15%), Architecture (10%)
- **Definition of Done**:
  1. Add targeted tests covering:
     - CLI entry (`__main__.py`) via subprocess/monkeypatch with stub providers to hit argument parsing, logging setup, agent/judge construction.
     - LLM client factory/backoff/budget guards (`tools/llm_client.py`) using mocked HTTP responses for at least one provider (e.g., OpenAI or mock) and token budget overflow.
     - Live route provider path (`route_provider.py`) with mocked requests to cover retry/backoff and transform logic.
     - Client wrappers (`youtube_client.py`, `spotify_client.py`, `wikipedia_client.py`) via requests-mock to hit search/fetch happy paths and one error path each.
     - Judge LLM/hybrid branch (reuse mock LLM from M7.16) to cover `_llm_score` path.
  2. Coverage report shows overall ≥85% with no new skips; CLI no longer 0% covered.
  3. No production code changes except test fixtures/mocks; config/doc updates limited to referencing new tests.
  4. Documentation updated: README testing section mentions the coverage suite; PRD/Missions updated with M7.17 and verification command.
  5. `.claude` updated (Section 5: Mission M7.17 completion) noting coverage achieved.
- **Self-Verify Command**: `pytest --cov=hw4_tourguide --cov-report=term --maxfail=1`
- **Dependencies**: M7.12 (resilience tests), M7.15 (LLM queries), M7.16 (judge LLM), existing test framework; optional requests-mock/ responses dependency if needed.
- **Status**: [✓] Completed
- **Blocks**: GATE 4a, GATE 4

### M7.18 – Live Mode Coverage & Metrics Toggle
**Goal:** Verify live API clients and metrics collection in integration tests.
- [x] Ensure `test_route_provider_live.py` is skipped unless keys present (or mocked correctly)
- [x] Verify `metrics.json` is written during integration runs
- [x] Test `checkpoints_enabled: false` config (performance mode)
- **Definition of Done:** Live clients have test coverage (mocked or live); metrics confirmed.
- **Status**: [✓] Completed

### 🚦 GATE 4a – LLM Agent Integration Complete
- **Criteria**:
  - [x] Agent Prompt Infrastructure (Loader + Templates) merged
  - [x] Agents can generate queries via LLM (with fallback)
  - [x] Judge uses LLM for scoring (with fallback)
  - [x] Coverage >85% maintained
  - [x] `pytest` passes all new LLM-related tests
- **Status**: Passed

### **M7.13 (Optional) – Advanced Multi-Source + LLM/Embedding Rerank**
- **Objective**: Explore multi-source search with optional LLM/embedding-based query expansion, reranking, and summarization
- **Definition of Done**:
  1. Agents generate multiple query variants (templated or LLM-assisted) from task context and query multiple sources in parallel (e.g., Video: YouTube/Vimeo/Dailymotion; Song: Spotify/Apple/YouTube; Knowledge: Wikipedia/DuckDuckGo/blogs) behind config flags
  2. Fetch light metadata for top candidates across sources; score by relevance to address/search_hint/context, authority, quality signals; optional LLM/embedding rerank with budget/cost guards
  3. Optional LLM summarization of candidate content (short rationale) for judge/report; fall back to heuristic-only paths on error/off state
 4. Preserve checkpoints for candidates/scores; tests cover multi-source fan-out, rerank/summary paths (mocked), and graceful degradation when secondary sources/timeouts occur
 5. Off by default to control cost/complexity; enabled via config; disabled path must remain functional
- **Status**: [ ] Skipped (Optional)
- **Dependencies**: M7.7b (LLM client), M7.7c (search/fetch), M7.7f (metrics)

### **M7.19 (Optional) – Claude CLI LLM Provider Support**
- **Objective**: Add a CLI-based LLM provider option (Claude CLI) alongside API-key providers so agents/judge can run via local Claude CLI without code changes elsewhere.
- **Rubric Focus**: Architecture (10%), Code Quality (15%), Testing (10%), Configurability (NFR-8)
- **Definition of Done**:
  1. Implement `ClaudeCliClient` in `src/hw4_tourguide/tools/llm_client.py` that shells out via `subprocess.run` (configurable command/model/extra args), enforces timeout, captures stdout as `{"text": ...}`, and retries/backoff consistent with other providers.
  2. Extend `llm_factory` to accept `llm_provider: "claude_cli"` (and `auto` should pick it if API keys absent but `llm_cli_enabled: true`). Wire config fields: `llm_cli_command` (default `["claude","chat","--model","claude-3-haiku-20240307"]`), `llm_cli_extra_args` (list), `llm_cli_env` (optional env overrides), `llm_cli_timeout` (fallback to llm_timeout), `llm_cli_max_prompt_chars` (reuse global).
  3. Config/schema updates: `config/settings.yaml` comments include `"claude_cli"` as valid provider; add CLI settings with defaults; update any validation to allow this provider.
  4. Tests:
     - New test file `tests/test_llm_cli_client.py` (or added to `tests/test_llm.py`) covering: happy path (stub subprocess returns JSON/text), non-zero exit (raises LLMError), timeout (raises), prompt truncation, retry/backoff invocation, and factory selection when `llm_provider="claude_cli"` and when `auto` + `llm_cli_enabled=true` with no API keys.
     - Add one agent-level smoke test using a fake CLI client injected into BaseAgent to verify `_build_queries_with_llm` parses CLI text.
  5. Docs:
     - README configuration section mentions the new `claude_cli` option, required local CLI install/auth, and how to enable via config.
     - PRD/ADR register: note provider option in LLM stack (no new ADR required; add one bullet under existing LLM decision).
     - Missions/Progress Tracker updated with M7.19 entry and verification command.
  6. Long-route readiness checklist:
     - Note in README/PRD that agents are instantiated once per run; `max_search_calls_per_run` and LLM token budgets are per-run caps. For long routes, recommend configurable profiles (e.g., “long-route mode”: `max_search_calls_per_run` ≥ 50, `max_workers` 8-10, `llm_max_tokens` ≥ 20000 for agents, judge ≥ 30000, `llm_query_timeout` 30s) and caution on API quotas.
     - Add guidance that search caps, timeouts, retries, and token budgets are the primary knobs to avoid premature fallback on long routes; document how to override via YAML/CLI/env.
     - Add a doc note to keep circuit-breaker thresholds/timeouts aligned with provider reliability (threshold 5, timeout 60s OK), and to monitor rate-limit logs (429) before raising caps.
     - Provide sizing example for 8-step routes: set `agents.llm_max_tokens: 50000`, `judge.llm_max_tokens: 25000`, and `max_search_calls_per_run` for each agent (video/song/knowledge) to ~32 so each step can issue LLM-assisted queries without hitting per-run caps; keep search_limit at 3. These values assume ~1.2–1.4k tokens per agent LLM call and ~1.2–1.7k per judge call with short completions, leaving headroom. Retain timeouts/retries and circuit breaker as guardrails; if provider rate-limits (429), retries/backoff still apply and fallback will mark unavailable rather than drop tasks.
     - Explicitly validate long-route runs: execute an 8-step cached run with elevated caps/budgets and confirm no fallback due to limits (LLM token exhaustion, search caps, circuit breaker). If fallback occurs because of configured limits (not API errors), ensure logs/metrics record it (e.g., `llm_fallback.query_generation` counters, warnings indicating cap/budget reached), and document the observed limits and suggested cap increases.
  6. Logging/metrics: CLI client logs provider name `ClaudeCliClient` with event_tag `LLM`; errors/timeouts mirror other providers; usage tokens omitted/zeroed. No changes to agent/judge logic.
- **Self-Verify Command**: `pytest tests/test_llm_cli_client.py -v && pytest tests/test_llm.py -k claude_cli -v`
- **Expected Evidence**: Tests pass; llm_factory returns `ClaudeCliClient` when configured; logs show `provider=ClaudeCliClient`; agent smoke test shows queries parsed from CLI text.
- **Time Estimate**: M (2-4h)
- **Status**: [ ] Skipped (Optional)
- **Dependencies**: M7.7b (LLM abstraction), M7.14 (prompt infrastructure), M7.15 (agent LLM queries)
- **Blocks**: None

### **GATE 4 – Core Implementation Complete**
- **Criteria**: M7.0-M7.12 complete; all unit + integration tests pass; coverage ≥85%; CLI functional; concurrency proven
- **Verification**: `pytest --cov=hw4_tourguide --cov-report=term && python -m hw4_tourguide --from "Boston" --to "MIT" --mode cached`
- **Blocker Recovery**: If tests fail or coverage <85%, fix before Phase 6
- **Status**: [✓] Completed

---

## Phase 6: Analysis & Documentation Polish (Due Dec 2-3)

### **M8.1 – Research Analysis Execution**
- **Objective**: Execute 4 research studies and populate results notebook with findings
- **Rubric Focus**: Research & Analysis (10%), Documentation (15%)
- **Definition of Done**:
  1. Study 1 (Orchestration Efficiency): Run 5 test routes, capture scheduler/orchestrator/agent timestamps, log queue depth at each scheduler push, generate Gantt chart showing parallelism and queue depth over time
  2. Study 2 (Cost Analysis): Run same route in live vs cached mode, compare API call counts (Maps/YouTube/Wikipedia/LLM), calculate cost savings
  3. Study 3 (Judge LLM Impact): Run route with heuristic-only judge vs LLM-assisted judge, compare score variance and rationale quality
  4. Study 4 (Results Visualization): Create ≥4 plot types (bar: agent call counts, line: queue depth over time, scatter: judge scores vs location popularity, heatmap: concurrency matrix)
  5. All findings documented in `docs/analysis/results.ipynb` with LaTeX formulas (e.g., cost_savings = (live_calls - cached_calls) / live_calls * 100)
  6. `.claude` updated (Section 5: Mission M8.1 completion)
- **Self-Verify Command**: `jupyter nbconvert --to html docs/analysis/results.ipynb && open docs/analysis/results.html`
- **Expected Evidence**: Notebook renders with ≥4 plots, LaTeX formulas, analysis text
- **Time Estimate**: XL (8-12h)
- **Status**: [→] In Progress
- **Dependencies**: M5, M7.10, GATE 4
- **Blocks**: M8.2

### **M8.2 – Cost Analysis Documentation**
- **Objective**: Complete `docs/cost_analysis.md` with API/token breakdown and optimization strategies
- **Rubric Focus**: Research & Analysis (10%), Documentation (15%)
- **Definition of Done**:
  1. Table: API call counts per run (Google Maps, YouTube, Spotify, Wikipedia, LLM) with estimated cost per call
  2. Comparison: live mode vs cached mode (show 90%+ cost reduction via caching)
  3. Token usage table (if LLM used): prompt tokens, completion tokens, total tokens, cost per run
  4. Optimization strategies documented: caching, query depth limits, free-tier APIs prioritized, mock mode for testing
  5. Cost projection: estimate for 100 routes with current settings (show how caching keeps costs under $10)
  6. `.claude` updated (Section 5: Mission M8.2 completion)
- **Self-Verify Command**: `grep -c "^|" docs/cost_analysis.md | head -2`
- **Expected Evidence**: ≥2 tables (API call counts, token usage) with ≥5 rows each
- **Time Estimate**: M (2-3h)
- **Status**: [→] In Progress
- **Dependencies**: M8.1
- **Blocks**: M8.3

### **M8.3 – README Finalization**
- **Objective**: Complete README with all 15+ sections, screenshots, troubleshooting guide, and links to documentation
- **Rubric Focus**: Documentation (15%), Usability (NFR-3), KPI #12
- **Definition of Done**:
  1. Sections complete: Overview, Features, Installation (step-by-step with venv), Usage (CLI examples), Configuration (YAML + .env guide), Architecture (link to C4 diagrams), Testing (pytest commands), Troubleshooting (common errors + fixes), API Reference (link), Research (link to notebook), UX Heuristics (summary + link), **Quality Standards (link to ISO/IEC 25010 assessment with 8 characteristics - mandatory for 90+ scores)**, Contributing, License, Credits, Screenshots/Logs
  2. Screenshots: CLI help output, sample logs (scheduler/orchestrator/agents), output JSON snippet, sample Markdown report
  3. Installation matrix from PRD (10 steps) embedded in README
  4. Troubleshooting: ≥5 common issues (missing API key → solution, import errors → solution, test failures → solution, etc.)
  5. README passes validation script: `python scripts/check_readme.py` reports ≥15 sections
  6. `.claude` updated (Section 5: Mission M8.3 completion)
- **Self-Verify Command**: `python scripts/check_readme.py && wc -l README.md`
- **Expected Evidence**: Script reports ≥15 sections, README ≥300 lines
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: M8.2
- **Blocks**: M9.1

### **M8.4 – Documentation Cross-Check & Links**
- **Objective**: Verify all documentation is complete, linked correctly, and referenced in README
- **Rubric Focus**: Documentation (15%), Submission Guidelines Compliance
- **Definition of Done**:
  1. All required docs exist and linked in README: PRD, Missions, Progress Tracker, .claude, Architecture (C4 + ADRs), API Reference, UX Heuristics, Cost Analysis, Results Notebook, Prompt Log, **ISO/IEC 25010 Quality Assessment (table with 8 characteristics: Functional Suitability, Performance Efficiency, Compatibility, Usability, Reliability, Security, Maintainability, Portability - mandatory for 90+ scores)**
  2. Internal links work (test all markdown links with `markdown-link-check` or manual verification)
  3. JSON contracts (`docs/contracts/*.json`) validated with sample data
  4. Screenshots saved in `docs/screenshots/` and referenced in README/UX heuristics
  5. Prompt log (`docs/prompt_log/`) contains ≥5 entries documenting LLM prompt iterations
  6. **ISO/IEC 25010 assessment document (`docs/quality/iso_25010_assessment.md`) contains table mapping all 8 characteristics to project evidence with verification commands**
  7. `.claude` updated (Section 5: Mission M8.4 completion)
- **Self-Verify Command**: `ls docs/{architecture,contracts,ux,analysis,prompt_log,screenshots,quality} && grep -c "docs/" README.md && grep -c "ISO/IEC 25010" docs/quality/iso_25010_assessment.md`
- **Expected Evidence**: All directories exist, README references docs/ ≥15 times, ISO assessment has ≥8 characteristics documented
- **Time Estimate**: S (1-2h)
- **Status**: [✓] Completed
- **Dependencies**: M8.3
- **Blocks**: M8.5

### M8.5 – LLM Agent Architecture Documentation
- **Objective**: Update all architecture documentation (PRD, ADRs, C4 diagrams, Missions, Progress Tracker, README) to reflect LLM agent intelligence layer
- **Rubric Focus**: Documentation (15%), Architecture (10%)
- **Definition of Done**:
  1. **PRD** (`PRD_Route_Enrichment_Tour_Guide_System.md`) updates:
     - Section 6 (Architecture Overview): Add subsection "6.4 Agent Intelligence Layer" describing LLM-based query generation pattern with markdown-defined prompts
     - Section 6a (Architecture Decisions): Add ADR-013 summary with link to full ADR
     - Section 12 (Testing Strategy): Add "LLM Agent Testing" subsection covering mocked LLM responses, fallback testing, integration tests with LLM enabled/disabled
     - Evidence Matrix: Add 3 entries for M7.14 (prompt infrastructure), M7.15 (LLM query generation), M7.16 (judge enhancement) with verification commands
  2. **ADR Register** (`docs/architecture/adr_register.md`) updates:
     - Add full ADR-013 "Agent Intelligence via Markdown-Defined LLM Prompts" (5-10 pages) with sections:
       - Status: ✅ Accepted (2025-11-26)
       - Context: Heuristic query generation limitations (string concatenation, no context awareness)
       - Decision: Separate agent intelligence (prompts in markdown) from orchestration logic (code)
       - Alternatives Considered: A) Hardcoded LLM prompts in code (rejected: hard to iterate), B) LLM for everything (rejected: high cost), C) Fine-tuned models (rejected: over-engineering)
       - Consequences: Pros (context-aware queries, easy tuning, cost control, observable, industry standard), Cons (LLM dependency, latency, non-deterministic)
       - Rationale: Markdown prompts are CrewAI/LangGraph/AutoGen standard; separates intelligence from orchestration
       - Implementation Details: Storage (`.claude/agents/*.md`), data flow (BaseAgent → PromptLoader → LLMClient → parse queries)
       - Cost Analysis: $0.001 per location (3 agents × $0.0003), vs heuristic $0.00
       - Related Missions: M7.14, M7.15, M7.16
       - References: CrewAI Agent Definitions, LangGraph patterns, OpenAI Assistants
     - Update summary table: Now 13 ADRs (was 12)
     - Update change log: Date 2025-11-26, Version 1.3, Added ADR-013 (LLM agent prompts)
  3. **C4 Diagrams** (`docs/architecture/c4_diagrams.md`) updates:
     - Level 2 (Container): Add ".claude/agents/" container as "Agent Prompt Definitions (Markdown)" alongside config/logs/output
     - Level 3 (Component): Add PromptLoader component in "Cross-Cutting Concerns" section
     - Level 3 (Component): Update Agent layer description to mention "LLM-guided query generation with markdown prompts"
     - Add new sequence diagram "Agent Query Generation with LLM":
       ```
       BaseAgent → PromptLoader: load_prompt_with_context(agent_type, task)
       PromptLoader → .claude/agents/: read video_agent.md
       PromptLoader → BaseAgent: formatted prompt
       BaseAgent → LLMClient: query(prompt)
       LLMClient → External LLM API: POST /chat/completions
       External LLM API → LLMClient: {"queries": [...]}
       LLMClient → BaseAgent: parsed queries
       BaseAgent → SearchTool: search(query)
       ```
  4. **Missions** (`Missions_Route_Enrichment_Tour_Guide_System.md`) updates:
     - Already updated with M7.14, M7.15, M7.16, GATE 4a, M8.5 (this mission)
     - Update mission count: 47 total (was 43)
     - Update Mission Statistics Summary section with new totals
  5. **Progress Tracker** (`PROGRESS_TRACKER.md`) updates:
     - Phase 5 section: Add M7.14, M7.15, M7.16, GATE 4a entries
     - Phase 6 section: Add M8.5 entry
     - Mission count: 47 (was 43)
     - Time estimates: Add 10-13h for M7.14-M7.16 + M8.5
  6. **README.md** updates:
     - Add section "Agent Intelligence: LLM-Based Query Generation" (after Architecture section):
       - Explain markdown-defined agent prompts
       - Show example: Video Agent role/mission/output format
       - Link to `.claude/agents/README.md` for full details
       - Example: How to customize agent prompts (edit markdown, no code changes)
       - Config flags: `use_llm_for_queries`, `llm_fallback`, `llm_query_timeout`
     - Architecture section: Add bullet "LLM-based intelligent agents with markdown prompt definitions"
     - Features section: Add "Context-aware query generation via LLM (optional, with heuristic fallback)"
  7. `.claude` updated (Section 5: Mission M8.5 completion)
- **Files Created**: None (all files already exist, only updating)
- **Files Modified**:
  - `PRD_Route_Enrichment_Tour_Guide_System.md` (~50 lines added: Section 6.4, ADR-013 summary, test strategy, evidence matrix entries)
  - `docs/architecture/adr_register.md` (~200 lines added: full ADR-013, summary table update, change log)
  - `docs/architecture/c4_diagrams.md` (~100 lines added: container update, PromptLoader component, sequence diagram)
  - `Missions_Route_Enrichment_Tour_Guide_System.md` (already updated with M7.14-M7.16, M8.5, statistics)
  - `PROGRESS_TRACKER.md` (add M7.14-M7.16, M8.5 entries, update counts)
  - `README.md` (~30 lines added: Agent Intelligence section, links, config examples)
- **Self-Verify Command**: `grep "ADR-013" docs/architecture/adr_register.md && grep "M7.14\\|M7.15\\|M7.16\\|M8.5" Missions_Route_Enrichment_Tour_Guide_System.md && grep "Agent Intelligence" README.md && wc -l docs/architecture/adr_register.md`
- **Expected Evidence**: ADR-013 documented with full sections (≥200 lines), C4 diagrams show LLM layer, Missions show M7.14-M7.16+M8.5, Progress Tracker updated, README explains agent prompts, ADR register line count increased by ~200
- **Time Estimate**: M (3-4h)
- **Status**: [✓] Completed
- **Dependencies**: M7.16 (LLM agent integration complete), GATE 4a, M8.4 (doc cross-check)
- **Blocks**: M9.1 (preflight checks)

---

## Phase 7: Submission Preparation (Due Dec 3-4)

### **M9.1 – Pre-Submission Checks (Preflight Script)**
- **Objective**: Create and run preflight script that validates package, tests, docs, config, and Git history before submission
- **Rubric Focus**: Testing (10%), Code Quality (15%), Submission Guidelines
- **Definition of Done**:
  1. `scripts/preflight.py` implements checks: Python version (≥3.11), dependencies installable, config files exist (settings.yaml, .env.example), directories present (logs/, output/, data/), tests pass (pytest exit 0), coverage ≥85%, README sections ≥15, docs exist (PRD, Missions, Tracker, .claude, Architecture, API ref, UX, Cost, Notebook), **Git history (≥15 commits with meaningful messages, .gitignore configured, no secrets in history)**
  2. Preflight script outputs checklist: ✅ or ❌ for each item
  3. Script exits with code 0 if all checks pass, code 1 if any fail (with error details)
  4. **Git history validation**: Check commit count (`git log --oneline | wc -l` ≥15), verify commit messages follow conventional format (feat:, fix:, docs:, test:, refactor:), check no API keys in history (`git log -p | grep -iE "(api_key|secret|password)" → empty or masked`)
  5. README includes section "Running Preflight Checks" with command: `python scripts/preflight.py`
  6. Preflight passes in clean venv: `python -m venv clean_venv && source clean_venv/bin/activate && pip install . && python scripts/preflight.py`
  7. `.claude` updated (Section 5: Mission M9.1 completion)
- **Self-Verify Command**: `python scripts/preflight.py && echo $? && git log --oneline | wc -l`
- **Expected Evidence**: All checks ✅, exit code 0, ≥15 commits
- **Time Estimate**: M (2-3h)
- **Status**: [ ] Not Started
- **Dependencies**: M8.3, M8.4, GATE 4
- **Blocks**: M9.2

### **M9.2 – Self-Evaluation Against Rubric**
- **Objective**: Complete self-evaluation checklist against grader_agent rubric, estimate score, document strengths/gaps
- **Rubric Focus**: All categories (100%), Submission Guidelines
- **Definition of Done**:
  1. `docs/self_evaluation.md` created with rubric category breakdown: Documentation (15%), Code Quality (15%), Testing (10%), Functional Requirements (20%), Architecture (10%), Installation (10%), Research (10%), Configurability (5%), Security (5%)
  2. Self-score estimation for each category with justification (evidence references)
  3. Strengths documented: e.g., "30+ missions with detailed DoD", "≥85% test coverage", "comprehensive research notebook with 4 plot types"
  4. Gaps/risks documented: e.g., "LLM judge not tested with real API (mocked only)", "Cost analysis estimates, not actual spend"
  5. Projected total score: 94-100/100 (Outstanding Excellence band)
  6. Create `docs/submission_checklist.md` mapping all guideline items (from software_submission_guidelines.txt sections 1-12) to evidence artifacts with ✅/❌ status; verify ≥50 items checked
  7. `.claude` updated (Section 5: Mission M9.2 completion)
- **Self-Verify Command**: `cat docs/self_evaluation.md | grep "Category:" | wc -l && grep -c "✅" docs/submission_checklist.md`
- **Expected Evidence**: 9 rubric categories documented, ≥50 checklist items completed
- **Time Estimate**: S (1-2h)
- **Status**: [ ] Not Started
- **Dependencies**: M9.1
- **Blocks**: M9.3

### **M9.3 – Final Verification Run (Live + Cached Demo)**
- **Objective**: Execute final demo runs (live + cached) and archive outputs/logs as submission evidence
- **Rubric Focus**: All Functional Requirements (20%), KPI #9
- **Definition of Done**:
  1. Live mode run: `python -m hw4_tourguide --from "Boston, MA" --to "Cambridge, MA" --mode live --output output/demo_live_route.json` exits 0
  2. Cached mode run: `python -m hw4_tourguide --from "Boston, MA" --to "Cambridge, MA" --mode cached --output output/demo_cached_route.json` exits 0
  3. Both runs produce: JSON output, Markdown summary, CSV export, system.log with ≥50 structured entries, metrics.json with API call counts
  4. Demo outputs archived in `output/demo/` with timestamp and mode label
  5. `docs/demo_run.md` documents both runs with command, log excerpts, output snippets, verification command results
  6. `.claude` updated (Section 5: Mission M9.3 completion)
- **Self-Verify Command**: `ls output/demo/ && grep -E "Scheduler|Orchestrator|Agent|Judge" logs/system.log | wc -l`
- **Expected Evidence**: Demo directory has ≥6 files (2 JSON, 2 MD, 2 CSV), log has ≥50 entries
- **Time Estimate**: M (2-3h including API quotas)
- **Status**: [ ] Not Started
- **Dependencies**: M9.2
- **Blocks**: GATE 5

### **GATE 5 – Submission Ready**
- **Criteria**: M9.1 + M9.2 + M9.3 complete; preflight passes; all docs finalized; demo runs archived; self-evaluation complete
- **Verification**: `python scripts/preflight.py && ls docs/{self_evaluation.md,demo_run.md} && ls output/demo/`
- **Blocker Recovery**: If preflight fails, address issues immediately; ensure demo runs succeed before M10

### **M10 – Final Submission**
- **Objective**: Package project, verify submission guidelines compliance, submit to course platform
- **Rubric Focus**: All categories (100%), Submission Guidelines
- **Definition of Done**:
  1. All files committed to Git (if using version control) or organized in submission directory
  2. `.gitignore` verified: no `.env`, `logs/`, `output/`, `__pycache__/` in repo
  3. Submission checklist from `software_submission_guidelines.pdf` completed (all items ✅)
  4. Archive created: `tar -czf HW4_Route_Enrichment_Tour_Guide_System.tar.gz LLM_Agent_Orchestration_HW4/` (or zip)
  5. Archive uploaded to course platform with submission form: project name, student info, self-evaluation score, README link
  6. Confirmation email received or submission portal shows "Submitted" status
  7. `.claude` updated (Section 5: Mission M10 completion)
- **Self-Verify Command**: `ls HW4_Route_Enrichment_Tour_Guide_System.tar.gz && tar -tzf HW4_Route_Enrichment_Tour_Guide_System.tar.gz | head -20`
- **Expected Evidence**: Archive exists, contains expected file structure (src/, tests/, docs/, config/, README.md, etc.)
- **Time Estimate**: S (1h)
- **Status**: [ ] Not Started
- **Dependencies**: GATE 5
- **Blocks**: None (final mission)

---

## Mission Statistics Summary

- **Total Missions**: 47 (M0 + M1-M10 with sub-missions, including M7.0 walking skeleton, M6.1 for JSON schemas, M7.1a cached demos, M7.7a-f foundations, M7.14-M7.16 LLM agent intelligence, M8.5 LLM docs, optional M7.13 advanced rerank)
- **Quality Gates**: 7 (GATE 0, GATE 1-5, GATE 4a LLM integration)
- **Estimated Total Effort**: ~108-145 hours (single developer; includes LLM agent layer + optional foundations)
- **Critical Path**: M0 → M1 → M2.0 → GATE1 → M3 → GATE2 → M4.1 → M7.0 → M6.1 → M7.7a-f → M7.1-7.12 → M7.14-M7.16 → GATE4a → GATE4 → M8.1-8.5 → M9.1-9.3 → GATE5 → M10
- **Parallelization Opportunities**: M7.4-7.6 (agents), M7.7a-f (tools), M8.1-8.4 (docs/research) in parallel when gates allow; M7.14 can start after M7.7b completes

---

## Status Legend
- **[ ]** Not Started
- **[→]** In Progress
- **[✓]** Completed
- **[⚠]** Blocked (dependencies unmet or issue encountered)

---

## Notes
1. **Time Estimates**: S (1-2h), M (2-4h), L (4-8h), XL (8-16h) are approximate and assume familiarity with Python, threading, APIs, and testing frameworks. Adjust based on team experience.
2. **Quality Gates**: Do NOT proceed to the next phase if a quality gate fails. Fix issues immediately to avoid compounding technical debt.
3. **Self-Verify Commands**: Run these commands after completing each mission to prove DoD met. Document results in Progress Tracker.
4. **Mission Dependencies**: Some missions can run in parallel (e.g., M7.4-7.6), but ensure upstream dependencies (config, logging, tests) are complete first.
5. **Rubric Alignment**: Each mission explicitly maps to rubric categories to ensure all 100 points are addressed across missions.

---

*Generated by Kickoff Agent v2.2 for Route Enrichment Tour-Guide System – Target Grade: 95*
