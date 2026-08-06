#!/usr/bin/env python3
"""Compaction survival — the implementor outlives its own context, unattended.

The friction this removes, in the Product Owner's words:

    The Architect stops and asks the PO to "run impl-end and start a fresh
    implementor" — when what the PO actually does is COMPACT it and say
    continue.

So the answer is not a faster way to spawn a replacement. It is that no
replacement was needed: compaction is a CONTEXT event, not a process event. The
session continues, the monitor keeps running (same pid, measured), the bus store
is untouched. Only the conversation is shorter.

Two hooks, both using mechanisms measured in the spike:

  PreCompact   -> snapshot mechanical state, and steer the summarizer
  SessionStart -> on source=compact ONLY, inject the pointer and say
                  plainly that this is routine

What this CANNOT do is author judgment. `prompt` and `agent` hooks are refused
at PreCompact ("Prompt stop hooks are not yet supported outside REPL"), so the
snapshot is mechanical facts only. Nor does it need to. What outlives a context belongs on a ledger,
which survives compaction untouched and is readable by an agent that was never
here.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))

MAX_LISTED = 15


def _git(cwd, *args):
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                           text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def snapshot_path(cwd, session):
    d = Path(cwd) / ".mcc" / "plumb"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"compaction-{(session or 'anon')[:8]}.md"


def write_snapshot(cwd, session, trigger):
    """Mechanical facts only — the things a fresh context cannot re-derive cheaply."""
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    head = _git(cwd, "log", "-1", "--format=%h %s")
    dirty = [ln for ln in _git(cwd, "status", "--porcelain").split("\n") if ln.strip()]
    recent = [ln for ln in _git(cwd, "log", "-8", "--format=%h %s").split("\n") if ln.strip()]

    lines = [
        "# Compaction snapshot",
        "",
        f"Written by PLUMB at {time.strftime('%Y-%m-%dT%H:%M:%S')} "
        f"({trigger or 'unknown'} compaction).",
        "",
        "**Mechanical facts only.** A hook cannot author judgment — what you were "
        "*thinking* is not here. If that matters it belongs on a ledger, where it "
        "survives anything rather than just this cut.",
        "",
        "## Repository",
        "",
        f"- branch: `{branch or '(unknown)'}`",
        f"- HEAD: {head or '(unknown)'}",
    ]
    if dirty:
        lines += ["", f"## Uncommitted at compaction ({len(dirty)})", ""]
        lines += [f"- `{d}`" for d in dirty[:MAX_LISTED]]
        if len(dirty) > MAX_LISTED:
            lines.append(f"- …and {len(dirty) - MAX_LISTED} more")
        lines += ["", "**Uncommitted work is the thing most likely to be forgotten "
                  "across a cut.** Check these are still intended before building on them."]
    else:
        lines += ["", "## Uncommitted at compaction", "", "None — the tree was clean."]

    if recent:
        lines += ["", "## Recent commits", ""] + [f"- {c}" for c in recent]

    try:
        import bus
        db = bus.db_path()
        if Path(db).exists():
            conn = bus.connect(db)
            me = os.environ.get("PLUMB_AGENT")
            if me:
                n = conn.execute(
                    "SELECT COUNT(*) FROM messages WHERE recipient=? AND "
                    "delivered_at IS NULL AND quarantined=0", (me,)).fetchone()[0]
                lines += ["", "## Bus", "",
                          f"- undelivered messages for @{me} at compaction: {n}",
                          "- The store is untouched by compaction; nothing was lost."]
            conn.close()
    except Exception:
        pass

    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ PreCompact

SUMMARIZER_STEER = (
    "When summarizing, preserve in this order of priority: (1) decisions made and "
    "the reasoning behind them, (2) what was tried and did NOT work, with the "
    "reason, (3) claims that are believed but NOT yet verified — label them as "
    "unverified, (4) the current objective and the next concrete step. "
    "Compress tool transcripts and file listings aggressively; they can be "
    "re-derived from disk. A summary that keeps the green results and loses the "
    "open questions is the wrong half."
)


def on_pre_compact(payload):
    cwd = payload.get("cwd") or os.getcwd()
    session = payload.get("session_id")
    path = snapshot_path(cwd, session)
    try:
        path.write_text(write_snapshot(cwd, session, payload.get("trigger")),
                        encoding="utf-8")
    except OSError:
        return

    # PreCompact stdout reaches the SUMMARIZER's instruction block, not the live
    # session — so this is a lever on WHAT SURVIVES THE CUT, which for an agent
    # running to exhaustion is worth more than appending a pointer afterwards:
    # the summary is what the next context is built on.
    # Single first-hand observation; additive, so it costs nothing if ignored.
    json.dump({"additionalContext": SUMMARIZER_STEER}, sys.stdout)


# ---------------------------------------------------------------- SessionStart

def on_session_start(payload):
    # Gate on source. Post-compaction context is the most crowded injection
    # point in the system — several plugins' blocks land together, and a stale
    # one actively pulls against the summary the agent was just handed. On
    # `compact`: the pointer and nothing else.
    if payload.get("source") != "compact":
        return

    cwd = payload.get("cwd") or os.getcwd()
    session = payload.get("session_id")
    snap = snapshot_path(cwd, session)

    out = [
        "=== PLUMB: you just compacted ===",
        "",
        "This is ROUTINE and requires nothing from anyone. Compaction is a context "
        "event, not a process event: your session is the same session, your bus "
        "monitor is the same process, and nothing was lost from any ledger.",
        "",
        "**Context pressure is not a reason to stop, and not a reason to ask the "
        "Product Owner to replace you.** If you were mid-task, continue it.",
    ]
    if snap.exists():
        out += ["", f"Mechanical snapshot from just before the cut: {snap}",
                "  (branch, HEAD, uncommitted files, undelivered bus messages)"]
    out += ["", "Anything that outlives a context belongs on a LEDGER, not in a "
            "handover file: rulings in the decisions log, traps in the failure "
            "catalog, progress in the tracker. Read those if the summary is thin."]
    out += ["", "Before building on anything the summary asserts, check whether it "
            "was VERIFIED or merely remembered. A summary flattens that distinction, "
            "and it is the one that matters."]

    print("\n".join(out))


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    event = payload.get("hook_event_name")
    if event == "PreCompact":
        on_pre_compact(payload)
    elif event == "SessionStart":
        on_session_start(payload)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"plumb compaction hook: {exc.__class__.__name__}: {exc}", file=sys.stderr)
    sys.exit(0)
