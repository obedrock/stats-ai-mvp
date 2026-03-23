---
phase: 1
slug: foundation-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio (backend); vitest (frontend) |
| **Config file** | `backend/pyproject.toml` `[tool.pytest.ini_options]` + `frontend/vitest.config.ts` |
| **Quick run command** | `cd backend && uv run pytest tests/test_auth.py -x` |
| **Full suite command** | `cd backend && uv run pytest && cd ../frontend && npm run test` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && uv run pytest && cd ../frontend && npm run test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | AUTH-01 | integration | `uv run pytest tests/test_auth.py::test_register -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | AUTH-01 | integration | `uv run pytest tests/test_auth.py::test_register_duplicate -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | AUTH-02 | integration | `uv run pytest tests/test_auth.py::test_login -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | AUTH-02 | integration | `uv run pytest tests/test_auth.py::test_login_invalid -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 1 | AUTH-03 | integration | `uv run pytest tests/test_auth.py::test_me -x` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 1 | AUTH-03 | integration | `uv run pytest tests/test_auth.py::test_me_unauthorized -x` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 2 | Celery | integration | `uv run pytest tests/test_jobs.py::test_job_lifecycle -x` | ❌ W0 | ⬜ pending |
| 01-05-01 | 05 | 2 | R sandbox | integration | `uv run pytest tests/test_r_sandbox.py::test_r_runs -x` | ❌ W0 | ⬜ pending |
| 01-05-02 | 05 | 2 | R sandbox | integration | `uv run pytest tests/test_r_sandbox.py::test_r_no_network -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/conftest.py` — async test fixtures, DB session override, test client
- [ ] `backend/tests/test_auth.py` — AUTH-01, AUTH-02, AUTH-03 coverage
- [ ] `backend/tests/test_jobs.py` — Celery job lifecycle smoke test
- [ ] `backend/tests/test_r_sandbox.py` — R subprocess execution + security tests
- [ ] `backend/pyproject.toml` pytest config with `asyncio_mode = "auto"`
- [ ] Docker must be running before integration tests execute (test prereq)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Browser refresh preserves login | AUTH-02 | Requires real browser with localStorage | 1. Log in 2. Refresh browser 3. Verify still authenticated |
| HTTPS on Digital Ocean | Deployment | Requires live droplet + certbot | 1. Deploy to droplet 2. Visit https://domain 3. Verify cert valid |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
