---
phase: 03-core-analysis-engine
plan: "05"
subsystem: frontend
tags: [zustand, tanstack-query, analysis-wiring, workspace-page, results-rendering]
dependency_graph:
  requires: [03-03, 03-04]
  provides: [end-to-end-analysis-flow, results-rendering, follow-up-wiring]
  affects: [frontend/src/store/analysis.ts, frontend/src/pages/WorkspacePage.tsx]
tech_stack:
  added: []
  patterns:
    - TanStack Query polling (2s interval) for analysis job status
    - Zustand atomic state transitions (set stage + result in single call)
    - Pipeline stage state machine for conditional rendering
key_files:
  created: []
  modified:
    - frontend/src/store/analysis.ts
    - frontend/src/pages/WorkspacePage.tsx
decisions:
  - Atomic transitions in setAnalysisComplete/setAnalysisError prevent flash-of-empty-state (pitfall 6 from research)
  - Follow-up chip selection resets to idle (not analysis_complete) per D-14 — user can review/edit before resubmitting
  - PromptInput rendered at top of analysis_complete and analysis_error stages so user can start new analysis without scrolling
  - analysisJobId tracked separately from jobId (data pipeline job) — both needed for separate polling queries
metrics:
  duration: ~8 minutes
  completed_date: "2026-03-24"
  tasks_completed: 2
  tasks_total: 3
  files_modified: 2
---

# Phase 03 Plan 05: Frontend Analysis Wiring Summary

Wire the frontend end-to-end: extend Zustand store with analysis execution states, add POST /analysis/run handler, add TanStack Query polling for analysis results, and render all result components in WorkspacePage in D-01 scrollable narrative order.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend Zustand store with analysis execution stages and result state | 50e1205 | frontend/src/store/analysis.ts |
| 2 | Wire WorkspacePage — Run Analysis handler, polling, and results rendering | cd1b2b9 | frontend/src/pages/WorkspacePage.tsx |
| 3 | Verify end-to-end analysis flow | PENDING — awaiting human verification | — |

## What Was Built

### Task 1: Zustand Store Extension

Extended `frontend/src/store/analysis.ts` with:
- 3 new pipeline stages: `running_analysis`, `analysis_complete`, `analysis_error`
- 3 new state fields: `analysisJobId`, `analysisResult`, `analysisError`
- 3 new atomic actions: `setAnalysisJobId`, `setAnalysisComplete`, `setAnalysisError`
- `setAnalysisComplete` and `setAnalysisError` atomically update both the result and `pipelineStage` in a single `set()` call to prevent flash-of-empty-state
- `persist` `partialize` still only saves `mode` to localStorage — all analysis state is ephemeral

### Task 2: WorkspacePage Wiring

Modified `frontend/src/pages/WorkspacePage.tsx` with:
- 7 new result component imports: `InterpretationSection`, `CoefficientTable`, `DiagnosticsRow`, `ChartGrid`, `RCodeBlock`, `ErrorResultCard`, `FollowUpRow`
- `AnalysisPollResponse` interface for GET `/analysis/{job_id}` response shape
- TanStack Query `useQuery` polling at 2s for `/analysis/${analysisJobId}`, stops on `success`/`error`
- `useEffect` handler for poll results — calls `setAnalysisComplete` or `setAnalysisError` atomically
- `handleRunAnalysis` — replaces stub, POSTs to `/analysis/run` with `job_id` and `prompt`, sets `running_analysis` stage
- `handleFollowUpSelect` — pre-fills prompt, resets to `idle`, scrolls to top
- `handleRetryPrompt` — pre-fills prompt from error's `suggested_prompt`, resets to `idle`, scrolls to top
- JSX for `running_analysis` stage: `JobStatusCard` with cancel
- JSX for `analysis_complete` stage: `PromptInput` + 6 result sections in D-01 order separated by slate-700 dividers with `gap-8`
- JSX for `analysis_error` stage: `PromptInput` + `ErrorResultCard` with retry handler

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All sections are wired to live data from `analysisResult`. The `PromptInput` at the top of results stages is wired to `handlePromptSubmit` which starts a new analysis pipeline.

## Pending: Human Verification (Task 3)

Task 3 is a `checkpoint:human-verify` gate. The following verification is pending:

1. Start backend and frontend dev servers
2. Log in, type an analysis prompt (e.g., "Run a regression of GDP growth on interest rates from 2000 to 2023")
3. Confirm data sources, let data fetch complete
4. On data preview, click "Run Analysis"
5. Verify: JobStatusCard shows "Running analysis" then "Generating interpretation" stages
6. Verify: Results appear with all 6 sections in order: Interpretation, Coefficients, Diagnostics, Charts, R Code, Follow-up suggestions
7. Verify: Diagnostic cards show PASS/WARN/FAIL badges with correct colors
8. Verify: Plotly charts are interactive (hover shows values) and match dark theme
9. Verify: "View R Code" expands to show R code, copy button works
10. Verify: Follow-up chips are clickable and pre-fill the prompt input
11. (Optional) Test error case: submit prompt that causes R error and verify ErrorResultCard appears

## Self-Check

### Files Exist
- frontend/src/store/analysis.ts: FOUND (modified)
- frontend/src/pages/WorkspacePage.tsx: FOUND (modified)

### Commits Exist
- 50e1205: FOUND (feat: extend Zustand store)
- cd1b2b9: FOUND (feat: wire WorkspacePage)

## Self-Check: PASSED
