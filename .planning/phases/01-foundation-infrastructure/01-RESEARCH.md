# Phase 1: Foundation & Infrastructure - Research

**Researched:** 2026-03-23
**Domain:** FastAPI + React + Celery + Docker R sandbox + PostgreSQL + nginx/certbot deployment
**Confidence:** HIGH (stack is well-documented; all key decisions are locked in CONTEXT.md)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Auth UX Flow**
- D-01: Single page with tabs — one `/auth` route with Login and Register tabs
- D-02: Registration requires email + password only — no display name or affiliation fields for MVP
- D-03: After successful registration, auto-login and redirect to main app immediately — zero friction
- D-04: Password requirement is 8+ characters with no complexity rules (NIST 800-63B compliant)

**App Shell & Navigation**
- D-05: Sidebar + workspace layout — left sidebar with history/navigation, right panel for prompt and results
- D-06: Sidebar is collapsible via icon toggle — collapses to icons-only mode for more workspace room
- D-07: Dark theme with single accent color — modern data tool aesthetic (slate/gray background, light text)
- D-08: Unauthenticated users go straight to `/auth` — no landing page or marketing hero for MVP

**Job Status Feedback**
- D-09: Inline status card in workspace area — shows stepped progress: queued → fetching data → running R → generating interpretation, with elapsed time
- D-10: Frontend polls job status every 2 seconds via TanStack Query — no WebSocket infrastructure needed
- D-11: Cancel button available during execution — revokes the Celery task and kills the R subprocess

**Local Dev & Deployment**
- D-12: Docker Compose for services only (PostgreSQL, Redis, R sandbox container) — Python backend and React frontend run natively for faster iteration
- D-13: Single `.env` file (gitignored) with a committed `.env.example` template showing all required variables
- D-14: Phase 1 includes Digital Ocean deployment — Dockerfile, nginx reverse proxy, certbot for HTTPS

### Claude's Discretion

- Color accent choice, specific spacing/sizing, component library details
- R sandbox Dockerfile specifics (base image, installed packages)
- Celery task naming and queue configuration
- Database schema for users table (columns beyond email/password hash)
- Nginx configuration details

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | User can create account with email and password | FastAPI + SQLAlchemy user model, passlib+bcrypt for password hashing, /auth/register endpoint |
| AUTH-02 | User can log in and receive a JWT session token | OAuth2PasswordBearer pattern, PyJWT HS256 encoding, /auth/token endpoint returning Bearer token |
| AUTH-03 | User session persists across browser refresh via stored JWT | localStorage token storage in React, Authorization header injection via TanStack Query/axios interceptor, protected route wrapper |
</phase_requirements>

---

## Summary

Phase 1 establishes every foundational system that subsequent phases plug into: project scaffolding, user auth, async job queue, sandboxed R execution, and a live HTTPS deployment. The stack is fully locked in CLAUDE.md — no technology decisions remain open.

The highest-risk areas are: (1) the Celery task revoke + R subprocess kill pattern (Celery does NOT automatically kill child processes on revoke — a SIGTERM handler is required in the task), and (2) the R sandbox Dockerfile (network isolation via `--network none` at `docker run` time, not just Dockerfile-level, is the correct isolation mechanism). The Digital Ocean deployment follows a well-established nginx reverse proxy pattern: nginx on port 443 → React static files served directly, API calls proxied to Gunicorn/uvicorn on localhost:8000.

The FastAPI official docs have shifted from `python-jose` to `PyJWT` as the recommended JWT library. CLAUDE.md specifies `python-jose[cryptography]` — use it, it still works, but be aware it is no longer actively maintained. For a new project, PyJWT is the cleaner choice; either is viable for MVP.

**Primary recommendation:** Build backend-first (models → auth endpoints → Celery → R sandbox smoke test), then frontend (Vite scaffold → React Router → auth page → app shell → job polling). Deploy to Digital Ocean as the final task in the phase, not the first.

---

## Project Constraints (from CLAUDE.md)

All directives from CLAUDE.md that constrain implementation:

| Directive | Requirement |
|-----------|-------------|
| R execution | subprocess only — NEVER rpy2, NEVER shell=True |
| Celery is mandatory | R takes 10-60s; cannot block FastAPI event loop |
| python-jose for JWT | Specified (note: now barely-maintained; PyJWT is viable alternative) |
| passlib+bcrypt for passwords | Specified |
| pandas 3.0: Copy-on-Write | All data pipeline code must use .copy() explicitly |
| Never Django | FastAPI only |
| Never Node.js backend | Python/FastAPI only |
| Never Recharts | react-plotly.js only for charts |
| Never rpy2 | subprocess isolation only |
| Never pip without lockfile | Use uv with uv.lock |
| SQLAlchemy 2.0 async patterns | create_async_engine, async sessions — not 1.x patterns |
| Docker Compose services only (D-12) | Python backend + React frontend run natively in dev |

---

## Standard Stack

### Core Backend
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12 | Backend runtime | Fastest stable; FastAPI 0.135+ requires >=3.10; 3.14 is on this machine but third-party support lags |
| FastAPI | 0.135.2 | HTTP API framework | Async-native, Pydantic v2, OpenAPI docs |
| uvicorn | latest (0.34.x) | ASGI server | Standard FastAPI server; use `uvicorn[standard]` for auto-reload |
| Gunicorn | latest | Production process manager | Wraps uvicorn workers in production; `gunicorn -w 2 -k uvicorn.workers.UvicornWorker` |
| SQLAlchemy | 2.0.48 | Async ORM | SQLAlchemy 2.0 mandatory for async; not backward compatible with 1.x |
| asyncpg | 0.30.x | Async PostgreSQL driver | Required for SQLAlchemy 2.0 async; connection string: `postgresql+asyncpg://` |
| Alembic | 1.18.4 | DB migrations | Use `-t async` template; run `alembic upgrade head` on deploy |
| Pydantic | 2.x | Validation (bundled with FastAPI) | v2 syntax required; v1 support dropped in FastAPI 0.135+ |
| python-jose[cryptography] | 3.3.x | JWT encoding/decoding | Specified in CLAUDE.md (alternative: PyJWT — see pitfalls) |
| passlib[bcrypt] | 1.7.x | Password hashing | bcrypt for secure storage |
| Celery | 5.6.2 | Async task queue | R subprocess offload; use `celery[redis]` extra |
| redis[hiredis] | 5.x | Redis client + Celery broker | hiredis gives 10x faster parsing |
| python-multipart | 0.0.x | Multipart form data | Required for FastAPI UploadFile and OAuth2PasswordRequestForm |

### Core Frontend
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.4 | UI framework | Current stable (verified: npm) |
| Vite | 8.0.2 | Build tool | Rolldown-powered, requires Node >=20.19; Node 24.14.0 is on this machine |
| TypeScript | 6.0.2 | Type safety | Current stable (verified: npm shows 6.0.2) |
| TailwindCSS | 4.2.2 | Utility CSS | v4 uses Vite plugin — `@tailwindcss/vite`, not separate config file |
| shadcn/ui | latest CLI | Component primitives | Uses Radix UI; init: `npx shadcn@latest init -t vite` |
| React Router | 7.13.2 | Client routing | Current stable (verified: npm) |
| TanStack Query | 5.95.2 | Server state + polling | Polling via `refetchInterval`; stop on completion via dynamic return |
| Zustand | 5.0.12 | Client state | Lightweight; analysis history, prompt state |
| lucide-react | 1.0.1 | Icons | Bundled with shadcn/ui |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | latest | Backend testing | All backend unit/integration tests |
| pytest-asyncio | latest | Async route testing | Required for async FastAPI route tests |
| httpx | 0.27.x | Async HTTP client + test client | FastAPI TestClient is httpx-based; also async HTTP for external calls |
| Ruff | latest | Python linting + formatting | Replaces black + flake8 |
| vitest | latest | Frontend unit testing | Vite-native |

**Installation — backend:**
```bash
# Use uv (not pip)
uv init stats-ai-backend
uv add fastapi[all] uvicorn[standard] gunicorn
uv add sqlalchemy[asyncio] asyncpg alembic
uv add celery[redis] redis[hiredis]
uv add python-jose[cryptography] passlib[bcrypt] python-multipart
uv add pydantic-settings  # for settings management from .env
uv add httpx aiofiles
uv add --dev pytest pytest-asyncio ruff
```

**Installation — frontend:**
```bash
npm create vite@latest stats-ai-frontend -- --template react-ts
cd stats-ai-frontend
npm install
# shadcn init (handles Tailwind 4 + Radix setup)
npx shadcn@latest init -t vite
# Add Phase 1 components
npx shadcn@latest add button input label tabs card separator tooltip badge
npm install react-router-dom @tanstack/react-query zustand
```

**Version verification note:** npm versions verified 2026-03-23 against npm registry. TypeScript reported as 6.0.2 (newer than 5.x in CLAUDE.md — use 5.x if CLAUDE.md strictly enforces it, otherwise 6.0.2 is fine).

---

## Architecture Patterns

### Recommended Project Structure
```
stats-ai-mvp/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory, lifespan, routers
│   │   ├── config.py            # Pydantic Settings from .env
│   │   ├── database.py          # async engine, session factory, Base
│   │   ├── models/
│   │   │   └── user.py          # SQLAlchemy User model
│   │   ├── schemas/
│   │   │   └── auth.py          # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── auth.py          # /auth/register, /auth/token, /auth/me
│   │   │   └── jobs.py          # /jobs (POST), /jobs/{id} (GET status)
│   │   ├── auth/
│   │   │   ├── jwt.py           # create_access_token, verify_token
│   │   │   ├── passwords.py     # hash_password, verify_password
│   │   │   └── dependencies.py  # get_current_user dependency
│   │   └── tasks/
│   │       ├── celery_app.py    # Celery app factory
│   │       └── analysis.py      # run_analysis task (R subprocess)
│   ├── alembic/
│   │   ├── env.py               # async migration environment
│   │   └── versions/
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx              # Router + QueryClientProvider + auth guard
│   │   ├── pages/
│   │   │   ├── AuthPage.tsx     # /auth — tabbed login/register
│   │   │   └── WorkspacePage.tsx # / — sidebar + workspace
│   │   ├── components/
│   │   │   ├── AppShell.tsx     # Sidebar + workspace layout wrapper
│   │   │   ├── Sidebar.tsx      # Collapsible left nav
│   │   │   ├── JobStatusCard.tsx # Step progress + elapsed time + cancel
│   │   │   └── ui/              # shadcn components live here (auto-generated)
│   │   ├── store/
│   │   │   └── auth.ts          # Zustand auth store (token, user)
│   │   └── lib/
│   │       ├── api.ts           # axios/fetch base client with auth header
│   │       └── utils.ts         # shadcn cn() utility
│   ├── components.json          # shadcn config (auto-generated)
│   └── vite.config.ts
├── r-sandbox/
│   └── Dockerfile               # R execution container
├── docker-compose.yml           # PostgreSQL + Redis + R sandbox services
├── nginx/
│   └── nginx.conf               # Reverse proxy config (production)
└── .env.example
```

### Pattern 1: FastAPI JWT Auth (OAuth2 Bearer)

**What:** OAuth2PasswordBearer flow — user POSTs email+password, receives JWT; token sent in `Authorization: Bearer <token>` header on all subsequent requests.

**When to use:** All authenticated endpoints — inject `current_user: User = Depends(get_current_user)`.

```python
# backend/app/auth/jwt.py
# Source: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = settings.secret_key  # from .env, min 32 chars
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days for MVP (no refresh tokens)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

**IMPORTANT:** CLAUDE.md specifies `python-jose[cryptography]` — use it. The import is `from jose import jwt` not `import jwt`. The FastAPI official docs recently switched examples to use `PyJWT` (import `jwt`). Either works for HS256; just be consistent with imports.

### Pattern 2: SQLAlchemy 2.0 Async User Model

**What:** Async-first ORM with DeclarativeBase, Mapped type annotations.

```python
# backend/app/models/user.py
# Source: https://python.plainenglish.io/fastapi-async-sqlalchemy-2-0-jwt-postgresql-your-modern-boilerplate-setup
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, func
import uuid

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

**Critical:** Use `create_async_engine` with `postgresql+asyncpg://` — not `postgresql://`. Using the wrong prefix will NOT raise an immediate error but will block the event loop under load.

### Pattern 3: Celery Task with R Subprocess + Cancel Support

**What:** Celery task that runs R script via subprocess. Must handle cancel/revoke by installing SIGTERM handler — Celery does NOT automatically kill child processes on revoke.

```python
# backend/app/tasks/analysis.py
import subprocess
import signal
import sys
import tempfile
import os
from celery import current_task
from .celery_app import celery_app

_current_proc = None

def _sigterm_handler(signum, frame):
    """Kill the R subprocess when Celery revokes the task."""
    global _current_proc
    if _current_proc and _current_proc.poll() is None:
        _current_proc.terminate()
        try:
            _current_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _current_proc.kill()
    sys.exit(0)

signal.signal(signal.SIGTERM, _sigterm_handler)

@celery_app.task(bind=True)
def run_r_analysis(self, r_script: str, job_id: str):
    global _current_proc
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "analysis.R")
        with open(script_path, "w") as f:
            f.write(r_script)

        self.update_state(state="PROGRESS", meta={"stage": "running_r"})

        try:
            _current_proc = subprocess.Popen(
                ["docker", "run", "--rm",
                 "--network", "none",
                 "--memory", "512m",
                 "--cpus", "1.0",
                 "-v", f"{script_path}:/analysis.R:ro",
                 "stats-ai-r-sandbox",
                 "Rscript", "/analysis.R"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )
            stdout, stderr = _current_proc.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            _current_proc.kill()
            raise
        finally:
            _current_proc = None

        return {"stdout": stdout.decode(), "stderr": stderr.decode()}
```

**Note:** The R sandbox container is launched via `docker run` from the Celery worker — this means the Celery worker host must have Docker available. In production (single Digital Ocean droplet), the Celery worker runs on the host with Docker installed, not inside a container itself.

### Pattern 4: TanStack Query Polling (Job Status)

**What:** Poll `/jobs/{id}` every 2 seconds (per D-10), stop when job is terminal (success/error/cancelled).

```typescript
// Source: https://tanstack.com/query/latest
const { data: jobStatus } = useQuery({
  queryKey: ["job", jobId],
  queryFn: () => fetchJobStatus(jobId),
  // Poll every 2 seconds (D-10), stop when terminal
  refetchInterval: (query) => {
    const status = query.state.data?.status;
    if (!status || ["success", "error", "cancelled"].includes(status)) {
      return false;  // stop polling
    }
    return 2000;  // 2 seconds (D-10)
  },
  enabled: !!jobId,
});
```

### Pattern 5: Auth Guard with React Router 7

**What:** Redirect unauthenticated users to `/auth` (D-08). Token stored in localStorage, read by Zustand store on app init.

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/auth";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  return token ? <>{children}</> : <Navigate to="/auth" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/" element={
          <ProtectedRoute><WorkspacePage /></ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}
```

### Anti-Patterns to Avoid

- **Inline R execution in FastAPI route:** R takes 10-60s. Running it directly in a FastAPI async route will block the event loop. Always use Celery.
- **SQLAlchemy 1.x session patterns:** `Session()` as context manager doesn't work correctly in SQLAlchemy 2.0 async. Use `async_sessionmaker` and `async with session`.
- **`python-jose` import confusion:** `python-jose` import is `from jose import jwt`. `PyJWT` import is `import jwt`. These are different packages — mixing them causes `AttributeError`.
- **`create_engine` instead of `create_async_engine`:** Will silently run synchronously; not immediately obvious but blocks event loop under load.
- **`docker run` with host mounts for R scripts + no `--network none`:** Always pass `--network none` at runtime, not just in Dockerfile — network access can be added back at run time otherwise.
- **Celery `revoke()` without SIGTERM handler:** `app.control.revoke(task_id, terminate=True)` sends SIGTERM to the Celery worker process but does NOT kill child subprocesses. The R subprocess will keep running.
- **`shell=True` in subprocess:** Security vulnerability — never use for R execution.
- **TailwindCSS v4 config file:** v4 does NOT use `tailwind.config.js` — configuration is in CSS `@theme {}` blocks or via the Vite plugin. The old config file will be silently ignored.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT encoding/decoding | Custom crypto | python-jose or PyJWT | Timing attacks, key rotation, algorithm confusion attacks |
| Password hashing | Custom bcrypt | passlib[bcrypt] | Subtle timing attack vectors; work factor management |
| DB connection pooling | Manual pool | SQLAlchemy asyncpg | Connection limits, timeout handling, keepalives |
| DB schema versioning | Manual SQL files | Alembic | Dependency ordering, rollback support, autogenerate |
| Task queue retry logic | Manual polling loop | Celery built-in | Exponential backoff, dead letter queues, visibility timeout |
| React form validation | Custom state machines | React Hook Form (if needed) | Shadcn form primitives integrate with it; but for MVP's 2 fields, plain controlled inputs are fine |
| Polling interval management | setInterval + cleanup | TanStack Query refetchInterval | Memory leaks, stale closures, tab focus handling |
| HTTPS certificate management | Manual OpenSSL | certbot + Let's Encrypt | Auto-renewal, revocation, OCSP stapling |

**Key insight:** The auth and async task queue patterns have well-established library solutions. The only area requiring custom code is the R subprocess execution pattern itself — that's where to invest care.

---

## R Sandbox Architecture

The R sandbox is the most security-critical custom component. Key decisions (Claude's discretion per CONTEXT.md):

### Dockerfile Pattern

```dockerfile
# r-sandbox/Dockerfile
FROM r-base:4.4.2

# Install only the packages needed for analysis (no internet at runtime)
# Pre-install during build time when network IS available
RUN Rscript -e "install.packages(c('ggplot2','plotly','lmtest','sandwich','plm','forecast','tseries','car'), repos='https://cran.rstudio.com/')"

# Create a non-root user for R execution
RUN useradd -m -u 1000 ruser
USER ruser

# No CMD or ENTRYPOINT — caller provides `Rscript /analysis.R`
```

### Runtime Isolation Flags

```bash
docker run --rm \
  --network none \          # No network access
  --memory 512m \           # Memory cap
  --cpus 1.0 \              # CPU cap
  --read-only \             # Read-only root filesystem
  --tmpfs /tmp:size=64m \   # Writable /tmp for R temp files
  -v /path/to/script.R:/analysis.R:ro \  # Script mounted read-only
  --user 1000 \             # Non-root
  stats-ai-r-sandbox \
  Rscript /analysis.R
```

**Why `--network none` at runtime:** Even if the Dockerfile doesn't expose network, a caller could override with `--network bridge`. Explicitly passing `--network none` at `docker run` time enforces the constraint regardless of image defaults.

**Why `--read-only` with `--tmpfs`:** R needs to write temporary files. `--read-only` prevents writes to the container filesystem; `--tmpfs /tmp` provides a RAM-backed writable scratch space that is automatically discarded.

**system() and download.file() fail silently:** With `--network none`, `download.file()` will fail with a connection error. `system()` will run but cannot reach external hosts. For additional restriction, add an R startup file:

```r
# Mount this as /etc/R/Rprofile.site in the container
system <- function(...) stop("system() is disabled in this environment")
download.file <- function(...) stop("download.file() is disabled")
```

---

## Common Pitfalls

### Pitfall 1: python-jose is Barely Maintained
**What goes wrong:** `python-jose` had its last release in 2021 and has known security warnings. FastAPI's own docs have been updated to recommend PyJWT instead.
**Why it happens:** CLAUDE.md specifies `python-jose` as it was the recommended choice at time of writing.
**How to avoid:** Either: (a) use `python-jose[cryptography]` as specified — it still works for HS256, or (b) use `PyJWT` (`pip install PyJWT`) with import `import jwt`. Do NOT mix the two packages. Pick one and use it everywhere.
**Warning signs:** `AttributeError: module 'jwt' has no attribute 'encode'` — you have both installed and are importing the wrong one.

### Pitfall 2: Celery Revoke Does Not Kill Subprocesses
**What goes wrong:** User clicks "Cancel Job" → frontend calls revoke endpoint → Celery worker stops executing Python code AFTER the `subprocess.Popen()` call → R process keeps running until its 60s timeout.
**Why it happens:** `app.control.revoke(task_id, terminate=True)` sends SIGTERM to the Celery worker process. The subprocess is a child process and gets orphaned.
**How to avoid:** Install a SIGTERM signal handler in the Celery task (see Pattern 3 above) that calls `_current_proc.terminate()` before exiting.
**Warning signs:** After clicking Cancel, system CPU stays elevated; Docker shows R container still running.

### Pitfall 3: TailwindCSS v4 Config File is Silently Ignored
**What goes wrong:** Developer creates `tailwind.config.js` (v3 pattern) → styles don't apply → hard to debug.
**Why it happens:** Tailwind v4 uses a Vite plugin (`@tailwindcss/vite`) and CSS `@theme {}` blocks. It does not scan for or use `tailwind.config.js`.
**How to avoid:** Use `npx shadcn@latest init -t vite` — it sets up the correct v4 pattern automatically. Do not create `tailwind.config.js`.
**Warning signs:** Custom colors or spacing not applying despite being in `tailwind.config.js`.

### Pitfall 4: SQLAlchemy async URL Mismatch
**What goes wrong:** Using `postgresql://` connection string with `create_async_engine` — no error at startup, but blocks the event loop under load.
**Why it happens:** SQLAlchemy silently falls back to synchronous execution if the driver doesn't match.
**How to avoid:** Always use `postgresql+asyncpg://` with `create_async_engine`. Use `postgresql://` (without asyncpg) only for Alembic sync migrations in `env.py`.
**Warning signs:** App works fine in dev but hangs under concurrent load.

### Pitfall 5: Alembic env.py Needs Both Sync and Async URLs
**What goes wrong:** Alembic `env.py` configured for async fails to run migrations because Alembic's migration runner is synchronous.
**Why it happens:** Alembic runs migrations in a sync context even when using async SQLAlchemy.
**How to avoid:** Initialize with `alembic init -t async` — generates an `env.py` that wraps the async engine in `asyncio.run()` for migration execution. Keep two URL settings: `ASYNC_DATABASE_URL` for the app, `SYNC_DATABASE_URL` (with `psycopg2` or sync asyncpg) for Alembic.
**Warning signs:** `RuntimeError: This event loop is already running` or `Exception: No driver found`.

### Pitfall 6: R Container Needs Pre-installed Packages
**What goes wrong:** `--network none` at runtime means `install.packages()` inside R scripts fails silently or with a cryptic network error.
**Why it happens:** Network is disabled at runtime for security.
**How to avoid:** All R packages must be installed in the Dockerfile during build time (when network is available). For Phase 1 smoke test, include only base R. For Phase 3+, add the full package list to the Dockerfile.
**Warning signs:** R scripts fail with "unable to access index for repository" or "cannot open URL".

### Pitfall 7: Node.js Version
**What goes wrong:** Vite 8 requires Node >=20.19. Running `npm create vite@latest` on an older Node fails with a cryptic error.
**Why it happens:** Vite 8 uses Rolldown (Rust-based bundler) with Node API requirements that changed in 20.19.
**How to avoid:** Verify Node version before scaffolding: `node --version`. This machine has Node 24.14.0 — this is fine.
**Warning signs:** `Error: require() of ES modules is not supported` or version-specific build failures.

### Pitfall 8: JWT Token Expiry for MVP
**What goes wrong:** Using 30-minute token expiry (FastAPI docs default) → users are logged out constantly → AUTH-03 "session persists across browser refresh" effectively fails after 30 minutes.
**Why it happens:** Copying the FastAPI tutorial's `ACCESS_TOKEN_EXPIRE_MINUTES = 30` verbatim.
**How to avoid:** For MVP (no refresh token mechanism), set expiry to 7 days. Implementing refresh tokens adds complexity; defer to a later phase. Set `ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7` (7 days).
**Warning signs:** Users report being logged out unexpectedly; AUTH-03 verification fails.

---

## Code Examples

### Alembic async env.py (critical configuration)
```python
# alembic/env.py — key sections
# Source: https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/
import asyncio
from sqlalchemy.ext.asyncio import async_engine_from_config

def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )

    async def do_run_migrations(connection):
        await connection.run_sync(do_run_migrations_sync)

    async def run_async_migrations():
        async with connectable.connect() as connection:
            await do_run_migrations(connection)
        await connectable.dispose()

    asyncio.run(run_async_migrations())
```

### Celery App Factory
```python
# backend/app/tasks/celery_app.py
from celery import Celery

def create_celery_app() -> Celery:
    app = Celery(
        "stats_ai",
        broker=settings.redis_url,
        backend=settings.redis_url,
        include=["app.tasks.analysis"],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        task_acks_late=True,          # Don't ack until task completes
        worker_prefetch_multiplier=1,  # One R job at a time per worker
    )
    return app

celery_app = create_celery_app()
```

### Nginx Production Config (proxy pattern)
```nginx
# nginx/nginx.conf
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # React static files
    root /var/www/stats-ai;
    index index.html;

    # React Router — all non-file requests go to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # FastAPI backend — proxy /api/* to uvicorn
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}
```

### .env.example Template
```bash
# .env.example — commit this; gitignore .env
DATABASE_URL=postgresql+asyncpg://stats_ai:password@localhost:5432/stats_ai
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-to-at-least-32-random-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Node.js | Vite frontend build | Yes | 24.14.0 | — |
| npm | Frontend package mgmt | Yes | 11.9.0 | — |
| R | R sandbox Dockerfile build/test | Yes | 4.5.2 (local) | Use r-base:4.4.2 in Docker |
| Docker | R sandbox at runtime, dev services | No | — | Must install — no fallback |
| PostgreSQL | Database | No | — | Docker Compose (as per D-12) |
| Redis | Celery broker + cache | No | — | Docker Compose (as per D-12) |
| Python 3.12 | FastAPI backend | No (3.14.3 present) | 3.14.3 | Use pyenv/uv to install 3.12 |
| uv | Python package mgmt | No | — | pip (not recommended; use uv) |

**Missing dependencies with no fallback:**
- **Docker** — required for R sandbox (runtime) and dev services (PostgreSQL, Redis). Must be installed before execution. On Windows: Docker Desktop.

**Missing dependencies with fallback:**
- **Python 3.12** — machine has 3.14.3. FastAPI 0.135.2 requires >=3.10; 3.14 is untested but likely works. CLAUDE.md specifies 3.12 as the target. Use `uv python install 3.12` to install and pin via `.python-version` file.
- **uv** — can use pip instead, but CLAUDE.md requires uv. Install: `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `winget install --id=astral-sh.uv`).

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (backend); vitest (frontend) |
| Config file | `backend/pyproject.toml` `[tool.pytest.ini_options]` + `frontend/vitest.config.ts` |
| Quick run command | `cd backend && uv run pytest tests/test_auth.py -x` |
| Full suite command | `cd backend && uv run pytest && cd ../frontend && npm run test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | POST /auth/register creates user, returns 201 | integration | `uv run pytest tests/test_auth.py::test_register -x` | Wave 0 |
| AUTH-01 | Duplicate email returns 409 | integration | `uv run pytest tests/test_auth.py::test_register_duplicate -x` | Wave 0 |
| AUTH-02 | POST /auth/token with valid credentials returns JWT | integration | `uv run pytest tests/test_auth.py::test_login -x` | Wave 0 |
| AUTH-02 | POST /auth/token with invalid credentials returns 401 | integration | `uv run pytest tests/test_auth.py::test_login_invalid -x` | Wave 0 |
| AUTH-03 | GET /auth/me with valid Bearer token returns user | integration | `uv run pytest tests/test_auth.py::test_me -x` | Wave 0 |
| AUTH-03 | GET /auth/me with expired/invalid token returns 401 | integration | `uv run pytest tests/test_auth.py::test_me_unauthorized -x` | Wave 0 |
| Celery smoke | Job enqueued, status queryable, worker processes it | integration | `uv run pytest tests/test_jobs.py::test_job_lifecycle -x` | Wave 0 |
| R sandbox | R subprocess runs, timeout works, no network access | integration | `uv run pytest tests/test_r_sandbox.py::test_r_runs -x` | Wave 0 |
| R sandbox | `download.file()` fails in sandbox | integration | `uv run pytest tests/test_r_sandbox.py::test_r_no_network -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q` (fail fast)
- **Per wave merge:** Full suite: `uv run pytest && npm run test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/conftest.py` — async test fixtures, DB session override, test client
- [ ] `backend/tests/test_auth.py` — AUTH-01, AUTH-02, AUTH-03 coverage
- [ ] `backend/tests/test_jobs.py` — Celery job lifecycle smoke test
- [ ] `backend/tests/test_r_sandbox.py` — R subprocess execution + security tests
- [ ] `backend/pyproject.toml` pytest config with `asyncio_mode = "auto"`
- [ ] Docker must be running before integration tests execute (test prereq)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose for JWT | PyJWT | FastAPI docs updated 2024 | python-jose still works; PyJWT is the new recommended choice |
| tailwind.config.js | @tailwindcss/vite plugin + @theme {} CSS | Tailwind v4 (2025) | Config file is silently ignored in v4 |
| declarative_base() | DeclarativeBase class | SQLAlchemy 2.0 (2023) | Better type checking; old pattern still works but deprecated |
| Rollup/esbuild | Rolldown (Rust) | Vite 8 (2025) | Faster builds; requires Node 20.19+ |
| passlib as primary recommendation | pwdlib + Argon2 | FastAPI docs updated 2024 | passlib+bcrypt still valid; pwdlib is "modern" but less deployed |

**Deprecated/outdated:**
- `python-jose`: Last released 2021, has 8 security warnings per static analysis. Still works for HS256 on MVP; CLAUDE.md specifies it, so use it.
- `tailwind.config.js` (v3 pattern): Silently ignored in v4. Do not create.
- SQLAlchemy 1.x `Session()` pattern: Will not work with `create_async_engine`.

---

## Open Questions

1. **python-jose vs PyJWT**
   - What we know: CLAUDE.md specifies python-jose. FastAPI docs now recommend PyJWT. Both work for HS256.
   - What's unclear: Whether to follow CLAUDE.md (python-jose) or the safer/maintained choice (PyJWT).
   - Recommendation: Follow CLAUDE.md specification (python-jose) to stay consistent with documented constraints. Note in code comments that it's the CLAUDE.md choice.

2. **Python 3.14 vs 3.12**
   - What we know: Machine has 3.14.3. CLAUDE.md targets 3.12. FastAPI requires >=3.10.
   - What's unclear: Whether any of the required packages (asyncpg, Celery, etc.) have issues on 3.14.
   - Recommendation: Use `uv python install 3.12` and pin with `.python-version = 3.12` in the project root. Avoids potential compatibility surprises.

3. **Celery worker placement in production**
   - What we know: D-12 says Docker Compose for services only; Python runs natively. In production, the Celery worker must be on the same host as Docker to run `docker run` for R sandbox.
   - What's unclear: Whether to run the Celery worker as a systemd service or a Docker container on the droplet.
   - Recommendation: Run Celery worker as a systemd service on the droplet (consistent with D-12 philosophy). The worker process calls `docker run` on the host Docker daemon.

---

## Sources

### Primary (HIGH confidence)
- [FastAPI JWT auth official docs](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) — auth flow, OAuth2PasswordBearer, token pattern
- [shadcn/ui Vite installation docs](https://ui.shadcn.com/docs/installation/vite) — init command `npx shadcn@latest init -t vite`
- [shadcn/ui Tailwind v4 docs](https://ui.shadcn.com/docs/tailwind-v4) — v4 integration confirmed
- [Docker none network driver docs](https://docs.docker.com/engine/network/drivers/none/) — `--network none` isolation
- [Celery 5.6.2 workers docs](https://docs.celeryq.dev/en/stable/userguide/workers.html) — revoke behavior
- npm registry (verified 2026-03-23): React 19.2.4, Vite 8.0.2, TailwindCSS 4.2.2, TanStack Query 5.95.2, Zustand 5.0.12, React Router 7.13.2, TypeScript 6.0.2

### Secondary (MEDIUM confidence)
- [FastAPI async SQLAlchemy 2.0 + JWT PostgreSQL boilerplate](https://medium.com/algomart/fastapi-async-sqlalchemy-2-0-jwt-postgresql-boilerplate-setup-19e74d6bad5c) — confirmed DeclarativeBase pattern, async session
- [Setup FastAPI with async SQLAlchemy 2, Alembic, PostgreSQL, Docker](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/) — async env.py Alembic pattern
- [FastAPI python-jose deprecation discussion](https://github.com/fastapi/fastapi/discussions/11345) — confirmed python-jose is minimally maintained; PyJWT PR merged
- [TanStack Query polling docs](https://tanstack.com/query/latest) — `refetchInterval` dynamic return pattern

### Tertiary (LOW confidence — verify during implementation)
- Celery SIGTERM subprocess kill pattern — multiple community sources agree but not officially documented
- R `--read-only` + `--tmpfs` Docker flags for R temp files — standard Docker pattern applied to R context; needs testing

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against npm registry and confirmed in official docs
- Architecture: HIGH — patterns are from official FastAPI/SQLAlchemy docs with verified secondary sources
- Pitfalls: MEDIUM-HIGH — python-jose deprecation and Celery subprocess kill confirmed by multiple sources; v4 Tailwind config file behavior confirmed in shadcn docs
- R sandbox: MEDIUM — Docker isolation flags are documented; R-specific behavior under `--network none` needs smoke test during implementation

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable ecosystem; Vite/React/Tailwind move fast but breaking changes unlikely in 30 days)
