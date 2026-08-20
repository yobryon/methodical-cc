#!/usr/bin/env python3
"""plumb — MCP server (stdio, JSON-RPC 2.0, stdlib only).

The plugin's agent-facing contract: the bus (peer messaging) and the process
host's read surface (role resolution, the way-of-working document, decision
numbers). The CLI in bin/ is the ENGINE (monitors, hooks) and the human
surface; agents get these tools.

Why MCP rather than a CLI for the agent surface:

    A tool description is guidance delivered at the POINT OF USE. A CLI's
    guidance lives in a skill that may not be loaded, mediated by memory —
    and the contract travels with the session either way.

For a plugin whose thesis is *make failures impossible or loud*, that is the
same argument as **lessons that can become guards, should** — so the tool
descriptions below are not documentation, they are the guard. They are where an
agent learns that `gating` costs the recipient an interruption, that a ruling
belongs on the ledger before it belongs on the wire, and that a retired role's
refusal is a process statement rather than an error.

Deliberately NO subject field on the bus. A schema with a subject invites the
model to pack meaning into it — the field is there, it looks important, and
nothing makes the size felt until the send fails. That is a tool-shape problem,
and owning the contract is how we decline to have it.

No third-party dependencies: the protocol is small and the repo's
pure-Python/no-build-step property is what let the last bus rewrite ship.
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import bus  # noqa: E402
import plumb  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "plumb", "version": bus.BUS_VERSION}

TOOLS = [
    {
        "name": "bus_send",
        "description": (
            "Send a message to a peer session on this project's bus.\n\n"
            "`urgency` is delivery timing, nothing else:\n"
            "  • 'gating'  delivered now; interrupts them if they are mid-turn.\n"
            "  • 'normal'  delivered now if they are idle (it wakes them); if they "
            "are mid-turn, it waits for their turn to end — which can be minutes "
            "or an hour.\n"
            "Delivery always carries everything pending for them, in send order; "
            "class never reorders. A peer who is not running receives at their "
            "next session start.\n\n"
            "There is no subject line; put everything in `body`."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {"type": "string",
                       "description": "Recipient agent name, e.g. 'impl' or 'arch'. "
                                      "bus_status lists who is on this bus."},
                "body": {"type": "string",
                         "description": "The whole message. No length ceiling."},
                "urgency": {"type": "string", "enum": ["gating", "normal"],
                            "default": "normal",
                            "description": "gating = interrupt a turn in progress; "
                                           "normal = wait one out. Idle peers get "
                                           "either immediately."},
                "thread": {"type": "string",
                           "description": "Optional thread id for grouping an "
                                          "exchange; no effect on delivery."},
                "record": {"type": "string",
                           "description": "The durable artifact this is about "
                                          "(issue id, doc path), if any — the "
                                          "message is the notification; the record "
                                          "is where it lives."},
            },
            "required": ["to", "body"],
        },
    },
    {
        "name": "bus_inbox",
        "description": (
            "Read messages addressed to you that have not been delivered yet.\n\n"
            "You rarely need this. Gating messages interrupt you; everything else is "
            "injected when your turn ends. Reach for it when you want to drain your "
            "inbox deliberately — for example before sending a status report, so you "
            "are not reporting against a ruling you have not read."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "process_path",
        "description": (
            "Resolve one of this project's artifact ROLES to its path — 'plan', "
            "'decisions', whatever this project declares in .plumb.toml. Use this "
            "instead of remembering or guessing filenames: skills and agents address "
            "artifacts by role, never by filename, so a file the project retired "
            "cannot be quietly recreated.\n\n"
            "A RETIRED role returns a refusal carrying the reason on record. That "
            "refusal is a PROCESS STATEMENT, not an error to work around — do not "
            "create the file by another route. If the role should genuinely return, "
            "that is a process change: the way-of-working document first, then the "
            "manifest."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "role": {"type": "string",
                         "description": "The artifact role name, e.g. 'plan' or "
                                        "'decisions'. Unknown names return the "
                                        "declared list."},
                "sub": {"type": "object",
                        "additionalProperties": {"type": "string"},
                        "description": "Values for any {token} placeholders in the "
                                       "role's path — the token names are the "
                                       "project's own ({issue}, {cycle}, {arc}, "
                                       "whatever its manifest declares)."},
                "arc": {"type": "string",
                        "description": "Sugar for sub={\"arc\": ...}."},
            },
            "required": ["role"],
        },
    },
    {
        "name": "process_read",
        "description": (
            "Read this project's way-of-working document — its NORMS, the source of "
            "truth for how this project works. Pass `section` to read one section by "
            "heading; omit it for the whole document; pass list=true for the table of "
            "contents.\n\n"
            "Consult it before making a process-shaped judgment (how work is bounded, "
            "who decides what, where things are recorded). Where guidance you are "
            "carrying — including a skill's — disagrees with this document, THE "
            "DOCUMENT WINS, and you should say so rather than quietly proceed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "section": {"type": "string",
                            "description": "Heading substring, e.g. 'Norms'."},
                "list": {"type": "boolean",
                         "description": "List section headings instead of content."},
            },
        },
    },
    {
        "name": "decision_next",
        "description": (
            "The next unclaimed decision number, read from this project's decisions "
            "log at this moment.\n\n"
            "Numbers are claimed by the LOG, never from memory — two agents ruling in "
            "parallel have collided by remembering. Call this immediately before "
            "writing the entry, not when you start composing it; in prose that "
            "anticipates a ruling, say 'resolves as the next D-number' rather than "
            "reserving one. On a collision, commit order is the tiebreak and both "
            "entries carry a note pointing at each other."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "bus_status",
        "description": (
            "Who is on this bus, whether their monitor is actually running, and what "
            "is pending for each of them.\n\n"
            "A recipient whose monitor is 'dead' or 'stale' cannot be interrupted or "
            "woken — messages to them arrive at their next turn boundary or session "
            "start. Check here when a peer seems unresponsive, before concluding a "
            "message was lost. Silence usually means someone is mid-turn; it never "
            "means the bus dropped something. For chronology — what was sent, when it "
            "was delivered, and where the repo stood at delivery — run `bus.py log` "
            "in a shell (filters: --record, --thread, --from, --to)."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
]


# ------------------------------------------------------------------ handlers

def _conn():
    return bus.connect(bus.db_path())


def tool_bus_send(args):
    me = bus.whoami()
    conn = _conn()
    try:
        mid = bus.send(conn, me, args["to"], args["body"],
                       args.get("urgency", "normal"), args.get("thread"),
                       args.get("record"))
        warning = bus.delivery_note(conn, args["to"])
        out = [f"Sent #{mid} to @{args['to']} ({args.get('urgency', 'normal')})."]
        if len(args["body"]) > bus.EVENT_CLIP_CHARS:
            out.append("")
            out.append(f"✂ #{mid} is {len(args['body']):,} chars — delivery clips at "
                       f"~{bus.EVENT_CLIP_CHARS:,}. The receiver gets a banner, the head, "
                       f"and a `bus.py show {mid}` pointer; the store holds it whole. "
                       f"If the tail carries a question or a decision, restate it in "
                       f"the first {bus.EVENT_CLIP_CHARS:,} chars or lean on the record — "
                       f"a sender who doesn't know their tail was clipped believes "
                       f"they asked a question.")
        if warning:
            out.append("")
            out.append(f"⚠ {warning}")
        # Point-of-use context, not alarms. Both notes surface only at the
        # moment the sender is already talking to this peer / about this
        # record — the moment a stale assumption would actually be acted on.
        now = time.time()
        aged = conn.execute(
            "SELECT id, urgency, created_at FROM messages WHERE sender=? AND "
            "recipient=? AND id!=? AND delivered_at IS NULL AND quarantined=0 "
            "AND created_at < ? ORDER BY id",
            (me, args["to"], mid, now - 300)).fetchall()
        if aged:
            bits = ", ".join(f"#{r['id']} ({r['urgency']}, "
                             f"{int((now - r['created_at']) / 60)}m)" for r in aged)
            out.append("")
            out.append(f"Note: your earlier {bits} to @{args['to']} "
                       f"{'is' if len(aged) == 1 else 'are'} still pending — they "
                       f"haven't hit a boundary yet. Factor that into anything you "
                       f"conclude from their silence.")
        if args.get("record"):
            prior = conn.execute(
                "SELECT COUNT(*) c FROM messages WHERE record_ref=? AND id!=?",
                (args["record"], mid)).fetchone()["c"]
            if prior:
                out.append("")
                out.append(f"FYI: {prior} earlier message(s) cite this record — "
                           f"`bus.py log --record '{args['record']}'` to review "
                           f"what has been said about it.")
        return "\n".join(out)
    finally:
        conn.close()


def tool_bus_inbox(_args):
    me = bus.whoami()
    conn = _conn()
    try:
        import io
        sink = io.StringIO()
        rows = bus.claim_and_emit(conn, me, via="inbox", out=sink)
        return sink.getvalue() if rows else "No undelivered messages."
    finally:
        conn.close()


def tool_bus_status(_args):
    conn = _conn()
    try:
        rows = bus.status(conn)
        if not rows:
            return "No agents have used this bus yet."
        lines = []
        for r in rows:
            mon = r["monitor"]
            if mon == "stale":
                mon = f"stale ({r['stale_for']}s since last tick)"
            elif mon == "dead":
                mon = f"NOT RUNNING (pid {r['pid']} gone)"
            bits = [f"@{r['agent']}: monitor {mon}"]
            if r["pending"]:
                bits.append(f"{r['pending']} pending"
                            + (f" (oldest {r['oldest_pending_age']}s)"
                               if r["oldest_pending_age"] else ""))
            if r["quarantined"]:
                bits.append(f"{r['quarantined']} quarantined")
            lines.append("  " + ", ".join(bits))
        return "Bus status:\n" + "\n".join(lines)
    finally:
        conn.close()


NO_MANIFEST = ("This project has not declared a process — no .plumb.toml found. "
               "Run `plumb init` and then the plumb:establish skill with the "
               "Product Owner to author one. Until then there are no roles to "
               "resolve and no document to read.")


def _manifest():
    return plumb.Manifest.load(required=False)


def tool_process_path(args):
    mf = _manifest()
    if mf is None:
        return NO_MANIFEST
    try:
        return str(mf.resolve(args["role"], arc=args.get("arc"),
                              subs=args.get("sub")))
    except plumb.Retired as exc:
        return plumb.retired_text(exc)
    except plumb.UnknownRole as exc:
        return plumb.unknown_text(exc)
    except ValueError as exc:
        return str(exc)


def tool_process_read(args):
    mf = _manifest()
    if mf is None:
        return NO_MANIFEST
    doc = mf.document
    if doc is None or not doc.is_file():
        return (f"the manifest declares no readable process document "
                f"({doc}). The establish conversation writes it.")
    text = doc.read_text(encoding="utf-8")
    if args.get("list"):
        import re
        heads = [f"{'  ' * (len(m.group(1)) - 1)}{m.group(2).strip()}"
                 for m in re.finditer(r"^(#{1,6})\s+(.*)$", text, re.MULTILINE)]
        return "Sections:\n" + "\n".join(heads)
    section = args.get("section")
    if not section:
        return f"<!-- {doc} (process v{mf.process_version}) -->\n{text}"
    body, headings = plumb.read_section(text, section)
    if body is None:
        return (f"no section matching '{section}'. "
                f"Sections: {', '.join(headings)}")
    return (f"<!-- {doc} § (process v{mf.process_version}) — "
            f"the project's own words -->\n{body}")


def tool_decision_next(_args):
    mf = _manifest()
    if mf is None:
        return NO_MANIFEST
    try:
        log = mf.resolve("decisions")
    except (plumb.Retired, plumb.UnknownRole):
        return ("this project declares no 'decisions' role — nothing to "
                "allocate against. If it keeps a decisions log under another "
                "name, resolve that role instead and read its tail.")
    if not log.is_file():
        return "D-1 (the log does not exist yet — this is the first)"
    used = plumb.scan_decision_numbers(log.read_text(encoding="utf-8"))
    nxt = (used[-1] + 1) if used else 1
    high = f"D-{used[-1]}" if used else "(none)"
    return (f"D-{nxt}  (highest on record: {high} in {log}). Claimed by the "
            f"log only — write the entry now, not later.")


HANDLERS = {
    "bus_send": tool_bus_send,
    "bus_inbox": tool_bus_inbox,
    "bus_status": tool_bus_status,
    "process_path": tool_process_path,
    "process_read": tool_process_read,
    "decision_next": tool_decision_next,
}


# -------------------------------------------------------------- JSON-RPC loop

def respond(msg_id, result=None, error=None):
    out = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        out["error"] = error
    else:
        out["result"] = result
    sys.stdout.write(json.dumps(out) + "\n")
    sys.stdout.flush()


def handle(req):
    method, msg_id = req.get("method"), req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        respond(msg_id, {
            "protocolVersion": params.get("protocolVersion") or PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    elif method in ("notifications/initialized", "initialized"):
        pass  # notification: no id, no response
    elif method == "ping":
        respond(msg_id, {})
    elif method == "tools/list":
        respond(msg_id, {"tools": TOOLS})
    elif method == "tools/call":
        name = params.get("name")
        handler = HANDLERS.get(name)
        if handler is None:
            respond(msg_id, error={"code": -32601, "message": f"unknown tool {name!r}"})
            return
        try:
            text = handler(params.get("arguments") or {})
            respond(msg_id, {"content": [{"type": "text", "text": text}]})
        except SystemExit as exc:   # whoami() with no identity
            respond(msg_id, {"content": [{"type": "text", "text": str(exc)}],
                             "isError": True})
        except Exception as exc:
            respond(msg_id, {"content": [{"type": "text",
                                          "text": f"{exc.__class__.__name__}: {exc}"}],
                             "isError": True})
    elif msg_id is not None:
        respond(msg_id, error={"code": -32601, "message": f"unknown method {method!r}"})


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            handle(req)
        except Exception as exc:
            if isinstance(req, dict) and req.get("id") is not None:
                respond(req["id"], error={"code": -32603, "message": str(exc)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
