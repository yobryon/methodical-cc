---
name: catalog
description: Add an entry to the failure-shape catalog — the shapes defects take here, ordered by WHY THEY HID rather than by what broke. Enforces the portable shape (what happened / why it hid / the tell, phrased as something to TRY / how it differs from its nearest kin) and refuses an entry that is only a bug report. Use when a defect's shape is understood, which is not the same moment as when it is fixed.
---

# The failure-shape catalog

Not a bug list. **A catalogue of the shapes defects take here, ordered by why they hid.**

> **A defect anyone would have caught teaches nothing.**

The effort this comes from accumulated 41 entries. Its highest-value use was **prospective** — an
entry used to design a test *before the code existed*, and another used to refuse building something
into a surface nobody reads. That is the catalog working. Explaining a defect afterwards is the
catalog merely functioning.

This skill is the sequence. Your project's process document holds the norms; where the two disagree,
**the document wins and you say so out loud.**

---

## Step 0 — Load the project's own words, and find the catalog

```bash
plumb process "failure"        # or "catalog"
plumb path failure_catalog
```

---

## Step 1 — Check that this is a shape, not a bug

**Write the entry when the defect's SHAPE is understood — not when it is fixed.** The fix goes in the
commit. The shape goes here. These are different moments and often different days.

Refuse the entry if you cannot answer all four of Step 2. In particular, refuse it if the honest
answer to *"why did it hide?"* is **"nobody looked"** — that is a process gap, not a shape, and it
belongs in a retro.

**The test of an entry is portability:** could someone who was not here use it on code we have never
seen? If the entry only makes sense with this codebase in hand, it is a bug report wearing a
catalog's clothes.

---

## Step 2 — The four required parts

An entry that is missing any of these is not an entry.

### 1. What happened
Briefly. The mechanism, not the symptom, and not the story of the debugging.

### 2. Why it hid
**This is the organising axis of the whole catalog** — entries are ordered by this, not by severity
or subsystem. Two lenses have proven most productive:

- **The reporting surface was silent in a way indistinguishable from healthy.** A test whose comment
  names a path it never executes; a gate whose input was never supplied; a response that reads
  identically on success and failure.
- **It supplied the feeling of having checked.** A sum that held because one addend was always zero;
  a search exclusion with a good reason; a probe that answered `200`; a claim written into a ledger.
  **None of these misbehaved** — which is why more care cannot fix any of them, and why every defence
  in this family has to be mechanical.

If you can say *which inquiry this ENDED rather than started*, say that. It is usually the sharpest
sentence in the entry.

### 3. The tell — phrased as something to TRY
**Not something to look for.** A reader cannot act on "watch out for stale config"; they can act on
"when a ruling changes a default, grep for config pins of the same key."

Make it a move: a command, a check, a question with a procedure attached.

### 4. How it differs from its nearest kin
Name the closest existing entry and say what distinguishes them. Without this the catalog degrades
into synonyms, and a reader looking for the shape they have finds four that almost fit.

If it has no kin, say that too — a genuinely new family is worth marking.

---

## Step 3 — Ask whether it can become a guard

The strongest finding behind this whole plugin:

> **Recorded PROCEDURAL lessons do not self-apply.** One timing trap fired twice. Control-byte
> separators fired three times — twice against the same person who had written the lesson down.
> Shared-index commit races fired three times.
>
> Recorded **structural** shapes *did* self-apply.
>
> **Lessons that can become guards, should.**

So, for every entry, answer explicitly: **can this be mechanised?**

- If yes → file the guard as an issue *now*, and reference it from the entry. An entry whose guard
  was never built will fire again, and the entry will be there to watch it happen.
- If no → say why not, in the entry. "Requires judgment" is a legitimate answer and worth recording,
  because it tells the next reader not to go looking for a check that cannot exist.

Guards already shipped by PLUMB, so you do not re-file them: secret scan, control bytes, foreign
staged entries, build verdict, skip-count surfacing.

---

## Step 4 — Write it, and place it by why-it-hid

Append to the catalog under the family it belongs to, not at the end. If it starts a new family,
name the family.

Then check the entry against itself:

- [ ] Portable — usable by someone who was not here, on code they have never seen
- [ ] The tell is a **move**, not a warning
- [ ] Its nearest kin is named
- [ ] The guard question is answered either way
- [ ] It says why it hid, not just what broke

---

## Using the catalog prospectively

This is the part worth building a habit around, because it is where the value actually is:

- **Before writing a test**, scan the catalog for the shape this code could take. One entry was used
  to design a test before the code existed.
- **Before building something ruled**, check whether the catalog already refuses it. One entry
  prevented a shape for the first time rather than explaining one — an implementor declined to build
  a ruled sentence into a surface nobody reads, citing the entry, prospectively.
- **At a design gate**, ask which entry the proposed design would make possible.

An entry read only after a defect is an entry that arrived too late to do its job.

---

> **Living document.** If this taught you something about *how you work* rather than about the code,
> put it in the reflection log — that is the only intake. Norms arrive by recurrence, not by decree;
> `plumb:promote` graduates the ones that recur. Your process document is meant to grow.
