#!/usr/bin/env python3
"""
Detect Multi-Agent Methodology project state.
Outputs a summary for Claude to understand the current project context.
"""

import os
import re
import glob
import json
import sys
from pathlib import Path

def find_project_root():
    """Find the project root by looking for .claude/ directory."""
    # Start from current directory and work up
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return Path.cwd()

def get_claude_md_state(project_root):
    """Extract state from .claude/CLAUDE.md if it exists."""
    claude_md = project_root / ".claude" / "CLAUDE.md"
    if not claude_md.exists():
        return None

    content = claude_md.read_text()

    # Look for Current Sprint marker
    sprint_match = re.search(r'\*\*Current Sprint\*\*:?\s*(\d+|Sprint\s*\d+|Not started)', content, re.IGNORECASE)
    if sprint_match:
        sprint_text = sprint_match.group(1)
        if sprint_text.lower() == "not started":
            return {"sprint": None, "status": "not_started"}
        sprint_num = re.search(r'\d+', sprint_text)
        if sprint_num:
            return {"sprint": int(sprint_num.group()), "status": "in_progress"}

    return {"sprint": None, "status": "unknown"}

def scan_sprint_artifacts(project_root):
    """Scan docs/ for sprint artifacts and infer state."""
    docs_dir = project_root / "docs"
    if not docs_dir.exists():
        return {"highest_sprint": 0, "artifacts": []}

    artifacts = []
    highest_sprint = 0

    patterns = [
        ("implementation_plan", "implementation_plan_sprint*.md"),
        ("implementor_brief", "implementor_brief_sprint*.md"),
        ("implementation_log", "implementation_log_sprint*.md"),
    ]

    for artifact_type, pattern in patterns:
        for f in docs_dir.glob(pattern):
            # Extract sprint number
            match = re.search(r'sprint(\d+)', f.name, re.IGNORECASE)
            if match:
                sprint_num = int(match.group(1))
                highest_sprint = max(highest_sprint, sprint_num)
                artifacts.append({
                    "type": artifact_type,
                    "sprint": sprint_num,
                    "file": str(f.relative_to(project_root))
                })

    # Also check for deltas
    deltas = list(docs_dir.glob("delta_*.md"))

    return {
        "highest_sprint": highest_sprint,
        "artifacts": sorted(artifacts, key=lambda x: (x["sprint"], x["type"])),
        "delta_count": len(deltas)
    }

def check_product_docs(project_root):
    """Check for product documentation."""
    docs_dir = project_root / "docs"
    if not docs_dir.exists():
        return {"exists": False, "files": []}

    # Common product doc patterns
    product_docs = []
    for pattern in ["product_design.md", "architecture.md", "design.md", "roadmap.md"]:
        matches = list(docs_dir.glob(pattern))
        product_docs.extend([str(f.relative_to(project_root)) for f in matches])

    return {"exists": len(product_docs) > 0, "files": product_docs}

def main():
    project_root = find_project_root()

    # Gather state
    claude_state = get_claude_md_state(project_root)
    sprint_artifacts = scan_sprint_artifacts(project_root)
    product_docs = check_product_docs(project_root)

    # Determine overall state
    has_methodology = (project_root / ".claude" / "CLAUDE.md").exists()

    # Build output
    output = []
    output.append("=" * 60)
    output.append("MULTI-AGENT METHODOLOGY - PROJECT STATE DETECTION")
    output.append("=" * 60)
    output.append("")

    if not has_methodology:
        output.append("STATUS: New project (no .claude/CLAUDE.md found)")
        output.append("")
        output.append("This appears to be a new project. To get started:")
        output.append("  - Run /multi-agent-methodology:arch-init to initialize")
        output.append("")
    else:
        # Infer sprint state
        inferred_sprint = None
        if claude_state and claude_state.get("sprint"):
            inferred_sprint = claude_state["sprint"]
        elif sprint_artifacts["highest_sprint"] > 0:
            inferred_sprint = sprint_artifacts["highest_sprint"]

        if inferred_sprint:
            output.append(f"STATUS: In-flight project")
            output.append(f"INFERRED CURRENT SPRINT: {inferred_sprint}")
            output.append("")

            # Show recent artifacts
            if sprint_artifacts["artifacts"]:
                output.append("Recent sprint artifacts:")
                for a in sprint_artifacts["artifacts"][-6:]:  # Last 6
                    output.append(f"  - Sprint {a['sprint']}: {a['type']} ({a['file']})")
                output.append("")

            if sprint_artifacts["delta_count"] > 0:
                output.append(f"Active deltas: {sprint_artifacts['delta_count']}")
                output.append("")
        else:
            output.append("STATUS: Project initialized but no sprints started")
            output.append("")

    if product_docs["exists"]:
        output.append("Product documentation found:")
        for f in product_docs["files"]:
            output.append(f"  - {f}")
        output.append("")

    output.append("-" * 60)
    output.append("If this state is incorrect, please tell me:")
    output.append('  "We\'re actually in sprint X" or "We just completed sprint Y"')
    output.append("-" * 60)

    print("\n".join(output))

if __name__ == "__main__":
    main()
