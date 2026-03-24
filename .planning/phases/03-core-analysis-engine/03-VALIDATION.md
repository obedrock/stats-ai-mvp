---
phase: 3
slug: core-analysis-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) + vitest (frontend) |
| **Config file** | `backend/pytest.ini` / `frontend/vitest.config.ts` |
| **Quick run command** | `cd backend && uv run pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `cd backend && uv run pytest tests/ -v && cd ../frontend && npx vitest run` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `cd backend && uv run pytest tests/ -v && cd ../frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | ANAL-01 | unit | `uv run pytest tests/test_r_template.py -k ols` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | ANAL-05 | unit | `uv run pytest tests/test_r_template.py -k diagnostic` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | ANAL-06 | unit | `uv run pytest tests/test_code_gen.py -k prompt_to_r` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | ANAL-07 | unit | `uv run pytest tests/test_code_gen.py -k tool_use` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 1 | ANAL-08 | integration | `uv run pytest tests/test_r_execution.py` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 2 | RSLT-01 | unit | `uv run pytest tests/test_interpretation.py` | ❌ W0 | ⬜ pending |
| 03-04-02 | 04 | 2 | RSLT-02 | unit | `uv run pytest tests/test_interpretation.py -k coeff_table` | ❌ W0 | ⬜ pending |
| 03-04-03 | 04 | 2 | RSLT-03 | unit | `uv run pytest tests/test_interpretation.py -k diagnostics` | ❌ W0 | ⬜ pending |
| 03-05-01 | 05 | 2 | RSLT-04 | frontend | `npx vitest run --reporter=verbose src/components/ResultsPanel` | ❌ W0 | ⬜ pending |
| 03-05-02 | 05 | 2 | RSLT-05 | frontend | `npx vitest run --reporter=verbose src/components/CodeViewer` | ❌ W0 | ⬜ pending |
| 03-06-01 | 06 | 3 | RSLT-06 | unit | `uv run pytest tests/test_interpretation.py -k follow_up` | ❌ W0 | ⬜ pending |
| 03-06-02 | 06 | 3 | ANAL-10 | unit | `uv run pytest tests/test_interpretation.py -k hypothesis` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_r_template.py` — stubs for OLS template output validation (ANAL-01, ANAL-05)
- [ ] `backend/tests/test_code_gen.py` — stubs for Claude prompt-to-R code generation (ANAL-06, ANAL-07)
- [ ] `backend/tests/test_r_execution.py` — stubs for R subprocess execution and error handling (ANAL-08)
- [ ] `backend/tests/test_interpretation.py` — stubs for result interpretation and follow-ups (RSLT-01, RSLT-02, RSLT-03, RSLT-06, ANAL-10)
- [ ] `frontend/src/components/__tests__/ResultsPanel.test.tsx` — stubs for results rendering (RSLT-04, RSLT-05)
- [ ] `react-plotly.js` and `plotly.js-dist-min` npm install

*Existing test infrastructure from Phase 1+2 covers pytest and vitest setup.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Interactive Plotly chart hover/zoom | RSLT-04 | Browser interaction not testable in vitest | Open results page, hover over coefficient plot, verify tooltip shows point values; zoom with scroll wheel |
| R code copy button | RSLT-05 | Clipboard API requires browser context | Click copy button on code viewer, paste into text editor, verify complete R script |
| Plain-English error messages | ANAL-08 | Requires subjective readability assessment | Trigger R error (e.g., singular matrix), verify error message is understandable to non-programmer |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
