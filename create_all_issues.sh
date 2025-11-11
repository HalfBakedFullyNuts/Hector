#!/bin/bash
# Complete script to create all 109 GitHub issues for Hector platform
# Run this after creating the required labels in your GitHub repository

set -e

REPO="HalfBakedFullyNuts/Hector"
CREATED=0
FAILED=0

echo "=========================================="
echo "Creating GitHub Issues for Hector Platform"
echo "=========================================="
echo ""

# Function to create an issue
create_issue() {
    local number="$1"
    local title="$2"
    local labels="$3"
    local body="$4"

    echo -n "Creating $number: $title... "

    if gh issue create --repo "$REPO" --title "$number: $title" --label "$labels" --body "$body" > /dev/null 2>&1; then
        echo "✓"
        ((CREATED++))
    else
        echo "✗ FAILED"
        ((FAILED++))
    fi
}

echo "PHASE 1: DATABASE FOUNDATION"
echo "-----------------------------"

create_issue "T-100" "Database Setup & Connection" \
    "phase-1-database,priority-p0,size-S" \
    "## User Story
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
P0 (Critical) | S (0.5-1 day)"
