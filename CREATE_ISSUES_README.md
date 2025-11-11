# Creating GitHub Issues for Hector Platform

I've prepared scripts to create all 109 GitHub issues from the tickets. Due to permission restrictions in my environment, you'll need to run these scripts yourself.

## Quick Start

```bash
# Make the script executable
chmod +x create_all_issues.sh

# Run the script
./create_all_issues.sh
```

This will create all 109 issues organized by phase with proper labels.

## What Gets Created

- **109 GitHub Issues** (T-100 through T-1008)
- **Organized by 10 Phases** with phase labels
- **Priority labels**: priority-p0, priority-p1, priority-p2
- **Size labels**: size-S, size-M, size-L
- **Category labels**: model, api, frontend, admin, etc.

## Labels to Create First

Before running the script, create these labels in your GitHub repository:

### Phase Labels
- `phase-1-database` (color: #0052CC)
- `phase-2-auth` (color: #5319E7)
- `phase-3-dogs` (color: #0E8A16)
- `phase-4-clinics` (color: #006B75)
- `phase-5-requests` (color: #D93F0B)
- `phase-6-responses` (color: #FBCA04)
- `phase-7-admin` (color: #E99695)
- `phase-8-frontend-foundation` (color: #BFD4F2)
- `phase-9-frontend-views` (color: #C5DEF5)
- `phase-10-enhancements` (color: #BFD4F2)

### Priority Labels
- `priority-p0` (color: #B60205) - Critical
- `priority-p1` (color: #D93F0B) - High
- `priority-p2` (color: #FBCA04) - Normal

### Size Labels
- `size-S` (color: #C2E0C6) - 0.5-1 day
- `size-M` (color: #FEF2C0) - 1-2 days
- `size-L` (color: #F9D0C4) - 3-5 days

### Category Labels
- `model` (color: #5319E7)
- `api` (color: #0075CA)
- `frontend` (color: #BFD4F2)
- `admin` (color: #E99695)

## Alternative: Manual Import

If you prefer, you can also create issues manually using the GitHub web interface, copying content from `Tickets.md`.

## Troubleshooting

If you get authentication errors:
```bash
gh auth login
```

If labels don't exist, the script will fail. Create labels first via:
```bash
gh label create "phase-1-database" --color "0052CC"
# ... etc for all labels
```
