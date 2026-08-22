# Hector MVP Design — Full Spec Completion

- **Date:** 2026-08-22
- **Status:** Approved (design reviewed in chat; scope, environment, and approach confirmed by project owner)
- **Scope:** All tickets T-000 through T-1008 — Phases 1–9 plus all Phase 10 enhancements

---

## 1. Context

Hector is a FastAPI + React platform matching dogs that need blood with donor dogs,
connecting veterinary clinics and dog owners. Development stalled mid-way. Current state:

**Backend (FastAPI 0.141 / SQLAlchemy 2 async / PostgreSQL / Alembic)**
- Routers exist for auth, dogs, clinics, donation requests, admin, health.
- Test suite cannot run: `current_user: CurrentUser = Depends(admin_only)` signatures
  (src/hector/routers/admin.py, src/hector/routers/donation_requests.py) are rejected by
  current FastAPI (`Cannot specify Depends in Annotated and default value together`).
- Alembic migration drifted from models: `clinics` expects `phone_number`/`country`/`owner_id`
  (model has `phone`, none of the others); `blood_donation_requests` has `patient_details`
  (model has `patient_info`). Any clinic/request DB write fails.
- Security gaps: registration accepts any role incl. `ADMIN`; startup logs full Settings
  (incl. JWT secret); no login rate limiting; IDOR on `/requests/compatible`; hard deletes
  destroy donation history; unsafe `decode_token_unsafe` exported; known-default secrets pass
  validation.
- Spec gaps: no pagination on `GET /dogs`; response count hardcoded to 0; no
  `compatibility_score`; admin stats ignore date filters; availability toggle conflated with
  soft-delete flag.

**Frontend (React 19 / Vite / Tailwind v4 / react-hook-form + zod / axios)**
- Builds clean; typecheck clean. Good patterns established in T-905 (DogProfileForm).
- `DEV_MODE = true` hardcoded in AuthContext — auth never touches the backend.
- Mock data in `dogService.getMyDogs`, `donationRequestService.getRequests/getMyResponses`.
- Missing views: Clinic Dashboard (T-901), Create Request form (T-902), Request Details for
  clinic (T-903), Browse Requests (T-906), Respond form (T-907), Admin Users (T-908),
  Admin Clinic Approval (T-909), Admin Stats (T-910). No frontend tests.

## 2. Goals / Non-Goals

**Goals**
1. Every acceptance criterion of T-100…T-704 (backend), T-800…T-910 (frontend), T-1000…T-1008
   (enhancements) met or explicitly deferred with rationale recorded here.
2. Secure by default: no privilege escalation paths, secrets never logged, rate-limited auth.
3. Efficient: no N+1 query patterns in list endpoints; indexed filters; pagination everywhere.
4. High quality: full test suite green against real Postgres, ≥80% backend coverage, zero
   lint/type errors, CI enforcing all gates.
5. A tester can run the whole system locally with Docker and exercise every user journey.

**Non-Goals**
- S3/cloud storage (local filesystem photos only), Redis/Celery (in-process limiter +
  APScheduler), external geocoding APIs (manual/browser lat-lng only).
- Production deployment infrastructure (CI runs tests only).
- Native mobile apps (responsive web satisfies T-1007).

## 3. Key Decisions (ADR-light)

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Full spec scope incl. Phase 10 | Owner choice |
| D2 | Layered approach: stabilize → secure → backend → frontend | Security debt never accumulates; each step lands green |
| D3 | docker-compose.yml provides PostgreSQL 16 for dev/test | Reproducible local env; CI service container |
| D4 | Admins created only via CLI (`hector create-admin`); public registration restricted to `dog_owner`/`clinic_staff` | Closes critical self-registration privilege escalation |
| D5 | Email service defaults to **log mode** (console + `email_log` table); SMTP via env when configured | Testable without SMTP server; spec T-1000 test-mode requirement |
| D6 | Dog photos stored on local disk under `media/dogs/{dog_id}/`; Pillow thumbnails | MVP-simple; S3 explicitly out of scope |
| D7 | Geo matching via Haversine on optional lat/lng (Clinic + User); browser geolocation on frontend; no external geocoder | Offline-testable; city filter remains fallback |
| D8 | In-process IP rate limiter for login failures; APScheduler in-process daily expiry job | No new infra dependencies for MVP |
| D9 | Replace drifted initial Alembic migration with regenerated one | Nothing deployed; single clean baseline beats a fix-forward chain |
| D10 | JWT access/refresh tokens in localStorage per T-900 spec | Matches existing apiClient refresh flow |

## 4. Architecture Overview

Stack unchanged: FastAPI + SQLAlchemy async + PostgreSQL + Alembic; React 19 + Vite +
Tailwind v4 + react-router + axios + react-hook-form/zod.

New backend modules:
```
src/hector/
├── services/
│   ├── email.py          # EmailService: send/log mode, Jinja2 templates
│   ├── photos.py         # validation, storage, thumbnail generation
│   ├── geo.py            # Haversine distance, distance-sorted queries
│   ├── rate_limit.py     # in-process sliding-window login limiter
│   └── compatibility.py  # blood-type matrix + scoring (extracted from router)
├── jobs/
│   └── expire_requests.py  # APScheduler job + startup sweep
└── cli.py                # create-admin command (argparse, no click dep)
```

New/changed persistence:
- `audit_logs(id, actor_user_id FK, action, target_type, target_id, details JSONB, created_at)`
- `email_log(id, recipient, subject, body_text, template, status, related_type, related_id, sent_at)`
- `password_reset_tokens(id, user_id FK, token_hash UNIQUE, expires_at, used_at)`
- `dog_profiles`: add `photo_url` already exists — keep; ensure `is_available_for_donation`
  is independent of soft-delete `is_active`
- `users`: add optional `latitude`, `longitude` (geo matching)
- `clinics`: model already carries lat/lng — verified in migration regen

## 5. Workstreams

### WS1 — Stabilize foundations
- Add `email-validator`, `types-python-jose`, `apscheduler`, `pillow`, `pytest-cov`,
  frontend `vitest`/`@testing-library/react`.
- Convert 6 enums to `enum.StrEnum` (ruff UP042).
- Replace illegal `CurrentUser = Depends(...)` parameter styles with
  `Annotated[User, Depends(RoleChecker(...))]` aliases already defined in auth dependencies.
- Regenerate initial Alembic migration from models (D9); verify upgrade/downgrade round-trip.
- docker-compose.yml: postgres:16 with healthcheck; `.env.example` updated (incl. SMTP vars,
  media path, geolocation note).
- pytest fixtures: session-scoped engine creating schema via metadata (or alembic) against
  compose Postgres; per-test transaction rollback; integration tests no longer skip.

### WS2 — Security hardening
- Registration schema rejects `role=ADMIN` with 422 validation error; CLI create-admin for bootstrap (D4).
- Startup logging redacts secret-bearing fields (mask values, log keys only).
- Login rate limit: max 5 failed attempts / 15 min / IP → 429 with Retry-After (spec T-203);
  successful login resets counter.
- `/requests/compatible`: requires auth; verifies dog ownership before returning eligibility
  data (IDOR fix).
- Soft deletes: `DELETE /dogs/{id}` sets `is_active=False` (204); admin reject clinic soft-
  deletes; all list/read endpoints filter inactive rows.
- Remove `decode_token_unsafe` from jwt module and package exports.
- Config rejects known-default/example JWT secrets at startup.
- Inactive-account login returns 403 "Account disabled" (spec wording).

### WS3 — Backend completion (Phases 3–7 gaps)
- `GET /dogs`: pagination (limit/offset), sorted created_at desc, excludes inactive (T-301).
- `GET /requests/{id}`: real response count via subquery (T-502).
- Compatible listing returns `compatibility_score` (T-604): 100 = DEA 1.1-negative universal
  donor; 75 = exact blood-type match; 50 = compatible because request type unspecified;
  ineligible dogs excluded entirely.
- Admin stats honor start/end date filters (T-703); batch aggregate queries (no per-row loops).
- Route ordering: static segments (`/my-responses`, `/compatible`) declared before
  `/{request_id}`; clinic request listing exposed at `GET /clinics/my-requests` (T-505).
- Audit log entries written on admin toggle/delete/approve/reject (T-701/702/704).
- Availability endpoint semantics: toggles `is_available_for_donation` only (T-305).

### WS4 — Phase 10 backend
- **Email service (T-1000):** async send via aiosmtplib when SMTP configured; otherwise log
  mode writes console + email_log row. Templates in Jinja2. Non-blocking fire-and-forget with
  failure captured in email_log.status.
- **Match notifications (T-1002):** on request creation, notify owners of available eligible
  compatible dogs within   same city (or any if owner has no city); ≤5 emails/user/day enforced
  via email_log count; emails carry a footer unsubscribe link pointing at a documented
  not-yet-functional endpoint (preference management out of MVP scope).
- **Response notifications (T-1003):** on ACCEPTED response, email requesting clinic contact.
- **Photo upload (T-1001):** `POST /dogs/{id}/photo` (multipart): JPEG/PNG only, ≤5 MB,
  ≤2000×2000 px; stores original + 400px thumbnail under media/dogs/{dog_id}/; replaces old
  file; photo served via StaticFiles mount `/media`. Frontend sends via existing dog form.
- **Geo proximity (T-1004):** optional lat/lng on User profile update; `GET /requests`
  accepts `lat`,`lng`,`max_distance_km` → SQL bounding-box prefilter, then Python-side
  Haversine on the bounded result set for exact distance, filtering and sorting (documented
  trade-off vs PostGIS).
- **Expiry automation (T-1005):** APScheduler daily at 00:05 UTC + startup sweep: OPEN requests
  past needed_by_date → EXPIRED; email_log notification to clinic staff.
- **Password reset (T-1008):** `POST /auth/forgot-password` always 200 (no account
  enumeration); creates hashed single-use token valid 1 h; `POST /auth/reset-password` sets
  new password (same strength rules), invalidates token; reset emails via email service.

### WS5 — Frontend completion
- Remove `DEV_MODE`; AuthContext ↔ authService fully wired; logout clears tokens+state.
- Un-mock `getMyDogs`, `getRequests`, `getMyResponses`; delete mock fixtures & artificial
  delays; add `clinicService.ts`, `adminService.ts`.
- Clinic views: Dashboard (request cards w/ urgency color badges, response counts,
  pending-approval banner, create CTA) · Create Request form (zod: volume 50–500 ml, date
  future ≤30 days) · Request Details (accepted/declined sections, dog+owner info, mailto:
  contact links, Mark Fulfilled, Cancel).
- Owner views: Browse Requests (urgency/blood-type/city/distance filters persisted in URL,
  compatibility badge, pagination) · Respond form (dog picker showing eligibility + last
  donation date, accept/decline, message, inline warnings) · wire dead nav targets
  (/owner/requests etc.).
- Admin views: Users table (search/filter/toggle-active/pagination) · Clinic approval queue
  (  pending/approved sections, approve/reject w/ confirm modal) · Stats dashboard (KPI cards;
  pure CSS/SVG bar visuals — no chart library dependency).
- Dog form gains photo upload (preview, progress, error states) hitting T-1001 endpoint.
- Password reset pages wired to T-1008 endpoints.
- Responsive pass (T-1007): mobile nav collapse, tables→cards, touch-target audit.
- ViewAs dev tools remain but compile-time-gated behind DEV build flag only.

### WS6 — Quality gates & verification
- Backend: pytest green incl. integration (compose DB), coverage ≥80% enforced, ruff check +
  format --check, mypy strict, pip-audit in CI.
- Frontend: Vitest + Testing Library covering services (mocked axios) and critical components
  (ProtectedRoute, forms happy/error paths); tsc --noEmit; production build.
- CI (.github/workflows/ci.yml): Postgres service container; matrix job runs backend gates
  then frontend gates.
- Fresh-clone smoke script (`scripts/smoke_test.sh`): compose up → migrate → seed admin →
  register staff+owner → approve clinic → create request → respond → complete → assert dog
  last_donation_date set and emails logged.
- README/docs refreshed to reflect reality (setup, env vars, testing, architecture).

## 6. Error Handling & Observability

- Consistent HTTP error shapes (FastAPI default validation + existing handlers); rate limiter
  adds 429 with Retry-After header.
- X-Request-ID middleware retained; structured logging keeps level config; no PII/secrets in
  logs (asserted by redaction test).

## 7. Testing Strategy

- Unit: services (compatibility matrix table-driven, geo math, rate limiter windows, password
  rules), schemas validators.
- Integration: endpoint suites per router against compose Postgres w/ rollback fixtures —
  including auth flows, ownership/IDOR negatives, soft-delete visibility, rate-limit lockout,
  photo upload constraints (tmp media dir), reset-token lifecycle, expiry job.
- Frontend: Vitest unit/integration as scoped in WS6.
- E2E: scripted smoke test (above) doubles as manual QA entry point.

## 8. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Migration regen loses hand-written bits | Diff old vs new migration; round-trip test upgrade→downgrade→upgrade |
| In-process rate limiter resets on restart | Acceptable MVP trade-off (documented); short access-token window bounds abuse |
| Python-side geo sorting cost | Bounded page sizes + SQL prefilter by bounding box before Haversine |
| APScheduler in dev reload double-run | Job idempotent (only flips OPEN→EXPIRED past date); guard via app state flag |
| Coverage gate blocks legacy code | Fix or explicitly mark thin glue modules; no blanket skips without rationale |

## 9. Acceptance Criteria (MVP done when)

1. All Phase 1–10 ticket acceptance criteria pass or deferrals are recorded in this doc.
2. `docker compose up -d && alembic upgrade head && uvicorn hector.main:app` serves API;
   frontend `npm run dev` completes full journeys for all three roles.
3. Smoke script passes end-to-end from clean state.
4. All quality gates green in CI.
