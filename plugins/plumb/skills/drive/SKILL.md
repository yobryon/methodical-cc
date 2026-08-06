---
name: drive
description: Run the closing drive of an arc — someone USING the thing, in the product, against real data, and writing a record of it. Not a review, not a test run. Enforces anchors named before the surface is opened, anchors measured on the day, parity as an equality between two live reads, and the honesty rule. Use at arc close where the arc changed anything a user sees, or any time you need to know whether green work actually works.
---

# The drive

**Every arc that ran one found defects in work that was closed, tested, and green.** One found four,
two of them P1s a user would have hit on day one. Another arc's *proof failed on its first attempt* —
a migration plan containing every correct statement in an order the engine could not run, because
**reading a plan is order-insensitive where execution is not.** No review finds that.

This skill is the sequence. Your project's process document holds the norms; where the two disagree,
**the document wins and you say so out loud** rather than proceeding.

---

## Step 0 — Load the project's own words

```bash
plumb process "drive"          # falls back: try "arc", then read the whole document
```

If your project's document says something about drives that contradicts anything below, **stop and
say so.** Do not silently follow this skill. Do not silently follow the document either — name the
disagreement, and let the human resolve it.

If the project has no drive section yet, proceed with this sequence and note at the end that the
project should write one.

---

## Step 1 — Name the anchors BEFORE you open the surface

An **anchor** is a value you already know, so that *"it renders"* can be distinguished from *"it
renders correctly."*

Write them down first, in the record, before opening anything. This ordering is the whole point: an
anchor chosen after you have seen the screen is not an anchor, it is a rationalisation.

- At least one anchor per surface the arc changed.
- Prefer values that are *never* blank in healthy data — production history, a known total, a
  specific row you can name.
- For a rolling window, **name the formula alongside the value**; the world moves between naming and
  driving.
- Pick boundary rows **by design, not by luck**. Sampling in order lets luck operate, and luck is
  not a method.

> An arc once rendered an emptied grid for an entire sprint. Every structural check agreed with
> itself — 61 groups before and after; grid, drill, overlay, loop all fine. It was looked at directly
> in three verification passes without being seen, because **absence of data and absence of correct
> data render identically.** The measurement that would have caught it existed the whole time,
> unasked.

## Step 2 — Measure the anchors ON THE DAY

Never quote a number forward. Three sharpenings, each earned by a separate failure:

1. **A number that reproduced an hour ago is not a number you have.** Two readings disagreed inside
   one session because the semantic model gained a product mid-drive. The system was correct at every
   run; the ground moved.
2. **Re-measuring protects the CLAIM, not just the number.** A figure reproduced to within a
   fraction of a percent while the sentence wrapped around it had been false for eight days — a
   mechanism landed after the claim was filed and quietly took its correctness load. **The stale part
   was never the digits; it was the sentence.** So ask what the number is being used to *assert*, and
   measure that.
3. **A number without its unit is not a measurement, it is an invitation** — and the invitation is
   always accepted in whichever unit the reader already cares about. Never state a rate without its
   denominator attached to the same phrase (*"46.5% of refusing products"*, never *"of the refusing
   population"*). Where something can be counted more than one way — rows vs groups, leaves vs nodes
   — **report both and say which question each answers.**

## Step 3 — Drive it

**Use the thing.** In the product. Against real data. As a user would.

- Not a review. Not a test run. Not a screenshot of a component in isolation.
- If a surface cannot be reached the way a user reaches it, that *is* a finding — record it.
- **Reading is how you confirm what you already believe; running is how you find out.**

Watch for the family that only driving crosses — a signal that is **silent in a way
indistinguishable from healthy**:

- A test whose comment names a path it never executes.
- A gate that is green because its input was never supplied.
- A console that cannot say which version of the code it ran.
- A response that reads identically on success and on failure.
- A skip condition that lies.

## Step 4 — Assert parity as an equality between two live reads

Never against a remembered number. Two reads, both taken now, asserted equal.

And interrogate any invariant that holds: **an invariant that survives a defect is not evidence — it
is a constraint the defect happens to satisfy.** Ask which wrong answers *also* satisfy it. If you
can name one, test it on purpose.

> Two readings, 582 rows and 583 rows, both summing to exactly the parent total. The arithmetic gate
> the arc owed was satisfied by a right answer and a stale one alike.

## Step 5 — Write the record

Resolve where it goes:

```bash
plumb path drive_record --arc <N>   # or: plumb roles, to see what this project declares
```

If the project has no role for a drive record, put it where its process document says arc evidence
goes, and say which choice you made. **Do not invent a new artifact type.** If `plumb path` refuses
a role as retired, that refusal is a process statement — read it and stop.

The record's shape, which is fixed:

1. **What the suites said.**
2. **What the drive found.**
3. **What it cost to see.** — this is the part that makes the next drive cheaper, and the part
   everyone omits.

Two rules on writing it:

- **When the product turns out righter than the script, the script changes and the record says so
  *in that order*.** Never silently reshoot to match.
- **Preserve the fact; refuse the flow.** If something is wrong-but-real, keep the record and fence
  its use. *Rewriting the record so the demo reads better is the same instinct that produced the
  bug.*

## Step 6 — Route what you found

- Defects → the ledger, as issues, now.
- Shapes → `plumb:catalog`, if the defect's *shape* is understood. The fix goes in the commit; the
  shape goes in the catalog.
- Rulings needed → `plumb:consult`, marked `gating` if it changes what someone is doing right now.

---

## The failure this skill exists to stop

**A good reason not to look.**

An implementor once declined a drive on honest-sounding grounds — staging it would have meant
manufacturing a decision to photograph. The architect pushed anyway. Fifteen minutes found a P1.

The reason was *about the product, not about convenience*: it invoked a rule the project genuinely
held, and reached a conclusion that happened to be less work. **A lazy excuse gets caught by anyone
reading it; a principled-sounding one recruits the reader's agreement.**

> **An explanation is the thing that stops you measuring.** The only defence against a good reason
> not to look is looking anyway.
