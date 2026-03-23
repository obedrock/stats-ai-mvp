# Architecture Research

**Domain:** AI-powered statistical analysis web application
**Researched:** 2026-03-23
**Confidence:** MEDIUM-HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (React SPA)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Prompt Input │  │ Results View │  │ History / Auth UI    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼─────────────────┼──────────────────────┼───────────────┘
          │ HTTP/REST        │ Polling / SSE         │
┌─────────▼─────────────────▼──────────────────────▼───────────────┐
│                    FastAPI Application Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  │
│  │  /analysis  │  │  /data      │  │  /auth      │  │ /jobs   │  │
│  │  router     │  │  router     │  │  router     │  │ router  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬────┘  │
│         │                │                │              │        │
│  ┌──────▼──────────────────────────────────────────────┐ │        │
│  │                  Service Layer                       │ │        │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │ │        │
│  │  │AnalysisOrch│  │DataPipeline│  │CodeGenService│   │ │        │
│  │  └─────┬──────┘  └──────┬─────┘  └──────┬───────┘   │ │        │
│  └────────┼────────────────┼───────────────┼───────────┘ │        │
└───────────┼────────────────┼───────────────┼─────────────┘        │
            │                │               │
┌───────────▼────────────────▼───────────────▼─────────────────────┐
│                       Worker Layer (Celery)                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  DataFetchWorker │  │  R ExecutorWorker│  │  InterpretWorker │ │
│  └──────┬───────────┘  └────────┬─────────┘  └──────────────────┘ │
└─────────┼──────────────────────┼────────────────────────────────── ┘
          │                      │
┌─────────▼──────────────────────▼──────────────────────────────────┐
│                       External / Storage Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐    │
│  │PostgreSQL│  │  Redis   │  │  FRED    │  │  Yahoo Finance  │    │
│  │(main DB) │  │(cache/q) │  │  (API)   │  │  (yfinance)     │    │
│  └──────────┘  └──────────┘  └──────────┘  └─────────────────┘    │
│  ┌──────────────────────┐  ┌───────────────────────┐               │
│  │  Filesystem/S3-like  │  │  Claude API           │               │
│  │  (uploaded files,    │  │  (code gen +          │               │
│  │   R script output)   │  │   interpretation)     │               │
│  └──────────────────────┘  └───────────────────────┘               │
└────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| React SPA | Prompt submission, result display, auth, history | FastAPI (HTTP REST) |
| FastAPI Routers | HTTP request validation, response serialization, auth guards | Service Layer |
| AnalysisOrchestrator | Coordinates end-to-end analysis job lifecycle | DataPipeline, CodeGenService, R Executor, Celery |
| DataPipelineService | Fetches, cleans, merges, and transforms data from all sources | FRED, yfinance, uploaded files, PostgreSQL cache |
| CodeGenService | Builds Claude prompt from analysis intent + cleaned data schema, parses response | Claude API |
| R ExecutorService | Writes R script to temp file, invokes R subprocess with timeout and resource limits, captures stdout/stderr | Subprocess (R runtime) |
| InterpretationService | Sends R output back to Claude for plain-English explanation | Claude API |
| Celery Workers | Run DataFetch + R execution + interpretation tasks outside the request cycle | Redis (broker), PostgreSQL (result store) |
| Redis | Job queue broker, dataset cache (short TTL), session data | Celery workers, FastAPI |
| PostgreSQL | Persistent store for users, analysis history, cached datasets, job status | FastAPI, Celery workers |

## Recommended Project Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI app factory, startup hooks
│   ├── config.py             # Settings via pydantic-settings
│   ├── dependencies.py       # Shared DI (db session, current user)
│   │
│   ├── routers/
│   │   ├── analysis.py       # POST /analysis, GET /analysis/{id}
│   │   ├── jobs.py           # GET /jobs/{job_id}/status
│   │   ├── data.py           # POST /data/upload, GET /data/preview
│   │   └── auth.py           # POST /auth/register, /auth/login
│   │
│   ├── services/
│   │   ├── orchestrator.py   # Coordinates analysis pipeline
│   │   ├── data_pipeline.py  # Source adapters + merge/clean logic
│   │   ├── code_gen.py       # Claude prompt construction + parsing
│   │   ├── r_executor.py     # Subprocess wrapper with timeout/limits
│   │   └── interpreter.py    # Claude result interpretation
│   │
│   ├── tasks/                # Celery task definitions
│   │   ├── celery_app.py     # Celery instance + config
│   │   ├── analysis_tasks.py # main analysis task chain
│   │   └── data_tasks.py     # data fetch / cache warm tasks
│   │
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── analysis.py
│   │   └── dataset.py
│   │
│   ├── schemas/              # Pydantic request/response schemas
│   │   ├── analysis.py
│   │   ├── data.py
│   │   └── auth.py
│   │
│   ├── data_sources/         # Pluggable source adapters
│   │   ├── base.py           # Abstract DataSource interface
│   │   ├── fred.py           # FRED API adapter
│   │   ├── yahoo.py          # yfinance adapter
│   │   └── upload.py         # User CSV/Excel/JSON parser
│   │
│   └── core/
│       ├── security.py       # JWT utils, password hashing
│       ├── db.py             # SQLAlchemy session factory
│       └── cache.py          # Redis client, cache decorators
│
├── r_scripts/
│   ├── template.R            # Base R environment loader (packages)
│   └── sandbox_runner.R      # Wrapper that sources generated script
│
frontend/
├── src/
│   ├── components/
│   │   ├── PromptInput/
│   │   ├── ResultsPanel/
│   │   ├── DataPreview/
│   │   └── AnalysisHistory/
│   ├── hooks/
│   │   ├── useAnalysis.ts    # Submit + poll job status
│   │   └── useDataSources.ts # Source selection state
│   ├── api/                  # Typed API client (axios/fetch wrappers)
│   └── pages/
│       ├── Home.tsx
│       └── Analysis.tsx
```

### Structure Rationale

- **services/ vs routers/:** Routers own HTTP request/response only. All business logic lives in services, keeping endpoints thin and unit-testable without HTTP context.
- **data_sources/:** A pluggable adapter pattern isolates source-specific quirks (rate limits, date formats, units). Adding a new source means a new adapter file, not touching core logic.
- **tasks/:** Celery task definitions are separate from services. Tasks call services — they are coordination wrappers, not logic holders. This keeps Celery-specific retry/state code from bleeding into business logic.
- **r_scripts/:** R execution environment configuration lives here, version-controlled alongside the application.

## Architectural Patterns

### Pattern 1: Job Queue for Analysis Execution

**What:** Analysis requests are not processed synchronously within the HTTP request cycle. The API accepts a request, enqueues a Celery task, and immediately returns a job ID. The frontend polls `GET /jobs/{job_id}/status` until complete.

**When to use:** Any operation that takes longer than ~2-3 seconds. R execution for real analyses can take 10-60 seconds. This pattern prevents HTTP timeouts and allows the server to handle concurrent users without blocking.

**Trade-offs:** Adds Celery + Redis infrastructure complexity. Worth it even for MVP — synchronous R execution under concurrent load will break the app quickly.

**Example:**

```python
# router: thin, just enqueue and return
@router.post("/analysis")
async def submit_analysis(request: AnalysisRequest, db: Session = Depends(get_db)):
    job = analysis_tasks.run_analysis.delay(request.dict())
    return {"job_id": job.id, "status": "queued"}

# task: coordinates the pipeline
@celery_app.task(bind=True, max_retries=2)
def run_analysis(self, request_data: dict):
    try:
        data = data_pipeline.fetch_and_merge(request_data)
        r_code = code_gen.generate(request_data, data.schema)
        result = r_executor.run(r_code, data)
        interpretation = interpreter.explain(result)
        db_session.save(Analysis(job_id=self.request.id, result=result, ...))
    except Exception as exc:
        self.retry(exc=exc, countdown=5)
```

### Pattern 2: Two-Stage Claude Interaction

**What:** Claude is called twice per analysis: once to generate R code, once to interpret results. These are separate, focused calls — not one giant prompt.

**When to use:** Always. Combining code generation and interpretation in one prompt produces lower-quality output on both. Focused prompts with clear output format constraints produce reliable, parseable responses.

**Trade-offs:** Two API calls per analysis (2x cost, 2x latency). Acceptable because each call is faster and more reliable than a combined call. Latency is hidden inside the async job.

**Example:**

```python
# Stage 1: Code generation
def generate_r_code(intent: str, data_schema: dict) -> str:
    prompt = build_codegen_prompt(intent, data_schema)
    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}],
        system="You are an expert R statistician. Return ONLY valid R code..."
    )
    return extract_r_code_block(response.content[0].text)

# Stage 2: Interpretation (called after R execution)
def interpret_results(intent: str, r_output: str, assumptions: dict) -> str:
    prompt = build_interpretation_prompt(intent, r_output, assumptions)
    response = anthropic.messages.create(...)
    return response.content[0].text
```

### Pattern 3: Data Source Adapter with Cache Layer

**What:** Each external data source (FRED, Yahoo Finance, uploads) implements a common interface: `fetch(series_id, start, end) -> pd.DataFrame`. A caching decorator checks Redis (short TTL, ~1 hour) then PostgreSQL (longer TTL, dataset table) before calling the external API.

**When to use:** Always. FRED and Yahoo Finance have rate limits. Repeated analyses on the same datasets (common in iterative research workflows) should not re-fetch external data.

**Trade-offs:** Cache invalidation complexity. Mitigated by using explicit TTL rather than invalidation. Users can force-refresh via override.

```python
class FREDDataSource(BaseDataSource):
    def fetch(self, series_id: str, start: str, end: str) -> pd.DataFrame:
        cache_key = f"fred:{series_id}:{start}:{end}"
        if cached := redis_cache.get(cache_key):
            return pd.read_json(cached)
        df = fred_client.get_series(series_id, start, end)
        redis_cache.setex(cache_key, 3600, df.to_json())
        return df
```

### Pattern 4: R Subprocess with Strict Resource Controls

**What:** R is invoked via `subprocess.run()` with explicit `timeout`, `stdout=PIPE`, `stderr=PIPE`, and no `shell=True`. The generated script is written to a temp file, executed, temp file cleaned up.

**When to use:** Every R execution call without exception.

**Trade-offs:** No shell=True means no shell injection. The timeout prevents runaway computations. Resource limits (CPU/memory via `resource` module preexec_fn) add additional protection.

```python
import subprocess, tempfile, os, resource

def run_r_script(r_code: str, data_path: str, timeout: int = 60) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".R", mode="w", delete=False) as f:
        f.write(r_code)
        script_path = f.name
    try:
        result = subprocess.run(
            ["Rscript", "--vanilla", script_path],
            capture_output=True, text=True,
            timeout=timeout,
            # No shell=True — prevents injection
        )
        return {"stdout": result.stdout, "stderr": result.stderr,
                "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"error": "execution_timeout", "limit_seconds": timeout}
    finally:
        os.unlink(script_path)
```

## Data Flow

### Primary Analysis Request Flow

```
User submits prompt
    ↓
POST /analysis  (FastAPI router)
    ↓
AnalysisOrchestrator.submit()
    ↓ enqueue
Celery: run_analysis task
    ├── DataPipelineService.fetch_and_merge()
    │       ├── Detect sources from prompt (FRED / Yahoo / upload)
    │       ├── Check Redis cache → check DB dataset cache → fetch external API
    │       ├── Align frequencies (flag mismatch → pause for user if needed)
    │       ├── Apply cleaning (missing values, date alignment, unit conversion)
    │       └── Return merged pd.DataFrame + schema metadata
    │
    ├── CodeGenService.generate(intent, schema, assumptions_mode)
    │       ├── Build structured prompt with data schema + intent
    │       ├── Claude API call (code generation)
    │       └── Extract + validate R code block from response
    │
    ├── RExecutorService.run(r_code, data_path)
    │       ├── Write data to temp CSV
    │       ├── Inject data path into R script
    │       ├── subprocess.run(["Rscript", script], timeout=60)
    │       └── Parse stdout (JSON results), stderr (diagnostics)
    │
    └── InterpretationService.explain(intent, r_output, assumptions)
            ├── Claude API call (interpretation)
            └── Return plain-English explanation + key findings

Job result stored in PostgreSQL (analyses table)
    ↓
Frontend polls GET /jobs/{job_id}/status
    ↓ (status = complete)
GET /analysis/{id} → return full result to UI
```

### Frequency Mismatch Handling Flow

```
DataPipelineService detects mismatched frequencies
    (e.g., daily Yahoo data + quarterly FRED data)
    ↓
Job paused, status = "awaiting_user_input"
    ↓
Frontend receives "awaiting_user_input" status + options
    (interpolate / aggregate / align to lower frequency)
    ↓
User selects option → PATCH /jobs/{job_id}/resolution
    ↓
Celery task resumes with user choice
```

### State Management (Frontend)

```
AnalysisContext (React Context or Zustand)
    ↓ (submit action)
useAnalysis hook
    ├── POST /analysis → store job_id
    ├── Poll GET /jobs/{job_id}/status every 2s
    │       ↑ exponential backoff after 30s
    ├── On "awaiting_user_input" → surface resolution UI
    └── On "complete" → fetch result → update display state
```

### Key Data Flows

1. **Dataset cache flow:** FRED/Yahoo data cached in Redis (TTL 1hr) and PostgreSQL datasets table (TTL 24hr). Cache key includes series ID + date range. Repeated analyses on same data avoid external calls.
2. **Generated code visibility:** R code string stored in the analysis record. Frontend retrieves and displays it. No re-generation needed for copy/inspect.
3. **Upload flow:** File uploaded to server filesystem → parsed to DataFrame → schema inferred → user confirms column mappings → stored as dataset record → treated same as API-sourced data downstream.
4. **Analysis sharing:** Shareable links resolve to GET /analysis/{id} with `public=True` flag check. No re-computation — results are fully stored.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 users | Single Digital Ocean droplet. Celery with 2-4 workers. Redis and PostgreSQL on same machine. Acceptable. |
| 100-1k users | Separate Redis to managed Redis (DO Managed Databases). Add Celery worker processes. Consider R worker pool (pre-warmed R processes avoid startup overhead per job). |
| 1k-10k users | Separate PostgreSQL to managed instance. Consider horizontal Celery workers. R startup time becomes the key bottleneck — R worker pool or persistent R process (rpy2) becomes important. |
| 10k+ users | R execution pool, read replicas for history/sharing queries, CDN for static assets, separate services for data pipeline vs analysis execution. |

### Scaling Priorities

1. **First bottleneck:** R startup time. Each `Rscript` invocation loads the R runtime + packages (~2-5s cold start). At scale, pre-warm a pool of R processes or use rpy2 for in-process R execution. For MVP, subprocess per job is acceptable.
2. **Second bottleneck:** External API rate limits (FRED: 120 req/min, Yahoo Finance: unofficial and fragile). Dataset caching is mandatory, not optional. Build it in Phase 1.
3. **Third bottleneck:** Claude API latency (P90 ~3-8s per call, 2 calls per analysis). This is largely irrelevant to scale — the async job pattern hides it. The cost scales linearly with usage, not the architecture.

## Anti-Patterns

### Anti-Pattern 1: Synchronous R Execution in HTTP Handler

**What people do:** Call `subprocess.run(["Rscript", ...])` directly inside the FastAPI route handler, making the HTTP request wait for R to finish.

**Why it's wrong:** R analyses take 10-60+ seconds. HTTP connections time out. Under concurrent load, the FastAPI event loop blocks (subprocess.run is blocking), starving other requests. No retry capability if R crashes.

**Do this instead:** Always dispatch R execution to a Celery worker. Return job_id immediately. Poll for status.

### Anti-Pattern 2: Building One Giant Claude Prompt

**What people do:** Send the full user prompt, data schema, analysis intent, expected output format, and interpretation instructions in a single Claude call.

**Why it's wrong:** Longer prompts produce lower instruction-following reliability. Code generation and interpretation are fundamentally different tasks — conflating them in one prompt produces mediocre output on both. Hard to debug when output is malformed.

**Do this instead:** Two-stage Claude interaction: Stage 1 = code generation only (system prompt: be an R statistician, output only valid R), Stage 2 = interpretation only (system prompt: explain these statistical results in plain English).

### Anti-Pattern 3: Trusting Claude's R Code Without Validation Gate

**What people do:** Execute whatever R code Claude returns immediately, with no validation step.

**Why it's wrong:** Claude occasionally generates syntactically invalid R, references variables that don't exist in the data, or uses packages not installed in the R environment. Silent failures produce confusing empty output.

**Do this instead:** Parse the R code block before execution. Check for package references against a whitelist. Use R's `parse()` for syntax validation before `eval()`. Return structured error to Claude for one auto-retry if execution fails (include stderr in the retry prompt).

### Anti-Pattern 4: Ad-hoc Data Cleaning Per Source

**What people do:** Write source-specific cleaning code scattered across fetch functions — different date parsing for FRED vs Yahoo, different column naming conventions, different NA handling.

**Why it's wrong:** The merge step becomes a fragile matrix of special cases. Adding a new source requires touching merge logic throughout. Frequency mismatch handling becomes impossible to centralize.

**Do this instead:** Each data source adapter outputs a canonical DataFrame schema: `{date: datetime64, value: float64, series_id: str, source: str, frequency: str}`. All cleaning happens inside the adapter before return. The merge layer works with canonical schema only.

### Anti-Pattern 5: shell=True in Subprocess Call

**What people do:** `subprocess.run(f"Rscript {script_path}", shell=True, ...)` because it looks simpler.

**Why it's wrong:** Shell injection. If any file path or parameter reaches the shell string, it can be exploited. On a server executing AI-generated code, defense in depth matters.

**Do this instead:** Always pass command as a list: `subprocess.run(["Rscript", "--vanilla", script_path], ...)`. Never use `shell=True` for external code execution.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Claude API (Anthropic) | Direct HTTP via `anthropic` Python SDK, called from service layer | Two calls per analysis. Use structured output prompting. Store raw responses for debugging. Rate limit: 1M tokens/min on Sonnet tier. |
| FRED API | REST via `fredapi` Python library or direct HTTP | Free API key required. Rate limit ~120 req/min. Cache all fetches. Series discovery from prompt needs synonym mapping (e.g., "GDP" → GDPC1). |
| Yahoo Finance | `yfinance` Python library (unofficial API) | No API key. Fragile — breaks periodically. Cache aggressively. Ticker symbol extraction from prompt is non-trivial. |
| Digital Ocean Droplet | Single VM deployment, systemd services for FastAPI + Celery workers | R must be installed on droplet with required packages pre-loaded. Use requirements.R script in deploy. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| FastAPI ↔ Celery | Redis message broker (task enqueue), PostgreSQL (result store) | Job IDs link HTTP layer to async layer. FastAPI never imports task implementation directly — only task name strings. |
| Celery Workers ↔ R Runtime | subprocess.run() with temp files | Workers write data to temp CSV, R script reads from path. stdout/stderr captured as strings. All temp files cleaned up after execution. |
| DataPipeline ↔ Claude | No direct connection | Claude only sees data schema/column names, not raw data. Data is passed to R script directly. This avoids token cost and privacy issues of sending data to Claude. |
| Frontend ↔ Backend | REST HTTP with JSON | No WebSocket for MVP — polling every 2-3s is sufficient. SSE is a clean upgrade path for streaming R output lines if needed later. |
| Service Layer ↔ DB | SQLAlchemy ORM with async sessions | Services receive db session via FastAPI Depends() injection. Never instantiate sessions inside service functions. |

## Build Order Implications

Build in this dependency order to avoid blocking:

1. **Database models + migrations** — everything persists to PostgreSQL; needed before any service can save state
2. **Auth (user model, JWT, login/register)** — gate all endpoints from the start; retrofitting auth is painful
3. **Data source adapters (canonical schema)** — the pipeline foundation; code gen and R execution both depend on knowing the data shape
4. **Data pipeline service (merge + clean)** — depends on adapters; needed before R execution makes sense
5. **R executor service** — can be built and tested in isolation with hand-written R scripts before code gen is ready
6. **Code generation service (Claude Stage 1)** — depends on data schema output from pipeline
7. **Interpretation service (Claude Stage 2)** — depends on R executor output
8. **Analysis orchestrator + Celery tasks** — wires steps 3-7 into a coordinated job chain
9. **FastAPI routers + job status polling** — thin HTTP layer over the orchestrator
10. **React frontend** — builds against the completed API

The R executor and data pipeline can be developed in parallel (steps 3-5 are independent of each other). The Claude integration (steps 6-7) should be last in the backend build — it can be mocked with hardcoded R scripts during development of earlier steps.

## Sources

- FastAPI background task patterns: [TestDriven.io FastAPI + Celery](https://testdriven.io/blog/fastapi-and-celery/), [Practical Background Processing Guide](https://blog.greeden.me/en/2025/12/02/practical-background-processing-with-fastapi-a-job-queue-design-guide-with-backgroundtasks-and-celery/)
- FastAPI project structure: [FastAPI Best Practices (GitHub)](https://github.com/zhanymkanov/fastapi-best-practices), [FastAPI Production Structure Guide](https://www.zestminds.com/blog/fastapi-project-structure/)
- Subprocess security patterns: [Sandboxed Code Execution for AI Agents](https://www.bluebag.ai/blog/sandboxed-code-execution-security), [Python Subprocess Security](https://www.sourcery.ai/vulnerabilities/python-lang-security-audit-dangerous-subprocess-use-audit/)
- LLM code execution sandbox: [LLM Sandbox patterns](https://amirmalik.net/2025/03/07/code-sandboxes-for-llm-ai-agents), [Running LLM-Generated Code Safely](https://www.daytona.io/dotfiles/running-llm-generated-code-safely-langchain-daytona-demo)
- Multi-source financial data pipeline: [Production financial data pipeline (GitHub)](https://github.com/martinkilombe/financial-data-pipeline), [yfinance FastAPI service pattern](https://github.com/Vorckea/yfinance-service)
- Caching patterns: [Redis Cache-Aside Tutorial](https://redis.io/tutorials/howtos/solutions/microservices/caching/), [Postgres vs Redis Caching](https://leapcell.io/blog/choosing-between-postgres-materialized-views-and-redis-application-caching)
- React polling patterns: [Polling in React](https://dev.to/tangoindiamango/polling-in-react-3h8a), [Async REST task management](https://zuplo.com/learning-center/asynchronous-operations-in-rest-apis-managing-long-running-tasks)

---
*Architecture research for: AI-powered statistical analysis web application (Stats-AI)*
*Researched: 2026-03-23*
