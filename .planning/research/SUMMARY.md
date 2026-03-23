# Project Research Summary

**Project:** Stats-AI — AI-powered statistical analysis web app
**Domain:** Natural language → automated econometric analysis (NLP + R execution + data pipeline)
**Researched:** 2026-03-23
**Confidence:** HIGH

## Executive Summary

Stats-AI is an econometric analysis platform that takes natural language prompts, auto-pulls data from FRED and Yahoo Finance, executes R-based statistical analysis via a sandboxed subprocess, and returns plain-English interpretations alongside coefficient tables, diagnostic tests, and interactive charts. This type of product sits at the intersection of a data pipeline application, an LLM orchestration layer, and a statistical computing environment — all three of which have well-documented production patterns. The recommended approach is a FastAPI backend with Celery task queue for async R execution, PostgreSQL for persistence, Redis for caching and job brokering, and a React/TypeScript SPA frontend that polls for job status. The core differentiator — automatic multi-source data pull with transparent assumption handling — is absent from every comparable competitor (Julius AI, DataGPT, camelAI) and represents a genuine, verifiable gap in the market.

The most critical architectural decision is treating R execution as an async task from day one. R processes take 10–60 seconds, block the FastAPI event loop if run inline, and are a resource exhaustion vector without proper isolation. Celery + Redis is the correct infrastructure; retrofitting it after synchronous R execution is wired in is painful and frequently incomplete. Equally non-negotiable is the Docker sandboxing of the R subprocess — executing LLM-generated code without OS-level isolation is a CVE-2025-3248-class vulnerability. Both of these must be in place before any external access, not added in a later hardening phase.

The secondary risk is statistical correctness: the app must not silently make data alignment decisions or allow Claude to skip stationarity pre-checks before running time-series regressions. These produce results that look valid (coefficients, p-values, charts) but are methodologically wrong. The mitigation is a mandatory frequency-mismatch confirmation dialog in the data pipeline, and structured output from Claude that forces diagnostic test specification before analysis code. Both require upfront design discipline — they cannot be bolted on after the UX is set.

---

## Key Findings

### Recommended Stack

The stack is built around a Python/FastAPI backend calling R via subprocess, with a React frontend consuming the results. Python 3.12 + FastAPI 0.135.2 handles the web layer; Celery 5.6.2 with Redis 7.x handles async R execution; PostgreSQL 16.x stores all persistent state; pandas 3.0.1 handles data pipeline logic; yfinance 1.2.0 and fredapi 0.5.x are the data source libraries. On the R side, the core econometric packages are lmtest, sandwich, plm, forecast, tseries, and car — all current as of early 2026. The frontend is React 19 + Vite 8 + TypeScript + TailwindCSS 4 + shadcn/ui, with react-plotly.js consuming the Plotly JSON that R emits via `ggplotly()`. The stack is well-verified: all Python package versions confirmed via PyPI, R packages confirmed via CRAN.

The single critical avoidance: rpy2 must not be used for R integration. Running R in-process via C bindings crashes the entire Python process on R memory errors, and the build requirements are fragile. The subprocess isolation pattern is the correct approach for this product's scale and security requirements.

**Core technologies:**
- Python 3.12 + FastAPI 0.135.2: async HTTP API, Pydantic v2 validation, OpenAPI docs
- R 4.4.x via subprocess: the only credible runtime for panel regressions, Breusch-Pagan, VIF, and ARIMA at production quality
- Celery 5.6.2 + Redis 7.x: mandatory for async R execution; R takes 10–60s and cannot block the event loop
- PostgreSQL 16.x: users, analysis history, cached datasets, job status — ACID, JSON support
- React 19 + Vite 8 + TypeScript + TailwindCSS 4: frontend with TanStack Query for polling job status
- react-plotly.js 2.6.x: renders R's `plotly_json()` output natively; no chart logic duplication in JS
- pandas 3.0.1: data pipeline; note Copy-on-Write is default — use `.copy()` explicitly
- yfinance 1.2.0: 1.x redesign (Dec 2025) stabilized the API; use `auto_adjust=True`
- fredapi 0.5.x: stable but not actively developed; validate FRED series IDs before fetching

See `.planning/research/STACK.md` for full versions, alternatives considered, and compatibility notes.

### Expected Features

The competitive gap is real and verified: no competitor combines automatic multi-source public data pulls (FRED + Yahoo Finance), R-native execution, econometric diagnostic tests as standard output, and transparent assumption display. This product's differentiation is grounded in concrete research, not assertion.

**Must have (table stakes):**
- Natural language prompt input — the entire value proposition
- Plain-English result interpretation via Claude — all competitors do this; absence signals incomplete product
- Coefficient tables with standard errors, p-values, confidence intervals — expected by any stats-savvy user
- At least two chart types (time-series, residual) — bare numbers feel unfinished
- CSV/Excel file upload — universal expectation
- Generated R code visible and copyable — researchers need to reproduce and cite
- Email/password authentication — required for any persistent-state web app
- Analysis history — users reference prior work
- Plain-English error feedback when R fails — cryptic R errors destroy trust

**Should have (competitive differentiators):**
- Auto-pull from FRED + Yahoo Finance — the core differentiator; without it the product is Julius AI with R
- Frequency mismatch detection with user confirmation dialog — no competitor handles this; silent alignment produces invalid results
- Transparent assumption display (quick mode + detailed mode) — builds trust with the target audience of researchers
- Econometric diagnostic tests as standard output (Breusch-Pagan, Durbin-Watson, VIF) — expected by economists; absent from competitors
- Guided upload parsing with user confirmation of column types
- Shareable analysis link (prompt + data + results + code permalink)
- Cached datasets for cross-analysis reuse
- Model comparison across multiple specifications

**Defer (v2+):**
- Bayesian analysis (MCMC, brms) — long runtimes, harder to interpret automatically, validate demand first
- Team collaboration / multiplayer editing — shareable read-only links satisfy 80% of the use case
- API access for programmatic use — build UI loop well first
- Additional data sources (Bloomberg, World Bank WDI) — after FRED + Yahoo Finance are solid
- Real-time streaming data — not needed for regression/time-series econometrics; adds WebSocket + paid API complexity

See `.planning/research/FEATURES.md` for full prioritization matrix and competitor analysis.

### Architecture Approach

The architecture is a four-layer system: React SPA (HTTP polling) → FastAPI routers (thin, validation only) → Service layer (AnalysisOrchestrator, DataPipelineService, CodeGenService, RExecutorService, InterpretationService) → Celery workers + external services (PostgreSQL, Redis, FRED, Yahoo Finance, Claude API). The key design decision is that the HTTP layer is deliberately thin — routers enqueue jobs and return job IDs immediately; all logic lives in services; Celery workers coordinate the pipeline. Claude is called twice per analysis (Stage 1: code generation only; Stage 2: interpretation only after R has executed). This two-stage approach produces significantly better output than a single combined prompt.

The recommended build order is: DB models/migrations → Auth → Data source adapters → Data pipeline service → R executor → Code generation service → Interpretation service → Analysis orchestrator + Celery tasks → FastAPI routers → React frontend. The R executor and data pipeline can be built in parallel; Claude integration should be last (mock with hardcoded R scripts during earlier development).

**Major components:**
1. DataPipelineService — fetches, cleans, merges data from FRED/Yahoo Finance/uploads; canonical DataFrame schema; frequency mismatch detection
2. RExecutorService — writes R to temp file, subprocess.run with timeout + no shell=True, parses stdout (Plotly JSON + coefficients) and stderr
3. CodeGenService + InterpretationService — two focused Claude calls; structured output for code generation; interpretation runs after R output is received
4. Celery task chain — coordinates the pipeline outside the HTTP request cycle; Redis broker, PostgreSQL result store
5. React SPA with TanStack Query — polls GET /jobs/{job_id}/status every 2s; surfaces frequency mismatch resolution UI when job pauses

See `.planning/research/ARCHITECTURE.md` for full system diagram, data flow, project structure, and anti-patterns.

### Critical Pitfalls

1. **Unauthenticated R code execution via LLM output** — Docker container per R execution with no network access, no host mounts, non-root user. Block `system()`, `system2()`, `download.file()` via `.Rprofile` stubs. Regex/AST scan generated code before subprocess call. Never use `shell=True`. Must be in place before any external access — Phase 1.

2. **Silent data alignment producing statistically invalid results** — Detect frequency mismatch before merging (check median inter-observation gap). Surface confirmation dialog with explicit options (aggregate / interpolate / restrict to common dates). Log every alignment decision in results pane. Never silently forward-fill across gaps larger than the native frequency — Phase 1.

3. **LLM selecting the wrong statistical test (spurious regression)** — Force structured output from Claude: `{ "precondition_tests": [...], "rationale": "...", "analysis_code": "..." }`. Enforce ADF test before any time-series OLS. Show assumption test outcomes alongside results — Phase 2.

4. **FRED data revisions introducing look-ahead bias** — Document "current vintage" in UI whenever FRED data is used. Offer ALFRED real-time vintage option for backtesting. Never describe FRED-based analyses as "backtests" without surfacing the revision caveat — Phase 1.

5. **R subprocess resource exhaustion** — Hard 60s timeout on every subprocess call. Docker memory caps (512MB per R process). Celery job queue before any multi-user deployment. Rate-limit analysis endpoint per user — Phase 1.

See `.planning/research/PITFALLS.md` for the full list including yfinance data quality issues, performance traps, security mistakes, and UX pitfalls.

---

## Implications for Roadmap

Based on research, the dependency graph forces a specific build order: security and infrastructure before features, data pipeline before analysis engine, analysis engine before interpretation and UI polish. The research explicitly maps pitfalls to phases, and the architecture document provides a recommended component build order. Suggested 5-phase structure:

### Phase 1: Infrastructure, Security, and Data Pipeline

**Rationale:** Auth, the job queue, R sandbox, and the data pipeline are prerequisites for everything else. Pitfalls 1, 2, 4, 5, and 6 (the most catastrophic failures) all occur in this phase if not addressed here. The ARCHITECTURE.md build order lists DB → Auth → Data source adapters → Data pipeline as the first four steps — these belong together.

**Delivers:** Working user accounts; FRED + Yahoo Finance data fetch with caching; data quality checks; frequency mismatch detection + confirmation dialog; CSV/Excel upload with guided parsing; data preview; sandboxed R subprocess with timeout and resource limits; Celery job queue with Redis; FRED vintage caveat in UI.

**Addresses features:** Auth, automatic data pull (FRED + Yahoo Finance), frequency mismatch handling, transparent assumption display (data alignment decisions), data preview, file upload with guided parsing, cached datasets.

**Must avoid:** Running R on host without Docker (never acceptable). Silent data alignment (must build confirmation flow at the same time as merge logic). subprocess without timeout. Any FRED fetch without vintage metadata.

**Research flag:** Standard patterns (well-documented); no additional research phase needed.

---

### Phase 2: Core Analysis Engine

**Rationale:** Once data flows reliably, wire the analysis pipeline: R executor → Claude code generation → R execution → interpretation. The Claude integration should be last in the backend build (mock with hardcoded scripts during Phase 1 development). Pitfall 3 (spurious regression from wrong test selection) must be addressed here in the system prompt design — it cannot be retrofitted after the UX assumes a certain output structure.

**Delivers:** OLS regression with full diagnostic output (Breusch-Pagan, Durbin-Watson, VIF, Shapiro-Wilk); plain-English interpretation via Claude; coefficient tables with standard errors, p-values, CIs; two chart types (time-series, residual) via R's ggplotly → react-plotly.js; generated R code visible and copyable; plain-English error feedback for R failures; structured Claude output with mandatory precondition tests for time-series data.

**Addresses features:** Natural language prompt, OLS regression, diagnostic tests, plain-English interpretation, coefficient table, visualizations, R code display, error feedback.

**Must avoid:** Single combined Claude prompt for code gen + interpretation. Executing Claude's R output without validation gate. Synchronous R execution in the FastAPI route handler. Starting interpretation before R has returned actual output.

**Research flag:** Needs deeper research during planning. The Claude system prompt engineering for structured output (precondition test enforcement, analysis-type-specific prompts, R code validation before execution) is the highest-risk technical element. Recommend `/gsd:research-phase` on the Claude → R code generation loop before implementation.

---

### Phase 3: Analysis History, Persistence, and Sharing

**Rationale:** History and shareable links depend on completed analysis records, which depend on Phase 2. These features require a stable analysis schema — building them before the analysis output format is final causes schema churn. The FEATURES.md dependency graph confirms: shareable links require auth (Phase 1) + history (this phase).

**Delivers:** Analysis history list (past prompts + results per user); shareable read-only analysis permalink (full result: prompt + data + assumptions + code + charts); history stores exact fetched dataset hash + vintage date (not just prompt text) for reproducibility.

**Addresses features:** Analysis history, shareable analysis links, data preview toggle.

**Must avoid:** History that stores only prompts without dataset snapshots (users get different results on re-run due to FRED revisions). Shareable links that only restore the prompt without the full result.

**Research flag:** Standard patterns (URL-based sharing and history pagination are well-documented); no additional research phase needed.

---

### Phase 4: Extended Analysis Types

**Rationale:** Once OLS is validated with real users, extend to logistic regression, panel data (plm: fixed/random effects, Hausman test), and time-series regression (ARIMA, VAR via forecast + tseries packages). Panel data is high-demand from economists. ARIMA adds meaningful depth for macro users. These are additive to Phase 2 infrastructure — no architectural changes required.

**Delivers:** Logistic regression; panel data regression (fixed effects, random effects, Hausman test); time-series regression (ARIMA, auto.arima); model comparison across specifications (AIC/BIC, F-tests, pseudo-R2); extended diagnostic outputs per model type.

**Addresses features:** Logistic regression, panel regression, time-series regression, model comparison.

**Must avoid:** Applying OLS system prompt to panel/time-series without analysis-type-specific precondition rules. Rolling out ARIMA without testing spurious regression safeguards on non-stationary data.

**Research flag:** Panel data and time-series analysis engine design may benefit from `/gsd:research-phase` — the Claude system prompt requirements for each analysis type are distinct, and the R packages (plm, forecast, tseries) have non-trivial output formats that need mapping to the result schema.

---

### Phase 5: Performance, Polish, and Scale

**Rationale:** After validated core product. Addresses the three identified scaling bottlenecks: R cold start time, external API rate limits (already mitigated by Phase 1 caching but needs monitoring), and UX latency feedback. Also adds streaming progress updates which the PITFALLS.md identifies as a UX pitfall (users abandon silent 30-second analyses).

**Delivers:** Streaming progress updates ("Fetching FRED data... Done. Generating R code... Running analysis..."); R process warm pool to eliminate cold start overhead; performance monitoring and rate-limit dashboards; refinements to assumption display and interpretation quality; cached dataset management UI.

**Addresses features:** UX feedback, performance, cached dataset reuse visibility.

**Research flag:** R process warm pool / persistent R process may benefit from `/gsd:research-phase` — the rpy2 vs persistent subprocess vs pre-warmed Docker container tradeoffs require validation at the chosen deployment scale.

---

### Phase Ordering Rationale

- Security (R sandbox, auth) must precede any external or multi-user access — cannot be added later without a rebuild
- Data pipeline must be complete and tested before wiring Claude, because code generation quality depends on having a reliable data schema
- The frequency mismatch flow and FRED vintage metadata must be built alongside their respective integrations, not added as polish afterward
- History and sharing depend on a stable analysis output schema — building them before Phase 2 is complete causes schema churn
- Extended analysis types are additive — they reuse Phase 2 infrastructure and should come after OLS is validated with real users
- Performance and polish belong last; premature optimization before user validation wastes effort

### Research Flags

Needs `/gsd:research-phase` during planning:
- **Phase 2** — Claude → R code generation: structured output format, precondition test enforcement in system prompt, R code validation gate, and analysis-type-specific prompt design are the highest technical risk area; sparse documentation on production-grade LLM → R pipelines
- **Phase 4** — Extended analysis type prompts: panel data and ARIMA output schemas from R need careful mapping; the Claude system prompt requirements differ substantially per analysis type
- **Phase 5** — R process pool: rpy2 vs persistent subprocess vs pre-warmed Docker container tradeoffs need benchmarking at MVP scale

Phases with standard patterns (skip research phase):
- **Phase 1** — Data pipeline + infrastructure: Celery + Redis, SQLAlchemy async, yfinance, fredapi, file upload are all well-documented
- **Phase 3** — History and sharing: CRUD history and UUID-keyed shareable links are standard patterns

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All Python package versions confirmed via PyPI (2026-03-23); R packages confirmed via CRAN; Vite 8 confirmed via official release blog |
| Features | MEDIUM-HIGH | Competitor feature matrix verified via multiple 2025-2026 sources; Julius AI, DataGPT, camelAI feature sets cross-referenced across independent reviews; some forward-looking assumptions about user behavior |
| Architecture | MEDIUM-HIGH | Patterns drawn from established FastAPI + Celery production guides and R subprocess security research; Plotly JSON roundtrip pattern confirmed but "needs testing" per STACK.md sources |
| Pitfalls | HIGH (critical), MEDIUM (performance/UX) | Critical pitfalls grounded in CVEs, official security advisories, and FRED/yfinance official documentation; performance and UX pitfalls based on community consensus |

**Overall confidence:** HIGH for technical decisions; MEDIUM-HIGH for product scope

### Gaps to Address

- **fredapi maintenance**: mortada/fredapi is not actively developed. Validate during Phase 1 that it handles the required FRED endpoint calls. If issues arise, evaluate `pyfredapi` (full endpoint coverage) or `fedfred` (async-native). Plan B should be identified before implementation, not during.

- **R plotly JSON size**: Plotly JSON blobs can be 1–5MB for large datasets. Test whether result caching in Redis (beyond input data caching) is needed to avoid regenerating charts on page refresh. Decide the caching strategy before Phase 3 (shareable links) is built.

- **pandas 3.0 Copy-on-Write**: All data pipeline code must be explicitly tested against pandas 3.0 semantics. Chained assignment patterns silently produce wrong results. Include pandas 3.0 CoW behavior in data pipeline integration tests from Phase 1.

- **FRED series ID hallucination**: Claude will occasionally generate non-existent FRED series IDs. The FRED `/series` endpoint must be called to validate series existence before fetching observations. This validation logic should be a defined Phase 1 deliverable, not an afterthought.

- **R subprocess security at public scale**: Docker isolation is adequate for MVP with a known user base. Before opening to untrusted public users, a formal security review of the R sandbox (seccomp syscall filter, Docker network policy) is needed. Flag this explicitly in the roadmap as a pre-public-launch gate.

---

## Sources

### Primary (HIGH confidence)
- FastAPI PyPI (0.135.2 verified): https://pypi.org/project/fastapi/
- Celery PyPI (5.6.2 verified): https://pypi.org/project/celery/
- SQLAlchemy PyPI (2.0.48 verified): https://pypi.org/project/sqlalchemy/
- pandas PyPI (3.0.1 verified): https://pypi.org/project/pandas/
- yfinance PyPI (1.2.0 verified): https://pypi.org/project/yfinance/
- Alembic PyPI (1.18.4 verified): https://pypi.org/project/alembic/
- anthropic PyPI (0.86.0 verified): https://pypi.org/project/anthropic/
- Vite 8 release announcement: https://vite.dev/blog/announcing-vite8
- plm CRAN (2.6-7, Nov 2025): https://cran.r-project.org/web/packages/plm/plm.pdf
- lmtest CRAN (Jul 2025): https://cran.r-project.org/web/packages/lmtest/lmtest.pdf
- CVE-2025-3248 (Langflow RCE): https://www.offsec.com/blog/cve-2025-3248/
- FastAPI security docs (JWT): https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- shadcn/ui Vite installation: https://ui.shadcn.com/docs/installation/vite
- Cloud Security Alliance — LLM code execution risks (2025): https://cloudsecurityalliance.org/blog/2025/06/03/llms-writing-code-cool-llms-executing-it-dangerous
- FRED data revisions — St. Louis Fed: https://www.stlouisfed.org/publications/page-one-economics/2022/08/01/data-revisions-with-fred
- FRED new API version (Nov 2025): https://news.research.stlouisfed.org/2025/11/fred-launches-new-version-of-api/

### Secondary (MEDIUM confidence)
- Julius AI features (2025): https://julius.ai/articles/13-powerful-features-that-make-julius-ai-the-top-data-analysis-tool
- DataGPT review 2025: https://research.com/software/reviews/datagpt
- camelAI blog (2026): https://camelai.com/blog/7-best-ai-powered-data-analysis-tools-for-non-tech
- TestDriven.io FastAPI + Celery: https://testdriven.io/blog/fastapi-and-celery/
- FastAPI best practices (GitHub): https://github.com/zhanymkanov/fastapi-best-practices
- R plotly JSON roundtrip pattern: https://plotly-r.com/overview.html
- Redis cache-aside tutorial: https://redis.io/tutorials/howtos/solutions/microservices/caching/
- Look-ahead bias in LLM economic queries — Federal Reserve Board (2025): https://www.federalreserve.gov/econres/feds/files/2025044pap.pdf
- yfinance data quality observations: https://medium.com/@Tobi_Lux/data-from-yfinance-some-observations-41e99d768069

### Tertiary (LOW confidence / needs validation)
- fredapi GitHub (last major update 2022 — stable but inactive): https://github.com/mortada/fredapi — validate during Phase 1 implementation; have pyfredapi or fedfred as fallback

---
*Research completed: 2026-03-23*
*Ready for roadmap: yes*
