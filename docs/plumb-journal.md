# PLUMB — design journal

**Status:** Pre-implementation thinking. Written from conversation only.
**Author:** Claude (Opus 5), as co-owner of methodical-cc, at the PO's request.

## What this document is, and why it exists

This is a deliberate brain dump of my current thinking about PLUMB — our next
plugin, the evolution of MAMA — written **before reading any other artifact**:
not the Plank proposal, not the Plank way-of-working doc, not any code we may
have already written.

It exists because of a specific failure we already had once. We ran the transport
spike, it succeeded, and we went straight into building. In doing so we lost the
product-shaped thinking that preceded it and **built what Plank proposed rather
than what we designed.** Plank's proposal is excellent and it is evidence, not
specification. It is written from inside one project's scars. Our job is the
generalization, and that job has its own conclusions — several of which
contradict or extend Plank's.

If a future session reads only this document, it should be able to reconstruct
*our* design intent, and specifically be able to tell the difference between
"this is what Plank asked for" and "this is what we decided."

---

## 1. Where this comes from — the evidence, and it is not just Plank

The PO has run this methodology stack across many projects. Three data points
matter, and **all three are load-bearing**. Plank's proposal only has access to
the third.

| Project shape | Process used | Outcome |
|---|---|---|
| nonlinear, augrid (clone-shaped, self-defining scope, low HITL) | **None.** Fable-5 drove itself, used fan-out workflows and subagents. No persistent implementor. | Excellent |
| Plank (platform build, high HITL, consequential design) | **Self-authored.** The arch was told "figure out how you'd like to work" and invented a rich evidence-discipline process over 16 arcs. | Excellent |
| Projects on MAMA-as-written | **Imposed, uniform, up front.** | Increasing friction as models evolved (4.7 → 4.8 → 5) |

### The conclusion I draw from this

The common factor in the two successes is **not the amount of process**. In one
case it was near-zero; in the other it was elaborate. The common factor is that
**the agent chose it.**

So MAMA's failure was not its content — most of MAMA's content is good and much
of it survives. MAMA's failure was **being a constant where the correct answer is
a variable.** It shipped one process and imposed it regardless of what the work
needed, at a time when models had become fully capable of selecting and running
their own.

This is the single most important framing in this document. Everything else
follows from it.

### What that means for what we build

PLUMB is not a better process. **PLUMB is a host for a process the arch and the
PO author together, and evolve as the project evolves.**

A corollary the PO stated explicitly and I want preserved: *ways of working
change over the course of a project.* Plumb must not merely support an initial
choice of process — it must make **evolving** the process a first-class,
supported, low-friction act. A project that has outgrown its own way of working
and can't cheaply say so will drift back into ceremony.

---

## 2. The pivot, in one line

> **MAMA's skills answer "what do I do now?" PLUMB's skills answer "is what I
> just did true?"**

Orchestration → verification.

This is why MAMA started getting in the way. Opus-5 and Fable-5 class models do
not need to be told what to do next; they are excellent at driving, decomposing,
fanning out, and finding their way. What they still need — what no model
generation removes the need for — is **something that cannot flatter them.**

That is the whole reason the name works, and it is the test I would apply to
every candidate feature: *does this tell the agent what to do, or does it tell
the agent when it is fooling itself?* Prefer the second. Cut most of the first.

---

## 3. The name

**PLUMB.** A plumb line is the reference a thing is trued against — it does not
build anything, it tells you whether what you built is straight. And *to plumb*
is to investigate to the bottom.

The Plank architect was given naming rights and proposed it with that rationale.
The PO likes it, I like it, it is settled. It is short, typeable, and a noun and
a verb at once.

---

## 4. The shape: three layers, deliberately separable

This is our design, not Plank's. Plank proposed a flat surface of skills, hooks,
monitors, and primitives. I think the separation into layers is what makes it
generalize, because **each layer is independently useful** and a project can
adopt one without the others.

### Layer 1 — the process host

The project's own **way-of-working document** is the single source of truth for
how that project works. Plumb does not contain the process; it hosts it.

- A **bootstrap** that helps the arch and PO author their way of working at
  project start — seeded from a **pattern library** carrying MAMA's and Plank's
  accumulated wisdom as *options and recipes*, never as defaults. The bootstrap
  produces **both** halves of the wow: the document *and* its project-local
  ceremony skills, together (see §5.6–5.7).
- Skills **read** the document and act on it rather than restating process in
  their own prompt text.
- **When plumb's guidance and the project's document disagree, the document
  wins, loudly** — the skill says so rather than quietly proceeding.
- **Version the process, not just the plugin.** A project can say "we are on
  process v3" and tooling honours it.
- **Deprecated ceremony fails rather than fades.** If a project's document says
  an artifact is dead, a skill that would create one refuses and names why.
- Support for the process **evolving** — promoting observations into norms,
  retiring norms that stopped earning their keep.

The failure this defends against is real and documented: a legacy skill invoked
for its substance dragged its template along and silently reintroduced ceremony
the project had already killed. Nobody decided; the scaffolding rode in attached
to a tool. **An architect cannot be trusted to remember their own document under
momentum**, which is why this has to be mechanical.

### Layer 2 — the evidence layer

The norms and the small set of scar-attached skills. **Usable standalone, by any
project, with or without Layer 1.**

The test of whether we generalized correctly: *would this have helped nonlinear
and augrid?* Those projects had no methodology at all, and a drive protocol, "a
gate's green means nothing until you have seen its red," and mechanical guards
would still have paid. If a proposed Layer 2 item would not have helped them, it
probably belongs in the pattern library, not the plugin.

### Layer 3 — mechanism

The things a plugin can do that a document cannot: the bus, mechanical guards,
per-agent identity, worktrees, allocators.

**A large share of this is `mcc` work, not plugin work.** Worth stating plainly
because it changes how we build: identity injection, session lifecycle, worktree
management, guard installation all live in the tooling arm we already own.

---

## 5. Design commitments I consider settled

These came out of our discussion and I want them held.

### 5.1 MAMA stays. PLUMB is new.

We did this once already with mam → mama. `mam` is arguably a fossil and harms
nobody. Plugin enablement is per-project and the PO owns that choice. The PO will
disable mama user-wide once plumb ships and re-enable it only on the specific
projects still running it.

**We owe a migration entry point** for an existing mama project to transition to
plumb — but we should design it **after** building plumb, so we actually
understand what the migration means rather than guessing.

### 5.2 No bias for or against the offboard implementor

This is the sharpest correction we made to Plank's proposal.

Plank asserts the separate-instance implementor is load-bearing, "not a
preference," justified on permission routing and context hygiene. But Plank has
never run the nonlinear/augrid model, which used no persistent implementor at all
and thrived.

The PO's diagnosis is sharper than Plank's and I want it recorded: **the cost of
the offboard implementor is not the implementor. It is that the PO became its
lifecycle operator** — launch it, run impl-end, start a fresh one — when what
actually happens is the PO just compacts it and tells arch to continue. That
chore is the single biggest impediment to a fully-designed project driving itself
to completion.

So: **plumb takes no position.** Subagent implementor, offboard implementor,
fan-out workflows — all first-class, chosen by the project, changeable mid-flight.
Plank's own delegation policy is in fact the correct generalization (whole arcs to
a persistent implementor; bounded tasks to subagents; fan-out work to workflows);
the proposal underweights it only because Plank sits at one end of the spectrum.

What plumb *should* do is make each mode cheap. The offboard implementor becomes
a free choice the moment the PO stops being its operator.

### 5.3 Recipes and options, never defaults

A fresh project gets the benefit of our collected methodological wisdom
**presented as options** to kickstart their way of working. Not imposed, not
pre-selected. This is the mechanism by which we avoid re-committing MAMA's error
while still not throwing away what MAMA and Plank learned.

### 5.4 The tracker is pluggable

The two-ledger idea generalizes; its backend does not. The principle:

> If it is *why / what / how-it-should-be*, it is a document.
> If it is *who / when / status / what-happened*, it is a ledger item.

Ship known options with plumb-specific guidance: **nonlinear** (the PO's own,
MIT-licensed, heavily used), **GitHub Issues**, **Jira**, possibly **Linear**
(untested — no account). The tracker MCPs are generally well-guiding on their
own; our contribution is *plumb-with-this-one*, not a re-explanation of the tool.

And a hard-won negative to encode: **the harness task board is not Ledger 1.** A
project reached for it as a de-facto third ledger and it violated the two-ledger
principle for no capability the real tracker lacked.

### 5.5 Commands are deprecated — everything ships as skills

Anthropic prefers skills over commands; skills remain user-invocable. What
previous plugins wrote as commands, plumb writes as skills.

### 5.6 The way of working has an executable surface: project-local skills

Added after the initial draft of this journal; it completes the thought §6's
norms-vs-procedures answer started, and it is load-bearing enough to be a
commitment.

MAMA's commands were genuinely valuable for two reasons that survive MAMA:
they **anchored** the methodology (a ceremony you can invoke is a ceremony that
actually gets run the same way each time), and they gave the PO **shorthand** —
a way to point at a step and say "do this now." What does not survive is their
*authorship*. MAMA shipped process-shaped skills from the plugin because MAMA
owned the methodology. Plumb does not own the methodology — the project does —
**so the project owns the skills.**

The way of working therefore materializes as **two artifacts, both in the
repo, both project-authored, evolving in the same commits**:

- **The document** — norms. Always-on, read at orientation.
- **Project-local skills** — procedures and ceremonies. Ordered, invoked at the
  moment of need, by the agent *or the PO* (skills are user-invocable — the PO
  keeps their shorthand), and readable by every teammate (the wow is not just
  documented but *operable*, identically, by every participant — shared
  vocabulary).

The layer boundary restated in skill terms, using the pivot line from §2:

- Skills that answer **"what do I do now?"** are process-shaped →
  **project-local, project-authored.** Arc planning, kickoff,
  reconcile-as-this-project-does-it, whatever the wow calls for.
- Skills that answer **"is what I just did true?"** are verification-shaped →
  **plumb ships them** (the evidence layer). They are universal — they pass the
  would-it-have-helped-nonlinear-and-augrid test.

This makes the Sprint-14 drift incident **impossible by construction rather
than guarded against**: a project-local skill cannot smuggle in a foreign
process because it has no foreign origin. It is versioned with the project,
written by the agent that owns the wow, touched by the same reconciliation that
touches the doc. That is the strongest form of "describe the process rather
than embed it" — the plugin embeds *nothing*; the project embeds *its own*.

**The failure mode this creates, named now:** project-local skills can rot
against their own document — the same shape as a pin outliving its reason, one
level down. The wow evolves to v3 and a skill still encodes v2. This relocates
the Sprint-14 hazard from plugin-scale to project-scale (much better: the
project can fix it and reconciliation can see it), but it is real. Therefore:
**doc and skills are one artifact** — a change to the way of working lands in
both, same commit — and **log-then-promote gains two promotion targets**:
observations promote into the doc when they are norms, and into a skill when
they are procedures.

### 5.7 Onboarding generates both — and ships exemplars, never starters

Two decisions, the second reached by deliberately role-playing the onboarding
agent's seat.

**Both, together.** When the agent and PO select recipes during onboarding,
plumb helps author the doc section *and* the corresponding ceremony skill in
the same pass — so the doc-and-skills-move-together habit is set from the first
commit, and the skill surface is never empty (an empty surface invites drifting
back to freeform).

**Exemplars and properties, never pre-written skill text.** The honest answer
from the agent's seat: skill *syntax* costs a capable model nothing, so a
starter file solves a problem the agent does not have — and creates one it
cannot easily see itself having: **anchoring**. Handed a pre-written
`arc-plan`, the agent's "adaptation" preserves its bones — phase structure,
assumptions, ceremony shape — even where the project genuinely differs, because
editing existing prose invites preserving it. The result *reads* adapted and
*is* inherited. A starter file is a template with a to-do sticker on it, and
the sticker makes it more dangerous: the adapted result looks chosen.
Adaptation is not ownership transfer; **the first draft coming from the agent
is the ownership mechanism.**

What the pattern library ships instead:

1. **Real exemplars, clearly marked as one project's answer** — e.g. Plank's
   actual `reconcile` skill, framed as *"what one mature project's ceremony
   skill looks like; calibrate against it, do not copy it."* Sets the quality
   bar and the grain (how thin, how much doc-pointing), not the content. The
   framing as somebody else's real artifact is itself the guard — it cannot be
   mistaken for a default.
2. **The property checklist — judgment, not text.** What makes a ceremony
   skill good and what makes it rot: points at the doc rather than restating
   it; names the scar or need that justifies it; meaningfully invocable by PO
   and teammates alike; fails loudly when the doc has moved past it.
3. **Precise mechanical conventions** — naming, file placement, frontmatter
   shape. Frame, not voice.

The rule in one line: **specify the frame, show real exemplars, never draft
the project's own words.** Where content is universal, plumb ships the skill
itself; where content is project-specific, plumb ships judgment and exemplars.

*(Sourcing decision, settled: no real project had authored ceremony skills yet,
and asking one to produce them on demand would manufacture the friction plumb
exists to remove. So v1's exemplars are written from an **illustrative**
project — "Kiln", fictional, honestly labelled as such in the exemplars' own
README — with a domain and vocabulary deliberately far from any real project's
so nothing reads as a default. They set the quality bar until real projects
contribute real ones, which replace them.)*

### 5.8 What plumb must not do

- **Not generate the design.** Templated rulings are worse than a read plus a
  person.
- **Not summarise for the architect.** The architect reading the implementor's
  actual words is where much of the value is; a report's *wording* has revealed
  problems its summary would have lost.
- **Not auto-close ledger items on commit.** A state change means someone judged
  it done.
- **Not enforce an arc shape rigidly.** The ledger absorbs mid-flight scope;
  ceremony does not.
- **Not be a pile of helpful templates.** Every skill should be attached to a
  scar. If it is merely nice to have, cut it.

---

## 6. The evidence layer — content I consider validated

These are Plank's, and I endorse them as genuinely universal. They are also the
highest-value / lowest-cost content in the whole proposal, and the part MAMA had
no equivalent of.

**The five norms**, to live in plumb's own prompts:

1. **"I remember" and "I verified" are different claims and must be said
   differently.** A true claim without its provenance label is indistinguishable
   from a measured one by the time it reaches a third person.
2. **A gate's green means nothing until you have seen its red.**
3. **An invariant that survives a defect is not evidence** — it is a constraint
   the defect happens to satisfy. Ask which wrong answers also satisfy it.
4. **The reporting surface can be silent in a way indistinguishable from
   healthy.** Only driving crosses that.
5. **Preserve the fact; refuse the flow.** Keep the record and fence its use;
   never delete it to make the story cleaner.

**The practices worth carrying:**

- **The design gate / read-before-rule.** The asymmetry is the point: the
  implementor brings the *read* (measures what the code and the world actually
  do, explicitly does not propose a design); the architect *rules*. A read
  containing a proposal is a failure mode; so is a ruling written without a read.
- **The drive.** An arc closes with someone *using* the thing against real data
  and writing a record: what the suites said, what the drive found, what it cost
  to see. Anchors named before the surface is opened; anchors measured on the day;
  parity asserted between two live reads, never against a remembered number; and
  when the product turns out righter than the script, the script changes and the
  record says so in that order.
- **Handoff at context exhaustion.** Leads with what is *missing*, not the green
  numbers. Queue in order. For each item, what the successor must not
  rediscover, with closed options named **by name**. Environment traps carry the
  day each cost. Committed-but-inert code labelled as such.
  *(Qualified during the rewrite: the standing per-session state document is
  retired — it existed to approximate compaction for an agent that had none,
  and durable sessions + the PreCompact snapshot killed the premise; kept as a
  document it becomes a fourth ledger. What survives is the **relay** case — a
  genuine handover to a different agent — and the shape above lives in the
  pattern library as `relay-handoff`, applied to the handoff message and the
  ledgers, not to a standing file.)*
- **The failure-shape catalog.** Entries ordered by *why they hid*, not by what
  broke. An entry earns its place by being portable — it tells you what to *try*.
  Its highest use is prospective.
- **Log-then-promote.** Observations accumulate as instances and graduate into
  norms once they recur. Note the lineage: this is a better-formed version of
  what we were reaching for with mama 3.6.0's methodology-holds forcing function.
  Plank invented it independently and their version is stronger.
- **Autonomy calibration** — three bins: *act then flag* (reversible, in your
  lane), *bring the fork* (anything moving a boundary), *route to the owner*. The
  test: **"if this call is wrong, who pays, and how much?"** This directly answers
  the PO's stated core concern — when input is needed versus when the corpus
  speaks.
- **Guards over documentation.** The strongest single finding: *recorded
  procedural lessons do not self-apply.* Structural shapes self-apply; procedural
  ones fire again and again, sometimes against the very person who wrote them
  down. **Lessons that can become guards, should.** This is the argument for
  hooks, and it is why hooks are not a nice-to-have.

**Reconciliation stays sacred.** It survives from MAMA unchanged and it is the
only real defence against documentation drift.

### Norms vs procedures — my answer to Plank's open question

Plank asked whether norms and procedures are different genres, having noticed
that "a document read for standing behaviors is exactly where a rarely-run
sequence goes unread."

**They are different genres, and the harness already gives us both surfaces:**

- **Norms** → the way-of-working document. Always on, read at orientation.
- **Procedures / ceremonies** → **skills.** Ordered, consulted at the moment of
  need, invoked by name.

So the answer to "where does a rarely-run ceremony live" is not a fourth document
genre — it is a **project-local skill**, and plumb should help a project author
its own. This uses an affordance that exists today rather than inventing a
surface. (This answer later generalized into a full design commitment — the
entire MAMA-style command surface becomes project-authored skills; see §5.6–5.7.)

---

## 7. The bus rebuild

This is the most concrete part and the part with the most of our own thinking in
it. Plank asked for "a genuinely blocking consult." We concluded something
different and better.

### 7.1 Why we leave Claude Code's TEAMS protocol

- **Turn-bounded delivery.** A message lands only when the *recipient's* turn
  ends. An agent that asks and keeps working sees nothing until it stops. This is
  the single largest invisible coordination cost, and it was misdiagnosed twice on
  a real project (first as "the bus drops messages," then as "batch-and-lag").
- **`SendMessage`'s shape invites overflow.** A subject-ish field leads models to
  pack body content into it and blow the character limit repeatedly. Auditing
  Claude's own inboxes shows why: the richer protocol is **JSON-stuffed into a
  `text` string field**. Structure-packed-into-a-string is baked into the format.
- **It is out of our control** and gated on
  `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`. Our entire peer-messaging story
  currently rides an experimental flag — the same class of fragility that killed
  bus v1 (channels gated to claude.ai auth).
- **The phantom coordinator is a vestige of a hack.** TEAMS is designed for a
  lead that spawns and owns teammates, and forwards permission requests to the
  lead — which works against how the PO actually runs sessions. We made every
  session think it is the coordinator under a different name. We do not need to
  carry that.
- **It imposes a shared task list.** Dropping TEAMS makes tasks agent-local
  again. This is not merely noise reduction: the shared board is an *available
  third ledger*, and an architect under pressure will reach for it. Removing the
  affordance removes a documented process violation.

**We are solving for CHAT, not control.** No permissions, no lead, no task
assignment, no lifecycle. That subtraction is most of the design.

### 7.2 Transport: plain SQLite, and the evidence for it

Audit of `~/.claude/teams` on this machine: a flat JSON array per inbox,
rewritten whole on every send, never pruned. 102 messages / 112 KB all still
present with `read=true`; the phantom coordinator holding **333 unread messages
that will never be read**, 677 across two projects. That is O(n) rewrite per send
and O(n) parse per poll at 1 Hz, with no retention.

Benchmarked our alternative — 50,000 messages, 114 MB, indexed:

```
monitor poll query:   2 µs   → at 1 Hz = 0.00018% of one core
                               at 10 Hz = 0.0018% of one core
send (insert+commit): 0.65 ms
```

**Polling is free.** SQLite, stdlib only, WAL mode, one DB per project.

### 7.3 Why not honker / pub-sub

[honker](https://honker.dev/) is real and good — WAL-watching, ~1 ms
cross-process NOTIFY/LISTEN for SQLite, durable streams, Python bindings. We
declined it, for reasons I want preserved so nobody relitigates it casually:

1. **The cost it removes does not exist.** 2 µs per poll. We would add a compiled
   native dependency to save two ten-thousandths of a percent of a core.
2. **Edge-triggered versus level-triggered — the real argument.** A notification
   is fire-and-forget: if the monitor is restarting, crashed, or racing when it
   fires, that message is missed permanently. A poll re-derives state from the
   table every tick and is therefore **self-healing**. We independently concluded
   we need the level-triggered path anyway (the Stop hook sweeping unread, as a
   backstop for a monitor that failed to deliver). If the level-triggered path is
   required for correctness, the edge-triggered one is pure addition.
3. **Distribution risk.** A native extension means per-platform binaries across
   Windows / macOS / Linux × x64 / arm64, and `enable_load_extension` is disabled
   in several stock Python builds (notably macOS system Python). Our suite is
   pure-Python/shell with no build step, and that is a stated virtue.
4. **It does not solve the repeat-spam problem** — that is the `delivered_at`
   column, identically under either transport.

### 7.4 MCP, not CLI — and why I changed my mind

My first instinct was a CLI shipped with `mcc`. The PO argued for MCP and the
argument is better. Recording both sides so this does not get re-fought:

- My case for CLI was: MCP schemas consume context; a CLI composes into hooks and
  scripts; we already own `mcc`; and *"a subject field invites the model to
  over-pack it."*
- **That last point is an indictment of `SendMessage`'s schema, not of MCP as a
  mechanism.** If we own the contract, the objection evaporates. I generalized
  from one bad contract to the whole category.
- **The decisive argument for MCP: a tool description is guidance delivered at
  the point of use.** It arrives with the tool, every time, unmissable. A CLI's
  guidance lives in a skill that may not be loaded, mediated by memory. For a
  plugin whose entire thesis is *make failures loud*, that is the same argument as
  *lessons that can become guards, should.*

So: **MCP.** This is settled and it is the thing we drifted off last time.

### 7.5 Delivery model

- **Two classes, not three.**
  - `gating` → monitor **interrupts**, full message, now.
  - `normal` → **Stop hook** injects at turn end via `additionalContext`.
- We considered a middle class (interrupt with a minimal "you have mail" notice)
  and cut it: it costs an interruption to save an interruption, and at high
  message volume notice-spam is its own friction.
- Misclassification risk is mitigated by the MCP tool description guiding the
  choice at the point of use — the two decisions reinforce each other.
- **The Stop hook also sweeps undelivered `gating` messages**, so a monitor that
  failed to deliver cannot lose a ruling.

**Interrupt delivery dissolves "blocking" as a control primitive.** Every problem
blocking was solving is downstream of *the answer cannot reach you while you are
working*. But the flag survives with a **changed meaning**: not "does the sender
block" but "does the receiver get interrupted" — which is the cost that is
actually real.

*(Completed after the first real adopter tripped the gap: the classes govern
delivery relative to an active turn, and an **idle** recipient has no turns —
a `normal` message to an idle peer waited forever. The full principle: urgency
rations derailment, and idle has none to ration — so both classes deliver
immediately to an idle session, waking it; that is what lets peers activate
each other without the PO couriering sessions awake. The busy/idle
discriminator is the harness's own session registry
(`~/.claude/sessions/<pid>.json`, transition-stamped `status`), layered over a
transcript-mtime fallback and a gating-only floor — nothing of ours stored,
nothing of ours to go stale. And boundaries have two edges plus a birth: the
sweep now runs at turn end, turn start, and session start, all through the one
transactional claim so over-delivery is impossible. Sender surface unchanged —
still two classes.)*

### 7.6 Architecture

Three processes, one store, **no IPC and no domain socket**:

- **MCP** writes messages (identity from injected env).
- **Monitor** (plugin-shipped, auto-launching, agent cannot forget it) polls the
  store for *my* undelivered `gating` messages and interrupts.
- **Stop hook** (plugin-shipped, same mechanism as our existing SessionStart
  hook — a small Python script) reads the store and injects at turn end.

A domain socket was considered and rejected: it adds a listener lifecycle, a
cleanup story, and platform quirks to solve a coordination problem the shared
database already solves.

### 7.7 Message and state semantics

Message is `{from, to, thread, class, body}`. That is the whole protocol.

**State fields — `delivered_at`, not `read`:**

- We can *know* delivered (we injected it). We can never know read. Claude's
  `read` flag is really a delivery flag, misnamed.
- **`acked_at` for `gating`** — explicit acknowledgement, either an ack call or
  implicitly on thread reply. *"A ruling was injected"* and *"the implementor has
  confirmed the ruling"* are different facts, and the difference is exactly the
  pain (rulings crossing in-flight work). An arch that can see
  **delivered-but-unacked** has a signal no discipline provided.

**Transactional delivery — PO's requirement, and it is right:** injecting the
context and marking the record delivered must **commit together**. The dangerous
failure is *successful injection, failed marking* — that re-delivers at 1–2 Hz and
spams the agent's context. Wrap it; defend against the partial case explicitly.

**THE BUS IS NOT A LEDGER — a PO ruling (2026-08-07) that supersedes part of
this section.** The `acked_at` design below was built (bus_ack, through 0.6.0),
went unused by every party while a drift detector watching it fired six times,
was wrong six times, and produced one false report the time it was believed —
and the PO's challenge went deeper than the incident: an accounting layer that
ticks-and-ties messages to actions rewards busy work and betrays the bus's
purpose, frictionless communication. The codified principles:

- **Passive memorialization, yes** — delivered_at, delivered_by, and the repo's
  commit hash at delivery, stamped by the system, asked of no one.
- **Active tracking handles, no** — no acks, no receipts, no protocol steps
  whose purpose is accounting. A sender who needs confirmation *asks*; the
  reply is a conversation and lands on the trail.
- **Pull diagnostics over push alarms** — `bus.py log` (lookback: chronology,
  state, hash, filters) and `bus_status` answer questions; detectors that
  watch proxies manufacture false signal and *train their readers invisibly*
  ("I did not notice I was being trained"). The one surviving detector
  (decision-collision) measures the work's own artifact, not a protocol about
  the work.
- **Point-of-use context over ceremony** — the send response may volunteer
  what the sender is about to overlook (their own still-pending messages to
  this peer; prior traffic citing this record), because that arrives at the
  exact moment a stale assumption would be acted on, and costs nothing.
- **Plumb never touches the tracker and never creates supplemental ledgers**
  for agents to maintain — reaffirmed.

The hallucinated-dispatch shape ("routed", written in the ruling's own
sentence, never performed) is real and recurring — the answer consistent with
this ruling is an implicit trail cheap enough that *checking a claim costs
less than trusting it*, not a receipt protocol.

**Retention:** SQLite makes pruning a `DELETE` rather than a rewrite. We need a
policy; the JSON-array model never had one and that is why it degrades.

### 7.8 Identity — and the second problem it solves

`mcc` injects per-agent identity at launch (env vars and/or CLI args). The MCP
reads it to know who is sending; the monitor reads it to know whose messages to
watch. This is what lets several agents **co-located in one repo** distinguish
themselves.

The same mechanism solves a second, separately-documented problem: **per-agent
tracker credentials.** All agents on a project currently authenticate to the
tracker as one identity because `.mcp.json` is shared, so author fields cannot
distinguish them and comments carry a hand-typed prefix by convention — *a
convention surviving on discipline inside an artifact whose whole purpose is
surviving context loss.* If mcc can inject per-agent env, `.mcp.json` can
reference it and each agent gets its own key.

One mechanism, two asks. The env contract should be designed knowing this is
coming, even if we implement it later.

### 7.9 The durable record survives every transport decision

Independent of all of the above: **anything that gates work goes on the durable
record at the moment it is decided.** The message is the *notification*, not the
record. This is true under any transport, it is the one rule no discipline fixed,
and it removes a step agents forget under momentum. Build it regardless.

---

## 8. Lifecycle and compaction — open, and parked deliberately

The PO observes that implementors "get tired" as context fills: deferring scope,
or simply stopping — *"my context is exhausted, have the PO run impl-end and start
a fresh impl."* The risk is **stopped work** under context pressure when the PO
has stepped away.

Threads here, none settled:

- **Can one agent tell another to invoke a skill over the bus?** Agents can
  activate skills through a harness mechanism. If agent A sends "invoke skill X"
  and B can act on it, that is a real capability — and the specific question is
  whether it extends to **compact**. Worth testing empirically; the PO wants this
  tested regardless of whether we end up using it.
- **`PreCompact` hook is available** (confirmed by the PO). Hooking it to fire the
  **handoff write automatically** is, I think, the better answer than
  agent-invoked compaction: it works *with* the mechanism rather than against it.
  Context exhaustion stops being an event anyone must attend — the implementor
  writes its state on the way down and reads it on the way up.
- That would make the offboard implementor genuinely free, because the thing that
  made it expensive was the PO being its operator.
- **Parked as a concern to observe.** We should see what actually happens under
  real plumb usage before designing for it.

Also worth recording: I suspect an agent cannot type `/compact` at itself
(output is not input), but the skill-invocation route is a different mechanism
and is the thing to actually test.

---

## 9. Already shipped (in main, before any plumb work)

- **bus 1.1.0** — documented turn-bounded delivery and the discipline it forces
  (send-and-stop when the answer changes your next move; never infer loss from
  silence; rulings on the durable record at decision time). Corrected in
  `SKILL.md`, the SessionStart hook, the README, and `/bus:identity`.
- **mama 3.6.1 / pdt 3.0.2 / mam 3.0.1** — the same wrong framing had been copied
  into all three methodology skills, which are the surfaces agents actually load.

This matters as evidence: our own documentation was actively teaching the model
that a real project had to unlearn expensively.

---

## 10. The trap — stated plainly so we notice it next time

**Plank's proposal is evidence, not specification.** It is 41 failure-shapes deep
in one codebase, and its author has never seen the projects that succeeded with
no methodology at all. If we build it faithfully we will ship *Plank's process* as
the new universal — which is **exactly MAMA's mistake with better content.**

Concrete tells that we are falling into it:

- A feature justified only by "Plank asked for it," with no answer to *would this
  have helped nonlinear and augrid?*
- Process text living in a skill's prompt instead of in the project's document.
- Anything that presumes a specific tracker, a specific stack, a specific team
  topology, or the offboard implementor.
- Any skill that is a helpful template rather than a guard against a named
  failure.

The defence is the instruction I care most about, and it is Plank's own best
insight turned back on itself: **describe the process rather than embed it.
Claims decay — build the expiry in.**

---

## 11. Where I would go next

1. **The spike** — monitor interrupt semantics (does a plugin-shipped monitor's
   output interrupt an in-progress turn, or land at the boundary — *the single
   fact the whole delivery design rests on*); Stop hook `additionalContext`
   behaviour; `PreCompact`; the skill-invocation-over-bus question; SQLite bus
   end-to-end. Most is testable **solo** — a script inserting a row stands in for
   a sender. Only the true two-agent flow needs the PO to launch a participant.
2. **The bus** on the settled architecture (SQLite + MCP + monitor + Stop hook,
   two classes, delivered/acked, transactional delivery, mcc-injected identity).
3. **Layer 1** — the process host. Least coupled to the transport work; the piece
   most likely to be skipped under momentum; **the piece that actually makes this
   plumb rather than MAMA-with-better-content.**
4. **Layer 2** — the evidence layer as skills.
5. **The mama → plumb migration**, designed last, once we know what migrating
   actually means.
6. **Plank adopts plumb** — the first real onboarding of an in-flight project,
   PO-guided, prescriptive. Also the first live test of `migrate` +
   `establish`-as-re-run against a project that already owns a mature
   way-of-working document; what it teaches feeds straight back into the
   plugin.
