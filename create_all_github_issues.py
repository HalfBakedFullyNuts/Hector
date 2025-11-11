#!/usr/bin/env python3
"""
Script to create GitHub issues from Tickets.md
Parses the ticket file and creates issues using gh CLI
"""

import subprocess
import sys

# Ticket data structure
tickets = [
    # PHASE 1: DATABASE FOUNDATION
    {
        "number": "T-100",
        "title": "Database Setup & Connection",
        "labels": ["phase-1-database", "priority-p0", "size-S"],
        "body": """## User Story
As a developer, I want a PostgreSQL database configured, so that I can persist application data.

## Acceptance Criteria
- Given a development environment, When I start the application, Then it connects successfully to a PostgreSQL database
- Database connection string is configured via environment variables
- Connection pooling is configured (min 5, max 20 connections)
- Database health check endpoint returns connection status
- README updated with database setup instructions

## Dependencies
None

## Technical Notes
- Use asyncpg or psycopg3 for async PostgreSQL
- Add to .env.example: DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW

## Priority & Effort
P0 (Critical) | S (0.5-1 day)""",
    },
    {
        "number": "T-101",
        "title": "SQLAlchemy Integration",
        "labels": ["phase-1-database", "priority-p0", "size-S"],
        "body": """## User Story
As a developer, I want SQLAlchemy ORM configured, so that I can define and query database models.

## Acceptance Criteria
- Given SQLAlchemy is installed, When I define a model class, Then it can be mapped to database tables
- Async session factory is configured
- Base model class created with common fields (id, created_at, updated_at)
- Dependency injection for database sessions in FastAPI endpoints
- Transaction rollback on errors

## Dependencies
T-100

## Technical Notes
- Use SQLAlchemy 2.0+ async API
- Create src/hector/database.py with get_db() dependency

## Priority & Effort
P0 (Critical) | S (0.5-1 day)""",
    },
    {
        "number": "T-102",
        "title": "Alembic Migrations Setup",
        "labels": ["phase-1-database", "priority-p0", "size-S"],
        "body": """## User Story
As a developer, I want database migrations configured, so that I can version control schema changes.

## Acceptance Criteria
- Given Alembic is installed and configured, When I run alembic upgrade head, Then all migrations execute successfully
- Alembic env.py configured for async SQLAlchemy
- Initial migration creates base tables
- README includes migration commands (upgrade, downgrade, autogenerate)
- CI runs migrations in test environment

## Dependencies
T-101

## Technical Notes
- Use alembic revision --autogenerate for schema detection
- Migration files stored in migrations/versions/

## Priority & Effort
P0 (Critical) | S (0.5-1 day)""",
    },
    {
        "number": "T-103",
        "title": "User Model",
        "labels": ["phase-1-database", "priority-p0", "size-S", "model"],
        "body": """## User Story
As a developer, I want a User database model, so that I can store user accounts.

## Acceptance Criteria
- Given the User model is defined, When I create a user instance, Then it can be saved to the database with: id (UUID, primary key), email (unique, indexed), hashed_password, role (enum: clinic_staff, dog_owner, admin), is_active (boolean, default True), is_verified (boolean, default False), created_at, updated_at timestamps
- Unique constraint on email
- Index on email and role
- Unit tests for model creation and validation

## Dependencies
T-101

## Technical Notes
- Use SQLAlchemy Enum for role
- Store passwords as bcrypt hashes (handle in T-201)

## Priority & Effort
P0 (Critical) | S (0.5-1 day)""",
    },
]


def create_issue(ticket):
    """Create a single GitHub issue using gh CLI"""
    labels_str = ",".join(ticket["labels"])

    cmd = [
        "gh",
        "issue",
        "create",
        "--title",
        f"{ticket['number']}: {ticket['title']}",
        "--label",
        labels_str,
        "--body",
        ticket["body"],
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✓ Created {ticket['number']}: {ticket['title']}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create {ticket['number']}: {e.stderr}")
        return False


def main():
    print("Creating GitHub issues for Hector Blood Donation Platform...")
    print(f"Total tickets to create: {len(tickets)}")
    print("=" * 60)

    created = 0
    failed = 0

    for ticket in tickets:
        if create_issue(ticket):
            created += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"\nSummary: {created} created, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
