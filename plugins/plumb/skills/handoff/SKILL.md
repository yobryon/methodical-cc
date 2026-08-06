---
name: handoff
description: Write the state document that carries an arc across a context boundary — session end, compaction, or an implementor relay. Leads with what is MISSING rather than the green numbers, names closed options so they cannot be reopened as fresh, and labels committed-but-inert code as such. Use when approaching context exhaustion, handing an arc to a successor, or standing down mid-arc.
---

# Handoff at context exhaustion

**Context loss is routine, not exceptional.** The effort this comes from survived four of them and
three implementor relays. Three relays across live arcs cost **zero rework**; the one arc that had no
state document cost its successor a morning.

The shape below is what made the difference. It is not a template to fill in — each element is there
because its absence cost something.

This skill is the sequence. Your project's process document holds the norms; where the two disagree,
**the document wins and you say so out loud.**

---

## Step 0 — Load the project's own words, and find where this goes

```bash
plumb process "handoff"
plumb path state --arc <N>
```

If `plumb path` refuses the role as retired, **that refusal is a process statement** — read it and
stop. Do not write the file somewhere else.

---

## Step 1 — Hand off a TRUE boundary, not a hopeful one

Before writing anything, decide where you are actually stopping.

> **"Server done, render gap named precisely" beats a rushed finish.** The successor inherits *a
> position*, not a promise.

If you are three minutes from a real boundary, take the three minutes. If you are an hour from one,
stop now and name where you are. Do not finish sloppily to make the handoff read better — that is the
same instinct as rewriting a record so the demo reads better.

---

## Step 2 — Lead with what is MISSING

Not with the green numbers. This is the single most important ordering rule in the document, and the
reason is mechanical:

> **A suite that is green is exactly what would hide the gap.**

Open with the gaps, the unknowns, and the things you believe but have not verified. The passing
counts, if they belong at all, go at the bottom.

---

## Step 3 — The queue, in order

For each item, in the order the successor should take them:

- What it is, and what "done" means for it.
- **What the successor must not rediscover** — rulings already made, and **options already closed
  BY NAME, with the reason each is closed.** An option that is merely absent gets reopened as fresh;
  an option named as closed does not.
- What you would do next, and why — clearly labelled as your judgment, not as a finding.

---

## Step 4 — Environment traps, carrying the day each cost

Not as rules. As incidents, with their price attached.

> A successor who reads *"a skip is not a pass"* learns a rule. One who reads that **28 tests went
> dark while the suite printed `Failed: 0`** learns to distrust a green.

Include anything in the family of *"am I actually running what I built?"* — stale containers, anon
volumes serving old packages, config pins overriding code defaults, a build that depends on what
happens to be on the builder's disk.

---

## Step 5 — Label committed-but-inert code AS SUCH, in those words

**A committed file implies more than it should.** If something is typed, rendered, compiled, and
never actually invoked, say *"committed but inert"* — not *"implemented"*, not *"done, pending
wiring"*.

> A feature sat entirely inert behind four green gates: every callback typed, rendered, and never
> once invoked, with a green typecheck, green lint, and eleven green unit tests over an adapter that
> had never executed.

---

## Step 6 — Check your own staleness before you send it

The failure to check for here is the staleness shape **occurring inside the artifact built to
prevent it** — a ruling appended to the foot of a handoff whose earlier section still said "open."

- [ ] Every "open" in the document is still open.
- [ ] Every claim carries whether it was **remembered** or **verified**.
- [ ] Nothing states a number without saying when it was measured.
- [ ] Anything that gates work is on the **ledger**, not only in this document.

That last one matters most: a successor may read the ledger before they read this.

---

## Step 7 — The successor's side

State these expectations explicitly in the document, because they are what made three relays cost
nothing:

1. **First act: an ACK with a read-back.** Not "got it" — a restatement of the position in the
   successor's own words, so a misunderstanding surfaces immediately.
2. **First *working* act: verify the inherited claim** rather than building on it.

> Two fresh implementors materially improved the design they inherited by doing exactly this. A third
> found a flaw in the spec they were handed, on their first act.

**Decline to inherit assumptions.** When you inherit a declaration, re-derive or re-ask. The check
works precisely because the checker did not already believe the thing.

---

## If a compaction is what is coming

Compaction is a context event, not a process event — the same session continues, with less of its own
history. PLUMB's compaction hooks snapshot mechanical state and re-inject a pointer to this document
afterwards, but **they cannot author judgment.** What the hooks preserve is the pointer; what you
write here is the substance.

So write it *before* you are out of room, not as the last thing you do.

---

> **Living document.** If this taught you something about *how you work* rather than about the code,
> put it in the reflection log — that is the only intake. Norms arrive by recurrence, not by decree;
> `plumb:promote` graduates the ones that recur. Your process document is meant to grow.
