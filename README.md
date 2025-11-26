# Hector - Dog Blood Donation Platform

A FastAPI-based platform that connects veterinary clinics in need of blood donations with dog owners whose pets can donate. The platform facilitates urgent matching between clinics and eligible donor dogs.

## Features

- **User Management**: Registration and authentication with role-based access (clinic staff, dog owners, admins)
- **Dog Profiles**: Dog owners can register their dogs with health information and blood type
- **Blood Donation Requests**: Clinics can post urgent requests for specific blood types
- **Response System**: Dog owners can respond to requests with their eligible dogs
- **Blood Type Compatibility**: Smart matching based on canine blood type compatibility
- **Admin Panel**: Platform statistics, user management, and clinic approval workflows

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + asyncpg |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt |
| Package Manager | uv |
| Quality | Ruff + MyPy |
| Testing | Pytest + HTTPX |

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/HalfBakedFullyNuts/Hector.git
cd Hector

# Install dependencies
uv venv
source .venv/bin/activate
uv pip install .[dev]

# Copy environment template
cp .env.example .env
# Edit .env with your database credentials
```

### Database Setup

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
```

### Running the Service

```bash
# Start the server
uv run hector

# Or with hot reload for development
uv run uvicorn hector.app:create_app --factory --reload
```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HECTOR_ENVIRONMENT` | Yes | - | Environment (development, staging, production) |
| `HECTOR_DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `HECTOR_JWT_SECRET_KEY` | No | (insecure default) | JWT signing secret (change in production!) |
| `HECTOR_PORT` | No | 8000 | HTTP server port |
| `HECTOR_LOG_LEVEL` | No | INFO | Logging level |

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get tokens
- `GET /auth/me` - Get current user profile
- `POST /auth/refresh` - Refresh access token

### Dog Profiles
- `POST /dogs` - Create dog profile
- `GET /dogs` - List my dogs
- `GET /dogs/{id}` - Get dog details
- `PUT /dogs/{id}` - Update dog profile
- `DELETE /dogs/{id}` - Delete dog profile
- `POST /dogs/{id}/toggle-availability` - Toggle availability

### Clinics
- `POST /clinics` - Create clinic (requires approval)
- `GET /clinics` - List approved clinics
- `GET /clinics/{id}` - Get clinic details
- `PUT /clinics/{id}` - Update clinic profile

### Donation Requests
- `POST /clinics/requests` - Create donation request
- `GET /clinics/my-requests` - List my clinic's requests
- `GET /requests/browse` - Browse open requests
- `GET /requests/{id}` - Get request details
- `PUT /requests/{id}` - Update request
- `POST /requests/{id}/cancel` - Cancel request
- `GET /requests/compatible` - Get compatible requests for a dog

### Responses
- `POST /requests/{id}/respond` - Respond to a request
- `GET /requests/{id}/responses` - List responses (clinic)
- `GET /my-responses` - List my responses
- `POST /requests/responses/{id}/complete` - Mark donation complete

### Admin
- `GET /admin/users` - List all users
- `POST /admin/users/{id}/toggle-active` - Enable/disable user
- `DELETE /admin/users/{id}` - Delete user
- `GET /admin/stats` - Platform statistics
- `GET /admin/clinics` - List all clinics (including unapproved)
- `POST /admin/clinics/{id}/approve` - Approve clinic
- `POST /admin/clinics/{id}/reject` - Reject clinic

## Development

### Quality Checks

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy src

# Run tests
pytest
```

### Creating Migrations

```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

## Project Structure

```
src/hector/
├── auth/           # Authentication (password, JWT, dependencies)
├── models/         # SQLAlchemy ORM models
├── routers/        # API route handlers
├── schemas/        # Pydantic request/response schemas
├── app.py          # FastAPI application factory
├── config.py       # Settings management
├── database.py     # Database connection
└── main.py         # CLI entry point
```

## License

MIT License - see LICENSE file for details.
