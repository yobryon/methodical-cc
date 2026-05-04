#!/usr/bin/env bash
# feedback-scan.sh — run the locked-down security scan over quarantined issues.
#
# For each issue listed in <round>/manifest.txt:
#   - Build prompt = preamble + delimited untrusted payload + epilogue
#   - Pipe via stdin to a heavily locked-down `claude -p` invocation
#   - Parse the verdict (first line) into CLEAR / CONCERNS / MALFORMED
#   - Write verdict file + a one-token `.firstline` summary
#
# Tag-based delimiters use a fresh random value per invocation that the
# attacker writing the issue could not have predicted.
#
# CRITICAL DISCIPLINE: this script never echoes payload content. The
# verdict file (issue-<N>.verdict.md) is for the user to read. The
# orchestrator agent only reads `issue-<N>.verdict.md.firstline`
# (which contains exactly CLEAR | CONCERNS | MALFORMED | FAILED).

set -euo pipefail

ROUND_DIR="${1:-}"
if [ -z "$ROUND_DIR" ] && [ -f /tmp/mcc-feedback-quarantine/.latest-round ]; then
  ROUND_DIR=$(cat /tmp/mcc-feedback-quarantine/.latest-round)
fi
[ -z "$ROUND_DIR" ] && { echo "no round dir; run feedback-fetch.sh first" >&2; exit 1; }
[ ! -d "$ROUND_DIR" ] && { echo "round dir not found: $ROUND_DIR" >&2; exit 1; }
[ ! -f "$ROUND_DIR/manifest.txt" ] && { echo "manifest.txt missing in $ROUND_DIR" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREAMBLE_FILE="$SCRIPT_DIR/prompts/incoming-feedback-safety-scan.preamble.md"
EPILOGUE_FILE="$SCRIPT_DIR/prompts/incoming-feedback-safety-scan.epilogue.md"

[ ! -f "$PREAMBLE_FILE" ] && { echo "preamble missing: $PREAMBLE_FILE" >&2; exit 1; }
[ ! -f "$EPILOGUE_FILE" ] && { echo "epilogue missing: $EPILOGUE_FILE" >&2; exit 1; }

if ! command -v claude >/dev/null; then
  echo "claude CLI not on PATH" >&2; exit 1
fi
if ! command -v openssl >/dev/null; then
  echo "openssl required for random tag generation" >&2; exit 1
fi

scan_one() {
  local N="$1"
  local TITLE_FILE="$ROUND_DIR/issue-$N.title.txt"
  local BODY_FILE="$ROUND_DIR/issue-$N.body.md"
  local PROMPT_FILE="$ROUND_DIR/issue-$N.prompt.tmp"
  local VERDICT_FILE="$ROUND_DIR/issue-$N.verdict.md"
  local FIRSTLINE_FILE="$ROUND_DIR/issue-$N.verdict.md.firstline"
  local STDERR_FILE="$ROUND_DIR/issue-$N.scan-stderr"

  if [ ! -f "$TITLE_FILE" ] || [ ! -f "$BODY_FILE" ]; then
    echo "MISSING" > "$FIRSTLINE_FILE"
    echo "  ! issue $N: title or body file missing"
    return
  fi

  # Random delimiter tag — uppercase hex, 16 chars
  local TAG
  TAG="UNTRUSTED_$(openssl rand -hex 8 | tr '[:lower:]' '[:upper:]')"

  # Build the prompt: preamble (with tag substituted) + delimited payload
  # + epilogue (with tag substituted). Body content goes file-to-file via
  # shell redirection only — no process in the orchestrator's context
  # touches the content.
  {
    sed "s/{{TAG}}/$TAG/g" "$PREAMBLE_FILE"
    printf '\n'
    printf '<BEGIN %s>\n' "$TAG"
    printf '## Issue title (untrusted)\n\n'
    cat "$TITLE_FILE"
    printf '\n\n## Issue body (untrusted)\n\n'
    cat "$BODY_FILE"
    printf '\n<END %s>\n\n' "$TAG"
    sed "s/{{TAG}}/$TAG/g" "$EPILOGUE_FILE"
  } > "$PROMPT_FILE"

  # Sandboxed claude invocation. The agent inside has:
  #   --bare                      no hooks, LSP, plugin sync, attribution,
  #                               auto-memory, background prefetches,
  #                               keychain reads, or CLAUDE.md auto-discovery
  #   --tools ""                  no built-in tools at all
  #   --disable-slash-commands    no skill resolution
  #   --strict-mcp-config         no MCP servers (no --mcp-config given)
  #   --settings '{}'             override any settings the env might inject
  #   --no-session-persistence    sessions not saved to disk
  #   --no-chrome                 no Chrome integration
  #   --permission-mode dontAsk   moot with no tools but extra safety
  #   --max-budget-usd 0.50       cap runaway API spend
  #
  # The agent is reduced to a pure text-in-text-out function.
  if ! claude -p \
      --bare \
      --tools "" \
      --disable-slash-commands \
      --strict-mcp-config \
      --settings '{}' \
      --no-session-persistence \
      --no-chrome \
      --permission-mode dontAsk \
      --max-budget-usd 0.50 \
      --input-format text \
      --output-format text \
      < "$PROMPT_FILE" \
      > "$VERDICT_FILE" \
      2> "$STDERR_FILE"; then
    echo "FAILED" > "$FIRSTLINE_FILE"
    echo "  ! issue $N: scan invocation failed (stderr in $STDERR_FILE)"
    rm -f "$PROMPT_FILE"
    return
  fi

  # Fail-closed first-line parse. Anything other than the literal token
  # CLEAR (with optional whitespace) gets treated as a non-CLEAR verdict.
  local FIRST
  FIRST=$(head -1 "$VERDICT_FILE" | tr -d '[:space:]')
  case "$FIRST" in
    CLEAR)
      echo "CLEAR" > "$FIRSTLINE_FILE"
      echo "  ✓ issue $N: CLEAR"
      ;;
    CONCERNS:*|CONCERNS)
      echo "CONCERNS" > "$FIRSTLINE_FILE"
      echo "  ⚠ issue $N: CONCERNS (details in issue-$N.verdict.md)"
      ;;
    *)
      echo "MALFORMED" > "$FIRSTLINE_FILE"
      echo "  ! issue $N: MALFORMED verdict — treat as CONCERNS"
      ;;
  esac

  # Remove the prompt file (contained the untrusted body)
  rm -f "$PROMPT_FILE"
}

while IFS= read -r N; do
  [ -z "$N" ] && continue
  scan_one "$N" || true
done < "$ROUND_DIR/manifest.txt"

echo
echo "Round directory: $ROUND_DIR"
echo "Run .claude/scripts/feedback-review.sh to see verdicts."
