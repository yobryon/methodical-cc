---
name: ceremony
description: Author or update a project procedure as a project-owned skill in .claude/skills/ — an ordered sequence, run rarely, specific to this project. Refuses one that is really a standing norm (belongs in the process document) or really a one-off (belongs in a record). Use the second time you run something, or when you catch yourself reconstructing a sequence from a retro.
---

# Author a project procedure

> **A ceremony that lives only in the record of the one time we ran it is indistinguishable from a
> ceremony, until the second time.**

That sentence is why this skill exists. The project it came from had a six-step grain-change ceremony
that lived only as prose in a roadmap and inside one sprint's record. When someone proposed a seventh
step — correcting an omission that had already cost them — **there was nowhere to put it.**

The trap is self-reinforcing. Their lesson *was* that the ruled steps had missed a part, and they
wrote that lesson into a retro and a record — **which is where a procedure goes to not be followed.**

A project procedure needs the same home a methodology procedure has: **a skill, invoked by name, at
the moment of need.** Ours ship with the plugin. Yours live in your repo.

---

## Step 1 — Check the genre. Four ways this is not the ceremony you think it is

Answer all four before writing anything. Getting this wrong is how the third home becomes the new
drift vector.

### Is it really yours to run?

**Will you still be the ones running this in a year — or are you standing in for a user who will?**
A project ceremony asserts *this is how we work.* A sequence you perform only because you currently
occupy a chair your product will hand to its users is not your way of working — it is a user
journey you happen to be rehearsing. Its durable content belongs in the failure catalog or an
operator runbook; its ordering belongs, eventually, in the product.

This check exists because the first migrated project authored a well-evidenced, well-shaped
ceremony that passed every craft check below — and their PO rejected it on exactly this ground.
For a project building a platform, this is the check that will catch the most.

### Is it really a norm?

A **norm** is a standing behaviour, always on, checked by habit. A **ceremony** is an ordered
sequence, run rarely, consulted at the moment of need.

| Norm | Ceremony |
|---|---|
| *Rulings land on the ledger at ruling time* | *How we retire a column* |
| *States move as work moves* | *How we onboard a new data source* |
| *Report the skip count with the pass count* | *How we cut a release* |

If it has no order, it is a norm. **Put it in the process document** — and say so rather than writing
it here, because:

> A document read for standing behaviours is exactly where a rarely-run sequence goes unread — and
> the reverse is just as true. A norm buried in a skill nobody invoked today is a norm nobody
> applied today.

```bash
plumb process --list        # where norms live
```

### Does it fire at a moment of insight, or a moment of decision?

A procedure whose trigger is *insight* — the shape becoming clear mid-thought, mid-reply —
gets bypassed, because stopping to fetch a procedure means leaving the thought to go and
get a form. **A bypassed ceremony looks like coverage.** If the material arrives at a
moment when its author has the content but not the patience, shape the skill as a
**review of what they wrote**, not a procedure for writing it: the moment produces the
artifact; the skill checks it afterward.

### Is it really a one-off?

**Has this been run more than once, or are you about to run it a second time?**

If neither, it is a record, not a ceremony. Write it up where the project puts evidence and come back
when it recurs. Writing a ceremony from a single instance means encoding the accidents of that
instance as if they were the procedure — and nobody will be able to tell which parts were which.

The honest exception: a sequence you *know* will recur and whose first run was expensive enough that
you do not want to re-derive it. Say that explicitly in the skill, so the next reader knows it has
one instance behind it rather than five.

---

## Step 2 — Calibrate, then scaffold

```bash
plumb exemplars                     # first time authoring one? read an exemplar for the GRAIN —
                                    #   how thin, how much doc-pointing, what an amendment looks like.
                                    #   Calibrate against it; do not copy it.
plumb ceremony list                 # what this project already has — check for a near-duplicate
plumb ceremony new <name> --description "<when to reach for this>"
```

The description is the trigger, and it is what gets matched when someone needs this without
remembering it exists. Write it as *when*, not *what*.

---

## Step 3 — Write the sequence, under two inherited rules

### Rule 1 — Address artifacts by ROLE, never by filename

```bash
plumb roles                         # what this project declares
plumb path <role> [--arc N]         # or the `process_path` tool — same contract, same refusal
```

**This is mechanical and non-negotiable, and your own skills are the likeliest place for it to be
broken.** A project procedure is written close to the work, in a hurry, by someone who knows the
filename — which is exactly the condition under which a retired artifact gets reinstated.

A skill that cannot say `implementation_log.md` cannot bring one back. Yours are not exempt from
that; they are the reason it matters.

If `plumb path` refuses a role as retired, **that refusal is a process statement.** Read it. Do not
route around it by writing the filename directly.

### Rule 2 — Carry sequence, not standing behaviour

If a step turns out to be *"always do X"*, it escaped from the document. Move it back.

### And write the trigger as a condition, not a slot

> A ruling whose trigger named a *sprint number* expired silently when the numbering moved under it.

*"When a fact table's grain changes"* survives. *"In Sprint 12"* does not.

---

## Step 4 — Make it checkable

Every ceremony ends with **how you know it worked** — checkable, not felt.

This is where most of the value is, and it is the part that decays first. The grain-change ceremony's
omission was precisely of this kind: six ruled steps, and none of them asked *what the contract
stopped saying* — so the retire-out half went unnamed until it cost something.

For each step, ask: **what would it look like if this step were skipped, and would anyone notice?**
If the answer is "no", that step needs a check, or it needs to become a guard.

---

## Step 5 — Amend rather than re-derive

The reason this home exists is so a procedure can be *corrected in place*.

When a run of this ceremony finds a missing step:

1. **Add it here, now**, while the instance is fresh.
2. Note what it cost — a step whose price is recorded gets followed.
3. If the omission has a *shape*, send it to `plumb:catalog` as well. The ceremony gets the fix; the
   catalog gets the shape.

**Do not write the correction into a retro and leave the ceremony unchanged.** That is the exact
failure this skill was built to end.

---

## Done when

- [ ] It is genuinely a sequence, genuinely recurring, genuinely **yours to run**, and shaped for
      its trigger (a decision-moment procedure, or an insight-moment **review**) — all four checked,
      not assumed
- [ ] The description says **when**, and names a condition rather than a slot
- [ ] No filenames — every artifact reached through `plumb path <role>`
- [ ] No standing behaviours — those went to the process document
- [ ] A "done when" that is checkable
- [ ] Committed. **A project procedure is design memory** and belongs in version control beside the
      process document
