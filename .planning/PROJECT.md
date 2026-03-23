# Stats-AI

## What This Is

A web app that lets users describe statistical analyses in plain English and automatically runs them. Users type prompts like "Run a regression of GDP growth on interest rates and inflation from 2000 to 2023" and Stats-AI handles everything: pulling data from the right sources, cleaning and merging it, generating R code, executing the analysis, and returning results with plain-English interpretation and visualizations. Built for economists, researchers, students, and business analysts.

## Core Value

The data acquisition and preparation pipeline must work reliably — automatically pulling, cleaning, merging, and transforming data from multiple sources so users never touch raw data. This is the hardest part and the core differentiator.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Natural language prompt → R code generation via Claude API
- [ ] Auto-detect data sources from prompt context (FRED for macro data, Yahoo Finance for market data)
- [ ] User override for data source selection
- [ ] Automatic data cleaning: missing values, date alignment, unit conversion, outlier handling
- [ ] Frequency mismatch handling with user confirmation (interpolate, aggregate, or align)
- [ ] Smart assumptions engine (levels vs %, log transforms, lag structure) with two modes:
  - Quick mode: run with smart defaults, explain assumptions in results
  - Detailed mode: list assumptions for user approval before execution
- [ ] User data upload with guided parsing (auto-detect columns/types, user confirms mappings)
- [ ] Optional data preview toggle (see cleaned/merged dataset before analysis)
- [ ] OLS, logistic, panel, and time series regressions
- [ ] Diagnostic tests: heteroskedasticity, autocorrelation, multicollinearity, normality
- [ ] Model comparison and selection
- [ ] Results display: plain-English interpretation + coefficient tables + interactive charts
- [ ] Visualizations: coefficient plots, residual plots, time series plots
- [ ] Simple email/password authentication
- [ ] Analysis history (past prompts and results)
- [ ] Generated R code visible/copyable for each analysis
- [ ] Cached datasets for reuse across analyses
- [ ] Shareable analysis links via URL

### Out of Scope

- Real-time streaming data — batch pulls are sufficient for MVP
- Mobile app — web-first
- Team/collaboration features — single-user focus for MVP
- Custom R package installation by users — curated R environment
- Bayesian analysis — frequentist methods only for MVP
- API access for programmatic use — UI only for MVP

## Context

- **Data pipeline is the core challenge.** The user emphasizes that pulling, cleaning, and merging data is easily the hardest part. Claude needs to make intelligent decisions about data transformations (levels vs percentages, log transforms) and be transparent about them.
- **Multi-source data merging** requires handling different frequencies (daily stock data vs quarterly GDP), different date formats, different units, and gaps. The system must ask users when frequency mismatches occur rather than silently choosing.
- **Target audience is broad** — from stats-savvy researchers who want to skip coding, to students learning methodology, to business analysts who just want answers. The AI interpretation layer should adapt depth accordingly.
- **Prior experience** with running R on Digital Ocean droplets informs the deployment strategy.
- **Data sources for MVP:** Yahoo Finance (yfinance), FRED (fredr/API), and user uploads (CSV, Excel, JSON).

## Constraints

- **Tech Stack**: React frontend, Python/FastAPI backend, R via subprocess on server
- **AI**: Claude API for NLP → R code generation and result interpretation
- **Deployment**: Digital Ocean droplet
- **R Execution**: Server-side via subprocess (sandboxed)
- **MVP Priority**: Core loop (prompt → data → analysis → interpretation) must work end-to-end before polish

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python/FastAPI over Node.js | Natural fit with R ecosystem (rpy2/subprocess), better data library support | — Pending |
| Digital Ocean droplet | Prior experience, full control over R installation | — Pending |
| Server-side R via subprocess | Simpler than cloud R services, sufficient for MVP scale | — Pending |
| Two-mode assumptions (quick/detailed) | Quick mode for speed, detailed mode for control — serves broad audience | — Pending |
| Ask user on frequency mismatches | Silent decisions on data alignment could produce misleading results | — Pending |
| Guided upload parsing | Balance between "magic" auto-detect and user control for correctness | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-23 after initialization*
