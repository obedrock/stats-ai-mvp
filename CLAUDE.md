<!-- GSD:project-start source:PROJECT.md -->
## Project

**Stats-AI**

A web app that lets users describe statistical analyses in plain English and automatically runs them. Users type prompts like "Run a regression of GDP growth on interest rates and inflation from 2000 to 2023" and Stats-AI handles everything: pulling data from the right sources, cleaning and merging it, generating R code, executing the analysis, and returning results with plain-English interpretation and visualizations. Built for economists, researchers, students, and business analysts.

**Core Value:** The data acquisition and preparation pipeline must work reliably — automatically pulling, cleaning, merging, and transforming data from multiple sources so users never touch raw data. This is the hardest part and the core differentiator.

### Constraints

- **Tech Stack**: React frontend, Python/FastAPI backend, R via subprocess on server
- **AI**: Claude API for NLP → R code generation and result interpretation
- **Deployment**: Digital Ocean droplet
- **R Execution**: Server-side via subprocess (sandboxed)
- **MVP Priority**: Core loop (prompt → data → analysis → interpretation) must work end-to-end before polish
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 | Backend runtime | 3.12 is the fastest and most stable release currently; FastAPI 0.135+ requires >=3.10; 3.13 exists but third-party library support lags |
| FastAPI | 0.135.2 | HTTP API framework | Best async Python framework for data APIs; native Pydantic v2 validation; automatic OpenAPI docs; large ecosystem; standard choice for ML/AI backends in 2025 |
| R | 4.4.x (latest) | Statistical computation | The only credible environment for econometric analysis (lm, plm, sandwich, lmtest are R-native); no Python equivalent for panel regressions and diagnostic testing at this quality level |
| React | 19.x | Frontend UI | Specified; React 19 with concurrent features is the current stable |
| Vite | 8.0.1 | Frontend build tool | Now Rolldown-powered (replaced Rollup+esbuild); faster builds; standard React scaffolding; requires Node 20.19+ |
| PostgreSQL | 16.x | Primary database | Stores users, analysis history, cached datasets, shareable links; ACID-compliant; better JSON support than MySQL for storing analysis metadata |
| Redis | 7.x | Task queue broker + cache | Brokers Celery tasks (R execution jobs); caches frequently-used FRED/Yahoo datasets to cut API latency; standard pairing with Celery |
| Celery | 5.6.2 | Async task queue | R execution via subprocess is a long-running, CPU-bound operation — it blocks FastAPI's event loop if run inline; Celery offloads it to a worker process; Redis as broker |
### Data Sourcing Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yfinance | 1.2.0 | Yahoo Finance market data | All equity prices, ETF data, market indices; the 1.x redesign (Dec 2025) stabilized the API significantly after years of breakage |
| fredapi | 0.5.x | FRED macroeconomic data | St. Louis Fed series (GDP, CPI, interest rates, unemployment); requires free API key from fred.stlouisfed.org |
| pandas | 3.0.1 | Data cleaning and merging | Date alignment, frequency resampling, missing value handling, unit conversion; requires Python >=3.11; primary data manipulation layer |
| openpyxl | 3.1.x | Excel file parsing | User upload support for .xlsx files; used as pandas `engine="openpyxl"` for `pd.read_excel()` |
### R Statistical Packages (server-installed)
| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| lmtest | 0.9-40+ | Diagnostic tests (Breusch-Pagan, Durbin-Watson, RESET) | Updated July 2025; pairs with sandwich for robust SEs |
| sandwich | 3.x | Heteroskedasticity-consistent and HAC standard errors | Required for all econometric inference; HC3 is default |
| plm | 2.6-7 | Panel data regression (fixed/random effects, Hausman test) | Updated Nov 2025; covers all standard panel models |
| forecast | 8.23+ | ARIMA, ETS, ACF/PACF, stationarity | Standard for time series in R; includes auto.arima() |
| tseries | 0.10-x | ADF unit root tests, GARCH, cointegration | Engle-Granger cointegration test; ADF for stationarity |
| car | 3.x | VIF for multicollinearity, linearHypothesis | Companion Applied Regression; used for multicollinearity checks |
| ggplot2 | 3.5.x | Chart generation | Publication-quality static charts; used as base for plotly conversion |
| plotly (R) | 4.10.x | Interactive chart serialization | `ggplotly()` converts ggplot2 to Plotly JSON; that JSON is returned to the React frontend to render via react-plotly.js |
### Frontend Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| TypeScript | 5.x | Type safety | Always; catches prop errors in chart/table components early |
| TailwindCSS | 4.x | Utility CSS | Fast UI development without custom CSS files; standard with Vite+React |
| shadcn/ui | latest | Headless component primitives | Provides accessible table, dialog, tabs, badge components; fully customizable; not a black-box library |
| react-plotly.js | 2.6.x | Interactive chart rendering | Renders Plotly JSON emitted by R's `plotly::ggplotly()`; avoids re-implementing chart logic in JS |
| Zustand | 5.x | Client state management | Analysis history, prompt state, data preview toggles; lighter than Redux for this use case |
| React Router | 7.x | Client-side routing | Shareable analysis URLs, auth pages, history view |
| TanStack Query | 5.x | Server state / API fetching | Poll Celery job status (polling pattern); cache API responses; handle loading/error states for analysis runs |
### Backend Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy | 2.0.48 | ORM + async DB access | Async session management with asyncpg; models for users, analyses, datasets |
| Alembic | 1.18.4 | DB schema migrations | Schema version control; run `alembic upgrade head` on deploy |
| asyncpg | 0.30.x | Async PostgreSQL driver | Required for SQLAlchemy 2.0 async; significantly faster than psycopg2 for async workloads |
| Pydantic | 2.x | Request/response validation | Bundled with FastAPI 0.135+; validates prompts, user data, API responses |
| python-jose[cryptography] | 3.3.x | JWT encoding/decoding | Email+password auth token generation; HS256 algorithm |
| passlib[bcrypt] | 1.7.x | Password hashing | bcrypt for password storage; FastAPI's own docs recommend pwdlib+Argon2 as modern alternative, but passlib+bcrypt has more deployment history |
| python-multipart | 0.0.x | Multipart form data | Required by FastAPI for file uploads (UploadFile); install explicitly |
| aiofiles | 23.x | Async file I/O | Write uploaded files to temp storage without blocking |
| redis[hiredis] | 5.x | Redis client | hiredis extra gives 10x faster response parsing; used for cache + Celery backend |
| httpx | 0.27.x | Async HTTP client | Call FRED API and any external data endpoints; async-native unlike requests |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Python package manager | Dramatically faster than pip; lockfile support; use `uv pip install` and `uv run` |
| pytest + pytest-asyncio | Backend testing | Test FastAPI routes and Celery tasks; asyncio mode for async route tests |
| Ruff | Python linting + formatting | Replaces black + flake8; single tool; fast |
| vitest | Frontend unit testing | Vite-native; same config as Vite 8 |
| Docker | Local dev environment | Containerize PostgreSQL and Redis locally; avoid local service management |
## Installation
# Python backend (uv recommended)
# Dev dependencies
# Frontend
# R packages (install on server)
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Celery + Redis | FastAPI BackgroundTasks | Only for trivially short tasks (<1s); R execution takes 5-30s, which will timeout without a proper queue |
| Celery + Redis | ARQ (async task queue) | ARQ is simpler and async-native; viable if Celery feels too heavy after MVP, but Celery has more operational tooling (Flower monitoring) |
| pandas | polars | Prefer polars if datasets exceed 1M rows or if doing heavy multi-core transformations; for MVP-scale macro data (a few thousand rows), pandas is simpler and yfinance/fredapi return pandas DataFrames natively |
| plotly R + react-plotly.js | ggplot2 → PNG | Static PNGs are simpler but lose interactivity (hover, zoom); Plotly JSON roundtrip is the right call for this app's UX |
| PostgreSQL | SQLite | SQLite for solo local dev only; cannot handle concurrent Celery workers writing simultaneously |
| asyncpg | psycopg2 | psycopg2 works but is sync-only; forces SQLAlchemy into sync mode which blocks FastAPI's event loop |
| python-jose | PyJWT | PyJWT is lighter; python-jose is compatible with FastAPI's official OAuth2+JWT tutorial so less custom wiring |
| shadcn/ui | MUI / Chakra UI | MUI/Chakra are full design systems; shadcn gives more control and avoids opinionated styling that fights TailwindCSS |
| TanStack Query | SWR | Both work; TanStack Query has better support for polling intervals (needed for Celery job status) and more ergonomic cache invalidation |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| rpy2 for R integration | Runs R in-process via C bindings; complex build requirements; segfaults on memory errors crash the entire Python process; subprocess isolation is safer | subprocess with timeout + resource limits |
| Django | Overkill ORM and admin for this use case; async story was bolted on; FastAPI has cleaner async primitives for long-running analysis jobs | FastAPI |
| Node.js backend | Loses native Python data ecosystem (pandas, yfinance, fredapi all return DataFrames); R subprocess management is harder from Node | Python/FastAPI |
| Shiny / Plumber (R web framework) | Putting the web layer in R means poor async support, no proper auth primitives, harder deployment; use R only for computation | R via subprocess, Python for web layer |
| cloud R execution (OpenCPU, RStudio Connect) | Adds external dependency and cost; overkill for MVP scale on a single droplet; loses full control over the R environment | subprocess on same Digital Ocean droplet |
| pip without lockfile | Non-reproducible installs; dependency conflicts emerge on server | uv with uv.lock |
| Rechartsfor this app | Recharts is SVG-based and can't render R's plotly output natively; would require duplicating chart logic in JS | react-plotly.js to consume R plotly JSON |
| pandas 2.x | pandas 3.0 requires Python >=3.11 and drops several deprecated APIs; pin to 3.0.x from the start to avoid later upgrade pain | pandas 3.0.1 (just use the current version) |
## Stack Patterns by Variant
- Celery worker receives task with R script content
- Worker writes script to a temp file in an isolated directory
- `subprocess.run(["Rscript", script_path], timeout=60, capture_output=True)`
- Parse stdout (plotly JSON + coefficient tables) and stderr (R errors/warnings)
- Clean up temp files after each run
- Set resource limits (ulimit via Docker or systemd) to cap memory per R process
- Key format: `{source}:{series_id}:{start}:{end}` (e.g., `fred:GDP:2000-01-01:2023-12-31`)
- TTL: FRED data = 24h (daily updates at most); Yahoo Finance = 1h (intraday stale quickly)
- Cache in Redis with json-serialized pandas records
- Python layer detects mismatches after fetching data (e.g., daily SPY + quarterly GDP)
- Returns a `frequency_conflict` object to frontend before executing R
- Frontend shows modal with options: aggregate daily to quarterly, interpolate quarterly to daily, or abort
- User choice stored with analysis record for reproducibility
- Single Claude API call with system prompt containing: available data series (post-fetch), data schema, R environment packages available, and output format spec (must emit plotly JSON + named list of coefficients)
- Structured output (JSON mode or tool use) to guarantee parseable R code block
- Temperature 0 for deterministic code generation
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| FastAPI 0.135.2 | Pydantic 2.x, Python >=3.10 | Pydantic v1 support dropped; use Pydantic v2 model syntax |
| SQLAlchemy 2.0.48 | Alembic 1.18.4, asyncpg 0.30.x | SQLAlchemy 2.0 async requires `create_async_engine`; not backward compatible with 1.x session patterns |
| pandas 3.0.1 | Python >=3.11, openpyxl 3.1.x | Copy-on-Write is default in 3.0; chained assignments silently break; use `.copy()` explicitly |
| Celery 5.6.2 | Redis 7.x, Python >=3.9 | Use `celery[redis]` extra; avoid mixing RabbitMQ and Redis backends |
| react-plotly.js 2.6.x | plotly.js 2.x, React 18/19 | Pass R's `plotly_json()` output directly as `data` and `layout` props |
| Vite 8.0.1 | Node.js >=20.19, React 19 | Uses Rolldown bundler; @vitejs/plugin-react v6 drops Babel dependency |
| yfinance 1.2.0 | Python >=3.9, pandas 2+ | 1.x API is a significant redesign from 0.x; Ticker.history() interface stable |
## Sources
- FastAPI PyPI — version 0.135.2 confirmed: https://pypi.org/project/fastapi/ (HIGH confidence)
- anthropic PyPI — version 0.86.0 confirmed: https://pypi.org/project/anthropic/ (HIGH confidence)
- yfinance PyPI — version 1.2.0 confirmed: https://pypi.org/project/yfinance/ (HIGH confidence)
- Celery PyPI — version 5.6.2 confirmed: https://pypi.org/project/celery/ (HIGH confidence)
- SQLAlchemy PyPI — version 2.0.48 confirmed: https://pypi.org/project/sqlalchemy/ (HIGH confidence)
- Alembic PyPI — version 1.18.4 confirmed: https://pypi.org/project/alembic/ (HIGH confidence)
- pandas PyPI — version 3.0.1 confirmed: https://pypi.org/project/pandas/ (HIGH confidence)
- Vite 8 release announcement — https://vite.dev/blog/announcing-vite8 (HIGH confidence)
- plm CRAN — version 2.6-7, updated Nov 2025: https://cran.r-project.org/web/packages/plm/plm.pdf (HIGH confidence)
- lmtest CRAN — updated July 2025: https://cran.r-project.org/web/packages/lmtest/lmtest.pdf (HIGH confidence)
- R plotly JSON roundtrip pattern: https://plotly-r.com/overview.html (MEDIUM confidence — pattern is standard but integration details need testing)
- fredapi GitHub: https://github.com/mortada/fredapi (MEDIUM confidence — last major version update 2022; library is stable/feature-complete but not actively developed; viable alternative is fedfred 2.1.5 if async FRED access is needed)
- FastAPI security docs (JWT pattern): https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ (HIGH confidence)
- shadcn/ui Vite installation: https://ui.shadcn.com/docs/installation/vite (HIGH confidence)
## Open Questions
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
