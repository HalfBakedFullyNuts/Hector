#!/usr/bin/env python3
"""
Automated GitHub Issue Creator for Hector Platform
Parses Tickets.md and creates 109 GitHub issues with proper labels and formatting
"""

import re
import subprocess
import sys
from pathlib import Path

# Phase to label mapping
PHASE_LABELS = {
    1: "phase-1-database",
    2: "phase-2-auth",
    3: "phase-3-dogs",
    4: "phase-4-clinics",
    5: "phase-5-requests",
    6: "phase-6-responses",
    7: "phase-7-admin",
    8: "phase-8-frontend-foundation",
    9: "phase-9-frontend-views",
    10: "phase-10-enhancements",
}


def parse_tickets_file():
    """Parse Tickets.md and extract all ticket information"""
    tickets = []
    tickets_file = Path(__file__).parent.parent / "Tickets.md"

    with open(tickets_file, encoding="utf-8") as f:
        content = f.read()

    # Find all ticket sections
    # Pattern: T-XXX Title (PX, Size)

    # Split by phase sections
    phases = re.split(r"PHASE \d+:", content)

    current_phase = 0
    for phase_content in phases[1:]:  # Skip first split (header)
        current_phase += 1

        # Find all tickets in this phase
        lines = phase_content.split("\n")
        current_ticket = None

        for i, line in enumerate(lines):
            # Match ticket header
            match = re.match(r"^(T-\d{3,4})\s+(.+?)\s+\((P\d),\s*([SML])\)", line)
            if match:
                if current_ticket:
                    tickets.append(current_ticket)

                ticket_num, title, priority, size = match.groups()
                current_ticket = {
                    "number": ticket_num,
                    "title": title.strip(),
                    "priority": priority,
                    "size": size,
                    "phase": current_phase,
                    "user_story": "",
                    "acceptance_criteria": "",
                    "dependencies": "",
                    "technical_notes": "",
                    "body_lines": [],
                }
                continue

            if current_ticket and i < len(lines) - 1:
                current_ticket["body_lines"].append(line)

        if current_ticket:
            tickets.append(current_ticket)

    return tickets


def extract_ticket_sections(body_lines):
    """Extract structured sections from ticket body"""
    sections = {
        "user_story": [],
        "acceptance_criteria": [],
        "dependencies": [],
        "technical_notes": [],
    }

    current_section = None

    for line in body_lines:
        line_lower = line.lower().strip()

        if line_lower.startswith("user story:"):
            current_section = "user_story"
            continue
        elif line_lower.startswith("acceptance criteria:"):
            current_section = "acceptance_criteria"
            continue
        elif line_lower.startswith("dependencies:"):
            current_section = "dependencies"
            continue
        elif line_lower.startswith("technical notes:"):
            current_section = "technical_notes"
            continue
        elif line.startswith("T-") or line.startswith("PHASE"):
            break

        if current_section and line.strip():
            sections[current_section].append(line)

    return sections


def format_issue_body(ticket):
    """Format the GitHub issue body"""
    sections = extract_ticket_sections(ticket["body_lines"])

    # Format sections with fallback text
    user_story = (
        chr(10).join(sections["user_story"]).strip()
        if sections["user_story"]
        else "See ticket description"
    )
    acceptance = (
        chr(10).join(sections["acceptance_criteria"]).strip()
        if sections["acceptance_criteria"]
        else "See ticket description"
    )
    dependencies = (
        chr(10).join(sections["dependencies"]).strip() if sections["dependencies"] else "None"
    )
    tech_notes = (
        chr(10).join(sections["technical_notes"]).strip()
        if sections["technical_notes"]
        else "See ticket description"
    )
    priority_info = (
        f"{ticket['priority']} ({get_priority_name(ticket['priority'])}) | "
        f"{ticket['size']} ({get_size_estimate(ticket['size'])})"
    )

    body = f"""## User Story
{user_story}

## Acceptance Criteria
{acceptance}

## Dependencies
{dependencies}

## Technical Notes
{tech_notes}

## Priority & Effort
{priority_info}

---
*This issue was automatically created from Tickets.md*
"""
    return body


def get_priority_name(priority):
    """Get priority description"""
    return {"P0": "Critical", "P1": "High", "P2": "Normal"}.get(priority, priority)


def get_size_estimate(size):
    """Get size estimate description"""
    return {"S": "0.5-1 day", "M": "1-2 days", "L": "3-5 days"}.get(size, size)


def get_labels(ticket):
    """Generate labels for the ticket"""
    labels = []

    # Phase label
    labels.append(PHASE_LABELS.get(ticket["phase"], f"phase-{ticket['phase']}"))

    # Priority label
    labels.append(f"priority-{ticket['priority'].lower()}")

    # Size label
    labels.append(f"size-{ticket['size']}")

    # Category labels based on ticket number ranges
    num = int(ticket["number"].split("-")[1])
    if 100 <= num < 108:
        labels.append("model")
    elif 200 <= num < 300:
        labels.append("api")
        labels.append("auth")
    elif 300 <= num < 400:
        labels.append("api")
        labels.append("dog-profiles")
    elif 400 <= num < 500:
        labels.append("api")
        labels.append("clinics")
    elif 500 <= num < 600:
        labels.append("api")
        labels.append("requests")
    elif 600 <= num < 700:
        labels.append("api")
        labels.append("responses")
    elif 700 <= num < 800:
        labels.append("api")
        labels.append("admin")
    elif 800 <= num < 900:
        labels.append("frontend")
        labels.append("infrastructure")
    elif 900 <= num < 1000:
        labels.append("frontend")
        labels.append("ui")
    elif num >= 1000:
        labels.append("enhancement")

    return labels


def create_github_issue(ticket, dry_run=False):
    """Create a GitHub issue using gh CLI"""
    labels = get_labels(ticket)
    body = format_issue_body(ticket)

    title = f"{ticket['number']}: {ticket['title']}"
    labels_str = ",".join(labels)

    if dry_run:
        print(f"\n{'=' * 60}")
        print(f"Would create: {title}")
        print(f"Labels: {labels_str}")
        print(f"Body preview (first 200 chars):\n{body[:200]}...")
        return True

    cmd = ["gh", "issue", "create", "--title", title, "--label", labels_str, "--body", body]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()
        print(f"✓ {ticket['number']}: {ticket['title']}")
        print(f"  {issue_url}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {ticket['number']}: Failed - {e.stderr}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Create GitHub issues from Tickets.md")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be created without creating"
    )
    parser.add_argument("--phase", type=int, help="Only create issues for a specific phase (1-10)")
    parser.add_argument("--ticket", help="Only create a specific ticket (e.g., T-100)")
    args = parser.parse_args()

    print("=" * 60)
    print("Hector Platform - GitHub Issue Creator")
    print("=" * 60)

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No issues will be created\n")

    # Parse tickets
    print("\n📖 Parsing Tickets.md...")
    tickets = parse_tickets_file()
    print(f"✓ Found {len(tickets)} tickets\n")

    # Filter tickets if requested
    if args.phase:
        tickets = [t for t in tickets if t["phase"] == args.phase]
        print(f"📌 Filtered to Phase {args.phase}: {len(tickets)} tickets\n")

    if args.ticket:
        tickets = [t for t in tickets if t["number"] == args.ticket]
        print(f"📌 Filtered to {args.ticket}: {len(tickets)} ticket(s)\n")

    if not tickets:
        print("❌ No tickets match the filters")
        return 1

    # Create issues
    print(f"🚀 Creating {len(tickets)} issues...\n")

    created = 0
    failed = 0

    for i, ticket in enumerate(tickets, 1):
        print(f"\n[{i}/{len(tickets)}] ", end="")
        if create_github_issue(ticket, dry_run=args.dry_run):
            created += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Created: {created}")
    if failed > 0:
        print(f"✗ Failed: {failed}")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
