# Pitfalls Research

**Domain:** AI-powered statistical analysis web app (NLP → R code → data pipeline → results)
**Researched:** 2026-03-23
**Confidence:** HIGH (critical pitfalls), MEDIUM (performance/UX pitfalls)

---

## Critical Pitfalls

### Pitfall 1: Unauthenticated R Code Execution via LLM Output

**What goes wrong:**
Claude generates R code from a user prompt, that code is passed to a Python subprocess, and the subprocess executes it on the server with the same OS-level permissions as the application process. A malicious or cleverly phrased prompt (prompt injection) can cause Claude to generate R code that reads server files, spawns shell commands (`system()` in R), exfiltrates environment variables including API keys, or downloads and runs remote payloads.

**Why it happens:**
The R language has `system()`, `system2()`, `readLines()`, `download.file()`, and `write()` built in. Claude will generate these if the prompt asks for something that sounds innocent — "fetch supplementary data from this URL" or "save results to a CSV". There is no built-in output sanitization layer between Claude's text output and the subprocess call.

CVE-2025-3248 (Langflow) is the canonical example: an AI-coding tool used Python `exec()` on LLM output without sanitization, leading to unauthenticated RCE on the host.

**How to avoid:**
- Run R in a Docker container with no network access, no host filesystem mounts, CPU/memory/time limits, and a non-root user.
- Maintain an allowlist of permitted R packages and block `system()`, `system2()`, `Sys.setenv()`, `download.file()`, and file-write functions at the R process level (via a startup `.Rprofile` that overwrites these with error-throwing stubs).
- Validate Claude's output before execution: scan generated code for blocked function calls using a regex/AST check before passing to subprocess.
- Never use `shell=True` in the Python subprocess call. Pass R script path as a list argument: `subprocess.run(["Rscript", script_path], ...)`.
- Do not include API keys or secrets in the subprocess environment — pass them separately and only to Python-side code.

**Warning signs:**
- Generated R code contains `system(`, `download.file(`, `readLines("http`, or references to `/etc/`, `~/.ssh`, or environment variables.
- No Docker isolation in place; R runs as the application user directly on the host.
- `shell=True` anywhere near the subprocess invocation.

**Phase to address:**
Phase 1 (Core loop infrastructure) — must be in place before any public or beta access. Security cannot be retrofitted.

---

### Pitfall 2: Silent Data Alignment Producing Statistically Invalid Results

**What goes wrong:**
Yahoo Finance returns daily data (trading days only, no weekends/holidays). FRED returns quarterly GDP data. When the app merges them on a date index without user confirmation, it silently forward-fills or drops observations. The merged dataset looks valid and produces results, but the regression coefficients reflect the alignment decision rather than the economic relationship. Users trust the output because it has a p-value and a chart.

**Why it happens:**
Pandas `merge()` and `join()` on datetime indices silently produce NaN rows or drop mismatched dates — the developer sees no error. The app "works" in a demo with a single data source. The bug only surfaces when cross-source merging is attempted, by which point the design may already assume silent alignment.

**How to avoid:**
- Detect frequency mismatch before merging: check the median inter-observation gap for each series and flag when series frequencies differ by more than 2x.
- When a mismatch is detected, surface a confirmation step with explicit options: aggregate (e.g., "use monthly average of daily data?"), interpolate ("linearly interpolate quarterly data to monthly?"), or restrict to common observations ("use only dates present in both series?").
- Log and display every alignment decision in the results pane: "GDP data was aggregated from quarterly to monthly by taking the last observation in each quarter."
- Never silently forward-fill across gaps larger than the natural frequency of the lower-frequency series.

**Warning signs:**
- Merge logic uses `pd.merge()` or `.join()` without a frequency-check guard before it.
- Test dataset uses two same-frequency sources; multi-frequency tests have never been run.
- The app produces analysis results for a "GDP vs daily stock price" query with no user interaction.

**Phase to address:**
Phase 1 (Data pipeline) — this is the stated core differentiator. Build the mismatch-detection and confirmation flow at the same time as the merge logic, not afterward.

---

### Pitfall 3: LLM Selecting the Wrong Statistical Test (Silent Methodological Error)

**What goes wrong:**
A user asks "Is there a relationship between interest rates and inflation?" Claude generates an OLS regression on two non-stationary time series. The regression shows R² = 0.87, p < 0.001. The result is a textbook spurious regression — the series are both trending upward and are not cointegrated. The app presents this as a meaningful finding with a plain-English interpretation saying "interest rates strongly predict inflation."

**Why it happens:**
LLMs are trained to produce statistically-sounding outputs. They know OLS syntax. They do not reliably check preconditions — stationarity (ADF/KPSS test), cointegration (Johansen/Engle-Granger), or homoskedasticity. The model's training data contains more examples of "run a regression" than "run a unit root test first, then decide whether to difference, cointegrate, or use an error-correction model."

Research confirms LLMs optimize for syntactic and semantic plausibility over factual/methodological accuracy — hallucination is a structural property, not an edge case.

**How to avoid:**
- Build a pre-analysis decision tree into the Claude system prompt: before generating regression code, Claude must explicitly state which diagnostic tests it is running first and why. Enforce this via structured output (JSON schema: `{ "precondition_tests": [...], "rationale": "...", "analysis_code": "..." }`).
- Run mandatory pre-checks in R for time series data: ADF test for stationarity, Durbin-Watson for autocorrelation. If preconditions fail, Claude must regenerate with the appropriate transformation (first-differencing, log transform, or ARIMA).
- In the results display, always show assumption test outcomes alongside the main results. A Durbin-Watson of 0.3 should render a visible warning, not just a coefficient table.
- Include in the system prompt explicit rules: "For any time series regression, always run an ADF test first. If either series is non-stationary, do not run OLS — run a cointegration test and use the appropriate model."

**Warning signs:**
- Generated R code goes directly to `lm()` without any diagnostic preamble for time series data.
- No structured output validation between Claude's response and R execution.
- Plain-English interpretation never mentions assumption tests.
- Test prompts only use cross-sectional data; time series edge cases have not been exercised.

**Phase to address:**
Phase 2 (Analysis engine) — the system prompt engineering and structured output schema for the Claude → R pipeline must be designed here, not bolted on later.

---

### Pitfall 4: FRED Data Revisions Introducing Look-Ahead Bias

**What goes wrong:**
A user asks for analysis using GDP or unemployment data. The app fetches from FRED using the default endpoint, which returns the most recently revised vintage of every series. If the analysis covers a historical period (e.g., 2000–2010), the values returned are the 2024-revised numbers, not the values that were known at the time. An analysis that uses revised data will appear more precise than any model could have been in real time, and users comparing results to published research from that period will get different numbers.

**Why it happens:**
FRED's default API endpoint (`/series/observations`) returns the latest revised values. ALFRED (Archival FRED) provides vintage-specific data, but it requires a different API parameter (`realtime_start`, `realtime_end`). Most tutorials and examples use the default FRED endpoint.

**How to avoid:**
- Document in the app UI that FRED data uses "current vintage" (latest revisions) by default, not real-time vintage.
- For analyses involving forecasting validation or policy backtesting, surface a "use real-time vintage data" option using the ALFRED API.
- In the plain-English interpretation, include a disclaimer when FRED data is used: "Note: GDP values reflect the most recent FRED revision, which may differ from data available at the time."
- Do not describe historical FRED-based analyses as "backtests" without surfacing the revision caveat.

**Warning signs:**
- The app uses `fredapi` with no `realtime_start` parameter and presents results as a "backtest."
- No UI mention of data vintages or revisions.
- User queries mentioning "real-time" or "what was known at the time" receive standard FRED data.

**Phase to address:**
Phase 1 (Data pipeline) — add a metadata field to every fetched series indicating data vintage policy. Add the UI caveat at the same time the FRED integration is built.

---

### Pitfall 5: R Subprocess Resource Exhaustion Taking Down the Server

**What goes wrong:**
A user submits a prompt that generates R code processing a large dataset or running a computationally expensive analysis (e.g., a rolling regression over 20 years of daily data, or a bootstrap with 10,000 iterations). The R process runs indefinitely, consuming all available RAM on the Digital Ocean droplet. The server becomes unresponsive for all users. Alternatively, two concurrent users each trigger an R subprocess simultaneously, and combined memory consumption exceeds available RAM, causing OOM kills.

**Why it happens:**
`subprocess.run()` by default blocks the Python process until R completes — there is no timeout. On a single droplet, R runs in the same memory space as the application. Without resource caps, a single R job can consume all available memory. This is not hypothetical: every R subprocess call is a potential DoS vector.

**How to avoid:**
- Always call R via `subprocess.run(..., timeout=60)` with a hard timeout. Catch `subprocess.TimeoutExpired` and return a user-facing error with a suggestion to narrow the date range.
- Use `ulimit` or Docker resource constraints to cap per-R-process memory (e.g., 512MB) and CPU time.
- Run R subprocess calls in FastAPI using `run_in_threadpool` — never directly inside an `async def` route, which would block the event loop for all users.
- Implement a job queue (e.g., Celery + Redis) before going to any multi-user deployment. Without a queue, two simultaneous analyses on a 2GB droplet will OOM.
- Set a concurrent-analysis limit per user session (max 1 in-flight analysis per user).

**Warning signs:**
- `subprocess.run()` called directly inside an `async def` FastAPI route handler.
- No `timeout` argument on the subprocess call.
- No queue or concurrency limit — second user can trigger analysis while first is running.
- Droplet RAM is less than 4x the expected largest dataset size.

**Phase to address:**
Phase 1 (Core loop infrastructure) — timeout and threadpool execution must be in place from the first working analysis. The job queue can be added in Phase 2 before multi-user exposure.

---

### Pitfall 6: yfinance Data Quality Issues Silently Corrupting Analysis

**What goes wrong:**
yfinance returns split-adjusted close prices by default but the adjustment quality is inconsistent — some series have identical Open/High/Low/Close values on certain days, some tickers have gaps for non-trading periods that are not flagged as missing, and delisted tickers return no data (survivorship bias — historical constituents that were acquired or went bankrupt simply disappear). Timezone handling is inconsistent between global tickers. The app uses this data directly, and the user has no visibility into these quality issues.

**Why it happens:**
yfinance is a third-party scraper of Yahoo Finance's undocumented internal API. It is not a licensed data feed. Yahoo makes no guarantees about data quality, and the library has open issues about data discrepancies versus exchange reference data (documented deviations up to 11% in XETRA data comparisons). Auto-adjustment (`auto_adjust=True`) addresses splits/dividends but does not fix underlying data quality.

**How to avoid:**
- Always use `auto_adjust=True` and `back_adjust=False` (which is the default) to get split/dividend-adjusted prices.
- Run a data quality check on every fetched series: flag days where O=H=L=C (suspect data), flag gaps larger than 5 trading days, flag series with fewer than 80% of expected observations.
- Surface data quality warnings in the UI before running analysis: "Warning: AAPL data has 3 suspicious trading days flagged."
- Document that yfinance data is sourced from Yahoo Finance and may differ from exchange reference data.
- Do not use yfinance for analyses requiring tick-level precision, intraday data older than 30 days (hard API limit), or delisted ticker history.

**Warning signs:**
- No post-fetch data quality validation before passing data to analysis.
- User prompts involving index constituents (e.g., "S&P 500 stocks") receive no survivorship bias warning.
- Intraday analysis uses yfinance for data older than 30 days.

**Phase to address:**
Phase 1 (Data pipeline) — add quality checks at fetch time, co-located with the yfinance integration.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Run R directly on host (no Docker) | Faster setup, no containerization | Full host exposure to LLM-generated code; unrecoverable security incident | Never |
| Pass Claude output directly to subprocess without validation | Simpler pipeline | Any prompt injection succeeds; first malicious prompt hits the system | Never |
| Use pandas `merge()` without frequency mismatch check | Simpler data pipeline code | Statistically invalid results that look correct; silent, no error | Never |
| `subprocess.run()` inside `async def` without threadpool | Works in single-user testing | Blocks FastAPI event loop; all users experience timeouts during any analysis | Never for production; ok in solo dev |
| No timeout on R subprocess | Simpler error handling | One long-running analysis OOMs the server | Never in production |
| Forward-fill all NaN values on merge | No NaN errors in R | Time series analysis is silently invalid (fabricated observations) | Only if the merge gap is <= 1 observation |
| Single Claude API call for both code gen and interpretation | Fewer API round-trips | Interpretation is generated before R actually runs; errors in R are post-hoc rationalized | Never — interpretation must run after R output is received |
| Hardcode R package list at server startup | Simpler dependency management | R fails silently if a package Claude uses is not installed; error surfaces at runtime for users | Acceptable in MVP if package list is audited and frozen |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FRED API | Fetch `observations` endpoint without `realtime_start`, present as historical data | Document "current vintage" default; offer ALFRED real-time vintage for backtesting |
| FRED API | Assume series ID is stable and well-known to Claude | Claude may hallucinate FRED series IDs. Always validate that a series ID exists before fetching (use `/series` endpoint to verify) |
| yfinance | Use `Ticker.history()` without checking for empty DataFrame | Delisted or wrong tickers return empty DataFrames silently; check `.empty` before proceeding |
| yfinance | Request intraday data older than 30 days for 1m interval | Hard API limit returns empty or error; document the constraint and surface it to users |
| yfinance | Use unadjusted close prices for return calculations | Always use `auto_adjust=True`; unadjusted prices produce incorrect returns around splits/dividends |
| Claude API | Include raw user-uploaded data in the system prompt | Tokens explode with large CSVs; user data should be described (schema + sample rows), not included verbatim |
| Claude API | Use same prompt template for all analysis types | Time series, cross-sectional, and panel data each require different precondition checks; use analysis-type-specific system prompts |
| R subprocess | Capture stdout only, discard stderr | R warnings (non-fatal) and errors both appear on stderr; always capture both and parse stderr for diagnostics |
| R subprocess | Rely on R's default package load on each subprocess call | Cold R subprocess startup takes 2-5 seconds per call; consider persistent R process or pre-loaded environment for latency |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous R subprocess in async FastAPI route | Second user gets no response while first analysis runs | Use `run_in_threadpool` + thread pool; add Celery job queue before multi-user | Immediately with 2 concurrent users |
| No caching of external data fetches | Every analysis re-fetches FRED/yfinance; rate limits hit quickly | Cache fetched series by (source, ticker/series_id, date_range) with TTL; Redis or disk-based | At ~20 analyses/hour hitting same data |
| Cold R process per analysis | 3-5 second overhead per request from R startup | Consider a persistent R process pool (using `subprocess.Popen` with persistent stdin/stdout) or rpy2 for common operations | Noticeable immediately; painful at 10+ analyses/day |
| Large CSV upload stored in memory | Server RAM consumed by uploaded file during analysis | Stream to disk, process in chunks; never hold full upload in memory | At ~50MB uploads or concurrent users |
| Returning full R output as JSON | Large datasets produce huge API payloads | Summarize results server-side; only return statistics, not raw data vectors | At ~1000 row datasets |
| No R process cleanup on timeout | Zombie R processes accumulate, consuming memory | Always `process.kill()` on timeout; use context managers for subprocess lifecycle | After ~10 timed-out analyses |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| LLM-generated code executed without sandboxing | Full server compromise via prompt injection (CVE-2025-3248 class) | Docker container per R execution, no network, no host mounts, non-root user |
| R `system()` and `system2()` not blocked | Shell command execution from within R code | Override in `.Rprofile` startup: `system <- function(...) stop("system() is not permitted")` |
| API keys in subprocess environment | FRED/Yahoo API keys readable by R code via `Sys.getenv()` | Pass API keys only to Python-side fetcher; R code never touches credentials |
| User-uploaded file passed directly to R `read.csv()` | Path traversal if filename is user-controlled | Generate a UUID-named temp file server-side; never use user-provided filename in R code |
| R code written to a predictable temp path | Race condition if two analyses share a filename | Use `tempfile()` in Python (`uuid4()`) per analysis; isolate in per-analysis directory |
| No rate limiting on analysis endpoint | Resource exhaustion attack; one user submits 100 analyses in parallel | Rate-limit to N analyses per user per minute; require authentication before analysis |
| Prompt injection via user-uploaded data | Malicious CSV cell contains "Ignore previous instructions and..." | Never include raw uploaded data in the LLM context; only include schema and sample statistics |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Analysis runs silently for 30+ seconds with no feedback | Users abandon, submit duplicates, or assume it crashed | Stream progress updates: "Fetching FRED data... Done. Generating R code... Running analysis..." |
| Assumption decisions made silently (log transform, differencing) | User cannot trust or reproduce results | Surface every transformation decision in results pane; Quick mode shows them after, Detailed mode shows them before |
| Plain-English interpretation with no uncertainty caveat | Non-statisticians treat p=0.04 as proof of causation | Always pair interpretation with assumption test outcomes; flag when preconditions were borderline |
| Results appear immediately but use wrong analysis type | User doesn't notice (wrong test for data type) | Show which statistical test was used prominently; let user override and rerun |
| Frequency mismatch silently resolved | User does not know their daily/quarterly merge was aggregated | Always show a "data alignment" summary section in results: what was done to each series |
| Error messages show raw R stderr | Intimidating for non-technical users; useless for business analysts | Catch R errors, pass to Claude for plain-English explanation of what went wrong |
| Analysis history stores prompts but not parameters | User reruns "the same" analysis but gets different results because FRED data was revised | History must store the exact fetched dataset (or a hash + vintage date) alongside the prompt |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **R code execution:** Works in dev (single user, no malicious input) — verify Docker sandbox, function allowlist, and timeout are all active before any external access.
- [ ] **Data merging:** Returns a merged DataFrame without errors — verify that multi-source, multi-frequency merges trigger the user confirmation flow (not just same-source merges).
- [ ] **FRED integration:** Returns data — verify that the series ID Claude generated actually exists by calling the FRED `/series` endpoint before fetching observations.
- [ ] **Plain-English interpretation:** Produces readable text — verify that the interpretation is generated *after* R execution with actual R output, not as a pre-execution prediction.
- [ ] **Time series regression:** Produces coefficients and p-values — verify that stationarity tests ran and their results are visible in the output.
- [ ] **User upload:** Parses a CSV successfully — verify that column type detection is shown to the user for confirmation before analysis, not silently assumed.
- [ ] **Cached datasets:** Reuses data across analyses — verify cache key includes the full date range and source parameters, not just the ticker name.
- [ ] **Shareable links:** URL loads the analysis — verify the link restores the full result including assumptions and diagnostics, not just the prompt text.

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Server compromised via R code injection | HIGH | Rotate all API keys immediately; audit logs for exfiltration; rebuild server from scratch; forensics on R scripts that ran |
| Silent data alignment produced invalid published results | HIGH | Identify all analyses using affected merge path; notify users; add explicit alignment disclosure; consider invalidating shared links from affected period |
| Spurious regression surfaced to users | MEDIUM | Add stationarity pre-check and re-run affected analysis types; add warning banner on affected historical results |
| Server OOM from R subprocess | MEDIUM | Restart droplet; add Docker memory limits + timeout immediately; implement job queue before next multi-user session |
| FRED hallucinated series ID returned error | LOW | R stderr caught and displayed; user-facing message "Could not find data series — try rephrasing or specifying the series ID"; log the failed ID for monitoring |
| yfinance returns empty data for delisted ticker | LOW | Detect empty DataFrame post-fetch; return user-facing error: "Could not retrieve data for [TICKER] — it may be delisted. Try specifying a date range before the delisting date." |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Unauthenticated R code execution | Phase 1 (Core loop) | Penetration test: submit a prompt asking R to read `/etc/passwd`; verify it fails safely |
| Silent data alignment | Phase 1 (Data pipeline) | Integration test: merge daily and quarterly series; verify confirmation dialog appears |
| Wrong statistical test selection | Phase 2 (Analysis engine) | Test suite: submit a prompt with two trending time series; verify ADF test runs before OLS |
| FRED data revision / look-ahead bias | Phase 1 (Data pipeline) | Check that UI shows "current vintage" disclaimer whenever FRED data is used |
| R subprocess resource exhaustion | Phase 1 (Core loop) | Load test: submit 3 concurrent analyses; verify second and third queue or reject, server remains responsive |
| yfinance data quality | Phase 1 (Data pipeline) | Test: fetch a known data-quality-problematic ticker; verify warning surfaces in UI |
| FastAPI event loop blocking | Phase 1 (Core loop) | Test: confirm R subprocess runs via `run_in_threadpool`; other endpoints respond during analysis |
| Prompt injection via user data | Phase 3 (User uploads) | Red team test: upload CSV with injection payload in a cell; verify it never reaches LLM context verbatim |

---

## Sources

- [Secure Boundaries: Understanding LLM Sandbox Environments — Sandgarden](https://www.sandgarden.com/learn/llm-sandbox)
- [LLMs Writing Code? Cool. LLMs Executing It? Dangerous — Cloud Security Alliance (2025)](https://cloudsecurityalliance.org/blog/2025/06/03/llms-writing-code-cool-llms-executing-it-dangerous)
- [CVE-2025-3248: Unauthenticated RCE in Langflow via Python exec — OffSec](https://www.offsec.com/blog/cve-2025-3248/)
- [Code Sandboxes for LLMs and AI Agents — Amir Malik (2025)](https://amirmalik.net/2025/03/07/code-sandboxes-for-llm-ai-agents)
- [Use subprocess securely — OpenStack Security Guidelines](https://security.openstack.org/guidelines/dg_use-subprocess-securely.html)
- [AI vs human code gen report: AI code creates 1.7x more issues — CodeRabbit](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report)
- [Data from yfinance — some observations — Medium / Tobi Lux](https://medium.com/@Tobi_Lux/data-from-yfinance-some-observations-41e99d768069)
- [The Insider's Guide to Clean Financial Market Data with Python and Yahoo Finance — PyQuantNews](https://www.pyquantnews.com/free-python-resources/insiders-guide-to-clean-financial-market-data-with-python-and-yahoo-finance)
- [Data Revisions with FRED — St. Louis Fed (2022)](https://www.stlouisfed.org/publications/page-one-economics/2022/08/01/data-revisions-with-fred)
- [FRED Launches New Version of API — St. Louis Fed (November 2025)](https://news.research.stlouisfed.org/2025/11/fred-launches-new-version-of-api/)
- [Look-ahead bias in LLM economic data queries — Federal Reserve Board (2025)](https://www.federalreserve.gov/econres/feds/files/2025044pap.pdf)
- [Time Series Regression IV: Spurious Regression — MATLAB/Simulink](https://www.mathworks.com/help/econ/time-series-regression-iv-spurious-regression.html)
- [Avoiding Common Mistakes with Time Series — SVDS](https://www.svds.com/avoiding-common-mistakes-with-time-series/)
- [How the Event Loop Handles Async and Sync Requests in FastAPI — Medium](https://medium.com/@nikhillad01/how-the-event-loop-handles-async-and-sync-requests-in-fastapi-94c292c9376a)
- [Running Blocking ML Operations in FastAPI — apxml.com](https://apxml.com/courses/fastapi-ml-deployment/chapter-5-async-operations-performance/running-blocking-ml-operations)
- [Prompt Injection and the Security Risks of Agentic Coding Tools — Secure Code Warrior](https://www.securecodewarrior.com/article/prompt-injection-and-the-security-risks-of-agentic-coding-tools)
- [When Prompts Go Wrong: Evaluating Code Model Robustness — arXiv 2507.20439](https://arxiv.org/html/2507.20439)

---
*Pitfalls research for: AI-powered statistical analysis web app (Stats-AI)*
*Researched: 2026-03-23*
