#!/usr/bin/env python3
"""plumb drift — detectors that run inside the bus monitor's tick.

Two of them, not five. The proposal named five; three depend on reading the
tracker or on a project-specific convention, and PLUMB does not proxy trackers
(see the ledger layer). Shipping a detector that only works on one adapter, or
only where a project happens to mark its pins a particular way, would be a
detector nobody can trust the silence of — and **the silence is the product**.
A check you cannot trust when it says nothing is worse than no check.

The two that survive are portable, cheap, and each attached to a real incident:

  unanswered-gating   a ruling delivered and never acknowledged
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
# A gating message is a ruling that changes what someone is doing right now.
# Unacknowledged for this long means it probably did not.
UNACKED_GRACE_S = 600.0

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


# ------------------------------------------------------- unanswered gating

def check_unanswered_gating(conn, agent):
    """A ruling delivered and never acknowledged.

    The scar: five rulings arrived after the work they governed. An architect
    could not tell "delivered" from "acted on", because nothing distinguished
    them. `acked_at` distinguishes them; this is what makes the distinction
    arrive without being asked for.

    Reported to the SENDER — they are the one whose ruling may not have landed.
    """
    cutoff = time.time() - UNACKED_GRACE_S
    rows = conn.execute(
        "SELECT id, recipient, delivered_at, substr(body,1,90) AS gist, record_ref "
        "FROM messages WHERE sender=? AND urgency='gating' AND delivered_at IS NOT NULL "
        "AND acked_at IS NULL AND delivered_at < ? ORDER BY delivered_at",
        (agent, cutoff)).fetchall()
    out = []
    for r in rows:
        mins = int((time.time() - r["delivered_at"]) / 60)
        note = (f"[plumb drift] Your gating message #{r['id']} to @{r['recipient']} was "
                f"delivered {mins} min ago and has NOT been acknowledged.\n"
                f"  \"{r['gist'].strip()}…\"\n")
        if r["record_ref"]:
            note += (f"  It is on the record at {r['record_ref']}, so it survives "
                     f"regardless — but nobody has confirmed acting on it.\n")
        else:
            note += ("  It is NOT on any durable record. If it gates work, put it on "
                     "the ledger now — the bus is the notification, not the record.\n")
        note += ("  Delivered is not acted-on. Check whether they saw it before "
                 "assuming the work reflects it.")
        out.append((f"unacked:{r['id']}", note))
    return out


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
        findings += check_unanswered_gating(conn, agent)
    except Exception:
        pass
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
