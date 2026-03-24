# Phase 3: Core Analysis Engine - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can submit an OLS regression prompt and receive a complete result: plain-English interpretation, coefficient table, diagnostic test outputs (Breusch-Pagan, Durbin-Watson, VIF, Shapiro-Wilk), interactive Plotly charts, the generated R code, and actionable error feedback if R fails. After results, Claude suggests 2-3 context-aware follow-up tests. This phase does NOT include logistic, panel, or time-series regressions (Phase 4), analysis history (Phase 5), or export (Phase 6).

</domain>

<decisions>
## Implementation Decisions

### Results Page Layout
- **D-01:** Scrollable sections — all results visible in a single scrollable view with anchored section headers. Order: interpretation at top, then coefficient table, diagnostics, charts, R code, follow-up suggestions. The full analysis reads as a narrative.
- **D-02:** Diagnostic tests displayed as summary cards — each diagnostic as a compact card with test name, statistic value, p-value, and a pass/warn/fail badge (green/yellow/red). Cards in a row for quick visual scan.
- **D-03:** Plotly charts displayed side-by-side in a 2-column grid (coefficient plot + residual plot). Falls back to stacked on narrow screens.
- **D-04:** R code section collapsed by default behind a "View R Code" expander with a copy-to-clipboard button visible even when collapsed.

### R Code Generation
- **D-05:** Single JSON to stdout — R script outputs one JSON object containing all sections: coefficients, diagnostics, plotly_charts, model_summary. Python parses stdout as JSON. Single contract between R and Python.
- **D-06:** Data handoff via CSV temp file — Python writes the merged DataFrame to a CSV in the temp directory. R reads it with read.csv(). Docker mounts the tmpdir as read-only. Simple and debuggable.
- **D-07:** Template with Claude filling slots — a base OLS template with standard diagnostics and Plotly output is pre-written. Claude fills in: dependent var, independent vars, transformations, column mappings. Ensures diagnostics and output format are always correct.
- **D-08:** Interpretation appears all at once — wait for Claude's full Stage 2 interpretation, then render the complete results page. The job status card shows "generating interpretation" stage during the wait. No streaming infrastructure needed.

### Error Feedback
- **D-09:** Inline error card replacing results — when R fails, the results area shows an error card with plain-English explanation, suggested fix, and a collapsible section with raw R error for power users.
- **D-10:** Claude translates R errors — send R stderr + original prompt context to Claude. Claude returns a plain-English explanation and a suggested modified prompt. Uses the Stage 2 interpretation call pattern with an error-focused system prompt.
- **D-11:** "Try a modified prompt" button pre-fills the prompt input with Claude's suggested fix. User can edit before submitting.

### Follow-up Suggestions
- **D-12:** Clickable suggestion chips below results — 2-3 chips at the bottom of the results page (e.g., "Add lag terms", "Test for structural break"). Each has a title and 1-line explanation.
- **D-13:** Suggestions are context-aware — Claude references specific diagnostic results when suggesting follow-ups (e.g., if Shapiro-Wilk fails, suggest log transform; if DW flags autocorrelation, suggest lag terms).
- **D-14:** Clicking a follow-up chip pre-fills the prompt input and scrolls up. User reviews/edits before submitting. User stays in control.

### Claude's Discretion
- R template structure and specific R code patterns for diagnostics
- System prompt wording for Stage 1 (code generation) and Stage 2 (interpretation)
- Diagnostic test pass/warn/fail thresholds (standard statistical conventions)
- Plotly chart styling and color scheme (consistent with dark theme)
- Coefficient table column formatting (decimal places, significance stars)
- How the existing `run_r_analysis` Celery task is extended vs refactored for the new data handoff and JSON output pattern

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Core value, constraints, two-stage Claude call pattern
- `.planning/REQUIREMENTS.md` — ANAL-01, ANAL-05, ANAL-06, ANAL-07, ANAL-08, ANAL-10, RSLT-01 through RSLT-06 are the requirements for this phase
- `.planning/ROADMAP.md` — Phase 3 success criteria (6 criteria that must be TRUE)
- `CLAUDE.md` — Full technology stack with versions, R packages (lmtest, sandwich, plm, forecast, tseries, car, ggplot2, plotly), R execution pattern, cache patterns

### Prior Phase Context
- `.planning/phases/01-foundation-infrastructure/01-CONTEXT.md` — App shell layout, sidebar, dark theme, job status card with stepped progress, 2s polling, cancel button
- `.planning/phases/02-data-pipeline/02-CONTEXT.md` — Data pipeline UX, quick/detailed mode, source chips, frequency mismatch dialog, assumptions display

### Existing Code (Phase 1+2 foundation)
- `backend/app/tasks/analysis.py` — R sandbox execution via Docker subprocess; needs extension for CSV data mount and JSON stdout parsing
- `backend/app/tasks/data_pipeline.py` — Data pipeline Celery task; Phase 3 chains data pipeline output into R execution
- `backend/app/services/data_pipeline.py` — clean_and_merge() returns merged DataFrame; Phase 3 writes this to CSV for R
- `backend/app/models/job.py` — Job model with r_script, result_stdout, result_stderr, prompt, stage fields
- `backend/app/services/series_mapper.py` — Claude-powered prompt parsing; Phase 3 adds Claude code generation service
- `frontend/src/store/analysis.ts` — Zustand store with pipelineStage state machine; needs new stages for analysis execution and results
- `frontend/src/pages/WorkspacePage.tsx` — Main workspace; needs results rendering section after pipeline stages
- `frontend/src/components/JobStatusCard.tsx` — Staged progress card; already has "running_r" and "generating_interpretation" stages

### Technology References (from CLAUDE.md)
- R packages: lmtest (bptest, dwtest), sandwich (HC3 SEs), car (vif), stats (shapiro.test), ggplot2, plotly R (ggplotly → JSON)
- react-plotly.js 2.6.x — renders Plotly JSON from R's plotly_json() output
- Claude API via anthropic Python SDK — two calls: Stage 1 code gen (temperature 0), Stage 2 interpretation

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/tasks/analysis.py` — `run_r_analysis` Celery task with Docker subprocess, timeout, and SIGTERM handling. Extend for CSV mount and JSON parsing.
- `backend/app/tasks/celery_app.py` — Celery app instance; new tasks register here
- `backend/app/services/data_pipeline.py` — `clean_and_merge()` returns merged DataFrame with assumptions; output feeds directly into Phase 3's CSV handoff
- `backend/app/services/series_mapper.py` — Claude API call pattern (system prompt + tools); reuse for R code generation prompt
- `frontend/src/store/analysis.ts` — Zustand store with `pipelineStage` state machine; extend with analysis execution stages
- `frontend/src/components/JobStatusCard.tsx` — Already supports "running_r" and "generating_interpretation" stages
- `frontend/src/lib/api.ts` — API client with auth headers
- `frontend/src/components/DataPreviewPanel.tsx` — Table rendering pattern; reuse for coefficient table

### Established Patterns
- Celery task with `self.update_state(state="PROGRESS", meta={"stage": "...", "job_id": ...})` for progress tracking
- Docker subprocess for sandboxed R execution with timeout (60s) and resource limits (512MB, 1 CPU)
- Two-stage Claude API calls: Stage 1 generates structured output, Stage 2 interprets results
- Pydantic v2 schemas for request/response validation
- TanStack Query polling at 2s intervals for job status
- Zustand pipelineStage state machine for conditional rendering in WorkspacePage
- Dark theme: slate-950 background, indigo-500 accent

### Integration Points
- New analysis endpoints mount on existing FastAPI app (`backend/app/main.py`)
- Phase 2 data pipeline output (merged DataFrame) feeds into Phase 3 R execution
- Job model extended with analysis result fields (parsed JSON from R stdout)
- WorkspacePage gets results rendering after the existing pipeline UI stages
- react-plotly.js renders Plotly JSON returned from R

</code_context>

<specifics>
## Specific Ideas

- Results as a scrollable narrative — interpretation first gives the "answer", then supporting evidence (coefficients, diagnostics, charts) below
- Diagnostic cards with pass/warn/fail badges for instant visual assessment without interpreting p-values
- Follow-up suggestions that reference specific diagnostic findings — makes the app feel intelligent and context-aware
- Error card with Claude-suggested fix pre-filling the prompt — minimal friction to retry after failure
- R code collapsed by default respects the "non-coder" audience while remaining accessible to power users

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-core-analysis-engine*
*Context gathered: 2026-03-24*
