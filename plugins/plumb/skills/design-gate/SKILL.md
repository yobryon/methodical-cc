---
name: design-gate
description: Run a read-before-rule design gate. The Implementor brings the READ (measures what the code and the world actually do, and explicitly does NOT propose a design); the Architect RULES. Enforces the asymmetry in both directions — a read containing a proposal is a failure, and so is a ruling written without a read. Use whenever the next step is a decision rather than a build, in any rhythm.
---

# The design gate — read before rule

The highest-value single addition over MAMA, which had no equivalent.

**The gate is a STOP: no build starts against a design that has not been ruled.**

Three decisions in the effort this came from had their central premise **overturned by the read**.
One read found six silently-destructive database behaviours that nobody would have quoted correctly
from memory.

This skill is the sequence. Your project's process document holds the norms; where the two disagree,
**the document wins and you say so out loud.**

---

## Step 0 — Load the project's own words

```bash
plumb process "design gate"     # falls back: try "read-before-rule", then "arcs"
```

## Step 1 — Establish the asymmetry, out loud, before anyone writes

Two roles, and they do not blur:

| | Brings | Must not |
|---|---|---|
| **Implementor** | The **read** — what the code and the world *actually do*, measured | Propose the design |
| **Architect** | The **ruling** | Rule without a read |

State which role you are before you start. The failure mode is a read that contains a proposal, and
it is a failure because a read is trusted differently from an argument — once a measurement arrives
wearing a recommendation, the reader cannot separate what was found from what was wanted.

The mirror failure is a ruling written from memory. **Reading a schema and reading the data are
different acts** — one ruling declared a column inert from a reading of its schema; the count found
60 of 62 rows carrying values. Settled with a count instead of an argument.

---

## Step 2 — The read (Implementor)

**Measure. Do not argue, do not propose, do not recommend.**

What a read contains:

- What the code **does**, established by running or reading it — say which, per claim.
- What the **world** does — the actual data, the actual engine, the actual dependency. Driven, not
  quoted.
- **Enumeration where memory would be used.** When identity or scope widens, every site that assumed
  the old one is suspect *by enumeration, not by recall*.
- **What is not measured** — an honest scope statement is part of the artifact. Nothing is claimed
  past its evidence.

Label every claim with its provenance:

> **"I remember" and "I verified" are different claims and must be said differently.** A true claim
> without its provenance label is indistinguishable from a measured one by the time it reaches a
> third person.

Cheap observations are biased, and the bias looks like the product. If a probe answered, ask what a
*wrong* answer would have looked like — and whether you would have been able to tell.

**If the read makes the design obvious, say the read and stop.** Letting the ruler reach it
themselves costs seconds and preserves the separation that makes the next read trustworthy.

---

## Step 3 — The ruling (Architect)

Read the read. Then, before ruling:

1. **Ask which layer the outcome lands in.** A capability/seam, or a value of that seam? Overfitting
   a platform to its first consumer forecloses the strategy.
2. **Ask what else the thing you are changing was holding.** A guard named for a *condition* rather
   than a *purpose* silently accumulates purposes. A relaxation ruled without that question retired a
   guard that was protecting a real incident.
3. **Rule against a measured case, not in the abstract.** Rulings made against a real case nearly
   write themselves; rulings made in the abstract meet their third state later.
4. **Prefer amendments that make the failure impossible by construction** over documented cautions.
   A guarantee with a test behind it survives context loss; a caution paragraph does not.

Then record it:

```bash
plumb decision next -v      # numbers are claimed by the log, never from memory
plumb path decisions
```

**The ruling lands on the ledger at ruling time**, and the message is only the notification. Mark the
message `gating` if it changes what someone is doing right now — see `plumb:consult`.

---

## Step 4 — Build it, and watch the suite

For the Implementor receiving a ruling:

> **Build what was ruled, watch the suite, and never make a red test green the easy way.**

An Architect once ruled a validator relaxation. The Implementor built exactly that, watched two tests
go red, recognised that they encoded a real prior incident, and **stopped rather than updating them
to match the ruling.** The ruling was reversed.

The norm is **procedural, not dispositional.** *"Trust your judgment against a ruling"* is not
repeatable and is not the lesson — a ruler with more context than the builder is usually right, which
is exactly why **the tests** have to be the thing that objects.

**Corollary, and it is the dangerous half:** updating a test to match a ruling is a decision
requiring the same justification as the ruling itself. It is defensible, invisible, and the standard
way a guard protecting a real incident gets retired by accident.

---

## Step 5 — Close the gate

The gate is closed when:

- [ ] The read exists, is recorded, and contains no proposal
- [ ] The ruling exists, is numbered, and is on the ledger
- [ ] The ruling names the case it was measured against
- [ ] Anything the read *retired* is named as retired — a premise that dies should not linger

One gate's best day: an issue was told to re-measure an eight-day-old claim and **retired the
premise rather than the number.** That is the gate working. Re-running the query and reporting the
same figure is the gate merely functioning.

---

> **Living document.** If this taught you something about *how you work* rather than about the code,
> put it in the reflection log — that is the only intake. Norms arrive by recurrence, not by decree;
> `plumb:promote` graduates the ones that recur. Your process document is meant to grow.
