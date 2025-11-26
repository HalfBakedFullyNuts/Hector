# Hector - Dog Blood Donation Platform

A FastAPI-based platform connecting dog owners and veterinary clinics for blood donation matching and coordination.

## Project Status

**Current Phase:** Phase 2 - Authentication & User Management ✅ **COMPLETE**

- ✅ Phase 1: Database Foundation (SQLAlchemy models, migrations)
- ✅ Phase 2: Authentication & User Management (JWT auth, role-based access control)
- ⏳ Phase 3: Dog Profiles & Blood Type Management (next)

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 16+
- Virtual environment tool

### Setup

```bash
# Clone repository
git clone <repo-url>
cd Hector

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your settings (especially JWT_SECRET_KEY)

# Run database migrations
alembic upgrade head

# Run the application
python -m hector.main
```

### Testing

```bash
# Run all tests
pytest -v

# Run specific test suite
pytest tests/test_auth_endpoints.py -v

# Run with database tests
pytest --run-db-tests -v

# Check code quality
ruff check src/ tests/
mypy src/
```

## Documentation

### Phase 2 Documentation (Current)

**📖 [Phase 2: Authentication & User Management](docs/phase-2-authentication.md)**

Comprehensive guide covering:
- Architecture decisions and rationale
- Implementation details for all authentication components
- Usage guide with code examples
- Testing approach (84 tests, 53 pass without DB)
- Troubleshooting and performance optimization
- Next steps for Phase 3 integration

**Quick Reference:**

- **Authentication**: JWT-based with access/refresh tokens
- **Authorization**: Role-based (admin, clinic_staff, dog_owner)
- **Endpoints**:
  - `POST /auth/register` - User registration
  - `POST /auth/login` - Login with email/password
  - `GET /auth/me` - Get current user
  - `POST /auth/refresh` - Refresh access token

### Using Authentication in Your Code

```python
from hector.auth import CurrentUser, RequireAdmin

# Any authenticated user
@router.get("/profile")
async def get_profile(current_user: CurrentUser):
    return {"email": current_user.email}

# Admin only
@router.post("/admin/settings")
async def update_settings(admin: RequireAdmin):
    return {"updated_by": admin.email}
```

See [full documentation](docs/phase-2-authentication.md#usage-guide) for more examples.

## Project Structure

```
Hector/
├── src/hector/              # Main application code
│   ├── auth/               # Authentication & authorization
│   ├── models/             # SQLAlchemy models
│   ├── routers/            # FastAPI route handlers
│   ├── schemas/            # Pydantic schemas
│   ├── app.py             # FastAPI app factory
│   ├── config.py          # Configuration management
│   ├── database.py        # Database setup
│   └── main.py            # Entry point
├── tests/                  # Test suite
│   ├── test_auth_*.py     # Authentication tests
│   └── conftest.py        # Test fixtures
├── alembic/               # Database migrations
├── docs/                  # Documentation
│   └── phase-2-authentication.md
├── pyproject.toml         # Project dependencies
└── .env.example           # Environment template
```

## Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `claude/phase-2-authentication-*` - Phase 2 development (current)
- `claude/phase-3-*` - Phase 3 development (upcoming)

### Making Changes

1. Create feature branch from current phase branch
2. Make changes following existing patterns
3. Run tests: `pytest -v`
4. Run code quality checks: `pre-commit run --all-files`
5. Commit with descriptive message
6. Push and create PR

### Code Quality Standards

All code must pass:
- ✅ `ruff check` - Linting (max line length 100)
- ✅ `ruff format --check` - Formatting
- ✅ `mypy` - Type checking (strict mode)
- ✅ Pre-commit hooks - Automated checks

## API Documentation

When running the application, interactive API docs are available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Technology Stack

- **Framework**: FastAPI 0.110+
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Authentication**: JWT (python-jose) with bcrypt password hashing
- **Validation**: Pydantic 2.6+
- **Testing**: pytest with pytest-asyncio
- **Code Quality**: ruff (linter/formatter) + mypy (type checking)

## Environment Variables

Key configuration (see `.env.example` for full list):

```bash
# Database
HECTOR_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/hector

# JWT Authentication
HECTOR_JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
HECTOR_JWT_ALGORITHM=HS256
HECTOR_ACCESS_TOKEN_EXPIRE_MINUTES=15
HECTOR_REFRESH_TOKEN_EXPIRE_DAYS=7

# Server
HECTOR_PORT=8000
HECTOR_LOG_LEVEL=INFO
HECTOR_ENVIRONMENT=development
```

## Next Steps

### For Continuing Development

1. **Review Phase 2 Documentation**: Read [docs/phase-2-authentication.md](docs/phase-2-authentication.md)
2. **Understand Authentication System**: See usage examples in documentation
3. **Start Phase 3**: Implement dog profiles and blood type management (T-300+)

### Recommended Improvements (Technical Debt)

- [ ] Email verification flow
- [ ] Password reset flow
- [ ] Rate limiting on authentication endpoints
- [ ] Token revocation/logout (T-207)
- [ ] Audit logging for security events
- [ ] Account lockout after failed login attempts

See [Phase 2 docs - Next Steps](docs/phase-2-authentication.md#next-steps) for details.

## Contributing

1. Follow existing code patterns and structure
2. Add tests for new features (aim for >80% coverage)
3. Update documentation for significant changes
4. Run full test suite and code quality checks before committing
5. Write clear, descriptive commit messages

## License

[Your License Here]

## Support

For questions about Phase 2 implementation, see:
- [Phase 2 Documentation](docs/phase-2-authentication.md)
- [Troubleshooting Guide](docs/phase-2-authentication.md#troubleshooting)
- Project tickets in `Tickets.md`
