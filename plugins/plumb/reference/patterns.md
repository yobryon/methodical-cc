# Pattern library

Practices that have been run, at scale, with their costs measured. **Not a methodology.** Not a
menu of things you should do.

## How to read this, and how NOT to

Every entry carries five fields, and the last one is the important one:

| Field | Why |
|---|---|
| **Practice** | What it is, in one line |
| **The scar** | What it cost when it was absent — concrete, with numbers where they exist |
| **Applies when** | The conditions under which it earns its keep |
| **Costs** | What running it takes, so you can decline on cost alone |
| **How you'd know it's wrong for you** | The tell that this is not your project's practice |

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

**Costs.** Two sessions to launch and keep alive. A messaging channel between them. Real coordination
overhead — one project measured ~15 ledger comments plus ~15 messages for an 8-issue arc.

**How you'd know it's wrong for you.** One human and one agent, short scoped tasks, or work where the
design is settled before building starts. If the architect has nothing to rule on while the
implementor builds, you are paying for a split you are not using.

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

---

## handoff-state — A state document that leads with what is missing

**Practice.** At a context boundary, write a document that opens with **what is missing**, then the
queue in order, what the successor must not rediscover (with closed options named *by name*),
environment traps carrying the day each cost, and committed-but-inert code labelled as such.

**The scar.** Three relays across live arcs cost **zero rework**. The one arc that had no state
document cost its successor a morning.

**Applies when.** Sessions end before the work does — which, at any real scale, is always.

**Costs.** Half an hour at exactly the moment you are out of room.

**How you'd know it's wrong for you.** Work that reliably fits in one session.

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
