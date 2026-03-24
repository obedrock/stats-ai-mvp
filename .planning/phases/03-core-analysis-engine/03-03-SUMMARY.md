---
phase: 03-core-analysis-engine
plan: 03
subsystem: backend
tags: [celery, analysis-pipeline, fastapi, r-execution, claude-api]
dependency_graph:
  requires:
    - 03-01  # Pydantic schemas, Job model columns, R template
    - 03-02  # r_code_gen.py, r_interpreter.py (Stage 1 + Stage 2 Claude services)
  provides:
    - run_ols_analysis Celery task (full 10-step OLS pipeline)
    - POST /analysis/run endpoint (trigger analysis)
    - GET /analysis/{job_id} endpoint (poll results)
  affects:
    - 03-04  # Frontend results panel wires to GET /analysis/{job_id}
tech_stack:
  added: []
  patterns:
    - Celery sync SQLAlchemy session (create_engine + Session) for DB writes in worker context
    - Redis cache key reconstruction: source:series_id:start:end format
    - Two Docker volume mounts: script + CSV data file
    - Plotly chart inner JSON parsing: chart["json"] string -> data + layout dict
    - GET endpoint returns union type: AnalysisResultResponse | AnalysisErrorResponse | running dict
key_files:
  created:
    - backend/app/routers/analysis.py
  modified:
    - backend/app/tasks/analysis.py
    - backend/app/main.py
decisions:
  - "Sync SQLAlchemy engine (create_engine + Session) used in Celery worker — async engine incompatible with sync Celery context"
  - "Plotly chart JSON parsed in both task (during R result processing) and router (GET endpoint) for robustness — handles both pre-parsed dict and raw JSON string formats"
  - "GET /analysis/{job_id} returns untyped dict for in-progress state rather than a schema — avoids forcing callers to handle a union type response model at FastAPI level"
  - "run_ols_analysis uses clean_and_merge() for DataFrame reconstruction (not raw pd.merge) — guarantees column naming consistency with Stage 1 Claude"
metrics:
  duration: 15
  completed_date: "2026-03-24"
  tasks_completed: 2
  files_changed: 3
---

# Phase 03 Plan 03: Backend Analysis Pipeline — Wire Celery Task and API Router

One-liner: Full OLS backend pipeline: Celery task wires data reconstruction + Stage 1 Claude + Docker R + Stage 2 Claude into two FastAPI endpoints.

## What Was Built

### Task 1: Extended Celery analysis task (`backend/app/tasks/analysis.py`)

Added `run_ols_analysis` Celery task implementing the complete 10-step OLS analysis pipeline:

1. Progress state update: `"preparing"`
2. Load Job from DB using sync SQLAlchemy session (Celery worker context requires sync engine)
3. Reconstruct DataFrame from Redis cache using stored `cached_data_keys`, then `clean_and_merge()` for consistent column names
4. Extract column names for Stage 1 Claude
5. Call `generate_ols_slots(prompt, column_names)` → dep_var, indep_vars, transformations
6. Call `render_ols_script()` → filled R script string with `/data/data.csv` data path
7. Progress state update: `"running_r"`. Write CSV + R script to tmpdir. Run Docker with two volume mounts (`-v script:/analysis.R:ro` and `-v csv:/data/data.csv:ro`)
8. On R success (returncode == 0): parse JSON stdout, process plotly_charts (parse inner JSON string), progress update `"generating_interpretation"`, call `interpret_ols_results()`, store all result fields on Job
9. On R error: call `explain_r_error()`, store error fields on Job
10. Full try/except: any unexpected exception stores `error_message` on Job and re-raises for Celery

The existing `run_r_analysis` task (Phase 1) is preserved unchanged.

### Task 2: Analysis router and FastAPI mounting (`backend/app/routers/analysis.py`, `backend/app/main.py`)

**POST /analysis/run:**
- Validates job UUID format, ownership (403 if not user's job), cached_data_keys presence (400 if missing)
- Updates job status to `"running"`, stage to `"running_analysis"`
- Enqueues `run_ols_analysis.delay(str(job.id), body.prompt)`
- Returns `JobCreated` schema

**GET /analysis/{job_id}:**
- Success path: parses `r_result_json` and `follow_up_suggestions` JSON; maps R's `plotly_charts` format to `ChartData` schema (handles both pre-parsed dicts and raw JSON string inner format); builds `AnalysisResultResponse` with full coefficient table, model summary, diagnostics bundle, charts, interpretation, follow-up suggestions
- Error path: returns `AnalysisErrorResponse` with error_explanation, suggested_prompt, r_stderr, r_code
- Running path: queries Celery `AsyncResult` for current stage meta; returns dict with status/stage/job_id

Router mounted at `/analysis` prefix with `tags=["analysis"]` in `main.py`.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data is wired from real sources (Redis cache, DB columns, Claude API, R stdout).

## Self-Check: PASSED

- backend/app/routers/analysis.py: EXISTS
- backend/app/tasks/analysis.py: EXISTS
- backend/app/main.py: EXISTS
- 03-03-SUMMARY.md: EXISTS
- Task 1 commit 2a01827: EXISTS
- Task 2 commit d58daf8: EXISTS
