#!/usr/bin/env python3
"""plumb drift — detectors that run inside the bus monitor's tick.

ONE of them, and the count has gone down twice — which is the design working.
The proposal named five; three depended on reading the tracker or on a
project-specific convention, and PLUMB does not proxy trackers. A fourth
(unanswered-gating) shipped and was removed after its first real week: it
watched `bus_ack`, a protocol call nobody made, so it fired six times, was
wrong six times, and produced one false report the time it was believed. "A
skipped protocol with a monitor attached is worse than no protocol, because it
manufactures false signal." A detector you cannot trust the silence OR the
noise of subtracts value; the bus now answers questions (`bus.py log`,
`bus_status`) instead of raising alarms about proxies.

The one that survives is portable, cheap, ledger-derived (it measures the
work's own artifact, not a protocol about the work), and 2-for-2 true:

  decision-collision  two entries claiming one number

They run inside the EXISTING monitor loop rather than as separate monitors.
Monitors are rate-limited by the harness — "monitors that produce too many
events are automatically stopped" — so more processes emitting more often is
the way to lose the one that actually matters. One process, one heartbeat, bus
every tick, drift on a slow cadence.

Emission is once per distinct finding. A detector that re-announces the same
drift every minute trains its reader to skip it, which is the same failure as
not having it.
"""

import json
import re
import time
from pathlib import Path

# Slow cadence: drift is not urgent, and cheap checks that fire often are how a
# monitor gets rate-limited into silence.
DRIFT_INTERVAL_S = 120.0

DECISION_RE = re.compile(r"^\s*#{1,6}\s*D-(\d+)\b|^\s*\|\s*D-(\d+)\b|^\s*\*\*D-(\d+)\b",
                         re.MULTILINE)


def state_file(root, agent):
    d = Path(root) / ".mcc" / "plumb"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"drift-{agent}.json"


def load_seen(root, agent):
    f = state_file(root, agent)
    if not f.exists():
        return set()
    try:
        return set(json.loads(f.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return set()


def save_seen(root, agent, seen):
    try:
        state_file(root, agent).write_text(json.dumps(sorted(seen)), encoding="utf-8")
    except OSError:
        pass


# ----------------------------------------------------- decision collision

def check_decision_collision(root):
    """Two entries claiming one decision number.

    The scar: twice, once with both collisions in a single evening — two agents
    ruling in parallel, each reading the log's tail and writing the same next
    number. Commit order is the tiebreak, but only if someone notices.
    """
    try:
        import plumb
        mf = plumb.Manifest.load(root, required=False)
        if not mf or "decisions" not in mf.roles:
            return []
        log = mf.resolve("decisions")
    except Exception:
        return []
    if not Path(log).is_file():
        return []
    try:
        text = Path(log).read_text(encoding="utf-8")
    except OSError:
        return []

    counts = {}
    for m in DECISION_RE.finditer(text):
        num = next(g for g in m.groups() if g)
        counts[num] = counts.get(num, 0) + 1
    out = []
    for num, n in sorted(counts.items(), key=lambda kv: int(kv[0])):
        if n > 1:
            out.append((f"dnum:{num}:{n}",
                        f"[plumb drift] D-{num} appears {n} times in {Path(log).name}.\n"
                        f"  Two agents claiming one number is a documented collision, and it "
                        f"has happened twice before.\n"
                        f"  Commit order is the tiebreak: renumber the later one and have "
                        f"BOTH entries carry a note pointing at each other, so a reader who "
                        f"finds one learns the other exists."))
    return out


# -------------------------------------------------------------------- run

def run(conn, root, agent, emit):
    """Collect findings, emit only what has not been emitted before."""
    seen = load_seen(root, agent)
    findings = []
    try:
        findings += check_decision_collision(root)
    except Exception:
        pass

    fresh = [(k, msg) for k, msg in findings if k not in seen]
    current = {k for k, _ in findings}
    # Drop keys that no longer apply, so a drift that is fixed and recurs is
    # reported again rather than suppressed forever.
    seen = (seen & current) | {k for k, _ in fresh}
    save_seen(root, agent, seen)

    if fresh:
        emit("\n\n".join(msg for _, msg in fresh))
    return len(fresh)
