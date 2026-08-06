# PLUMB — Design Document

**Status:** Design — pinning the architecture before any skill is written
**Date:** 2026-08-05
**Authors:** Bryon (Product Owner) + Claude (design partner)
**Sources:** a field proposal from the Architect of a sixteen-arc effort (§0 below), that project's
living way-of-working document, and a throwaway spike that measured what the plugin surface can
actually do (`tmp/spike-plumb/FINDINGS.md`).

PLUMB is MAMA's successor. It keeps MAMA's bones — architect and implementor as separate
instances, an arc rhythm between them — and replaces MAMA's ceremony with **mechanical guards, a
pluggable execution ledger, and a process that lives in the project rather than in the plugin.**

---

## 0. Where this comes from

The proposal PLUMB is built on was not written from theory. It came from a project that ran
**sixteen arcs over roughly six months**: four context losses, three implementor relays, ~1,150
tests, 48 decisions, 41 catalogued failure shapes. Every recommendation in it is traced to
something that actually happened, usually more than once.

That matters for what PLUMB is allowed to contain. The proposal's own framing, which this document
adopts as its acceptance test:

> **This plugin's job is not to help agents work. It is to make specific, repeatedly-observed
> failures impossible or loud.** Every skill that is merely "a helpful template" should be cut. The
> ones that survive are the ones attached to a scar.

The name is a double meaning, both halves load-bearing. A **plumb line** is a reference a thing is
trued against — it builds nothing, it tells you whether what you built is straight. And *to plumb*
is to investigate to the bottom. One idea in two directions: **make claims that survive, and check
them against something that cannot flatter you.**

---

## 1. The governing constraint

The single most important instruction in the proposal is §6:

> **Make PLUMB describe the process rather than embed it.**

This is not a style preference. It is a bug report against MAMA, with a date. At Sprint 14 that
project's Architect invoked `mama:arch-sprint-start` for its *substance* and inherited its
*template* with it — silently reintroducing three practices the project had killed eleven arcs
earlier: an `implementation_log.md` per arc, the kickoff as a document section, and `/impl-end`
command ceremony. **Nobody decided any of it.** The scaffolding rode in attached to a tool, and the
tell is that no one could point to when it was chosen.

The project already had a name for this shape at other grains — *a pin outliving its reason*, *a
workaround outliving its cause*. Sprint 14 found it at process grain: **a process we evolved away
from can return through a tool that still encodes it.**

So PLUMB must be designed so it cannot do that to *its* successor. Everything in §2 follows from
that.

---

## 2. The core architectural idea: norms live in the project, procedures live in the plugin

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

| | Norms | Procedures |
|---|---|---|
| What | Standing behavior, always on | An ordered sequence, run rarely |
| Read | By habit, continuously | At the moment of need, by name |
| Lives in | **The project's own process document** (Ledger 2, versioned with the code) | **A PLUMB skill** (invoked by name, at the moment of need) |
| Example | *evidence outranks argument*; *send-and-stop when the answer changes your next move* | *how to run a drive*; *how to close an arc* |

A skill is, structurally, already the procedures genre: named, invoked deliberately, consulted only
when you're about to do the thing. That's the genre match, and it resolves the open question
without inventing a fourth document surface.

The rule that falls out, and it is the whole defence against Sprint 14:

> **A PLUMB skill carries sequence. It does not carry norms. When it needs a judgment, it reads the
> project's process document and defers.**

A skill with no norms in it has no norms to smuggle. This is checkable by review, which is the
point.

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
state           = "docs/sprints/sprint_{arc}/state.md"

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

### 4.1 The ledger interface

PLUMB defines a narrow interface and ships adapters. The operations are derived from what sixteen
arcs actually used, not from what trackers offer:

| Operation | Why it's in the interface |
|---|---|
| `arc_open(name)` → arc ref | One project/milestone per arc |
| `issue_create(arc, title, body)` | Planned scope, filed at planning time |
| `issue_comment(id, body)` | **The play-by-play, and the ruling-to-ledger primitive** |
| `issue_state(id, state)` | States move as work moves |
| `issue_get(id)` / `issue_list(arc, filter)` | Reconciliation and drift detection |
| `search(query)` | *Search their tracker before filing* — the cross-team norm |

State vocabulary is normalized to `triage → backlog → todo → in_progress → in_review → done`;
adapters map to native states and **declare what they cannot express** rather than approximating
silently.

### 4.2 Adapters shipped

| Adapter | Mechanism | Status |
|---|---|---|
| `nonlinear` | MCP, agent-native | Primary — this is what the evidence base ran on |
| `github` | `gh` CLI | Full support; issues + milestones (arc = milestone) |
| `jira` | REST | Full support |
| `linear` | GraphQL | **Best-effort, marked as such** — no account available to test against. Shipped unverified, and the adapter says so at load |
| `markdown` | Files in the repo | The honest degradation, see below |

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

## 6. Monitors — drift detectors

The spike confirmed plugin-shipped monitors auto-launch, run at ~1 Hz in the session's working
directory, survive compaction as the same process, and **interrupt a turn mid-flight**. Every
detector below corresponds to a drift that actually happened.

| Monitor | Detects | Incident |
|---|---|---|
| **Ledger-state drift** | Issues whose recorded state disagrees with observable activity | ~16 issues sat in Triage while their work shipped; the PO caught it, not the agents |
| **Unanswered consult** | A `gating` question with no answer after N turns | The turn-bounded-delivery failure mode, made visible |
| **Plan-vs-delivery** | Committed phases with no closed issue as an arc approaches close | One arc's committed scope went undelivered and was nearly re-labelled silently |
| **Decision-number collision** | Two entries claiming one number | 2× — once twice in one evening |
| **Stale pin** | A pin/override/workaround whose stated reason no longer holds | A dependency override outlived its cause and its failure mode **inverted**, from "fixes a 404" to "silently installs a version skew" |

The stale-pin monitor implies a convention worth stating: **a pin carries its reason inline, so its
expiry is detectable.**

Monitors are rate-limited by the harness (too many events → auto-stopped), so all of these batch
and debounce. They are also **interactive-CLI only** — headless sessions get nothing, which the
docs must say plainly.

---

## 7. Primitives — the things a plugin can do that a document cannot

This is where the proposal says to spend the design effort, because these are the failures no amount
of discipline fixed.

### 7.1 Turn-bounded messaging (the biggest coordination cost, and it is invisible)

Messages between agent instances arrive only when the **recipient's** turn ends. An agent that asks
a question and keeps working sees nothing until it stops. This was misdiagnosed **twice** — first as
"the bus drops messages", then as "batch-and-lag" — and a workaround was built on the wrong model.
Real consequences: one ruling crossed the implementor **three times**; five rulings arrived after
the work they ruled on.

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

## 8. Handoff at context exhaustion — proven mechanics

Context loss is routine, not exceptional: four losses and three implementor relays in the evidence
base. The spike established the full mechanism, end to end:

**PreCompact (`command` hook) snapshots → SessionStart (`source=compact`) injects the pointer.**

Both halves observed in one run. `transcript_path` arrives on *both* sides of the cut, so either
hook can read pre-compaction history. Three constraints the spike measured:

- **`prompt` and `agent` PreCompact hooks are refused, not absent** — *"Prompt stop hooks are not
  yet supported outside REPL"*. Explicit and visible, so declaring them breaks nothing, and the
  blocker is temporal. Build the authoring step behind a seam so a `prompt` hook can take it over
  later; don't put it on the critical path.
- **Gate SessionStart output on `source`.** Post-compaction context is the most crowded injection
  point in the system — three plugins' blocks landed together in the spike, one of them stale and
  actively pulling against the summary. On `compact`: the handoff pointer and *nothing else*.
- **Make the injector idempotent and treat `transcript_path` as optional** — an aborted compaction
  appears to fire the same event with a degraded payload.

**Unclaimed lever, worth a graded test:** PreCompact's `additionalContext` is not ignored — it
reaches the **compaction summarizer**, in its "Additional Instructions" block. That is a lever on
*what survives the cut*, which for an implementor running to exhaustion is worth more than appending
a pointer afterwards: the summary is what the next 200k tokens are built on. (Single first-hand
observation; summarizer prompts aren't persisted, so it needs a sentinel test to grade.)

### 8.1 The shape of the state doc

Non-negotiable, and it is what made three relays cost zero rework:

- **Leads with what is MISSING**, not the green numbers — *a suite that's green is exactly what
  would hide the gap.*
- The queue **in order**, and for each item **what the successor must not rediscover** — rulings
  already made, options already closed **by name**, and the reason each is closed.
- **Environment traps carry the day they cost.** A successor who reads *"a skip is not a pass"*
  learns a rule; one who reads that 28 tests went dark while the suite printed `Failed: 0` learns to
  distrust a green.
- **Committed-but-inert code is labelled as such, in those words** — a committed file implies more
  than it should.
- The successor's first act is an **ACK with a read-back**; their first *working* act is
  **verifying the inherited claim** rather than building on it. Two fresh implementors materially
  improved the design they inherited by doing exactly this.

---

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
blocking primitive. It ships **urgency as a property of the message, set by the sender**:

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

Thin by construction, per §2. Each reads the process document for judgment and the manifest for
paths.

| Skill | What it sequences | Scar |
|---|---|---|
| `plumb:arc-plan` | Tracker arc + issues + the plan doc. **Out-of-scope is a required field** | Arcs that used *"optional"* and *"if time permits"* had those items exploited as skippable and accumulated as debt. **Every phase in a plan is committed scope; if you aren't ready to commit, leave it out** |
| `plumb:arc-kickoff` | Composes and **sends** the kickoff. **Must not write a file** | The kickoff is a *message* — writing it to a file records a thing whose value was that it was said at a moment |
| `plumb:design-gate` | Impl **brings the read**, arch **rules**. Enforces the asymmetry both ways | *The highest-value single addition; MAMA had no equivalent.* D-31, D-43, D-45 all had their central premise overturned by the read. D-45's found six silently-destructive database behaviours nobody would have quoted correctly from memory |
| `plumb:drive` | The closing drive as protocol: anchors named **before** the surface is opened, measured on the day, parity as an equality between two **live** reads | Every arc that ran one found defects in closed, tested, green work. Sprint 14's found four, two of them P1s. Sprint 16's *proof failed on its first attempt* — **reading a plan is order-insensitive where execution is not** |
| `plumb:rule` | Ledger first, notify second, atomically | Five rulings arrived after the work they ruled on |
| `plumb:reconcile` | **Checks rather than prompts**: diffs issues against the decisions log, flags decisions referenced but unlogged, issues closed without a state change, plan phases never delivered | The sacred step. One arc's committed scope went undelivered and was nearly re-labelled silently |
| `plumb:handoff` | The state doc in the shape of §8.1 | Three relays, zero rework — the arc *without* a state doc cost its successor a morning |
| `plumb:catalog` | A failure-shape entry: *what happened / why it hid / the tell, phrased as something to try / how it differs from its nearest kin.* **Refuses an entry that is only a bug report** | 41 entries; highest-value use was **prospective** — an entry used to design a test before the code existed |
| `plumb:consult` | A `gating` question to the design partner or architect. Records question **and answer** on the ledger, not only in the message | §9 |
| `plumb:promote` | Reviews the reflection log for observations that have recurred enough to become norms, and moves them into the process document | Every good norm in the evidence project's process doc arrived this way. Left to memory, they stay in the log where nobody reads them |

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

The proposal names the smallest useful version: *if I could have only three things — **the drive
protocol**, **the pre-commit guards**, and **a real blocking consult.** Everything else we carried by
hand at acceptable cost.*

Quoted as written; the third item is delivered as §9's urgency classes rather than as a blocking
primitive, because the blocking was a workaround for a channel we replaced. The *need* behind it —
an answer that reaches a working agent — is met.

1. **Manifest + artifact-role resolution + retired-artifact refusal** (§3). Everything else depends
   on it, and it is the Sprint 14 guard.
2. **The guards** (§5). Highest value per line, zero process alignment needed, independently useful
   to a project that adopts nothing else.
3. **`plumb:drive`, `plumb:design-gate`, `plumb:handoff`, `plumb:catalog`** (§11) — the four skills
   attached to the deepest scars.
4. **The ledger interface + `github` and `markdown` adapters** (§4), then `nonlinear`, `jira`,
   `linear`.
5. **The bus: two delivery classes, urgency declared per message by the sender** (§9), then
   `plumb:consult` and `plumb:rule` on top of it.
6. **Monitors** (§6).
7. **MAMA → PLUMB migration** — deliberately last. A migration written before PLUMB exists would be
   a migration to a guess.

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

MAMA gave the two-agent shape and the arc rhythm, and those were the right bones. What PLUMB adds is
**evidence discipline**, and the part discipline keeps failing at: the mechanical guards, the honest
channels, and a structure that does not quietly reinstate itself after we have moved on.

**Claims decay. Build the expiry in.**
