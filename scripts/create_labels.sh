#!/bin/bash
# Create all required GitHub labels for Hector platform issues

set -e

REPO="HalfBakedFullyNuts/Hector"

echo "=========================================="
echo "Creating GitHub Labels for Hector Platform"
echo "=========================================="
echo ""

# Function to create a label (idempotent - won't fail if exists)
create_label() {
    local name="$1"
    local color="$2"
    local description="$3"

    echo -n "Creating label: $name... "

    # Try to create, ignore if already exists
    if gh label create "$name" --color "$color" --description "$description" --repo "$REPO" 2>/dev/null; then
        echo "✓ Created"
    else
        # Check if it already exists
        if gh label list --repo "$REPO" | grep -q "^$name"; then
            echo "⊙ Already exists"
        else
            echo "✗ Failed"
        fi
    fi
}

echo "PHASE LABELS"
echo "------------"
create_label "phase-1-database" "0052CC" "Phase 1: Database Foundation"
create_label "phase-2-auth" "5319E7" "Phase 2: Authentication & User Management"
create_label "phase-3-dogs" "0E8A16" "Phase 3: Dog Profile Management"
create_label "phase-4-clinics" "006B75" "Phase 4: Clinic Management"
create_label "phase-5-requests" "D93F0B" "Phase 5: Blood Donation Request Management"
create_label "phase-6-responses" "FBCA04" "Phase 6: Donation Response & Matching"
create_label "phase-7-admin" "E99695" "Phase 7: Admin Features"
create_label "phase-8-frontend-foundation" "BFD4F2" "Phase 8: Frontend Foundation"
create_label "phase-9-frontend-views" "C5DEF5" "Phase 9: Frontend Views"
create_label "phase-10-enhancements" "FEF2C0" "Phase 10: Notifications & Enhancements"

echo ""
echo "PRIORITY LABELS"
echo "---------------"
create_label "priority-p0" "B60205" "P0: Critical - Must have for MVP"
create_label "priority-p1" "D93F0B" "P1: High - Important for MVP"
create_label "priority-p2" "FBCA04" "P2: Normal - Nice to have"

echo ""
echo "SIZE LABELS"
echo "-----------"
create_label "size-S" "C2E0C6" "Small: 0.5-1 day"
create_label "size-M" "FEF2C0" "Medium: 1-2 days"
create_label "size-L" "F9D0C4" "Large: 3-5 days"

echo ""
echo "CATEGORY LABELS"
echo "---------------"
create_label "model" "5319E7" "Database model"
create_label "api" "0075CA" "API endpoint"
create_label "frontend" "BFD4F2" "Frontend UI"
create_label "ui" "C5DEF5" "User Interface"
create_label "admin" "E99695" "Admin features"
create_label "auth" "7057FF" "Authentication & Authorization"
create_label "dog-profiles" "0E8A16" "Dog profile management"
create_label "clinics" "006B75" "Clinic management"
create_label "requests" "D93F0B" "Blood donation requests"
create_label "responses" "FBCA04" "Donation responses"
create_label "enhancement" "84B6EB" "New feature or enhancement"
create_label "infrastructure" "BFD4F2" "Infrastructure & tooling"

echo ""
echo "=========================================="
echo "✓ Label creation complete!"
echo "=========================================="
