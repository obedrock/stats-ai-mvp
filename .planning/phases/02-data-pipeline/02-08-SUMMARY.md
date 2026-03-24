---
phase: "02-data-pipeline"
plan: "08"
subsystem: "frontend/workspace"
tags: ["react", "zustand", "tanstack-query", "data-pipeline", "ui", "workspace"]
dependency_graph:
  requires: ["02-06", "02-07"]
  provides: ["workspace-ui", "data-pipeline-ux", "DataPreviewPanel", "AssumptionsBanner", "AssumptionsChecklist"]
  affects: ["03-analysis-execution"]
tech_stack:
  added: []
  patterns:
    - "Zustand pipelineStage state machine driving conditional rendering of all pipeline UI states"
    - "TanStack Query polling /data/preview/{jobId} with refetchInterval stopping on terminal response shapes"
    - "useEffect on query data to detect FrequencyConflict vs DataPreview response shape and transition pipeline stage"
key_files:
  created:
    - "frontend/src/components/DataPreviewPanel.tsx"
    - "frontend/src/components/AssumptionsBanner.tsx"
    - "frontend/src/components/AssumptionsChecklist.tsx"
  modified:
    - "frontend/src/pages/WorkspacePage.tsx"
    - "frontend/src/components/JobStatusCard.tsx"
    - "frontend/src/components/FrequencyMismatchDialog.tsx"
    - "frontend/src/components/UploadDropzone.tsx"
decisions:
  - "TanStack Query v5 onSuccess removed from useQuery — use useEffect on query data to handle preview poll transitions"
  - "Unused @ts-expect-error and invalid onInteractOutside prop removed from FrequencyMismatchDialog to unblock build"
  - "ACCEPTED_MIME constant removed from UploadDropzone (was declared but never read)"
  - "pipelineStage state machine centralizes all conditional rendering logic in WorkspacePage — no local component state for pipeline flow"
metrics:
  duration_minutes: 25
  completed_date: "2026-03-24"
  tasks_completed: 2
  tasks_total: 3
  files_created: 3
  files_modified: 4
---

# Phase 02 Plan 08: Frontend Data Pipeline UI Integration Summary

**One-liner:** Zustand state machine workspace integrating all 10 Phase 2 components with DataPreviewPanel, AssumptionsBanner, AssumptionsChecklist, and JobStatusCard sub-status extension.

## What Was Built

This plan wired all Phase 2 UI components into a cohesive data pipeline workspace orchestrated by a `pipelineStage` state machine in the Zustand store.

### New Components

**DataPreviewPanel** (`frontend/src/components/DataPreviewPanel.tsx`)
- Expandable Collapsible card using shadcn Card + base-ui Collapsible
- Collapsed trigger: "Show data preview (N rows)" / expanded: "Hide data preview"
- Scrollable Table (max-height 320px) showing first 50 preview rows
- Stats bar below table: per-column min/max/mean/missing_count in 12px muted text, horizontally scrollable
- Skeleton rows with `animate-pulse` for loading states
- "Run Analysis" primary button visible when expanded only

**AssumptionsBanner** (`frontend/src/components/AssumptionsBanner.tsx`)
- Collapsible banner pinned to top of content area for quick mode
- Collapsed: "Assumptions applied — click to review" with ChevronDown
- Expanded: bulleted list of assumption strings in 14px body text
- Background `#1e293b` (--card), border-bottom `--border`

**AssumptionsChecklist** (`frontend/src/components/AssumptionsChecklist.tsx`)
- Checkbox list for detailed mode pre-fetch assumptions confirmation
- Each item uses base-ui Checkbox with `checked = confirmed ?? recommended`
- "Confirm and Fetch Data" CTA disabled if no items checked

### Extended Components

**JobStatusCard** — added `sub_status` field to `JobStatusResponse` interface; renders `<span className="text-[12px] text-slate-400">` below progress track when stage is "fetching_data" and sub_status is present.

### Rewritten WorkspacePage

Full state machine orchestration across 6 pipeline stages:
- **idle**: empty state heading + PromptInput + QuickDetailedToggle + UploadDropzone
- **parsing**: disabled PromptInput + spinner
- **confirming_sources**: SourceChips + Fetch Data button (or AssumptionsChecklist for detailed mode)
- **fetching**: JobStatusCard + background preview polling
- **frequency_conflict**: FrequencyMismatchDialog modal overlay
- **preview_ready**: AssumptionsBanner (quick mode) + DataPreviewPanel with Run Analysis

Preview polling uses TanStack Query with `refetchInterval` that stops on terminal response shapes (FrequencyConflict or DataPreview), and `useEffect` on query data to detect shape and transition stages.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TanStack Query v5 onSuccess removed**
- **Found during:** Task 2 WorkspacePage build
- **Issue:** TanStack Query v5 removed `onSuccess` from `useQuery` options; using it caused TypeScript errors
- **Fix:** Replaced with `useEffect` watching query data to detect FrequencyConflict vs DataPreview response and call store transitions
- **Files modified:** `frontend/src/pages/WorkspacePage.tsx`
- **Commit:** e149836

**2. [Rule 1 - Bug] FrequencyMismatchDialog build errors**
- **Found during:** Task 2 build (`npm run build`)
- **Issue:** Unused `@ts-expect-error` directive (TS2578) and `onInteractOutside` prop not in Dialog component type (TS2322)
- **Fix:** Removed `disablePointerDismissal` prop and `onInteractOutside` handler; removed `@ts-expect-error`
- **Files modified:** `frontend/src/components/FrequencyMismatchDialog.tsx`
- **Commit:** e149836

**3. [Rule 1 - Bug] UploadDropzone unused variable**
- **Found during:** Task 2 build
- **Issue:** `ACCEPTED_MIME` array declared but never read (TS6133 error)
- **Fix:** Removed unused constant
- **Files modified:** `frontend/src/components/UploadDropzone.tsx`
- **Commit:** e149836

## Commits

| Hash | Task | Description |
|------|------|-------------|
| 77a1348 | Task 1 | feat(02-08): build DataPreviewPanel, AssumptionsBanner, AssumptionsChecklist; extend JobStatusCard |
| e149836 | Task 2 | feat(02-08): rewrite WorkspacePage with full data pipeline state machine |

## Pending

**Task 3** (checkpoint:human-verify) — awaiting user visual verification of the data pipeline UI in browser. Build compiles cleanly. Frontend is ready for visual inspection at http://localhost:5173.

## Self-Check: PASSED

- `frontend/src/components/DataPreviewPanel.tsx` — FOUND
- `frontend/src/components/AssumptionsBanner.tsx` — FOUND
- `frontend/src/components/AssumptionsChecklist.tsx` — FOUND
- `frontend/src/pages/WorkspacePage.tsx` — FOUND (modified)
- Commit 77a1348 — FOUND
- Commit e149836 — FOUND
- `npm run build` — exits 0
- `tsc --noEmit` — exits 0
