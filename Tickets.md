Tickets
========

Ziel: Konkrete, umsetzbare Tickets, damit die Implementierung sofort starten kann. Aktueller Stand: Repo enthält nur `LICENSE`; `Readme.md` und `Playbook.md` sind leer. Dieser Plan führt vom leeren Repo zum lauffähigen Grundgerüst mit Qualitätssicherung.

Hinweise
- Priorität: P0 (kritisch), P1 (hoch), P2 (normal)
- Aufwand: S (0.5–1d), M (1–2d), L (3–5d)

T-000 Scope & MVP definieren (P0, S)
- Ergebnis: Knappe Beschreibung des Produkts, Zielgruppe, 3–5 Kernziele, MVP-Umfang, Nichtziele
- Akzeptanzkriterien:
  - `Readme.md` enthält Projektbeschreibung, MVP-Ziele, grobe Architektur-Skizze
  - Liste der ersten 3–5 User Stories mit Akzeptanzkriterien

T-001 Tech-Stack-Entscheidungen dokumentieren (P0, S)
- Ergebnis: Entscheidung für Programmiersprache, App-Typ (HTTP-API vs. CLI), Paketmanager, Test-Framework, Lizenz- und Security-Vorgaben
- Akzeptanzkriterien:
  - `Playbook.md` Abschnitt „Entscheidungen“ mit: Sprache, Framework, Build, Test, Lint, Format, CI, Deployment-Ziel
  - Falls bis Entscheidungsdatum keine Präferenz: Default auf HTTP-API in Node.js (Express) ODER Python (FastAPI) festhalten und begründen

T-010 Repository-Grundgerüst anlegen (P0, S)
- Ergebnis: Ordnerstruktur und Basiskonventionen
- Akzeptanzkriterien:
  - Verzeichnisstruktur: `src/`, `tests/`, `docs/`, `.github/`
  - `.gitignore` erstellt (passend zum Stack)
  - Initiale Paket-/Projektdatei (z. B. `package.json` oder `pyproject.toml`)

T-011 Umgebungsvariablen und `.env.example` (P0, S)
- Ergebnis: Einheitliches Config-Handling
- Akzeptanzkriterien:
  - `.env.example` mit kommentierten Keys (z. B. `PORT`, `LOG_LEVEL`)
  - Code lädt Config aus ENV; Start schlägt fehl mit hilfreicher Meldung, wenn Pflichtwerte fehlen

T-012 Linting und Formatierung (P1, S)
- Ergebnis: Einheitlicher Stil und schnelle Qualitätschecks
- Akzeptanzkriterien:
  - Linter + Formatter konfiguriert (z. B. ESLint + Prettier oder Ruff/Black)
  - `npm run lint && npm run format` oder äquivalente Befehle vorhanden

T-013 Pre-commit Hooks (optional) (P2, S)
- Ergebnis: Schnelle lokale Checks vor Commits
- Akzeptanzkriterien:
  - Husky / lefthook / pre-commit konfiguriert für Lint, Format und Tests (stubs okay)

T-014 CI: Lint und Tests (P0, S)
- Ergebnis: Automatische Pipeline bei PRs
- Akzeptanzkriterien:
  - GitHub Actions Workflow unter `.github/workflows/ci.yml`
  - Job führt Lint, Format-Check und Tests aus

T-020 Hello-World Service (HTTP-API, Default) (P0, S)
- Ergebnis: Startfähige App mit Health Endpoint
- Akzeptanzkriterien:
  - Startskript: `npm run start` oder äquiv. (z. B. `uvicorn app:app --reload`)
  - `GET /health` liefert `200 OK` mit `{ status: "ok", version }`
  - Logs beim Start mit Port und Environment
  - Alternativ (falls CLI gewählt): Kommando `hector hello` gibt Gruß + Version aus, Exit-Code 0

T-021 Basis-Routing/Kommandostruktur (P1, S)
- Ergebnis: Struktur für zukünftige Endpunkte/Kommandos
- Akzeptanzkriterien:
  - Trennung von Entry-Point, Routing/CLI-Parser und Business-Logik
  - Erste, leere Handler/Kommandos angelegt mit TODO-Kommentaren

T-022 Fehlerbehandlung und Logging (P1, S)
- Ergebnis: Vorhersehbares Fehlerverhalten und brauchbare Logs
- Akzeptanzkriterien:
  - Zentrales Error-Handling (HTTP: 4xx/5xx konsistent; CLI: Exit-Codes)
  - Logger mit Leveln (debug, info, warn, error) und korrelierenden Request-IDs (HTTP)

T-030 Tests: Grundsetup und Smoke-Test (P0, S)
- Ergebnis: Test-Framework + erster Test läuft in CI
- Akzeptanzkriterien:
  - Test-Runner konfiguriert (z. B. Vitest/Jest bzw. Pytest)
  - Smoke-Test: Health-Endpoint (oder CLI-Kommando) testet Exit-Code/Status 200

T-031 Security-Baseline (P1, S)
- Ergebnis: Minimaler Schutz vor gängigen Risiken
- Akzeptanzkriterien:
  - Abhängigkeitsprüfung (z. B. `npm audit`/`pip-audit`) in CI
  - `SECURITY.md` mit Meldeweg
  - Optional: `CODEOWNERS` gepflegt

T-040 Readme befüllen (P0, S)
- Ergebnis: Schnellstart für Entwickler:innen
- Akzeptanzkriterien:
  - Projektbeschreibung, Setup-Schritte, Starten/Tests, ENV-Variablen, Architektur-Übersicht
  - Verweis auf `Playbook.md` für Prozesse/Entscheidungen

T-041 Playbook befüllen (P1, S)
- Ergebnis: Arbeitsweise und Entscheidungen dokumentiert
- Akzeptanzkriterien:
  - Bereiche: Entscheidungsprotokoll (ADR light), Branch-/Release-Strategie, Code-Style, PR-Checkliste

Backlog-Vorlage (für neue Features)
- Titel im Format: `F-XXX Kurzbeschreibung`
- Inhalt: Problem, Zielbild, Akzeptanzkriterien (Given/When/Then), Abhängigkeiten, Risiken, Messbare Metriken

Status der ursprünglichen Tickets
===================================
✅ T-000 bis T-041: Abgeschlossen (FastAPI Scaffolding, CI/CD, Security)

========================================================================
HECTOR BLOOD DONATION PLATFORM - Feature Tickets
========================================================================

PHASE 1: DATABASE FOUNDATION
=============================

T-100 Database Setup & Connection (P0, S)
------------------------------------------
User Story:
As a developer, I want a PostgreSQL database configured, so that I can persist application data.

Acceptance Criteria:
- Given a development environment,
  When I start the application,
  Then it connects successfully to a PostgreSQL database
- Database connection string is configured via environment variables
- Connection pooling is configured (min 5, max 20 connections)
- Database health check endpoint returns connection status
- README updated with database setup instructions

Dependencies: None
Technical Notes:
- Use asyncpg or psycopg3 for async PostgreSQL
- Add to .env.example: DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW


T-101 SQLAlchemy Integration (P0, S)
-------------------------------------
User Story:
As a developer, I want SQLAlchemy ORM configured, so that I can define and query database models.

Acceptance Criteria:
- Given SQLAlchemy is installed,
  When I define a model class,
  Then it can be mapped to database tables
- Async session factory is configured
- Base model class created with common fields (id, created_at, updated_at)
- Dependency injection for database sessions in FastAPI endpoints
- Transaction rollback on errors

Dependencies: T-100
Technical Notes:
- Use SQLAlchemy 2.0+ async API
- Create src/hector/database.py with get_db() dependency


T-102 Alembic Migrations Setup (P0, S)
---------------------------------------
User Story:
As a developer, I want database migrations configured, so that I can version control schema changes.

Acceptance Criteria:
- Given Alembic is installed and configured,
  When I run alembic upgrade head,
  Then all migrations execute successfully
- Alembic env.py configured for async SQLAlchemy
- Initial migration creates base tables
- README includes migration commands (upgrade, downgrade, autogenerate)
- CI runs migrations in test environment

Dependencies: T-101
Technical Notes:
- Use alembic revision --autogenerate for schema detection
- Migration files stored in migrations/versions/


T-103 User Model (P0, S)
------------------------
User Story:
As a developer, I want a User database model, so that I can store user accounts.

Acceptance Criteria:
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

Dependencies: T-101
Technical Notes:
- Use SQLAlchemy Enum for role
- Store passwords as bcrypt hashes (handle in T-201)


T-104 Clinic Model (P0, S)
--------------------------
User Story:
As a clinic staff member, I want my clinic information stored, so that dog owners can identify us.

Acceptance Criteria:
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

Dependencies: T-103
Technical Notes:
- Add PostGIS extension for geographic queries (optional for MVP)


T-105 Dog Profile Model (P0, M)
--------------------------------
User Story:
As a dog owner, I want my dog's profile stored, so that clinics can find suitable donors.

Acceptance Criteria:
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

Dependencies: T-103
Technical Notes:
- Research canine blood types: DEA 1.1, 1.2, 3, 4, 5, 7
- Photo upload handled in separate ticket (T-1001)


T-106 Blood Donation Request Model (P0, M)
-------------------------------------------
User Story:
As a clinic, I want to create blood donation requests, so that dog owners can respond.

Acceptance Criteria:
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

Dependencies: T-104
Technical Notes:
- Auto-expire requests after needed_by_date (background job)


T-107 Donation Response Model (P0, S)
--------------------------------------
User Story:
As a dog owner, I want to respond to donation requests, so that clinics know I'm available.

Acceptance Criteria:
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

Dependencies: T-105, T-106
Technical Notes:
- Consider adding appointment_datetime for scheduled donations


PHASE 2: AUTHENTICATION & USER MANAGEMENT
==========================================

T-200 Password Hashing Utilities (P0, S)
-----------------------------------------
User Story:
As a developer, I want secure password hashing, so that user credentials are protected.

Acceptance Criteria:
- Given a plain text password,
  When I call hash_password(password),
  Then it returns a bcrypt hash
- Given a password and hash,
  When I call verify_password(password, hash),
  Then it returns True if valid, False otherwise
- Bcrypt cost factor is configurable (default 12)
- Unit tests verify hashing and verification
- Timing-safe comparison to prevent timing attacks

Dependencies: None
Technical Notes:
- Use passlib with bcrypt backend
- Create src/hector/auth/password.py


T-201 JWT Token Generation (P0, S)
-----------------------------------
User Story:
As a developer, I want JWT token generation, so that users can authenticate API requests.

Acceptance Criteria:
- Given user credentials,
  When a valid login occurs,
  Then an access token and refresh token are generated
- Access token expires in 15 minutes
- Refresh token expires in 7 days
- Tokens include user_id, email, role in payload
- Secret key loaded from environment variable
- Unit tests for token generation and validation

Dependencies: None
Technical Notes:
- Use python-jose or PyJWT
- Create src/hector/auth/jwt.py
- Add to .env: JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


T-202 User Registration Endpoint (P0, M)
-----------------------------------------
User Story:
As a new user, I want to register an account, so that I can access the platform.

Acceptance Criteria:
- Given valid registration data (email, password, role),
  When I POST /auth/register,
  Then:
    * A new user is created with hashed password
    * Response includes user id and email (no password)
    * HTTP 201 Created is returned
- Given an existing email,
  When I attempt to register,
  Then HTTP 409 Conflict is returned
- Password validation:
  * Minimum 8 characters
  * At least one uppercase, one lowercase, one digit
- Email validation (valid format)
- Integration tests for success and error cases

Dependencies: T-103, T-200
Technical Notes:
- Create Pydantic schemas for request/response
- Hash password before storing
- Return sanitized user data (exclude password)


T-203 User Login Endpoint (P0, M)
----------------------------------
User Story:
As a registered user, I want to log in, so that I can access protected features.

Acceptance Criteria:
- Given valid credentials (email, password),
  When I POST /auth/login,
  Then:
    * User credentials are verified
    * Access and refresh tokens are returned
    * HTTP 200 OK is returned
- Given invalid credentials,
  When I attempt to login,
  Then HTTP 401 Unauthorized with message "Invalid credentials"
- Given an inactive account,
  When I attempt to login,
  Then HTTP 403 Forbidden with message "Account disabled"
- Rate limiting: max 5 failed attempts per 15 minutes per IP
- Integration tests for all scenarios

Dependencies: T-103, T-200, T-201
Technical Notes:
- Return tokens in response body, not cookies (for SPA)
- Log failed login attempts


T-204 Get Current User Endpoint (P0, S)
----------------------------------------
User Story:
As an authenticated user, I want to retrieve my profile, so that I can verify my identity.

Acceptance Criteria:
- Given a valid access token,
  When I GET /auth/me,
  Then my user profile is returned (id, email, role, is_active)
- Given an invalid token,
  When I GET /auth/me,
  Then HTTP 401 Unauthorized is returned
- Given an expired token,
  When I GET /auth/me,
  Then HTTP 401 Unauthorized with message "Token expired"

Dependencies: T-201, T-203
Technical Notes:
- Create get_current_user() dependency for FastAPI
- Use OAuth2PasswordBearer for token extraction


T-205 Refresh Token Endpoint (P1, S)
-------------------------------------
User Story:
As a user, I want to refresh my access token, so that I can stay logged in without re-entering credentials.

Acceptance Criteria:
- Given a valid refresh token,
  When I POST /auth/refresh,
  Then a new access token is returned
- Given an expired refresh token,
  When I POST /auth/refresh,
  Then HTTP 401 Unauthorized is returned
- Given an invalid refresh token,
  When I POST /auth/refresh,
  Then HTTP 401 Unauthorized is returned

Dependencies: T-201, T-203
Technical Notes:
- Refresh tokens should be stored/validated (consider token rotation)


T-206 Role-Based Authorization Middleware (P0, M)
--------------------------------------------------
User Story:
As a developer, I want role-based authorization, so that users can only access permitted endpoints.

Acceptance Criteria:
- Given an endpoint requiring "admin" role,
  When a non-admin user accesses it,
  Then HTTP 403 Forbidden is returned
- Given an endpoint requiring "clinic_staff" role,
  When a clinic staff or admin accesses it,
  Then the request proceeds
- Create decorators for common role checks:
  * require_role(role: UserRole)
  * require_any_role(roles: List[UserRole])
  * require_ownership(resource_owner_id: UUID)
- Unit tests for all authorization scenarios

Dependencies: T-204
Technical Notes:
- Create src/hector/auth/authorization.py
- Use FastAPI Depends for dependency injection


T-207 Logout Endpoint (Token Revocation) (P2, M)
-------------------------------------------------
User Story:
As a user, I want to log out, so that my session is invalidated.

Acceptance Criteria:
- Given a valid access token,
  When I POST /auth/logout,
  Then the token is added to a revocation list
- Given a revoked token,
  When I attempt to access protected endpoints,
  Then HTTP 401 Unauthorized is returned
- Implement token revocation using Redis or database table
- Cleanup expired tokens from revocation list daily

Dependencies: T-203, T-204
Technical Notes:
- Consider using Redis with TTL for token blacklist
- For MVP, can be deferred if using short-lived tokens


PHASE 3: DOG PROFILE MANAGEMENT
================================

T-300 Create Dog Profile Endpoint (P0, M)
------------------------------------------
User Story:
As a dog owner, I want to create a profile for my dog, so that clinics can see my dog is available for donation.

Acceptance Criteria:
- Given valid dog profile data,
  When I POST /dogs,
  Then:
    * A new dog profile is created linked to my user account
    * Response includes the created dog profile
    * HTTP 201 Created is returned
- Validation rules:
  * Name is required (max 100 chars)
  * Weight must be >= 25kg (minimum for donation)
  * Date of birth required, dog must be 1-8 years old
  * Blood type is optional
- Given I'm not authenticated,
  When I POST /dogs,
  Then HTTP 401 Unauthorized is returned
- Integration tests for validation and authorization

Dependencies: T-105, T-204
Technical Notes:
- Auto-set owner_id from authenticated user
- Create Pydantic schema: DogProfileCreate, DogProfileResponse


T-301 List My Dogs Endpoint (P0, S)
------------------------------------
User Story:
As a dog owner, I want to view all my dog profiles, so that I can manage them.

Acceptance Criteria:
- Given I'm authenticated as a dog owner,
  When I GET /dogs,
  Then all my dog profiles are returned (not other users' dogs)
- Response includes pagination (limit, offset)
- Response sorted by created_at descending
- Empty list returned if no dogs

Dependencies: T-105, T-204
Technical Notes:
- Filter by current user's ID from token
- Support query params: limit (default 20), offset (default 0)


T-302 Get Single Dog Profile Endpoint (P0, S)
----------------------------------------------
User Story:
As a dog owner, I want to view a specific dog profile, so that I can review its details.

Acceptance Criteria:
- Given a valid dog ID that I own,
  When I GET /dogs/{dog_id},
  Then the dog profile is returned
- Given a dog ID I don't own,
  When I GET /dogs/{dog_id},
  Then HTTP 403 Forbidden is returned
- Given a non-existent dog ID,
  When I GET /dogs/{dog_id},
  Then HTTP 404 Not Found is returned

Dependencies: T-300, T-206
Technical Notes:
- Use require_ownership check


T-303 Update Dog Profile Endpoint (P0, M)
------------------------------------------
User Story:
As a dog owner, I want to update my dog's profile, so that information stays current.

Acceptance Criteria:
- Given valid update data for my dog,
  When I PUT /dogs/{dog_id},
  Then the dog profile is updated and returned
- Given a dog ID I don't own,
  When I PUT /dogs/{dog_id},
  Then HTTP 403 Forbidden is returned
- Partial updates allowed (PATCH semantics)
- Validation same as create endpoint
- Cannot change owner_id

Dependencies: T-300, T-206
Technical Notes:
- Use Pydantic schema: DogProfileUpdate (all fields optional)


T-304 Delete Dog Profile Endpoint (P1, S)
------------------------------------------
User Story:
As a dog owner, I want to delete a dog profile, so that I can remove dogs no longer available.

Acceptance Criteria:
- Given a dog ID I own,
  When I DELETE /dogs/{dog_id},
  Then:
    * The dog profile is soft-deleted (is_active = False)
    * HTTP 204 No Content is returned
- Given a dog ID I don't own,
  When I DELETE /dogs/{dog_id},
  Then HTTP 403 Forbidden is returned
- Soft delete preserves historical donation responses

Dependencies: T-300, T-206
Technical Notes:
- Add is_active field to DogProfile model
- Filter out inactive dogs from list endpoints


T-305 Mark Dog Available/Unavailable (P1, S)
---------------------------------------------
User Story:
As a dog owner, I want to toggle my dog's availability, so that I can control when they appear in searches.

Acceptance Criteria:
- Given my dog is available,
  When I POST /dogs/{dog_id}/toggle-availability,
  Then is_available_for_donation is set to False
- Given my dog is unavailable,
  When I toggle availability,
  Then is_available_for_donation is set to True
- Response includes updated dog profile

Dependencies: T-300
Technical Notes:
- Simple boolean toggle endpoint


PHASE 4: CLINIC MANAGEMENT
===========================

T-400 Create Clinic Profile Endpoint (P0, M)
---------------------------------------------
User Story:
As a clinic staff member, I want to create a clinic profile, so that we can post donation requests.

Acceptance Criteria:
- Given valid clinic data,
  When I POST /clinics with role=clinic_staff,
  Then:
    * A new clinic is created
    * My user is linked to the clinic
    * is_approved is set to False (requires admin approval)
    * HTTP 201 Created is returned
- Given I'm a dog_owner,
  When I POST /clinics,
  Then HTTP 403 Forbidden is returned
- Required fields: name, address, city, phone, email
- Email validation

Dependencies: T-104, T-204, T-206
Technical Notes:
- Create Pydantic schemas: ClinicCreate, ClinicResponse
- Auto-link creating user to clinic


T-401 Get Clinic Details Endpoint (P0, S)
------------------------------------------
User Story:
As any user, I want to view clinic details, so that I can see who is requesting donations.

Acceptance Criteria:
- Given a valid clinic ID,
  When I GET /clinics/{clinic_id},
  Then clinic details are returned
- Public endpoint (no authentication required)
- Non-existent clinic returns HTTP 404

Dependencies: T-400
Technical Notes:
- Public read access for transparency


T-402 Update Clinic Profile Endpoint (P1, M)
---------------------------------------------
User Story:
As a clinic staff member, I want to update our clinic profile, so that information is accurate.

Acceptance Criteria:
- Given I'm linked to a clinic,
  When I PUT /clinics/{clinic_id},
  Then the clinic is updated
- Given I'm not linked to the clinic,
  When I PUT /clinics/{clinic_id},
  Then HTTP 403 Forbidden is returned
- Admins can update any clinic
- Cannot change is_approved (admin only via T-704)

Dependencies: T-400, T-206
Technical Notes:
- Check user is staff of this clinic or admin


T-403 List All Clinics Endpoint (P1, S)
----------------------------------------
User Story:
As a dog owner, I want to browse all approved clinics, so that I can learn about them.

Acceptance Criteria:
- Given I GET /clinics,
  Then all approved clinics are returned
- Pagination supported (limit, offset)
- Filter by city (query param: ?city=Berlin)
- Sorted by name alphabetically

Dependencies: T-400
Technical Notes:
- Only show is_approved=True to non-admins
- Admins see all clinics


PHASE 5: BLOOD DONATION REQUEST MANAGEMENT
===========================================

T-500 Create Donation Request Endpoint (P0, M)
-----------------------------------------------
User Story:
As a clinic staff member, I want to create a blood donation request, so that dog owners can respond.

Acceptance Criteria:
- Given I'm clinic staff,
  When I POST /requests with valid data,
  Then:
    * A new donation request is created
    * Status is set to OPEN
    * clinic_id is auto-set from my user
    * HTTP 201 Created is returned
- Required fields: blood_type_needed, volume_ml, urgency, needed_by_date
- Validation:
  * volume_ml between 50-500
  * needed_by_date must be in the future
  * needed_by_date within 30 days
- Given I'm not clinic staff,
  When I POST /requests,
  Then HTTP 403 Forbidden is returned

Dependencies: T-106, T-204, T-206, T-400
Technical Notes:
- Create schemas: DonationRequestCreate, DonationRequestResponse
- Auto-populate created_by_user_id from token


T-501 List All Open Donation Requests (P0, M)
----------------------------------------------
User Story:
As a dog owner, I want to see all open donation requests, so that I can find opportunities to help.

Acceptance Criteria:
- Given I GET /requests,
  Then all open requests are returned
- Filters:
  * ?status=OPEN (default)
  * ?blood_type=DEA_1_1_POSITIVE
  * ?urgency=CRITICAL
  * ?city=Berlin (filter by clinic city)
- Sorted by urgency (CRITICAL first), then created_at
- Pagination supported
- Include clinic details in response

Dependencies: T-500
Technical Notes:
- Join with Clinic table for clinic details
- Consider adding geographic distance filter later


T-502 Get Single Donation Request (P0, S)
------------------------------------------
User Story:
As a user, I want to view details of a specific request, so that I can decide whether to respond.

Acceptance Criteria:
- Given a valid request ID,
  When I GET /requests/{request_id},
  Then full request details are returned
- Include clinic information
- Include response count
- Public endpoint (no auth required for transparency)

Dependencies: T-500
Technical Notes:
- Join with Clinic
- Count responses for this request


T-503 Update Donation Request Endpoint (P1, M)
-----------------------------------------------
User Story:
As a clinic staff member, I want to update a donation request, so that I can correct mistakes or update urgency.

Acceptance Criteria:
- Given I'm staff of the clinic that created the request,
  When I PUT /requests/{request_id},
  Then the request is updated
- Cannot update if status is FULFILLED or CANCELLED
- Can update: urgency, needed_by_date, patient_info, volume_ml
- Cannot change: blood_type_needed, status (use separate endpoints)
- Given I'm not the creating clinic,
  Then HTTP 403 Forbidden is returned

Dependencies: T-500, T-206
Technical Notes:
- Check created_by_user's clinic matches authenticated user's clinic


T-504 Cancel Donation Request Endpoint (P1, S)
-----------------------------------------------
User Story:
As a clinic staff member, I want to cancel a request, so that I can close it if no longer needed.

Acceptance Criteria:
- Given I'm staff of the clinic that created the request,
  When I POST /requests/{request_id}/cancel,
  Then status changes to CANCELLED
- Cannot cancel if already FULFILLED
- Given I'm not the creating clinic,
  Then HTTP 403 Forbidden is returned

Dependencies: T-500, T-206
Technical Notes:
- Simple status update endpoint


T-505 List My Clinic's Requests Endpoint (P0, S)
-------------------------------------------------
User Story:
As a clinic staff member, I want to see all my clinic's requests, so that I can manage them.

Acceptance Criteria:
- Given I'm clinic staff,
  When I GET /clinics/my-requests,
  Then all requests created by my clinic are returned
- Filter by status (query param)
- Sorted by created_at descending
- Pagination supported

Dependencies: T-500, T-206
Technical Notes:
- Filter by authenticated user's clinic_id


PHASE 6: DONATION RESPONSE & MATCHING
======================================

T-600 Respond to Donation Request (P0, M)
------------------------------------------
User Story:
As a dog owner, I want to accept or decline a donation request, so that clinics know my availability.

Acceptance Criteria:
- Given I'm a dog owner with a dog profile,
  When I POST /requests/{request_id}/respond,
  Then:
    * A response is created linking my dog to the request
    * status is set to ACCEPTED or DECLINED based on input
    * HTTP 201 Created is returned
- Request body includes: dog_id, status (ACCEPTED/DECLINED), response_message (optional)
- Validation:
  * dog_id must belong to the authenticated user
  * request must be OPEN
  * cannot respond twice with same dog to same request
  * dog must be available_for_donation
  * dog's last_donation_date must be > 8 weeks ago
- Given I already responded with this dog,
  When I POST again,
  Then HTTP 409 Conflict is returned

Dependencies: T-107, T-204, T-206, T-300, T-500
Technical Notes:
- Create schemas: DonationResponseCreate, DonationResponseResponse
- Implement business rules for eligibility


T-601 List Responses to My Request (P0, S)
-------------------------------------------
User Story:
As a clinic staff member, I want to see all responses to my request, so that I can contact donors.

Acceptance Criteria:
- Given I'm staff of the clinic that created a request,
  When I GET /requests/{request_id}/responses,
  Then all responses are returned
- Include dog profile and owner contact information
- Filter by status (ACCEPTED, DECLINED)
- Sorted by created_at

Dependencies: T-600, T-206
Technical Notes:
- Join with DogProfile and User tables
- Only show to clinic staff who owns the request


T-602 List My Dogs' Responses (P0, S)
--------------------------------------
User Story:
As a dog owner, I want to see all my responses, so that I can track my donation history.

Acceptance Criteria:
- Given I'm a dog owner,
  When I GET /my-responses,
  Then all responses for my dogs are returned
- Include request and clinic details
- Filter by status
- Sorted by created_at descending
- Pagination supported

Dependencies: T-600
Technical Notes:
- Filter by authenticated user's dogs


T-603 Mark Response as Completed (P1, S)
-----------------------------------------
User Story:
As a clinic staff member, I want to mark a response as completed, so that I can track successful donations.

Acceptance Criteria:
- Given a response with status=ACCEPTED,
  When I POST /responses/{response_id}/complete,
  Then:
    * Response status changes to COMPLETED
    * Dog's last_donation_date is updated to today
    * HTTP 200 OK is returned
- Given I'm not staff of the clinic that owns the request,
  Then HTTP 403 Forbidden is returned

Dependencies: T-600, T-601, T-206
Technical Notes:
- Update DogProfile.last_donation_date
- Consider sending notification to dog owner


T-604 Blood Type Compatibility Check (P1, M)
---------------------------------------------
User Story:
As a dog owner, I want to see only compatible requests for my dog's blood type, so that I don't waste time.

Acceptance Criteria:
- Given I GET /requests/compatible?dog_id={dog_id},
  Then only compatible requests are returned
- Compatibility rules:
  * DEA 1.1 negative dogs are universal donors (match all)
  * DEA 1.1 positive dogs can only donate to DEA 1.1 positive recipients
  * If request has no blood_type_needed, show all
- Include "compatibility_score" in response
- Dog must be available and eligible (weight, age, last donation)

Dependencies: T-500, T-300
Technical Notes:
- Implement blood type compatibility matrix
- Research canine blood compatibility thoroughly


PHASE 7: ADMIN FEATURES
========================

T-700 List All Users Endpoint (Admin) (P1, M)
----------------------------------------------
User Story:
As an admin, I want to view all users, so that I can manage accounts.

Acceptance Criteria:
- Given I'm an admin,
  When I GET /admin/users,
  Then all users are returned
- Include user count, dog count, clinic association
- Filter by role, is_active, is_verified
- Search by email (query param)
- Pagination and sorting
- Given I'm not an admin,
  Then HTTP 403 Forbidden is returned

Dependencies: T-103, T-206
Technical Notes:
- Create admin router module
- Include related counts via joins


T-701 Enable/Disable User Account (Admin) (P1, S)
--------------------------------------------------
User Story:
As an admin, I want to enable or disable user accounts, so that I can manage access.

Acceptance Criteria:
- Given I'm an admin,
  When I POST /admin/users/{user_id}/toggle-active,
  Then is_active is toggled
- Disabled users cannot log in
- Include reason in request body (optional)
- Audit log entry created

Dependencies: T-700
Technical Notes:
- Check is_active in login endpoint (T-203)


T-702 Delete User Account (Admin) (P2, M)
------------------------------------------
User Story:
As an admin, I want to delete user accounts, so that I can remove inappropriate users.

Acceptance Criteria:
- Given I'm an admin,
  When I DELETE /admin/users/{user_id},
  Then:
    * User is soft-deleted
    * Associated dogs are soft-deleted
    * User cannot log in
    * Historical data preserved
- Cannot delete other admins
- Confirmation required (pass user_id in body)

Dependencies: T-700
Technical Notes:
- Soft delete cascade to related entities
- Preserve audit trail


T-703 View Platform Statistics (Admin) (P2, M)
-----------------------------------------------
User Story:
As an admin, I want to see platform statistics, so that I can monitor usage.

Acceptance Criteria:
- Given I'm an admin,
  When I GET /admin/stats,
  Then I see:
    * Total users (by role)
    * Total dogs
    * Total clinics (approved/pending)
    * Total requests (by status)
    * Total responses (by status)
    * Successful donations this month
- Date range filter (query params)

Dependencies: T-700
Technical Notes:
- Aggregate queries for counts
- Consider caching for performance


T-704 Approve/Reject Clinic (Admin) (P0, M)
--------------------------------------------
User Story:
As an admin, I want to approve clinic registrations, so that only legitimate clinics can post requests.

Acceptance Criteria:
- Given I'm an admin,
  When I POST /admin/clinics/{clinic_id}/approve,
  Then is_approved is set to True
- Given I POST /admin/clinics/{clinic_id}/reject,
  Then clinic is soft-deleted
- Email notification sent to clinic staff
- Approved clinics can create donation requests

Dependencies: T-400, T-700
Technical Notes:
- Add approval workflow
- Email notification in T-1002


PHASE 8: FRONTEND FOUNDATION
=============================

T-800 Frontend Technology Decision (P0, S)
-------------------------------------------
User Story:
As a developer, I want a frontend framework chosen, so that I can start building UI.

Acceptance Criteria:
- Decision documented in Playbook.md
- Options evaluated:
  * Server-side: Jinja2 templates + HTMX
  * SPA: React, Vue, or Svelte
- Justification includes: team skills, complexity, SEO needs
- Initial project structure created

Dependencies: None
Technical Notes:
- For MVP, Jinja2 + HTMX is faster
- For scalability, React/Vue better


T-801 CORS Configuration (P0, S)
---------------------------------
User Story:
As a frontend developer, I want CORS configured, so that my SPA can call the API.

Acceptance Criteria:
- Given CORS middleware is configured,
  When frontend makes requests from allowed origin,
  Then requests succeed
- Allowed origins configurable via environment variable
- Allow credentials (for cookies if needed)
- Allow methods: GET, POST, PUT, DELETE, PATCH
- Allow headers: Content-Type, Authorization

Dependencies: None
Technical Notes:
- Use fastapi.middleware.cors.CORSMiddleware
- Add ALLOWED_ORIGINS to .env


T-802 Static File Serving (P1, S)
----------------------------------
User Story:
As a developer, I want to serve static files (CSS, JS, images), so that the frontend works.

Acceptance Criteria:
- Given static files in static/ directory,
  When I request /static/style.css,
  Then the file is served
- Support for CSS, JS, images, fonts
- Proper MIME types set
- Cache headers configured

Dependencies: T-800
Technical Notes:
- Use FastAPI StaticFiles
- Mount at /static


T-803 Base HTML Templates (P1, M)
----------------------------------
User Story:
As a developer, I want base HTML templates, so that I can build consistent pages.

Acceptance Criteria:
- Given Jinja2 is configured,
  When I render a template,
  Then it inherits from base.html
- base.html includes:
  * DOCTYPE, meta tags
  * CSS framework (Bootstrap or Tailwind)
  * Navigation bar (placeholder)
  * Footer
  * Flash message support
- Templates directory: templates/
- Reusable components: nav.html, footer.html

Dependencies: T-800
Technical Notes:
- Use Jinja2Templates from FastAPI
- Choose CSS framework (recommend Tailwind for modern look)


PHASE 9: FRONTEND VIEWS
========================

T-900 Login/Register Page (P0, M)
----------------------------------
User Story:
As a new user, I want a login/register page, so that I can create an account or sign in.

Acceptance Criteria:
- Given I visit /login,
  When I see the page,
  Then I see:
    * Login form (email, password)
    * Link to register page
    * "Forgot password" link (placeholder)
- Given I visit /register,
  When I see the page,
  Then I see:
    * Registration form (email, password, confirm password, role selector)
    * Link to login page
- Form validation (client-side and server-side)
- Success redirects to appropriate dashboard
- Error messages displayed

Dependencies: T-202, T-203, T-803
Technical Notes:
- Use HTMX for form submission (or vanilla JS)
- Store JWT in localStorage
- Redirect based on role after login


T-901 Clinic Dashboard (P0, L)
-------------------------------
User Story:
As a clinic staff member, I want a dashboard, so that I can manage blood donation requests.

Acceptance Criteria:
- Given I'm logged in as clinic staff,
  When I visit /clinic/dashboard,
  Then I see:
    * List of my clinic's requests (status badges)
    * "Create New Request" button
    * Each request shows: blood type, urgency, date, response count
    * Click request to view details
- Pending approval notice if clinic not approved
- Responsive design (mobile-friendly)

Dependencies: T-500, T-505, T-900
Technical Notes:
- Use cards or table for request list
- Color-code by urgency (red=critical, yellow=urgent, green=routine)


T-902 Create Donation Request Form (P0, M)
-------------------------------------------
User Story:
As a clinic staff member, I want a form to create donation requests, so that I can post new needs.

Acceptance Criteria:
- Given I click "Create New Request",
  When the form loads,
  Then I see fields:
    * Blood type (dropdown, optional)
    * Volume (number input, ml)
    * Urgency (radio buttons)
    * Needed by date (date picker)
    * Patient info (textarea, optional)
- Form validation (required fields, date in future)
- Submit redirects to request detail page
- Cancel button returns to dashboard

Dependencies: T-500, T-901
Technical Notes:
- Use date input type or date picker library
- Pre-fill clinic_id from session


T-903 View Donation Request Details (Clinic) (P0, M)
-----------------------------------------------------
User Story:
As a clinic staff member, I want to view request details and responses, so that I can contact donors.

Acceptance Criteria:
- Given I click a request,
  When the detail page loads,
  Then I see:
    * All request details
    * List of responses (accepted vs declined)
    * Dog details for each response (name, breed, weight, blood type)
    * Owner contact info (email, phone if available)
    * Buttons: Mark as Fulfilled, Cancel Request
- Tabs or sections for Accepted vs Declined responses
- "Contact Owner" button (opens email client)

Dependencies: T-500, T-601, T-901
Technical Notes:
- Show accepted responses prominently
- Include mailto: links for easy contact


T-904 Dog Owner Dashboard (P0, L)
----------------------------------
User Story:
As a dog owner, I want a dashboard, so that I can manage my dogs and see requests.

Acceptance Criteria:
- Given I'm logged in as dog owner,
  When I visit /owner/dashboard,
  Then I see:
    * My dog profiles (cards with photo, name, blood type, availability)
    * "Add New Dog" button
    * Recent donation requests (filtered by compatible blood type)
    * My response history
- Click dog card to edit
- Click request to view details
- Responsive design

Dependencies: T-300, T-301, T-500, T-900
Technical Notes:
- Grid layout for dog cards
- Show compatibility indicator on requests


T-905 Create/Edit Dog Profile Form (P0, M)
-------------------------------------------
User Story:
As a dog owner, I want to add or edit my dog's profile, so that the information is accurate.

Acceptance Criteria:
- Given I click "Add New Dog" or edit existing,
  When the form loads,
  Then I see fields:
    * Name (text)
    * Breed (text)
    * Date of birth (date picker)
    * Weight (number, kg)
    * Blood type (dropdown, optional)
    * Available for donation (checkbox)
    * Health notes (textarea)
    * Photo upload (optional, placeholder for T-1001)
- Form validation (required fields, min weight 25kg)
- Submit redirects to dashboard
- Success message displayed

Dependencies: T-300, T-303, T-904
Technical Notes:
- Calculate age from date of birth
- Show eligibility status (too young, too light, etc.)


T-906 Browse Donation Requests (Dog Owner) (P0, M)
---------------------------------------------------
User Story:
As a dog owner, I want to browse donation requests, so that I can find ways to help.

Acceptance Criteria:
- Given I visit /requests/browse,
  When the page loads,
  Then I see:
    * List of open requests (cards or table)
    * Filters: urgency, blood type, city
    * Each request shows: clinic name, urgency, blood type, date needed
    * "Respond" button on each request
- Highlighted if compatible with my dogs
- Pagination if many requests

Dependencies: T-501, T-604, T-900
Technical Notes:
- Show compatibility badge
- Sort by urgency and date


T-907 Respond to Donation Request Form (P0, M)
-----------------------------------------------
User Story:
As a dog owner, I want to accept or decline a request, so that the clinic knows my decision.

Acceptance Criteria:
- Given I click "Respond" on a request,
  When the form loads,
  Then I see:
    * Request details
    * Dropdown to select my dog
    * Accept/Decline radio buttons
    * Optional message textarea
    * Submit button
- If dog ineligible (last donation too recent), show warning
- Submit creates response and redirects to dashboard
- Success message displayed

Dependencies: T-600, T-906
Technical Notes:
- Validate dog eligibility before submit
- Show last donation date for selected dog


T-908 Admin Panel - User Management (P1, L)
--------------------------------------------
User Story:
As an admin, I want a user management panel, so that I can oversee accounts.

Acceptance Criteria:
- Given I'm logged in as admin,
  When I visit /admin/users,
  Then I see:
    * Table of all users (email, role, active status, created date)
    * Search by email
    * Filter by role, active status
    * Actions: Enable/Disable, View Details
    * Pagination
- Click user to see details (dog count, clinic, activity)

Dependencies: T-700, T-701, T-900
Technical Notes:
- Use data table with sorting
- Inline toggle for enable/disable


T-909 Admin Panel - Clinic Approval (P0, M)
--------------------------------------------
User Story:
As an admin, I want to approve pending clinics, so that only verified clinics can post requests.

Acceptance Criteria:
- Given I'm logged in as admin,
  When I visit /admin/clinics,
  Then I see:
    * List of clinics (pending and approved separately)
    * Each clinic shows: name, address, email, submitted date
    * Actions: Approve, Reject
- Approve button changes status to approved
- Reject button soft-deletes clinic
- Confirmation modal before approve/reject

Dependencies: T-704, T-900
Technical Notes:
- Color-code pending vs approved
- Include notes field for rejection reason


T-910 Admin Panel - Statistics Dashboard (P2, M)
-------------------------------------------------
User Story:
As an admin, I want to see platform statistics, so that I can monitor health of the platform.

Acceptance Criteria:
- Given I'm logged in as admin,
  When I visit /admin/dashboard,
  Then I see:
    * KPI cards: total users, dogs, clinics, requests, donations
    * Charts: requests over time, donations by blood type
    * Recent activity feed
- Date range selector for time-based stats

Dependencies: T-703, T-900
Technical Notes:
- Use Chart.js or similar for visualizations
- Cache stats for performance


PHASE 10: NOTIFICATIONS & ENHANCEMENTS
=======================================

T-1000 Email Service Configuration (P1, S)
-------------------------------------------
User Story:
As a developer, I want email sending configured, so that users receive notifications.

Acceptance Criteria:
- Given SMTP settings in environment,
  When email.send() is called,
  Then email is sent via SMTP
- Support for:
  * SMTP server, port, username, password (env vars)
  * TLS/SSL configuration
  * From address
- Async email sending (non-blocking)
- Test mode (log emails instead of sending)

Dependencies: None
Technical Notes:
- Use fastapi-mail or aiosmtplib
- Add to .env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS


T-1001 Dog Photo Upload (P2, M)
--------------------------------
User Story:
As a dog owner, I want to upload photos of my dog, so that clinics can see them.

Acceptance Criteria:
- Given I'm creating/editing a dog profile,
  When I upload a photo,
  Then:
    * Photo is saved to storage (S3 or local filesystem)
    * Photo URL is stored in dog profile
    * Thumbnail generated
- Validation:
  * File type: JPEG, PNG only
  * Max size: 5MB
  * Image dimensions: max 2000x2000
- Delete old photo when uploading new one

Dependencies: T-300, T-905
Technical Notes:
- Use Pillow for image processing
- Store in /media/dogs/{dog_id}/ or S3 bucket
- Consider using boto3 for S3


T-1002 Email Notifications - New Request Match (P1, M)
-------------------------------------------------------
User Story:
As a dog owner, I want email notifications when a compatible request is posted, so that I can respond quickly.

Acceptance Criteria:
- Given a clinic creates a new request,
  When the request matches my dog's blood type and location,
  Then I receive an email notification
- Email includes:
  * Request details (urgency, blood type, volume)
  * Clinic name and location
  * Link to view and respond
- Unsubscribe link in footer
- Rate limit: max 5 emails per day per user

Dependencies: T-500, T-1000
Technical Notes:
- Background job to match and send emails
- Use email templates (Jinja2)
- Store email preferences in User model


T-1003 Email Notifications - Response Received (P2, M)
-------------------------------------------------------
User Story:
As a clinic staff member, I want email notifications when a donor responds, so that I can follow up.

Acceptance Criteria:
- Given a dog owner responds to my request,
  When the response is created,
  Then I receive an email notification
- Email includes:
  * Dog details (name, breed, blood type)
  * Owner contact information
  * Response message (if provided)
  * Link to view request details
- Only send for ACCEPTED responses (not declined)

Dependencies: T-600, T-1000
Technical Notes:
- Trigger on DonationResponse creation
- Include dog photo if available


T-1004 Geographic Proximity Matching (P2, L)
---------------------------------------------
User Story:
As a dog owner, I want to see requests near me first, so that I can find convenient donation opportunities.

Acceptance Criteria:
- Given dog owner has location set,
  When browsing requests,
  Then requests are sorted by distance
- Show distance in km from clinic
- Filter by max distance (query param)
- Requires:
  * User location (city/postal code or lat/lng)
  * Clinic location (lat/lng)
- Calculate distance using Haversine formula

Dependencies: T-501, T-906
Technical Notes:
- Add lat/lng to User and Clinic models
- Use PostGIS or Python geopy library
- Geocode addresses to coordinates


T-1005 Request Expiration Automation (P1, M)
---------------------------------------------
User Story:
As a system, I want to automatically expire old requests, so that outdated requests don't clutter the system.

Acceptance Criteria:
- Given a request has passed its needed_by_date,
  When the expiration job runs,
  Then status changes to EXPIRED
- Background job runs daily
- Email notification to clinic staff
- Expired requests hidden from public listing

Dependencies: T-500, T-1000
Technical Notes:
- Use APScheduler or Celery for background jobs
- Create src/hector/jobs/expire_requests.py


T-1006 Search and Filtering UI Enhancement (P2, M)
---------------------------------------------------
User Story:
As a user, I want advanced search and filtering, so that I can find relevant information quickly.

Acceptance Criteria:
- Request browsing page includes:
  * Text search (clinic name, patient info)
  * Multi-select filters (blood type, urgency)
  * Date range filter
  * Sort options (date, urgency, distance)
- Filters persist in URL query params
- Live search (debounced)
- Clear all filters button

Dependencies: T-906
Technical Notes:
- Use HTMX or Alpine.js for interactivity
- Backend supports all filter combinations


T-1007 Mobile Responsive Design (P1, M)
----------------------------------------
User Story:
As a user on mobile, I want the site to work well on my phone, so that I can use it anywhere.

Acceptance Criteria:
- Given I visit on a mobile device,
  When pages load,
  Then:
    * Layout adapts to screen size
    * Forms are usable (large touch targets)
    * Tables become cards on mobile
    * Navigation collapses to hamburger menu
- Test on iOS and Android
- Lighthouse mobile score > 90

Dependencies: All frontend tickets
Technical Notes:
- Use Tailwind responsive classes or Bootstrap grid
- Mobile-first approach


T-1008 Password Reset Flow (P2, M)
-----------------------------------
User Story:
As a user who forgot my password, I want to reset it via email, so that I can regain access.

Acceptance Criteria:
- Given I click "Forgot Password",
  When I enter my email,
  Then a reset link is sent to my email
- Reset link expires after 1 hour
- Given I click the reset link,
  When I enter a new password,
  Then my password is updated
- Invalid/expired links show error message

Dependencies: T-203, T-1000
Technical Notes:
- Generate secure token (UUID or JWT)
- Store token in database with expiration
- Create endpoints: /auth/forgot-password, /auth/reset-password/{token}


========================================================================
IMPLEMENTATION NOTES
========================================================================

Suggested Sprint Organization:
- Sprint 1: Database + Auth (T-100 to T-207) - 2 weeks
- Sprint 2: Dogs + Clinics (T-300 to T-403) - 2 weeks
- Sprint 3: Requests + Responses (T-500 to T-604) - 2 weeks
- Sprint 4: Admin + Frontend Foundation (T-700 to T-803) - 2 weeks
- Sprint 5: Core UI (T-900 to T-907) - 3 weeks
- Sprint 6: Admin UI + Enhancements (T-908 to T-1008) - 2 weeks

Total: ~13 weeks for full MVP

Critical Path:
T-100 → T-101 → T-103 → T-200 → T-202 → T-203 → T-204 → T-300 → T-500 → T-600 → T-900 → T-904

Quick Win Early Deliverables:
- End of Week 2: Login/Register working
- End of Week 4: Dog profiles can be created
- End of Week 6: Clinics can post requests
- End of Week 8: End-to-end flow working (create request → respond)
- End of Week 13: Full MVP with admin panel
