# Hector MVP — Plan 1 of 4: Backend Stabilize, Secure, Complete

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing FastAPI backend fully runnable, secure against known gaps, and complete against ticket specs T-100…T-704 — with every quality gate green.

**Architecture:** Layered remediation of the existing FastAPI + SQLAlchemy async app: stabilize tooling/tests first, then security hardening, then close spec gaps. No framework or structural rewrites; follow existing router/model/schema patterns.

**Tech Stack:** Python 3.12, FastAPI 0.141, SQLAlchemy 2 async, PostgreSQL 16 (docker compose), Alembic, pytest/pytest-asyncio, ruff, mypy strict.

**Spec:** `docs/superpowers/specs/2026-08-22-hector-mvp-design.md` (decisions D1–D10). Plans 2–4 will cover Phase 10 backend, frontend completion, and CI/final gates.

## Global Constraints

- Branch: `mvp/backend-foundation` (created from main).
- venv via uv at `./venv`; all commands run through `./venv/bin/`.
- Every task must leave `./venv/bin/ruff check src/ tests/`, `./venv/bin/ruff format --check src/ tests/`, and `./venv/bin/mypy src/` clean before commit (except tasks that explicitly defer to a later gate).
- Functions ≤60 lines; declare data at smallest scope; every non-void return checked; ≥1 assert per new non-trivial function guarding impossible states (AGENTS.md rules).
- No comments except docstrings ≤3 lines explaining purpose (AGENTS.md reporting rule).
- Test DB URL convention: `postgresql+asyncpg://hector:hector@localhost:5433/hector_test` (compose maps host 5433→5432).
- Never log secrets: JWT secret and DB URL password must be masked in any log output.

---

## Phase A — Stabilize

### Task A1: Toolchain fixes (deps + StrEnum)

**Files:**
- Modify: `pyproject.toml` (dependencies)
- Modify: `src/hector/models/user.py:15`, `dog_profile.py:17,35`, `donation_request.py:19,27`, `donation_response.py:18`

**Steps:**
- [ ] Add `"email-validator>=2.0,<3"` to `[project.dependencies]` (pydantic EmailStr needs it at runtime) and `"types-python-jose>=1.5,<2"` + `"pytest-cov>=5,<7"` to dev extras.
- [ ] Convert six enums to `class X(enum.StrEnum)` (drop `str, Enum` bases). Values unchanged → DB enum types unaffected.
- [ ] `uv pip install -e ".[dev]" --python venv/bin/python`
- [ ] Verify: `ruff check src/ tests/` exits 0.
- [ ] Commit: `fix(backend): add missing deps, convert enums to StrEnum`

### Task A2: Fix illegal Depends-in-default signatures (unblocks test collection)

**Files:**
- Modify: `src/hector/routers/admin.py` (lines 42,135,207,276,391,442)
- Modify: `src/hector/routers/donation_requests.py:383`

**Interfaces (produces):**
```python
# admin.py — alongside admin_only definition
AdminUser = Annotated[User, Depends(admin_only)]
# donation_requests.py — alongside clinic_staff_or_admin
StaffUser = Annotated[User, Depends(clinic_staff_or_admin)]
```
- [ ] Replace each `current_user: CurrentUser = Depends(admin_only)` with `current_user: AdminUser`; same pattern for `clinic_staff_or_admin` → `StaffUser`. Remove now-unused `CurrentUser` imports if flagged by lint.
- [ ] Run `pytest -q tests/test_auth_jwt.py tests/test_auth_password.py tests/test_config.py` → PASS (non-DB suites; DB suites fixed in A3).
- [ ] Commit: `fix(backend): replace illegal Depends defaults with Annotated aliases`

### Task A3: Dockerized Postgres + real DB test fixtures

**Files:**
- Create: `docker-compose.yml`, `scripts/init-test-db.sql`
- Modify: `tests/conftest.py`, `.env.example`

**Interfaces (produces):**
```python
# conftest.py
@pytest.fixture(scope="session")
def database_url() -> str  # HECTOR_TEST_DATABASE_URL or compose default
@pytest.fixture
async def db_engine(database_url) -> AsyncEngine  # schema created if absent
@pytest.fixture
async def db_session(db_engine) -> AsyncSession   # truncates ALL tables after each test
```
Compose: postgres:16-alpine, user/pass/db `hector`/`hector`/`hector`, port `5433:5432`, healthcheck `pg_isready`, volume `./scripts/init-test-db.sql:/docker-entrypoint-initdb.d/` containing `CREATE DATABASE hector_test;`.

conftest: env defaults pinned in `pytest_configure` (`HECTOR_ENVIRONMENT=test`, `HECTOR_DATABASE_URL=<test url>`, strong default `HECTOR_JWT_SECRET_KEY`). `db_session` yields a session then runs `TRUNCATE <all tables> RESTART IDENTITY CASCADE` (table names from `Base.metadata.sorted_tables`) so tests are isolated without savepoint gymnastics (endpoints call `commit()` internally).

- [ ] Write failing sanity test asserting `db_session.execute(select(User))` works and rows don't leak between two sequential tests.
- [ ] Implement conftest + compose; `docker compose up -d db` healthy.
- [ ] Full suite: `pytest -q` → all pass including endpoint tests.
- [ ] Commit: `test(backend): dockerized Postgres and isolated DB fixtures`

### Task A4: Regenerate Alembic initial migration

**Files:**
- Delete: `migrations/versions/b641ac919ab9_*.py`
- Create: fresh autogenerated revision

- [ ] `docker compose up -d db`; recreate empty dev DB `hector`.
- [ ] `rm migrations/versions/b641ac919ab9_*.py && alembic revision --autogenerate -m "initial schema"`
- [ ] Review generated file: users/clinics/dog_profiles/blood_donation_requests/donation_responses tables incl. `patient_info`, `phone`, `uq_request_dog`; five PG enums.
- [ ] Round-trip: `alembic upgrade head && alembic downgrade base && alembic upgrade head`.
- [ ] Full pytest still green (fixtures use metadata.create_all — independent of alembic).
- [ ] Commit: `fix(db): regenerate initial migration matching models`

## Phase B — Security Hardening

### Task B1: Registration role restriction + admin CLI

**Files:**
- Modify: `src/hector/schemas/auth.py`, `pyproject.toml` (entry point)
- Create: `src/hector/cli.py`, `tests/test_cli.py`, extend `tests/test_auth_endpoints.py`

**Interfaces:**
```python
# schemas/auth.py — field_validator("role") raising ValueError when value is ADMIN → FastAPI 422
# cli.py
def main(argv: list[str] | None = None) -> int
# usage: python -m hector.cli create-admin --email a@b.c --password Str0ngPass
# entry point: hector = "hector.cli:main"; server start moves to `hector serve`
```
CLI validates password with the same strength regex as registration (extract shared `validate_password_strength(value: str) -> str` into schemas.auth and reuse). Creates User(role=ADMIN, is_verified=True).

- [ ] Tests first: register role=admin → 422; CLI happy path creates verified admin; duplicate email → exit≠0; weak password → exit≠0.
- [ ] Implement; update pyproject scripts (`hector` → cli dispatch: `serve` subcommand keeps old behavior).
- [ ] Commit: `feat(security): forbid self-registered admins, add create-admin CLI`

### Task B2: Secret hygiene (log redaction + reject default secret)

**Files:**
- Modify: `src/hector/config.py` (validators + redaction), `src/hector/app.py` (startup log uses masked dict)
- Extend: `tests/test_config.py`

**Interfaces:**
```python
KNOWN_DEFAULT_SECRETS = frozenset({"your-secret-key-here-change-in-production", "changeme", "secret"})
def settings_asdict(settings) -> dict[str, Any]  # masks jwt_secret_key="***", database_url password=":***@"
```
Settings gains `@field_validator("jwt_secret_key")` rejecting values in KNOWN_DEFAULT_SECRETS (exact match; test default key differs, so suite unaffected).

- [ ] Tests: masked asdict output contains no secret substring; Settings() raises on example-secret value; startup path doesn't log raw secret (caplog assertion).
- [ ] Implement; full pytest green.
- [ ] Commit: `feat(security): redact secrets from logs, reject known-default JWT secret`

### Task B3: Login rate limiting

**Files:**
- Create: `src/hector/services/__init__.py`, `services/rate_limit.py`, `tests/test_rate_limit.py`
- Modify: `src/hector/routers/auth.py` (login endpoint), `tests/conftest.py` (autouse reset fixture)

**Interfaces:**
```python
class SlidingWindowLimiter:
    def __init__(self, max_failures: int, window_seconds: int,
                 clock: Callable[[], float] = time.monotonic) -> None: ...
    def check(self, key: str) -> tuple[bool, int]   # (blocked?, retry_after_seconds)
    def record_failure(self, key: str) -> None
    def reset(self, key: str) -> None

def get_login_limiter() -> SlidingWindowLimiter  # module singleton; 5 failures / 900 s; bounded dict size 10_000 (evict oldest)
```
Login endpoint keys on client IP; on blocked → 429 `Retry-After` header; failed password → record_failure; success → reset. Autouse fixture resets singleton between tests.

- [ ] Unit tests with fake clock: block at threshold, window expiry unblocks, reset clears. Endpoint tests: 5 bad logins → 6th returns 429; successful login resets counter.
- [ ] Commit: `feat(security): rate-limit login attempts per IP`

### Task B4: IDOR fix + route ordering in donation requests

**Files:**
- Modify: `src/hector/routers/donation_requests.py`

Changes:
1. Move `/my-responses` and `/compatible` route declarations **before** `/{request_id}` (FastAPI matches in order; today they 422).
2. `/compatible`: require `CurrentUser`, fetch dog, `403 "This dog does not belong to you"` unless `dog.owner_id == current_user.id`.
- [ ] Tests: owner B requesting compatible list for A's dog → 403; unauthenticated → 401; GET `/requests/my-responses` no longer 422s (401/200 instead).
- [ ] Commit: `fix(security): enforce dog ownership on /compatible, fix route shadowing`

### Task B5: Soft deletes everywhere

**Files:**
- Modify: `src/hector/models/clinic.py` (add `is_active` column, default True), `src/hector/routers/admin.py` (reject → `is_active=False`), `src/hector/models/dog_profile.py` (add `is_available_for_donation` default True; eligibility property requires both active AND available), `src/hector/schemas/dog.py` (availability schema field `is_available`), `src/hector/routers/dogs.py` (delete → `is_active=False`; availability PATCH toggles `is_available_for_donation`; list/get filter `is_active == True`)
- Migration: autogenerated revision adding the two columns.

Rules: DELETE dog → 204, row kept inactive, hidden from list/get/respond eligibility. Clinic reject → soft-deleted; public clinic listings/details hide inactive. Respond-to-request checks `is_active and is_available_for_donation`.
- [ ] Tests: deleted dog invisible but row exists; rejected clinic hidden from listing; availability toggle doesn't change is_active.
- [ ] Commit: `feat(data): soft-delete dogs and clinics, independent donation-availability flag`

### Task B6: Remove unsafe JWT helper

**Files:** `src/hector/auth/jwt.py` (drop `decode_token_unsafe`), `src/hector/auth/__init__.py` (export), grep for usages.
- [ ] Test asserting import fails / symbol gone; commit: `chore(security): remove decode_token_unsafe`

### Task B7: Inactive login semantics

**Files:** `src/hector/routers/auth.py` (login: 403 `"Account disabled"`), refresh endpoint message aligned to spec wording.
- [ ] Endpoint test: disabled user login → 403 detail "Account disabled". Commit: `fix(auth): return 403 Account disabled for inactive users`

## Phase C — Close Backend Spec Gaps

### Task C1: Pagination + sorting on GET /dogs (T-301)

`limit`/`offset` Query params (defaults 20/0, le=100), `order_by(created_at.desc())`. Response stays `list[DogProfileResponse]`. Tests: ordering, limits, empty page. Commit: `feat(dogs): paginate and sort dog listing`

### Task C2: Real response count on request details (T-502)

Replace hardcoded 0 in `get_donation_request` with `select(func.count(DonationResponse.id)).where(request_id=...)` scalar. Test: request with 2 responses returns count 2. Commit: `fix(requests): report real response count`

### Task C3: Compatibility score (T-604)

New response model `CompatibleRequest(DonationRequestWithClinic)` + `compatibility_score: int`: 100 universal donor (DEA_1_1_NEGATIVE), 75 exact blood-type match, 50 unspecified-request compatibility. Compute in Python post-query. Tests cover all three branches. Commit: `feat(matching): compatibility scores on compatible listing`

### Task C4: Admin stats date filters (T-703) + batched queries

Apply `start_date/end_date` filters to counts where meaningful (users/requests/responses/donations created_at range); replace per-role/per-status N-query loops with single `GROUP BY` aggregates. Tests: date filtering excludes out-of-range rows; results identical shape. Commit: `perf(admin): batch stats queries, honor date range`

### Task C5: Audit logging (T-701/702/704)

Create `AuditLog` model (id UUID, actor_user_id FK users nullable, action str, target_type str, target_id str, details JSONB, created_at) + migration. Write entries in toggle-active, delete-user, approve-clinic, reject-clinic. Expose `GET /admin/audit-log` (admin only, paginated newest-first). Tests: each action writes exactly one row with actor and target. Commit: `feat(admin): audit trail for privileged actions`

### Task C6: Spec path alignment (T-505)

Add `GET /clinics/my-requests` in clinics router (staff token → their clinics' requests, status filter, paginated). Keep old `/requests/my-clinic` as thin alias for one release; mark deprecated in docstring. Tests hit new path. Commit: `feat(clinics): expose /clinics/my-requests per spec`

### Task C7: Phase C gate sweep

Full `pytest -q` vs compose DB; coverage ≥80% (`--cov=src/hector --cov-report=term`); ruff/format/mypy/pip-audit clean; update README (quick start with compose, testing commands, new endpoints summary); update Tickets.md status column for completed tickets.
Commit: `docs: refresh README and ticket status through backend completion`
