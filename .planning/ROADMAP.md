# Roadmap: Stats-AI

## Overview

Stats-AI is built in six phases that follow a strict dependency order: secure infrastructure and user accounts first, then the data pipeline (the core differentiator), then the OLS analysis engine with full output, then extended analysis types, then history and persistence, and finally export and polish. Each phase delivers a coherent, independently verifiable capability. Nothing that touches user data or executes LLM-generated code ships before the security and sandboxing layer is in place.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Infrastructure** - Project scaffolding, auth, async job queue, and sandboxed R execution environment (completed 2026-03-23)
- [ ] **Phase 2: Data Pipeline** - Auto-pull from FRED and Yahoo Finance, data cleaning, frequency mismatch handling, user uploads, caching, and data preview
- [ ] **Phase 3: Core Analysis Engine** - OLS regression with full diagnostics, Claude-powered code generation and interpretation, result display, and error feedback
- [ ] **Phase 4: Extended Analysis Types** - Logistic, panel, and time-series regression; model comparison
- [ ] **Phase 5: History & Persistence** - Analysis history list and full result revisitation
- [ ] **Phase 6: Export & Polish** - PDF/Excel report export and UX refinements

## Phase Details

### Phase 1: Foundation & Infrastructure
**Goal**: A secure, working foundation that authenticates users and can safely execute sandboxed R code via an async job queue — before any external access
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03
**Success Criteria** (what must be TRUE):
  1. User can create an account with email and password and immediately log in
  2. User can log in and stay logged in across browser refreshes without re-entering credentials
  3. A submitted job is enqueued, picked up by a Celery worker, and its status is queryable via the API
  4. An R subprocess is executed inside a Docker container with no host mounts, no network access, and a hard 60-second timeout — and attempting system() or download.file() fails silently
  5. The running application is reachable on a Digital Ocean droplet with HTTPS
**Plans**: 5 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffolding (backend + frontend + Docker Compose + R sandbox)
- [x] 01-02-PLAN.md — Auth backend (User model, JWT, register/login/me endpoints, tests)
- [x] 01-03-PLAN.md — Celery + R sandbox (async task queue, Docker R execution, job endpoints)
- [x] 01-04-PLAN.md — Frontend UI (auth page, app shell, sidebar, job status card)
- [x] 01-05-PLAN.md — Digital Ocean deployment (Dockerfile, nginx, HTTPS, deploy script)

**UI hint**: yes

### Phase 2: Data Pipeline
**Goal**: Users can describe what data they need in plain English and the system pulls, cleans, and merges it from FRED and Yahoo Finance automatically — surfacing all assumptions and never silently making alignment decisions
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08, DATA-09, DATA-10, DATA-11, DATA-12, DATA-13, DATA-14, DATA-15, DATA-16
**Success Criteria** (what must be TRUE):
  1. User types "GDP growth regressed on fed funds rate 2000-2023" and the system fetches the correct FRED series without user specifying series IDs
  2. User types "AAPL vs SPY since 2010" and the system fetches both from Yahoo Finance correctly
  3. When data from two sources have different frequencies (e.g., daily vs quarterly), the system pauses and presents a resolution dialog before proceeding — it never silently aligns
  4. User can upload a CSV or Excel file, see auto-detected column types, and correct any mapping before proceeding
  5. User can toggle a data preview to inspect the cleaned and merged dataset before running any analysis
  6. A previously fetched dataset is reused from cache on a second analysis that references the same series and date range
**Plans**: 8 plans


Plans:
- [x] 02-01-PLAN.md — Python deps, Job model migration, Alembic migration
- [x] 02-02-PLAN.md — shadcn UI components, test scaffolds, fixture files
- [x] 02-03-PLAN.md — Type contracts (Pydantic schemas, TypeScript types, Zustand analysis store)
- [x] 02-04-PLAN.md — Backend services: series mapper, FRED fetcher, Yahoo fetcher, Redis cache
- [x] 02-05-PLAN.md — Backend services: file parser, frequency resolver, data pipeline orchestrator
- [x] 02-06-PLAN.md — Backend API: data router endpoints and Celery fetch_data task
- [x] 02-07-PLAN.md — Frontend components: PromptInput, SourceChip, UploadDropzone, FrequencyMismatchDialog
- [ ] 02-08-PLAN.md — Frontend integration: WorkspacePage wiring, DataPreviewPanel, assumptions UI

**UI hint**: yes

### Phase 3: Core Analysis Engine
**Goal**: Users can submit an OLS regression prompt and receive a complete result: plain-English interpretation, coefficient table, diagnostic test outputs, interactive charts, the generated R code, and actionable error feedback if R fails
**Depends on**: Phase 2
**Requirements**: ANAL-01, ANAL-05, ANAL-06, ANAL-07, ANAL-08, ANAL-10, RSLT-01, RSLT-02, RSLT-03, RSLT-04, RSLT-05, RSLT-06
**Success Criteria** (what must be TRUE):
  1. User submits an OLS regression prompt and receives results with a coefficient table showing standard errors, p-values, and confidence intervals
  2. Results always include Breusch-Pagan, Durbin-Watson, VIF, and Shapiro-Wilk test outputs alongside the main regression output
  3. Results include interactive Plotly charts (at minimum: coefficient plot and residual plot) that render in the browser
  4. The generated R code for the analysis is visible and copyable on the results page
  5. When R returns an error, the user sees a plain-English explanation of what went wrong and what to try next — not a raw R stack trace
  6. After receiving results, Claude suggests 2-3 related follow-up tests the user might want to run
**Plans**: TBD
**UI hint**: yes

### Phase 4: Extended Analysis Types
**Goal**: Users can run logistic regression, panel data regression (fixed/random effects), time-series regression (ARIMA, VAR), standalone hypothesis tests, and compare multiple model specifications — all from natural language prompts
**Depends on**: Phase 3
**Requirements**: ANAL-02, ANAL-03, ANAL-04, ANAL-09
**Success Criteria** (what must be TRUE):
  1. User submits a prompt for a binary outcome variable and the system runs logistic regression with appropriate diagnostics
  2. User submits a prompt for panel data (e.g., country-year data) and the system runs fixed-effects and random-effects regression with a Hausman test
  3. User submits a time-series prompt and the system runs ARIMA or VAR — and the ADF stationarity pre-check result is visible in output
  4. User can run two or more regression specifications in a session and compare them via AIC/BIC and F-tests in a comparison table
**Plans**: TBD
**UI hint**: yes

### Phase 5: History & Persistence
**Goal**: Users can browse their past analyses and revisit any prior result in full — including the original data, assumptions, code, and charts — without re-running the analysis
**Depends on**: Phase 3
**Requirements**: HIST-01, HIST-02
**Success Criteria** (what must be TRUE):
  1. User can navigate to a history page and see a list of all past analyses with prompt text, date, and analysis type
  2. User can click any past analysis and see the complete result exactly as it appeared when first run — including coefficient table, charts, R code, and interpretation
  3. Re-opening a past analysis that used FRED data shows a note indicating the data vintage date used, so the user understands results reflect data as of that date
**Plans**: TBD
**UI hint**: yes

### Phase 6: Export & Polish
**Goal**: Users can export any analysis result as a PDF or Excel report for sharing or citation outside the app
**Depends on**: Phase 5
**Requirements**: RSLT-07
**Success Criteria** (what must be TRUE):
  1. User can click an export button on any completed analysis and download a PDF containing the prompt, coefficient table, diagnostic tests, charts, and plain-English interpretation
  2. User can download an Excel export containing the coefficient table and diagnostic test results in a structured, citation-ready format
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Infrastructure | 5/5 | Complete   | 2026-03-23 |
| 2. Data Pipeline | 7/8 | In Progress|  |
| 3. Core Analysis Engine | 0/TBD | Not started | - |
| 4. Extended Analysis Types | 0/TBD | Not started | - |
| 5. History & Persistence | 0/TBD | Not started | - |
| 6. Export & Polish | 0/TBD | Not started | - |
