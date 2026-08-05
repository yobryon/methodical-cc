#!/usr/bin/env bash
# feedback-fetch.sh — fetch open methodology-feedback issues into a quarantine.
#
# CRITICAL DISCIPLINE: this script must NOT print issue title or body content
# to stdout/stderr. The orchestrator agent invokes this script and must remain
# unexposed to the untrusted content. Only safe metadata (counts, the round
# directory path, integer issue numbers) goes to stdout/stderr.
#
# Output:
#   stdout: round directory path (single line)
#   stderr: human-readable status (count, repo, label)

set -euo pipefail

REPO="${REPO:-yobryon/methodical-cc}"
LABEL="${LABEL:-methodology-feedback}"
QUARANTINE_BASE="/tmp/mcc-feedback-quarantine"

if ! command -v gh >/dev/null; then
  echo "gh CLI not on PATH — install from https://cli.github.com" >&2
  exit 1
fi

if ! command -v jq >/dev/null; then
  echo "jq not on PATH (gh's --jq depends on it for some operations)" >&2
  # Continue; gh's --jq usually has its own jq embedded
fi

ROUND_DIR="$QUARANTINE_BASE/round-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$ROUND_DIR"

# Fetch ONLY issue numbers — the only trusted identifier we let the
# orchestrator see. Titles and bodies are written to disk separately.
NUMBERS=$(gh issue list \
  --repo "$REPO" \
  --label "$LABEL" \
  --state open \
  --json number \
  --jq '.[].number')

: > "$ROUND_DIR/manifest.txt"

COUNT=0
if [ -n "$NUMBERS" ]; then
  while IFS= read -r N; do
    [ -z "$N" ] && continue
    # Validate that N is a positive integer (defense-in-depth — gh should
    # never return anything else, but we don't trust ourselves either).
    if ! [[ "$N" =~ ^[0-9]+$ ]]; then
      echo "skipping non-integer issue id from gh output" >&2
      continue
    fi

    # Body and title go directly file-to-disk via shell redirection.
    # No process in the orchestrator's context sees the content.
    gh issue view "$N" --repo "$REPO" --json title --jq '.title' \
      > "$ROUND_DIR/issue-$N.title.txt"
    gh issue view "$N" --repo "$REPO" --json body --jq '.body' \
      > "$ROUND_DIR/issue-$N.body.md"

    echo "$N" >> "$ROUND_DIR/manifest.txt"
    COUNT=$((COUNT + 1))
  done <<< "$NUMBERS"
fi

# Track latest round so downstream scripts can find it without the
# orchestrator having to remember and pass paths.
echo "$ROUND_DIR" > "$QUARANTINE_BASE/.latest-round"

# Output: round dir to stdout (orchestrator-safe), human status to stderr
echo "$ROUND_DIR"
echo "fetched $COUNT issues from $REPO label=$LABEL into $ROUND_DIR" >&2
