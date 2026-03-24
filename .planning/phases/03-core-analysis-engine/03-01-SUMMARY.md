---
phase: 03-core-analysis-engine
plan: "01"
subsystem: analysis-contracts
tags: [pydantic, typescript, r-template, alembic, type-contracts]
dependency_graph:
  requires: []
  provides:
    - backend/app/schemas/analysis.py
    - backend/app/templates/ols_template.R
    - backend/app/models/job.py (5 new columns)
    - frontend/src/types/analysis.ts
  affects:
    - Plans 02-05 of Phase 03 (all consume these contracts)
tech_stack:
  added: []
  patterns:
    - Pydantic v2 ConfigDict(from_attributes=True) for ORM-to-schema mapping
    - R template slot substitution pattern ({{SLOT}} markers)
    - Manual Alembic migration (no live PostgreSQL in dev)
    - Text columns for JSON blobs (SQLite test compatibility)
key_files:
  created:
    - backend/app/schemas/analysis.py
    - backend/app/templates/ols_template.R
    - backend/alembic/versions/c7d3f1a9b5e2_add_analysis_columns_to_jobs.py
    - frontend/src/types/analysis.ts
  modified:
    - backend/app/models/job.py
decisions:
  - "ChartData uses unknown[] interim types for Plotly until react-plotly.js installed in Plan 04"
  - "Shapiro-Wilk guarded: NULL if n<3, sample 5000 if n>5000"
  - "DW p-value emitted as null (not NA) in JSON for Pydantic nullable field"
  - "VIF wrapped in tryCatch — returns empty dict for single-predictor models"
  - "All new Job columns stored as Text (JSON-serialized) for SQLite test compatibility"
metrics:
  duration_minutes: 15
  completed_date: "2026-03-24T15:02:06Z"
  tasks_completed: 2
  files_created: 4
  files_modified: 1
---

# Phase 03 Plan 01: Type Contracts and R Template Summary

**One-liner:** Pydantic/TypeScript type contracts and OLS R template with slot substitution, edge-case guards, and dark-theme Plotly charts.

## What Was Built

Established the shared type contracts that all Phase 3 plans depend on:

1. **Pydantic schemas** (`backend/app/schemas/analysis.py`): Full schema hierarchy — `AnalysisRunRequest`, `CoefficientRow`, `ModelSummary`, `DiagnosticResult`, `DiagnosticsBundle`, `ChartData`, `FollowUpSuggestion`, `AnalysisResultResponse`, `AnalysisErrorResponse`. DW `p_value` is nullable. VIF is `dict[str, float]` (dynamic keys).

2. **TypeScript types** (`frontend/src/types/analysis.ts`): Mirrors the Pydantic schemas exactly. `ChartData.data` uses `unknown[]` and `ChartData.layout` uses `Record<string, unknown>` as interim types pending react-plotly.js installation in Plan 04.

3. **R template** (`backend/app/templates/ols_template.R`): Complete runnable OLS template with:
   - Four slot markers: `{{DATA_PATH}}`, `{{DEP_VAR}}`, `{{INDEP_VARS}}`, `{{TRANSFORMATIONS}}`
   - `suppressPackageStartupMessages()` on all 6 library calls
   - Shapiro-Wilk sample-size guard (NULL if n<3, sample(5000) if n>5000)
   - VIF in `tryCatch` returning empty list for single-predictor models
   - DW p-value NA→NULL conversion for valid JSON
   - Dark theme: indigo-500 (#6366f1) points/bars, slate-400 (#94a3b8) reference lines, slate-700 (#334155) grid
   - JSON output via `cat(toJSON(output, auto_unbox = TRUE))` as sole stdout

4. **Job model extension** (`backend/app/models/job.py`): 5 new Text columns — `r_result_json`, `interpretation`, `follow_up_suggestions`, `error_explanation`, `suggested_prompt`.

5. **Alembic migration** (`c7d3f1a9b5e2`): Adds all 5 columns, down_revision=`b5e1a3c7d9f2`, includes both upgrade() and downgrade().

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1: Type contracts | fe31691 | Pydantic schemas and TypeScript types |
| Task 2: R template + Job model | 5ba7485 | OLS R template, Job model columns, Alembic migration |

## Deviations from Plan

**1. [Rule 1 - Bug] Replaced pre-existing ols_template.R with correct contract**
- **Found during:** Task 2
- **Issue:** A pre-existing `ols_template.R` existed at the target path but had the wrong JSON structure — used `coef_table` (data.frame), no `model_summary` key, no ggplot2/plotly charts, no `suppressPackageStartupMessages`, and the DW p-value was not null-guarded. The Pydantic schema and frontend types would not have been able to parse its output.
- **Fix:** Replaced with the complete template from RESEARCH.md with all required additions.
- **Files modified:** `backend/app/templates/ols_template.R`
- **Commit:** 5ba7485

## Known Stubs

None. All fields are real contracts (no hardcoded empty values). The `ChartData` Plotly types use `unknown[]` interim types intentionally — Plan 04 resolves them when react-plotly.js is installed.

## Self-Check: PASSED

Files exist:
- backend/app/schemas/analysis.py: EXISTS
- backend/app/templates/ols_template.R: EXISTS
- backend/alembic/versions/c7d3f1a9b5e2_add_analysis_columns_to_jobs.py: EXISTS
- frontend/src/types/analysis.ts: EXISTS
- backend/app/models/job.py (modified): EXISTS

Commits exist:
- fe31691: FOUND
- 5ba7485: FOUND
