---
phase: 2
slug: data-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 (backend), vitest (frontend) |
| **Config file** | `backend/pyproject.toml` (`asyncio_mode = "auto"`) |
| **Quick run command** | `cd backend && uv run pytest tests/test_data_pipeline.py -x -q` |
| **Full suite command** | `cd backend && uv run pytest -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/test_data_pipeline.py -x -q`
- **After every plan wave:** Run `cd backend && uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green + `cd frontend && npm run test -- --run`
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | DATA-01 | unit | `pytest tests/test_series_mapper.py -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 0 | DATA-03 | unit | `pytest tests/test_fred_fetcher.py -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 0 | DATA-04 | unit | `pytest tests/test_yahoo_fetcher.py -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 0 | DATA-05,06,07,08,10 | unit | `pytest tests/test_data_pipeline.py -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 0 | DATA-09 | unit | `pytest tests/test_frequency_resolver.py -x` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 0 | DATA-15 | unit | `pytest tests/test_data_cache.py -x` | ❌ W0 | ⬜ pending |
| 02-01-07 | 01 | 0 | DATA-13 | unit | `pytest tests/test_file_parser.py -x` | ❌ W0 | ⬜ pending |
| 02-01-08 | 01 | 0 | DATA-12,14 | integration | `pytest tests/test_upload.py -x` | ❌ W0 | ⬜ pending |
| 02-01-09 | 01 | 0 | DATA-02,09,11,16 | integration | `pytest tests/test_data_router.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_series_mapper.py` — stubs for DATA-01; mock anthropic client
- [ ] `backend/tests/test_fred_fetcher.py` — stubs for DATA-03; mock fredapi + httpx
- [ ] `backend/tests/test_yahoo_fetcher.py` — stubs for DATA-04; mock yfinance
- [ ] `backend/tests/test_data_pipeline.py` — stubs for DATA-05, DATA-06, DATA-07, DATA-08, DATA-10; mock external calls
- [ ] `backend/tests/test_frequency_resolver.py` — stubs for DATA-09; pure unit, no mocks needed
- [ ] `backend/tests/test_data_cache.py` — stubs for DATA-15; use fakeredis
- [ ] `backend/tests/test_file_parser.py` — stubs for DATA-13; use fixture files
- [ ] `backend/tests/test_upload.py` — stubs for DATA-12, DATA-14; fixture CSV/Excel/JSON
- [ ] `backend/tests/test_data_router.py` — stubs for DATA-02, DATA-09 (API), DATA-11, DATA-16
- [ ] `backend/tests/fixtures/` — sample CSV, Excel, JSON files for upload tests
- [ ] `uv add fakeredis --dev` — required for DATA-15 cache tests without running Redis

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Drag-and-drop file upload UX | DATA-12 | Browser drag events cannot be simulated in pytest | Open browser, drag CSV onto upload area, verify preview appears |
| Data preview scrolling with 50 rows | DATA-16 | Visual table rendering | Open browser, fetch data, toggle preview panel, verify scrollable table |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
