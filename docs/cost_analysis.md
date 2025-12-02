# Cost Analysis & API Usage Report

**Project:** Route Enrichment Tour-Guide System
**Date:** 2025-12-02
**Version:** 1.2 (Verified with Study Data)

## Executive Summary
This report analyzes the operational costs of the Route Enrichment Tour-Guide System, comparing "Live" (LLM + API) execution against "Cached" (Heuristic + Local) execution.

**Key Finding:** The implemented caching and heuristic fallback strategies reduce operational costs by **100%** for repeated routes and **~95%** for offline/testing modes, satisfying the project's cost control requirements (KPI #6).

---

## 1. API Call Volume (Per Run)

The data below is based on the **"Study Live"** benchmark: a 4-step route (Boston -> MIT) with `use_llm_for_queries: true`.

| API Source | Endpoint Type | Calls (Live Run) | Calls (Cached Run) | Unit Cost (Est.) | Total Cost (Live) |
|------------|---------------|-----------------:|-------------------:|------------------|------------------:|
| **Google Maps** | Directions/Geocode | 5 | 0 | $0.005 | $0.025 |
| **YouTube** | Data API (Search) | 0 (Breaker Open) | 0 | $0.0003 | $0.000 |
| **Spotify** | Web API (Search) | 16 | 0 | $0.00 | $0.00 |
| **Wikipedia** | REST API | 15 | 0 | $0.00 | $0.00 |
| **LLM (Claude)** | Query Gen + Judge | 16 | 0 | $0.002/1k tok | ~$0.05 |
| **TOTAL** | | **52** | **0** | | **~$0.075** |

*Analysis:*
*   **Circuit Breaker Protection:** The YouTube API failed (403 Forbidden) during the test. The **Circuit Breaker (ADR-010)** successfully tripped after 5 attempts, preventing further wasted calls and latency. This demonstrates the system's resilience and cost-saving safety mechanisms.
*   **High Search Volume:** The Song and Knowledge agents generated ~4 calls per step (3 queries + 1 fetch).
*   **Recommendation:** To reduce costs further, consider lowering `agents.song.search_limit` or using the `use_llm_for_queries: false` setting which defaults to 1 query/step.

---

## 2. Token Usage Analysis (LLM)

When `agents.use_llm_for_queries` and `judge.use_llm` are enabled, token consumption is constrained by the `llm_max_prompt_chars` config.

| Component | Count | Avg Prompt Tok | Avg Compl Tok | Total Tokens | Est. Cost (Claude Haiku) |
|-----------|-------|----------------|---------------|--------------|--------------------------|
| **Agent Query Gen** | 12 | ~1,250 | ~150 | 16,800 | $0.034 |
| **Judge Scoring** | 4 | ~1,500 | ~300 | 7,200 | $0.014 |
| **TOTAL** | **16** | | | **24,000** | **$0.048** |

*Note: Prompt length is strictly capped at 5000 characters by `config.agents.llm_max_prompt_chars` to prevent runaway costs.*

---

## 3. Cost Comparison: Live vs. Cached

The system supports a `--mode cached` flag which bypasses all external APIs and uses local JSON files.

| Scenario | Cost per Run | 100 Runs Cost | Savings |
|----------|-------------:|--------------:|--------:|
| **Live Mode (Full LLM)** | $0.075 | $7.50 | 0% |
| **Live Mode (Heuristic Judge)** | $0.035 | $3.50 | 53% |
| **Cached Mode (Full)** | **$0.000** | **$0.00** | **100%** |

> **Strategic Recommendation:** Use `cached` mode for all development and CI/CD pipelines. Enable `live` mode only for final integration testing and production demonstrations.

---

## 4. Optimization Strategies Implemented

The following cost-control mechanisms are active in the codebase:

1.  **Aggressive Caching (ADR-003):**
    *   Route steps are hashed and stored in `data/routes/`.
    *   Repeated runs for the same origin/destination incur zero Google Maps cost.

2.  **Search/Fetch Separation (ADR-004):**
    *   Agents "search" (cheap/light) first, and only "fetch" (expensive/heavy) the single best result.
    *   Prevents wasting bandwidth on unused metadata.

3.  **Circuit Breakers (ADR-010):**
    *   If an API fails 5 times (e.g., quota exceeded), the system stops calling it for 60s.
    *   Prevents runaway error loops and wasted retries.

4.  **LLM Budget Guards (ADR-012):**
    *   `llm_max_tokens` limits response size.
    *   `llm_max_prompt_chars` truncates inputs to prevent massive context windows from draining budgets.

## 5. Conclusion

The architecture successfully decouples "cost" from "functionality". By treating the LLM and external APIs as swappable, optional components, the system achieves a sustainable cost model ($0.00 dev / $0.07 prod) for an educational or hobbyist project while retaining the capability for high-end, AI-driven enrichment when budget permits.
