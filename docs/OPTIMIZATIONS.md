# Hector Optimization Tickets

This document contains identified optimizations, security improvements, and technical debt items discovered during codebase analysis.

## Priority Legend

- **CRITICAL**: Must fix before production
- **HIGH**: Should address soon
- **MEDIUM**: Address when convenient
- **LOW**: Nice to have

---

## Security Issues (CRITICAL)

### SEC-001: Remove Temporary Auth Headers

**Priority**: CRITICAL
**Effort**: High
**Files**: All routers (`clinics.py`, `dogs.py`, `requests.py`, `responses.py`)

**Issue**: `X-User-Id` and `X-Clinic-Id` headers are used for authentication instead of JWT tokens. This allows anyone to impersonate any user or clinic by simply setting these headers.

**Current Code** (clinics.py:52-53):
```python
user_id_header: Annotated[str | None, Header(alias="X-User-Id")] = None,
clinic_id_header: Annotated[str | None, Header(alias="X-Clinic-Id")] = None,
```

**Fix**: Replace all temp header authentication with proper JWT-based auth:
```python
current_user: Annotated[User, Depends(get_current_active_user)]
```

**Affected Endpoints**:
- All clinic endpoints
- All dog profile endpoints
- All request endpoints
- All response endpoints

---

### SEC-002: Fix UUID Type Hint Vulnerability

**Priority**: HIGH
**Effort**: Low
**File**: `src/hector/routers/requests.py:428`

**Issue**: `request_id: str` instead of `UUID` bypasses UUID validation.

**Fix**:
```python
# Before
request_id: str

# After
request_id: UUID
```

---

### SEC-003: Add Rate Limiting

**Priority**: HIGH
**Effort**: Medium
**File**: `src/hector/routers/auth.py`

**Issue**: Authentication endpoints have no rate limiting, making them vulnerable to brute force attacks.

**Fix**: Add slowapi or similar rate limiting:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(...):
```

---

### SEC-004: Add Account Lockout

**Priority**: HIGH
**Effort**: Medium
**File**: `src/hector/models/user.py`, `src/hector/routers/auth.py`

**Issue**: No tracking of failed login attempts; unlimited brute force possible.

**Fix**:
1. Add fields to User model:
```python
failed_login_attempts: Mapped[int] = mapped_column(default=0)
locked_until: Mapped[datetime | None] = mapped_column(nullable=True)
```

2. Implement lockout logic in login endpoint:
```python
if user.locked_until and user.locked_until > datetime.now(UTC):
    raise HTTPException(status_code=423, detail="Account temporarily locked")
```

---

### SEC-005: Require JWT Secret in Production

**Priority**: CRITICAL
**Effort**: Low
**File**: `src/hector/config.py:45`

**Issue**: Default JWT secret is hardcoded and weak.

**Fix**:
```python
@field_validator("jwt_secret_key")
@classmethod
def validate_jwt_secret(cls, v: str, info: ValidationInfo) -> str:
    if info.data.get("environment") == "production" and v == "CHANGE-ME-IN-PRODUCTION":
        raise ValueError("JWT secret must be set in production")
    return v
```

---

### SEC-006: Add Input Length Validation

**Priority**: MEDIUM
**Effort**: Low
**Files**: Schema files

**Issue**: Text fields like `patient_info`, `response_message` have no max_length.

**Fix**:
```python
patient_info: str | None = Field(default=None, max_length=2000)
response_message: str | None = Field(default=None, max_length=1000)
```

---

## Performance Issues

### PERF-001: N+1 Query in Admin User List

**Priority**: HIGH
**Effort**: Medium
**File**: `src/hector/routers/admin.py:150-160`

**Issue**: Gets users then makes N separate queries for dog counts.

**Current Code**:
```python
user_ids = [u.id for u in users]
dog_count_query = select(DogProfile.owner_id, func.count(DogProfile.id))...
```

**Fix**: Use single query with subquery:
```python
dog_count_subquery = (
    select(DogProfile.owner_id, func.count(DogProfile.id).label('dog_count'))
    .group_by(DogProfile.owner_id)
    .subquery()
)
query = (
    select(User, dog_count_subquery.c.dog_count)
    .outerjoin(dog_count_subquery, User.id == dog_count_subquery.c.owner_id)
)
```

---

### PERF-002: N+1 Query in Browse Requests

**Priority**: HIGH
**Effort**: Medium
**Files**: `src/hector/routers/requests.py:127-138`, `src/hector/routers/clinics.py:449-460`

**Issue**: Same response count N+1 pattern in multiple locations.

**Fix**: Same approach as PERF-001 - use aggregation subquery.

---

### PERF-003: Missing Database Indexes

**Priority**: MEDIUM
**Effort**: Low

**A) Clinic email index**
File: `src/hector/models/clinic.py:49`
```python
email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
```

**B) Dog blood type index**
File: `src/hector/models/dog_profile.py:88`
```python
blood_type: Mapped[BloodType | None] = mapped_column(index=True)
```

**C) Composite indexes on BloodDonationRequest**
File: `src/hector/models/donation_request.py`
```python
__table_args__ = (
    Index('idx_request_clinic_status', 'clinic_id', 'status'),
    Index('idx_request_blood_type_status', 'blood_type_needed', 'status'),
)
```

---

### PERF-004: Inefficient Count Query Pattern

**Priority**: LOW
**Effort**: Low
**Files**: All paginated endpoints

**Issue**: Using subquery for count is less efficient.

**Current**:
```python
count_query = select(func.count()).select_from(base_query.subquery())
```

**Better**:
```python
count_query = select(func.count(Model.id)).where(/* same filters */)
```

---

## Code Quality

### OPT-001: Extract Duplicated Enum Mappers

**Priority**: MEDIUM
**Effort**: Low
**Files**: Multiple routers

**Issue**: `_map_blood_type`, `_map_urgency`, `_map_status` duplicated across files.

**Fix**: Create `src/hector/utils/enum_mappers.py`:
```python
def map_blood_type(bt: BloodType | None) -> str | None:
    return bt.value if bt else None

def map_urgency(u: RequestUrgency) -> str:
    return u.value

def map_status(s: RequestStatus) -> str:
    return s.value
```

---

### OPT-002: Extract Pagination Pattern

**Priority**: MEDIUM
**Effort**: Medium

**Issue**: Pagination logic repeated in every list endpoint.

**Fix**: Create reusable pagination dependency:
```python
# src/hector/utils/pagination.py
from pydantic import BaseModel

class PaginationParams(BaseModel):
    limit: int = 20
    offset: int = 0

def get_pagination(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)
```

---

### OPT-003: Move Business Logic to Service Layer

**Priority**: MEDIUM
**Effort**: High

**Issue**: Business logic (eligibility checks, compatibility) embedded in endpoints.

**Fix**: Create service modules:
```
src/hector/services/
├── __init__.py
├── donation_service.py    # Blood type compatibility, eligibility
├── dog_service.py         # Dog profile operations
└── clinic_service.py      # Clinic operations
```

---

### OPT-004: Fix Type Hints Using Any

**Priority**: LOW
**Effort**: Low
**Files**: `routers/responses.py:33`, `routers/admin.py:37`

**Issue**: Using `Any` for datetime fields.

**Fix**:
```python
from datetime import datetime
created_at: datetime  # instead of Any
```

---

## Missing Tests

### TEST-001: Auth Endpoint Tests

**Priority**: HIGH
**Effort**: Medium

Tests needed:
- Register with valid/invalid data
- Login success/failure
- Token refresh
- Protected endpoint access
- Role-based access control

---

### TEST-002: Admin Endpoint Tests

**Priority**: HIGH
**Effort**: Medium

Tests needed:
- List users with filters
- Toggle user active status
- Soft delete user
- Platform statistics
- Clinic approval/rejection

---

### TEST-003: CRUD Operation Tests

**Priority**: HIGH
**Effort**: High

Tests needed for:
- Dog profiles (create, read, update, delete, toggle)
- Clinics (create, read, update)
- Donation requests (full lifecycle)
- Responses (create, complete)

---

### TEST-004: Authorization Tests

**Priority**: HIGH
**Effort**: Medium

Tests needed:
- Cannot modify others' dogs
- Cannot modify others' clinics
- Admin-only endpoints reject non-admins
- Clinic staff permissions

---

### TEST-005: Blood Type Compatibility Tests

**Priority**: MEDIUM
**Effort**: Low

Tests needed:
- Universal donor matching
- Same-type matching
- Unknown type handling
- Compatible requests endpoint

---

## Concurrency & Data Integrity

### RACE-001: Last Donation Date Race Condition

**Priority**: MEDIUM
**Effort**: Medium
**File**: `src/hector/routers/requests.py:712-713`

**Issue**: Concurrent donations could overwrite last_donation_date incorrectly.

**Fix**: Use `SELECT ... FOR UPDATE`:
```python
dog = await db.execute(
    select(DogProfile)
    .where(DogProfile.id == response.dog_id)
    .with_for_update()
)
```

---

### RACE-002: Add Optimistic Locking

**Priority**: LOW
**Effort**: Medium

**Issue**: No version control for concurrent updates.

**Fix**: Add version field to critical models:
```python
version: Mapped[int] = mapped_column(default=1)

# On update:
stmt = update(Model).where(
    Model.id == id,
    Model.version == current_version
).values(version=current_version + 1, ...)
```

---

## Operational

### OPS-001: Add Health Check Dependencies

**Priority**: LOW
**Effort**: Low
**File**: `src/hector/routers/health.py`

**Issue**: Health check doesn't verify database connectivity.

**Fix**:
```python
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}
```

---

### OPS-002: Add Request Logging Middleware

**Priority**: LOW
**Effort**: Low

Add structured logging for all requests:
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    LOG.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": (time.time() - start) * 1000,
        }
    )
    return response
```

---

### OPS-003: Add Prometheus Metrics

**Priority**: LOW
**Effort**: Medium

Add metrics for monitoring:
- Request count by endpoint
- Response time histogram
- Error rate
- Active database connections

---

## Architecture Improvements

### ARCH-001: Move Blood Type Compatibility to Database

**Priority**: LOW
**Effort**: Medium
**File**: `src/hector/routers/requests.py:747-775`

**Issue**: Hardcoded compatibility matrix.

**Fix**: Create database table or configuration file for easier maintenance.

---

### ARCH-002: Add Database Connection Retry

**Priority**: MEDIUM
**Effort**: Low
**File**: `src/hector/database.py`

**Issue**: No retry logic for transient connection failures.

**Fix**: Add tenacity retry decorator:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def get_db():
    ...
```

---

## Summary

| Category | Count | Priority Distribution |
|----------|-------|----------------------|
| Security | 6 | 2 CRITICAL, 3 HIGH, 1 MEDIUM |
| Performance | 4 | 2 HIGH, 1 MEDIUM, 1 LOW |
| Code Quality | 4 | 3 MEDIUM, 1 LOW |
| Tests | 5 | 4 HIGH, 1 MEDIUM |
| Concurrency | 2 | 1 MEDIUM, 1 LOW |
| Operations | 3 | 3 LOW |
| Architecture | 2 | 1 MEDIUM, 1 LOW |
| **Total** | **26** | |

## Recommended Order of Implementation

1. **Immediate** (before any production use):
   - SEC-001: Remove temp auth headers
   - SEC-005: Require JWT secret in production
   - SEC-002: Fix UUID type hint

2. **Short-term** (next sprint):
   - SEC-003: Add rate limiting
   - SEC-004: Add account lockout
   - PERF-001/002: Fix N+1 queries
   - TEST-001/002: Add critical tests

3. **Medium-term** (next month):
   - PERF-003: Add database indexes
   - OPT-001/002: Extract duplicated code
   - TEST-003/004: Complete test coverage

4. **Long-term** (backlog):
   - OPT-003: Service layer refactor
   - OPS-003: Prometheus metrics
   - ARCH-001: Blood type config
