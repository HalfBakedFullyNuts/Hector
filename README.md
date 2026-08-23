# Hector - Dog Blood Donation Platform

A FastAPI + React platform connecting dog owners and veterinary clinics for blood
donation matching and coordination.

## Project Status

**MVP COMPLETE** — all ticketed features (Phases 1-10) implemented and verified:

- Auth: JWT + refresh, login rate limiting, password reset, admin CLI bootstrap
- Dogs: profiles, availability toggle, soft delete, photo upload with thumbnails
- Clinics: registration → admin approval workflow, profile management
- Requests: creation → owner notifications → responses → completion tracking
- Matching: blood-type compatibility scores, Haversine distance sort/filter
- Admin: user management, clinic approvals, platform stats, audit trail
- Frontend: full React UI for all three roles, responsive, Vitest-tested
- Verified end-to-end by `scripts/smoke_test.sh`

## Quick Start

### Prerequisites

- Python 3.12 (uv recommended)
- Docker (for PostgreSQL 16)

### Backend

```bash
# Start the database (dev DB `hector` + test DB `hector_test` on host port 5433)
docker compose up -d db

# Create virtualenv and install
uv venv venv --python 3.12
uv pip install -e ".[dev]" --python venv/bin/python

# Configure environment
cp .env.example .env
# Edit .env - generate a JWT secret: openssl rand -hex 32

# Run database migrations
./venv/bin/alembic upgrade head

# Bootstrap the first admin (self-registration of admins is blocked)
./venv/bin/python -m hector.cli create-admin --email admin@example.com --password 'Str0ngPass'

# Run the API
./venv/bin/hector serve          # http://localhost:8000/docs
```

### Frontend

```bash
cd frontend && npm install && npm run dev   # http://localhost:5173
```

### End-to-end smoke test

With the API running (`hector serve`) and Docker DB up:

```bash
PATH="$PWD/venv/bin:$PATH" bash scripts/smoke_test.sh
```

Exercises the complete journey: admin bootstrap → clinic approval → dog + photo →
request → compatibility match → respond → complete → notifications → stats.

## Testing & Quality Gates

```bash
docker compose up -d db                       # required for integration tests
./venv/bin/python -m pytest --run-db-tests    # full suite vs real Postgres
./venv/bin/ruff check src/ tests/             # lint
./venv/bin/ruff format --check src/ tests/    # formatting
./venv/bin/mypy src/                          # strict type checking
./venv/bin/pip-audit                          # dependency vulnerabilities
```

Frontend gates: `npm run build` (typecheck + build), `npm run lint`, `npm test`.

## API Overview

| Area  | Endpoints (prefix) | Highlights |
|-------|--------------------|------------|
| Auth  | `/auth` | register (owner/staff only), login (5 fails / 15 min / IP → 429), refresh, me, forgot/reset password |
| Dogs  | `/dogs` | CRUD, pagination, soft delete, availability toggle, photo upload |
| Clinics | `/clinics` | create (auto-links staff), public listing/details, update, `/my-requests` |
| Requests | `/requests` | CRUD w/ ownership checks, respond, responses listing, complete, `/compatible?dog_id=` with `compatibility_score`, `/my-responses`, geo sort/filter |
| Admin | `/admin` | users list/toggle/delete, clinic approve/reject (soft deletes), stats w/ date range, `/audit-log` |
| Health | `/health` | status, version, request id |

Business rules enforced server-side: dogs 25 kg+, 1-8 years, ≥8 weeks since last
donation; volume 50-500 ml; needed-by date within 30 days; DEA 1.1-negative =
universal donor; duplicate responses blocked by unique constraint; overdue requests
auto-expire daily.

## Security Notes

- Admins only via CLI bootstrap (`create-admin`); registration rejects role=admin.
- Known-default JWT secrets are rejected at startup; secrets are masked in logs.
- Login rate limiting: 5 failed attempts / 15 min / IP (429 + Retry-After).
- Soft deletes everywhere history matters (dogs, clinics); disabled accounts get
  403 on login and instant lockout via per-request `is_active` re-check.
- Ownership checks on every dog/request mutation (IDOR-tested).
- Password reset tokens are stored hashed, single-use, and expire after one hour.

See `SECURITY.md` for reporting policy.

## Documentation

- Design/spec: `docs/superpowers/specs/2026-08-22-hector-mvp-design.md`
- Implementation plans + execution addenda: `docs/superpowers/plans/`
- Phase 2 auth deep-dive: `docs/phase-2-authentication.md`
- Ticket backlog + status: `Tickets.md`; process decisions: `Playbook.md`

## Technology Stack

FastAPI 0.141 · SQLAlchemy 2 async · PostgreSQL 16 · Alembic · APScheduler ·
pytest(+asyncio) · ruff · mypy(strict) · React 19 · Vite · Tailwind CSS v4 ·
react-hook-form + zod · Vitest

## License

MIT
