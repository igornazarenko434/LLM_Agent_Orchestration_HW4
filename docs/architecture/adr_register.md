# Architecture Decision Records (ADR) Register

**Project:** Route Enrichment Tour-Guide System
**Package:** hw4_tourguide
**Version:** 1.3 (Agent Prompt Infrastructure - LLM Intelligence Layer)
**Last Updated:** 2024-11-26
**Total ADRs:** 13 (Original 7 + Enhanced 6)

---

## ADR Summary Table

| ADR # | Title | Status | Date | Category | Impact |
|-------|-------|--------|------|----------|--------|
| ADR-001 | Python 3.11+ as Implementation Language | ✅ Accepted | 2024-11-20 | Language | High |
| ADR-002 | Threading (not AsyncIO) for Concurrency | ✅ Accepted | 2024-11-20 | Concurrency | High |
| ADR-003 | Google Maps API with Aggressive Caching | ✅ Accepted | 2024-11-20 | External APIs | High |
| ADR-004 | Search+Fetch Separation for Agent Architecture | ✅ Accepted | 2024-11-20 | Architecture | Medium |
| ADR-005 | YAML Configuration with CLI Overrides | ✅ Accepted | 2024-11-20 | Configuration | Medium |
| ADR-006 | Structured Logging with Python `logging` Module | ✅ Accepted | 2024-11-20 | Observability | Medium |
| ADR-007 | ThreadPoolExecutor for Orchestrator Workers | ✅ Accepted | 2024-11-20 | Concurrency | High |
| **ADR-008** | **Transaction ID (TID) Propagation** | ✅ **Accepted** | **2024-11-22** | **Observability** | **High** |
| **ADR-009** | **File-Based Checkpoints at Every Stage** | ✅ **Accepted** | **2024-11-22** | **Debugging** | **High** |
| **ADR-010** | **Circuit Breaker for External APIs** | ✅ **Accepted** | **2024-11-22** | **Resilience** | **Medium** |
| **ADR-011** | **Metrics Aggregator (Separate from Logging)** | ✅ **Accepted** | **2024-11-22** | **Performance** | **Medium** |
| **ADR-012** | **LLM Client Abstraction (Priority, Budget Guards)** | ✅ **Accepted** | **2025-11-24** | **Architecture** | **Medium** |
| **ADR-013** | **Agent Intelligence via Markdown-Defined LLM Prompts** | ✅ **Accepted** | **2024-11-26** | **Architecture** | **High** |

**Legend:**
- ✅ Accepted: Decision approved and ready for implementation
- 🟡 Proposed: Under review
- ❌ Rejected: Decision rejected with rationale
- ⚠️ Superseded: Replaced by newer ADR

---

## ADR-001: Python 3.11+ as Implementation Language

### Status
✅ **Accepted** (2024-11-20)

### Context
Need modern language with strong ecosystem for networking, threading, data processing, and testing. Project is educational but should use production-grade tools.

### Decision
Use **Python 3.11+** (specifically targeting 3.11.x for development, compatible with 3.12+)

### Alternatives Considered

#### Alternative A: Python 3.9
- **Pros:** Broader compatibility, stable
- **Cons:** Lacks newer performance improvements (faster CPython, improved error messages), missing syntax features
- **Rejected:** Trading performance + developer experience for marginal compatibility gain

#### Alternative B: Node.js/TypeScript
- **Pros:** Excellent async/await support, fast runtime, strong typing with TypeScript
- **Cons:** Instructor examples use Python; steeper learning curve for thread-based concurrency; less familiar ecosystem for data science
- **Rejected:** Misalignment with course focus and instructor tooling

#### Alternative C: Go
- **Pros:** Superior concurrency primitives (goroutines), compiled performance, type safety
- **Cons:** Less familiar ecosystem for data science/notebooks; harder to prototype agents; steeper learning curve
- **Rejected:** Over-engineering for educational project; Python's ecosystem better for rapid development

### Consequences

**Pros:**
- ✅ Rich ecosystem (pytest, requests, pyyaml, jupyter)
- ✅ Instructor familiarity and alignment with course examples
- ✅ Fast prototyping with REPL and notebooks
- ✅ Strong typing with type hints (gradual typing)
- ✅ Performance improvements in 3.11+ (faster CPython)

**Cons:**
- ❌ GIL limits CPU-bound parallelism (mitigated: agents are I/O-bound)
- ❌ Requires virtual environment management
- ❌ Slower than compiled languages (not critical for I/O-bound workload)

### Rationale
Python 3.11+ strikes optimal balance for educational project with production characteristics:
- Instructor examples and course focus on Python
- Fast development cycle for iterative agent design
- Mature libraries for all required integrations (Google Maps, YouTube, etc.)
- GIL not a bottleneck for I/O-bound agents
- Type hints provide safety without Go's compilation overhead

### Related Missions
- M2.0: Package setup with `pyproject.toml`
- M4.1: Pytest framework selection

### References
- Python 3.11 release notes: https://docs.python.org/3/whatsnew/3.11.html
- Course materials (HW4_Project_Mission.md)

---

## ADR-002: Threading (not AsyncIO) for Concurrency

### Status
✅ **Accepted** (2024-11-20)

### Context
Need concurrent execution for scheduler, orchestrator, and agents. Multiple approaches available in Python ecosystem. Instructor spec mentions "multi-threaded" system.

### Decision
Use **`threading.Thread`** for scheduler, **`ThreadPoolExecutor`** for orchestrator workers, standard **`queue.Queue`** for task passing

### Alternatives Considered

#### Alternative A: AsyncIO
- **Pros:** Modern Python approach, efficient for I/O-bound tasks, single-threaded event loop, lower memory overhead
- **Cons:** Requires async/await throughout codebase; harder to debug than synchronous code; incompatible with synchronous libraries; not mentioned in instructor spec
- **Rejected:** Adds complexity without clear benefit for this workload; instructor examples use threading

#### Alternative B: Multiprocessing
- **Pros:** True parallelism via separate processes, bypasses GIL, suitable for CPU-intensive work
- **Cons:** Higher overhead (process creation, IPC), pickle limitations for object passing, overkill for I/O-bound agents
- **Rejected:** Not needed for I/O-bound workload; threading sufficient and simpler

#### Alternative C: Celery
- **Pros:** Distributed task queue, battle-tested for production systems, worker management, monitoring
- **Cons:** Heavy dependency (requires message broker like Redis/RabbitMQ), over-engineering for single-machine deployment
- **Rejected:** Too complex for educational project; threading meets all requirements

### Consequences

**Pros:**
- ✅ Simpler mental model than async/await (synchronous function calls)
- ✅ Matches instructor examples (HW4 spec explicitly mentions "multi-threaded")
- ✅ Standard library only (no extra dependencies)
- ✅ Straightforward debugging (no event loop state)
- ✅ Compatible with all libraries (no async infection)

**Cons:**
- ❌ Not as "modern" as AsyncIO
- ❌ Can't leverage async HTTP libraries (e.g., httpx)
- ❌ Thread overhead higher than coroutines (but negligible for 5-10 threads)
- ❌ GIL limits CPU parallelism (not an issue for I/O agents)

### Rationale
Threading is optimal choice for this project:
- Instructor spec explicitly mentions "multi-threaded" system
- Agents are I/O-bound (network calls to APIs), so GIL not a bottleneck
- Simpler to reason about than async state machines
- Standard library provides all needed primitives (Thread, ThreadPoolExecutor, Queue)
- Easier to test and debug than AsyncIO

### Related Missions
- M7.2: Scheduler thread implementation
- M7.3: Orchestrator ThreadPoolExecutor
- M7.11: Concurrency verification tests

### References
- HW4_Project_Mission.md Section 2.3 (multi-threaded requirement)
- Python threading docs: https://docs.python.org/3/library/threading.html
- ThreadPoolExecutor: https://docs.python.org/3/library/concurrent.futures.html

---

## ADR-003: Google Maps API with Aggressive Caching Strategy

### Status
✅ **Accepted** (2024-11-20)

### Context
Need real route data but free tier limited to 2,500 requests/month. Development requires frequent runs (testing, debugging). Must balance realism with cost control.

### Decision
Implement **`RouteProvider`** abstraction with two backends:
1. **Live:** Google Maps Directions API (for real data)
2. **Cached:** File-based provider reading `data/routes/*.json` (for offline/testing)

### Alternatives Considered

#### Alternative A: MapBox API
- **Pros:** Comparable free tier, different data format may offer more features
- **Cons:** Requires learning new API; less familiar than Google Maps; still has quota limits
- **Rejected:** Google Maps more widely known; no significant advantage

#### Alternative B: OpenStreetMap Nominatim
- **Pros:** Fully open-source, no API key required, unlimited usage
- **Cons:** Geocoding-only (not full routing with turn-by-turn steps); lower quality data than Google
- **Rejected:** Doesn't provide step-by-step route directions needed for enrichment

#### Alternative C: Hard-coded mock routes
- **Pros:** No API dependency, zero cost, fully controlled
- **Cons:** Unrealistic, doesn't demonstrate API integration, not useful for real users
- **Rejected:** Fails to meet requirement of working with real routing data

### Consequences

**Pros:**
- ✅ Caching enables unlimited dev/test runs without API costs
- ✅ Abstraction allows swapping providers (future: MapBox, OSM)
- ✅ Live mode proves real API integration capability
- ✅ Instructor can run cached demos without own API key
- ✅ Demonstrates good software practice (caching, abstraction)

**Cons:**
- ❌ Cached data may become stale (routes change over time)
- ❌ Need to manage cache files (version control, storage)
- ❌ Two code paths to maintain (live + cached)

### Rationale
Aggressive caching is essential for educational project:
- Protects free tier quota (2,500 requests/month)
- Enables rapid iteration during development (no API calls)
- Allows instructor to grade without providing API key (cached mode)
- Demonstrates production pattern (cache expensive operations)
- Abstraction enables future provider swaps (extensibility)

### Implementation Details
- **Mode Selection:** `--mode [live|cached]` CLI flag (default: cached)
- **Cache Storage:** `data/routes/{hash}.json` (hash of from/to)
- **Transaction IDs:** Link cached files to original API requests
- **Schema:** Providers emit a list of task dicts (one per step) ready for the Scheduler; cache files follow `docs/contracts/route_schema.json` when materialized

### Cost Analysis
- **Live mode:** 1 Directions API call (approx. $0.005) + (Number of steps) Geocoding API calls (approx. $0.005/call). For an 8-step route, this is 1 + 8 = 9 calls, costing approx. $0.045 per demo.
- **Cached mode:** $0.00 per demo
- **Savings:** Over 99% for subsequent runs after initial caching.

### Related Missions
- M7.1: Route Provider implementation
- M3: Config for API keys
- M9.3: Live + cached demo runs

### References
- Google Maps Pricing: https://developers.google.com/maps/billing-and-pricing/pricing
- Directions API Docs: https://developers.google.com/maps/documentation/directions

---

## ADR-004: Search+Fetch Separation for Agent Architecture

### Status
✅ **Accepted** (2024-11-20)

### Context
Agents need external data (YouTube videos, Spotify songs, Wikipedia articles). Unclear whether to fetch all candidates or single result. Need to balance quality (more options) with cost (API calls).

### Decision
Each agent implements **two-phase pipeline**:
1. **Search Phase:** Query API, return list of candidate IDs (limit 3)
2. **Fetch Phase:** Retrieve full metadata for selected candidate(s)

### Alternatives Considered

#### Alternative A: Direct Fetch
- **Pros:** Simpler code, one API call per location, faster execution
- **Cons:** No choice (stuck with first result), judge can't compare options, poor quality if first result irrelevant
- **Rejected:** Sacrifices quality for minor cost savings

#### Alternative B: Fetch All Candidates
- **Pros:** Judge can compare all 3 options, highest quality selection
- **Cons:** 4 API calls per location (1 search + 3 fetches), expensive, slower
- **Rejected:** Excessive cost (3× more API calls) for marginal quality gain

#### Alternative C: Streaming Search
- **Pros:** Fetch candidates lazily (generator pattern) until judge satisfied
- **Cons:** Complex state management, harder to test, unclear stopping condition
- **Rejected:** Over-engineering; search+fetch separation sufficient

### Consequences

**Pros:**
- ✅ **Modularity:** Test search/fetch independently
- ✅ **Cost Control:** Fetch only selected items (not all 3)
- ✅ **Flexibility:** Judge can request more data if needed (future)
- ✅ **Clear Logging:** Separate SEARCH and FETCH log entries for debugging
- ✅ **Observability:** Checkpoint search results before fetch

**Cons:**
- ❌ Two API calls instead of one (search + fetch)
- ❌ More code complexity (two methods per agent)
- ❌ Need to design candidate selection logic

### Rationale
Separation makes cost/quality trade-offs explicit:
- Search is cheap (single API call, small payload)
- Fetch is expensive (per-item API call, large payload)
- Enables future optimizations:
  - Cache search results (reuse across runs)
  - Smart candidate ranking (ML model on search results)
  - Lazy fetching (fetch only if judge needs)
- Aligns with instructor's emphasis on "search" and "enrichment" as distinct steps

### Implementation Details
- **Base Class:** `Agent(ABC)` with abstract `search()` and `fetch()` methods
- **Search Output:** `List[CandidateID]` (max 3 items)
- **Fetch Input:** Single `CandidateID`
- **Fetch Output:** `MediaMetadata` (title, URL, description, etc.)
- **Example:**
  ```python
  video_ids = VideoAgent.search("MIT campus")  # ["vid123", "vid456", "vid789"]
  metadata = VideoAgent.fetch("vid123")        # {title, channel, duration, ...}
  ```

### Related Missions
- M7.4: Video Agent implementation
- M7.5: Song Agent implementation
- M7.6: Knowledge Agent implementation
- M5: Cost tracking

### References
- YouTube Data API quota costs: https://developers.google.com/youtube/v3/determine_quota_cost
- Spotify Web API best practices: https://developer.spotify.com/documentation/web-api/concepts/rate-limits

---

## ADR-005: YAML Configuration with CLI Overrides

### Status
✅ **Accepted** (2024-11-20)

### Context
Many tunable parameters (scheduler interval, agent query limits, API endpoints, log levels, output paths). Need balance between flexibility (easy experimentation) and ease of use (sane defaults).

### Decision
**Centralize all parameters in `config/settings.yaml`**, allow CLI flags to override specific values for single-run experiments, load secrets from `.env` file

### Alternatives Considered

#### Alternative A: Environment Variables Only
- **Pros:** 12-factor app pattern, no config files, cloud-native
- **Cons:** Harder to document (20+ env vars), difficult to manage, verbose, hard to version control
- **Rejected:** Impractical for 20+ parameters; YAML more readable

#### Alternative B: Command-Line Flags Only
- **Pros:** Maximum explicitness, no hidden state, full control per run
- **Cons:** Impractical for 20+ parameters (very long commands), no defaults, not user-friendly
- **Rejected:** Too verbose for typical usage

#### Alternative C: Python `config.py` Module
- **Pros:** Code-based config with Python expressions, type checking, IDE support
- **Cons:** Less accessible to non-programmers, requires code restart to change, no comments
- **Rejected:** YAML more user-friendly and standard

### Consequences

**Pros:**
- ✅ **Single Source of Truth:** YAML file documents all parameters with inline comments
- ✅ **CLI Overrides:** Quick experiments without editing files
- ✅ **Human-Readable:** YAML easier than JSON, supports comments
- ✅ **Versionable:** Commit `settings.yaml` to repo (configuration as code)
- ✅ **Flexible:** Power users edit YAML, quick users override via CLI

**Cons:**
- ❌ Two places to check for param values (YAML + CLI)
- ❌ Need precedence rules (CLI > YAML > defaults)
- ❌ YAML parsing adds dependency (pyyaml)

### Rationale
Hybrid approach (YAML + CLI) optimal for this project:
- **Power users:** Edit `settings.yaml` once for consistent settings
- **Quick users:** Override specific flags per run (`--log-level DEBUG`)
- **Instructor:** Can tweak config without code changes
- **Follows best practices:** 12-factor apps (config separate from code)

### Configuration Priority Order
1. **Code defaults** (hardcoded fallbacks)
2. **`config/settings.yaml`** (base configuration)
3. **Environment variables** (`.env` for secrets)
4. **CLI flags** (highest priority, single-run overrides)

### Implementation Details
- **ConfigLoader Class:** Merges sources in priority order
- **`--config` Flag:** Allows custom YAML path
- **Validation:** Required keys checked, defaults applied
- **Example:**
  ```bash
  python -m hw4_tourguide --mode cached --log-level DEBUG
  # Overrides settings.yaml but keeps other params unchanged
  ```

### Related Missions
- M3: Config & Security layer
- M3.1: YAML schema definition
- M7.9: CLI argument parsing

### References
- 12-Factor App Config: https://12factor.net/config
- YAML Spec: https://yaml.org/spec/1.2.2/

---

## ADR-006: Structured Logging with Python `logging` Module

### Status
✅ **Accepted** (2024-11-20)

### Context
Need observability for scheduler/orchestrator/agent activity. Logs must prove concurrency, cadence, cost control for grading. Must be machine-parseable and human-readable.

### Decision
Use **Python standard library `logging`** with custom format: `TIMESTAMP | LEVEL | MODULE | EVENT_TAG | MESSAGE`. Write to `logs/system.log` with rotation. Event tags: `Scheduler`, `Orchestrator`, `Agent`, `Judge`, `Error`, `API_Call`, `Config`.

### Alternatives Considered

#### Alternative A: Print Statements
- **Pros:** Simplest approach, writes to stdout, no setup
- **Cons:** Not structured, no log levels, hard to filter, mixes with normal output, not production-grade
- **Rejected:** Insufficient for observability requirements

#### Alternative B: Third-Party Logger (loguru)
- **Pros:** Modern API, colored output, simpler configuration, better defaults
- **Cons:** Adds dependency, unfamiliar to instructor, non-standard
- **Rejected:** Standard library sufficient; avoid unnecessary dependencies

#### Alternative C: JSON Logs
- **Pros:** Machine-readable, easy to parse with jq, structured by design
- **Cons:** Harder for humans to read during development, verbose, requires jq for inspection
- **Rejected:** Human readability more important for educational project

### Consequences

**Pros:**
- ✅ **Standard Library:** No dependency, familiar to instructor
- ✅ **Configurable Levels:** DEBUG/INFO/WARNING/ERROR for different verbosity
- ✅ **Rotation:** Prevents disk bloat (10MB per file, 5 backups)
- ✅ **Structured Format:** Enables grep filtering (`grep "Scheduler" logs/system.log`)
- ✅ **Event Tags:** Quick filtering by component or event type

**Cons:**
- ❌ Verbose API (need `logger.info(...)` instead of `print(...)`)
- ❌ Requires setup boilerplate
- ❌ Less modern than loguru

### Rationale
Standard library `logging` meets all observability NFR requirements:
- Structured format enables KPI verification commands
- Log rotation prevents disk space issues
- Event tags enable component-specific filtering
- Familiar to instructor (standard Python)
- Zero dependencies

### Log Format
```
2024-11-22 10:15:23.456 | INFO | scheduler | Scheduler | EMIT | Step 1/5: MIT Campus | TID: 1732278923_abc12345
```

**Fields:**
1. Timestamp (ISO 8601 with milliseconds)
2. Level (DEBUG/INFO/WARNING/ERROR)
3. Module (scheduler/orchestrator/agent/judge)
4. Event Tag (Scheduler/Agent/Judge/Error)
5. Event Type (EMIT/DISPATCH/SEARCH/FETCH/SCORE)
6. Message (human-readable description)
7. TID (Transaction ID for correlation)

### Related Missions
- M3.2: Logging infrastructure setup
- M7.2-7.7: Component logging implementation
- M8.4: Log evidence for docs

### Verification
KPI #8 requires ≥50 log entries per run:
```bash
grep -E "Scheduler|Orchestrator|Agent|Judge|Error" logs/system.log | wc -l
```

### References
- Python logging docs: https://docs.python.org/3/library/logging.html
- Structured logging patterns: https://www.structlog.org/en/stable/standard-library.html

---

## ADR-007: ThreadPoolExecutor for Orchestrator Workers

### Status
✅ **Accepted** (2024-11-20)

### Context
Orchestrator needs to spawn concurrent workers to process route steps. Each worker coordinates 3 agents + judge. Must be scalable and testable.

### Decision
Use **`concurrent.futures.ThreadPoolExecutor`** with configurable `max_workers` (default 5). Submit worker jobs as futures, main loop waits for all futures before shutdown.

### Alternatives Considered

#### Alternative A: Manual Thread Management
- **Pros:** More control over thread lifecycle, low-level customization
- **Cons:** Error-prone (thread leaks, zombie threads), complex lifecycle management, reinvents wheel
- **Rejected:** ThreadPoolExecutor handles lifecycle automatically

#### Alternative B: Thread Pool via `queue.Queue` + Daemon Threads
- **Pros:** Custom pool implementation, educational (learn threading internals)
- **Cons:** Reinvents wheel, harder to debug, no standard error handling
- **Rejected:** Standard library solution better

#### Alternative C: ProcessPoolExecutor
- **Pros:** True parallelism via multiprocessing, bypasses GIL
- **Cons:** Overkill for I/O-bound agents, pickle overhead for object passing, higher memory usage
- **Rejected:** Threading sufficient for I/O-bound workload

### Consequences

**Pros:**
- ✅ **Standard Library:** Production-grade pattern, well-tested
- ✅ **Automatic Lifecycle:** Prevents thread leaks, handles cleanup
- ✅ **Futures API:** Simplifies error handling (`future.result(timeout)`)
- ✅ **Easy to Test:** Can mock executor in tests
- ✅ **Graceful Shutdown:** `executor.shutdown(wait=True)` waits for in-flight work

**Cons:**
- ❌ Less control than manual threads
- ❌ Futures add slight abstraction overhead
- ❌ Need to understand executor shutdown semantics

### Rationale
ThreadPoolExecutor is production-grade pattern:
- Automatic cleanup prevents resource leaks
- Futures API allows graceful shutdown (wait for in-flight work)
- Standard library, familiar to Python developers
- Easy to test (mock executor, verify dispatch)

### Implementation Details
- **Initialization:** Orchestrator spawns executor on startup with `max_workers` from config
- **Task Submission:** `executor.submit(worker_fn, task)` for each queue task
- **Shutdown:** `executor.shutdown(wait=True)` on exit signal (Ctrl+C)
- **Configuration:** `orchestrator.max_workers: 5` in `config/settings.yaml`

### Sizing Considerations
- **Default 5 workers:** 3 agents + 2 buffer (handles queue depth)
- **Scalable:** Increase `max_workers` for longer routes (10-20 steps)
- **I/O-bound:** More workers = more concurrency (GIL not a bottleneck)

### Related Missions
- M7.3: Orchestrator & Worker Threads implementation
- M7.11: Concurrency verification tests
- M7.12: Resilience to worker failures

### References
- ThreadPoolExecutor docs: https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor
- Concurrency patterns: https://python-patterns.guide/concurrency/

---

## ADR-008: Transaction ID (TID) Propagation

### Status
✅ **Accepted** (2024-11-22) **[NEW]**

### Context
Multi-threaded system with concurrent agent processing. Need to correlate logs across threads, trace requests end-to-end, debug race conditions. Standard logging doesn't provide request correlation.

### Decision
**Every operation carries a Transaction ID (TID)** from route fetch to final output. TID generated at route fetch time: `f"{timestamp}_{uuid4().hex[:8]}"`. Passed through all components, logged in every message.

### Alternatives Considered

#### Alternative A: No Correlation IDs
- **Pros:** Simpler code, no parameter passing
- **Cons:** Can't correlate logs across threads, debugging nightmares, can't trace specific requests
- **Rejected:** Fatal for debugging multi-threaded systems

#### Alternative B: Thread-Local Storage
- **Pros:** No explicit parameter passing, automatic context
- **Cons:** Magic behavior (implicit context), harder to test, doesn't work with ThreadPoolExecutor (thread reuse)
- **Rejected:** Explicit is better than implicit; parameter passing clearer

#### Alternative C: Correlation via Timestamps
- **Pros:** No extra IDs, use timestamps to correlate
- **Cons:** Ambiguous (multiple requests at same second), fragile, not unique
- **Rejected:** Not reliable for correlation

### Consequences

**Pros:**
- ✅ **Distributed Tracing:** Correlate logs across all threads for single request
- ✅ **Debuggability:** Filter logs by TID to see complete request flow
- ✅ **Observability:** Checkpoint files organized by TID (`output/checkpoints/{TID}/`)
- ✅ **Audit Trail:** Full trace of every decision for single route
- ✅ **Testing:** Verify component interactions via TID in test assertions

**Cons:**
- ❌ Slight overhead (+8 bytes per log entry)
- ❌ Must pass TID through all function calls (parameter pollution)

### Rationale
TID propagation is **essential for production systems**:
- Multi-threaded logging without correlation is useless
- Debugging race conditions requires request tracing
- Checkpoint organization by TID enables replay
- Minimal overhead (8 bytes) for massive observability gain
- Industry standard pattern (OpenTelemetry, Zipkin)

### Implementation Details
- **Generation:** `tid = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"` at route fetch
- **Propagation:** Pass as parameter to all functions: `def process(task: Task, tid: str)`
- **Logging:** Include in every log message: `logger.info(f"Processing | TID: {tid} | ...")`
- **Checkpoints:** Create directory `output/checkpoints/{tid}/` for all intermediate files

### Example TID
```
1732278923_abc12345
├─ 1732278923: Unix timestamp (route fetch time)
└─ abc12345: Random UUID prefix (uniqueness)
```

### Log Filtering
```bash
# View all logs for specific request
grep "TID: 1732278923_abc12345" logs/system.log

# View scheduler events for request
grep "TID: 1732278923_abc12345.*Scheduler" logs/system.log
```

### Related Missions
- M7.1: Route Provider (TID generation)
- M7.2-7.7: All components (TID propagation)
- M7.11: Concurrency tests (TID correlation)

### References
- OpenTelemetry Trace Context: https://opentelemetry.io/docs/concepts/signals/traces/
- Distributed Tracing Patterns: https://microservices.io/patterns/observability/distributed-tracing.html

---

## ADR-009: File-Based Checkpoints at Every Stage

### Status
✅ **Accepted** (2024-11-22) **[NEW]**

### Context
Complex pipeline (route → schedule → agents → judge → output) makes debugging hard. Need to inspect intermediate state, replay from mid-pipeline, verify component outputs independently.

### Decision
**Each pipeline stage writes intermediate results to `output/checkpoints/{TID}/`**. After each major operation, write JSON file following schema. Files: `00_route.json`, `01_scheduler_queue.json`, `02_agent_search_{type}.json`, `03_agent_fetch_{type}.json`, `04_judge_decision.json`, `05_final_output.json`.

### Alternatives Considered

#### Alternative A: No Checkpoints (Logs Only)
- **Pros:** No disk I/O overhead, simpler code
- **Cons:** Can't replay pipeline, can't inspect intermediate state, debugging requires printf-style log reading
- **Rejected:** Insufficient for complex pipeline debugging

#### Alternative B: In-Memory Checkpoints
- **Pros:** Faster (no disk I/O), still enables replay
- **Cons:** Lost on crash, not persistent, can't inspect between runs
- **Rejected:** Defeats purpose of checkpoints (debugging across runs)

#### Alternative C: Database Storage
- **Pros:** Queryable, structured, persistent
- **Cons:** Over-engineering, requires DB setup, not file-based (violates user requirement)
- **Rejected:** Files meet requirement and simpler

### Consequences

**Pros:**
- ✅ **Replay Capability:** Restart pipeline from any checkpoint (e.g., test judge without re-running agents)
- ✅ **Debugging:** Inspect intermediate state at every stage
- ✅ **Audit Trail:** Full trace of every decision made
- ✅ **Testing:** Verify component outputs against expected files (golden file testing)
- ✅ **Observability:** See exactly what each component produced

**Cons:**
- ❌ **Disk I/O Overhead:** 5-10ms per checkpoint write (~50ms total per route)
- ❌ **Disk Space:** ~500KB per route (6 JSON files × ~80KB each)
- ❌ **Management:** Need pruning strategy (auto-delete old checkpoints)

### Rationale
Checkpoints are **invaluable for debugging**:
- Complex pipelines are hard to debug without intermediate state
- Replay from mid-pipeline speeds up development (don't re-run slow API calls)
- Golden file testing verifies component contracts
- Audit trail proves system behavior (for grading evidence)
- Disk I/O overhead negligible compared to API latency (100-500ms)
- Can disable via config for performance testing

### Implementation Details

#### Checkpoint Directory Structure
```
output/checkpoints/{TID}/
├── 00_route.json              # Raw route from Google Maps
├── 01_scheduler_queue.json    # Tasks emitted by scheduler
├── 02_agent_search_video.json # Video agent search results (3 candidates)
├── 02_agent_search_song.json  # Song agent search results
├── 02_agent_search_knowledge.json
├── 03_agent_fetch_video.json  # Video agent fetch result (1 selected)
├── 03_agent_fetch_song.json
├── 03_agent_fetch_knowledge.json
├── 04_judge_decision.json     # Judge scoring + rationale
└── 05_final_output.json       # Aggregated final output
```

#### Checkpoint Manager API
```python
class CheckpointManager:
    def write(self, tid: str, stage: str, data: dict):
        """Write checkpoint to output/checkpoints/{tid}/{stage}.json"""

    def read(self, tid: str, stage: str) -> dict:
        """Read checkpoint for replay"""

    def prune(self, days: int = 7):
        """Delete checkpoints older than N days"""
```

#### Configuration
```yaml
checkpoints:
  enabled: true            # Enable/disable checkpoints
  pruning_days: 7          # Auto-delete after 7 days
  compression: false       # Optional: gzip compress (future)
```

### Pruning Strategy
- **Auto-Prune:** Delete checkpoints >7 days old at startup
- **Manual Prune:** CLI command `python -m hw4_tourguide prune --days 7`
- **Disk Usage:** Monitor `output/checkpoints/` size, warn if >1GB

### Related Missions
- M7.1-7.8: All pipeline components (write checkpoints)
- M7.10: Integration tests (verify checkpoint files)
- M8.1: Research analysis (read checkpoints for metrics)

### References
- Checkpoint Pattern: https://martinfowler.com/eaaCatalog/checkpoint.html
- Event Sourcing: https://martinfowler.com/eaaDev/EventSourcing.html

---

## ADR-010: Circuit Breaker for External APIs

### Status
✅ **Accepted** (2024-11-22) **[NEW]**

### Context
External APIs (Google Maps, YouTube, Spotify, Wikipedia) may fail (timeouts, rate limits, server errors). Retrying failed API repeatedly wastes time and quota. Need to fail fast when API is down.

### Decision
Implement **circuit breaker pattern** for all external API calls. 3 states: **CLOSED** (normal), **OPEN** (failing, no calls), **HALF_OPEN** (testing recovery). Failure threshold: 5 consecutive failures → OPEN. Timeout: 60s in OPEN state → HALF_OPEN. Success in HALF_OPEN → CLOSED.

### Alternatives Considered

#### Alternative A: Retry Logic Only
- **Pros:** Simpler, handles transient failures
- **Cons:** Wastes time on persistent failures, no fail-fast, eats API quota
- **Rejected:** Insufficient for resilient systems

#### Alternative B: Manual Disable Flag
- **Pros:** Simple implementation (if API down, user sets flag)
- **Cons:** Requires manual intervention, not automatic, poor UX
- **Rejected:** Circuit breaker automates recovery

#### Alternative C: Rate Limiter Only
- **Pros:** Prevents quota exhaustion
- **Cons:** Doesn't handle failures, different problem domain
- **Rejected:** Complementary, not alternative (can use both)

### Consequences

**Pros:**
- ✅ **Fail Fast:** Stop hitting failing API immediately (save time + quota)
- ✅ **Auto-Recovery:** Automatically test API health after timeout
- ✅ **Resilience:** Prevent cascading failures (one API down doesn't crash system)
- ✅ **Observability:** Circuit state logged (CLOSED/OPEN/HALF_OPEN)
- ✅ **Graceful Degradation:** Fallback to cached/mock data when circuit OPEN

**Cons:**
- ❌ **Added Complexity:** State machine to maintain
- ❌ **Configuration:** Need to tune failure threshold and timeout
- ❌ **False Opens:** Transient blips may open circuit (mitigated with threshold)

### Rationale
Circuit breakers are **production-grade resilience pattern**:
- Prevent wasting time on failing APIs (fail fast)
- Automatic recovery testing (no manual intervention)
- Graceful degradation (use cached data when API down)
- Standard pattern (Hystrix, resilience4j)
- Minimal overhead (state machine check < 1ms)

### Implementation Details

#### 3-State State Machine
```
CLOSED (normal)
   │
   │ 5 consecutive failures
   ▼
OPEN (failing, block all calls)
   │
   │ 60s timeout
   ▼
HALF_OPEN (test recovery, allow 1 call)
   │                     │
   │ success             │ failure
   ▼                     ▼
CLOSED                OPEN
```

#### Circuit Breaker API
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.state = State.CLOSED
        self.failure_count = 0
        self.last_failure_time = None

    def call(self, func, *args, **kwargs):
        if self.state == State.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = State.HALF_OPEN
            else:
                raise CircuitOpenError("API unavailable")

        try:
            result = func(*args, **kwargs)
            if self.state == State.HALF_OPEN:
                self.state = State.CLOSED
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = State.OPEN
                self.last_failure_time = time.time()
            raise
```

#### Usage
```python
maps_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def get_route(origin, destination):
    try:
        return maps_breaker.call(google_maps_api.directions, origin, destination)
    except CircuitOpenError:
        logger.warning("Google Maps circuit OPEN, using cached route")
        return cached_route_provider.get_route(origin, destination)
```

#### Configuration
```yaml
circuit_breaker:
  failure_threshold: 5    # Failures before OPEN
  timeout: 60             # Seconds in OPEN before HALF_OPEN
  enabled: true           # Enable/disable circuit breaker
```

### Monitoring
Log circuit state transitions:
```
2024-11-22 10:15:23 | WARNING | CircuitBreaker | OPEN | Google Maps API (5 failures)
2024-11-22 10:16:23 | INFO | CircuitBreaker | HALF_OPEN | Testing Google Maps recovery
2024-11-22 10:16:24 | INFO | CircuitBreaker | CLOSED | Google Maps recovered
```

### Related Missions
- M7.1: Route Provider (wrap Google Maps calls)
- M7.4-7.6: Agents (wrap YouTube, Spotify, Wikipedia calls)
- M7.12: Resilience tests (verify circuit breaker behavior)

### References
- Circuit Breaker Pattern: https://martinfowler.com/bliki/CircuitBreaker.html
- Hystrix (Netflix): https://github.com/Netflix/Hystrix
- resilience4j (Java): https://resilience4j.readme.io/docs/circuitbreaker

---

## ADR-011: Metrics Aggregator (Separate from Logging)

### Status
✅ **Accepted** (2024-11-22) **[NEW]**

### Context
Need to track performance metrics (API call counts, latencies, queue depth, worker utilization) for cost analysis and performance optimization. Logs are for debugging; metrics are for monitoring. Mixing them degrades both.

### Decision
**Separate metrics collection** from logging. Implement `MetricsCollector` that aggregates counters (API calls), timers (latencies), gauges (queue depth). Writes to `logs/metrics.json` (live updates). Thread-safe via `threading.Lock`.

### Alternatives Considered

#### Alternative A: Metrics in Logs
- **Pros:** Single system, simpler, no extra code
- **Cons:** Pollutes logs with metrics, hard to extract, not queryable, poor performance (string parsing)
- **Rejected:** Logs and metrics serve different purposes

#### Alternative B: Third-Party Metrics (Prometheus)
- **Pros:** Industry standard, powerful querying, dashboards
- **Cons:** Over-engineering, requires server, not file-based, adds dependency
- **Rejected:** Too complex for educational single-machine project

#### Alternative C: No Metrics
- **Pros:** Simplest, zero overhead
- **Cons:** Can't track API costs, can't measure performance, fails cost control requirement (KPI #6)
- **Rejected:** Metrics required for cost analysis and research

### Consequences

**Pros:**
- ✅ **Separation of Concerns:** Logs for debugging, metrics for monitoring
- ✅ **Performance:** JSON easier to parse than log files
- ✅ **Queryable:** `jq` queries for specific metrics
- ✅ **Live Updates:** Metrics updated in real-time (can watch during run)
- ✅ **Cost Tracking:** API call counts for cost analysis (KPI #6)
- ✅ **Research:** Latencies and queue depth for performance analysis (M8.1)

**Cons:**
- ❌ **Separate System:** Need to maintain MetricsCollector
- ❌ **Thread-Safety:** Need locking (slight overhead)
- ❌ **Not Real-Time Monitoring:** No dashboard (just file watching)

### Rationale
Separate metrics aggregator is **best practice**:
- Logs and metrics serve different audiences (devs vs ops)
- JSON metrics easier to query than log parsing
- Enables cost tracking (required for KPI #6)
- Supports research analysis (M8.1: performance studies)
- Standard pattern (Prometheus, StatsD separate from logging)

### Implementation Details

#### Metrics JSON Structure
```json
{
  "run_id": "1732278923_abc12345",
  "start_time": "2024-11-22T10:15:23Z",
  "end_time": "2024-11-22T10:18:45Z",
  "counters": {
    "api_calls_google_maps": 3,
    "api_calls_youtube": 15,
    "api_calls_spotify": 15,
    "api_calls_wikipedia": 15,
    "api_calls_llm": 5,
    "routes_processed": 1,
    "steps_processed": 5,
    "agents_executed": 15
  },
  "timers": {
    "route_fetch_ms": {"values": [450, 380, 420], "avg": 416.6},
    "agent_search_ms": {"values": [120, 110], "avg": 115.0},
    "agent_fetch_ms": {"values": [80, 90], "avg": 85.0},
    "judge_scoring_ms": {"values": [200, 210], "avg": 205.0}
  },
  "gauges": {
    "queue.depth": 0,
    "worker.active": 3
  }
}
```

#### MetricsCollector API
```python
class MetricsCollector:
    def __init__(self):
        self.lock = threading.Lock()
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = {}

    def increment(self, counter: str, value: int = 1):
        """Thread-safe counter increment"""
        with self.lock:
            self.counters[counter] += value

    def record_time(self, timer: str, duration_ms: float):
        """Thread-safe timer recording"""
        with self.lock:
            self.timers[timer].append(duration_ms)

    def set_gauge(self, gauge: str, value: float):
        """Thread-safe gauge update"""
        with self.lock:
            self.gauges[gauge] = value

    def write(self, path: str = "logs/metrics.json"):
        """Write metrics to JSON file"""
        with self.lock:
            with open(path, 'w') as f:
                json.dump({
                    "counters": dict(self.counters),
                    "timers": {k: {"values": v, "avg": statistics.mean(v)}
                               for k, v in self.timers.items()},
                    "gauges": self.gauges
                }, f, indent=2)
```

#### Usage in Components
```python
# In Route Provider
start = time.time()
route = google_maps_api.directions(origin, destination)
metrics.record_time("route_fetch_ms", (time.time() - start) * 1000)
metrics.increment("api_calls_google_maps")

# In Orchestrator
metrics.set_gauge("queue_depth_current", queue.qsize())
metrics.set_gauge("worker_count_active", executor._threads)
```

#### Querying Metrics
```bash
# Get total API calls
jq '.counters.api_calls_google_maps' logs/metrics.json

# Get average agent search latency
jq '.timers.agent_search_ms.avg' logs/metrics.json

# Get max queue depth
jq '.gauges.queue_depth_max' logs/metrics.json
```

### Cost Analysis Integration
Metrics feed directly into cost analysis (M8.2):
```python
cost_maps = metrics.counters['api_calls_google_maps'] * 0.005
cost_llm = metrics.counters['api_calls_llm'] * 0.002 * (tokens / 1000)
total_cost = cost_maps + cost_llm
```

### Related Missions
- M5: Research plan (metrics collection framework)
- M7.1-7.7: All components (metrics recording)
- M8.1: Research analysis (metrics consumption)
- M8.2: Cost analysis (API call metrics)

### References
- Metrics vs Logs: https://www.vividcortex.com/blog/logs-vs-metrics
- StatsD: https://github.com/statsd/statsd
- Prometheus Metric Types: https://prometheus.io/docs/concepts/metric_types/

---

## ADR Summary & Status

### Original ADRs (7) - From PRD
- ✅ ADR-001: Python 3.11+
- ✅ ADR-002: Threading (not AsyncIO)
- ✅ ADR-003: Google Maps + Caching
- ✅ ADR-004: Search+Fetch Separation
- ✅ ADR-005: YAML Config + CLI Overrides
- ✅ ADR-006: Structured Logging
- ✅ ADR-007: ThreadPoolExecutor

### Enhanced ADRs (5) - Architecture Review Updates
- ✅ **ADR-008:** Transaction ID Propagation (Observability++)
- ✅ **ADR-009:** File-Based Checkpoints (Debugging++)
- ✅ **ADR-010:** Circuit Breaker (Resilience++)
- ✅ **ADR-011:** Metrics Aggregator (Performance Monitoring++)
- ✅ **ADR-012:** LLM Client Abstraction (Priority, Budget Guards)

**Total: 12 ADRs** covering Language, Concurrency, APIs, Architecture, Configuration, Observability, Resilience, Performance Monitoring, and Optional LLM usage.

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-11-20 | 1.0 | Initial ADR register with 7 decisions from PRD | Kickoff Agent |
| 2024-11-22 | 1.1 | Added 4 enhanced ADRs (008-011) from senior architect review | Senior Architect (30+ years) |
| 2025-11-24 | 1.2 | Added ADR-012 (LLM priority/budget guards), synced counts/dates | Engineering |
| 2024-11-26 | 1.3 | Added ADR-013 (Agent LLM Prompts via Markdown) - M7.14 complete | Engineering |

---

**Next Steps:**
1. Update PRD Section 6a with ADR-008 through ADR-012
2. Implement ADRs in respective missions (M7.x)
3. Validate decisions during implementation
4. Update ADR status if decisions change

**Review Cycle:** After each major milestone (GATE 1-5), review ADRs for continued relevance.

---

*ADR Register maintained by Project Architecture Team*
*For questions or proposed changes, see `docs/prompt_log/001_architecture_design_session.md`*

---

## ADR-012: LLM Client Abstraction (Priority, Budget Guards)

### Status
✅ **Accepted** (2025-11-24)

### Context
Judge can optionally use LLM scoring. We need a unified, cost-aware interface with provider priority, budget/timeout/backoff guards, prompt redaction, and heuristic fallback.

### Decision
- Support providers via factory: **Claude > OpenAI > Gemini > Ollama (default `llama3.1:8b`) > Mock** when `llm_provider=auto`.
- Default **`use_llm=true`**; judge defaults to LLM scoring and falls back to heuristics on error/unavailability.
- Enforce prompt-length/tokens guard (`llm_max_tokens`, truncation) and optional budget guard; redact prompts in logs; apply timeouts/retries/backoff per provider.

### Alternatives Considered
- **Heuristics only:** Lowest cost/risk but less nuanced scoring.
- **Provider-specific code in Judge:** Tighter coupling, harder to swap/extend; rejected.

### Consequences
**Pros:**
- ✅ Unified interface with safe defaults and priority ordering
- ✅ Cost/risk mitigations (budgets, timeouts, backoff, redaction)
- ✅ Fails safe to heuristics; works offline with Mock/Ollama

**Cons:**
- ❌ Additional config surface (provider selection, budgets/timeouts)
- ❌ Extra dependency when LLMs enabled

### Related Missions
- M7.7b (LLM abstraction), M7.13 (optional advanced rerank)

### References
- `src/hw4_tourguide/tools/llm_client.py`, `config/settings.yaml` (llm section)

---

## ADR-013: Agent Intelligence via Markdown-Defined LLM Prompts

### Status
✅ **Accepted** (2024-11-26)

### Context
Agents currently generate search queries using simple heuristics (string concatenation: `f"{location_name} {search_hint}"`). This approach has limitations:
- **No semantic understanding**: Can't distinguish landmark types, infer context, or optimize for platform algorithms
- **Hard-coded logic**: Query generation rules embedded in agent code, difficult to iterate
- **Limited adaptability**: Can't leverage location-specific knowledge (e.g., "Nashville" → country music, "MIT" → university tour)
- **No reasoning traces**: Unclear why specific queries were chosen

We want to add LLM-powered intelligence for query generation while:
- Maintaining cost control (budget, timeout, prompt limits)
- Preserving fallback to heuristics (offline operation, LLM failures)
- Enabling rapid iteration via markdown prompts (no code changes)
- Following industry best practices (CrewAI, LangGraph pattern)

### Decision
Implement **markdown-defined agent prompts** with LLM-powered query generation:

#### Architecture
1. **Prompt Templates** (`.claude/agents/*.md`):
   - Separate markdown files per agent type (video, song, knowledge, judge)
   - Role-Mission-Context-Skills-Process-Constraints structure
   - Template variables for runtime substitution: `{location_name}`, `{search_hint}`, `{route_context}`, etc.
   - Concrete examples (3-5 per prompt) showing input→output patterns
   - Output format enforcement: JSON only, no markdown code blocks

2. **PromptLoader Utility** (`tools/prompt_loader.py`):
   - `load_agent_prompt(agent_type)`: Load raw markdown template
   - `load_prompt_with_context(agent_type, context)`: Load + substitute variables
   - Flatten nested dicts (`coordinates.lat` → `coordinates_lat`)
   - Handle missing optional variables gracefully (replace with empty string)

3. **Agent Integration** (`base_agent.py`):
   ```python
   def _build_queries(self, task: Dict) -> List[str]:
       if self.llm_client and self.config.get("use_llm_for_queries"):
           try:
               return self._build_queries_with_llm(task)
           except Exception as exc:
               self.logger.warning(f"LLM failed: {exc}, fallback to heuristic")
               self._metrics.increment_counter("llm_fallback.query_generation")
       return self._build_queries_heuristic(task)  # Existing logic
   ```

4. **Configuration Controls** (`config/settings.yaml`):
   ```yaml
   agents:
     use_llm_for_queries: true          # Enable LLM query generation
     llm_fallback: true                  # Fallback to heuristics on failure
     llm_query_timeout: 10.0             # Max seconds for LLM call
     llm_max_prompt_chars: 4000          # Truncate prompts for cost control
   ```

### Alternatives Considered

#### Alternative A: Hardcoded LLM prompts in agent code
**Approach:** Embed prompts as Python strings in agent classes
- **Pros:** Simple, no external files, faster to implement initially
- **Cons:** Prompts scattered across codebase, hard to iterate/review, not version-controlled separately, mixing concerns (code + prompts)
- **Rejected:** Poor separation of concerns; prompts should be declarative artifacts

#### Alternative B: Fine-tuned models for each agent
**Approach:** Train/fine-tune separate models for video/song/knowledge query generation
- **Pros:** Potentially better performance, no prompt engineering, faster inference
- **Cons:** High upfront cost (training data, compute), inflexible (retraining for changes), vendor lock-in, overkill for this use case
- **Rejected:** Over-engineering; prompt-based approach more maintainable and cost-effective

#### Alternative C: Keep heuristics only (no LLM)
**Approach:** Improve heuristic query generation with better rules/keywords
- **Pros:** Zero API cost, instant response, works offline, deterministic
- **Cons:** Limited by hard-coded rules, can't understand semantic context, brittle (many edge cases), requires manual tuning for each location type
- **Rejected:** Doesn't unlock intelligence benefits; LLM optional with fallback mitigates downsides

#### Alternative D: Hybrid: Templates + LLM fill-in-the-blank
**Approach:** Define query templates (e.g., "{location} {content_type} {year}"), use LLM only to fill placeholders
- **Pros:** Reduces LLM workload (cheaper/faster), more structured output
- **Cons:** Still requires prompt engineering, limits LLM creativity, templates need maintenance
- **Rejected:** Doesn't significantly reduce complexity vs. full LLM approach

### Consequences

**Pros:**
- ✅ **Separation of concerns**: Prompts are declarative, version-controlled markdown files
- ✅ **Rapid iteration**: Edit prompts without touching code, hot-swappable
- ✅ **Semantic intelligence**: LLM understands location types, music-geography connections, authority sources
- ✅ **Cost awareness**: Timeout (10s), prompt limits (4K chars), configurable disable
- ✅ **Fallback safety**: Graceful degradation to heuristics on LLM failures
- ✅ **Observable**: Log LLM reasoning, track fallback rates via metrics
- ✅ **Industry standard**: Follows CrewAI/LangGraph/AutoGen pattern
- ✅ **Testable**: Mock LLM responses easily, test heuristic fallbacks independently

**Cons:**
- ❌ **Additional complexity**: New abstraction layer (PromptLoader), more files to maintain
- ❌ **Cost**: ~$0.0004 per location (Claude Haiku) → $0.004 per 10-step route (manageable)
- ❌ **Latency**: 1-3 seconds per query generation (vs. <10ms heuristics)
- ❌ **Dependency on external services**: LLM unavailability requires fallback
- ❌ **Prompt engineering**: Requires skill to write effective prompts with examples

### Rationale
Markdown-defined LLM prompts strike optimal balance:
- **Cost-effective**: ~$0.004 per route negligible for quality gain
- **Flexible**: Iterate prompts without code changes (edit .md files, commit, deploy)
- **Safe**: Fallback to heuristics ensures system always works
- **Maintainable**: Prompts reviewed/versioned separately from code
- **Extensible**: Adding new agent types requires only markdown file + config

Pattern proven by:
- **CrewAI**: Markdown task definitions with LLM execution
- **LangGraph**: Prompt templates as configuration
- **AutoGen**: Agent roles defined via system messages

### Cost Analysis

**Typical query generation**:
- Prompt size: ~3,500 tokens (after variable substitution)
- Response size: ~100 tokens (JSON with 3 queries + reasoning)
- Total: ~3,600 tokens per location

**Pricing** (per location, 3 agents):
- **Claude Haiku**: $0.00025/1K input + $0.00125/1K output = ~$0.0012 per agent → **$0.0036 per location**
- **GPT-3.5-turbo**: $0.0005/1K input + $0.0015/1K output = ~$0.0020 per agent → **$0.0060 per location**
- **Ollama (local)**: $0.00 per location (self-hosted, hardware cost amortized)

**10-step route cost**:
- Claude Haiku: **$0.036** (< 4 cents)
- GPT-3.5: **$0.060** (6 cents)
- Ollama: **$0.00**

**Cost mitigation strategies**:
- Default: LLM disabled (`use_llm_for_queries: false`)
- Timeout: 10 seconds (prevents runaway costs)
- Prompt limit: 4,000 chars (truncate before sending)
- Batch optimization (future): Single LLM call for all 3 agents (3× cost reduction)
- Caching (future): Cache prompts for repeated location types

### Implementation Phases

**Phase 1: M7.14 - Agent Prompt Infrastructure** (✅ Complete)
- Create `.claude/agents/*.md` prompt files (video, song, knowledge, judge)
- Implement `PromptLoader` utility
- Write comprehensive tests
- Document in ADR-013

**Phase 2: M7.15 - LLM Query Generation Integration** (🔜 Next)
- Modify `BaseAgent._build_queries()` to try LLM first
- Add `_build_queries_with_llm()` method
- Update config with LLM control flags
- Add integration tests with mocked LLM

**Phase 3: M7.16 - Enhanced Judge Prompt** (🔜 After M7.15)
- Replace hardcoded judge LLM prompt with markdown template
- Preserve existing fallback behavior
- Add test for markdown template loading

### Related Missions
- **M7.14**: Agent Prompt Infrastructure (foundation)
- **M7.15**: LLM-Based Query Generation for Agents (integration)
- **M7.16**: Enhanced Judge Prompt with Markdown Template
- **M8.5**: LLM Agent Architecture Documentation

### References
- `.claude/agents/README.md` - Comprehensive prompt system documentation
- `src/hw4_tourguide/tools/prompt_loader.py` - Implementation
- `tests/test_prompt_loader.py` - Test coverage
- CrewAI documentation: https://docs.crewai.com/
- LangGraph prompt patterns: https://langchain-ai.github.io/langgraph/
