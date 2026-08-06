#!/usr/bin/env python3
"""plumb bus — MCP server (stdio, JSON-RPC 2.0, stdlib only).

Why MCP for the send side rather than a CLI:

    A tool description is guidance delivered at the POINT OF USE. A CLI's
    guidance lives in a skill that may not be loaded, mediated by memory.

For a plugin whose thesis is *make failures impossible or loud*, that is the
same argument as **lessons that can become guards, should** — so the tool
descriptions below are not documentation, they are the guard. They are where an
agent learns that `gating` costs the recipient an interruption, and that a
ruling belongs on the ledger before it belongs on the wire.

Deliberately NO subject field. A schema with a subject invites the model to pack
meaning into it — the field is there, it looks important, and nothing makes the
size felt until the send fails. That is a tool-shape problem, and owning the
contract is how we decline to have it.

No third-party dependencies: the protocol is small and the repo's
pure-Python/no-build-step property is what let the last bus rewrite ship.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import bus  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "plumb-bus", "version": bus.BUS_VERSION}

TOOLS = [
    {
        "name": "bus_send",
        "description": (
            "Send a message to another session on this project's bus (the Architect, "
            "the Implementor, a design partner).\n\n"
            "CHOOSING urgency — pick by the RECIPIENT's cost, not your own:\n"
            "  • 'gating'  INTERRUPTS them mid-turn, right now. Use it when this "
            "changes what they are doing at this moment — a ruling that redirects "
            "work, a stop, a correction. Interrupting is not free: a message that "
            "lands eight steps into a careful edit sequence derails work.\n"
            "  • 'normal'  arrives at their next turn boundary. Use it for anything "
            "they can read when they surface. This is the right default.\n"
            "You do NOT need a reply to have arrived to keep working — the answer can "
            "reach you mid-turn. Send and continue unless a wrong step in the meantime "
            "would be expensive or hard to reverse.\n\n"
            "IF THIS IS A RULING THAT GATES WORK: put it on the ledger FIRST and pass "
            "the reference as `record`. The ledger is readable without waiting on "
            "anyone's turn — including by an agent that was not running when you ruled. "
            "The message is the notification; the ledger is the record.\n\n"
            "There is no subject line. Put everything in `body`."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {"type": "string",
                       "description": "Recipient agent name, e.g. 'impl' or 'arch'. "
                                      "Use bus_status to see who is on this bus."},
                "body": {"type": "string",
                         "description": "The whole message. No length ceiling."},
                "urgency": {"type": "string", "enum": ["gating", "normal"],
                            "default": "normal",
                            "description": "gating = interrupt them now; "
                                           "normal = arrives at their turn boundary."},
                "thread": {"type": "string",
                           "description": "Optional thread id, for grouping a durable "
                                          "exchange. Does NOT affect delivery — urgency "
                                          "is declared per message, by you."},
                "record": {"type": "string",
                           "description": "Reference to the durable record for this "
                                          "(issue id, doc path). Required in spirit for "
                                          "anything that gates work."},
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
        "name": "bus_ack",
        "description": (
            "Acknowledge a gating message once you have ACTED on it — not merely read "
            "it.\n\n"
            "'A ruling was delivered' and 'the recipient has acted on the ruling' are "
            "different facts. The sender can see delivered-but-unacked, which is the "
            "signal that tells them whether their ruling actually landed. Rulings "
            "arriving after the work they governed is a documented, repeated failure; "
            "this is what makes it visible."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "integer",
                                  "description": "Message id, shown with the message."}},
            "required": ["id"],
        },
    },
    {
        "name": "bus_status",
        "description": (
            "Who is on this bus, whether their monitor is actually running, what is "
            "pending, and what has been delivered but not acknowledged.\n\n"
            "A recipient whose monitor is 'dead' or 'stale' cannot be interrupted — "
            "gating messages to them will arrive late, at their next turn boundary. "
            "Check here when a peer seems unresponsive, before concluding a message "
            "was lost. Silence usually means someone is mid-turn; it never means the "
            "bus dropped something."
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
        if warning:
            out.append("")
            out.append(f"⚠ {warning}")
        if args.get("urgency") == "gating" and not args.get("record"):
            out.append("")
            out.append("Note: this was sent as gating but carries no `record`. If it "
                       "gates work, put it on the ledger too — the bus is the "
                       "notification, not the record.")
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


def tool_bus_ack(args):
    me = bus.whoami()
    conn = _conn()
    try:
        ok = bus.ack(conn, int(args["id"]), me)
        return (f"Acknowledged #{args['id']}." if ok else
                f"#{args['id']} was not acknowledged — it is not addressed to you, "
                f"does not exist, or was already acknowledged.")
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
            if r["unacked_gating"]:
                bits.append(f"{r['unacked_gating']} gating delivered-but-UNACKED")
            if r["quarantined"]:
                bits.append(f"{r['quarantined']} quarantined")
            lines.append("  " + ", ".join(bits))
        return "Bus status:\n" + "\n".join(lines)
    finally:
        conn.close()


HANDLERS = {
    "bus_send": tool_bus_send,
    "bus_inbox": tool_bus_inbox,
    "bus_ack": tool_bus_ack,
    "bus_status": tool_bus_status,
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
