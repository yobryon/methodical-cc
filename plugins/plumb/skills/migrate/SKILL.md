---
name: migrate
description: Move an in-flight MAMA project onto PLUMB — by re-opening the question of what process it actually needs, not by porting the one it has. Challenges the structural assumptions MAMA imposed, uses the project's own history as evidence rather than as the answer, then forges a way of working the team chose. Nothing is deleted and MAMA keeps working. Use when adopting PLUMB on a project that ran MAMA.
---

# Migrate a MAMA project

**This is not a port.** Almost nothing needs converting.

What this is: an in-flight project gets the conversation it never had. A project on MAMA has been
running a process **it did not choose** — MAMA supplied one, and it worked well enough that nobody
re-opened it. This is the moment to re-open it.

> The question that caught MAMA's drift was *"can anyone point to when this was chosen?"*
>
> **Ask it of the process itself, not only of the files.**

The trap this skill exists to avoid is the obvious one, and it is the same shape as the drift: taking
the de facto process, writing it into a manifest and a process document, and calling that a
migration. That carries MAMA's shape forward *because it is what was there* — which is precisely how
scaffolding survives a change of tools.

**Two things make re-opening genuinely necessary rather than ceremonial:**

1. **The models changed.** MAMA was designed when they needed to be told what to do next. That is no
   longer the constraint, and it is the whole reason MAMA began to cost more than it returned. A
   project that adopted MAMA a year ago is carrying a shape built for a weaker collaborator.
2. **What happened is evidence of what happened.** It is not evidence of what is needed. A sprint doc
   written every arc for a year proves the ceremony ran, not that it earned its keep.

**Re-adopting most of what you had is a perfectly good outcome** — the difference afterwards is that
someone *can* point to when it was chosen, and say why. This skill re-opens the question. It does not
presume the answer.

**This wants a fresh context — it is a conversation, not a chore.** The migration is
conversation-dense and judgment-dense; run at the tail of a long working session, the judgment is
what degrades first. Start it as the session's main event.

---

## Step 1 — The unlearning pass, before any inventory

Do this **first**, deliberately, with the Product Owner. If you start from the artifacts, the
artifacts set the frame and you will spend the conversation defending them.

Put each of MAMA's structural impositions back on the table. For each: *did we choose this, or did it
come with the tool — and would we choose it today?*

- **Do you need a separate implementor session at all?** MAMA assumed yes. Two of the three projects
  behind PLUMB shipped substantial products with **no persistent implementor** — self-directed, with
  subagents and fan-out workflows. It is one of four delegation modes, and the only one that costs
  you a session to run and a bus to coordinate. `plumb patterns two-sessions` states the case and the
  cost.
- **Do you need arcs?** Bounded bodies of work with a start and a close is one shape. Continuous flow
  is another. MAMA had an opinion; PLUMB does not.
- **What was the arch/impl split buying you** — and is it still? The honest argument for it is *two
  agents with different jobs checking each other against something neither controls.* If in practice
  one of them mostly relays, that is not the split working.
- **Which ceremonies has nobody defended in months?** Not "which are stale" — that comes later from
  evidence — but which would nobody argue for if it vanished.
- **Where did MAMA make the PO do a chore?** Launching, ending, refreshing, relaying. Some of those
  are gone by construction now (an implementor compacts and continues). Others were never necessary.
- **What did you work around?** A workaround is a design note about the process. Ask what it was
  routing around, and whether that thing should exist.

Write the answers down as they are given. These become the process document's first real content —
**the first content anyone on this project actually chose.**

---

## Step 2 — Inventory, as evidence for the above

```bash
plumb migrate scan
```

Now the artifacts, and note what they are *for*: they answer *what happened*, which is input to Step
1's questions, not a substitute for them.

For each artifact the scan reports whether it exists and whether it is **alive** — last touched, by
whom, how long ago, against how active the repo is.

- **Disposition is a proposal; evidence outranks it.** An artifact marked `CARRY` whose every
  instance is stale is flagged for retirement anyway.
- **Three are `RETIRE` by design**, not by judgment: `implementation_log`, `brief`,
  `implementor_state`. Each carries the reason it died — **read the reasons out, do not summarise
  them.** The reason is what stops the artifact coming back.
- **An artifact maintained faithfully is not thereby justified.** Ask who reads it. Several of
  MAMA's were written every arc and read by no one.

Nothing is changed. The scan only reads.

---

## Step 3 — Sort what remains

| Ask | If yes | If no |
|---|---|---|
| Does anyone *read* this? | A live role → `[artifacts]` | Retire |
| Can you point to when we chose it? | It was decided | **Scaffolding.** Retire |
| Would you notice if it vanished? | Keep | Retire |

Retire generously. **A retired role is cheap and reversible; a carried-forward artifact nobody
maintains is a hazard that looks like state.** And retiring is not deleting — it converts a file into
a refusal with a reason attached, which is strictly more information than the file was carrying.

**Retire something that worked.** The retirements with teeth are the ones recording a practice you
chose, used, and *outgrew* — nobody was ever going to re-adopt the failure. If every entry in the
retired table records a thing that failed, the table is guarding doors nobody would open.

```bash
plumb migrate retired     # the [artifacts.retired] block this project has earned
```

---

## Step 3½ — Ask what the file tree asserts

**The directory structure is a claim about the process. It is the first thing a fresh session
reads, and it outlives every document that contradicts it.** Eighteen plan docs under
`docs/sprints/` assert *we work in sprints* more loudly than a process document asserting you do
not — retiring a rhythm leaves its folder structure behind, still teaching the old shape.

Walk the tree with the PO and sort **by role, not by age**:

- **Live artifacts filed under a dead rhythm** move to homes keyed by something durable (an issue
  id, a topic — whatever survives a change of cadence).
- **Records are live evidence that happens to be old.** A measurement a current ruling rests on is
  not archive material, however stale its folder looks — burying it buries what the ruling stands
  on.
- **Genuinely dead plans and ceremony output** go to an archive directory, where the tree stops
  asserting them.

This step exists because the first project to migrate found it *after* both skills had finished —
prompted by their PO, not by the tooling — and rated it the highest-value thing they did.

---

## Step 4 — Forge the way of working

Run **`plumb:establish`** properly — the whole thing, not an abbreviated version. Steps 1 and 2 have
given you a head start no greenfield project has: real history, and answers from a team that has
actually felt this process.

Three adjustments for the in-flight case:

- **Feed the archaeology in as evidence, never as the default.** *"You closed 14 arcs at roughly two
  weeks each"* is a finding worth putting in front of them. *"So we'll keep two-week arcs"* is the
  frame doing the deciding.
- **Carry earned norms forward with their evidence — establish's "write the minimum" does not apply
  here.** That is greenfield guidance; this project's norms arrived exactly the way the good ones
  arrive (logged as instances, promoted after recurrence, several carrying their scar), and starting
  thin would destroy the most valuable content it owns. **The burden is on deleting a norm, not on
  keeping it.** What gets rewritten is what MAMA *supplied*; what the team *earned* comes along.
- **Offer patterns after they have spoken** (`plumb patterns`), one at a time — including patterns
  describing things they already do. A practice they have run for a year and can now see the *cost
  and scar* of is a practice they can finally choose, rather than one they inherited.

Set `process_version = 1`. Whatever came before was not this project's process.

---

## Step 5 — Author the project's own skills

MAMA's sprint commands do not ship, and the rows that matter are the ones with **no replacement**:

| | |
|---|---|
| `/mama:impl-end` | **Nothing.** The implementor compacts and continues — there is nothing to end |
| `/mama:impl-begin` | **Nothing.** A user-launched implementor just starts working |
| `/mama:arch-sprint-*` | **Skills this project writes**, in this project's vocabulary |

That last row is the point of the migration. `arch-sprint-start` is *the skill whose template caused
the drift*; replacing it with another shipped skill would rebuild the failure with a new name. Use
`plumb:ceremony`, and write it in the team's own words — if they say "batch" or "cycle", the skill
says that, not "arc."

**Only write the ones they will actually invoke.** A project skill authored to fill a gap in a
diagram is scaffolding you made yourself.

---

## Step 6 — Keep everything, change one behaviour

- **MAMA state stays.** It is history, and history is cheap.
- **MAMA stays enabled** as long as the PO wants. Both plugins can be active; the command namespaces
  do not collide. Disabling is a session-control decision and it is theirs.

The one thing that must change is behavioural:

> **Stop invoking MAMA skills for their substance.**

That is exactly how the drift happened — a skill invoked for what it knew, dragging its template in
behind it. If a MAMA skill still holds something worth having, **take the substance and leave the
template**: write it into this project's own skill, in this project's words.

---

## Done when

- [ ] The **unlearning pass happened first**, and its answers are in the process document
- [ ] Every structural assumption was re-opened — separate implementor, arcs, the split, the chores
- [ ] Anything re-adopted was re-adopted **with a recorded reason**, not by default
- [ ] `[artifacts.retired]` has the three retired-by-design entries plus everything the inventory
      showed abandoned, each with a reason
- [ ] `[artifacts]` holds only roles someone actually reads
- [ ] **The file tree stopped asserting the old process** — live artifacts re-homed by role,
      records kept as evidence, dead ceremony archived
- [ ] The process document describes what this team **chose**, not what MAMA prescribed and not
      merely what they happened to do
- [ ] Project skills exist for the ceremonies they will really run, in their vocabulary
- [ ] Crossover traffic has moved to the bus
- [ ] Nothing was deleted; MAMA still works
- [ ] `plumb doctor` passes
- [ ] The PO knows `plumb:establish` is re-runnable, and that this was its first run

---

> **The measure of a good migration is not how much carried over.** It is whether, afterwards,
> anyone can say why each thing is there.
