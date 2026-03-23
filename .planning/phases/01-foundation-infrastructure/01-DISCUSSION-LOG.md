# Phase 1: Foundation & Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-23
**Phase:** 01-foundation-infrastructure
**Areas discussed:** Auth UX flow, App shell & nav, Job status feedback, Local dev setup

---

## Auth UX Flow

### Auth Page Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Single page with tabs | One /auth page with Login/Register tabs — fewer routes, clean for tool-focused app | ✓ |
| Separate pages | Dedicated /login and /register pages with links between them | |
| Landing page first | Marketing/hero page at / with CTA buttons leading to auth pages | |

**User's choice:** Single page with tabs
**Notes:** None

### Registration Fields

| Option | Description | Selected |
|--------|-------------|----------|
| Email + password only | Minimal friction — just email and password for MVP | ✓ |
| Email + password + display name | Adds display name for personalization | |
| Email + password + name + affiliation | Capture institution/company — more friction | |

**User's choice:** Email + password only
**Notes:** None

### Post-Registration Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-login to main app | Register → immediately logged in on main prompt page | ✓ |
| Success message then login tab | Show confirmation then switch to login tab | |
| Email verification required | Verify email before app access — adds email infra | |

**User's choice:** Auto-login to main app
**Notes:** None

### Password Requirements

| Option | Description | Selected |
|--------|-------------|----------|
| 8+ characters, no other rules | NIST 800-63B compliant — length matters most | ✓ |
| 8+ chars + 1 uppercase + 1 number | Traditional complexity rules | |
| You decide | Claude picks based on security best practices | |

**User's choice:** 8+ characters, no other rules
**Notes:** None

---

## App Shell & Nav

### Main App Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Centered prompt-first | Clean focused layout with prompt front and center — ChatGPT style | |
| Sidebar + workspace | Left sidebar with history/nav, right panel for prompt and results — data tool style | ✓ |
| Top nav + full-width | Horizontal top nav with page sections — traditional web app | |

**User's choice:** Sidebar + workspace
**Notes:** None

### Sidebar Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Collapsible with toggle | Icon toggle to collapse to icons-only mode | ✓ |
| Always visible | Fixed width, always open | |
| You decide | Claude picks best approach | |

**User's choice:** Collapsible with toggle
**Notes:** None

### Visual Style

| Option | Description | Selected |
|--------|-------------|----------|
| Dark theme with accent color | Dark background, light text, single accent color — modern data tool aesthetic | ✓ |
| Light theme, professional | White/light gray — academic/research feel | |
| Both with toggle | Dark and light modes with user toggle | |
| You decide | Claude picks clean professional look | |

**User's choice:** Dark theme with accent color
**Notes:** None

### Unauthenticated Root URL

| Option | Description | Selected |
|--------|-------------|----------|
| Straight to auth page | / redirects to /auth — no marketing page | ✓ |
| Simple hero + CTA | Brief tagline, example screenshot, Get Started button | |
| You decide | Claude picks simplest approach | |

**User's choice:** Straight to auth page
**Notes:** None

---

## Job Status Feedback

### Status Display

| Option | Description | Selected |
|--------|-------------|----------|
| Inline status in workspace | Status card with stepped progress: queued → running → done, with elapsed time | ✓ |
| Simple spinner + toast | Spinner overlay on submit, toast when done — simpler but less detail | |
| You decide | Claude picks best UX for async job progress | |

**User's choice:** Inline status in workspace
**Notes:** None

### Polling Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| 2-second intervals | Poll every 2s via TanStack Query — responsive without hammering API | ✓ |
| WebSocket push | Real-time server push — more responsive but adds WebSocket infra | |
| You decide | Claude picks right strategy for tech stack | |

**User's choice:** 2-second intervals
**Notes:** None

### Job Cancellation

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, cancel button | Cancel button during execution — revokes Celery task, kills R subprocess | ✓ |
| No, just wait | 60s timeout is safety net — no cancel UI | |
| You decide | Claude picks based on complexity | |

**User's choice:** Yes, cancel button
**Notes:** None

---

## Local Dev Setup

### Dev Environment Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Docker Compose for services only | PostgreSQL, Redis, R sandbox in Docker; Python + React run natively | ✓ |
| Full Docker Compose | Everything in containers including Python and React | |
| You decide | Claude picks balanced approach | |

**User's choice:** Docker Compose for services only
**Notes:** None

### Environment Variables

| Option | Description | Selected |
|--------|-------------|----------|
| .env file with .env.example | Single .env (gitignored) with committed .env.example template | ✓ |
| Separate .env per service | backend/.env, frontend/.env — isolated but more files | |
| You decide | Claude picks simplest approach | |

**User's choice:** .env file with .env.example
**Notes:** None

### Deployment Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Include DO deployment | Phase 1 includes Dockerfile, nginx, certbot — meets success criterion #5 | ✓ |
| Local only, deploy later | Work locally first, push deployment to sub-phase | |
| You decide | Claude decides based on success criteria | |

**User's choice:** Include DO deployment
**Notes:** None

---

## Claude's Discretion

- Color accent choice, spacing/sizing, component library details
- R sandbox Dockerfile specifics
- Celery task naming and queue configuration
- Database schema details beyond email/password
- Nginx configuration

## Deferred Ideas

None — discussion stayed within phase scope
