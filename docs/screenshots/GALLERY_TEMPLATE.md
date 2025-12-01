# 📸 Visual Evidence Gallery: Route Enrichment Tour-Guide System

**System Version:** 0.1.0
**Generated:** 2025-11-30
**Mission:** 8.3 (Project Evaluation & Documentation)

---

## 📋 Overview

This gallery serves as visual verification of the system's **Functional Suitability**, **Usability**, **Maintainability**, and **Observability**. It documents the user experience from CLI initiation to final artifact generation, highlighting the multi-agent orchestration and advanced engineering practices in real-time.

**📸 Instructions for User:**
1.  Run the commands listed in the "Reproduction Command" sections.
2.  Take a screenshot of your terminal or file viewer.
3.  Save the image to `docs/screenshots/` with the filename suggested.
4.  Update this file to link the actual image (e.g., change `placeholder.png` to `cli_help.png`).
5.  Ensure the `<latest_run>` placeholder is replaced with your actual output directory name (e.g., `2025-11-30_10-00-00_Boston_MA_to_MIT`).

---

## 1. CLI User Experience (UX)

Demonstrates the **Usability** and **Helpfulness** of the interface (Nielsen Heuristic #1 & #2).

### 1.1 Help & Configuration
Shows that the system is self-documenting and standard-compliant.

**Reproduction Command:**
```bash
python -m hw4_tourguide --help
```

**Expected Output:**
```
usage: hw4_tourguide [-h] [-v] --from ORIGIN --to DESTINATION
                     [--mode {live,cached}] [--config CONFIG]
                     [--log-level {DEBUG,INFO,WARNING,ERROR}] [--output OUTPUT]

Route Enrichment Tour-Guide System

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  --from ORIGIN         Starting location (e.g., "Boston, MA")
  --to DESTINATION      Destination location (e.g., "Cambridge, MA")
  --mode {live,cached}  Run mode (live uses real APIs; cached uses local data).
  --config CONFIG       Path to YAML configuration file (default: config/settings.yaml)
  --log-level {DEBUG,INFO,WARNING,ERROR}
                        Logging level (default: INFO)
  --output OUTPUT       Path for output JSON file (default: output/final_route.json)

Examples:
  python -m hw4_tourguide --from "Boston, MA" --to "Cambridge, MA" --mode cached --log-level DEBUG
  python -m hw4_tourguide --from "Home" --to "Work" --mode live
```



### 1.2 Live Execution Progress
Demonstrates **Visibility of System Status**. Shows the progress bar or real-time log streaming during a run.

**Reproduction Command:**
```bash
# Run in cached mode to ensure deterministic output for the screenshot
python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode cached --log-level INFO
```

**Expected Output (Terminal):**
```
2025-11-30 10:00:00 | INFO     | config.loader  | ConfigLoader  | Initializing ConfigLoader...
2025-11-30 10:00:00 | INFO     | config.loader  | ConfigLoader  | Loaded config from config/settings.yaml.
2025-11-30 10:00:00 | INFO     | main           | Main          | Starting Route Enrichment Tour-Guide System...
2025-11-30 10:00:00 | INFO     | main           | RouteProvider | Selecting CachedRouteProvider.
2025-11-30 10:00:01 | INFO     | main           | Scheduler     | Initializing Scheduler with 5 steps, interval=2.0s.
2025-11-30 10:00:01 | INFO     | main           | Orchestrator  | Initializing Orchestrator with 5 workers.
2025-11-30 10:00:01 | INFO     | main           | Main          | Processing route from Boston, MA to MIT.
2025-11-30 10:00:01 | INFO     | Scheduler      | EMIT          | Step 1/5: Boston Common (TID: abcdef123)
2025-11-30 10:00:01 | INFO     | Orchestrator   | DISPATCH      | Dispatching Task for Step 1. Active Workers: 1/5
2025-11-30 10:00:01 | INFO     | agent.video    | SEARCH        | Searching for video content for "Boston Common"
2025-11-30 10:00:01 | INFO     | agent.song     | SEARCH        | Searching for song content for "Boston Common"
2025-11-30 10:00:02 | INFO     | agent.knowledge| SEARCH        | Searching for knowledge content for "Boston Common"
2025-11-30 10:00:03 | INFO     | agent.video    | FETCH         | Fetching details for video 'xyz1'
2025-11-30 10:00:03 | INFO     | agent.song     | FETCH         | Fetching details for song 'sng1'
2025-11-30 10:00:03 | INFO     | agent.knowledge| FETCH         | Fetching details for article 'art1'
2025-11-30 10:00:04 | INFO     | judge          | SCORE         | Evaluating 3 candidates for Step 1. Overall score: 85.0. Chosen: video.
2025-11-30 10:00:04 | INFO     | Scheduler      | EMIT          | Step 2/5: MIT Campus (TID: abcdef123)
2025-11-30 10:00:04 | INFO     | Orchestrator   | DISPATCH      | Dispatching Task for Step 2. Active Workers: 1/5
```



---

## 2. System Observability (Logs)

Demonstrates **Maintainability** and **Reliability**. Shows how the system tracks internal state across multiple threads.

### 2.1 Structured System Logs
Shows the main `system.log` with event tags, ensuring easy debugging.

**File to View:** `output/<latest_run>/logs/system.log`

**Expected Content (Partial):**
```
2025-11-30 10:00:00 | INFO     | config.loader  | ConfigLoader  | Initializing ConfigLoader...
2025-11-30 10:00:00 | INFO     | config.loader  | ConfigLoader  | Loaded config from config/settings.yaml.
2025-11-30 10:00:00 | DEBUG    | config.loader  | ConfigLoader  | Secret loaded for GOOGLE_MAPS_API_KEY: GOOGLE_MAPS_API_KEY=****.
2025-11-30 10:00:00 | INFO     | main           | Main          | Starting Route Enrichment Tour-Guide System...
2025-11-30 10:00:00 | INFO     | main           | RouteProvider | Selecting CachedRouteProvider.
2025-11-30 10:00:01 | INFO     | main           | Scheduler     | Initializing Scheduler with 5 steps, interval=2.0s.
2025-11-30 10:00:01 | INFO     | main           | Orchestrator  | Initializing Orchestrator with 5 workers.
2025-11-30 10:00:01 | INFO     | Scheduler      | EMIT          | Step 1/5: Boston Common (TID: abcdef123)
2025-11-30 10:00:01 | INFO     | Orchestrator   | DISPATCH      | Dispatching Task for Step 1. Active Workers: 1/5
2025-11-30 10:00:01 | INFO     | agent.video    | SEARCH        | Searching for video content for "Boston Common"
2025-11-30 10:00:01 | INFO     | api.youtube    | API_Call      | YouTube search request for 'Boston Common'.
2025-11-30 10:00:01 | INFO     | agent.song     | SEARCH        | Searching for song content for "Boston Common"
2025-11-30 10:00:02 | INFO     | api.spotify    | API_Call      | Spotify search request for 'Boston Common music'.
2025-11-30 10:00:02 | INFO     | agent.knowledge| SEARCH        | Searching for knowledge content for "Boston Common"
2025-11-30 10:00:02 | INFO     | api.wikipedia  | API_Call      | Wikipedia search request for 'Boston Common history'.
2025-11-30 10:00:03 | INFO     | agent.video    | FETCH         | Fetching details for video 'xyz1'.
2025-11-30 10:00:03 | INFO     | agent.song     | FETCH         | Fetching details for song 'sng1'.
2025-11-30 10:00:03 | INFO     | agent.knowledge| FETCH         | Fetching details for article 'art1'.
2025-11-30 10:00:04 | INFO     | judge          | SCORE         | Evaluating 3 candidates for Step 1. Overall score: 85.0. Chosen: video.
2025-11-30 10:00:04 | INFO     | Scheduler      | EMIT          | Step 2/5: MIT Campus (TID: abcdef123)
```



### 2.2 Module-Specific Logs (Separation of Concerns)
Evidence that agents, judge, and APIs write to separate logs for clarity (Mission M8).

**Files to View:** Side-by-side view of `agents.log` and `judge.log` from the latest run in `output/<latest_run>/logs/`.

**Expected Content (Partial):**
`agents.log`
```
2025-11-30 10:00:01 | INFO     | agent.video    | SEARCH        | Searching for video content for "Boston Common"
2025-11-30 10:00:01 | INFO     | agent.song     | SEARCH        | Searching for song content for "Boston Common"
2025-11-30 10:00:02 | INFO     | agent.knowledge| SEARCH        | Searching for knowledge content for "Boston Common"
2025-11-30 10:00:03 | INFO     | agent.video    | FETCH         | Fetching details for video 'xyz1'
2025-11-30 10:00:03 | INFO     | agent.song     | FETCH         | Fetching details for song 'sng1'
2025-11-30 10:00:03 | INFO     | agent.knowledge| FETCH         | Fetching details for article 'art1'
```
`judge.log`
```
2025-11-30 10:00:04 | INFO     | judge          | SCORE         | Evaluating 3 candidates for Step 1. Overall score: 85.0. Chosen: video.
2025-11-30 10:00:04 | INFO     | judge          | SCORE         | Evaluating 3 candidates for Step 2. Overall score: 90.0. Chosen: knowledge.
```



---

## 3. Rich Artifact Generation

Demonstrates **Functional Suitability**. The core value proposition of the system.

### 3.1 JSON Machine-Readable Output
The raw data contract for downstream applications.

**File to View:** `output/<latest_run>/final_route.json`

**Expected Content (Partial):**
```json
[
  {
    "transaction_id": "abcdef123",
    "step_number": 1,
    "location_name": "Boston Common",
    "coordinates": {"lat": 42.3552, "lng": -71.0658},
    "instructions": "Head east on Beacon St...",
    "agents": {
      "video": {
        "agent_type": "video",
        "status": "ok",
        "metadata": {"title": "Boston Common Tour", "url": "https://youtu.be/bostoncommon", "duration": "10:00"},
        "rationale": "Relevant historical overview."
      },
      "song": {
        "agent_type": "song",
        "status": "ok",
        "metadata": {"title": "Dirty Water", "artist": "The Standells", "url": "https://spotify.com/dirtywater"},
        "rationale": "Classic Boston anthem."
      },
      "knowledge": {
        "agent_type": "knowledge",
        "status": "ok",
        "metadata": {"title": "History of Boston Common", "url": "https://wikipedia.org/bostoncommon"},
        "rationale": "Historical context of the area."
      }
    },
    "judge": {
      "overall_score": 85.0,
      "chosen_agent": "video",
      "individual_scores": {"video": 88.0, "song": 70.0, "knowledge": 85.0},
      "rationale": "Video provides the best visual and contextual overview for this step.",
      "chosen_content": {"title": "Boston Common Tour", "url": "https://youtu.be/bostoncommon"}
    }
  },
  {
    "transaction_id": "abcdef123",
    "step_number": 2,
    "location_name": "MIT Campus",
    "coordinates": {"lat": 42.3601, "lng": -71.0942},
    "instructions": "Turn left onto Vassar St...",
    "agents": {
      "video": {
        "agent_type": "video",
        "status": "ok",
        "metadata": {"title": "MIT Campus Tour Video", "url": "https://youtu.be/mitcampus", "duration": "08:30"},
        "rationale": "Visual tour of MIT."
      },
      "song": {
        "agent_type": "song",
        "status": "ok",
        "metadata": {"title": "MIT Anthem", "artist": "MIT Students", "url": "https://spotify.com/mitanthem"},
        "rationale": "Motivational song for MIT."
      },
      "knowledge": {
        "agent_type": "knowledge",
        "status": "ok",
        "metadata": {"title": "History of MIT", "url": "https://wikipedia.org/mit"},
        "rationale": "Detailed historical overview."
      }
    },
    "judge": {
      "overall_score": 90.0,
      "chosen_agent": "knowledge",
      "individual_scores": {"video": 75.0, "song": 60.0, "knowledge": 92.0},
      "rationale": "Knowledge article provides rich historical and architectural context of MIT.",
      "chosen_content": {"title": "History of MIT", "url": "https://wikipedia.org/mit"}
    }
  }
]
```



### 3.2 Markdown Report (Human-Readable)
The user-facing itinerary.

**File to View:** `output/<latest_run>/summary.md` (rendered preview).

**Expected Content (Partial):**
```markdown
# Tour Guide System Report

**Route:** Boston, MA to MIT
**Generated On:** 2025-11-30 10:00:05
**Total Steps:** 5
**Transaction ID:** `abcdef123`

---

## Route Step 1: Boston Common
- **Instructions:** Head east on Beacon St...
- **Chosen Content Type:** **Video**
- **Title:** [Boston Common Tour](https://youtu.be/bostoncommon)
- **Rationale:** Video provides the best visual and contextual overview for this step.
- **Overall Score:** `85.0`
- **Agent Scores:** Video: 88.0, Song: 70.0, Knowledge: 85.0

---

## Route Step 2: MIT Campus
- **Instructions:** Turn left onto Vassar St...
- **Chosen Content Type:** **Knowledge**
- **Title:** [History of MIT](https://wikipedia.org/mit)
- **Rationale:** Knowledge article provides rich historical and architectural context of MIT.
- **Overall Score:** `90.0`
- **Agent Scores:** Video: 75.0, Song: 60.0, Knowledge: 92.0

---
```



### 3.3 CSV Data Export
Data ready for analysis.

**File to View:** `output/<latest_run>/final_route.csv`

**Expected Content (Partial):**
```csv
location,video_title,video_url,video_score,song_title,song_url,song_score,knowledge_title,knowledge_url,knowledge_score,judge_overall_score,judge_chosen_agent,judge_chosen_content_title,judge_chosen_content_url
Boston Common,Boston Common Tour,https://youtu.be/bostoncommon,88.0,Dirty Water,https://spotify.com/dirtywater,70.0,History of Boston Common,https://wikipedia.org/bostoncommon,85.0,85.0,video,Boston Common Tour,https://youtu.be/bostoncommon
MIT Campus,MIT Campus Tour Video,https://youtu.be/mitcampus,75.0,MIT Anthem,https://spotify.com/mitanthem,60.0,History of MIT,https://wikipedia.org/mit,92.0,90.0,knowledge,History of MIT,https://wikipedia.org/mit
```



---

## 4. Resilience & Error Handling

Demonstrates **Reliability**. Shows the system surviving failures.

### 4.1 Circuit Breaker & Retry Logic
Visual proof that the system handles API failures gracefully.

**Reproduction Logic:**
*(Requires forcing a failure, e.g., by temporarily disabling network, setting an invalid API key in `.env` for YouTube, or blocking `youtube.com` via `/etc/hosts`. Then run a live mode for a destination like "Times Square".)*

```bash
# Example: Run with a deliberately invalid YOUTUBE_API_KEY set in .env
# YOUTUBE_API_KEY=INVALID_KEY
python -m hw4_tourguide --from "New York, NY" --to "Times Square" --mode live --log-level INFO
```

**Expected Log Content (Partial from `output/<latest_run>/logs/errors.log`):**
```
2025-11-30 10:10:15 | ERROR    | api.youtube    | API_Call      | YouTube API call failed: (400) Bad Request. Consecutive failures: 1.
2025-11-30 10:10:16 | ERROR    | api.youtube    | API_Call      | YouTube API call failed: (400) Bad Request. Consecutive failures: 2.
2025-11-30 10:10:17 | WARNING  | tools.circuit_breaker| CIRCUIT_BREAKER| Circuit breaker 'youtube_api' is now OPEN due to 2 consecutive failures. It will remain open for 60 seconds.
2025-11-30 10:10:18 | INFO     | agent.video    | SEARCH        | Circuit breaker 'youtube_api' is OPEN. Falling back to stub or unavailable.
```



---

## 5. Advanced Observability & Configuration

Demonstrates **Observability** (ADR-008, ADR-011) and **Maintainability** (ADR-013) of the system.

### 5.1 Metrics Dashboard
Displays key performance indicators (KPIs) collected during a run.

**Reproduction Command:**
```bash
# Run a cached trip, then view the metrics file
python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode cached
# Then:
# cat output/<latest_run>/logs/metrics.json
```

**Expected Content (Partial from `output/<latest_run>/logs/metrics.json`):**
```json
{
  "timestamp": "2025-11-30T10:00:05Z",
  "run_id": "abcdef123",
  "counters": {
    "api_calls.google_maps.directions": 1,
    "api_calls.google_maps.geocoding": 2,
    "api_calls.youtube": 5,
    "api_calls.spotify": 3,
    "api_calls.wikipedia": 4,
    "llm_calls.query_generation": 2,
    "llm_calls.judge_scoring": 2
  },
  "gauges": {
    "queue.depth": 0,
    "active_workers": 0
  },
  "latencies": {
    "agent.video.search_ms": {"min": 120, "max": 180, "avg": 150, "count": 2},
    "agent.song.search_ms": {"min": 200, "max": 250, "avg": 225, "count": 2},
    "agent.knowledge.search_ms": {"min": 100, "max": 140, "avg": 120, "count": 2},
    "judge.scoring_ms": {"min": 50, "max": 70, "avg": 60, "count": 2},
    "llm.query_generation_ms": {"min": 800, "max": 1200, "avg": 1000, "count": 2}
  }
}
```



### 5.2 Checkpoint File Content
Verifies the system's ability to persist and recover state at critical pipeline stages.

**Reproduction Command:**
```bash
# Run a cached trip, then view a checkpoint file
python -m hw4_tourguide --from "Boston, MA" --to "MIT" --mode cached
# Then:
# cat output/<latest_run>/checkpoints/abcdef123/01_scheduler_queue.json
```

**Expected Content (Partial from `output/<latest_run>/checkpoints/abcdef123/01_scheduler_queue.json`):**
```json
{
  "transaction_id": "abcdef123",
  "steps_in_queue": [
    {
      "step_number": 1,
      "location_name": "Boston Common",
      "coordinates": {"lat": 42.3552, "lng": -71.0658},
      "instructions": "Head east on Beacon St...",
      "emit_timestamp": "2025-11-30T10:00:01Z"
    },
    {
      "step_number": 2,
      "location_name": "MIT Campus",
      "coordinates": {"lat": 42.3601, "lng": -71.0942},
      "instructions": "Turn left onto Vassar St...",
      "emit_timestamp": "2025-11-30T10:00:04Z"
    }
  ]
}
```



### 5.3 Agent Prompt Template
Shows how LLM agent behaviors are configured via Markdown templates (ADR-013).

**File to View:** `src/hw4_tourguide/prompts/agents/video_agent.md`

**Expected Content (Partial):**
```markdown
# Video Agent Prompt Template

## Role
You are an expert video content curator for a driving tour guide system. Your goal is to identify relevant and engaging videos for a specific geographic location and driving context.

## Mission
For a given route step, generate a list of precise and diverse search queries to find videos. Consider the `location_name`, `search_hint`, and `route_context`. Prioritize safety, educational value, and entertainment.

## Constraints
- Output a JSON object.
- The JSON must contain a single key: `queries`.
- The value of `queries` must be a JSON array of strings, where each string is a search query.
- Add a `reasoning` key to explain your strategy.

## Input
```json
{
  "location_name": "{location_name}",
  "coordinates_lat": "{coordinates_lat}",
  "coordinates_lng": "{coordinates_lng}",
  "instructions": "{instructions}",
  "search_hint": "{search_hint}",
  "route_context": "{route_context}"
}
```

## Output Format Example
```json
{
  "queries": [
    "historical sites {location_name}",
    "famous landmarks near {location_name} driving tour"
  ],
  "reasoning": "Generated queries focusing on history and visual tours based on the input context."
}
```
```



---

## 6. Project Structure

Demonstrates **Maintainability** and professional organization.

### 6.1 File System Layout
Shows the clean separation of `src`, `tests`, `config`, `docs`, and `output`.

**Reproduction Command:**
```bash
# On macOS/Linux (ensure 'tree' is installed: brew install tree / apt-get install tree)
tree -L 2 -I "__pycache__|.git|.venv"
```

**Expected Output:**
```
.
├── config
│   ├── .gitkeep
│   ├── run1.yaml
│   ├── run2.yaml
│   ├── run3.yaml
│   └── settings.yaml
├── data
│   ├── .DS_Store
│   └── routes
├── docs
│   ├── .DS_Store
│   ├── api_reference.md
│   ├── cost_analysis.md
│   ├── research_plan.md
│   ├── analysis
│   ├── architecture
│   ├── contracts
│   ├── prompt_log
│   ├── quality
│   └── screenshots
├── logs
│   ├── .gitkeep
│   ├── agents.log
│   ├── apis.log
│   ├── errors.log
│   ├── judge.log
│   ├── metrics.json
│   ├── route_provider.log
│   ├── run1_metrics.json
│   ├── run1_system.log
│   ├── run2_metrics.json
│   ├── run2_system.log
│   ├── run3_metrics.json
│   └── system.log
├── output
│   ├── .DS_Store
│   ├── .gitkeep
│   ├── run1
│   ├── run2
│   └── run3
├── scripts
│   ├── create_full_notebook.py
│   └── diagnose_llm_query_generation.py
├── src
│   ├── .DS_Store
│   ├── hw4_tourguide
│   └── hw4_tourguide.egg-info
└── tests
    ├── .gitkeep
    ├── conftest.py
    ├── ... (other test files)
    └── mocks
```
