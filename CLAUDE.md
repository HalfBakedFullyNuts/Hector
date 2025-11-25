# CLAUDE.md - AI Assistant Guide for Hector

## Project Overview

**Hector** is a dog blood donation platform built with FastAPI. It connects veterinary clinics that need blood donations with dog owners whose pets can donate. The platform facilitates urgent matching between clinics in need and eligible donor dogs.

### Core Domain Concepts

- **Users**: Can be clinic staff, dog owners, or admins
- **Clinics**: Veterinary clinics that can post blood donation requests
- **Dog Profiles**: Information about dogs including blood type, weight, and donation eligibility
- **Blood Donation Requests**: Urgent requests from clinics needing specific blood types
- **Donation Responses**: Dog owners' responses to donation requests

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Framework | FastAPI + Uvicorn (ASGI) |
| Database | PostgreSQL with asyncpg |
| ORM | SQLAlchemy 2.0+ (async) |
| Migrations | Alembic |
| Package Manager | uv |
| Linting/Formatting | Ruff |
| Type Checking | MyPy |
| Testing | Pytest + HTTPX |
| CI | GitHub Actions |

## Project Structure

```
.
├── src/hector/              # Main application source code
│   ├── __init__.py          # Package init, version handling
│   ├── app.py               # FastAPI application factory
│   ├── config.py            # Pydantic settings (env vars)
│   ├── database.py          # SQLAlchemy engine and session management
│   ├── logging_config.py    # Structured logging setup
│   ├── main.py              # Uvicorn entry point (CLI: `hector`)
│   ├── middleware.py        # Request-ID middleware
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── base.py          # BaseModel with UUID, timestamps
│   │   ├── user.py          # User model with roles
│   │   ├── clinic.py        # Clinic model
│   │   ├── dog_profile.py   # Dog profile model
│   │   ├── donation_request.py  # Blood donation requests
│   │   └── donation_response.py # Responses to requests
│   └── routers/             # API route handlers
│       └── health.py        # Health check endpoint
├── tests/                   # Pytest test suite
│   ├── conftest.py          # Test fixtures
│   ├── test_config.py       # Configuration tests
│   ├── test_database.py     # Database tests
│   ├── test_health.py       # Health endpoint tests
│   └── test_models.py       # Model tests
├── migrations/              # Alembic database migrations
│   ├── env.py               # Alembic configuration
│   └── versions/            # Migration scripts
├── .github/workflows/       # CI pipeline
│   └── ci.yml               # Lint, format, type check, test
├── pyproject.toml           # Project dependencies and tool config
├── alembic.ini              # Alembic configuration
├── .env.example             # Environment variable template
└── .pre-commit-config.yaml  # Pre-commit hooks
```

## Development Commands

### Setup

```bash
# Install uv (if not installed)
pip install --user uv

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install .[dev]

# Or install system-wide (CI style)
uv pip install --system .[dev]
```

### Running the Service

```bash
# Start with CLI command
uv run hector

# Or with uvicorn directly (hot reload)
uv run uvicorn hector.app:create_app --factory --reload

# Service runs on http://localhost:8000
# Health check: GET /health
```

### Quality Checks

```bash
# Linting
ruff check .

# Formatting
ruff format .           # Apply formatting
ruff format --check .   # Check only

# Type checking
mypy src

# Security audit
pip-audit

# Run all tests
pytest

# Run tests with database (requires PostgreSQL)
pytest --run-db-tests
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Database Operations

```bash
# Start PostgreSQL (Docker)
docker run --name hector-postgres \
  -e POSTGRES_USER=hector \
  -e POSTGRES_PASSWORD=hector \
  -e POSTGRES_DB=hector \
  -p 5432:5432 \
  -d postgres:16-alpine

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Environment Variables

All environment variables are prefixed with `HECTOR_`. Copy `.env.example` to `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HECTOR_ENVIRONMENT` | Yes | - | Deployment environment (development, staging, production) |
| `HECTOR_DATABASE_URL` | Yes | - | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `HECTOR_PORT` | No | 8000 | HTTP server port |
| `HECTOR_LOG_LEVEL` | No | INFO | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `HECTOR_DB_POOL_SIZE` | No | 5 | Database connection pool size |
| `HECTOR_DB_MAX_OVERFLOW` | No | 10 | Max connections beyond pool size |
| `HECTOR_DB_ECHO` | No | false | Echo SQL statements |

## Code Conventions

### General Guidelines

- Use **async/await** for all I/O operations
- Follow **PEP 8** style (enforced by Ruff)
- Add **type annotations** for all public functions and return values
- Keep functions under **60 lines** of code
- Aim for **2+ assertions per function** for validation
- Declare variables at the **smallest possible scope**
- **Check return values** of all non-void functions
- **Validate parameters** at function boundaries

### Naming Conventions

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/Methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Environment variables: `HECTOR_` prefix

### Database Models

All models inherit from `BaseModel` which provides:
- `id`: UUID primary key (auto-generated)
- `created_at`: Timestamp (auto-set)
- `updated_at`: Timestamp (auto-updated)

### API Patterns

- Use FastAPI's dependency injection with `Depends()`
- Database sessions via `Depends(get_db)`
- Settings via `Depends(get_settings)`
- Request IDs available via `get_request_id()`

## Testing Guidelines

- Tests live in `tests/` directory
- Use `pytest-asyncio` for async tests
- Database tests require `--run-db-tests` flag
- Use HTTPX `AsyncClient` for API tests
- Rollback database changes after each test

Example test pattern:
```python
@pytest.mark.asyncio
async def test_something(db_session):
    # Test using the db_session fixture
    pass
```

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/hector/app.py` | Application factory - start here for app structure |
| `src/hector/config.py` | All configuration settings |
| `src/hector/database.py` | Database engine, session management, `get_db()` |
| `src/hector/models/base.py` | Base model with common fields |
| `pyproject.toml` | Dependencies and tool configuration |
| `.github/workflows/ci.yml` | CI pipeline definition |
| `Tickets.md` | Detailed feature tickets and implementation plan |

## Current Project Status

**Phase 1 (Database Foundation)** is complete:
- Database setup and connection (T-100)
- SQLAlchemy integration (T-101)
- Alembic migrations (T-102)
- User model (T-103)
- Clinic model (T-104)
- Dog Profile model (T-105)
- Blood Donation Request model (T-106)
- Donation Response model (T-107)

**Next phases** (see `Tickets.md` for details):
- Phase 2: Authentication & User Management (T-200 - T-207)
- Phase 3: Dog Profile Management (T-300 - T-305)
- Phase 4: Clinic Management (T-400 - T-403)
- Phase 5: Blood Donation Request Management (T-500 - T-505)
- Phase 6: Donation Response & Matching (T-600 - T-604)
- Phase 7: Admin Features (T-700 - T-704)
- Phases 8-10: Frontend and Enhancements

## Important Relationships

```
User (1) ──────< DogProfile (n)
User (1) ──────< Clinic (n) [as staff]
Clinic (1) ────< BloodDonationRequest (n)
BloodDonationRequest (1) ──< DonationResponse (n)
DogProfile (1) ──< DonationResponse (n)
```

## CI Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on all PRs to `main`:

1. Ruff lint check
2. Ruff format check
3. MyPy type check
4. pip-audit security scan
5. Pytest test suite

All checks must pass before merging.

## Branch Strategy

- `main`: Always releasable
- Feature branches: `feature/<ticket-id>-description`
- Claude branches: `claude/<description>-<session-id>`
- PRs require at least one review

## Working with This Codebase

### Before Making Changes

1. Read relevant existing code first
2. Check `Tickets.md` for context and requirements
3. Follow the established patterns in existing code

### When Adding Features

1. Create/update SQLAlchemy models in `src/hector/models/`
2. Generate Alembic migration: `alembic revision --autogenerate -m "..."`
3. Add API routes in `src/hector/routers/`
4. Write tests in `tests/`
5. Run all quality checks before committing

### When Fixing Bugs

1. Write a failing test first
2. Fix the bug
3. Verify the test passes
4. Run full test suite

## Reference Documentation

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Ruff Docs](https://docs.astral.sh/ruff/)
