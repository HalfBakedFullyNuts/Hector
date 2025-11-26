# Hector Architecture

This document provides a technical overview of the Hector platform architecture.

## System Overview

Hector is a RESTful API service built with FastAPI that facilitates blood donation matching between veterinary clinics and dog owners. The system uses a PostgreSQL database with async SQLAlchemy for data persistence.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                       │
│                   (Web App, Mobile App, CLI)                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Routers    │  │  Middleware  │  │   Auth Dependencies  │  │
│  │  (endpoints) │  │  (request-ID)│  │   (JWT validation)   │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────────┘  │
│         │                                                        │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Schemas    │  │    Models    │  │      Database        │  │
│  │  (Pydantic)  │  │ (SQLAlchemy) │  │   (async sessions)   │  │
│  └──────────────┘  └──────┬───────┘  └──────────┬───────────┘  │
└────────────────────────────┼─────────────────────┼──────────────┘
                             │                     │
                             ▼                     ▼
                    ┌─────────────────────────────────┐
                    │         PostgreSQL Database      │
                    │  (asyncpg connection pool)       │
                    └─────────────────────────────────┘
```

## Directory Structure

```
src/hector/
├── __init__.py              # Package version
├── app.py                   # FastAPI application factory
├── config.py                # Pydantic settings management
├── database.py              # SQLAlchemy engine & sessions
├── logging_config.py        # Structured logging setup
├── main.py                  # CLI entry point (uvicorn)
├── middleware.py            # Request ID middleware
│
├── auth/                    # Authentication module
│   ├── __init__.py          # Public exports
│   ├── password.py          # bcrypt password hashing
│   ├── jwt.py               # JWT token generation/validation
│   └── dependencies.py      # FastAPI auth dependencies
│
├── models/                  # SQLAlchemy ORM models
│   ├── __init__.py          # Model exports
│   ├── base.py              # BaseModel with UUID, timestamps
│   ├── user.py              # User model with roles
│   ├── clinic.py            # Clinic model
│   ├── dog_profile.py       # Dog profile with eligibility
│   ├── donation_request.py  # Blood donation requests
│   └── donation_response.py # Owner responses to requests
│
├── routers/                 # API route handlers
│   ├── __init__.py          # Router aggregation
│   ├── health.py            # Health check endpoint
│   ├── auth.py              # Authentication endpoints
│   ├── dogs.py              # Dog profile CRUD
│   ├── clinics.py           # Clinic management
│   ├── requests.py          # Donation requests
│   ├── responses.py         # Owner response management
│   └── admin.py             # Admin panel endpoints
│
└── schemas/                 # Pydantic schemas
    ├── __init__.py          # Schema exports
    ├── clinic.py            # Clinic input/output
    ├── dog_profile.py       # Dog profile schemas
    ├── donation_request.py  # Request schemas
    └── donation_response.py # Response schemas
```

## Data Models

### Entity Relationship Diagram

```
┌──────────────┐       ┌────────────────────┐
│     User     │       │       Clinic       │
├──────────────┤       ├────────────────────┤
│ id (UUID)    │       │ id (UUID)          │
│ email        │       │ name               │
│ hashed_pass  │       │ address, city      │
│ role (enum)  │       │ phone, email       │
│ is_active    │       │ lat, lng           │
│ is_verified  │       │ is_approved        │
└──────┬───────┘       └─────────┬──────────┘
       │                         │
       │ 1:N                     │ 1:N
       ▼                         ▼
┌──────────────┐       ┌────────────────────┐
│  DogProfile  │       │ BloodDonationReq   │
├──────────────┤       ├────────────────────┤
│ id (UUID)    │       │ id (UUID)          │
│ owner_id(FK) │       │ clinic_id (FK)     │
│ name, breed  │       │ created_by_user_id │
│ date_of_birth│       │ blood_type_needed  │
│ weight_kg    │       │ volume_ml          │
│ blood_type   │       │ urgency (enum)     │
│ last_donation│       │ needed_by_date     │
│ is_active    │       │ status (enum)      │
└──────┬───────┘       └─────────┬──────────┘
       │                         │
       │                         │
       │    ┌────────────────────┘
       │    │ N:1
       ▼    ▼
┌─────────────────────────┐
│   DonationResponse      │
├─────────────────────────┤
│ id (UUID)               │
│ request_id (FK)         │
│ dog_id (FK)             │
│ owner_id (FK)           │
│ status (enum)           │
│ response_message        │
└─────────────────────────┘
```

### Key Enums

**UserRole**
- `clinic_staff` - Can create clinics and donation requests
- `dog_owner` - Can register dogs and respond to requests
- `admin` - Full platform access

**BloodType** (Canine DEA System)
- DEA 1.1 Positive/Negative (most important)
- DEA 1.2, 3, 4, 5, 7 Positive/Negative
- Unknown

**RequestUrgency**
- `CRITICAL` - Immediate need
- `URGENT` - Within 24 hours
- `ROUTINE` - Planned procedure

**RequestStatus**
- `OPEN` - Accepting responses
- `FULFILLED` - Donation completed
- `CANCELLED` - No longer needed
- `EXPIRED` - Past needed_by_date

**ResponseStatus**
- `ACCEPTED` - Owner agrees to donate
- `DECLINED` - Owner declined
- `COMPLETED` - Donation performed

## Authentication Flow

```
1. Registration (/auth/register)
   └─> Create user with hashed password
   └─> Return user profile (no tokens)

2. Login (/auth/login)
   └─> Verify credentials
   └─> Generate access token (15 min)
   └─> Generate refresh token (7 days)
   └─> Return both tokens

3. Protected Request
   └─> Extract Bearer token from header
   └─> Decode and validate JWT
   └─> Load user from database
   └─> Check is_active status
   └─> Check role permissions

4. Token Refresh (/auth/refresh)
   └─> Validate refresh token
   └─> Generate new access token
   └─> Return new tokens
```

### JWT Token Structure

**Access Token Payload:**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "dog_owner",
  "type": "access",
  "exp": 1234567890,
  "iat": 1234567890
}
```

## Blood Type Compatibility

DEA 1.1 Negative dogs are universal donors. The compatibility matrix:

| Donor Type | Can Donate To |
|------------|---------------|
| DEA 1.1 Negative | All types (universal donor) |
| DEA 1.1 Positive | DEA 1.1 Positive only |
| Other Negative | Same type Positive/Negative |
| Other Positive | Same type Positive only |
| Unknown | Not recommended |

## Dog Eligibility Requirements

A dog is eligible for donation if:
- Profile is active
- Weight >= 25 kg
- Age between 1-8 years
- Last donation > 8 weeks ago (if applicable)

## Request/Response Lifecycle

```
1. Clinic creates donation request (OPEN)
   │
2. Dog owners browse compatible requests
   │
3. Owner responds with eligible dog (ACCEPTED)
   │
4. Clinic reviews responses
   │
5. Clinic marks response as COMPLETED
   │  └─> Dog's last_donation_date updated
   │
6. Request can be marked FULFILLED or CANCELLED
```

## Database Connection

- Uses SQLAlchemy 2.0 async API
- Connection pool: 5 base, 10 overflow (configurable)
- Async sessions with automatic rollback on errors
- UUID primary keys for all entities

## Middleware

**Request ID Middleware:**
- Generates unique ID for each request
- Available via `get_request_id()` context var
- Included in all log entries

## Configuration

All settings use `HECTOR_` prefix and are loaded from:
1. Environment variables
2. `.env` file (development)

Required settings:
- `HECTOR_ENVIRONMENT`
- `HECTOR_DATABASE_URL`

## Security Considerations

- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with configurable expiration
- Role-based access control on all protected endpoints
- Input validation via Pydantic schemas
- SQL injection protection via SQLAlchemy ORM
- Soft deletes preserve audit trail

## Performance Notes

- Pagination on all list endpoints (default 20, max 100)
- Eager loading with `selectinload` for N+1 prevention
- Database connection pooling
- Async I/O throughout

## Future Enhancements

See `Tickets.md` for planned features:
- Email notifications
- Geographic proximity matching
- Photo uploads
- Request expiration automation
- Password reset flow
