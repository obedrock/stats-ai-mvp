---
phase: 02-data-pipeline
plan: 09
subsystem: backend-data-pipeline
tags: [schema-fix, date-range, fetch-endpoint, job-model, alembic, tdd]
dependency_graph:
  requires: []
  provides:
    - FetchRequest without required job_id
    - date_range extraction from Claude via DETECT_TOOL
    - date_range stored on Job model
    - resolve-frequency uses stored date_range
  affects:
    - backend/app/schemas/data.py
    - backend/app/services/series_mapper.py
    - backend/app/routers/data.py
    - backend/app/models/job.py
    - backend/alembic/versions/
    - backend/tests/test_data_router.py
    - backend/tests/test_series_mapper.py
tech_stack:
  added: []
  patterns:
    - Optional dict field with None default for date_range in Pydantic model
    - Claude tool_use schema extended with date_range property
    - map_prompt_to_sources returns dict instead of list (sources + date_range)
    - date_range defaulted to last 20 years when None in fetch endpoint
    - date_range stored as JSON Text on Job model for reuse by resolve-frequency
key_files:
  created:
    - backend/alembic/versions/b5e1a3c7d9f2_add_date_range_to_jobs.py
    - backend/tests/test_02_09_fetch_fixes.py
  modified:
    - backend/app/schemas/data.py
    - backend/app/services/series_mapper.py
    - backend/app/routers/data.py
    - backend/app/models/job.py
    - backend/tests/test_data_router.py
    - backend/tests/test_series_mapper.py
decisions:
  - Remove job_id from FetchRequest — backend creates Job itself at fetch endpoint; no need for client to supply it
  - date_range defaults to last 20 years when None — sensible fallback without requiring user to always specify dates
  - DETECT_TOOL extended with date_range as required field — ensures Claude always extracts date context from prompt
  - map_prompt_to_sources return type changed from list to dict — cleaner API, explicit sources and date_range keys
  - date_range stored as JSON Text on Job (not JSONB) — consistent with existing pattern for SQLite test compatibility
metrics:
  duration_minutes: 5
  completed_date: "2026-03-24"
  tasks_completed: 2
  files_modified: 8
---

# Phase 02 Plan 09: Fix FetchRequest Schema and date_range Flow Summary

Fix two critical blockers that prevented /data/fetch from functioning: removed the required `job_id` field from FetchRequest, added `date_range` extraction from Claude's DETECT_TOOL, stored date_range on Job model, and fixed resolve-frequency to use the stored date_range instead of the hardcoded 2000-2023 fallback.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Fix FetchRequest schema, add date_range to Claude tool and parse_prompt, store date_range on Job | c657834 | schemas/data.py, series_mapper.py, routers/data.py, models/job.py, migration b5e1a3c7d9f2, test_02_09_fetch_fixes.py |
| 2 | Update tests for corrected FetchRequest schema and date_range flow | 66a28fc | test_data_router.py, test_series_mapper.py |

## What Was Built

### FetchRequest Schema Fix
- Removed `job_id: str` (required field that frontend never sent — caused HTTP 422 on every fetch)
- Changed `date_range: dict` to `date_range: Optional[dict] = None` (frontend sends null when no date specified)
- Endpoint now defaults to last 20 years when date_range is None

### DETECT_TOOL Extension
- Added `date_range` object with `start`/`end` string properties to DETECT_TOOL input_schema
- Added `date_range` to required fields so Claude always extracts date context from the prompt
- `map_prompt_to_sources` now returns `{"sources": [...], "date_range": {...}}` dict instead of a plain list

### parse_prompt Endpoint Update
- Extracts `date_range_obj` from the new dict return value
- Returns `PromptParseResponse(sources=parsed, date_range=date_range_obj)` — frontend now receives the extracted date range

### fetch_data_endpoint Fix
- Applies 20-year default when `payload.date_range is None`
- Stores `json.dumps(date_range)` on `Job.date_range` column for downstream reuse

### resolve_frequency Fix
- Reads `original_job.date_range` from the database (JSON decode)
- Falls back to "2000-01-01" to "2023-12-31" only if column is NULL
- Carries `original_job.date_range` forward onto the new_job for audit trail
- Removed the dead code block that tried to extract date_range from Celery task results

### Job Model + Migration
- Added `date_range: Mapped[str] = mapped_column(Text, nullable=True)` to Job
- Alembic migration b5e1a3c7d9f2 with down_revision a4f9c2b8d3e1

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_parse_prompt_endpoint mock to use new dict return format**
- **Found during:** Task 2 (running existing tests after Task 1 changes)
- **Issue:** `test_parse_prompt_endpoint` mocked `map_prompt_to_sources` returning a list; after the function return type changed to a dict, the endpoint raised `TypeError: list indices must be integers or slices, not str`
- **Fix:** Updated mock_sources in that test from a list to a dict `{"sources": [...], "date_range": None}`
- **Files modified:** backend/tests/test_data_router.py
- **Commit:** 66a28fc

**2. [Rule 1 - Bug] Updated test_series_mapper.py to check dict return shape**
- **Found during:** Task 2 (running series mapper tests)
- **Issue:** All three mapper tests asserted `len(result) == 1` (treating result as a list); after the function returns `{"sources": [...], "date_range": ...}`, `len(result)` returns 2 (number of dict keys)
- **Fix:** Updated `_make_tool_use_response` helper to include `date_range` in the mock input, updated all assertions to check `result["sources"]` and verify dict shape
- **Files modified:** backend/tests/test_series_mapper.py
- **Commit:** 66a28fc

## Known Stubs

None — all functional fixes are fully wired. date_range flows from Claude → parse_prompt response → fetch payload → Job model → resolve_frequency.

## Self-Check: PASSED

- `backend/alembic/versions/b5e1a3c7d9f2_add_date_range_to_jobs.py` — FOUND
- `backend/tests/test_02_09_fetch_fixes.py` — FOUND
- Commit c657834 — FOUND
- Commit 66a28fc — FOUND
- `FetchRequest` has no `job_id` field — VERIFIED
- `DETECT_TOOL` has `date_range` in properties — VERIFIED
- `Job.date_range` column exists — VERIFIED
- All 12 tests in test_data_router.py + test_series_mapper.py pass — VERIFIED
