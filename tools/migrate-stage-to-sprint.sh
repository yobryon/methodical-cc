#!/bin/bash
#
# Stage-to-Sprint Migration Tool
# Uses Claude Code to intelligently migrate PM terminology from "stage" to "sprint"
#
# Usage:
#   ./migrate-stage-to-sprint.sh [project_path]
#
# If no path provided, uses current directory.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_FILE="$SCRIPT_DIR/migrate-stage-to-sprint.md"

# Get project path
if [ -n "$1" ]; then
    PROJECT_PATH="$(cd "$1" && pwd)"
else
    PROJECT_PATH="$(pwd)"
fi

# Verify the prompt file exists
if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: Prompt file not found: $PROMPT_FILE"
    exit 1
fi

# Verify the project path exists
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project path does not exist: $PROJECT_PATH"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║           Stage → Sprint Terminology Migration                   ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║  This tool uses Claude Code to intelligently migrate your        ║"
echo "║  project management terminology from 'stage' to 'sprint'.        ║"
echo "║                                                                  ║"
echo "║  Claude will:                                                    ║"
echo "║  • Explore your project structure                                ║"
echo "║  • Identify PM artifacts (not domain content)                    ║"
echo "║  • Rename files and update content                               ║"
echo "║  • Report what was changed                                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Project: $PROJECT_PATH"
echo ""

# Confirm before proceeding
read -p "Proceed with migration? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Run mode:"
echo "  [i] Interactive - Claude will ask permission for each change (safer)"
echo "  [a] Autonomous - Claude will make all changes without prompts (faster)"
echo ""
read -p "Choose mode [i/a]: " -n 1 -r MODE
echo ""

echo ""
echo "Starting Claude Code..."
echo ""

cd "$PROJECT_PATH"

if [[ $MODE =~ ^[Aa]$ ]]; then
    # Autonomous mode - bypass permissions
    claude -p --dangerously-skip-permissions "$(cat "$PROMPT_FILE")"
else
    # Interactive mode - will prompt for permissions
    claude -p "$(cat "$PROMPT_FILE")"
fi

echo ""
echo "Migration complete. Review changes with 'git diff' or 'git status'."
echo ""
