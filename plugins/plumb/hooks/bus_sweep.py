#!/usr/bin/env python3
"""Boundary sweep — the bus's level-triggered backstop, at every turn boundary.

Registered for three hook events, because a boundary has two edges and a
session has a beginning:

  Stop              turn END — the original sweep
  UserPromptSubmit  turn START — pending mail lands BEFORE the turn's work,
                    not after it. Without this, an engaged-after-idle agent
                    does the user's request under stale context and only
                    learns about the waiting message when it stops.
  SessionStart      session birth (startup|resume matchers) — the "peer
                    wasn't running" case: a message sent to a session that
                    didn't exist yet is delivered the moment it comes up,
                    and the agent gets into action right away. (compact is
                    excluded: the post-compaction context is the most crowded
                    injection point and compaction.py owns it.)

Sweeps EVERYTHING undelivered, not only `normal`. If the monitor is dead, this
is the only path a gating message has, so it is what turns a silent LOSS into a
merely-late delivery — and `format_message(late=True)` then tells the recipient
their monitor is down, which is what stops the lateness being silent too.

Over-delivery across boundaries and the monitor is impossible by construction:
every path claims through the same transaction in bus.py (delivered_at is
marked atomically with the emit), so whichever path wins the race, the others
find nothing.

Idempotence is load-bearing: injecting via `additionalContext` RE-INVOKES the
agent, which will Stop again. A sweep that finds nothing emits nothing and exits
0, which terminates the loop. That property is transactional in bus.py, not a
convention here.
"""
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))

try:
    import bus
except ImportError:
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    if not os.environ.get("PLUMB_AGENT"):
        sys.exit(0)  # not a bus-enabled session; say nothing

    if payload.get("cwd"):
        os.environ.setdefault("CLAUDE_PROJECT_DIR", payload["cwd"])

    db = bus.db_path()
    if not Path(db).exists():
        sys.exit(0)  # no bus in this project

    event = payload.get("hook_event_name") or "Stop"

    conn = bus.connect(db)
    try:
        me = bus.whoami()
        sink = io.StringIO()
        rows = bus.claim_and_emit(
            conn, me, via=f"hook:{event}", out=sink,
            render=lambda rs: "\n\n".join(
                bus.format_message(r, late=(r["urgency"] == "gating")) for r in rs))
    finally:
        conn.close()

    if not rows:
        sys.exit(0)

    json.dump({"hookSpecificOutput": {
        "hookEventName": event,
        "additionalContext": sink.getvalue().rstrip(),
    }}, sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"plumb bus stop hook: {exc.__class__.__name__}: {exc}", file=sys.stderr)
    sys.exit(0)
