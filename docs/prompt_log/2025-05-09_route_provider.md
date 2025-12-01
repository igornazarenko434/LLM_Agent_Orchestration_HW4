# Prompt Log – Route Provider (M7.1)

**Date:** 2025-05-09  
**Author:** Dev Agent  
**Context:** Build route retrieval module with live (Google Maps) and cached modes, aligned to PRD/ADR/C4 and cost controls; integrate with walking skeleton.

**User Prompt:**  
“i want you now to proceed to mission 7.1, explain me what are you going to do and how this system work in brief simply way, how do i need to get tha api from google, on what do i pay or need to pay actuall money, how we desgined our this route retriver according to the costs and everything, how we manage and what is the differenc ebetween the live or cach mode, i want you to add this full prompt as new file in prompt log also that will show our building proccess of this specific module and our understanding of how you build this. think also how this module handles all kind of errors and edge cases and what else did we missed with this module. if anything is missing in our PRD or architecture design or next missions or previos missions didnt include all what we need for this module to work perfectly so add this.”

**Plan & Design (Summary to user):**
- Provide `RouteProvider` abstraction with two implementations:
  - **CachedRouteProvider**: loads pre-fetched JSON routes from `data/routes/`, writes checkpoint `00_route.json` when enabled. Default uses hash of origin/destination; falls back to first JSON in cache dir. No external calls, no cost.
  - **GoogleMapsProvider**: calls Directions API with retries/backoff; writes checkpoint `00_route.json`. Requires `GOOGLE_MAPS_API_KEY`. Costs only when invoking live mode; free tier applies. If key missing, CLI falls back to stub to avoid breaking runs.
- Error handling/edge cases: missing cache dir/file raises; live mode retries on HTTP/status errors; transaction_id/timestamp auto-filled if absent; checkpoint writing guarded by config flag.
- Live vs Cached: cached is default for demos/tests; live only when explicitly requested and key present. Cached mode costs $0; live mode incurs API usage.

**Actions Taken:**
1. Implemented `route_provider.py` with `RouteProvider` ABC, `CachedRouteProvider`, and `GoogleMapsProvider` (retries, checkpoint write). Fallback to stub when no API key in live mode.
2. Updated CLI (`__main__.py`) to select providers per mode, run threaded skeleton (scheduler → orchestrator → stub agents/judge) with route from provider.
3. Added tests: `tests/test_route_provider.py` (cached load + checkpoint; missing file raises) plus regression run of config/logging/utils.
4. Ran tests without coverage: `pytest tests/test_route_provider.py tests/test_config_loader.py tests/test_logging.py tests/test_utils.py -q --no-cov` → 30 passed.

**Notes/Alignment:**
- Aligns with ADR-003 (live + cached), ADR-009 (checkpoint 00_route.json), ADR-002/007 (threaded scheduler/orchestrator). Metrics/circuit-breaker hooks remain for later missions (M7.7e/f).
- Costs: only Google Maps live calls incur cost; default to cached to avoid charges. Free tier assumed; retries/backoff to minimize waste.
- Next missions (M7.7a, M7.7e/f) will add checkpoint manager, circuit breaker, and metrics integration; update PRD/C4 if needed when those land.

---

# Prompt Log – Mission 7.1 Review (Gemini)

**Date:** 2025-11-22  
**Author:** Gemini Agent (acting as Senior Architect)  
**Context:** Review of Mission 7.1 (Route Provider) implementation.

---
## User Prompt

> i want you to check our mission 7.1 implementation as the same persone with specialty in agents desinger and API inference disgner for this specific mission 7.1. i want you to do the same, write you conclusions after full investigate on our mission 7.1 implementation according to overall PRD and project's architecture and add this full prompt with your review to the prompt log folder inside the route provider file as a gemini review

---
## Gemini Architectural Review Findings

### Final Architectural Verdict on Mission 7.1

The implementation of Mission 7.1 has **significant gaps** and **does not meet the bar** for a production-ready component as defined by the project's own architectural principles and mission requirements.

**Summary of Deviations:**
1.  **Architecture:**
    *   **No Circuit Breaker:** Fails to implement the resilience pattern from **ADR-010**.
    *   **No Metrics Collection:** Fails to implement the observability requirement from **ADR-011**.
2.  **Implementation:**
    *   **Unsafe Data Transformation:** The `GoogleMapsProvider` uses direct key access, making it brittle to changes in the API response format.
    *   **Code Duplication:** The checkpointing logic is duplicated in both provider classes.
    *   **Inconsistent Inheritance:** The `StubRouteProvider` does not inherit from the `RouteProvider` ABC.
3.  **Testing:**
    *   **Critically Insufficient:** The test suite is dangerously incomplete. It completely ignores the `GoogleMapsProvider` and its complex logic for API calls, retries, and data transformation. The resilience features that *are* implemented (retries) are not covered by any tests.

**Overall Recommendation:**
This component needs **significant rework** before it can be considered complete.
1.  **High Priority:** Implement the **Circuit Breaker** and **Metrics Collection** as required by the ADRs.
    * Status: Circuit breaker/metrics hooks added but full modules/tests remain in missions M7.7e/f.
2.  **High Priority:** Write comprehensive unit tests for `GoogleMapsProvider`. This must include mocking the `requests` library to test the retry logic, contract testing for the `_convert_response` method, and testing for API error handling.
    * Status: Added mocked transform and retry tests; will expand once circuit breaker/metrics are wired.
3.  **Medium Priority:** Refactor the code to make the data transformation more defensive, move the duplicated checkpointing logic to a shared location, and have the `StubRouteProvider` inherit from the ABC.
    * Status: Added defensive parsing; checkpointing will migrate to CheckpointWriter (M7.7a); StubRouteProvider can be refactored to inherit from RouteProvider when the full provider registry is introduced.

The current implementation of M7.1 introduces significant risk and technical debt. It prioritizes the "happy path" while neglecting the resilience, observability, and testing required for a production-grade system.
