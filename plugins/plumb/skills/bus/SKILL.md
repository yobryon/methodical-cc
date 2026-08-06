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
coordinating — that has the harness's own messaging. And the bus itself is **chat, not
control**: nothing here launches, refreshes or retires a session. Session lifecycle
belongs to the user *by default* — if your project's way of working assigns some of it
elsewhere, that is the document's call to make, not this skill's to forbid.

If your project's way of working is *the Architect drives everything with subagents and
workflows*, the only traffic here is Architect ↔ design partner. That is a complete shape,
not a degraded one.

---

## Choose urgency by the RECIPIENT's cost

The question is not *"am I blocked?"* It is **"does this change what they are doing
right now?"** — and it only matters while they are actually doing something:

| | Recipient mid-turn | Recipient idle | Not running |
|---|---|---|---|
| `gating` | **Interrupts them, now** | Wakes them, now | Next session start |
| `normal` | Their next turn boundary | **Wakes them, now** | Next session start |

**Urgency rations derailment, and an idle peer has no work to derail** — so both
classes deliver immediately to an idle session, waking it. That is what lets peers
activate each other and work drive itself without the user couriering sessions awake.
A `normal` message never means "may sit forever"; it means "don't derail work in
progress."

**Urgency decides *whether* an interruption happens; it never reorders messages.** When
a `gating` message interrupts a working peer, everything else pending for them rides
along in the same delivery, **in send order** — if you sent 1, 2 (`normal`) and then 3
(`gating`), they read 1, 2, 3, because the gating message may depend on the context you
sent before it. Batches are always chronological.

Interrupting mid-turn is not free. A message that arrives eight steps into a careful
edit sequence derails work in a way a queued one never does. Turn-boundary delivery
has one real virtue — it arrives at a coherent moment — and that is worth keeping for
anything that does not need to land immediately.

A peer who is not running receives at their next session start (the sweep runs at
session birth, turn start, and turn end). If your message needs them *now*, ask the
user to launch them — nothing can wake a session that does not exist.

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
nothing can **interrupt or wake** that session — messages arrive at its next turn
boundary or session start instead, carrying a warning that tells the recipient their
monitor is down.

Nothing is lost. It is late, and it says so.

Tell the PO: a monitor starts with its session and cannot be restarted from inside it.
Headless sessions never have one at all, which is expected rather than broken — they
receive at turn boundaries only.
