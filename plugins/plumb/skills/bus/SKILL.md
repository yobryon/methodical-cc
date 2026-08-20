---
name: bus
description: How peer messaging works on this project — an interrupting bus with two delivery classes. Covers the delivery physics of gating vs normal (interrupt a turn, or wait one out — turns can run an hour), why silence never means loss, why a ruling goes on the ledger before the wire, and the lookback (`bus.py log`). Use when messaging another session, or when a peer seems unresponsive.
---

# The bus

Messages between sessions travel over a bus this plugin owns, not the harness's team
protocol. The difference that matters: **a `gating` message interrupts the recipient
mid-turn.** It does not wait for their turn to end.

The tools carry their own guidance — `bus_send`, `bus_inbox`, `bus_status` — and the
lookback lives in a shell command, `bus.py log`. This skill is the part that is not in
a tool description.

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

## Urgency is delivery timing, nothing else

| | Recipient mid-turn | Recipient idle | Not running |
|---|---|---|---|
| `gating` | Interrupts, now | Wakes them, now | Next session start |
| `normal` | Waits for their turn's end — **which can be minutes or an hour** | Wakes them, now | Next session start |

Delivery always carries everything pending, in send order; class never reorders — if
you sent 1, 2 (`normal`) and then 3 (`gating`), they read 1, 2, 3. A peer who is not
running cannot be woken by anything; if your message needs them *now*, ask the user to
launch them.

Two facts worth having at your fingertips when you choose:

- **Turns run long.** `normal` to a busy peer means they may keep acting on what they
  already believe until their turn ends.
- **An answer to a question someone kept working past lands after they have chosen a
  branch.** If your answer rules on that fork, `gating` is what makes it arrive in
  time.

The rest is your call — you know your team, and you will grow your own norms about
what interrupts whom. That is as it should be.

## You do not have to stop after asking

An answer can reach you while you work. So keep working, unless a wrong step in the
meantime would be **expensive or hard to reverse** — which is an ordinary engineering
judgment, not a protocol.

When your question genuinely does not change your next move, say so: **"proceeding
unless countermanded."** And the phrase means *proceed* — actually proceed. Announcing
a plan and then going idle is asking permission with extra steps: the countermand
window is *while you work*, not before you start, and nobody treats your statement of
intent as a request awaiting approval.

## Going idle is silent — nothing announces it

The physics fact nobody states: **no peer is notified when you stop.** Idle-wake makes
stopping *safe* — anything pending will wake you — but it does not make stopping
*visible*. To your teammates, your going idle and your being mid-task look identical:
silence.

So the turn boundary is a communication act you perform by omission. If your stopping
*means* something — done with what was asked, blocked, handing off, queue empty — only
a message makes it mean that. Ending a turn with your loops closed and your leader told
is finishing; ending one with an unstated handoff is not resting, it is disappearing.

## Silence is not loss

**Never infer a dropped message from silence.** Silence means the other session is
mid-turn, or not running. Re-sending creates duplicates that arrive together and read as
contradictions.

If you want to know rather than guess, ask: `bus_status` shows whether each peer's
monitor is actually running and what is pending for them; `bus.py log` shows the
chronology, including your own messages still sitting `pending` — which is what a
"stale" peer usually turns out to be.

## A ruling goes on the ledger *before* it goes on the wire

The bus is the **notification**. The ledger is the **record**.

A ruling that gates work is written to the issue at ruling time, and the message carries
the reference (`record`). The ledger is readable without waiting on anyone's turn —
including by an agent that was not running when you ruled, and by whoever replaces them.

This is not tidiness. Rulings arriving after the work they governed is a documented,
repeated failure, and the ledger is the only channel immune to it.

## There is no ack, on purpose — the work is the acknowledgment

The bus asks for no receipts. An ack protocol existed and was removed: nobody called
it, and a monitor watching it manufactured false signal about people who were doing
everything right. **If you need confirmation that a message landed and was absorbed,
ask for it in the message** — "confirm when you've picked this up" is a conversation,
it gets answered, and the answer sits on the trail like everything else. The reply and
the commit are acknowledgments in themselves. **The board is one only where your team
has wired it to speak** — an inbox hook, a ticker — otherwise moving an issue is a
record nobody hears, and "I marked it Done, so they know" is a belief about a
subscription that does not exist. If nothing subscribes, say it on the bus.

## Tickers — your project's own wake-ups, riding our monitor

The harness allows monitors only from plugins, so a project cannot watch anything while
idle — except through us. `[tickers.<name>]` in `.plumb.toml` runs a project script
inside plumb's monitor with the bus's own contours: `normal` tickers run only when the
session is idle (their output *wakes* you — a tracker inbox check, a CI watch);
`gating` tickers may interrupt mid-turn. The script gets `$PLUMB_TICK_PREV` (epoch of
its last successful run) as its new-since-X cursor; non-empty stdout is delivered,
empty is silence. Guardrails are enforced (interval floor, output cap, failure
backoff) because the ticker is a tenant in the process that delivers your mail.

Seam manners: if your ticker watches a tracker whose notifications mirror bus traffic,
`bus.py refs --since 2h` lists record refs already delivered to you over the bus — an
inbox item citing one is redundant by construction, and suppressing it is your
script's one-line courtesy to your future attention.

## The trail answers questions — `bus.py log`

Every message is memorialized as it flows: sent, delivered (when, via what, and **the
repo's commit hash at that moment**). Nothing is asked of you to maintain this — it is
implicit. When you need to sort something out, query it:

```bash
bus.py log                          # chronology, one line per message + snippet
bus.py log --record PLANK-139      # everything ever said citing a durable record
bus.py log --thread t-7            # one conversation
bus.py log --from arch --to impl   # one direction of one pair
```

Use it before concluding anything from silence (a stale board usually shows as
`pending` right there), to check a claim that something was sent ("routed yesterday" —
was it?), and to re-read what was already said about a record before publishing more
derived from it.

## If a peer's monitor is down

`bus_status` will say `dead` or `stale`, and `bus_send` warns you at send time. It means
nothing can **interrupt or wake** that session — messages arrive at its next turn
boundary or session start instead, carrying a warning that tells the recipient their
monitor is down.

Nothing is lost. It is late, and it says so.

Tell the PO: a monitor starts with its session and cannot be restarted from inside it.
Headless sessions never have one at all, which is expected rather than broken — they
receive at turn boundaries only.
