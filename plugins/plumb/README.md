# PLUMB

**The evolution of MAMA.** Architect and implementor as separate sessions with an arc rhythm — but
the process lives in *your project*, not in this plugin.

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

## The one idea: norms in the project, procedures in the plugin

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
plumb init          # scaffolds .plumb.toml + a starter process document
plumb doctor        # validates the manifest against the filesystem
```

Both files belong in version control. Then make the process document *yours* — it is the source of
truth, and the starter is only a shape.

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
| `plumb path <role> [--arc N]` | Resolve a role. Exit `2` retired, `3` unknown, `4` no manifest |
| `plumb roles` | List live and retired roles |
| `plumb process [section]` | Print your process document, or one section — how skills consult your norms |
| `plumb decision next` | The next unclaimed decision number, read from the log |
| `plumb doctor` | Validate the manifest against the filesystem |
| `plumb ceremony list` | List this project's own procedures |
| `plumb ceremony new <name>` | Scaffold a project procedure in `.claude/skills/` |

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

**0.1.0 — foundations.** Built and tested:

- ✅ The process host: manifest, role resolution, retired-role refusal, process reader, decision
  allocator, `doctor`
- ✅ All five guards
- ✅ The skills attached to the deepest scars: `drive`, `design-gate`, `catalog`
- ✅ The process negotiation: `establish` (author the way of working *with* the PO) and `ceremony`
  (give a project procedure a home), plus `plumb ceremony list|new`

- ✅ The bus: MCP send, monitor for `gating` (interrupts mid-turn), Stop hook for `normal`, SQLite
  store, `mcc`-injected identity — verified live
- ✅ Compaction survival: PreCompact snapshots and steers the summarizer; SessionStart re-orients on
  `source=compact` only

Next, in build order: the ledger adapters, then `plumb:promote`, then the drift monitors.
**MAMA → PLUMB migration is deliberately last** — a migration written before PLUMB exists would be a
migration to a guess.

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
