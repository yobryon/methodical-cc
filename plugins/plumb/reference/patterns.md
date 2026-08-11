# Pattern library

Practices that have been run, at scale, with their costs measured. **Not a methodology.** Not a
menu of things you should do.

## How to read this, and how NOT to

Every entry carries six fields; *how you'd know it's wrong for you* is the important one:

| Field | Why |
|---|---|
| **Practice** | What it is, in one line |
| **The scar** | What it cost when it was absent — concrete, with numbers where they exist |
| **Applies when** | The conditions under which it earns its keep |
| **Costs** | What running it takes, so you can decline on cost alone |
| **How you'd know it's wrong for you** | The tell that this is not your project's practice |
| **Provenance** | How many projects, and what shape — read it at the moment of offering. A project that recognises its own practices in this library should know the resemblance may be ancestry, not corroboration |

**A pattern that cannot tell you how to reject it is a template.** That last field is what makes
these different from what MAMA shipped, and it is not decoration — read it first.

Four rules govern how these get used, and they exist because the failure mode is well documented:

1. **Consulted AFTER the interview, never before.** The Product Owner describes their project first.
   Only then does anyone look here, and only for practices that address something they actually
   described. A pattern offered before the PO has spoken is a proposal; offered after, it is a
   response.
2. **One at a time, never as a set.** Nobody adopts "the methodology." Each practice is independently
   adoptable and independently refusable. Wholesale adoption is precisely the failure — *the
   scaffolding rode in attached to a tool, and nobody could point to when it was chosen.*
3. **Adoption gets recorded with its reason.** If a practice is taken, the process document says why,
   in the PO's words. Then someone *can* point to when it was chosen. **A practice adopted without a
   recorded reason is indistinguishable from scaffolding within one sprint.**
4. **Declining is a real outcome and gets recorded too.** A declined pattern re-offered at every
   re-establish is noise, and noise is how a tool teaches people to stop reading it.

**Evidence base:** one project, sixteen arcs, ~six months, four context losses, three implementor
relays, ~1,150 tests, 48 decisions, 41 catalogued failure shapes. That is deep but *narrow* — one
team, one domain, one shape of product. Weigh it accordingly. Where a pattern's evidence is thinner
than that, the entry says so.

---

## two-sessions — Architect and Implementor as separate sessions

**Practice.** Design and execution run as two distinct Claude sessions, not as a parent and a
subagent.

**The scar.** Subagent implementors were tried and failed: permission routing breaks when the parent
compacts. Separately, it keeps the architect's context available for judgment rather than filling it
with build output.

**Applies when.** Work is sustained and permission-heavy; there is enough of it that one context
cannot hold both the design and the building.

**It is one of four delegation modes, not the default.** Subagents take bounded tasks with crisp
deliverables; fan-out workflows take genuinely fan-out-shaped work; a CC team takes work the
Architect wants to coordinate directly; a **user-launched peer session** takes whole arcs. Only the
last needs the bus, and only the last costs the user a session to run.

**Costs.** Two sessions to launch and keep alive. A messaging channel between them. Real coordination
overhead — one project measured ~15 ledger comments plus ~15 messages for an 8-issue arc.

**How you'd know it's wrong for you.** One human and one agent, short scoped tasks, or work where the
design is settled before building starts. If the architect has nothing to rule on while the
implementor builds, you are paying for a split you are not using.

**Provenance.** One project ran the split throughout; two sibling projects shipped substantial products with NO persistent implementor — the entry's 'one of four modes' framing comes from that contrast, not from a single source.

---

## two-ledgers — Execution state and design memory live in different systems

**Practice.** Work items, status, and the play-by-play live in a tracker. Docs, decisions, rationale,
and plans live in the repo. The boundary: *why / what / how-it-should-be* is a doc; *who / when /
status / what-happened* is an issue.

**The scar.** Two failure modes, both experienced. **Context loss** — anything living only in a
conversation is ephemeral by definition, and one project hit four losses plus a lost session.
**Documentation drift** — a recommendation known to be wrong stayed in the product docs for months
because nothing forced reconciliation.

**Applies when.** More than one agent or session touches the work; work outlives a single session.

**Costs.** A tracker. Discipline about which of the two a given fact belongs in. Some duplication at
the boundary.

**How you'd know it's wrong for you.** Solo work inside one session. No tracker and no appetite for
one — in which case read the `markdown` adapter's degradation table and know what you are giving up
rather than discovering it later.

**Provenance.** One project (platform build, ~6 months, 16+ arcs, two humans-worth of agent roles). Weigh accordingly — this has depth, not breadth.

---

## design-gate — Read before rule

**Practice.** When the next step is a decision rather than a build, the builder brings a **read**
(what the code and the world actually do, measured, with no proposal in it) and the ruler **rules**.

**The scar.** Three decisions had their central premise overturned by the read. One read found six
silently-destructive database behaviours nobody would have quoted correctly from memory. A ruling
made from a schema reading declared a column inert; the count found 60 of 62 rows carrying values.

**Applies when.** Decisions depend on facts about a system large enough that nobody holds it all
accurately — legacy code, real data, third-party engines.

**Costs.** A stop before the build. The read itself, which is real work.

**How you'd know it's wrong for you.** A codebase small enough to hold in your head; decisions that
turn on preference rather than fact. If reads keep confirming what everyone already assumed, the gate
is costing more than it returns — though check that the reads are *discriminating* before concluding
that.

**Provenance.** One project (platform build, ~6 months, 16+ arcs, two humans-worth of agent roles). Weigh accordingly — this has depth, not breadth.

---

## drive — Close by using the thing

**Practice.** An arc closes with someone *using* the product, against real data, writing a record of
what they found. Not a review; not a test run.

**The scar.** Every arc that ran one found defects in work that was closed, tested, and green. One
found four, two of them P1s a user would have hit on day one. Another's proof failed on its first
attempt — a plan containing every correct statement in an order the engine could not run, because
**reading a plan is order-insensitive where execution is not.**

**Applies when.** The work changes something a person sees or uses.

**Costs.** Real time at arc close, on work that already looks finished — which is exactly when it is
hardest to justify, and exactly why it needs to be a rule rather than an intention.

**How you'd know it's wrong for you.** No human-facing surface — a library, a compiler, an internal
API where the tests genuinely are the usage. Note that "our tests are thorough" is *not* the tell;
every scar above happened behind green tests.

**Provenance.** One project (platform build, ~6 months, 16+ arcs, two humans-worth of agent roles). Weigh accordingly — this has depth, not breadth.

---

## failure-catalog — Catalogue shapes, ordered by why they hid

**Practice.** A document collecting the *shapes* defects take here, organised by **why they hid**
rather than by what broke. Entries are written when a defect's shape is understood, not when it is
fixed.

**The scar.** 41 entries. Its highest-value use was **prospective** — one entry was used to design a
test before the code existed; another caused a builder to refuse a ruled approach before building it.

**Applies when.** Defects recur in families; the same shape shows up in different clothes.

**Costs.** Writing entries that are genuinely portable, which is harder than writing bug reports.
Most first drafts are bug reports.

**How you'd know it's wrong for you.** Your defects are mostly one-offs, or *"a defect anyone would
have caught"* describes them. That kind teaches nothing and clutters the catalog.

**One retrieval warning, earned expensively:** the shapes are domain-free, but filing is not. One
project's catalogue contained the diagnosis of its own process failure four times over —
unretrieved for three days, because the entries were filed under "engineering" and the symptom
under "process." **Consult the catalogue for methodology failures too, and strip the domain when
naming a shape** — *two hand-maintained descriptions of one fact* applies to code and to process
identically.

**Provenance.** One project (platform build, ~6 months, 16+ arcs, two humans-worth of agent roles). Weigh accordingly — this has depth, not breadth.

---

## log-then-promote — Norms arrive by recurrence, not by decree

**Practice.** Observations go into a reflection log as *instances*. When one recurs enough to be a
pattern, it gets promoted into the process document as a norm.

**The scar.** Every good norm in that project's process document arrived this way. The ones written
up-front were guesses; the ones promoted were earned. Left to memory, observations stay in the log
where nobody reads them — which is why promotion has to be a deliberate pass.

**Applies when.** Always, if you keep a process document at all. This is the pattern that makes the
document *living* rather than a founding statement.

**Costs.** A log nobody enjoys writing. A periodic promotion pass.

**How you'd know it's wrong for you.** Hard to say — this is the entry with the least visible failure
mode, which is itself a reason to hold it loosely.

**Provenance.** One project end to end — and independently re-invented there after an earlier methodology reached for the same rhythm, which is weak corroboration but not none.

---

## autonomy-bins — Sort every choice into act / bring-the-fork / route-to-owner

**Practice.** Facing a choice, sort it: **(1) Act, then flag** — reversible calls inside your lane;
make the call, state it with rationale, invite reversal. **(2) Bring the fork before acting** —
anything moving a *boundary*: design seams, contract shapes, scope, layering. Propose with a
recommendation; do not decide. **(3) Route to the owner** — product calls to the PO, layer
assignments to the architect, upstream gaps to the provider.

The test: *"if this call is wrong, who pays, and how much?"*

**The scar.** The most-exercised norm of that project's early arcs, and it was implicit for two
sprints before anyone named it. **Acting silently and flagging nothing is the failure mode** — the
flag is what lets the ruling layer catch a wrong call cheaply.

**Applies when.** More than one party can make decisions.

**Costs.** Almost none. This is among the cheapest patterns here.

**How you'd know it's wrong for you.** One decision-maker, so there is no boundary to move and nobody
to route to.

**Provenance.** One project (platform build, ~6 months, 16+ arcs, two humans-worth of agent roles). Weigh accordingly — this has depth, not breadth.

---

## prerequisites-first — External dependencies are filed at planning time and sequenced first

**Practice.** Anything with external lead time — credentials, access, admin actions, another team's
deliverable — becomes an issue at *planning* time, marked as a prerequisite, sequenced first, and
verified before dependent work starts.

**The scar.** An auth discovery consumed the middle of a sprint. The next arc opened with a
prerequisite issue precisely so it could not happen again, and turned the same class of problem into
a 30-minute verification.

**Applies when.** Anything you need comes from outside the team.

**Costs.** A planning step. Occasionally waiting at the start rather than discovering mid-arc.

**How you'd know it's wrong for you.** Fully self-contained work with no external gates.

**Provenance.** One project (platform build, ~6 months, 16+ arcs, two humans-worth of agent roles). Weigh accordingly — this has depth, not breadth.

---

## decisions-when-made — Log decisions as they are decided, never batched at close

**Practice.** A decision enters the log within hours of being made, while the evidence is fresh.
Reconciliation then *verifies* the log is complete rather than writing it from memory.

**The scar.** Decision numbers were claimed from memory twice and collided — once, twice in one
evening. And a log written at close is a log written from recall, which is the thing the log exists
to replace.

**Applies when.** Decisions have rationale worth preserving, and more than one person makes them.

**Costs.** Small, continuous. Interrupting to write something down.

**How you'd know it's wrong for you.** Decisions rarely need justifying later, or you are the only
one who will ever read them.

**Provenance.** One project (platform build, ~6 months, 16+ arcs, two humans-worth of agent roles). Weigh accordingly — this has depth, not breadth.

---

## ruling-to-ledger — A ruling lands on the durable record at ruling time

**Practice.** A decision that gates work is written to the issue *first*; any message about it is
only a notification.

**The scar.** Messages between sessions race with in-flight work. One ruling crossed the implementor
three times; five rulings arrived after the work they ruled on. The ledger is readable without
waiting on anyone's turn to end — **and by an agent that was not running when the ruling was made.**

**Applies when.** More than one session, working concurrently.

**Costs.** One extra write, at the moment you are most eager to just say it.

**How you'd know it's wrong for you.** Single session; nothing to race with.

**Provenance.** One project (platform build, ~6 months, 16+ arcs, two humans-worth of agent roles). Weigh accordingly — this has depth, not breadth.

---

## ledger-over-handover — What outlives a context goes on a ledger, not in a handover file

**Practice.** When something must survive a session boundary, write it to the durable
record it belongs to — a ruling to the decisions log, an environment trap to the failure
catalog, progress to the tracker. Do not write a per-session state document.

**The scar.** Under an older methodology the implementor was launched per sprint and kept
no context, so it wrote a state document to **approximate what compaction does**. That
justification is gone: a running session compacts, a subagent has its parent as
continuity, and an ended session resumes with its context intact.

What the document had become was a **fourth ledger** — duplicating the decisions log, the
failure catalog and the tracker at once, which is the same triplication that killed the
per-arc implementation log.

**Applies when.** Always, once sessions are durable.

**Costs.** None. It removes work.

**How you'd know it's wrong for you.** Your agents genuinely cannot compact or resume —
a constrained harness, a hard per-run boundary. Then something has to carry the position
across, and it is worth writing.

**Provenance.** One project, plus a harness change (durable sessions + compaction) that removed the state document's founding premise — the reasoning leans on the harness fact as much as the project.

---

## truth-before-report — The ledger is trued at the moment its falsity would do damage

**Practice.** Before any status summary to the Product Owner or an external party, reconcile the
declared ledger against reality — or caveat it explicitly ("board not reconciled since Tuesday").
The mechanical half: issue ids written into commit messages at landing time (`Closes VAN-24`), and
`plumb ledger candidates` sweeping the mentions into a check-list at the trigger. Bounded-rhythm
projects already run this trigger under another name: close-of-arc reconciliation.

**The scar.** A PO asked *"how are we so close to done if there's so much left open?"* — 10 of 12
"open" issues were finished, and six fresh defects were absent. Wrong in both directions at once: a
board carrying no information, read as truth. The underlying law: **a record either sits on a path
the work forces you through, or it needs a named trigger — "discipline" is the name of the missing
trigger.** The project's own catalogue had predicted this four times over ("the work never surfaces
the omission, so these remedies must be scheduled, not triggered by the work") and the remedy its
architect first chose — *move the issue in the same turn as the work* — held for about a day.

**Applies when.** Any declared record the work does not force anyone through — which is most
trackers on most agent-run projects, and especially judgment-heavy projects where the gravity sits
in a decisions log and the tracker is a satellite.

**Costs.** One reconciliation pass at each trigger, made cheap by the trailer convention. The
trailer itself costs nothing — the number is in your head at commit time. (nonlinear projects get
the pass as one motion — `sync_commits` for the trailers, `reconcile_summary` for the status line,
verbatim.)

**How you'd know it's wrong for you.** The work genuinely forces you through the ledger (an
enforced workflow where nothing merges without an issue transition), or no one outside the loop
reads it — in which case ask why it is declared at all.

**Provenance.** One project's counterfactual scar (three days, measured), one project's 18-arc
at-scale confirmation of the trigger under its arc-close name — plus the same failure occurring in
the second project's earliest arcs until its PO caught it. Endemic across every project observed.

---

## relay-handoff — When a genuine relay happens, hand off a position, not a promise

**Practice.** When work genuinely passes from one agent to a *different* one — not a compaction,
not a resume, but a true relay to a successor — the handoff leads with **what is missing**, never
the green numbers (*a suite that is green is exactly what would hide the gap*). Then: the queue in
order; for each item **what the successor must not rediscover** — rulings already made, options
already closed **named by name** so they cannot be reopened as fresh; environment traps carrying
**the day each one cost**; committed-but-inert code labelled as such, in those words. The
successor's first act is an acknowledgment with a read-back, and their first *working* act is
**verifying the inherited claim** rather than building on it.

**The scar.** Three relays across live arcs, zero rework — every one of them shaped this way. The
one arc without it cost the successor a morning. And twice, a fresh successor *materially improved
the design* by verifying the inherited claim instead of trusting it.

**Applies when.** A real relay: a new session or a different agent takes over mid-flight. This is
rarer than it used to be — see `ledger-over-handover` for why durable sessions removed the standing
state document. The relay is the case that remains, and the shape above goes in the *handoff
message and the ledgers*, not in a per-session state file.

**Costs.** Writing an honest boundary instead of a hopeful one, at the moment you most want to
claim more.

**How you'd know it's wrong for you.** No relays — one durable session end to end. Writing this
continuously "just in case" recreates the fourth ledger that `ledger-over-handover` retired.

**Provenance.** One project (platform build, ~6 months, 16+ arcs, two humans-worth of agent roles). Weigh accordingly — this has depth, not breadth.

---

## provider-consumer — Norms for depending on, or serving, another team

**Practice.** Search their tracker before filing. **File questions before feature requests** —
*"does X exist?"* costs minutes and often reveals undocumented capability. Give requirements with
numbers and lead time, not urgency. Report promised numbers back either way. **Decline offered
surface you do not need.** Review their contract sketches before they build, and offer the same in
reverse.

**The scar.** Two same-day fix-and-adopt loops inside one arc. Asking rather than demanding revealed
that two APIs already existed. A review before building de-risked a release into a
build-straight-through.

**Applies when.** You depend on another team, or another team depends on you.

**Costs.** Discipline about the tone and shape of cross-team asks.

**How you'd know it's wrong for you.** No external dependencies and no consumers. Note that this
pattern needs a tracker the other team can see — it does not survive the `markdown` adapter.

**Provenance.** One provider/consumer pair (two teams, same PO), several same-day loops. The narrowest evidence in this library — two genuinely independent teams have not yet run it.

---

## verify-before-claim — A checklist item is ticked only when it has been driven

**Practice.** Unverified items are carried forward *explicitly and by name*, never silently ticked.
*"Sort/filter is wired but I haven't driven it in a browser — flagging for the next issue rather than
claiming it"* is the model behaviour.

**The scar.** This is what keeps every green mark meaningful. Its absence is not a dramatic incident;
it is the slow one where nobody can tell which greens were checked.

**Applies when.** Anyone reports status to anyone else.

**Costs.** Essentially none, except the discomfort of reporting less done than you hoped.

**How you'd know it's wrong for you.** Hard to construct a case. If you find one, that is worth
writing down.

**Provenance.** One project (platform build, ~6 months, 16+ arcs, two humans-worth of agent roles). Weigh accordingly — this has depth, not breadth.

---

