# Research Plan – Route Enrichment Tour-Guide System (Mission M5)

## Overview
Four focused studies aligned to PRD goals, ADRs, and C4 architecture. All runs should use cached routes unless cost evaluation requires live mode. Metrics source: `logs/metrics.json`; checkpoints and logs provide traceability (ADR-009/ADR-011).

## Study 1: Orchestration Efficiency
- **Objective:** Measure scheduler cadence, queue depth, worker overlap.
- **Data:** `logs/system.log` timestamps (Scheduler/Orchestrator tags), `logs/metrics.json` gauges (`queue.depth`, `threads.active`), checkpoints.
- **Method:** Run cached route (10 steps). Compute inter-arrival deltas, worker overlap windows, queue depth over time. Produce Gantt + queue-depth line plot.
- **Success Criteria:** Interval ±0.2s; concurrent agent windows observed; queue depth bounded by max_workers.

## Study 2: Cost Analysis (Live vs Cached)
- **Objective:** Quantify API cost savings from caching and query limits.
- **Data:** `metrics.json` counters (`api_calls.*`), config query limits, live vs cached runs.
- **Method:** Run one live and one cached route; compare call counts; estimate dollar cost using free-tier rates; compute savings %.
- **Success Criteria:** Cached mode uses 0 external calls; live mode ≤3 Maps calls/run; ≥90% cost reduction.

## Study 3: Judge LLM Impact
- **Objective:** Assess scoring/rationale quality with vs without LLM.
- **Data:** Judge outputs (checkpoint `04_judge_decision.json`, final JSON), optional LLM call metrics.
- **Method:** Run cached route twice: heuristic-only vs LLM-enabled (mock or real). Compare scores variance, rationale length/clarity, and latency.
- **Success Criteria:** LLM run improves rationale richness without excessive latency; fallback logged if LLM unavailable.

## Study 4: Results Visualization
- **Objective:** Visualize system behavior and outputs.
- **Data:** Metrics/logs/checkpoints; final JSON.
- **Plots:** Bar (API call counts by agent), line (queue depth over time), scatter (judge scores vs step), heatmap (agent concurrency matrix).
- **Success Criteria:** Plots render in notebook; insights traceable to logs/checkpoints.

## Execution Protocol
1. Use cached routes for reproducibility; live only for cost study.
2. Run with DEBUG logging and checkpoints enabled; preserve artifacts under `output/demo/`.
3. Capture `logs/metrics.json` and `logs/system.log` per run; avoid mixing runs (one log set per study).
4. Document commands and configs used for each run in notebook markdown cells.

## Artifacts
- Notebook: `docs/analysis/results.ipynb` (one section per study, code + plots).
- Metrics: `logs/metrics.json` (counters/latencies/gauges).
- Logs: `logs/system.log` with event tags.
- Checkpoints: `output/checkpoints/{TID}/` for replay/inspection.
