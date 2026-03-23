# Phase 2: Data Pipeline - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can describe what data they need in plain English and the system pulls, cleans, and merges it from FRED and Yahoo Finance automatically — surfacing all assumptions and never silently making alignment decisions. Includes user file uploads with guided parsing, dataset caching, and data preview. This phase does NOT include Claude-powered R code generation or analysis execution — it delivers clean, merged data ready for Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Prompt Parsing & Source Detection
- **D-01:** Claude auto-picks the best-match series (e.g., "GDP" → GDPC1) and shows what it chose — user can override after seeing the selection via editable source chips
- **D-02:** Every FRED series ID is validated against the FRED /series endpoint before fetching data. If invalid, the system searches FRED for similar series names and suggests alternatives to the user
- **D-03:** After parsing, detected sources appear as editable chips (e.g., [FRED: GDPC1] [Yahoo: AAPL]) — user can click to change source or series ID before fetch starts
- **D-04:** Multi-source prompts (e.g., "AAPL price vs GDP growth") fetch all sources in parallel — frequency mismatch dialog handles alignment afterward

### Frequency Mismatch UX
- **D-05:** System auto-resolves frequency mismatches by picking the statistically appropriate method and explains its reasoning — but the dialog always blocks, requiring explicit user confirmation or override before proceeding
- **D-06:** Mismatch dialog appears after all data is fetched, showing actual data context (e.g., "AAPL has 3,200 daily rows, GDP has 92 quarterly rows — recommending quarterly aggregation via mean")
- **D-07:** Per PROJECT.md core principle: the system NEVER silently aligns data — user must always confirm the resolution strategy

### User Upload & Parsing Flow
- **D-08:** Upload entry point is a dedicated drag-and-drop area alongside the prompt input — click to browse or drag CSV/Excel/JSON files
- **D-09:** After auto-detecting columns and types, show a table preview (first 5-10 rows) with editable column type dropdowns (numeric, date, text, category) and role selectors (dependent var, independent var, date index)
- **D-10:** Malformed files are auto-fixed where possible (drop bad rows, coerce types) with a report of all changes made — user sees what was fixed before proceeding

### Data Preview & Assumptions Display
- **D-11:** Data preview appears as an expandable panel below the prompt after data is fetched/cleaned — scrollable table with first 50 rows, column stats (min/max/mean/missing count), and a "Run Analysis" button
- **D-12:** Quick mode (default): run with smart defaults, show a collapsible "Assumptions" banner at the top of results listing what was assumed (e.g., "Used log GDP, % change for CPI, no lags")
- **D-13:** Detailed mode: show each assumption as a checklist item with recommended defaults pre-selected (e.g., "☑ Log-transform GDP  ☑ CPI as % change  ☐ Include 1-period lag") — user toggles and confirms before execution
- **D-14:** Quick/Detailed toggle switch near the prompt input — persists across analyses via user preference. Quick is default.

### Claude's Discretion
- Specific FRED series ID mapping logic and fallback strategies
- Aggregation methods offered in frequency mismatch dialog (mean, last, sum, etc.)
- Column type auto-detection algorithm for uploads
- Data preview table styling and column stats selection
- Cache TTL values (CLAUDE.md suggests: FRED 24h, Yahoo 1h)
- Redis cache key format and eviction strategy

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Core value ("data pipeline is the core differentiator"), constraints, key decisions
- `.planning/REQUIREMENTS.md` — DATA-01 through DATA-16 are the requirements for this phase
- `.planning/ROADMAP.md` — Phase 2 success criteria (6 criteria that must be TRUE)
- `CLAUDE.md` — Full technology stack with versions, data sourcing libraries (yfinance 1.2.0, fredapi 0.5.x, pandas 3.0.1), R packages, cache patterns, and frequency conflict handling spec

### Prior Phase Context
- `.planning/phases/01-foundation-infrastructure/01-CONTEXT.md` — Phase 1 decisions (app shell, sidebar layout, job status card, dark theme, polling pattern)

### Existing Code (Phase 1 foundation)
- `backend/app/tasks/analysis.py` — R sandbox execution via Docker subprocess; Phase 2 adds data fetching pipeline BEFORE this step
- `backend/app/models/job.py` — Job model with stage field (queued, fetching_data, running_r, generating_interpretation, done)
- `backend/app/schemas/jobs.py` — Currently accepts raw r_script; needs new schema for natural language prompts + data source metadata
- `frontend/src/components/JobStatusCard.tsx` — Staged progress display; Phase 2 adds "fetching_data" stage visualization
- `frontend/src/lib/api.ts` — API client utilities
- `frontend/src/components/AppShell.tsx` — Main layout wrapper
- `frontend/src/pages/WorkspacePage.tsx` — Primary workspace where data preview and upload UI will live

### Technology References (from CLAUDE.md)
- yfinance 1.2.0 — 1.x redesign; Ticker.history() interface
- fredapi 0.5.x — FRED API wrapper; STATE.md notes possible fallback to pyfredapi or fedfred
- pandas 3.0.1 — Copy-on-Write is default; must use .copy() explicitly (flagged in STATE.md)
- Redis cache pattern: `{source}:{series_id}:{start}:{end}` with TTL (FRED=24h, Yahoo=1h)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/tasks/celery_app.py` — Celery app instance; new data pipeline tasks register here
- `backend/app/tasks/analysis.py` — R sandbox execution pattern; data fetching task follows same Celery task pattern
- `backend/app/models/job.py` — Job model with staged progress; extend with data source metadata columns
- `frontend/src/components/JobStatusCard.tsx` — Staged progress card; extend with "fetching_data" stage
- `frontend/src/store/auth.ts` — Zustand store pattern; create similar stores for data/analysis state
- `frontend/src/lib/api.ts` — API client with auth headers; reuse for all new endpoints

### Established Patterns
- Celery task with `self.update_state(state="PROGRESS", meta={"stage": "...", "job_id": ...})` for progress tracking
- Docker subprocess for sandboxed execution with timeout
- SQLAlchemy async models with UUID primary keys
- Pydantic v2 schemas with `from_attributes = True`
- TanStack Query polling at 2s intervals for job status
- shadcn/ui components with TailwindCSS dark theme (slate-950/indigo-500)

### Integration Points
- New data pipeline endpoints mount on existing FastAPI app (`backend/app/main.py`)
- New Celery tasks for data fetching register alongside existing `run_r_analysis` task
- Job model extended with data source metadata and cached dataset references
- Frontend workspace page gets new components: upload area, source chips, data preview panel, assumptions UI
- Redis used for both Celery broker (existing) and data caching (new)

</code_context>

<specifics>
## Specific Ideas

- Editable source chips pattern for data source override — visual, quick to scan, click-to-edit
- Frequency mismatch dialog that auto-recommends but blocks — reduces cognitive load while maintaining transparency
- Assumptions checklist in detailed mode with pre-selected defaults — toggling is faster than choosing from scratch
- Auto-fix with report for malformed uploads — don't reject outright, fix and show what changed

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-data-pipeline*
*Context gathered: 2026-03-23*
