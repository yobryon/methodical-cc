#!/usr/bin/env bash
# feedback-review.sh — surface scan verdicts for the user's review.
#
# Reads each issue's `.verdict.md.firstline` (CLEAR / CONCERNS / MALFORMED /
# FAILED) and prints status for the user. For non-CLEAR issues, also prints
# the full verdict body so the user can review the scanner's flags.
#
# CRITICAL DISCIPLINE: this script's output is for the *user* to read. The
# orchestrator agent should treat the printed CONCERNS detail as user-bound
# information, not as input for synthesis. The agent's job here is to invoke
# this script and report status counts to the user; the user is the gate.
#
# Approval is explicit: user runs `touch <round>/issue-<N>.approved` for each
# issue they want to release for triage. Until that file exists, the
# orchestrator does not read the issue body.

set -euo pipefail

ROUND_DIR="${1:-}"
if [ -z "$ROUND_DIR" ] && [ -f /tmp/mcc-feedback-quarantine/.latest-round ]; then
  ROUND_DIR=$(cat /tmp/mcc-feedback-quarantine/.latest-round)
fi
[ -z "$ROUND_DIR" ] && { echo "no round dir; run feedback-fetch.sh first" >&2; exit 1; }
[ ! -d "$ROUND_DIR" ] && { echo "round dir not found: $ROUND_DIR" >&2; exit 1; }
[ ! -f "$ROUND_DIR/manifest.txt" ] && { echo "manifest.txt missing in $ROUND_DIR" >&2; exit 1; }

echo "Round directory: $ROUND_DIR"
echo

CLEAR_COUNT=0
CONCERN_COUNT=0
MALFORMED_COUNT=0
APPROVED_COUNT=0
NOT_SCANNED_COUNT=0

while IFS= read -r N; do
  [ -z "$N" ] && continue
  FIRSTLINE_FILE="$ROUND_DIR/issue-$N.verdict.md.firstline"
  VERDICT_FILE="$ROUND_DIR/issue-$N.verdict.md"
  APPROVED_FILE="$ROUND_DIR/issue-$N.approved"

  if [ ! -f "$FIRSTLINE_FILE" ]; then
    echo "Issue #$N — NOT YET SCANNED (run feedback-scan.sh)"
    echo
    NOT_SCANNED_COUNT=$((NOT_SCANNED_COUNT + 1))
    continue
  fi

  STATUS=$(cat "$FIRSTLINE_FILE")
  APPROVED_TAG=""
  if [ -f "$APPROVED_FILE" ]; then
    APPROVED_TAG=" [APPROVED for triage]"
    APPROVED_COUNT=$((APPROVED_COUNT + 1))
  fi

  case "$STATUS" in
    CLEAR)
      CLEAR_COUNT=$((CLEAR_COUNT + 1))
      echo "Issue #$N — CLEAR$APPROVED_TAG"
      if [ -z "$APPROVED_TAG" ]; then
        echo "  scanner found no concerns. To release for triage:"
        echo "    touch $APPROVED_FILE"
      fi
      echo
      ;;
    CONCERNS)
      CONCERN_COUNT=$((CONCERN_COUNT + 1))
      echo "Issue #$N — CONCERNS$APPROVED_TAG"
      echo "  scanner flagged the following:"
      echo "  ──────"
      sed 's/^/  /' "$VERDICT_FILE"
      echo "  ──────"
      if [ -z "$APPROVED_TAG" ]; then
        echo "  Review the flags above. If you decide to triage despite concerns:"
        echo "    touch $APPROVED_FILE"
      fi
      echo
      ;;
    MALFORMED|FAILED)
      MALFORMED_COUNT=$((MALFORMED_COUNT + 1))
      echo "Issue #$N — $STATUS scanner output (treat as CONCERNS)$APPROVED_TAG"
      echo "  ──────"
      sed 's/^/  /' "$VERDICT_FILE" 2>/dev/null || echo "  (verdict file missing)"
      echo "  ──────"
      if [ -z "$APPROVED_TAG" ]; then
        echo "  Review manually before approving. To release anyway:"
        echo "    touch $APPROVED_FILE"
      fi
      echo
      ;;
    *)
      echo "Issue #$N — UNKNOWN STATUS '$STATUS'$APPROVED_TAG"
      echo
      ;;
  esac
done < "$ROUND_DIR/manifest.txt"

echo "Summary"
echo "  CLEAR:        $CLEAR_COUNT"
echo "  CONCERNS:     $CONCERN_COUNT"
echo "  MALFORMED:    $MALFORMED_COUNT"
echo "  Not scanned:  $NOT_SCANNED_COUNT"
echo "  Approved:     $APPROVED_COUNT (ready for orchestrator to read)"
echo
echo "Approve an issue for triage:"
echo "  touch $ROUND_DIR/issue-<N>.approved"
echo
echo "Cleanup at end of round:"
echo "  .claude/scripts/feedback-cleanup.sh"
