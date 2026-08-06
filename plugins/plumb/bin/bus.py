#!/usr/bin/env python3
"""plumb bus — peer messaging that can interrupt.

The harness's team protocol delivers a message only when the RECIPIENT's turn
ends. An agent that asks a question and keeps working cannot see the answer
until it stops. That single property is what forced "send and stop" discipline,
what made a blocking consult look necessary, and — through a longer chain — what
made the Product Owner the implementor's lifecycle operator:

    teammates cannot spawn teammates
      -> the PO launches every session by hand
        -> the PO is the one who refreshes the implementor

That constraint belongs to the harness. This bus is ours, so it is ours to
remove.

Three processes, one SQLite store, no IPC:

    MCP server   writes messages            (identity from $PLUMB_AGENT)
    monitor      reads MY undelivered gating -> interrupts mid-turn
    Stop hook    reads MY undelivered ANY    -> injects at the turn boundary

The Stop hook deliberately sweeps *everything*, not just `normal`. If the
monitor is dead, gating messages still arrive — late rather than never. That
converts a silent LOSS into a silent LATENESS, and `delivered_by` plus the
heartbeat then make the lateness loud. A bus that stops receiving quietly is
"silent in a way indistinguishable from healthy", which is the exact failure
family this plugin exists to attack; we do not get to ship one.
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

BUS_VERSION = "0.1.0"
DEFAULT_DB = ".mcc/bus.db"
MAX_ATTEMPTS = 5
# A monitor ticks at 1 Hz, so this is ten missed ticks — tight enough that a
# degraded bus is noticed fast, loose enough to survive a blocked write. The
# pid check below is the exact signal; this only backstops it.
HEARTBEAT_STALE_S = 10.0

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS messages(
  id            INTEGER PRIMARY KEY,
  thread        TEXT,
  sender        TEXT NOT NULL,
  recipient     TEXT NOT NULL,
  urgency       TEXT NOT NULL CHECK(urgency IN ('gating','normal')),
  body          TEXT NOT NULL,
  record_ref    TEXT,
  created_at    REAL NOT NULL,
  delivered_at  REAL,
  delivered_by  TEXT,
  acked_at      REAL,
  attempts      INTEGER NOT NULL DEFAULT 0,
  quarantined   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_pending
  ON messages(recipient, delivered_at, quarantined, urgency);
CREATE INDEX IF NOT EXISTS idx_unacked
  ON messages(sender, urgency, acked_at);
CREATE TABLE IF NOT EXISTS agents(
  agent        TEXT PRIMARY KEY,
  last_seen    REAL NOT NULL,
  monitor_pid  INTEGER,
  session      TEXT
);
"""


# ------------------------------------------------------------------ plumbing

def db_path(explicit=None):
    if explicit:
        return Path(explicit)
    if os.environ.get("PLUMB_BUS_DB"):
        return Path(os.environ["PLUMB_BUS_DB"])
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return Path(root) / DEFAULT_DB


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def whoami(explicit=None):
    """Identity comes from the environment mcc injects at session launch.

    Never inferred, never guessed. An agent that cannot say who it is must not
    silently become someone else — a monitor started with a bad identity stays
    bad for the whole session, because compaction is a context event and not a
    process event.
    """
    who = explicit or os.environ.get("PLUMB_AGENT")
    if not who:
        raise SystemExit(
            "plumb bus: no identity. $PLUMB_AGENT is unset and --agent was not "
            "given.\n  Sessions get their identity from `mcc`; launch via `mcc "
            "<name>` or pass --agent."
        )
    return who


# -------------------------------------------------------------------- writes

def send(conn, sender, recipient, body, urgency="normal", thread=None,
         record_ref=None):
    if urgency not in ("gating", "normal"):
        raise ValueError(f"urgency must be 'gating' or 'normal', not {urgency!r}")
    if not body or not body.strip():
        raise ValueError("refusing to send an empty message")
    cur = conn.execute(
        "INSERT INTO messages(thread,sender,recipient,urgency,body,record_ref,"
        "created_at) VALUES(?,?,?,?,?,?,?)",
        (thread, sender, recipient, urgency, body, record_ref, time.time()))
    return cur.lastrowid


def heartbeat(conn, agent, pid=None, session=None):
    conn.execute(
        "INSERT INTO agents(agent,last_seen,monitor_pid,session) VALUES(?,?,?,?) "
        "ON CONFLICT(agent) DO UPDATE SET last_seen=excluded.last_seen, "
        "monitor_pid=COALESCE(excluded.monitor_pid, agents.monitor_pid), "
        "session=COALESCE(excluded.session, agents.session)",
        (agent, time.time(), pid, session))


def ack(conn, msg_id, agent):
    cur = conn.execute(
        "UPDATE messages SET acked_at=? WHERE id=? AND recipient=? AND acked_at IS NULL",
        (time.time(), msg_id, agent))
    return cur.rowcount


# ---------------------------------------------------- the load-bearing read

def claim_and_emit(conn, recipient, via, urgency=None, render=None, out=None):
    """Mark delivered and emit, inside one transaction.

    One column solves three problems, and it has to be transactional to solve
    any of them:

      1. No spam      — a delivered message is never re-emitted at 1 Hz.
      2. No silent loss — if the emit raises, the transaction rolls back and
                          the message is undelivered again on the next tick.
      3. No Stop-loop  — a Stop hook that injects re-invokes the agent, which
                         will Stop again. Idempotent sweeps terminate.

    Crash between flush and COMMIT redelivers once: at-least-once, which is the
    right side to err on. `attempts` quarantines a poison message so it can
    never spam forever.
    """
    out = out or sys.stdout
    render = render or (lambda rows: "\n".join(format_message(r) for r in rows))
    sql = ("SELECT * FROM messages WHERE recipient=? AND delivered_at IS NULL "
           "AND quarantined=0")
    params = [recipient]
    if urgency:
        sql += " AND urgency=?"
        params.append(urgency)
    sql += " ORDER BY CASE urgency WHEN 'gating' THEN 0 ELSE 1 END, id"

    conn.execute("BEGIN IMMEDIATE")
    try:
        rows = conn.execute(sql, params).fetchall()
        if not rows:
            conn.execute("COMMIT")
            return []
        now = time.time()
        for r in rows:
            if r["attempts"] + 1 > MAX_ATTEMPTS:
                conn.execute("UPDATE messages SET quarantined=1 WHERE id=?", (r["id"],))
                continue
            conn.execute(
                "UPDATE messages SET delivered_at=?, delivered_by=?, attempts=attempts+1 "
                "WHERE id=?", (now, via, r["id"]))
        live = [r for r in rows if r["attempts"] + 1 <= MAX_ATTEMPTS]
        if live:
            out.write(render(live))
            out.write("\n")
            out.flush()
        conn.execute("COMMIT")
        return live
    except Exception:
        conn.execute("ROLLBACK")
        raise


def format_message(row, late=False):
    head = f"[plumb bus] {row['urgency'].upper()} from @{row['sender']}"
    if row["thread"]:
        head += f"  (thread {row['thread']})"
    lines = [head]
    if late:
        lines.append(
            "  ⚠ This was sent as GATING — meant to interrupt you — but arrived at your "
            "turn boundary instead. Your bus monitor is not running, so urgent messages "
            "are being delayed. Tell the PO.")
    if row["record_ref"]:
        lines.append(f"  durable record: {row['record_ref']}")
    lines.append("")
    lines.append(row["body"])
    if row["urgency"] == "gating":
        lines.append("")
        lines.append(f"  → acknowledge with bus_ack(id={row['id']}) once you have acted on it. "
                     f"The sender can see delivered-but-unacked.")
    return "\n".join(lines)


# -------------------------------------------------------------------- status

def _pid_alive(pid):
    """Exact liveness, where the heartbeat is only an estimate.

    Signal 0 tests existence without touching the process. Sessions for a
    project run on one machine, so this is available and precise; where it is
    not (a recycled pid, a different host) the heartbeat age still backstops it.
    Returns None when we cannot tell, so callers fall back rather than guess.
    """
    if not pid:
        return None
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True   # exists, owned by someone else
    except OSError:
        return None


def agent_liveness(conn, agent):
    row = conn.execute("SELECT * FROM agents WHERE agent=?", (agent,)).fetchone()
    if row is None:
        return {"agent": agent, "monitor": "never-seen", "stale_for": None, "pid": None}
    age = time.time() - row["last_seen"]
    alive = _pid_alive(row["monitor_pid"])
    if alive is False:
        state = "dead"          # exact: the process is gone
    elif age > HEARTBEAT_STALE_S:
        state = "stale"         # heuristic: it exists but stopped ticking
    else:
        state = "alive"
    return {"agent": agent, "monitor": state, "stale_for": round(age, 1),
            "pid": row["monitor_pid"]}


def delivery_note(conn, recipient):
    """What the SENDER is told about how their message will actually land.

    This is the signal no discipline ever gave them: an architect who can see
    that the implementor's monitor is down knows their ruling will land late,
    at the moment they send it, rather than discovering it afterwards.
    """
    live = agent_liveness(conn, recipient)
    if live["monitor"] == "alive":
        return None
    if live["monitor"] == "dead":
        return (f"@{recipient}'s bus monitor is NOT RUNNING (pid {live['pid']} is gone). "
                f"This will not interrupt them — it will arrive at their next turn "
                f"boundary, and they will be told their monitor is down.")
    if live["monitor"] == "never-seen":
        return (f"@{recipient} has never checked in on this bus. They may not be "
                f"running, or may be a headless session (which cannot run monitors "
                f"at all). A gating message will not interrupt them; it will arrive "
                f"whenever they next end a turn — if they are running.")
    return (f"@{recipient}'s monitor has not checked in for {live['stale_for']}s. "
            f"Gating messages will NOT interrupt them — this will arrive at their "
            f"next turn boundary instead.")


def status(conn):
    agents = {r["agent"]: dict(r) for r in conn.execute("SELECT * FROM agents")}
    for r in conn.execute("SELECT DISTINCT recipient AS a FROM messages "
                          "UNION SELECT DISTINCT sender FROM messages"):
        agents.setdefault(r["a"], {"agent": r["a"], "last_seen": None})
    out = []
    for name in sorted(agents):
        counts = conn.execute(
            "SELECT COUNT(*) FILTER (WHERE delivered_at IS NULL AND quarantined=0) AS pending,"
            " COUNT(*) FILTER (WHERE urgency='gating' AND delivered_at IS NOT NULL"
            "                  AND acked_at IS NULL) AS unacked,"
            " COUNT(*) FILTER (WHERE quarantined=1) AS quarantined,"
            " MIN(CASE WHEN delivered_at IS NULL AND quarantined=0 THEN created_at END) AS oldest"
            " FROM messages WHERE recipient=?", (name,)).fetchone()
        entry = agent_liveness(conn, name)
        entry.update(pending=counts["pending"], unacked_gating=counts["unacked"],
                     quarantined=counts["quarantined"])
        entry["oldest_pending_age"] = (round(time.time() - counts["oldest"], 1)
                                       if counts["oldest"] else None)
        out.append(entry)
    return out


# ------------------------------------------------------------------ commands

def cmd_init(args):
    conn = connect(db_path(args.db))
    print(f"bus store ready: {db_path(args.db)}")
    conn.close()


def cmd_send(args):
    conn = connect(db_path(args.db))
    body = args.body
    if body == "-" or body is None:
        body = sys.stdin.read()
    mid = send(conn, whoami(args.agent), args.to, body, args.urgency,
               args.thread, args.record)
    note = delivery_note(conn, args.to)
    print(json.dumps({"id": mid, "to": args.to, "urgency": args.urgency,
                      "delivery_warning": note}))
    conn.close()


def cmd_watch(args):
    """The monitor. Level-triggered by design: it re-derives state every tick.

    An edge-triggered notification is lost forever if the listener is restarting
    when it fires. A poll that re-reads the table is self-healing — miss a tick,
    the next one catches it; die and come back, and everything undelivered is
    still there.
    """
    me = whoami(args.agent)
    conn = connect(db_path(args.db))
    pid = os.getpid()
    while True:
        try:
            heartbeat(conn, me, pid=pid, session=os.environ.get("CLAUDE_SESSION_ID"))
            claim_and_emit(conn, me, via="monitor", urgency=args.urgency)
        except sqlite3.OperationalError:
            pass  # a writer held the lock; next tick re-derives. Never fatal.
        time.sleep(args.interval)


def cmd_sweep(args):
    """The Stop hook's backstop. Sweeps EVERYTHING undelivered, not just normal.

    If the monitor is down, this is the only path a gating message has. It marks
    such a message as late so the recipient learns their monitor is dead.
    """
    me = whoami(args.agent)
    conn = connect(db_path(args.db))
    def render(rows):
        return "\n\n".join(
            format_message(r, late=(r["urgency"] == "gating")) for r in rows)
    rows = claim_and_emit(conn, me, via="stop-hook", render=render)
    conn.close()
    return rows


def cmd_ack(args):
    conn = connect(db_path(args.db))
    n = ack(conn, args.id, whoami(args.agent))
    print(json.dumps({"acked": bool(n), "id": args.id}))
    conn.close()


def cmd_status(args):
    conn = connect(db_path(args.db))
    rows = status(conn)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print(f"{'agent':<14}{'monitor':<12}{'pending':>8}{'unacked':>9}{'quarantined':>13}")
        for r in rows:
            mon = r["monitor"]
            if mon == "stale":
                mon = f"stale {r['stale_for']:.0f}s"
            print(f"{r['agent']:<14}{mon:<12}{r['pending']:>8}"
                  f"{r['unacked_gating']:>9}{r['quarantined']:>13}")
    conn.close()


def build_parser():
    p = argparse.ArgumentParser(prog="bus", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"plumb bus {BUS_VERSION}")
    p.add_argument("--db", help=f"store path (default $PLUMB_BUS_DB or {DEFAULT_DB})")
    p.add_argument("--agent", help="identity (default $PLUMB_AGENT)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init"); s.set_defaults(func=cmd_init)

    s = sub.add_parser("send")
    s.add_argument("--to", required=True)
    s.add_argument("--body", help="message body, or '-' for stdin")
    s.add_argument("--urgency", choices=("gating", "normal"), default="normal")
    s.add_argument("--thread")
    s.add_argument("--record", help="durable record reference (issue id, doc path)")
    s.set_defaults(func=cmd_send)

    s = sub.add_parser("watch", help="monitor loop: gating messages for me")
    s.add_argument("--urgency", choices=("gating", "normal"))
    s.add_argument("--interval", type=float, default=1.0)
    s.set_defaults(func=cmd_watch)

    s = sub.add_parser("sweep", help="Stop-hook backstop: everything undelivered")
    s.set_defaults(func=cmd_sweep)

    s = sub.add_parser("ack")
    s.add_argument("id", type=int)
    s.set_defaults(func=cmd_ack)

    s = sub.add_parser("status")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
