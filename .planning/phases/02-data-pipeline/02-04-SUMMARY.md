---
phase: 02-data-pipeline
plan: "04"
subsystem: backend-services
tags: [data-pipeline, series-mapper, fred-fetcher, yahoo-fetcher, data-cache, tdd, claude-tool-use]
dependency_graph:
  requires: ["02-01", "02-03"]
  provides: [series_mapper, fred_fetcher, yahoo_fetcher, data_cache]
  affects: [data-pipeline-orchestration, celery-fetch-task]
tech_stack:
  added: [fredapi==0.5.2, yfinance==1.2.0, pandas>=3.0.1, anthropic>=0.86.0, openpyxl>=3.1.0, fakeredis>=2.0.0]
  patterns: [claude-tool-use, tdd-red-green, fakeredis-time-travel, utc-tz-normalization]
key_files:
  created:
    - backend/app/services/__init__.py
    - backend/app/services/series_mapper.py
    - backend/app/services/data_cache.py
    - backend/app/services/fred_fetcher.py
    - backend/app/services/yahoo_fetcher.py
    - backend/tests/test_series_mapper.py
    - backend/tests/test_data_cache.py
    - backend/tests/test_fred_fetcher.py
    - backend/tests/test_yahoo_fetcher.py
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
decisions:
  - "fakeredis TTL expiry tested by patching time.time rather than FakeServer.time (server.time attribute does not exist in fakeredis 2.x)"
metrics:
  duration_seconds: 266
  completed_date: "2026-03-24"
  tasks_completed: 2
  files_created: 9
  files_modified: 2
---

# Phase 02 Plan 04: Core Backend Services Summary

Four backend services fully implemented with TDD: Claude tool-use series mapper, FRED fetcher with series validation and search fallback, Yahoo Finance fetcher with UTC conversion, and Redis cache helpers — all external APIs mocked in tests with fakeredis and unittest.mock.

## Tasks Completed

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | series_mapper.py + data_cache.py with tests | Done | 7421266 |
| 2 | fred_fetcher.py + yahoo_fetcher.py with tests | Done | f45555b |

## What Was Built

### series_mapper.py
- `map_prompt_to_sources(prompt: str) -> list[dict]` using Claude `claude-sonnet-4-5` with `detect_data_sources` tool
- Temperature 0 for determinism; `tool_choice={"type": "tool", "name": "detect_data_sources"}` forces structured output
- Lazy `get_client()` helper enables test mocking via `patch("app.services.series_mapper.get_client")`
- Raises `ValueError` with descriptive message on failure

### data_cache.py
- `get_cached(key) -> str | None`: Redis GET with decode
- `set_cached(key, value, ttl)`: Redis SETEX
- `init_redis(client)`: test injection hook for fakeredis
- Lazy `get_redis()` falls back to `redis://redis:6379/0`

### fred_fetcher.py
- `async validate_series(series_id)`: httpx GET to `FRED /series` endpoint; returns `(True, [])` on 200 or `(False, suggestions)` on 400 with `Fred.search()` fallback
- `fetch_fred_series(series_id, start, end)`: fredapi wrapper; UTC `tz_localize("UTC")` applied to tz-naive FRED DatetimeIndex; `.copy()` for pandas 3.0 CoW

### yahoo_fetcher.py
- `fetch_yahoo_series(symbol, start, end)`: yfinance 1.x `Ticker.history()` wrapper; `tz_convert("UTC")` applied to tz-aware Yahoo DatetimeIndex; raises `ValueError` on empty DataFrame; `.copy()` for pandas 3.0 CoW

## Test Results

```
11 passed in 1.71s
tests/test_series_mapper.py::test_map_prompt_detects_fred_source PASSED
tests/test_series_mapper.py::test_map_prompt_detects_yahoo_source PASSED
tests/test_series_mapper.py::test_map_prompt_multi_source PASSED
tests/test_data_cache.py::test_set_and_get_cached PASSED
tests/test_data_cache.py::test_cache_miss_returns_none PASSED
tests/test_data_cache.py::test_cache_ttl_expiry PASSED
tests/test_fred_fetcher.py::test_validate_series_valid_id PASSED
tests/test_fred_fetcher.py::test_validate_series_invalid_returns_suggestions PASSED
tests/test_fred_fetcher.py::test_fetch_fred_series_returns_dataframe PASSED
tests/test_yahoo_fetcher.py::test_fetch_yahoo_series_returns_dataframe PASSED
tests/test_yahoo_fetcher.py::test_fetch_yahoo_invalid_ticker_raises PASSED
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed fakeredis TTL time travel mechanism**
- **Found during:** Task 1 (test_cache_ttl_expiry)
- **Issue:** The plan specified `server.time = 2.0` to advance fakeredis clock, but `FakeServer` in fakeredis 2.x does not expose a `time` attribute. The test passed the set step but `get_cached` still returned the cached value after the "clock advance."
- **Fix:** Replaced `server.time = 2.0` with `patch("time.time", return_value=start + 2)` — verified that fakeredis uses `time.time()` internally and that patching it correctly triggers TTL expiry.
- **Files modified:** backend/tests/test_data_cache.py
- **Commit:** 7421266

## Known Stubs

None — all four service modules are fully implemented with real logic. No hardcoded empty values or placeholders.

## Self-Check: PASSED
