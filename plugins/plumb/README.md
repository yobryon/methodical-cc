# PLUMB

**The evolution of MAMA.** Not a better methodology — a **host** for a methodology your project
authors and evolves, plus an evidence layer that works whether or not you adopt any methodology at
all.

It assumes nothing about your shape: not a separate implementor session, not an arc rhythm, not a
tracker, not a design partner. Those are asked, never imposed.

> A plumb line is the reference a thing is trued against: it builds nothing, it tells you whether
> what you built is straight. And *to plumb* is to investigate to the bottom.
>
> One idea in two directions: **make claims that survive, and check them against something that
> cannot flatter you.**

Design document: [`docs/plumb-design.md`](../../docs/plumb-design.md).

---

## What this plugin is for

PLUMB's job is **not to help agents work**. It is to make specific, repeatedly-observed failures
impossible or loud. Every piece of it is attached to an incident that actually happened — usually
more than once — across a sixteen-arc effort with four context losses, three implementor relays, and
41 catalogued failure shapes.

If something here looks like a helpful template, it is a bug. File it.

---

## The product goal

> **Keep the Product Owner as the decider. Remove them as the operator.**

Being the bottleneck is *correct* for a consequential call and *pure friction* for a chore. MAMA
made you its implementor's lifecycle operator — *"run `impl-end` and start a fresh one"* — when what
you actually did was compact it and say continue. So PLUMB deletes that chore rather than
automating it: the implementor compacts and continues, and is told in as many words that context
pressure is not a reason to stop.

---

## The one idea: three homes, split by genre and by owner

MAMA had a failure mode with a date. An Architect invoked `mama:arch-sprint-start` for its
*substance* and inherited its *template* with it — silently reintroducing three practices the
project had killed eleven arcs earlier. **Nobody decided any of it.** The scaffolding rode in
attached to a tool, and the tell was that no one could point to when it was chosen.

PLUMB is built so it cannot do that to its successor:

| | Norms | Methodology procedures | Project procedures |
|---|---|---|---|
| What | Standing behaviour, always on | An ordered sequence, run rarely | Same, but specific to you |
| Read | By habit, continuously | At the moment of need, by name | At the moment of need, by name |
| Lives in | **Your `docs/way_of_working.md`** | **A PLUMB skill** | **Your own `.claude/skills/`** |

That third column matters: *a ceremony that lives only in the record of the one time you ran it is
indistinguishable from a ceremony, until the second time.* **The shipped skill set is a floor, not a
ceiling** — establishing your way of working means authoring your own skills too, not just your
document.

**A PLUMB skill carries sequence. It does not carry norms.** When it needs a judgment, it reads your
process document and defers. Where the two disagree, **your document wins, loudly.**

A skill with no norms in it has no norms to smuggle.

---

## Getting started

```bash
plumb init          # scaffolds .plumb.toml + a process document — both deliberately EMPTY
plumb doctor        # validates the manifest; fails until establish has run — that's the design
```

Then run the **`plumb:establish` skill with the Product Owner.** The scaffold declares nothing —
no roles, no artifacts, no pre-written process — because a declaration nobody made is a suggestion,
and suggestions become obligations. Everything in both files arrives from that conversation:
`doctor` passing is the conversation's exit criterion. Both files belong in version control.

### The manifest: `.plumb.toml`

Declares **where artifacts live** and **what is dead**. It does not declare how to work; that is
prose, in your document, where a human wrote it.

```toml
process_version = 1
document = "docs/way_of_working.md"

[ledger]
adapter = "github"        # nonlinear | github | jira | linear | markdown

[artifacts]
plan      = "docs/arcs/arc_{arc}/implementation_plan.md"
decisions = "docs/decisions_log.md"

[artifacts.retired]
implementation_log = "Died with MAMA: triplication. Issue comments are the play-by-play."
```

**Artifacts are addressed by role, never by filename.** A skill asks for `plan`; the manifest
resolves it. A skill *cannot* name `implementation_log.md`, because it does not know that string.

**A retired role is a refusal that carries its reason:**

```
$ plumb path implementation_log
plumb: artifact role 'implementation_log' is RETIRED — this project does not have one.

  Reason on record: Died with MAMA: triplication. Issue comments are the play-by-play.

  This is not an error to work around, and creating the file anyway is the
  exact failure this refusal exists to prevent…
```

Add entries as you kill things. Never delete them — the entry *is* the guard.

### Commands

| | |
|---|---|
| `plumb path <role> [--sub k=v]` | Resolve a role — any `{token}` in its path via `--sub` (`--arc` is sugar). Exit `2` retired, `3` unknown, `4` no manifest |
| `plumb roles` | List live and retired roles |
| `plumb process [section]` | Print your process document, or one section — how skills consult your norms |
| `plumb decision next` | The next unclaimed decision number, read from the log |
| `plumb doctor` | Validate the manifest against the filesystem |
| `plumb ceremony list` | List this project's own procedures |
| `plumb ceremony new <name>` | Scaffold a project procedure in `.claude/skills/` |
| `plumb exemplars [name]` | Ceremony-skill exemplars from one project — calibrate, don't copy |
| `plumb patterns [name]` | Practices with their costs measured — consult after the interview |
| `plumb ledger guide` | How an arc and the states map onto your tracker |
| `plumb ledger states` | The normalized state vocabulary |
| `plumb migrate scan` | Inventory a MAMA project's artifacts and how alive each one is |

**The agent contract is the MCP server, not this CLI.** Agents get `bus_send` / `bus_inbox` /
`bus_ack` / `bus_status` (the bus) and `process_path` / `process_read` / `decision_next` (the
process host) as tools whose descriptions carry the guidance — the contract travels with the
session instead of depending on a skill being loaded. The CLI is the engine (monitors, hooks) and
the human surface; the retired-role refusal is the same utterance on both.

---

## The guards

The strongest single finding behind PLUMB:

> **Recorded procedural lessons do not self-apply.** The rAF-timing trap fired twice. Control-byte
> separators fired three times — twice against the same person who had *written the lesson down*.
> Shared-index commit races fired three times.
>
> **Lessons that can become guards, should.**

None of these require judgment, which is exactly why they belong in tooling rather than a document.
They work on any project, whether or not it has adopted the rest of PLUMB.

| Guard | When | Defends against |
|---|---|---|
| **Secret scan** | blocks `git commit` | Credentials entering history. Scans *added lines only*; suppresses obvious placeholders |
| **Control bytes** | blocks `git commit` | A source file `grep` will silently skip, so *"not found"* comes to mean *"not searched"* |
| **Foreign staged** | blocks `git commit` | Another agent's staged work riding into your commit under your message. Steps aside for `git commit -- <paths>`, which cannot sweep |
| **Build verdict** | warns after a run | `--no-build` testing a binary that contains none of your changes — *a green indistinguishable from a green* |
| **Skip count** | warns after tests | A suite printing `Failed: 0` while an entire layer is dark |

Two epistemics are doing the real work here, and both generalise past their guards:

- **A tool returning nothing is ambiguous between "absent" and "unsearchable."** Verify the tool
  could see before believing what it didn't find.
- **The reporting surface can be silent in a way indistinguishable from healthy.** Only driving
  crosses that.

### Turning guards off

```toml
[guards]
enabled = false        # all of them
secrets = false        # or one: secrets | control_bytes | foreign_staged
                       #          build_verdict | skip_count
```

A guard that fires wrongly is worth reporting rather than disabling — but it is your tree.

---

## Status

**0.2.0.** Everything below is built and, where it touches the harness, verified live:

- **The process host** — empty-by-design genesis (`init` → `establish`), role resolution with the
  retired-role refusal, the process reader, decision allocator, `doctor` — surfaced to agents as
  MCP tools and to humans as the CLI
- **The bus** — MCP send with two delivery classes, turn-state-aware monitor (`gating` interrupts
  mid-turn; an **idle** session is woken by anything pending — urgency rations derailment, and
  idle has none to ration), boundary sweeps at turn end, turn start, and session start, SQLite
  store, `mcc`-injected identity
- **Compaction survival** — PreCompact snapshots and steers the summarizer; SessionStart re-orients
  on `source=compact` only
- **All five guards**, and two drift detectors (unanswered gating rulings, decision-number
  collisions) inside the monitor's tick
- **Seven skills** — `establish`, `ceremony`, `promote` (about the methodology itself);
  `design-gate`, `drive`, `catalog`, `bus` (portable, epistemic, usable with no methodology at all)
- **The reference shelf** — the pattern library (costs measured, rejection criteria first-class)
  and the ceremony-skill exemplars (calibrate, don't copy)
- **The ledger layer** — guidance for nonlinear / GitHub / Jira / Linear, a real `markdown` adapter
- **`migrate`** — re-opens the process question for a MAMA project rather than porting its answers

MAMA stays shipped and enable-able. PLUMB is a separate plugin, not a replacement in place.

---

## The five norms

These are the one place PLUMB is permitted to state a norm, because they are norms about
*epistemics* rather than about process — and they are what the plugin is named for.

1. **"I remember" and "I verified" are different claims, and must be said differently.** *A true
   claim without its provenance label is indistinguishable from a measured one by the time it
   reaches a third person.*
2. **A gate's green means nothing until you have seen its red.**
3. **An invariant that survives a defect is not evidence** — it is a constraint the defect happens
   to satisfy. Ask which wrong answers also satisfy it, and test one on purpose.
4. **The reporting surface can be silent in a way indistinguishable from healthy.**
5. **Preserve the fact; refuse the flow.** *Rewriting the record so the demo reads better is the
   same instinct that produced the bug.*
