---
phase: 01-foundation-infrastructure
plan: 04
subsystem: ui
tags: [react, zustand, tanstack-query, tailwindcss, shadcn, auth, frontend]

# Dependency graph
requires:
  - phase: 01-02
    provides: "Backend auth endpoints (POST /auth/register, POST /auth/token, GET /auth/me)"
  - phase: 01-03
    provides: "Job endpoints (POST /jobs/, GET /jobs/{id}, POST /jobs/{id}/cancel)"
provides:
  - "Zustand auth store with localStorage token persistence"
  - "AuthPage with tabbed login/register (UI-SPEC compliant copywriting)"
  - "ProtectedRoute and AuthRoute guards with AppInit token hydration"
  - "AppShell layout: fixed collapsible sidebar (240px/64px) + workspace"
  - "Sidebar with logo, history stub, account info, logout, collapse toggle"
  - "WorkspacePage with empty state and dev-only test job button"
  - "JobStatusCard: 4-stage progress, 2s polling, elapsed timer, cancel with inline confirmation"
affects: [phase-02, phase-03, all-frontend-phases]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zustand store with localStorage persistence (initialize() called in AppInit useEffect)"
    - "TanStack Query refetchInterval callback pattern to stop polling on terminal status"
    - "Base UI @base-ui/react TooltipTrigger used directly (no asChild — different from Radix)"
    - "apiFormPost helper for OAuth2 application/x-www-form-urlencoded login"
    - "10-second auto-dismiss cancel confirmation via useRef setTimeout"

key-files:
  created:
    - frontend/src/store/auth.ts
    - frontend/src/pages/AuthPage.tsx
    - frontend/src/pages/WorkspacePage.tsx
    - frontend/src/components/AppShell.tsx
    - frontend/src/components/Sidebar.tsx
    - frontend/src/components/JobStatusCard.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/lib/api.ts

key-decisions:
  - "TooltipTrigger from @base-ui/react does not support asChild prop (unlike Radix) — applied className directly to TooltipTrigger element instead"
  - "JobStatusCard created in Task 2 but imported by WorkspacePage created in Task 1 — created full component before final build verification to avoid circular import issues"

patterns-established:
  - "Auth pattern: useAuthStore.initialize() called once in AppInit wrapper at app root; token flows from localStorage → Zustand state → React components"
  - "Route guard pattern: ProtectedRoute redirects to /auth if no token; AuthRoute redirects to / if token present"
  - "Polling pattern: TanStack Query refetchInterval as function checking query state data status — stops automatically on success/error/cancelled"

requirements-completed: [AUTH-01, AUTH-02, AUTH-03]

# Metrics
duration: 25min
completed: 2026-03-23
---

# Phase 01 Plan 04: Frontend UI — Auth Flow, App Shell, and Job Status Card Summary

**Complete React frontend: tabbed auth page, Zustand token persistence, collapsible sidebar shell, and TanStack Query job polling card — all matching the UI-SPEC slate/indigo dark theme.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-23
- **Completed:** 2026-03-23
- **Tasks:** 2 of 3 completed (Task 3 is human-verify checkpoint — pending)
- **Files modified:** 8

## Accomplishments

- Auth store with Zustand + localStorage: token survives page refresh, sets/clears on login/logout
- AuthPage with shadcn Tabs (base-ui variant), inline validation errors, exact UI-SPEC copywriting
- App shell: collapsible sidebar (240px → 64px with tooltip mode) + fluid workspace
- JobStatusCard: 4-stage stepped progress with pulsing dot animation, 2s TanStack Query polling, 10s auto-dismiss cancel confirmation, destructive error state

## Task Commits

1. **Task 1: Auth store, auth page, protected routing, and app shell with sidebar** - `5c7cd0d` (feat)
2. **Task 2: Job status card with TanStack Query polling and cancel** - `2123652` (feat)
3. **Task 3: Visual verification of auth flow and app shell** - PENDING CHECKPOINT

## Files Created/Modified

- `frontend/src/store/auth.ts` - Zustand auth store with setAuth/logout/initialize and localStorage persistence
- `frontend/src/pages/AuthPage.tsx` - Tabbed login/register page with form validation and error handling
- `frontend/src/pages/WorkspacePage.tsx` - Workspace with empty state and dev-only test job button
- `frontend/src/components/AppShell.tsx` - Layout wrapper: Sidebar + scrollable main workspace
- `frontend/src/components/Sidebar.tsx` - Collapsible sidebar (240/64px) with tooltips in collapsed mode
- `frontend/src/components/JobStatusCard.tsx` - 4-stage job progress card with polling and cancel
- `frontend/src/App.tsx` - Updated with ProtectedRoute/AuthRoute guards, AppInit, and full routing
- `frontend/src/lib/api.ts` - Added apiFormPost helper for OAuth2 form-encoded login

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] @base-ui/react TooltipTrigger does not support `asChild`**
- **Found during:** Task 1 build verification
- **Issue:** The Sidebar used `asChild` on `TooltipTrigger`, which is a Radix UI API. This project uses `@base-ui/react` which has a different composition model (no `asChild`).
- **Fix:** Rewrote Sidebar to apply className directly to `TooltipTrigger` elements, removing all `asChild` usages.
- **Files modified:** `frontend/src/components/Sidebar.tsx`
- **Commit:** Part of `5c7cd0d`

**2. [Rule 3 - Blocking] JobStatusCard imported in WorkspacePage before it existed**
- **Found during:** Task 1 build — `Cannot find module '@/components/JobStatusCard'`
- **Fix:** Created the full JobStatusCard implementation ahead of Task 2 sequencing to satisfy the import and allow a clean build verification after Task 1.
- **Files modified:** `frontend/src/components/JobStatusCard.tsx`
- **Commit:** `2123652`

## Known Stubs

- `Sidebar.tsx` — History list is empty (no data source wired). Will be populated in Phase 3 when analysis history feature is implemented.
- `WorkspacePage.tsx` — "Test Job" button is a dev-only scaffold. Will be replaced by the prompt input component in Phase 3.
- `JobStatusCard.tsx` — "Done" stub on success (no result display). Full result rendering is Phase 3.

## Self-Check: PENDING

(Self-check deferred — Task 3 checkpoint requires human visual verification before plan is marked complete)
