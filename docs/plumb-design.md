# PLUMB — Design Document

**Status:** Design
**Date:** 2026-08-05
**Authors:** Bryon (Product Owner) + Claude (design partner)

PLUMB is MAMA's successor. **It is not a better methodology. It is a host for a methodology the
project authors and evolves** — plus an evidence layer that works whether or not the project adopts
any methodology at all.

---

## 0. The problem

### 0.1 MAMA got in the way, and the reason is specific

MAMA served well early and then began to cost more than it returned as the models improved. The
diagnosis is not "the process was wrong" — most of MAMA's content was right. It is:

> **MAMA made a constant out of something where the right answer is a variable.**

Two projects (a Linear clone and a grid component) ran to substantial v1 with **no methodology at
all** — self-directed, fan-out workflows, no persistent implementor — and did excellently. A third
was told to *invent its own way of working* and did excellently by a completely different route,
producing sixteen arcs of evidence discipline. MAMA-as-written, imposed uniformly and up front,
produced increasing friction.

**The common factor in the successes is not the amount of process. It is that the agent chose it.**

### 0.2 The friction that actually costs the Product Owner

The PO is usually the bottleneck, and that is **correct** when the question is consequential — a
direction to set, a product call, a boundary to move. It is **pure friction** when it is a chore.

The canonical instance, and the one that matters most:

> The Architect stops and asks the PO to *"run `impl-end` and start a fresh implementor"* — when
> what the PO actually does is compact the implementor and tell the Architect to continue.

Stated as the finding it is:

> **The cost of the independent implementor is not the implementor. It is that the PO became its
> lifecycle operator.**

The separate-instance implementor is defended on context and permission grounds, and those are real.
**But nothing in that argument requires the PO to be the one who starts and refreshes it.** If
session lifecycle were agent-drivable, the independent implementor would keep its benefits and shed
nearly all of its friction.

So PLUMB's product goal, in one line:

> **Keep the PO as the decider. Remove the PO as the operator.**

This is *the* acceptance test for the product. A feature that makes the methodology tidier while
leaving the PO running session chores has not paid for itself.

### 0.3 The pivot

> **MAMA's skills answer *"what do I do now?"* PLUMB's answer *"is what I just did true?"***

Orchestration → verification. This generation of models does not need to be told what is next; they
are excellent at driving. What they still need is **something that cannot flatter them** — which is
also why the name works. A plumb line builds nothing; it tells you whether what you built is
straight.

### 0.4 The three layers, deliberately separable

| Layer | What it is | Depends on |
|---|---|---|
| **1. Process host** | The project's way-of-working document as the single source of truth; the manifest; role resolution; retired-ceremony refusal; the pattern library; `establish` | Nothing |
| **2. Evidence layer** | The epistemic norms and the scar-attached skills — `design-gate`, `drive`, `catalog`, `promote` — plus the mechanical guards | Nothing. **Usable standalone by any project with zero methodology attached** |
| **3. Mechanism** | The bus, per-agent identity, worktrees, the decision allocator | `mcc` for identity injection |

Layer 2 standing alone is not a nice-to-have; it is the generalization test in §0.5 made structural.

### 0.5 The standing generalization test

Every candidate feature gets asked:

> **Would this have helped the two projects that ran with no methodology at all?**

If yes, it generalizes and PLUMB may ship it. If it only helps a project shaped like the one that
produced our evidence, **it belongs in that project's own skills**, authored by `establish` (§11.1).

This test exists because the richest evidence available to us came from *one* team, in *one* domain,
and the failure mode of rich evidence is shipping it as law. The pre-commit guards, the drive
protocol, and *a gate's green means nothing until you have seen its red* all pass. An arc-planning
skill does not.

---

## 1. Evidence base, and what it is not

The deepest input is a field proposal from the Architect of a project that ran **sixteen arcs over
roughly six months**: four context losses, three implementor relays, ~1,150 tests, 48 decisions, 41
catalogued failure shapes. Every recommendation in it traces to something that actually happened,
usually more than once. Its companion is that project's living way-of-working document. A throwaway
spike (`tmp/spike-plumb/FINDINGS.md`) measured what the plugin surface can actually do.

**That proposal is evidence, not thesis.** It is magnificent and it is 41-failure-shapes deep in
*one* codebase, written by an agent describing the methodology it needs. Built faithfully, we would
ship that project's process as the new universal — which is MAMA's mistake again with better
content. §0.5 is the guard against exactly that, and it has already caught three skills that were
about to ship (§11.1).

Its own framing, which PLUMB adopts as the test for **layer 2 specifically**:

> **This plugin's job is not to help agents work. It is to make specific, repeatedly-observed
> failures impossible or loud.** Every skill that is merely "a helpful template" should be cut. The
> ones that survive are the ones attached to a scar.

### 1.1 The governing constraint

The single most important instruction in the proposal:

> **Make PLUMB describe the process rather than embed it.**

This is not a style preference. It is a bug report against MAMA, with a date. At Sprint 14 that
project's Architect invoked `mama:arch-sprint-start` for its *substance* and inherited its
*template* with it — silently reintroducing three practices the project had killed eleven arcs
earlier: an `implementation_log.md` per arc, the kickoff as a document section, and `/impl-end`
command ceremony. **Nobody decided any of it.** The scaffolding rode in attached to a tool, and the
tell is that no one could point to when it was chosen.

That project already had a name for the shape at other grains — *a pin outliving its reason*, *a
workaround outliving its cause*. Sprint 14 found it at process grain: **a process we evolved away
from can return through a tool that still encodes it.**

So PLUMB must be designed so it cannot do that to *its* successor. Everything in §2 follows.

### 1.2 What PLUMB does not assume

Held explicitly, because each was a MAMA fixture and none survives as one:

| Not assumed | Why |
|---|---|
| **A separate implementor session** | A **delegation mode selected by work shape**, not a fixture. Whole arcs → an implementor; bounded tasks → subagents; fan-out-shaped work → workflows. Two of our three successful projects used none |
| **An arc rhythm** | How work is bounded is asked, neutrally, at `establish`. Some projects flow |
| **A tracker** | Pluggable, with an honest degradation table for projects without one (§4.3) |
| **A design-partner role** | Asked, not assumed |

---

## 2. The core architectural idea: three homes, split by genre and by owner

The project that produced the proposal also produced, in its final reflection entries, an open
question it deliberately declined to answer:

> We own a **norms** surface that works — does its success generalize to **procedures**, or do
> rarely-run ordered sequences need their own genre?
>
> A norm is a standing behavior, always on, checked by habit. A ceremony is an ordered sequence run
> rarely, consulted only at the moment of need. **A document read for standing behaviors is exactly
> where a rarely-run sequence goes unread.**

**PLUMB's answer: they are different genres, and the plugin/project boundary is exactly where the
seam falls.**

| | Norms | Methodology procedures | **Project procedures** |
|---|---|---|---|
| What | Standing behaviour, always on | An ordered sequence, run rarely | An ordered sequence, run rarely, **specific to this project** |
| Read | By habit, continuously | At the moment of need, by name | At the moment of need, by name |
| Lives in | **The project's process document** (Ledger 2) | **A PLUMB skill** (shipped) | **A project-authored skill** in `.claude/skills/` (Ledger 2) |
| Example | *evidence outranks argument* | *how to run a drive*; *how to close an arc* | *the grain-change ceremony*; *how we cut a release here* |
| Authored by | The PO, over time | Us | **The PO and the agent together** (`plumb:establish`, `plumb:ceremony`) |

A skill is, structurally, already the procedures genre: named, invoked deliberately, consulted only
when you're about to do the thing. That is the genre match.

### 2.0a The third column is not optional — an earlier draft omitted it and reopened the question

This design document originally had two columns and claimed they resolved the source project's open
question *"do rarely-run ordered sequences need their own genre?"* **They resolve half of it.**

The question was raised by a concrete homeless artifact: a **grain-change ceremony** that existed
only as prose in a roadmap and inside the record of the one sprint that ran it. It is not a norm —
it is an ordered sequence, consulted at the moment of need. And it is not something PLUMB can ship,
because PLUMB has never heard of grain changes. With two columns it stays exactly where it was:

> **A ceremony that lives only in the record of the one time we ran it is indistinguishable from a
> ceremony, until the second time.**

And the trap is self-reinforcing: that project's lesson *was* that its ruled steps had missed a part,
and it wrote that lesson into a retro and a record — **which is where a procedure goes to not be
followed.**

So project procedures get a real home: **skills the project authors for itself**, living in its own
`.claude/skills/`, versioned with the code, invocable by name. Same genre as a PLUMB skill, same
invocation, different owner. The PO gets shorthand through their own established workflow; the
ceremony gets a place where it is consulted rather than remembered.

This also means **the shipped skill set is a floor, not a ceiling** — and that the process
negotiation which produces a project's way of working must produce *its skills too*, not just its
document. That is `plumb:establish` (§11).

The rule that falls out, and it is the whole defence against Sprint 14:

> **A PLUMB skill carries sequence. It does not carry PROCESS norms. When it needs a judgment about
> how this project works, it reads the project's process document and defers.**

### 2.0 The line, stated precisely enough to review against

"Carries no norms" is too absolute to survive contact with a real skill — `plumb:drive` cannot
usefully sequence a drive without saying *why* an anchor must be named before the surface is opened.
The distinction that actually holds:

| | **Epistemic** norms — PLUMB may state these | **Process** norms — the project's, always |
|---|---|---|
| About | How to know whether a claim is true | How *this project* works |
| Example | *An invariant that survives a defect is not evidence.* | *An arc closes with reconciliation.* |
| | *A gate's green means nothing until you've seen its red.* | *States move as work moves.* |
| | *"I remember" and "I verified" are different claims.* | *Product calls route to the PO.* |
| Portable? | **Yes** — true on any codebase, for anyone | **No** — earned here, expires here |

The test: **would this sentence still be true on a project that had never heard of us?** If yes, it
is epistemics and PLUMB may carry it — that is what the plugin is *named for*. If it describes an
artifact, a role, a state, a cadence, or a routing rule, it is process, and PLUMB may only *read* it.

**The mechanical half, and the one that actually stops Sprint 14 from recurring:** a skill may never
name an artifact by filename. It asks for a *role*, the manifest resolves it, and a retired role
resolves to a refusal (§3). A skill that cannot say `implementation_log.md` cannot reinstate one,
regardless of what norms it carries. Epistemics have no templates attached; process does, and the
templates are what rode in last time.

### 2.1 The consequences, stated as rules

1. **One source of truth for the process: the project's own way-of-working document, in its repo.**
   Skills *read* it. They never restate it.
2. **When a skill's guidance and the project's document disagree, the document wins — loudly.** The
   skill says so and stops, rather than quietly proceeding.
3. **Version the process, not just the plugin.** A project declares "we are on process v3" and the
   tooling honours it.
4. **Deprecated ceremony fails rather than fades.** A skill that would create a retired artifact
   refuses and names the reason.

Rule 4 needs a mechanism, not an intention. That mechanism is the manifest.

---

## 3. The process manifest

`.plumb.toml` at the project root — the project's declaration of its own way of working. Small,
hand-editable, versioned in the repo.

> **Why not `.mcc/process.toml`?** `.mcc/` is operational state and is gitignored. The manifest is
> the opposite: it is design memory, it belongs in Ledger 2, and it must travel with the code it
> describes. A root dotfile also makes *"is this a PLUMB project?"* a one-line check.

```toml
process_version = 3
document = "docs/way_of_working.md"

[roles]
architect   = "arch"
implementor = "impl"
design      = "pdt"

[ledger]
adapter = "nonlinear"          # nonlinear | github | jira | linear | markdown
space   = "PLANK"

[artifacts]
plan            = "docs/sprints/sprint_{arc}/implementation_plan.md"
decisions       = "docs/decisions_log.md"
backlog         = "docs/concept_backlog.md"
failure_catalog = "docs/failure_shapes.md"
drive_record    = "docs/sprints/sprint_{arc}/drive_record.md"

[artifacts.retired]
implementation_log = "Died Sprint 3: triplication. Issue comments are the play-by-play."
brief              = "Died Sprint 3: folded into plan + kickoff message."
```

Three things this buys, each attached to a scar:

**Artifacts are addressed by role, never by filename.** A skill says *"write the plan at the path
the `plan` role resolves to"*. It cannot name `implementation_log.md`, because it does not know that
string — the manifest does.

**`[artifacts.retired]` makes deprecated ceremony fail with its reason attached.** If a skill (or an
agent) reaches for a retired role, PLUMB refuses and prints the reason and the date. This is the
Sprint 14 guard, and it is mechanical: it does not depend on anyone remembering that the log died.

The refusal is deliberately worded to close the workaround, because the agent reading it is
precisely the party who could route around it:

```
$ plumb path implementation_log
plumb: artifact role 'implementation_log' is RETIRED — this project does not have one.

  Reason on record: Died with MAMA: triplication. Issue comments are the play-by-play.

  This is not an error to work around, and creating the file anyway is the
  exact failure this refusal exists to prevent: a process the project evolved
  away from returning through a tool that still encodes it.

  If the role should genuinely return, that is a PROCESS CHANGE, not a
  workaround: say so in the process document, then edit .plumb.toml.
```

Exit codes are part of the contract: `2` retired, `3` unknown role, `4` no manifest. A retired role
and a typo are different failures and must not be conflated — the first is a process statement, the
second is a mistake.

**`process_version` lets the plugin move without moving the project.** PLUMB upgrades ship with
migration notes, not silent behaviour changes.

> **Design note — deliberately not a schema for the process.** The manifest declares *where things
> are* and *what is dead*. It does not declare *how to work*; that is prose, in the document, where
> a human wrote it. The moment the manifest starts encoding process semantics, PLUMB has embedded
> the process again through a side door.

---

## 4. The two ledgers, and the pluggable one

The structural idea PLUMB inherits: **execution state and design memory live in different systems,
each shaped for its job.**

- **Ledger 1 — the tracker.** Work items, bugs, blockers, states, the play-by-play of doing.
  Survives context loss; queryable by every agent; readable **without waiting on a turn boundary**
  (this is what makes it the fix for the bus's turn-bounded delivery, not a workaround for it).
- **Ledger 2 — the repo.** Product docs, decisions log, concept backlog, one plan doc per arc, the
  failure-shape catalog. Versioned alongside the code it describes.

The boundary: *why / what / how-it-should-be* → a doc. *who / when / status / what-happened* → an
issue.

### 4.0 Guidance, not a wrapper — the decision and its reason

PLUMB does **not** wrap your tracker, and that is a deliberate reversal of this document's first
draft, which specified a six-operation interface with adapters behind it.

Two of the shipped options (`nonlinear`, `linear`) are **MCP servers** — the agent already holds
their tools, and a CLI could not call them regardless. The other two (`github`, `jira`) have mature
CLIs and MCPs that **carry their own guidance at the point of use**, which is the exact property
PLUMB spends its design budget on elsewhere (§7.1b). A wrapper over any of them would duplicate a
well-guided tool and could only fall behind it.

So PLUMB supplies the part a tracker cannot know about itself: **how an arc maps onto its native
grouping, what PLUMB's state vocabulary means in its workflow, how attribution works when several
agents share one identity, and what it cannot express.** `plumb ledger guide` prints it.

`markdown` is the exception and is real code, because there is nothing else to call.

**Consequence for the `--record` primitive:** a ruling reaches the ledger because the *agent* writes
it with the tracker's own tools, and passes the reference to `bus_send`. PLUMB does not perform the
write, so `record` is a reference the sender supplies — and `bus_send` says so when a `gating`
message arrives without one.

### 4.1 The normalized state vocabulary

```
triage → backlog → todo → in_progress → in_review → done
```

**States move as work moves.** ~16 issues once sat in `triage` while their work shipped, and the
Product Owner caught it rather than the agents. Where a tracker cannot express one of these, its
guidance says so rather than approximating silently.

### 4.2 Adapters shipped

| Adapter | Mechanism | Status |
|---|---|---|
| `nonlinear` | MCP, agent-native | Primary — this is what the evidence base ran on |
| `github` | `gh` CLI | Full support; issues + milestones (arc = milestone) |
| `jira` | REST | Full support |
| `linear` | GraphQL | **Best-effort, marked as such** — no account available to test against. Shipped unverified, and the adapter says so at load |
| `markdown` | Files in the repo | The honest degradation, see below |

**Each adapter ships GUIDANCE, not just code** — a setup section covering auth, how an arc maps onto
that tracker's native grouping (project / milestone / epic / fix-version), how PLUMB's normalized
states map to its workflow, and what it cannot express. An adapter that connects but leaves the PO
guessing at the mapping has moved the work rather than done it. `plumb ledger setup <adapter>` prints
it; `plumb doctor` checks the parts that are checkable.

**Arc mapping, per tracker** — the one thing every adapter must answer explicitly, because it is the
first thing a PO hits:

| Adapter | An arc is a… | Notes |
|---|---|---|
| `nonlinear` | project | One project per arc; issues are work items within it |
| `github` | milestone | Labels carry state where the Projects API is unavailable |
| `jira` | fix version *or* epic | Declared in the manifest — teams genuinely differ here, and guessing wrong is expensive |
| `linear` | project or cycle | **Unverified** |
| `markdown` | a directory | `docs/ledger/<arc>/`, one file per issue |

### 4.3 The `markdown` adapter, and answering "should the tracker be assumed?"

The proposal's open question 3: *our two-ledger split depends on an agent-native issue tracker; a
project without one needs a different Ledger 1, and the plugin should say which parts survive.*

**Answer: no, the tracker is not assumed — and PLUMB says exactly what degrades.** The `markdown`
adapter puts Ledger 1 in `docs/ledger/` as one file per issue. What survives and what does not:

| Property | Tracker | `markdown` |
|---|---|---|
| Survives context loss | ✅ | ✅ |
| Readable without a turn boundary | ✅ | ✅ |
| Queryable by state/assignee | ✅ | ⚠️ grep-grade |
| Visible across teams | ✅ | ❌ **lost** — cross-team provider/consumer norms do not survive |
| Per-agent attribution | ⚠️ see §7.3 | ✅ (author written inline) |
| Merge conflicts under concurrent agents | ✅ none | ❌ **real** — one file per issue mitigates, doesn't eliminate |

The adapter prints that table on first use. A project on `markdown` should know it is running
without the cross-team half of the methodology, rather than discovering it.

---

## 5. Guards — where lessons become guards

The strongest single finding in the evidence base, and the one that most changes what a plugin is
*for*:

> **Recorded procedural lessons do not self-apply.** The rAF-timing trap fired twice. Control-byte
> separators fired three times — twice against the same person who had written the lesson down.
> Shared-index commit races fired three times. **Lessons that can become guards, should.**
>
> (Recorded *structural* shapes did self-apply. It is specifically the procedural ones that decay.)

None of these require judgment, which is exactly why they belong in tooling rather than a document.
All ship as hooks; all are individually disable-able in the manifest.

| Guard | Event | Defends against | Incidents |
|---|---|---|---|
| **Foreign staged entries** | PreToolUse on `git commit` | One agent's staged work riding into another's commit in a shared tree | 3× — most recently caught the Architect mid-sentence *about process drift* |
| **Build verdict** | PostToolUse on build/test | `--no-build` running stale binaries after a failed build — *four green suites containing none of your changes* | 2× in two days, two different implementors. A green indistinguishable from a green |
| **Control byte / binary source** | PreToolUse on `git commit` | A source file containing raw control bytes; `grep` silently skips it, so "not found" means "not searched" | 3× |
| **Secret scan** | PreToolUse on `git commit` | Credentials entering history | Caught a live API token swept in by `git add -A` |
| **Skip-count surfacing** | PostToolUse on test runs | A suite reporting success while an entire integration layer skipped | 28 tests dark behind a lying skip condition; console said `Failed: 0` |

The generalisable epistemics behind two of these are worth stating, because they are what makes the
guards more than chores:

- **A tool returning nothing is ambiguous between "absent" and "unsearchable."** Verify the tool
  could see before believing what it didn't find.
- **The reporting surface can be silent in a way indistinguishable from healthy.** A skip is not a
  pass; a green is not a green if it ran the wrong binary.

### 5.1 Per-agent worktrees

The proposal calls this *"the single highest-value structural change"* — it would delete the
shared-index race class outright, and that class has cost attribution three times plus one
near-miss where content could have been lost.

**Position: ship it as opt-in, not default, and say why.** The proposal's own open question 2 is
the blocker: *are per-agent worktrees compatible with a shared dev environment* — containers
bind-mounting source, one database, one running app? Theirs could not trivially fork. A default
that breaks the dev loop of the project that asked for it is not a default.

So: `[worktrees] enabled = true` in the manifest, with a documented compatibility checklist. The
foreign-staged-entries guard is the shared-tree fallback and stays on either way.

---

## 6. Drift detectors

The spike confirmed plugin-shipped monitors auto-launch, run at ~1 Hz in the session's working
directory, survive compaction as the same process, and **interrupt a turn mid-flight** — all
verified again live in the shipped plugin.

### 6.1 Two detectors, not five — and why the other three are absent

The proposal named five. Three are not shipped, and the reason is the same one that made the ledger
layer guidance rather than a wrapper:

| Not shipped | Why |
|---|---|
| **Ledger-state drift** | Requires reading the tracker. PLUMB does not proxy trackers (§4.0), so this could only work on one adapter — and a detector that works on one adapter is a detector whose *silence* means nothing on the others |
| **Plan-vs-delivery** | Same, plus it needs the project's plan shape, which is project-defined |
| **Stale pin** | Needs a project convention for what a pin looks like. Worth adopting — *a pin should carry its reason inline so its expiry is detectable* — but that is a norm for the process document, not something PLUMB can detect universally |

**The silence is the product.** A check you cannot trust when it says nothing is worse than no check
at all — it is the reporting surface that is silent in a way indistinguishable from healthy, which is
the failure family this plugin exists to attack. So PLUMB ships only detectors whose silence is
meaningful everywhere.

### 6.2 What ships

| Detector | Reads | Scar |
|---|---|---|
| **Unanswered gating** | The bus, which we own | Five rulings arrived after the work they governed. An architect could not tell *delivered* from *acted on*, because nothing distinguished them. Reported **to the sender**, since it is their ruling that may not have landed |
| **Decision collision** | The `decisions` role | Twice — once with both collisions in a single evening. Two agents ruling in parallel each read the log's tail and wrote the same next number |

### 6.3 They run inside the bus monitor's tick

Not as separate monitors. The harness stops monitors that produce too many events, so more processes
emitting more often is precisely how the one that actually matters gets shut off. One process, one
heartbeat: bus every tick, drift on a slow cadence (120 s).

**Emission is once per distinct finding.** A detector that re-announces the same drift every two
minutes trains its reader to skip it — the same failure as not having it. But a finding that is
resolved and later *recurs* is reported again, because suppressing forever is the other half of the
same mistake.

## 7. Primitives — the things a plugin can do that a document cannot

This is where the proposal says to spend the design effort, because these are the failures no amount
of discipline fixed.

### 7.1 Turn-bounded messaging (the biggest coordination cost, and it is invisible)

Messages between agent instances arrive only when the **recipient's** turn ends. An agent that asks
a question and keeps working sees nothing until it stops. This was misdiagnosed **twice** — first as
"the bus drops messages", then as "batch-and-lag" — and a workaround was built on the wrong model.
Real consequences: one ruling crossed the implementor **three times**; five rulings arrived after
the work they ruled on.

### 7.1a Why we own the bus — it is what delivers §0.2

The transport decision and *"is the independent implementor still right?"* are **the same question**,
and this is the chain:

> Teammates cannot spawn teammates → so the PO launches every session by hand → so the PO is the
> implementor's lifecycle operator.
>
> **That constraint belongs to the harness's team protocol. If we own the bus, it is ours to
> remove.**

So the bus is not plumbing that messaging happens to need. **It is the mechanism that turns the
independent implementor from a tax the PO pays in interruptions into a free project-level choice.**
That is why it sits high in the build order rather than after the adapters.

**And it gives the harness's team protocol back.** `mcc` previously had to occupy that protocol to
get peer messaging at all — every session launched believing it was the coordinator, with a phantom
coordinator that never runs, because the protocol is designed for a lead that spawns and owns its
teammates and forwards their permission prompts. With messaging moved onto our own bus, **the team
protocol is free for its intended use**: an Architect that wants to run a team can simply be the
coordinator of one. That is a capability we returned rather than removed.

Three further arguments, each independently sufficient:

- **It drops the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` dependency.** Today the entire peer-messaging
  story rides an experimental flag — the same class of fragility that killed bus v1 (channels gated
  to claude.ai auth).
- **It removes an available third ledger.** The harness task board became a de-facto ruling channel
  in the evidence project, violating the two-ledger principle for no capability the tracker lacked.
  Removing the affordance removes a documented process violation, not just noise.
- **The harness inbox does not scale.** A flat JSON array, rewritten whole per send, never pruned:
  O(n) rewrite per send and O(n) parse per poll, at 1 Hz. Measured on this box: 677 unread messages
  accumulated in phantom-coordinator inboxes nobody will ever read.

### 7.1a.1 Who spawns what — and what the bus is actually for

This boundary has been blurred twice in design and is worth stating flatly.

| Spawned by | What | They coordinate via |
|---|---|---|
| **The user** | Independent Claude Code sessions — `arch`, `pdt`, a user-launched `impl` — via `mcc <name>` (`= mcc session resume`) or `mcc term up` for several at once | **This bus** |
| **The Architect** | Subagents (bounded tasks, crisp deliverables) | Their return value, in band |
| **The Architect** | Fan-out workflows | In band |
| **The Architect** | A **CC team**, with arch as coordinator, if the project wants to work that way | The harness's native team protocol |

**`mcc` session control belongs to the user. The Architect does not launch, refresh, or retire a peer
session** — those are independent sessions whose lifecycle the person owns, and an agent reaching for
`mcc <name>` has crossed a boundary rather than removed friction.

**The bus carries traffic between user-spawned sessions only.** `arch ↔ pdt` is the case every
project has. `arch ↔ impl` exists only where the project chose a user-spawned implementor. A project
whose way of working is *arch drives everything with subagents and workflows* has **no bus traffic
at all beyond `arch ↔ pdt`** — and that is a perfectly good shape, not a degraded one.

### 7.1b The architecture, as decided

| Concern | Mechanism |
|---|---|
| **Send** | **MCP tools.** A tool description is guidance delivered *at the point of use* — the same argument as *lessons that can become guards, should.* A CLI's guidance lives in a skill that may not be loaded |
| **Receive — `gating`** | **Monitor.** Plugin-shipped, auto-launching, interrupts mid-turn (measured: landed between two `Write` calls) |
| **Receive — `normal`** | **Stop hook**, injecting via `additionalContext` at the turn boundary |
| **Store** | **SQLite** at `.mcc/bus.db`, WAL. All three read and write it; **no IPC** |
| **Identity** | **Env vars injected by `mcc`** at session launch. The same mechanism carries per-agent tracker credentials (§7.3) |

SQLite is *why* this composes: three processes sharing one store need no socket, no listener
lifecycle, no cleanup story. Measured at 50,000 messages / 114 MB: unread-lookup **2 µs**, send
0.65 ms. At 1 Hz that is 0.00018% of a core.

**Two columns, not one.** `delivered_at` is the honest field — we can know we injected; we can never
know it was read. But for `gating`, add **`acked_at`**: *"a ruling was injected"* and *"the
implementor has confirmed the ruling"* are different facts, and five rulings in the evidence project
arrived after the work they governed. **An architect who can see delivered-but-unacked has a signal
no discipline ever gave them.**

**`--record` in the same call.** The send that carries a ruling writes the durable ledger copy in one
operation, so it cannot be forgotten under momentum. This is the difference between a norm and a
mechanism.

**Open: liveness.** A monitor that silently stops receiving is *"silent in a way indistinguishable
from healthy"* — the exact family this plugin exists to attack, and we would own it. Monitors do not
appear in `TaskList`, so there is no liveness signal for free; the monitor must write its own
heartbeat and something must notice its absence. **This needs an answer before the bus ships.**

---

All three answers are settled:

- **Ruling-to-ledger by default.** A ruling posts to the issue *at ruling time*, and the bus message
  is only the notification. In PLUMB this stops being a norm and becomes the `plumb:rule` skill's
  mechanics: ledger first, notify second, in that order, in one step.
- **A non-blocking variant that says so** — *"proceeding unless countermanded"* as a message **type**
  rather than a convention people remember.
- **Urgency, in place of blocking.** See §9 — the proposal asked for a blocking consult, and the
  answer is that the question dissolves.

### 7.2 Decision-number allocator

Trivially small; prevents a collision class hit twice (once, twice in one evening). Rule inherited:
**numbers are claimed by the log, never from memory** — read the log's tail immediately before
writing; issues say *"resolves as the next D-number"* rather than reserving one. On a collision,
commit order is the tiebreak and both entries carry a note pointing at each other.

The allocator makes this atomic instead of disciplined.

### 7.3 Per-agent tracker identities

All agents on the evidence project authenticate as one tracker identity, so author fields cannot
distinguish them and comments are prefixed by convention — *a convention surviving on discipline, in
an artifact whose whole purpose is surviving context loss.* Wrong shape.

The spike found the mechanism: monitor and hook commands substitute **any** `${ENV_VAR}`, so
`mcc`-injected per-agent credentials reach the adapter without the agent handling them. Adapters
that support multiple identities use them; adapters that can't fall back to the prefix convention
and **say which one is in force.**

---

## 8. Compaction survival — the implementor outlives its own context

Context exhaustion was routine in the evidence project: four losses and three implementor relays.
Under MAMA it cost the Product Owner a chore every time — *"run `impl-end` and start a fresh
implementor"* — when what they actually did was **compact it and say continue**.

**So there is nothing to replace.** Compaction is a *context* event, not a *process* event: the
session is the same session, the monitor is the same process (measured — same pid across a cut), and
every ledger is untouched. Only the conversation is shorter.

### 8.1 The mechanism, measured end to end

**PreCompact (`command` hook) snapshots → SessionStart (`source=compact`) injects.**

- **PreCompact** writes mechanical facts: branch, HEAD, uncommitted files, undelivered bus messages.
  Mechanical *only* — `prompt` and `agent` hooks are refused here (*"Prompt stop hooks are not yet
  supported outside REPL"*), so a hook cannot author judgment. It is explicit about that in the file
  rather than implying more than it knows.
- **PreCompact also steers the summarizer.** Its stdout reaches the summarization sub-call's
  instruction block, not the live session — a lever on *what survives the cut*, which is worth more
  than a pointer appended afterwards because the summary is what the next context is built on. It
  asks for decisions and their reasoning, what failed and why, claims believed but **unverified**,
  and the next concrete step; and for tool transcripts to be compressed, since those re-derive from
  disk. *(Single first-hand observation — additive, so it costs nothing if ignored.)*
- **SessionStart injects on `source=compact` only.** Post-compaction context is the most crowded
  injection point in the system; a stale block there competes with the summary the agent was just
  handed. Verified silent on `startup`, `resume`, `clear`, `fork`.

Two constraints the spike measured: an **aborted** compaction appears to fire the same event with a
degraded payload, so the injector must be idempotent and treat `transcript_path` as optional.

### 8.2 What the injection says, and why that is the product change

> This is ROUTINE and requires nothing from anyone. **Context pressure is not a reason to stop, and
> not a reason to ask the Product Owner to replace you.**

That directly counter-teaches a behaviour the PO could not place the origin of — an implementor
announcing exhaustion and asking for `impl-end` plus a fresh instance. **It learned that from MAMA's
ceremony.** A methodology that made the human a lifecycle operator taught its agents to summon one.

It closes by telling the agent to check whether a claim in the summary was **verified** or merely
**remembered** — a summary flattens exactly the distinction that matters.

### 8.3 The implementor state document is retired

MAMA's implementor was launched per sprint, ended at sprint close, and kept no context. The state
document existed to **approximate what compaction does** for an agent that had none.

Every branch of that justification is now gone:

| Shape | Continuity comes from |
|---|---|
| Independent session that keeps running | **Compaction** |
| Subagent | **Its parent** |
| Session that genuinely ended | **`mcc <name>`** resumes it with its context |

And it had become a **fourth ledger**: rulings duplicated the decisions log, environment traps the
failure catalog, progress the tracker. That is the same triplication that killed the per-arc
implementation log, rebuilt under a new name — which is why it ships in `[artifacts.retired]` with
its reason rather than merely being left out. A project migrating from MAMA has one, and the refusal
is what stops it coming back.

**What outlives a context goes on a ledger**, which survives anything rather than just this cut, and
is readable by an agent that was never here.

## 9. Urgency, not blocking — the consult question dissolves

The proposal's question 1, the one it says to answer first: *can the harness actually block on a
consult?* If not, everything in §7.1 stays convention.

**The question dissolves, and the answer is that it was never the requirement.** Blocking was a
workaround for turn-bounded delivery. The asker had to stop because stopping was *the only moment an
answer could reach it* — a "blocking consult" is what you ask for when your channel can only deliver
at a turn boundary. The spike removed that constraint:

> **Monitor events interrupt mid-turn.** Landed *between two `Write` tool calls*, twice — once
> tool-armed, once plugin-armed. This is the fact the whole design rests on.

Once an answer can reach a working agent, the asker has no reason to stop. So PLUMB does not ship a
blocking primitive.

**And the flag does not disappear — it changes what it controls**, which makes it a better primitive
than blocking ever was:

> From *"does the **sender** block?"* to *"does the **receiver** get interrupted?"*

That is the question worth asking, because **the receiver's cost is the one that is real.**
Interrupting is not strictly better than turn-end delivery — it trades *late* for *disruptive*. A
message that barges in eight steps into a careful edit sequence derails work in a way a queued one
never does. Turn-end delivery's one virtue is that it arrives at a coherent boundary, and that virtue
is worth preserving for everything that does not need to land now.

| Class | Delivery | Sender means |
|---|---|---|
| `gating` | Monitor → **interrupts the recipient mid-turn** | *This changes what you are doing right now.* |
| `normal` | Stop-hook sweep → arrives at the recipient's next turn boundary | *This is for when you surface.* |

Two classes suffice; the spike tested a third and found no use for it (a `normal` message sat
undelivered for two minutes beside a live gating-only monitor, which is the behaviour we want, not a
gap).

### 9.1 The sender declares urgency, per message, always

No inheritance, no thread-carried urgency, no derivation from what a message is replying to.

This was argued the other way first — that a reply on a `gating` thread should default to `gating`,
on the theory that the asker knows they are blocked while the answerer may not. That is wrong three
times over, and the reasons are worth keeping because each one is a trap:

1. **The most important interrupt replies to nothing.** The PO and Architect realising that the
   Implementor is down the wrong path, and redirecting them, is unsolicited by construction. If
   urgency can only arrive by inheritance, that case has no mechanism at all — so sender-declares
   must exist regardless, and inheritance becomes extra machinery over a path that already works.
2. **Threading is a tracking problem that fails silently.** Inheritance requires every reply to
   correctly name what it answers. A mis-attributed reply does not error; it produces *quietly wrong
   urgency*, which is worse than no mechanism. Threads already have a job here — grouping durable
   consult artifacts — and routing delivery through them couples two concerns that fail differently.
3. **It degrades what `gating` means.** The answerer is *better* positioned to judge urgency than
   the asker, because the answerer knows the answer. Impl asking *"A or B?"* and proceeding with A
   needs an interrupt when the ruling is **B** and does not when the ruling is **A**. Inheritance
   fires on both. A class that interrupts for *"yes, carry on"* stops carrying information.

The asker knows they are **waiting**; only the sender knows whether the answer is a **redirect**.
Urgency is a property of the second, so it is declared by the party who holds it.

**What catches a carelessly-marked message** is not a routing rule — inheritance would not have
caught it either, since the answerer could still downgrade. It is the two things that were already
load-bearing:

- **Rulings land on the ledger at ruling time.** The ledger is readable without waiting on a turn
  boundary, by an agent that was not even running when the ruling was made. This was always the real
  fix; the bus is the notification.
- **The unanswered-consult monitor** (§6) surfaces a `gating` question that never got an answer.

What remains is a norm — *mark it `gating` if it changes what the recipient is doing right now* —
and a norm belongs in the project's process document, not in the plugin. That is §2 working.

### 9.2 What survives of "send and STOP"

The norm narrows rather than disappearing, and it is worth stating precisely because the reasoning
changed underneath it:

- **Before:** stop, because continuing means acting on your own judgment while the ruling sits
  undelivered for as long as your turn runs.
- **Now:** the window between asking and being interrupted is bounded by *the answerer's* latency,
  not by your own turn length. Stop only when a wrong step inside that window is expensive or hard
  to reverse — which is a normal engineering judgment, not a workaround for a channel.

**Never infer loss from silence** survives untouched, and **rulings still land on the ledger at
ruling time.** The bus is the notification; the ledger is the record. That was never about latency —
it is about durability, and a durable record is readable by an agent that was not even running when
the ruling was made.

---

## 10. What PLUMB must not do

Each of these is a refusal earned by an attempt that went badly:

- **Not generate the design.** Every attempt to template a ruling produced worse rulings than a read
  plus a person.
- **Not summarise the implementor for the architect.** The architect reading the implementor's
  *actual words* is where half the value is — three times a report's **wording** revealed a problem
  its summary would have lost.
- **Not auto-close issues on commit.** A state means *someone judged this done*.
- **Not enforce the arc shape rigidly.** Two of the best arcs absorbed mid-flight scope cleanly.
  **The ledger absorbs; ceremony doesn't.**

---

## 11. The skill surface

### 11.1 The test for what PLUMB may ship

The proposal listed ten skills. **That list was written by someone describing their own project**,
and an earlier draft of this document imported it uncritically — which is the exact bias §0 warns
about, committed in the section that decides what gets built.

Applying §2.0's test to a *sequence* rather than a sentence: **would this sequence be the same on a
project that had never heard of us?**

| Ships with PLUMB | Why it passes |
|---|---|
| `establish`, `ceremony`, `promote` | **Meta.** About the methodology itself, not about any project's work |
| `design-gate`, `drive`, `handoff`, `catalog` | **The sequence is portable and epistemic.** Anchors-before-surface, read-without-proposal, missing-before-green, why-it-hid — all true anywhere |

| Does NOT ship | Why it fails |
|---|---|
| `arc-plan` | **What an arc *is* is project-defined** — its size, its boundary, what its plan contains. This is precisely the shape of `mama:arch-sprint-start`, *the skill that caused the drift.* Shipping it would rebuild the failure |
| `arc-kickoff` | Content depends entirely on this project's roles, tracker, and plan shape. The only portable part — *a kickoff is a message, not a file* — is a one-line norm |
| `reconcile` | Every step names a project artifact and a project cadence. The portable part is a mechanical diff (issues vs decisions log, closed-without-state-change, phases never delivered) — that is a **check**, not a procedure |
| `rule`, `consult` | Mostly a norm plus a mechanical write. **CLI operations**, not skills |

Those first three become **project-authored skills**, written during `plumb:establish` Step 4, in the
project's own vocabulary. If they say *batch* or *cycle*, their skill says that — not *arc*.

> **The shipped set is a floor.** PLUMB ships what is true anywhere and helps the project author what
> is only true here. A methodology plugin that ships the second kind has confused its evidence for a
> law.

### 11.2 Shipped skills

| Skill | What it sequences | Scar |
|---|---|---|
| `plumb:establish` | **Negotiate this project's way of working.** Reads before it asks; interviews; writes the *minimum*; offers patterns one at a time **after** the interview; authors the project's own skills. Re-runnable | The entire architecture defers to a document. Shipping a mechanism that assumes a good one exists leaves the most important artifact unauthored |
| `plumb:ceremony` | Author a **project procedure** as a project-owned skill. Refuses one that is really a norm, or really a one-off | *A ceremony that lives only in the record of the one time we ran it is indistinguishable from a ceremony, until the second time* |
| `plumb:design-gate` | Impl **brings the read**, arch **rules**. Enforces the asymmetry both ways | Three decisions had their central premise overturned by the read. One found six silently-destructive database behaviours nobody would have quoted correctly from memory |
| `plumb:drive` | Anchors named **before** the surface is opened, measured on the day, parity as an equality between two **live** reads | Every arc that ran one found defects in closed, tested, green work. One found four, two of them P1s. Another's *proof failed on its first attempt* — **reading a plan is order-insensitive where execution is not** |
| `plumb:catalog` | A failure-shape entry: *what happened / why it hid / the tell, as something to TRY / how it differs from its nearest kin.* **Refuses an entry that is only a bug report** | 41 entries; highest-value use was **prospective** — one designed a test before the code existed |
| `plumb:promote` | Review the reflection log for observations that have recurred enough to become norms; move them into the process document | Every good norm in the source project arrived this way. Left to memory, they stay in the log where nobody reads them |

### 11.3 The pattern library — how accumulated wisdom travels without becoming a template

`plumb patterns` ships practices that have been run at scale **with their costs measured**. Each
entry carries five fields, and the last is load-bearing: *practice / the scar / applies when / costs
/ **how you'd know it's wrong for you***.

**A pattern that cannot tell you how to reject it is a template.**

Four rules make it a resource rather than a menu, and the first does most of the work:

1. **Consulted after the interview, never before.** Offered before the PO has spoken it is a
   proposal; offered after, it is a response to something they said.
2. **One at a time, never as a set.** A menu gets taken wholesale, and wholesale adoption *is* the
   failure — nobody could point to when it was chosen.
3. **Adoption recorded with its reason**, in the PO's words. *A practice adopted without a recorded
   reason is indistinguishable from scaffolding within one sprint.*
4. **Declining recorded too** — a declined pattern re-offered every re-run is noise, and noise
   teaches people to stop reading.

The evidence base is deep but **narrow**: one team, one domain, one shape of product. The library
says so, because a PO who knows the sample size weights the advice correctly and one who does not
hears it as settled.

**Five norms go in the plugin's own prompts** — not as skills, as the character the tooling
encourages. These are the one place PLUMB is permitted to state a norm, because they are norms about
*epistemics* rather than about *process*, and they are what the plugin is named for:

1. **"I remember" and "I verified" are different claims and must be said differently.** The most
   expensive corrections all began as a true-but-unlabelled inference restated until it was fact. *A
   true claim without its provenance label is indistinguishable from a measured one by the time it
   reaches a third person.*
2. **A gate's green means nothing until you have seen its red.** A typecheck gate passed a planted
   error for a week.
3. **An invariant that survives a defect is not evidence — it is a constraint the defect happens to
   satisfy.** Ask of any guarantee *which wrong answers also satisfy it*, and test one on purpose.
4. **The reporting surface can be silent in a way indistinguishable from healthy.** Only driving
   crosses that.
5. **Preserve the fact; refuse the flow.** When something is wrong-but-real, keep the record and
   fence its use. *Rewriting the record so the demo reads better is the same instinct that produced
   the bug.*

---

## 12. Build order

The proposal names its own smallest useful version: *if I could have only three things — **the drive
protocol**, **the pre-commit guards**, and **a real blocking consult.** Everything else we carried by
hand at acceptable cost.* Quoted as written; the third is delivered as §9's urgency classes rather
than a blocking primitive, because the blocking was a workaround for a channel we replaced.

**Ordered by §0.2 — what removes the PO from operator duty soonest — not by architectural tidiness.**

1. ✅ **Manifest + artifact-role resolution + retired-artifact refusal** (§3). Everything else
   depends on it, and it is the Sprint 14 guard.
2. ✅ **The guards** (§5). Highest value per line, zero process alignment needed. **Layer 2 — useful
   to a project that adopts nothing else**, which is §0.5 made concrete.
3. ✅ **`drive`, `design-gate`, `catalog`** (§11.2) — the four skills attached to the
   deepest scars. Also layer 2, also standalone.
4. ✅ **`establish` + `ceremony` + the pattern library** (§11.1–11.3) — the process negotiation.
5. **The bus** (§7.1a/b). **Ahead of the adapters, deliberately**: it is what turns the independent
   implementor from a tax the PO pays in interruptions into a free project-level choice, which is
   the product goal in §0.2. MCP send, monitor for `gating`, Stop hook for `normal`, SQLite store,
   `mcc`-injected identity, `acked_at` on gating, `--record` in the same call.
   **Liveness (§7.1b) is answered here, not deferred** — a bus that silently stops receiving is the
   exact failure family this plugin exists to attack, and it would be ours.
6. **Compaction survival** (§8) — the step that actually closes §0.2, and it closes it by deleting
   the chore rather than delegating it. There is nothing to refresh: the implementor compacts and
   continues, and the injection tells it so in as many words. Note what this is *not* — the Architect
   does **not** gain the ability to launch or refresh a peer session (§7.1a.1); `mcc` belongs to the
   user. The friction went away because the operation stopped being necessary.
7. **The ledger interface + adapters** (§4). First tranche: **`markdown`** (no external dependency,
   and it forces the degradation question to be answered honestly), **`github`** (testable here via
   `gh`), and **`nonlinear`** (the reference implementation). Then **`jira`**, then `linear` shipped
   unverified and labelled. Each ships **guidance**, not just code.
8. ✅ **`plumb:promote`** (§11.2) — the last shipped skill, and the mechanism by which a process
   document is *supposed* to grow. It runs in **both** directions: observations graduate in, and
   norms whose premise has died graduate out. The second half is what *claims decay, build the
   expiry in* actually cashes out to.
9. **Monitors** (§6) — the drift detectors.
10. ✅ **MAMA → PLUMB migration** — deliberately last, and worth the wait. It is not a port. An
    in-flight MAMA project has been running a process **it never chose**, so the migration is the
    conversation it never had: re-open the structural assumptions MAMA imposed *before* looking at
    any artifact, because starting from the artifacts lets them set the frame.

    The first draft got this wrong in an instructive way — it asked *"can anyone point to when this
    was chosen?"* of every **artifact** and never of **the process itself**, which is the thing MAMA
    imposed. That is the drift, one level up: carrying a shape forward because it is what was there.
    Two facts make re-opening necessary rather than ceremonial: **the models changed** (MAMA was
    built for a collaborator that needed telling what to do next), and **what happened is evidence of
    what happened, not of what is needed.**

    Re-adopting most of what they had is a good outcome; the difference is that afterwards someone
    can say why. **The measure of a good migration is not how much carried over — it is whether
    anyone can say why each thing is there.**

`arc-plan`, `arc-kickoff` and `reconcile` are **not built** — see §11.1; they are authored
per-project by `establish`. `rule` and `consult` are operations on the bus and the ledger.

MAMA stays shipped and enable-able throughout; PLUMB is a separate plugin, not a replacement in
place.

---

## 13. Open questions

1. ~~**Can the harness block on a consult?**~~ **Closed** (§9) — the question dissolved. Blocking was
   a workaround for turn-bounded delivery; monitor-class messages interrupt mid-turn, so urgency on
   the message covers the space and a blocking primitive is not built.
2. **Are per-agent worktrees compatible with a shared dev environment?** (§5.1) — opt-in until
   answered, with a compatibility checklist.
3. **How much should the design-partner boundary be encoded?** The arch ↔ design-partner split works
   because the *routing* is disciplined (product calls one way, platform calls the other). It may be
   codifiable as a consult type; it may be exactly the judgment that should stay human. **Current
   lean: a consult *type*, which routes and records, and never decides.**
4. **Does the PreCompact→summarizer lever work?** (§8) — a sentinel test grades it, and it also
   measures how much steering we get.

---

## 14. Closing

The honest summary of sixteen arcs, from the people who ran them:

> The process works because **two agents with different jobs keep checking each other against
> something neither controls** — a ledger, a measurement, a running product.

MAMA gave the two-agent shape and the arc rhythm. It was right about the content and wrong to make
it a constant. PLUMB keeps the evidence discipline, makes the shape a choice, and spends its
mechanism budget on the one thing no discipline fixed: **getting the Product Owner out of the
operator's chair without taking them out of the decisions.**

**Claims decay. Build the expiry in.**
