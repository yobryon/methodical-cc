---
name: bus
description: How peer messaging works on this project — an interrupting bus with two delivery classes. Covers choosing gating vs normal by the RECIPIENT's cost, why silence never means loss, why a ruling goes on the ledger before the wire, and what to do when a peer's monitor is down. Use when messaging another session, or when a peer seems unresponsive.
---

# The bus

Messages between sessions travel over a bus this plugin owns, not the harness's team
protocol. The difference that matters: **a `gating` message interrupts the recipient
mid-turn.** It does not wait for their turn to end.

The tools carry their own guidance — `bus_send`, `bus_inbox`, `bus_ack`, `bus_status`.
This skill is the part that is not in a tool description.

## Who is on it

**Only sessions the user launched.** The Architect and the design partner always; an
Implementor where the project chose a user-launched one.

Not subagents — you get their answer as a return value. Not a CC team you are
coordinating — that has the harness's own messaging. And **session lifecycle is the
user's**: nothing here launches, refreshes or retires a session, and reaching for `mcc`
to do so is crossing a boundary rather than removing friction.

If your project's way of working is *the Architect drives everything with subagents and
workflows*, the only traffic here is Architect ↔ design partner. That is a complete shape,
not a degraded one.

---

## Choose urgency by the RECIPIENT's cost

The question is not *"am I blocked?"* It is **"does this change what they are doing
right now?"**

| | Lands | Send it when |
|---|---|---|
| `gating` | **Interrupts them, now** | A ruling that redirects work; a stop; a correction that makes their current step wrong |
| `normal` | Their next turn boundary | Everything else. **This is the default** |

Interrupting is not free. A message that arrives eight steps into a careful edit
sequence derails work in a way a queued one never does. Turn-boundary delivery has one
real virtue — it arrives at a coherent moment — and that is worth keeping for anything
that does not need to land immediately.

**You declare it, per message.** There is no inheritance from a thread, and a reply does
not become urgent because the question was. Only the sender knows whether the answer is
a *redirect*, and that is what urgency measures. A class that fires for *"yes, carry
on"* stops carrying information.

## You do not have to stop after asking

The reason "send and stop" was a rule is gone: an answer can now reach you while you
work. So keep working, unless a wrong step in the meantime would be **expensive or hard
to reverse** — which is an ordinary engineering judgment, not a protocol.

When your question genuinely does not change your next move, say so: **"proceeding
unless countermanded."**

## Silence is not loss

**Never infer a dropped message from silence.** Silence means the other session is
mid-turn, or not running. Re-sending creates duplicates that arrive together and read as
contradictions.

If you want to know rather than guess, ask: `bus_status` shows whether each peer's
monitor is actually running, what is pending, and what has been delivered but not
acknowledged.

## A ruling goes on the ledger *before* it goes on the wire

The bus is the **notification**. The ledger is the **record**.

A ruling that gates work is written to the issue at ruling time, and the message carries
the reference (`record`). The ledger is readable without waiting on anyone's turn —
including by an agent that was not running when you ruled, and by whoever replaces them.

This is not tidiness. Rulings arriving after the work they governed is a documented,
repeated failure, and the ledger is the only channel immune to it.

## Acknowledge gating messages once you have ACTED

`bus_ack(id)` — not when you read it, when you have acted on it.

*"A ruling was delivered"* and *"the recipient has acted on the ruling"* are different
facts. The sender can see delivered-but-unacked, which is the signal that tells them
whether their ruling actually landed.

## If a peer's monitor is down

`bus_status` will say `dead` or `stale`, and `bus_send` warns you at send time. It means
gating messages **will not interrupt them** — those arrive at that session's next turn
boundary instead, carrying a warning that tells the recipient their monitor is down.

Nothing is lost. It is late, and it says so.

Tell the PO: a monitor starts with its session and cannot be restarted from inside it.
Headless sessions never have one at all, which is expected rather than broken — they
receive at turn boundaries only.
