# Phase 1: Foundation & Infrastructure - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a secure, working foundation: project scaffolding (React + FastAPI + R), user authentication (email/password with JWT), an async job queue (Celery + Redis), sandboxed R execution (Docker container with no host mounts, no network, 60s timeout), and deployment to a Digital Ocean droplet with HTTPS. No data pipeline, no analysis logic, no Claude API calls — just the infrastructure that everything else plugs into.

</domain>

<decisions>
## Implementation Decisions

### Auth UX Flow
- **D-01:** Single page with tabs — one `/auth` route with Login and Register tabs
- **D-02:** Registration requires email + password only — no display name or affiliation fields for MVP
- **D-03:** After successful registration, auto-login and redirect to main app immediately — zero friction
- **D-04:** Password requirement is 8+ characters with no complexity rules (NIST 800-63B compliant)

### App Shell & Navigation
- **D-05:** Sidebar + workspace layout — left sidebar with history/navigation, right panel for prompt and results
- **D-06:** Sidebar is collapsible via icon toggle — collapses to icons-only mode for more workspace room
- **D-07:** Dark theme with single accent color — modern data tool aesthetic (slate/gray background, light text)
- **D-08:** Unauthenticated users go straight to `/auth` — no landing page or marketing hero for MVP

### Job Status Feedback
- **D-09:** Inline status card in workspace area — shows stepped progress: queued → fetching data → running R → generating interpretation, with elapsed time
- **D-10:** Frontend polls job status every 2 seconds via TanStack Query — no WebSocket infrastructure needed
- **D-11:** Cancel button available during execution — revokes the Celery task and kills the R subprocess

### Local Dev & Deployment
- **D-12:** Docker Compose for services only (PostgreSQL, Redis, R sandbox container) — Python backend and React frontend run natively for faster iteration
- **D-13:** Single `.env` file (gitignored) with a committed `.env.example` template showing all required variables
- **D-14:** Phase 1 includes Digital Ocean deployment — Dockerfile, nginx reverse proxy, certbot for HTTPS (required by success criterion #5)

### Claude's Discretion
- Color accent choice, specific spacing/sizing, component library details
- R sandbox Dockerfile specifics (base image, installed packages)
- Celery task naming and queue configuration
- Database schema for users table (columns beyond email/password hash)
- Nginx configuration details

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Core value, constraints, tech stack decisions
- `.planning/REQUIREMENTS.md` — AUTH-01, AUTH-02, AUTH-03 are the requirements for this phase
- `.planning/ROADMAP.md` — Phase 1 success criteria (5 criteria that must be TRUE)
- `CLAUDE.md` — Full technology stack with versions, compatibility notes, and "What NOT to Use" guidance

### Technology Stack (from CLAUDE.md)
- FastAPI 0.135.2, Python 3.12, React 19, Vite 8.0.1, PostgreSQL 16.x, Redis 7.x, Celery 5.6.2
- SQLAlchemy 2.0.48 + asyncpg, Alembic 1.18.4, Pydantic 2.x
- python-jose for JWT, passlib+bcrypt for passwords
- shadcn/ui + TailwindCSS 4.x + TypeScript 5.x for frontend
- TanStack Query 5.x for polling, Zustand 5.x for state, React Router 7.x for routing
- R 4.4.x with subprocess execution (never rpy2)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project. Only CLAUDE.md exists in the repo.

### Established Patterns
- None yet — Phase 1 establishes all patterns.

### Integration Points
- This phase creates the foundation that all subsequent phases build on:
  - Auth system → used by every authenticated endpoint
  - Celery + Redis → used by analysis execution in Phases 2-4
  - R sandbox → used by all R code execution
  - App shell (sidebar + workspace) → results display in Phases 3-6
  - Database schema → extended in every subsequent phase

</code_context>

<specifics>
## Specific Ideas

- Sidebar layout inspired by data tools (Jupyter, Observable) with history list and account section
- Job status card with stepped progress visualization (not just a spinner) — shows which stage the job is in
- Dark theme aesthetic fitting a modern data/analytics tool

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-infrastructure*
*Context gathered: 2026-03-23*
