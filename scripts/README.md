# GitHub Issue Creation Scripts

Automated tools to create all 109 GitHub issues for the Hector Blood Donation Platform from `Tickets.md`.

## 📋 Overview

These scripts will:
- Create all required GitHub labels
- Parse `Tickets.md` and create 109 well-formatted issues
- Apply appropriate labels based on phase, priority, size, and category
- Link related issues through dependency references

## 🚀 Quick Start

```bash
# 1. Navigate to scripts directory
cd scripts

# 2. Make scripts executable
chmod +x create_labels.sh
chmod +x create_github_issues.py

# 3. Ensure you're authenticated with gh CLI
gh auth status
# If not authenticated:
gh auth login

# 4. Create labels first
./create_labels.sh

# 5. Create all issues
python3 create_github_issues.py
```

## 📊 What Gets Created

### Labels (35 total)

**Phase Labels (10)**
- `phase-1-database` through `phase-10-enhancements`

**Priority Labels (3)**
- `priority-p0` (Critical)
- `priority-p1` (High)
- `priority-p2` (Normal)

**Size Labels (3)**
- `size-S` (0.5-1 day)
- `size-M` (1-2 days)
- `size-L` (3-5 days)

**Category Labels (13)**
- `model`, `api`, `frontend`, `ui`, `admin`
- `auth`, `dog-profiles`, `clinics`, `requests`, `responses`
- `enhancement`, `infrastructure`

### Issues (109 total)

Organized into 10 phases:
- **Phase 1**: Database Foundation (T-100 to T-107) - 8 issues
- **Phase 2**: Authentication (T-200 to T-207) - 8 issues
- **Phase 3**: Dog Profiles (T-300 to T-305) - 6 issues
- **Phase 4**: Clinic Management (T-400 to T-403) - 4 issues
- **Phase 5**: Blood Donation Requests (T-500 to T-505) - 6 issues
- **Phase 6**: Donation Responses (T-600 to T-604) - 5 issues
- **Phase 7**: Admin Features (T-700 to T-704) - 5 issues
- **Phase 8**: Frontend Foundation (T-800 to T-803) - 4 issues
- **Phase 9**: Frontend Views (T-900 to T-910) - 11 issues
- **Phase 10**: Enhancements (T-1000 to T-1008) - 9 issues

## 🎯 Usage Options

### Create All Issues
```bash
python3 create_github_issues.py
```

### Dry Run (Preview Only)
```bash
python3 create_github_issues.py --dry-run
```

### Create Issues for Specific Phase
```bash
# Only create Phase 1 issues
python3 create_github_issues.py --phase 1
```

### Create a Single Ticket
```bash
python3 create_github_issues.py --ticket T-100
```

### Combine Options
```bash
# Dry run for Phase 2 only
python3 create_github_issues.py --dry-run --phase 2
```

## 📖 Script Details

### `create_labels.sh`
- Bash script to create all GitHub labels
- Idempotent (safe to run multiple times)
- Uses `gh label create` command
- Skips labels that already exist

### `create_github_issues.py`
- Python script to create GitHub issues from Tickets.md
- Parses ticket structure and extracts:
  - User stories
  - Acceptance criteria
  - Dependencies
  - Technical notes
- Automatically assigns appropriate labels
- Supports filtering and dry-run mode

## 🔧 Requirements

- **GitHub CLI (`gh`)**: Version 2.0 or higher
  ```bash
  # Install on macOS
  brew install gh

  # Install on Linux
  sudo apt install gh

  # Install on Windows
  winget install GitHub.cli
  ```

- **Python 3**: Version 3.7 or higher (for the Python script)
  ```bash
  python3 --version
  ```

- **Authentication**: Must be logged into GitHub
  ```bash
  gh auth login
  ```

## 📝 Issue Format

Each created issue includes:

```markdown
## User Story
As a [role], I want [feature], so that [benefit]

## Acceptance Criteria
- Given [context]
  When [action]
  Then [outcome]

## Dependencies
T-XXX, T-YYY (or None)

## Technical Notes
- Implementation guidance
- Library recommendations
- Architecture decisions

## Priority & Effort
P0 (Critical) | S (0.5-1 day)
```

## 🐛 Troubleshooting

### "gh: command not found"
Install GitHub CLI:
```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh
```

### "HTTP 401: Bad credentials"
Authenticate with GitHub:
```bash
gh auth login
```

### "Label not found"
Run the label creation script first:
```bash
./create_labels.sh
```

### "Permission denied"
Make scripts executable:
```bash
chmod +x create_labels.sh create_github_issues.py
```

### "No module named 'subprocess'"
You're using Python 2. Use Python 3:
```bash
python3 create_github_issues.py
```

## 📂 File Structure

```
scripts/
├── README.md                  # This file
├── create_labels.sh          # Label creation script
└── create_github_issues.py   # Issue creation script
```

## 🔍 Verifying Results

After running the scripts:

```bash
# List all issues
gh issue list --limit 200

# List issues by label
gh issue list --label "phase-1-database"
gh issue list --label "priority-p0"

# View specific issue
gh issue view 1
```

## 🚦 Recommended Workflow

1. **First time setup** (one-time):
   ```bash
   gh auth login
   chmod +x *.sh *.py
   ```

2. **Create labels** (one-time):
   ```bash
   ./create_labels.sh
   ```

3. **Test with dry run**:
   ```bash
   python3 create_github_issues.py --dry-run --phase 1
   ```

4. **Create Phase 1** (to verify everything works):
   ```bash
   python3 create_github_issues.py --phase 1
   ```

5. **Create all remaining issues**:
   ```bash
   python3 create_github_issues.py
   ```

## 📊 Expected Output

```
==========================================================
Hector Platform - GitHub Issue Creator
==========================================================

📖 Parsing Tickets.md...
✓ Found 109 tickets

🚀 Creating 109 issues...

[1/109] ✓ T-100: Database Setup & Connection
  https://github.com/HalfBakedFullyNuts/Hector/issues/1

[2/109] ✓ T-101: SQLAlchemy Integration
  https://github.com/HalfBakedFullyNuts/Hector/issues/2

...

==========================================================
SUMMARY
==========================================================
✓ Created: 109
==========================================================
```

## 💡 Tips

- Use `--dry-run` first to preview what will be created
- Create issues phase by phase if you prefer incremental approach
- Labels can be edited later via GitHub web interface
- Issues can be closed/deleted if needed via `gh issue close` or `gh issue delete`

## 📞 Support

If you encounter issues:
1. Check that `gh` CLI is authenticated: `gh auth status`
2. Verify you have write access to the repository
3. Ensure labels exist: `gh label list`
4. Try with `--dry-run` to see what would be created

## 🎉 What's Next

After creating all issues:
1. Create a GitHub Project board
2. Organize issues into sprints/milestones
3. Start with Phase 1: Database Foundation
4. Reference ticket numbers in commits: `git commit -m "Implement T-100: Database setup"`
