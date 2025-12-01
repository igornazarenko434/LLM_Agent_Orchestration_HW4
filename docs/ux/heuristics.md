# UX Heuristics – Route Enrichment Tour-Guide System (Mission M6)

Mapping Nielsen’s 10 Heuristics to our CLI/log-driven experience. Evidence references current/expected behaviors; verify with cached runs to avoid external calls.

## Heuristic 1: Visibility of System Status
- Evidence: Structured logs with event tags (`Scheduler`, `Orchestrator`, `Agent`, `Judge`, `Error`) inside each run folder.
- Command: `python -m hw4_tourguide --from "A" --to "B" --mode cached --log-level DEBUG` then `tail -n 20 output/<run>/logs/system.log`.
- Goal: Users see cadence, dispatch, and agent activity in near real time.

## Heuristic 2: Match Between System and Real World
- Evidence: CLI arguments use route terminology (`--from`, `--to`, `--mode`); outputs include route steps, distance/duration metadata.
- Command: `python -m hw4_tourguide --help` (help text uses travel language).

## Heuristic 3: User Control and Freedom
- Evidence: `--mode cached` for offline/testing; stubs via `use_live:false`/`mock_mode:true`; Ctrl+C leaves written checkpoints/logs intact.
- Command: Run cached mode and interrupt; inspect `output/<run>/checkpoints/` to confirm partial artifacts remain.

## Heuristic 4: Consistency and Standards
- Evidence: Consistent log format `TIMESTAMP | LEVEL | MODULE | EVENT_TAG | MESSAGE`; config keys mirror mission/ADR names (scheduler, orchestrator, agents, judge).
- Command: `grep -E "Scheduler|Orchestrator|Agent|Judge" output/<run>/logs/system.log | head`.

## Heuristic 5: Error Prevention
- Evidence: Config validation falls back from live to cached when API keys missing; schema validation resets invalid values to defaults.
- Command: `pytest tests/test_config_loader.py -k validation`.

## Heuristic 6: Recognition Rather Than Recall
- Evidence: CLI defaults (cached mode, default output paths), YAML inline comments describing valid ranges; help text lists examples.
- Command: `python -m hw4_tourguide --help`.

## Heuristic 7: Flexibility and Efficiency of Use
- Evidence: Config + CLI overrides allow quick tuning (intervals, worker counts); mock mode available via config for fast tests.
- Command: `python -m hw4_tourguide --mode cached --log-level DEBUG --output /tmp/final.json`.

## Heuristic 8: Aesthetic and Minimalist Design
- Evidence: Concise CLI output (version, parsed args), structured logs avoiding clutter; reports generated in Markdown/CSV.
- Command: `python -m hw4_tourguide --from "A" --to "B" --mode cached` then view `output/<run>/summary.md` and `tour_export.csv`.

## Heuristic 9: Help Users Recognize, Diagnose, and Recover from Errors
- Evidence: Error log stream (`output/<run>/logs/errors.log`), circuit breaker warnings, retries/backoff; warnings emitted for missing .env/invalid config.
- Command: `grep -i "warning\\|error" output/<run>/logs/errors.log output/<run>/logs/system.log`.

## Heuristic 10: Help and Documentation
- Evidence: `docs/api_reference.md` (config reference), this heuristics mapping, PRD/Missions/Progress Tracker links, sample commands embedded in docs.
- Command: Open docs folder (`ls docs/`) and check references from README (to be finalized in M8.3).
