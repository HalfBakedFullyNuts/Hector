#!/bin/bash
# Script to create GitHub issues from Hector tickets
# Run this script to create all 109 issues in the repository

set -e  # Exit on error

REPO="HalfBakedFullyNuts/Hector"

echo "Creating GitHub issues for Hector Blood Donation Platform..."

# PHASE 1: DATABASE FOUNDATION

gh issue create \
  --repo "$REPO" \
  --title "T-100: Database Setup & Connection" \
  --label "phase-1-database,priority-p0,size-S" \
  --body "$(cat <<'EOF'
## User Story
As a developer, I want a PostgreSQL database configured, so that I can persist application data.

## Acceptance Criteria
- Given a development environment,
  When I start the application,
  Then it connects successfully to a PostgreSQL database
- Database connection string is configured via environment variables
- Connection pooling is configured (min 5, max 20 connections)
- Database health check endpoint returns connection status
- README updated with database setup instructions

## Dependencies
None

## Technical Notes
- Use asyncpg or psycopg3 for async PostgreSQL
- Add to .env.example: DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW

## Priority
P0 (Critical)

## Effort
S (0.5-1 day)
EOF
)"

gh issue create \
  --repo "$REPO" \
  --title "T-101: SQLAlchemy Integration" \
  --label "phase-1-database,priority-p0,size-S" \
  --body "$(cat <<'EOF'
## User Story
As a developer, I want SQLAlchemy ORM configured, so that I can define and query database models.

## Acceptance Criteria
- Given SQLAlchemy is installed,
  When I define a model class,
  Then it can be mapped to database tables
- Async session factory is configured
- Base model class created with common fields (id, created_at, updated_at)
- Dependency injection for database sessions in FastAPI endpoints
- Transaction rollback on errors

## Dependencies
T-100

## Technical Notes
- Use SQLAlchemy 2.0+ async API
- Create src/hector/database.py with get_db() dependency

## Priority
P0 (Critical)

## Effort
S (0.5-1 day)
EOF
)"

gh issue create \
  --repo "$REPO" \
  --title "T-102: Alembic Migrations Setup" \
  --label "phase-1-database,priority-p0,size-S" \
  --body "$(cat <<'EOF'
## User Story
As a developer, I want database migrations configured, so that I can version control schema changes.

## Acceptance Criteria
- Given Alembic is installed and configured,
  When I run alembic upgrade head,
  Then all migrations execute successfully
- Alembic env.py configured for async SQLAlchemy
- Initial migration creates base tables
- README includes migration commands (upgrade, downgrade, autogenerate)
- CI runs migrations in test environment

## Dependencies
T-101

## Technical Notes
- Use alembic revision --autogenerate for schema detection
- Migration files stored in migrations/versions/

## Priority
P0 (Critical)

## Effort
S (0.5-1 day)
EOF
)"

gh issue create \
  --repo "$REPO" \
  --title "T-103: User Model" \
  --label "phase-1-database,priority-p0,size-S,model" \
  --body "$(cat <<'EOF'
## User Story
As a developer, I want a User database model, so that I can store user accounts.

## Acceptance Criteria
- Given the User model is defined,
  When I create a user instance,
  Then it can be saved to the database with:
    * id (UUID, primary key)
    * email (unique, indexed)
    * hashed_password
    * role (enum: clinic_staff, dog_owner, admin)
    * is_active (boolean, default True)
    * is_verified (boolean, default False)
    * created_at, updated_at timestamps
- Unique constraint on email
- Index on email and role
- Unit tests for model creation and validation

## Dependencies
T-101

## Technical Notes
- Use SQLAlchemy Enum for role
- Store passwords as bcrypt hashes (handle in T-201)

## Priority
P0 (Critical)

## Effort
S (0.5-1 day)
EOF
)"

gh issue create \
  --repo "$REPO" \
  --title "T-104: Clinic Model" \
  --label "phase-1-database,priority-p0,size-S,model" \
  --body "$(cat <<'EOF'
## User Story
As a clinic staff member, I want my clinic information stored, so that dog owners can identify us.

## Acceptance Criteria
- Given the Clinic model is defined,
  When a clinic is created,
  Then it stores:
    * id (UUID)
    * name (required)
    * address (text)
    * city (indexed)
    * postal_code
    * phone
    * email
    * latitude, longitude (for geo-matching)
    * is_approved (boolean, default False)
    * created_at, updated_at
- One-to-Many relationship with User (clinic can have multiple staff)
- Unit tests for clinic creation

## Dependencies
T-103

## Technical Notes
- Add PostGIS extension for geographic queries (optional for MVP)

## Priority
P0 (Critical)

## Effort
S (0.5-1 day)
EOF
)"

gh issue create \
  --repo "$REPO" \
  --title "T-105: Dog Profile Model" \
  --label "phase-1-database,priority-p0,size-M,model" \
  --body "$(cat <<'EOF'
## User Story
As a dog owner, I want my dog's profile stored, so that clinics can find suitable donors.

## Acceptance Criteria
- Given the DogProfile model is defined,
  When a dog profile is created,
  Then it stores:
    * id (UUID)
    * owner_id (foreign key to User)
    * name (required)
    * breed
    * date_of_birth
    * weight_kg (float, required)
    * blood_type (enum: DEA_1_1_POSITIVE, DEA_1_1_NEGATIVE, etc.)
    * last_donation_date
    * is_available_for_donation (boolean)
    * health_notes (text)
    * photo_url
    * created_at, updated_at
- One-to-Many relationship: User -> DogProfile
- Validation: weight must be > 0, age must be >= 1 year for donation
- Unit tests for validation rules

## Dependencies
T-103

## Technical Notes
- Research canine blood types: DEA 1.1, 1.2, 3, 4, 5, 7
- Photo upload handled in separate ticket (T-1001)

## Priority
P0 (Critical)

## Effort
M (1-2 days)
EOF
)"

gh issue create \
  --repo "$REPO" \
  --title "T-106: Blood Donation Request Model" \
  --label "phase-1-database,priority-p0,size-M,model" \
  --body "$(cat <<'EOF'
## User Story
As a clinic, I want to create blood donation requests, so that dog owners can respond.

## Acceptance Criteria
- Given the BloodDonationRequest model is defined,
  When a request is created,
  Then it stores:
    * id (UUID)
    * clinic_id (foreign key to Clinic)
    * created_by_user_id (foreign key to User)
    * blood_type_needed (enum, nullable for universal donors)
    * volume_ml (integer, required)
    * urgency (enum: CRITICAL, URGENT, ROUTINE)
    * patient_info (text, optional)
    * needed_by_date (datetime, required)
    * status (enum: OPEN, FULFILLED, CANCELLED, EXPIRED)
    * created_at, updated_at
- Many-to-One relationship: Request -> Clinic
- Index on status, blood_type_needed, created_at
- Validation: volume_ml must be between 50-500ml

## Dependencies
T-104

## Technical Notes
- Auto-expire requests after needed_by_date (background job)

## Priority
P0 (Critical)

## Effort
M (1-2 days)
EOF
)"

gh issue create \
  --repo "$REPO" \
  --title "T-107: Donation Response Model" \
  --label "phase-1-database,priority-p0,size-S,model" \
  --body "$(cat <<'EOF'
## User Story
As a dog owner, I want to respond to donation requests, so that clinics know I'm available.

## Acceptance Criteria
- Given the DonationResponse model is defined,
  When a response is created,
  Then it stores:
    * id (UUID)
    * request_id (foreign key to BloodDonationRequest)
    * dog_id (foreign key to DogProfile)
    * owner_id (foreign key to User)
    * status (enum: ACCEPTED, DECLINED, COMPLETED)
    * response_message (text, optional)
    * created_at, updated_at
- Many-to-One relationships: Response -> Request, Response -> Dog
- Unique constraint: (request_id, dog_id) - can't respond twice with same dog
- Index on request_id, status

## Dependencies
T-105, T-106

## Technical Notes
- Consider adding appointment_datetime for scheduled donations

## Priority
P0 (Critical)

## Effort
S (0.5-1 day)
EOF
)"

echo "✓ Phase 1 complete (8 issues created)"

# Continue with remaining phases...
# Due to length, I'll create a separate script for each phase

echo ""
echo "Phase 1 issues created successfully!"
echo "Run ./create_github_issues_phase2.sh for Phase 2"
