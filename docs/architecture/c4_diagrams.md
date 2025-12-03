# C4 Architecture Diagrams - Route Enrichment Tour-Guide System

**Document Version:** 1.1
**Date:** 2025-11-24
**Architecture Status:** Core Implementation Complete (cached demo, metrics, validation, LLM priority)
**Architect:** Senior Systems Architect (30+ years experience in full-stack + agent systems)

---

## Introduction

This document presents the Route Enrichment Tour-Guide System architecture using the C4 model (Context, Container, Component, Code) created by Simon Brown. The C4 model provides a hierarchical set of software architecture diagrams for different audiences.

**C4 Model Levels:**
1. **Level 1 - System Context:** How the system fits in the world (users, external systems)
2. **Level 2 - Container:** High-level technology choices (applications, data stores)
3. **Level 3 - Component:** Components within containers and their interactions
4. **Level 4 - Deployment:** Infrastructure, networking, deployment

**Reference:** https://c4model.com/

---

## Level 1: System Context Diagram

### Purpose
Shows how the Route Enrichment Tour-Guide System fits into the world, focusing on people and systems that interact with it.

### Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         System Context                                   │
└─────────────────────────────────────────────────────────────────────────┘

     [Moshe Buzaglos]                    [Danit Griner]
      Bored Commuter                    Tour Strategist
            │                                  │
            │ Provides                         │ Exports
            │ route details                    │ tour plans
            ├──────────────┐        ┌──────────┤
            │              │        │          │
            ▼              ▼        ▼          ▼
    ┌────────────────────────────────────────────────┐
    │                                                 │
    │     Route Enrichment Tour-Guide System         │
    │                                                 │
    │  "Multi-agent orchestration platform that      │
    │   enriches driving routes with curated         │
    │   video, music, and knowledge content"         │
    │                                                 │
    │  [Python 3.10+ Application]                    │
    │                                                 │
    └────────────────────────────────────────────────┘
              │         │         │         │
              │         │         │         │
        Calls │   Calls │   Calls │   Calls │
              │         │         │         │
              ▼         ▼         ▼         ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ Google   │ │ YouTube  │ │ Spotify  │ │Wikipedia │
    │ Maps API │ │ Data API │ │ Web API  │ │   API    │
    │          │ │          │ │          │ │          │
    │[External]│ │[External]│ │[External]│ │[External]│
    └──────────┘ └──────────┘ └──────────┘ └──────────┘

    Optional:
              │
        Calls │
              ▼
    ┌──────────────┐
    │ OpenAI /     │
    │ Anthropic    │
    │ LLM API      │
    │ [External]   │
    └──────────────┘
```

### Key Relationships

| From | To | Relationship | Protocol |
|------|----|--------------| ---------|
| Moshe Buzaglos (Commuter) | Tour-Guide System | Provides route (from/to locations) | CLI arguments |
| Danit Griner (Tour Strategist) | Tour-Guide System | Exports enriched tour plans | File export (JSON/MD/CSV) |
| Tour-Guide System | Google Maps API | Fetches route directions (Directions & Geocoding) | HTTPS/REST |
| Tour-Guide System | YouTube Data API | Searches video content | HTTPS/REST |
| Tour-Guide System | Spotify Web API | Searches music tracks | HTTPS/REST |
| Tour-Guide System | Wikipedia/DuckDuckGo | Fetches knowledge articles | HTTPS/REST |
| Tour-Guide System | OpenAI/Gemini/Anthropic | Core Intelligence (Query Gen & Scoring) | HTTPS/REST |

### External Systems

1. **Google Maps Platform**
   - **Directions API:** Fetch route steps
   - **Geocoding API:** Reverse geocode coordinates for addresses
   - Authentication: API key
   - Rate Limit: 2,500 requests/month (free tier)

2. **YouTube Data API v3**
   - Purpose: Search for relevant videos per location
   - Authentication: API key
   - Rate Limit: 10,000 quota units/day

3. **Spotify Web API**
   - Purpose: Search for relevant music per location
   - Authentication: Client ID + Secret

4. **Knowledge Sources**
   - **Wikipedia API:** Fetch authoritative articles
   - **DuckDuckGo API:** Secondary search for broader topics
   - Authentication: None required

5. **LLM Providers** (OpenAI, Anthropic, Google Gemini)
   - Purpose: Agent query generation and Judge scoring
   - Authentication: API keys
   - Fallback: Heuristics (if keys missing or quota exceeded)

---

## Level 2: Container Diagram

### Purpose
Shows the high-level shape of the software architecture and how responsibilities are distributed across containers (applications, data stores).

### Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│           Route Enrichment Tour-Guide System [Container View]           │
└─────────────────────────────────────────────────────────────────────────┘

    [User]
      │
      │ python -m hw4_tourguide --from X --to Y
      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CLI Application                                                         │
│  [Python 3.10+ Package: hw4_tourguide]                                  │
│                                                                          │
│  Entry Point: src/hw4_tourguide/__main__.py                            │
│  Role: Parse arguments, load config, orchestrate pipeline               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │  Core Pipeline Components                                   │        │
│  │                                                              │        │
│  │  [Route Provider] → [Scheduler] → [Orchestrator]           │        │
│  │        ↓                              ↓                     │        │
│  │  [Config Loader]         [Agent Registry + 3 Agents]       │        │
│  │        ↓                              ↓                     │        │
│  │  [Logger Setup]                  [Judge Agent]             │        │
│  │                                       ↓                     │        │
│  │                              [Output Writer]               │        │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
      │              │                │              │
      │ Reads        │ Writes         │ Writes       │ Calls
      ▼              ▼                ▼              ▼
┌─────────┐   ┌───────────┐   ┌──────────┐   ┌────────────┐
│ Config  │   │   Logs    │   │  Output  │   │  External  │
│  Files  │   │           │   │  Files   │   │    APIs    │
│         │   │           │   │          │   │            │
│[YAML/   │   │[Rotating  │   │[JSON/MD/ │   │[Google/    │
│ .env]   │   │ Logs]     │   │ CSV]     │   │ YouTube/   │
│         │   │           │   │          │   │ Spotify/   │
│         │   │           │   │          │   │ Wikipedia/ │
│         │   │           │   │          │   │ LLM]       │
└─────────┘   └───────────┘   └──────────┘   └────────────┘
  config/        logs/          output/        HTTPS/REST
                                checkpoints/
```

### Containers Detailed

#### 1. CLI Application Container
- **Technology:** Python 3.10+ (single process, multi-threaded)
- **Responsibilities:**
  - Parse command-line arguments
  - Load configuration (YAML + .env)
  - Initialize logging infrastructure
  - Orchestrate pipeline execution (Route → Schedule → Process → Judge → Output)
  - Handle graceful shutdown (Ctrl+C)
- **Deployment:** Single executable Python package
- **Entry Point:** `python -m hw4_tourguide`

#### 2. Configuration Files Container
- **Technology:** YAML + .env files
- **Location:** `config/settings.yaml`, `.env`
- **Contents:**
  - `settings.yaml`: 20+ parameters (scheduler interval, agent limits, retry counts)
  - `.env`: API keys and secrets (never committed to Git)
- **Access Pattern:** Read once at startup, cached in memory

#### 3. Logs Container
- **Technology:** Rotating file logs
- **Location:** `logs/system.log`, `logs/metrics.json`, `logs/errors.log`
- **Format:** Structured logs: `TIMESTAMP | LEVEL | MODULE | EVENT_TAG | MESSAGE`
- **Rotation:** 10MB per file, 5 backups
- **Access Pattern:** Async writes from all components

#### 4. Output Files Container
- **Technology:** JSON, Markdown, CSV files
- **Location:** `output/final_route.json`, `output/summary.md`, `output/tour_export.csv`
- **Checkpoints:** `output/checkpoints/{TID}/00_route.json` through `05_final_output.json`
- **Access Pattern:** Sequential writes at each pipeline stage

#### 5. External APIs Container
- **Technology:** HTTPS/REST APIs (3rd-party services)
- **APIs:** Google Maps, YouTube, Spotify, Wikipedia, LLM (optional)
- **Access Pattern:** HTTP client with retry logic, circuit breakers, connection pooling
- **Error Handling:** Exponential backoff, fallback to cached/mock data

---

## Level 3: Component Diagram

### Purpose
Decompose the CLI Application container into components, showing their responsibilities and interactions.

### Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLI Application [Component View]                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Initialization Layer                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [CLI Parser]  →  [Config Loader]  →  [Logger Setup]                   │
│   (argparse)       (YAML + .env)        (structured)                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            │ Configured components
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Pipeline Orchestration Layer                                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [Route Provider]                                                        │
│  ├─ GoogleMapsProvider (live mode)                                      │
│  └─ CachedRouteProvider (cached mode)                                   │
│       │                                                                  │
│       │ route.json (with TID)                                           │
│       ▼                                                                  │
│  [Scheduler Thread]                                                      │
│  ├─ Emits tasks at configured interval                                  │
│  ├─ Writes to queue.Queue (thread-safe)                                 │
│  └─ Logs: "Scheduler | EMIT | Step X/Y | TID: xxx"                     │
│       │                                                                  │
│       │ Tasks to queue                                                   │
│       ▼                                                                  │
│  [Orchestrator + ThreadPoolExecutor]                                     │
│  ├─ Consumes tasks from queue                                           │
│  ├─ Spawns worker threads (default: 5)                                  │
│  ├─ Coordinates agents per location                                     │
│  └─ Aggregates results → judge → output                                 │
│       │                                                                  │
│       │ Worker dispatch                                                  │
│       ▼                                                                  │
│  ┌───────────────────────────────────────────────┐                      │
│  │  Worker Thread (per location step)            │                      │
│  │                                                │                      │
│  │  [Agent Registry]                             │                      │
│  │  ├─ get_agent('video')   → [Video Agent]     │                      │
│  │  ├─ get_agent('song')    → [Song Agent]      │                      │
│  │  └─ get_agent('knowledge')→ [Knowledge Agent]│                      │
│  │       │           │              │            │                      │
│  │       │           │              │            │                      │
│  │       └──────┬────┴───────┬──────┘            │                      │
│  │              │            │                   │                      │
│  │              │ All 3 agent results           │                      │
│  │              ▼                                 │                      │
│  │         [Judge Agent]                         │                      │
│  │         ├─ Heuristic Scorer                   │                      │
│  │         ├─ Optional: LLM Scorer               │                      │
│  │         └─ Returns: scores + rationale        │                      │
│  │              │                                 │                      │
│  │              ▼                                 │                      │
│  │         Aggregated Result                     │                      │
│  └───────────────────────────────────────────────┘                      │
│       │                                                                  │
│       │ All steps processed                                             │
│       ▼                                                                  │
│  [Output Writer]                                                         │
│  ├─ JSONWriter → final_route.json                                       │
│  ├─ MarkdownWriter → summary.md                                         │
│  └─ CSVWriter → tour_export.csv                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Cross-Cutting Concerns                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [Transaction ID (TID) Propagation] (ADR-008)                           │
│  └─ Every component receives + logs TID for distributed tracing         │
│                                                                          │
│  [File-Based Checkpoints] (ADR-009)                                     │
│  └─ Each stage writes to output/checkpoints/{TID}/ for replay           │
│                                                                          │
│  [Circuit Breaker for APIs] (ADR-010)                                   │
│  └─ Wraps all external API calls (3-state: CLOSED/OPEN/HALF_OPEN)      │
│                                                                          │
│  [Metrics Collector] (ADR-011)                                          │
│  └─ Aggregates counters (API calls), timers (latencies), gauges (queue) │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### Initialization Layer

1. **CLI Parser** (`src/hw4_tourguide/__main__.py`)
   - Parse command-line arguments (--from, --to, --mode, --config, --log-level, --output)
   - Validate required arguments (origin, destination)
   - Display help text and version
   - Return: `argparse.Namespace` with parsed arguments

2. **Config Loader** (`src/hw4_tourguide/config_loader.py`)
   - Load `config/settings.yaml` (20+ parameters)
   - Load `.env` secrets (API keys)
   - Merge CLI flags (highest priority)
   - Validate required keys, set defaults
   - Return: `Config` object (immutable dataclass)

3. **Logger Setup** (`src/hw4_tourguide/logger.py`)
   - Initialize structured logging (format: `TIMESTAMP | LEVEL | MODULE | TAG | MESSAGE`)
   - Configure rotation (10MB × 5 backups)
   - Set log level from config
   - Create separate error log stream
   - Return: Configured `logging.Logger` instance

#### Pipeline Orchestration Layer

4. **Validator** (`src/hw4_tourguide/validators.py`)
   - Validates schema of agent results and judge decisions
   - Drops malformed data to prevent pipeline crashes

#### Pipeline Orchestration Layer

5. **Route Provider** (`src/hw4_tourguide/route_provider.py`)
   - **Interface:** `RouteProvider(ABC)` with `get_route(origin, destination) -> Route`
   - **GoogleMapsProvider:** Calls Directions API + Geocoding API per step
   - **CachedRouteProvider:** Reads from `data/routes/{hash}.json`

6. **Scheduler Thread** (`src/hw4_tourguide/scheduler.py`)
   - Runs as daemon thread (`threading.Thread`)
   - Emits route steps to `queue.Queue`

7. **Orchestrator** (`src/hw4_tourguide/orchestrator.py`)
   - Consumes tasks, spawns workers via `ThreadPoolExecutor`
   - Coordinates Agent Factory, Agents, and Judge

#### Agent Layer

8. **Agent Factory** (`_build_agents` in `__main__`)
   - Instantiates agents with injected clients (Live vs Stub) based on config
   - Registers Video, Song, Knowledge agents

9. **PromptLoader** (`src/hw4_tourguide/tools/prompt_loader.py`)
   - Loads markdown prompt templates from `.claude/agents/`
   - Substitutes context variables for LLM calls

10. **Search/Fetch Tools** (`src/hw4_tourguide/tools/search.py`, `src/hw4_tourguide/tools/fetch.py`)
    - Shared wrappers for provider clients

11. **LLM Client Abstraction** (`src/hw4_tourguide/tools/llm_client.py`)
    - Factory for Claude/OpenAI/Gemini/Ollama
    - Enforces budgets and timeouts

12. **Video Agent** (`src/hw4_tourguide/agents/video_agent.py`)
    - Uses `PromptLoader` for query gen (if LLM enabled) or heuristics
    - Search -> Fetch -> Checkpoint

13. **Song Agent** (`src/hw4_tourguide/agents/song_agent.py`)
    - Spotify (Primary) + YouTube (Secondary)

14. **Knowledge Agent** (`src/hw4_tourguide/agents/knowledge_agent.py`)
    - Wikipedia (Primary) + DuckDuckGo (Secondary)

15. **Judge Agent** (`src/hw4_tourguide/judge.py`)
    - **LLM Scoring (Primary):** Uses `judge_agent.md` prompt to score and select content
    - **Heuristic Scoring (Fallback):** Presence/Quality/Relevance logic if LLM fails
    - **Output:** `JudgeDecision` with rationale

12. **Output Writer** (`src/hw4_tourguide/output_writer.py`)
    - **JSONWriter:** Serialize to `output/final_route.json` (schema-compliant)
    - **MarkdownWriter:** Generate `output/summary.md` (human-readable report)
    - **CSVWriter:** Export to `output/tour_export.csv` (columns: location, video, song, knowledge, score)
    - **Checkpoint:** Write `final_output.json`

#### Cross-Cutting Components

13. **Validation & Determinism**
    - Warn-level schema validation; malformed agent results dropped before judge
    - Output writer sorts steps by `step_number` for deterministic JSON/MD/CSV
14. **Transaction ID (TID) Service** (implemented in `src/hw4_tourguide/route_provider.py`)
    - Generate unique TID at route fetch: `f"{timestamp}_{uuid4().hex[:8]}"`
    - Propagate through all components via task dictionaries
    - Log in every message for distributed tracing

14. **File Checkpoint Manager** (`src/hw4_tourguide/file_interface.py`)
    - Create checkpoint directory: `output/checkpoints/{TID}/`
    - Write JSON files at each stage (00-05)
    - Read checkpoints for replay/debugging
    - Pruning: Auto-delete checkpoints >7 days old

15. **Circuit Breaker** (`src/hw4_tourguide/tools/circuit_breaker.py`)
    - 3 states: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
    - Failure threshold: 5 consecutive failures → OPEN
    - Timeout: 60s in OPEN state → HALF_OPEN
    - Success in HALF_OPEN → CLOSED
    - Wraps all external API calls

16. **Metrics Collector** (`src/hw4_tourguide/tools/metrics_collector.py`)
    - Counters: API call counts (per API), total requests
    - Timers: Latencies (API calls, agent execution, judge scoring)
    - Gauges: Queue depth, active workers, memory usage
    - Writes to `logs/metrics.json` (live updates)
    - Thread-safe (protected by `threading.Lock`)

---

## Level 4: Deployment Diagram

### Purpose
Shows infrastructure, networking, and deployment topology.

### Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Deployment Environment: MacBook Pro                   │
│                    OS: macOS 14+ (Darwin)                                │
│                    Runtime: Python 3.10+ (.venv)                         │
└─────────────────────────────────────────────────────────────────────────┘

                           ┌─────────────────┐
                           │   User Shell    │
                           │   (Terminal)    │
                           └────────┬────────┘
                                    │
                                    │ python -m hw4_tourguide
                                    ▼
            ┌───────────────────────────────────────────────┐
            │  Python 3.10+ Virtual Environment (.venv)     │
            │                                                │
            │  ┌──────────────────────────────────────┐    │
            │  │  hw4_tourguide Process               │    │
            │  │  (Single Process, Multi-Threaded)    │    │
            │  │                                        │    │
            │  │  Main Thread                          │    │
            │  │  ├─ CLI Parsing                       │    │
            │  │  ├─ Config Loading                    │    │
            │  │  ├─ Logger Setup                      │    │
            │  │  └─ Orchestrator (queue consumer)     │    │
            │  │                                        │    │
            │  │  Scheduler Thread (daemon)            │    │
            │  │  └─ Emits tasks at 2.0s intervals     │    │
            │  │                                        │    │
            │  │  ThreadPoolExecutor (5 workers)       │    │
            │  │  ├─ Worker 1 (Agent processing)       │    │
            │  │  ├─ Worker 2 (Agent processing)       │    │
            │  │  ├─ Worker 3 (Agent processing)       │    │
            │  │  ├─ Worker 4 (Standby)                │    │
            │  │  └─ Worker 5 (Standby)                │    │
            │  │                                        │    │
            │  └────────────┬──────────────────────────┘    │
            │               │                                │
            └───────────────┼────────────────────────────────┘
                            │
                            │ File I/O
                            ▼
    ┌───────────────────────────────────────────────────────────┐
    │  Local Filesystem                                          │
    │                                                            │
    │  LLM_Agent_Orchestration_HW4/                             │
    │  ├── config/                                              │
    │  │   ├── settings.yaml         [R] Config params          │
    │  │   └── .env                  [R] API keys (git-ignored) │
    │  │                                                         │
    │  ├── data/routes/                                         │
    │  │   └── *.json                [R] Cached routes          │
    │  │                                                         │
    │  ├── logs/                                                │
    │  │   ├── system.log            [W] Structured logs        │
    │  │   ├── metrics.json          [W] Performance metrics    │
    │  │   └── errors.log            [W] Error-only stream      │
    │  │                                                         │
    │  └── output/                                              │
    │      ├── checkpoints/{TID}/                               │
    │      │   ├── 00_route.json     [W] Route checkpoint       │
    │      │   ├── 01_scheduler.json [W] Scheduler checkpoint   │
    │      │   ├── 02_agent_*.json   [W] Agent search results   │
    │      │   ├── 03_agent_*.json   [W] Agent fetch results    │
    │      │   ├── 04_judge.json     [W] Judge decision         │
    │      │   └── 05_final.json     [W] Final aggregation      │
    │      │                                                     │
    │      ├── final_route.json      [W] Primary output         │
    │      ├── summary.md            [W] Human report           │
    │      └── tour_export.csv       [W] Spreadsheet export     │
    │                                                            │
    └────────────────────────────────────────────────────────────┘

                            │
                            │ HTTPS/REST
                            ▼
    ┌───────────────────────────────────────────────────────────┐
    │  External APIs (Internet)                                  │
    │                                                            │
    │  ┌─────────────────┐  ┌─────────────────┐               │
    │  │ Google Maps API │  │ YouTube API     │               │
    │  │ maps.google.com │  │ youtube.com/api │               │
    │  │ HTTPS, Port 443 │  │ HTTPS, Port 443 │               │
    │  └─────────────────┘  └─────────────────┘               │
    │                                                            │
    │  ┌─────────────────┐  ┌─────────────────┐               │
    │  │ Spotify API     │  │ Wikipedia API   │               │
    │  │ spotify.com/api │  │ wikipedia.org   │               │
    │  │ HTTPS, Port 443 │  │ HTTPS, Port 443 │               │
    │  └─────────────────┘  └─────────────────┘               │
    │                                                            │
    │  Optional:                                                 │
    │  ┌─────────────────────────────────────┐                 │
    │  │ OpenAI / Anthropic LLM API          │                 │
    │  │ api.openai.com / api.anthropic.com  │                 │
    │  │ HTTPS, Port 443                     │                 │
    │  └─────────────────────────────────────┘                 │
    │                                                            │
    └────────────────────────────────────────────────────────────┘
```

### Deployment Specifications

#### Hardware Requirements
- **CPU:** Multi-core (4+ cores recommended for thread pool)
- **RAM:** 512MB minimum, 1GB recommended
- **Disk:** 100MB for package + 500MB for logs/outputs
- **Network:** Internet connection (for live mode)

#### Software Requirements
- **OS:** macOS 14+, Linux (Ubuntu 20.04+), Windows 10+ (with WSL)
- **Python:** 3.10 or higher
- **Dependencies:** See `pyproject.toml` (requests, pyyaml, python-dotenv)

#### Network Configuration
- **Outbound HTTPS:** Port 443 (for all external APIs)
- **Firewall:** Allow outbound HTTPS to:
  - `maps.googleapis.com`
  - `www.googleapis.com` (YouTube)
  - `api.spotify.com`
  - `en.wikipedia.org`
  - `api.openai.com` (optional)
  - `api.anthropic.com` (optional)

#### File Permissions
- **config/.env:** 0600 (owner read/write only)
- **config/settings.yaml:** 0644 (owner write, all read)
- **logs/:** 0755 (owner write, all read/execute)
- **output/:** 0755 (owner write, all read/execute)

#### Process Management
- **Single Process:** One Python interpreter instance
- **Graceful Shutdown:** Ctrl+C → SIGINT → save partial results
- **Exit Codes:**
  - 0: Success
  - 1: Configuration error
  - 2: API error
  - 3: No results generated

---

## Sequence Diagrams for Critical Flows

### Flow 1: End-to-End Route Enrichment (Happy Path)

```
User       CLI     Config  Route   Sched   Queue  Orch    Agent   Judge   Output
 │          │        │       │       │       │      │       │       │       │
 │ run CLI  │        │       │       │       │      │       │       │       │
 ├─────────>│        │       │       │       │      │       │       │       │
 │          │ load   │       │       │       │      │       │       │       │
 │          ├───────>│       │       │       │      │       │       │       │
 │          │<───────┤       │       │       │      │       │       │       │
 │          │ Config │       │       │       │      │       │       │       │
 │          │        │       │       │       │      │       │       │       │
 │          │   get route   │       │       │      │       │       │       │
 │          ├───────────────>│       │       │      │       │       │       │
 │          │                │ [API] │       │      │       │       │       │
 │          │<───────────────┤       │       │      │       │       │       │
 │          │ Route (w/ TID) │       │       │      │       │       │       │
 │          │                │       │       │      │       │       │       │
 │          │  start scheduler       │       │      │       │       │       │
 │          ├───────────────────────>│       │      │       │       │       │
 │          │                │       │ emit  │      │       │       │       │
 │          │                │       ├──────>│      │       │       │       │
 │          │                │       │  Task1│      │       │       │       │
 │          │                │       │       │      │       │       │       │
 │          │  start orchestrator    │       │      │       │       │       │
 │          ├───────────────────────────────────────>│       │       │       │
 │          │                │       │       │ pop  │       │       │       │
 │          │                │       │       │<─────┤       │       │       │
 │          │                │       │       │Task1 │       │       │       │
 │          │                │       │       │      │ spawn │       │       │
 │          │                │       │       │      │ worker│       │       │
 │          │                │       │       │      ├──────>│       │       │
 │          │                │       │       │      │ search│       │       │
 │          │                │       │       │      │  +    │       │       │
 │          │                │       │       │      │ fetch │       │       │
 │          │                │       │       │      │<──────┤       │       │
 │          │                │       │       │      │results│       │       │
 │          │                │       │       │      │       │       │       │
 │          │                │       │       │      │  judge│       │       │
 │          │                │       │       │      ├──────────────>│       │
 │          │                │       │       │      │       │ score │       │
 │          │                │       │       │      │<──────────────┤       │
 │          │                │       │       │      │   decision    │       │
 │          │                │       │       │      │               │       │
 │          │                │       │   ... more steps ...         │       │
 │          │                │       │       │      │               │       │
 │          │                │       │       │  all done            │       │
 │          │                │       │       │<─────┤               │       │
 │          │                │       │       │      │  write output │       │
 │          │<──────────────────────────────────────────────────────────────>│
 │          │                │       │       │      │               │  JSON │
 │          │                │       │       │      │               │   MD  │
 │          │                │       │       │      │               │  CSV  │
 │<─────────┤                │       │       │      │               │       │
 │ Files    │                │       │       │      │               │       │
 │ created  │                │       │       │      │               │       │
```

### Flow 2: Circuit Breaker Activation (Error Handling)

```
Agent   CircuitBreaker   ExternalAPI
  │           │              │
  │ call API  │              │
  ├──────────>│              │
  │           │  HTTP GET    │
  │           ├─────────────>│
  │           │              │ [TIMEOUT]
  │           │              X
  │           │<─────────────┤
  │           │  Error #1    │
  │<──────────┤              │
  │  Retry    │              │
  ├──────────>│              │
  │           ├─────────────>│
  │           │              │ [ERROR 500]
  │           │<─────────────┤
  │           │  Error #2    │
  │<──────────┤              │
  │  ... (3 more failures) ...│
  │           │  Error #5    │
  │           │              │
  │           │ [OPEN STATE] │
  │           │  No API calls│
  │           │  for 60s     │
  │<──────────┤              │
  │  Fallback │              │
  │  (cached) │              │
  │           │              │
  │  ... 60s later ...       │
  │           │              │
  │ call API  │[HALF_OPEN]   │
  ├──────────>│ Test call    │
  │           ├─────────────>│
  │           │              │ [200 OK]
  │           │<─────────────┤
  │           │ [CLOSED]     │
  │           │ Resume normal│
  │<──────────┤              │
```

---

## Architecture Quality Attributes

### Modularity
- **Score: 9/10**
- Each component has single responsibility
- Clear boundaries via interfaces (RouteProvider, Agent, Judge)
- Independent testing possible for all modules

### Observability
- **Score: 10/10**
- Transaction ID propagation for distributed tracing
- Structured logging at every step
- File checkpoints at each pipeline stage
- Metrics collection (API calls, latencies, queue depth)

### Testability
- **Score: 9/10**
- Dependency injection for all external dependencies
- Mock interfaces for APIs, file I/O, queue
- Checkpoints enable verification of intermediate state
- Integration tests use cached data (no external calls)

### Resilience
- **Score: 8/10**
- Circuit breakers for external APIs
- Retry logic with exponential backoff
- Graceful degradation (agent failures don't cascade)
- Partial results saved on Ctrl+C

### Performance
- **Score: 7/10**
- I/O-bound agents benefit from threading
- Connection pooling for HTTP clients
- Lazy loading (don't fetch until needed)
- Trade-off: File I/O checkpoints add overhead (optional via config)

### Scalability
- **Score: 6/10**
- Single-machine deployment (not distributed)
- Thread pool sizing limits concurrency
- File-based state (not database)
- Good enough for educational project + single-user tool

### Security
- **Score: 8/10**
- Secrets in `.env` (never committed)
- Logs redact API keys
- HTTPS for all external calls
- File permissions (0600 for .env)

---

## Implementation Notes

### Dependencies Between Components
1. **Config Loader** → All components (dependency injection)
2. **Logger Setup** → All components (logging)
3. **Route Provider** → Scheduler (route input)
4. **Scheduler** → Orchestrator (task queue)
5. **Orchestrator** → Agent Registry, Judge, Output Writer
6. **Agent Registry** → Individual Agents (factory pattern)
7. **Agents** → External APIs (circuit breaker wrapper)
8. **Judge** → Agents (scoring input)
9. **Output Writer** → Judge results (final export)

### File-Based Contracts (ADR-009)
All components write JSON files following schemas in `docs/contracts/`:
- `route_schema.json`
- `task_schema.json`
- `agent_result_schema.json`
- `judge_decision_schema.json`
- `final_output_schema.json`

### Thread Safety Checklist
- ✅ `queue.Queue` (thread-safe by design)
- ✅ `Metrics Collector` (protected by `threading.Lock`)
- ✅ `Immutable Task objects` (no shared mutable state)
- ✅ `Logger` (thread-safe in Python standard library)
- ✅ `Circuit Breaker` (atomic state transitions)

---

## Related Documents

- **ADR Register:** `docs/architecture/adr_register.md` (11 ADRs total: original 7 + new 4)
- **Prompt Log:** `docs/prompt_log/001_architecture_design_session.md` (design rationale)
- **JSON Schemas:** `docs/contracts/*.json` (data contracts)
- **PRD:** `PRD_Route_Enrichment_Tour_Guide_System.md` (requirements, original ADRs)

---

**Architecture Status:** ✅ **Production-Ready Design Complete**
**Next Phase:** Implementation (M3-M7) - Build components following this architecture
**Design Review Date:** 2024-11-22
**Architect:** Senior Systems Architect (30+ years experience)
