#!/usr/bin/env bash
# feedback-cleanup.sh — remove the quarantine directory after the round.
#
# Use after triage is complete (enhancement issues opened, feedback issues
# closed, implementation committed). Removes the round directory and clears
# the .latest-round pointer if it pointed at this round.
#
# Includes a path guard: refuses to clean anything not under
# /tmp/mcc-feedback-quarantine/round-*.

set -euo pipefail

ROUND_DIR="${1:-}"
if [ -z "$ROUND_DIR" ] && [ -f /tmp/mcc-feedback-quarantine/.latest-round ]; then
  ROUND_DIR=$(cat /tmp/mcc-feedback-quarantine/.latest-round)
fi

if [ -z "$ROUND_DIR" ]; then
  echo "no round dir; nothing to clean" >&2
  exit 0
fi

if [ ! -d "$ROUND_DIR" ]; then
  echo "already gone: $ROUND_DIR" >&2
  # Clear the pointer if it referenced a missing dir
  if [ -f /tmp/mcc-feedback-quarantine/.latest-round ] \
     && [ "$(cat /tmp/mcc-feedback-quarantine/.latest-round)" = "$ROUND_DIR" ]; then
    rm -f /tmp/mcc-feedback-quarantine/.latest-round
  fi
  exit 0
fi

# Path guard — refuse to remove anything not under the quarantine base
case "$ROUND_DIR" in
  /tmp/mcc-feedback-quarantine/round-*) ;;
  *)
    echo "refuse to clean: $ROUND_DIR is not under /tmp/mcc-feedback-quarantine/round-*" >&2
    exit 1
    ;;
esac

# Final guard: dir name should match round-<timestamp> pattern
BASENAME=$(basename "$ROUND_DIR")
if ! [[ "$BASENAME" =~ ^round-[0-9]{8}-[0-9]{6}$ ]]; then
  echo "refuse to clean: '$BASENAME' doesn't match round-YYYYMMDD-HHMMSS pattern" >&2
  exit 1
fi

rm -rf "$ROUND_DIR"
echo "Removed: $ROUND_DIR"

LATEST=/tmp/mcc-feedback-quarantine/.latest-round
if [ -f "$LATEST" ] && [ "$(cat "$LATEST")" = "$ROUND_DIR" ]; then
  rm -f "$LATEST"
  echo "Cleared .latest-round pointer"
fi
