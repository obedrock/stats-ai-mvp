# Requirements: Stats-AI

**Defined:** 2026-03-23
**Core Value:** The data acquisition and preparation pipeline must work reliably — automatically pulling, cleaning, merging, and transforming data from multiple sources so users never touch raw data.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication

- [x] **AUTH-01**: User can create account with email and password
- [x] **AUTH-02**: User can log in and receive a JWT session token
- [x] **AUTH-03**: User session persists across browser refresh via stored JWT

### Data Pipeline

- [x] **DATA-01**: System auto-detects data sources from prompt context (e.g. "GDP" → FRED, "AAPL price" → Yahoo Finance)
- [x] **DATA-02**: User can override auto-detected data source selection
- [x] **DATA-03**: System pulls data from FRED API based on detected series
- [x] **DATA-04**: System pulls data from Yahoo Finance API based on detected ticker/series
- [x] **DATA-05**: System handles missing values automatically (interpolation, forward-fill, or drop)
- [x] **DATA-06**: System aligns different date formats and time zones across sources
- [x] **DATA-07**: System normalizes units (billions vs millions, % vs decimal)
- [x] **DATA-08**: System flags or handles outliers automatically
- [x] **DATA-09**: System detects frequency mismatches (daily vs quarterly) and prompts user to choose resolution strategy
- [x] **DATA-10**: System displays assumptions (levels vs %, log transforms, lag structure) in quick mode — runs with smart defaults, explains in results
- [x] **DATA-11**: System displays assumptions in detailed mode — lists for user approval before execution
- [x] **DATA-12**: User can upload CSV, Excel, or JSON files
- [x] **DATA-13**: System auto-detects columns, types, and date formats from uploaded files
- [x] **DATA-14**: User can confirm or correct column mappings after auto-detection
- [x] **DATA-15**: Pulled datasets are cached per user for reuse across analyses
- [x] **DATA-16**: User can preview cleaned/merged dataset before running analysis

### Analysis Engine

- [ ] **ANAL-01**: User can run OLS regression via natural language prompt
- [ ] **ANAL-02**: User can run logistic regression via natural language prompt
- [ ] **ANAL-03**: User can run panel data regression (fixed/random effects) via natural language prompt
- [ ] **ANAL-04**: User can run time series analysis (ARIMA, VAR) via natural language prompt
- [ ] **ANAL-05**: System automatically runs diagnostic tests: heteroskedasticity (Breusch-Pagan)
- [ ] **ANAL-06**: System automatically runs diagnostic tests: autocorrelation (Durbin-Watson)
- [ ] **ANAL-07**: System automatically runs diagnostic tests: multicollinearity (VIF)
- [ ] **ANAL-08**: System automatically runs diagnostic tests: normality (Shapiro-Wilk)
- [ ] **ANAL-09**: User can compare models within a session (AIC/BIC, F-tests, pseudo-R2)
- [ ] **ANAL-10**: User can run standalone hypothesis tests: t-tests, F-tests, chi-square, ANOVA

### Results & Output

- [ ] **RSLT-01**: System displays plain-English interpretation of results via Claude API
- [ ] **RSLT-02**: System displays coefficient tables with standard errors, p-values, and confidence intervals
- [ ] **RSLT-03**: System generates interactive Plotly charts (coefficient plots, residual plots, time series plots)
- [ ] **RSLT-04**: User can view and copy the generated R code for each analysis
- [ ] **RSLT-05**: System translates R errors into actionable plain-English feedback
- [ ] **RSLT-06**: After analysis, Claude suggests related follow-up tests the user might want to run
- [ ] **RSLT-07**: User can export results as PDF or Excel report

### History & Persistence

- [ ] **HIST-01**: User can view list of past analyses (prompts + results)
- [ ] **HIST-02**: User can revisit and view full results of any past analysis

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Authentication

- **AUTH-04**: User can reset password via email link
- **AUTH-05**: OAuth login (Google, GitHub)

### Sharing & Collaboration

- **SHAR-01**: User can share analysis results via URL (read-only permalink)
- **SHAR-02**: Team workspaces with shared analysis history

### Advanced Analysis

- **ADVN-01**: Bayesian analysis (MCMC, stan, brms)
- **ADVN-02**: Custom R package installation by users

### Platform

- **PLAT-01**: API access for programmatic use
- **PLAT-02**: Mobile-responsive design

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time streaming data | Batch pulls sufficient for regression/econometric work; streaming adds WebSocket complexity and paid API tiers |
| Team collaboration / multiplayer editing | Complex concurrent-edit logic; solo researcher focus for MVP |
| User-installable R packages | Sandbox security risk, breaks reproducibility; curated environment instead |
| Bayesian analysis | Long MCMC run times, harder to interpret automatically; frequentist covers 95% of needs |
| API access | Must validate core UX before exposing as platform |
| Custom dashboards / BI-style reports | Turns product into BI tool competing with Tableau; not the core value |
| AI-generated paper drafts / LaTeX export | Separate product category; poorly done erodes trust in core analysis |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Complete |
| AUTH-02 | Phase 1 | Complete |
| AUTH-03 | Phase 1 | Complete |
| DATA-01 | Phase 2 | Complete |
| DATA-02 | Phase 2 | Complete |
| DATA-03 | Phase 2 | Complete |
| DATA-04 | Phase 2 | Complete |
| DATA-05 | Phase 2 | Complete |
| DATA-06 | Phase 2 | Complete |
| DATA-07 | Phase 2 | Complete |
| DATA-08 | Phase 2 | Complete |
| DATA-09 | Phase 2 | Complete |
| DATA-10 | Phase 2 | Complete |
| DATA-11 | Phase 2 | Complete |
| DATA-12 | Phase 2 | Complete |
| DATA-13 | Phase 2 | Complete |
| DATA-14 | Phase 2 | Complete |
| DATA-15 | Phase 2 | Complete |
| DATA-16 | Phase 2 | Complete |
| ANAL-01 | Phase 3 | Pending |
| ANAL-02 | Phase 4 | Pending |
| ANAL-03 | Phase 4 | Pending |
| ANAL-04 | Phase 4 | Pending |
| ANAL-05 | Phase 3 | Pending |
| ANAL-06 | Phase 3 | Pending |
| ANAL-07 | Phase 3 | Pending |
| ANAL-08 | Phase 3 | Pending |
| ANAL-09 | Phase 4 | Pending |
| ANAL-10 | Phase 4 | Pending |
| RSLT-01 | Phase 3 | Pending |
| RSLT-02 | Phase 3 | Pending |
| RSLT-03 | Phase 3 | Pending |
| RSLT-04 | Phase 3 | Pending |
| RSLT-05 | Phase 3 | Pending |
| RSLT-06 | Phase 3 | Pending |
| RSLT-07 | Phase 6 | Pending |
| HIST-01 | Phase 5 | Pending |
| HIST-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 38 total
- Mapped to phases: 38
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-23 after roadmap creation*
