---
phase: 01-foundation-infrastructure
plan: 02
subsystem: backend-auth
tags: [auth, jwt, fastapi, sqlalchemy, testing]
dependency_graph:
  requires: [01-01]
  provides: [auth-api, user-model, jwt-utilities, auth-tests]
  affects: [all future protected endpoints]
tech_stack:
  added: [passlib[bcrypt], python-jose[cryptography], aiosqlite, pytest, pytest-asyncio]
  patterns: [OAuth2PasswordBearer, JWT HS256, SQLAlchemy Mapped types, AsyncClient ASGI testing]
key_files:
  created:
    - backend/app/models/user.py
    - backend/app/schemas/auth.py
    - backend/app/auth/jwt.py
    - backend/app/auth/passwords.py
    - backend/app/auth/dependencies.py
    - backend/app/routers/auth.py
    - backend/alembic/versions/6f82ac72c104_create_users_table.py
    - backend/tests/__init__.py
    - backend/tests/conftest.py
    - backend/tests/test_auth.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/main.py
    - backend/pyproject.toml
decisions:
  - Used SQLAlchemy `Uuid` (cross-DB) instead of `postgresql.UUID` to support both PostgreSQL production and SQLite test environments
  - Used aiosqlite in-memory SQLite for tests since Docker/PostgreSQL unavailable on dev machine
  - Pinned bcrypt<5 because bcrypt 5.0 broke passlib compatibility (changed internal API)
  - UUID string-to-object coercion in get_current_user required for cross-DB compatibility
metrics:
  duration_minutes: 6
  completed_date: "2026-03-23"
  tasks_completed: 2
  files_created: 13
---

# Phase 01 Plan 02: Auth Backend Summary

**One-liner:** Email+password auth with bcrypt hashing, python-jose JWT (HS256), and 7 passing integration tests using SQLite in-memory test DB.

## What Was Built

Complete authentication backend with:
- SQLAlchemy 2.0 User model (UUID pk, email unique+indexed, bcrypt hashed_password, is_active, created_at)
- `POST /auth/register` — creates user, hashes password, returns 201 + JWT token
- `POST /auth/token` — OAuth2 form login, validates credentials, returns JWT token
- `GET /auth/me` — Bearer token validation, returns user info
- Alembic migration: `create_users_table` (ready to run when PostgreSQL is available)
- Full test suite: 7 integration tests, all passing

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| SQLAlchemy `Uuid` over `postgresql.UUID` | Enables cross-DB compatibility for SQLite test environment |
| aiosqlite in-memory for tests | Docker/PostgreSQL not installed on dev machine; tests must pass locally |
| bcrypt pinned to `<5` | bcrypt 5.0 dropped `__about__` attribute breaking passlib backend detection |
| UUID string-to-object coercion in `get_current_user` | JWT payload stores UUID as string; SQLAlchemy Uuid type requires uuid.UUID object |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed UUID type mismatch in get_current_user**
- **Found during:** Task 2 (test_me test failure)
- **Issue:** JWT stores user_id as string; SQLAlchemy `Uuid` type requires `uuid.UUID` object for queries against SQLite
- **Fix:** Added `uuid.UUID(user_id_str)` conversion in `get_current_user` before DB query
- **Files modified:** `backend/app/auth/dependencies.py`
- **Commit:** 95e4093

**2. [Rule 1 - Bug] bcrypt 5.0 incompatible with passlib**
- **Found during:** Task 2 (test_register failure)
- **Issue:** bcrypt 5.0 changed internal API — removed `__about__` attribute and raised ValueError for long passwords during backend detection
- **Fix:** Pinned `bcrypt<5` in pyproject.toml (installs 4.3.0)
- **Files modified:** `backend/pyproject.toml`, `backend/uv.lock`
- **Commit:** 95e4093

**3. [Rule 3 - Blocking] Switched from postgresql.UUID to SQLAlchemy Uuid**
- **Found during:** Task 2 (test infrastructure setup)
- **Issue:** `postgresql.UUID` is PostgreSQL-only; SQLite test DB cannot process the type processor
- **Fix:** Changed User model to use `sqlalchemy.Uuid(as_uuid=True)` which renders as native UUID on PostgreSQL and as STRING on SQLite
- **Files modified:** `backend/app/models/user.py`, `backend/alembic/versions/6f82ac72c104_create_users_table.py`
- **Commit:** 95e4093

**4. [Rule 3 - Blocking] Added aiosqlite for async SQLite testing**
- **Found during:** Task 2 (test DB setup)
- **Issue:** No PostgreSQL available locally; plan called for using `settings.database_url` which requires a running PostgreSQL
- **Fix:** Added aiosqlite as dev dependency; conftest uses `sqlite+aiosqlite:///:memory:` for isolated, fast test runs
- **Files modified:** `backend/tests/conftest.py`, `backend/pyproject.toml`
- **Commit:** 95e4093

## Test Results

```
7 passed in 1.11s

tests/test_auth.py::test_register PASSED
tests/test_auth.py::test_register_duplicate PASSED
tests/test_auth.py::test_register_weak_password PASSED
tests/test_auth.py::test_login PASSED
tests/test_auth.py::test_login_invalid PASSED
tests/test_auth.py::test_me PASSED
tests/test_auth.py::test_me_unauthorized PASSED
```

## Known Stubs

None — all auth functionality is fully wired.

## Self-Check: PASSED

- backend/app/models/user.py — FOUND
- backend/app/auth/jwt.py — FOUND
- backend/app/auth/passwords.py — FOUND
- backend/app/auth/dependencies.py — FOUND
- backend/app/routers/auth.py — FOUND
- backend/tests/conftest.py — FOUND
- backend/tests/test_auth.py — FOUND
- Commit 2e8792b (Task 1) — FOUND
- Commit 95e4093 (Task 2) — FOUND
