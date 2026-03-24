---
phase: 02-data-pipeline
plan: 07
subsystem: ui
tags: [react, typescript, shadcn, tailwind, zustand, lucide-react]

# Dependency graph
requires:
  - phase: 02-data-pipeline plan 02
    provides: shadcn UI primitives (Button, Textarea, Badge, Popover, Tabs, Dialog, RadioGroup, Table, Collapsible, Input)
  - phase: 02-data-pipeline plan 03
    provides: data types (ParsedSource, FrequencyConflict, ColumnInfo, UploadResult, ResolutionChoice, AnalysisMode) and Zustand analysis store
provides:
  - PromptInput: multi-line prompt textarea with Fetch Data CTA, reads/writes Zustand store
  - SourceChip: editable chip with FRED/Yahoo icon, Popover edit state, error/valid states, fade animations
  - QuickDetailedToggle: two-option Tabs toggle persisted via Zustand store
  - UploadDropzone: drag-and-drop file upload with POST to /data/upload, shake animation on invalid file
  - ColumnMappingTable: column type and role editor with shadcn Table, coercion warnings, Collapsible auto-fix report
  - FrequencyMismatchDialog: blocking shadcn Dialog with RadioGroup resolution options, no outside dismiss
affects: [02-08, 03-workspace-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zustand selector pattern: one hook call per state slice (useAnalysisStore((s) => s.X))"
    - "Native drag-and-drop via onDragOver/onDragEnter/onDragLeave/onDrop — no third-party DnD library"
    - "Multipart file upload via fetch + FormData directly (not apiFetch which sets Content-Type: application/json)"
    - "base-ui Dialog blocking: disablePointerDismissal prop + onInteractOutside preventDefault + onOpenChange with preventUnmountOnClose"
    - "Native <select> for type/role dropdowns in ColumnMappingTable — no shadcn Select component needed"

key-files:
  created:
    - frontend/src/components/PromptInput.tsx
    - frontend/src/components/SourceChip.tsx
    - frontend/src/components/QuickDetailedToggle.tsx
    - frontend/src/components/UploadDropzone.tsx
    - frontend/src/components/ColumnMappingTable.tsx
    - frontend/src/components/FrequencyMismatchDialog.tsx
  modified: []

key-decisions:
  - "ColumnMapping type defined in ColumnMappingTable.tsx (not data.ts) as it is a component-local contract"
  - "base-ui Dialog blocked via disablePointerDismissal prop (root-level) + onInteractOutside event handler on Popup — dual approach for robustness"
  - "UploadDropzone uses fetch directly with FormData; apiFetch cannot be used for multipart uploads"

patterns-established:
  - "Component-local types: when a type is only used within one component as its own output contract, define it in that file"
  - "Fade-in on mount: set visible=false, then requestAnimationFrame(() => setVisible(true)) for CSS opacity transition"

requirements-completed: [DATA-01, DATA-02, DATA-03, DATA-09, DATA-12, DATA-13, DATA-14]

# Metrics
duration: 20min
completed: 2026-03-24
---

# Phase 02 Plan 07: Data Pipeline UI Components Summary

**6 standalone React UI components: PromptInput, SourceChip, QuickDetailedToggle, UploadDropzone, ColumnMappingTable, FrequencyMismatchDialog — each consuming shadcn primitives and Zustand types from Plan 03**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-03-24T01:10:00Z
- **Completed:** 2026-03-24T01:17:42Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- PromptInput textarea reads/writes Zustand store, validates min 5 chars, Cmd+Enter shortcut
- SourceChip with FRED/Yahoo Lucide icons, Popover edit state, error state, suggestion list, 150ms fade-in / 100ms fade-out animations
- QuickDetailedToggle as shadcn Tabs, persisted to localStorage via Zustand persist middleware
- UploadDropzone with native DnD, multipart POST, >500ms loading spinner, shake animation on bad file type
- ColumnMappingTable shows first 10 preview rows, type/role dropdowns, yellow dot for coercion issues, Collapsible auto-fix report, confirm disabled until all roles assigned
- FrequencyMismatchDialog as fully blocking modal: no X close, no outside click, no Escape dismiss; RadioGroup with 5 resolution options initialized to recommended method

## Task Commits

1. **Task 1: Build PromptInput, SourceChip, and QuickDetailedToggle** - `6aa5cb5` (feat)
2. **Task 2: Build UploadDropzone, ColumnMappingTable, and FrequencyMismatchDialog** - `0cf974f` (feat)

## Files Created/Modified
- `frontend/src/components/PromptInput.tsx` - Prompt textarea with Fetch Data CTA, Zustand integration
- `frontend/src/components/SourceChip.tsx` - Editable source chip with Popover, error state, animations
- `frontend/src/components/QuickDetailedToggle.tsx` - Mode toggle tabs with accent active state
- `frontend/src/components/UploadDropzone.tsx` - Drag-and-drop file upload area
- `frontend/src/components/ColumnMappingTable.tsx` - Column type/role editor with preview table
- `frontend/src/components/FrequencyMismatchDialog.tsx` - Blocking frequency conflict resolution dialog

## Decisions Made
- `ColumnMapping` type defined locally in `ColumnMappingTable.tsx` (not exported from `data.ts`) because it represents the component's output contract rather than a backend schema mirror
- Dialog blocking implemented via both `disablePointerDismissal` (base-ui root prop) and `onInteractOutside` preventDefault for defense-in-depth
- Used native `<select>` elements for type/role dropdowns in ColumnMappingTable — no shadcn Select installed, and native selects render correctly in the dark theme

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The shadcn Dialog wrapper does not expose `disablePointerDismissal` in its TypeScript props (it's a base-ui root prop not threaded through). Used `@ts-expect-error` comment to pass it through. This is intentional — the prop works at runtime via prop spreading.

## Known Stubs
None — all components have wired data sources from props. Integration with the WorkspacePage (Plan 08) will wire these together.

## Next Phase Readiness
- All 6 UI components ready for WorkspacePage integration in Plan 08
- Components are self-contained — no circular dependencies, all types from data.ts imported correctly
- TypeScript check passes (`npx tsc --noEmit` exits 0)

---
*Phase: 02-data-pipeline*
*Completed: 2026-03-24*
