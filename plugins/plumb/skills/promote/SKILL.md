---
name: promote
description: Review the reflection log for observations that have recurred enough to become norms, and move them into the process document — and check whether norms already there have expired. The pass that makes a process document living rather than founding. Use at an arc close, a phase change, or whenever the log has grown faster than the norms.
---

# Promote — and expire

> **Every good norm in that project's process document arrived this way**: logged as an instance,
> promoted once it had recurred. The ones written up front were guesses; the ones promoted were
> earned. Left to memory, observations stay in the log where nobody reads them.

This is the pass that makes a process document *living* rather than *founding*. It runs in both
directions: observations graduate **in**, and norms whose premise has died graduate **out**.

Nothing here decides for the Product Owner. Promotion is a change to how the project works, and it
gets their assent.

---

## Step 0 — Read both halves

```bash
plumb manifest            # where the process document is, and the process version
plumb process --list      # its sections
plumb process "reflection"
plumb process "norms"
```

You are looking at two surfaces: the **log** (instances, dated, accumulating) and the **norms**
(standing behaviour, always on). This pass moves things between them.

> **A process document is most attractive to write to at exactly the moment its content is least
> reliable** — right after a vivid incident, when the sentence is good and the evidence is one
> event. A fresh scar is evidence of one event; a norm is a claim about many. One adopter promoted
> a drive norm the morning it was observed and corrected it twice within four hours — the log was
> where it belonged until it recurred.

---

## Step 1 — Find what has recurred

Read the log for **the same shape appearing more than once**, not for the most interesting entry. An
observation that is vivid and singular is a record; an observation that is dull and third is a norm.

The threshold discipline, taken from a case where it was applied explicitly:

| Instances | What it is |
|---|---|
| **1** | A record. Leave it in the log. Promoting now encodes that instance's accidents as if they were the rule |
| **2** | *"A pattern worth naming, not yet a practice worth prescribing."* Name it in the log; do not promote |
| **3+** | Promotable |

Cross the log against what actually happened: a shape can recur without anyone logging it twice.
Two entries plus a live instance you remember is three.

**Say out loud what you are NOT promoting, and why.** A candidate rejected for having two instances
is a candidate someone should look at again next pass — and silence about it is how it gets lost.

---

## Step 2 — State it in its most repeatable form

This is where most of the value is, and the first phrasing is usually not it.

- **Procedural beats dispositional.** *"Build what was ruled, watch the suite, and never make a red
  test green the easy way"* is repeatable. *"Trust your judgment against a ruling"* is not — it asks
  for a quality rather than an action, and a ruler with more context is usually right, which is
  exactly why the *tests* have to be the thing that objects.
- **Prefer the form the person who lived it used.** Several norms in the evidence project reached
  their sharpest statement as a correction by the practitioner, not the author. Keep their words.
- **Name a condition, not a slot.** A norm whose trigger names a sprint number expires silently when
  the numbering moves under it.
- **If it can be mechanised, say so.** Recorded *procedural* lessons demonstrably do not self-apply —
  one timing trap fired twice, control-byte separators three times, twice against the person who had
  written the lesson down. **Lessons that can become guards, should.** File the guard as an issue in
  the same pass and reference it from the norm.

---

## Step 3 — Promote the scar with the norm

A norm without its instances is a rule. With them, it teaches.

Carry at least one concrete instance, with what it cost. *"A skip is not a pass"* is a rule; *"28
tests went dark while the suite printed `Failed: 0`"* is why anyone will follow it.

Leave the log entry in place. The log is the record of *when we learned it*; the norms section is
what we do now. Deleting the entry destroys the provenance that makes the norm re-examinable later —
and **a record that says how it knows can be re-opened; one that merely states can only be
believed.**

---

## Step 4 — Expire what no longer holds

**The half nobody runs**, and the one the plugin's own closing line is about: *claims decay; build
the expiry in.*

Walk the existing norms and ask of each:

- **Is its premise still true?** A norm built on a constraint that has since been removed is not
  neutral — its failure mode can *invert*. One dependency override existed because a registry 404'd;
  after the registry was fixed, the same override silently installed a version skew. **When the
  reason dies, the rule dies the same day.**
- **Can anyone point to when this was chosen?** If not, it may be scaffolding that arrived attached
  to a tool rather than a decision anyone made. That is the tell.
- **Has it been superseded by a mechanism?** A norm that became a guard should say so and stop asking
  people to remember it.
- **Is it being followed?** A norm nobody follows and nobody misses is describing a project that no
  longer exists.

Retire by **moving it to the log with the date and the reason**, not by deleting it. A future reader
needs to know it was considered and dropped, or they will propose it again as fresh.

If retiring a norm also retires an artifact, say so in `.plumb.toml` under `[artifacts.retired]` —
that is what turns the decision into a refusal instead of a memory.

---

## Step 5 — Land it

- Write the promotions into the norms section, in the project's own vocabulary.
- Write the retirements into the log, dated, with reasons.
- **Bump `process_version`** if the shape of the work changed — not for wording. The version says
  *"we work differently now"*, and it is what lets a project say which process a decision was made
  under.
- Commit both files together. The manifest and the document are one change.

---

## Done when

- [ ] Every promotion has **3+ instances**, or a stated reason for going early
- [ ] Every promotion carries at least one scar with its cost
- [ ] Every promotion is phrased as an **action**, triggered by a **condition**
- [ ] Candidates you declined are named, so the next pass can reconsider them
- [ ] The existing norms were walked for expiry — **this is not optional; it is half the pass**
- [ ] Anything mechanisable has a guard filed against it
- [ ] The PO has agreed to the changes; this is a change to how the project works

---

> **Living document.** The log is the intake and this is the pump. A project that only ever promotes
> accumulates norms until nobody reads them; a project that only ever logs never changes how it
> works. Run both directions, or the document stops describing you.
