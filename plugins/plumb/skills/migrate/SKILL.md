---
name: migrate
description: Move an existing MAMA project onto PLUMB. Inventories the MAMA artifacts and how alive each one is, separates what was chosen from what arrived as scaffolding, and turns the result into a manifest and a process document. Nothing is deleted and MAMA keeps working. Use when adopting PLUMB on a project that ran MAMA.
---

# Migrate a MAMA project

**Migration is not a file conversion.** Almost nothing needs converting. What needs doing is a
judgment, on each artifact, that nobody has made yet:

> **Can anyone point to when this was chosen?**

That is the question that caught MAMA's drift in the first place. An artifact nobody chose and
nobody maintains is not state to carry forward — it is scaffolding that rode in attached to a tool,
and carrying it forward is how the same process returns under a new plugin's name.

This is `plumb:establish` with a head start: the project's *de facto* way of working is already
written down, in its artifacts and its git history. Read it out of them rather than asking.

---

## Step 0 — Inventory, and let evidence outrank the default

```bash
plumb migrate scan
```

For each artifact it reports **whether it exists** and **whether it is alive** — last touched, by
whom, how long ago, measured against how active the repo is.

Two things to notice in the output:

- **Disposition is a proposal.** `CARRY` is a default, not a finding. An artifact marked `CARRY`
  whose every instance is stale gets flagged as a retirement candidate anyway, and **the evidence
  wins.**
- **Three artifacts are `RETIRE` by design**, not by judgment: `implementation_log`, `brief`,
  `implementor_state`. Those decisions are already made and each carries its reason. Read the reasons
  aloud to the PO rather than summarising them — the reason is what stops the artifact coming back.

**Nothing has been changed.** The scan only reads.

---

## Step 1 — Sort the rest, with the PO

For everything not retired by design, ask the question in its usable form:

| Ask | If yes | If no |
|---|---|---|
| Does anyone read this? | It is a live role → `[artifacts]` | Candidate for retirement |
| Can you point to when we chose it? | It was decided | **Scaffolding.** Retire it |
| Would you notice if it stopped existing? | Keep | Retire |

Retire generously. **A retired role is cheap and reversible; a carried-forward artifact nobody
maintains is a hazard that looks like state.** And the retirement entry is not a deletion — it is a
refusal with a reason attached, which is strictly more information than the file was carrying.

```bash
plumb migrate retired     # the [artifacts.retired] block this project has earned
```

---

## Step 2 — Recover the process from the artifacts

This is the part that has a head start over a greenfield `establish`. Do not interview for what the
repo already answers:

- **`git log`** — the real cadence. How big is an arc here, how often does one close, who touches what.
- **The sprint log and architect state** — the arc rhythm as actually run, including where it drifted
  from what MAMA prescribed. **Where they differ, what happened is the truth.**
- **Existing plans** — what a plan doc actually contains here, which becomes the shape of the
  project's own arc skill.
- **`docs/crossover/`** — how consults actually flowed. That traffic moves to the bus.

Then run the rest of **`plumb:establish`** for what the artifacts cannot tell you: roles and their
decision boundaries, how work is bounded going forward, the tracker, and cross-team relationships.
Offer patterns only after (`plumb patterns`), one at a time.

---

## Step 3 — Author the project's own arc skills

MAMA's sprint commands do not ship. `plumb migrate scan` prints the mapping, and the important rows
are the ones with **no replacement at all**:

| | |
|---|---|
| `/mama:impl-end` | **Nothing.** The implementor compacts and continues — there is nothing to end |
| `/mama:impl-begin` | **Nothing.** A user-launched implementor just starts working |
| `/mama:arch-sprint-*` | **Skills this project writes**, in this project's vocabulary |

That third row is the point of the whole migration. `arch-sprint-start` is *the skill whose template
caused the drift*; replacing it with another shipped skill would rebuild the failure. Use
`plumb:ceremony` to write the project's own — and if the team says "batch" or "cycle", the skill says
that, not "arc."

---

## Step 4 — Do not delete anything, and do not disable MAMA

- **MAMA state stays where it is.** It is history, and history is cheap.
- **MAMA stays enabled** for as long as the PO wants. Both plugins can be active; PLUMB does not
  overlap MAMA's command namespace.
- The PO decides when to disable MAMA per project. That is a session-control decision and it is
  theirs.

The one thing that *must* change is behavioural: **stop invoking MAMA skills for their substance.**
That is exactly how the drift happened — a skill invoked for what it knew, dragging its template in
behind it. If a MAMA skill still has substance worth having, take the substance and write it into
this project's own skill.

---

## Done when

- [ ] `plumb doctor` passes
- [ ] `[artifacts.retired]` carries the three retired-by-design entries **and** everything the
      inventory showed abandoned, each with a reason
- [ ] `[artifacts]` contains only roles someone actually reads
- [ ] The process document describes what the project **actually did**, not what MAMA prescribed —
      including the places those differ
- [ ] The project's own arc skills exist, in the project's own vocabulary
- [ ] Crossover traffic has moved to the bus
- [ ] Nothing was deleted; MAMA still works
- [ ] The PO knows `plumb:establish` is re-runnable, and that this migration was its first run
