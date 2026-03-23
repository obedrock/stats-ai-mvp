# Feature Research

**Domain:** AI-powered statistical analysis web app (natural language → R → interpreted results)
**Researched:** 2026-03-23
**Confidence:** MEDIUM-HIGH (competitor landscape verified via web; some assumptions from PROJECT.md cross-referenced with market evidence)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Natural language prompt input | This is the entire value proposition — users come because they don't want to write code | LOW | The interface is a text box; the complexity is in what happens after |
| Plain-English result interpretation | Tools like Julius AI and DataGPT both do this; users expect the AI to explain what the numbers mean, not just print them | MEDIUM | Must handle uncertainty honestly — avoid confident-sounding hallucinations |
| Coefficient tables with standard errors, p-values, CIs | Any stats-savvy user will immediately check these; missing them signals amateur product | LOW | R outputs these natively; formatting for web display is the work |
| At least one chart per analysis | Every competitor (Julius AI, DataGPT, ThoughtSpot) generates visualizations automatically; bare numbers feel unfinished | MEDIUM | Scatter, residual, time-series; interactive via Plotly/ggplot2 rendered as SVG/PNG |
| CSV/Excel file upload | Universal expectation for any data tool; primary data entry point for researchers | LOW | Guided column-mapping adds polish but core upload is simple |
| Generated R code visible and copyable | Researchers and students need to reproduce, extend, or cite their work; hidden code feels like a black box | LOW | Syntax-highlighted code block with copy button |
| Authentication (login/signup) | Any web app with persistent state and user data needs auth | LOW | Email/password with JWT; no need for OAuth in MVP |
| Analysis history | Users reference prior work, share methodology, or re-run analyses; losing history = re-do from scratch | MEDIUM | Simple list of past prompts + results per user account |
| Error feedback when analysis fails | R can fail for many reasons (singular matrix, non-convergence, bad data); cryptic errors destroy trust | MEDIUM | Translate R error messages into actionable plain-English guidance |
| Basic data preview before analysis | Users need confidence the data loaded correctly before running expensive analysis | LOW | Show first N rows of merged/cleaned dataset; already in PROJECT.md as optional toggle |

### Differentiators (Competitive Advantage)

Features that set this product apart. Competitors either lack these entirely or do them poorly.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Automatic multi-source data pull (FRED + Yahoo Finance) | Julius AI, DataGPT, and camelAI all require the user to upload data; none auto-pull from FRED or Yahoo Finance by prompt context. This is the stated core differentiator in PROJECT.md and it is genuinely absent from competitors | HIGH | Requires reliable series detection from NL prompt, API integrations with FRED and Yahoo Finance, and graceful fallback when series cannot be found |
| Transparent assumption display (quick/detailed modes) | Other tools make silent data decisions (log transforms, lag structures, frequency alignment) and bury them in footnotes. Showing assumptions — and letting users approve them — builds trust with the researchers and economists who are the target audience | HIGH | Two-mode system (quick defaults + explanation vs. explicit approval before run) maps directly to the "stats-savvy" vs. "student/analyst" user spectrum |
| Frequency mismatch detection with user confirmation | Multi-source data at different frequencies (daily OHLC vs. quarterly GDP) is a known hard problem. Silent interpolation or aggregation can silently invalidate an analysis. Asking the user is the correct behavior and competitors don't do this | MEDIUM | Prompt user when daily/monthly/quarterly series are merged; offer options (aggregate, interpolate, align to lower frequency) with plain-English explanation of trade-offs |
| Econometric diagnostic tests as standard output | OLS diagnostics (Breusch-Pagan, Durbin-Watson, VIF, Shapiro-Wilk) are expected by economists but treated as optional add-ons elsewhere. Outputting them automatically signals the product understands its domain | MEDIUM | R packages `lmtest`, `car`, `sandwich` handle this; surfacing results in plain English is the differentiator |
| Model comparison support | Researchers routinely run multiple specifications; no competitor streamlines this in a conversational flow | HIGH | Compare AIC/BIC, F-tests, or pseudo-R2 across models within a session |
| Shareable analysis link | Researchers need to share results with advisors, collaborators, or in papers; a permalink to a full analysis (prompt + data + results + charts + code) is high-value and low-cost | MEDIUM | URL-based sharing with read-only view; does not require collaboration editing |
| Cached datasets for cross-analysis reuse | Users who run multiple analyses on the same underlying data (e.g., different FRED series for a paper) should not re-download and re-clean on each prompt | MEDIUM | Cache keyed by source + date range + series ID; invalidate on explicit user action |
| Guided upload parsing with user confirmation | Julius AI struggles with ambiguous column headers. A guided parsing step (AI proposes column types + roles, user confirms) reduces hallucination risk on user-provided data | MEDIUM | Show proposed mapping; allow user to override variable type, date format, unit |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem desirable but create more problems than they solve at this stage.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time streaming data | "I want live stock prices" sounds useful | Adds WebSocket complexity, requires subscription-tier API access (Yahoo Finance's streaming is not free), and statistical analyses rarely need tick-level data | Batch pulls with a user-specified date range are correct for regression, time series, and most econometric work; document this trade-off clearly |
| Team collaboration / multiplayer editing | Multi-user sounds like growth | Requires complex concurrent-edit logic, permission systems, conflict resolution; the "final 20% taking 80% of time" problem — and the target user is a solo researcher or student | Shareable read-only links satisfy 80% of the collaboration use case; defer real collaboration to v2 if validated |
| User-installable R packages | Power users will ask for this | Arbitrary package installation is a sandbox security nightmare and breaks reproducibility guarantees; package version drift breaks saved analyses | Maintain a curated, versioned R environment; add packages based on user demand, not on request |
| Bayesian analysis | Researchers will ask for it | Bayesian methods (MCMC, stan, brms) have very long run times, are far harder to interpret automatically, and require more domain knowledge from the AI layer. Frequentist methods cover 95% of the target audience's needs | Defer to v2; flag as a roadmap item to validate demand before building |
| API access for programmatic use | Developer-minded users will request it | Adds authentication surface area, rate-limiting, documentation burden, and SDK maintenance; MVP must validate core UX before exposing it as a platform | Build the UI loop well first; an API becomes straightforward once the backend is stable |
| Custom dashboards / BI-style reports | Looks like a natural extension | Turns the product into a BI tool (competing with Tableau/Power BI) rather than an analysis tool; dashboard builders are high-effort and distract from the core "run analysis on demand" loop | Shareable links and downloadable charts satisfy the reporting need for MVP |
| AI-generated paper drafts / LaTeX export | Researchers may ask for write-up help | Writing assistance is a separate product category; poorly done it trains users to distrust the core analysis output | Provide clean, copyable coefficient tables and an accessible R code block; let researchers write their own prose |

---

## Feature Dependencies

```
[Auth / User accounts]
    └──requires──> [Analysis history]
    └──requires──> [Cached datasets]
    └──requires──> [Shareable analysis links]

[Automatic data pull (FRED + Yahoo Finance)]
    └──requires──> [Frequency mismatch detection]
    └──requires──> [Transparent assumption display]
    └──enables──>  [Multi-source data merge]

[Multi-source data merge]
    └──requires──> [Frequency mismatch detection + user confirmation]
    └──requires──> [Automatic data cleaning pipeline]

[Guided upload parsing]
    └──enhances──> [Multi-source data merge]  (user-uploaded data as a third source)

[Natural language prompt input]
    └──requires──> [Claude API integration (NL → R code)]
    └──requires──> [Automatic data pull OR user upload]

[R code execution]
    └──requires──> [Sandboxed server-side R subprocess]
    └──enables──>  [Coefficient tables]
    └──enables──>  [Diagnostic tests]
    └──enables──>  [Visualizations]

[Plain-English result interpretation]
    └──requires──> [R code execution]
    └──requires──> [Claude API integration (results → prose)]

[Model comparison]
    └──requires──> [R code execution]
    └──requires──> [Analysis history] (compare models within session)

[Shareable analysis link]
    └──requires──> [Auth / User accounts]
    └──requires──> [Analysis history]

[Transparent assumption display]
    └──enhances──> [Plain-English result interpretation]

[Cached datasets]
    └──requires──> [Auth / User accounts]
    └──enhances──> [Automatic data pull]
```

### Dependency Notes

- **Auth is a prerequisite for most persistence features.** History, caching, and shareable links all depend on a user identity. This makes auth an early-phase requirement even though it is low-complexity.
- **Data pull is the critical path.** All downstream features — diagnostics, interpretation, charts — are only as reliable as the data pipeline. Frequency mismatch handling and assumption transparency are not optional polish; they are required for the data pipeline to produce trustworthy results.
- **Guided upload must integrate with the data merge pipeline.** An uploaded CSV needs to be treated as a first-class data source alongside FRED and Yahoo Finance pulls, with the same cleaning and alignment logic applied.
- **Model comparison enhances but does not block MVP.** It builds on history and execution infrastructure, but the core loop works without it.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what is needed to validate the "prompt → data → analysis → interpretation" loop.

- [ ] Natural language prompt input — the product does not exist without it
- [ ] Automatic data pull from FRED and Yahoo Finance (the core differentiator; without it, the app is just Julius AI with R)
- [ ] User file upload with guided column parsing — fallback when auto-pull cannot satisfy the prompt
- [ ] Automatic data cleaning: missing values, date alignment, unit normalization
- [ ] Frequency mismatch detection with user confirmation dialog
- [ ] Transparent assumption display (quick mode with explanation, detailed mode as toggle)
- [ ] OLS regression (minimum viable analysis type; covers the majority of user prompts)
- [ ] Diagnostic tests output (heteroskedasticity, autocorrelation, multicollinearity, normality) — these validate OLS assumptions and are expected by the target audience
- [ ] Plain-English result interpretation via Claude API
- [ ] Coefficient table with standard errors, p-values, confidence intervals
- [ ] At least two chart types: time-series plot and residual/coefficient plot
- [ ] Generated R code visible and copyable
- [ ] Email/password auth
- [ ] Analysis history (list of past prompts + results)
- [ ] Error feedback with plain-English R error translation

### Add After Validation (v1.x)

Features to add once the core loop is working and real users are running analyses.

- [ ] Logistic regression — add when users report needing binary outcomes; complexity is low once OLS is wired
- [ ] Panel data (fixed effects / random effects) — high demand from economists; add after OLS validated
- [ ] Time-series regression (ARIMA, VAR) — natural extension for macro users; add after core loop stable
- [ ] Shareable analysis links — add once history is stable; unblocks researcher use cases
- [ ] Cached datasets — add when users complain about re-pulling the same data
- [ ] Model comparison — add after logistic/panel implemented; requires multi-model session context
- [ ] Data preview toggle — already planned; can ship as day-1 polish or v1.1

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Bayesian analysis — validate demand via user requests before investing; long run times require rethinking the execution model
- [ ] API access — becomes straightforward once the backend is stable and the product is validated
- [ ] Team collaboration / workspace sharing — only if user research shows researchers working in teams at scale
- [ ] Additional data sources (Bloomberg, Quandl, World Bank WDI) — expand after FRED + Yahoo Finance are solid
- [ ] Scheduled / recurring analyses — monitoring use case; validate with real users first

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Natural language prompt | HIGH | LOW | P1 |
| FRED + Yahoo Finance auto-pull | HIGH | HIGH | P1 |
| Data cleaning pipeline | HIGH | HIGH | P1 |
| Frequency mismatch dialog | HIGH | MEDIUM | P1 |
| Transparent assumption display | HIGH | MEDIUM | P1 |
| OLS regression execution | HIGH | MEDIUM | P1 |
| Diagnostic tests | HIGH | LOW | P1 |
| Plain-English interpretation | HIGH | MEDIUM | P1 |
| Coefficient table display | HIGH | LOW | P1 |
| Visualizations (2 types) | HIGH | MEDIUM | P1 |
| R code display/copy | MEDIUM | LOW | P1 |
| Auth (email/password) | HIGH | LOW | P1 |
| Analysis history | MEDIUM | MEDIUM | P1 |
| Error feedback (plain English) | MEDIUM | MEDIUM | P1 |
| Guided upload parsing | MEDIUM | MEDIUM | P1 |
| Shareable analysis links | MEDIUM | MEDIUM | P2 |
| Cached datasets | MEDIUM | MEDIUM | P2 |
| Logistic regression | MEDIUM | LOW | P2 |
| Panel regression | HIGH | HIGH | P2 |
| Time-series regression | MEDIUM | HIGH | P2 |
| Model comparison | MEDIUM | HIGH | P2 |
| Data preview toggle | LOW | LOW | P2 |
| Bayesian analysis | LOW | HIGH | P3 |
| API access | LOW | MEDIUM | P3 |
| Team collaboration | LOW | HIGH | P3 |
| Additional data sources | MEDIUM | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | Julius AI | DataGPT | camelAI | Stats-AI (this product) |
|---------|-----------|---------|---------|------------------------|
| Natural language query | Yes | Yes | Yes | Yes |
| Auto-pull from public APIs (FRED, Yahoo Finance) | No — upload only | No — connect to own DB | No — upload/connect | **Yes — core differentiator** |
| R code generation + execution | Partial (Python-first, R "coming soon" per 2025 review) | No | No | **Yes — native R** |
| Econometric diagnostics (Breusch-Pagan, VIF, DW) | No — basic stats only | No | No | **Yes — automatic output** |
| Transparent assumption display | No — silent decisions | No | No | **Yes — two-mode system** |
| Frequency mismatch handling | Not applicable (no multi-source pull) | Not applicable | Not applicable | **Yes — user confirmation dialog** |
| Plain-English result interpretation | Yes | Yes | Partial | Yes |
| Visualizations | Yes | Yes | Yes | Yes |
| Analysis history | Yes | Yes | Yes | Yes |
| Shareable links | Partial | Partial | No | Yes (v1.x) |
| Code export | Python only | No | No | **Yes — R code** |
| File upload | Yes (CSV, Excel, PDF) | Yes | Yes | Yes (CSV, Excel, JSON) |
| Auth | Yes | Yes | Yes | Yes |

**Gap analysis:** The competitive gap is real. No competitor combines automatic multi-source public data pulls, R-native execution, and transparent assumption handling. Julius AI is the closest but is Python-centric, requires manual upload, and lacks econometric diagnostics. This product occupies a distinct niche: automated econometric analysis for researchers, not general BI for business teams.

---

## Sources

- [Julius AI features overview (2025)](https://julius.ai/articles/13-powerful-features-that-make-julius-ai-the-top-data-analysis-tool)
- [Julius AI review — Fritz.ai](https://fritz.ai/julius-ai-review/)
- [Julius AI guide — DataCamp](https://www.datacamp.com/tutorial/julius-ai-guide)
- [DataGPT review 2025 — Research.com](https://research.com/software/reviews/datagpt)
- [camelAI — 7 Best AI-Powered Data Analysis Tools 2026](https://camelai.com/blog/7-best-ai-powered-data-analysis-tools-for-non-tech)
- [Best Data Analysis Tools 2026 — Anomaly AI](https://www.findanomaly.ai/best-data-analysis-tools-2026)
- [10 Best AI Data Analysis Tools 2026 — Zerve](https://www.zerve.ai/blog/ai-data-analysis-tools)
- [AI for Data Analysis guide — Luzmo](https://www.luzmo.com/blog/ai-data-analysis)
- [StatGPT: AI for Official Statistics — IMF 2026](https://www.imf.org/en/publications/departmental-papers-policy-papers/issues/2026/03/10/statgpt-ai-for-official-statistics-573514)
- [AI agents for economic research — AEA 2025](https://www.aeaweb.org/content/file?id=23290)
- [SaaS roadmaps 2026: Prioritising AI features — IT Idol](https://itidoltechnologies.com/blog/saas-roadmaps-2026-prioritising-ai-features-without-breaking-product/)

---
*Feature research for: AI-powered statistical analysis web app (Stats-AI)*
*Researched: 2026-03-23*
