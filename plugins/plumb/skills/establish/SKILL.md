---
name: establish
description: Negotiate this project's way of working with the Product Owner, and record it. New project — interview. Existing project — read what is there, infer the de facto process, propose it back. Produces the manifest, the process document, and the project's own skills. Re-runnable, because process evolves. Use when adopting PLUMB, when a project's way of working has drifted from what is written, or when a phase change makes the old shape wrong.
---

# Establish this project's way of working

Everything else in PLUMB defers to a document. **This is the skill that writes it — with the Product
Owner, not for them.**

MAMA shipped a process and asked projects to conform. PLUMB does the opposite: the process is
negotiated, recorded in the project, and **PLUMB reads it.** So this conversation is not setup. It is
the product.

---

## The stance, before you start

Three things that will make this go wrong if you forget them:

**1. Do not propose a methodology *as a package*.** You are not here to sell an arc rhythm. If you
arrive with a shape and collect agreement to it, you have written a template with extra steps — and a
template arriving attached to a tool is the precise failure PLUMB exists to prevent.

But that is not a licence to withhold what has been learned. There *is* a pattern library
(`plumb patterns`) — practices that have been run at scale with their costs measured — and Step 3½
is when you use it. Four rules make it a resource rather than a template, and they are not optional:
**consulted after the interview, never before; offered one at a time, never as a set; adoption
recorded with its reason; declining recorded too.**

**2. Write the minimum, and expect to be wrong.** A process document authored in one sitting, before
any work has happened, is a guess wearing a document's clothes. Establish the *skeleton* — who does
what, where things live, what is already dead — and let norms arrive the way the good ones actually
arrive:

> Every good norm in the source project's process document was **logged as an instance and promoted
> after it recurred.** Left to memory, they stay in the log where nobody reads them.

So the reflection log matters more than the norms section on day one. The norms section is supposed
to be thin at the start. **Say that out loud** so its thinness does not read as incompleteness.

**This is greenfield guidance, and it inverts for an in-flight adoption.** A project with real
history has norms that arrived exactly the right way — logged as instances, promoted after
recurrence, several carrying the scar that produced them. Starting thin there would destroy the
most valuable content the project owns. The in-flight default: **carry earned norms forward with
their evidence; the burden is on deleting one, not on keeping it.** What gets rewritten is what the
old tooling *supplied* — the norms the team *earned* are precisely what "let norms arrive by
recurrence" produces, already arrived. (`plumb:migrate` owns that path and says the same.)

**3. This skill is re-runnable, and that is the point.** An establishing step that runs once is a
template. Say when you finish: *"run this again when the way of working has moved."*

---

## Step 1 — Read before you ask

Never open with a blank page. Even on a greenfield repo there is usually something.

```bash
plumb manifest 2>/dev/null      # already established? then this is a RE-run — see Step 6
plumb ceremony list
```

Then read what the project already says about itself:

- `CLAUDE.md` / `AGENTS.md` — often the de facto process, written informally
- `README`, `CONTRIBUTING`, anything in `docs/`
- **`git log`** — the real cadence. Commit shapes, release rhythm, who touches what
- Existing trackers, issue templates, PR templates
- **MAMA artifacts** (`.mcc/`, `docs/sprint/`, `architect_state.md`) — see Step 5

Come to the conversation with **observations, not questions**. *"You seem to release on a tag and
squash-merge everything else — is that a rule or a habit?"* beats *"how do you release?"*

---

## Step 2 — Establish the skeleton, by asking

Eight things. Ask about what is not already answered by Step 1; confirm what is.

1. **Who is in this?** Which roles actually exist here — a separate implementor session, a design
   partner, or only the PO and one agent? Do not assume PLUMB's default cast. A project with one
   agent and one human is legitimate and much of PLUMB still applies.
2. **What may each of them decide alone, and when do they escalate?** Ask it as *"if this call is
   wrong, who pays, and how much?"* — cheap calls inside your lane, boundary moves, and calls that
   belong to the PO are different kinds of decision, and roles without boundaries are just names.
   A short answer now is fine; this is one that sharpens with use.
3. **How does work get bounded here?** Bounded bodies of work with a start and a close, a continuous
   flow, something else entirely? **Ask it neutrally.** Do not offer an arc rhythm as the default —
   but *do* ask, because unlike most of this document a cadence cannot arrive by promotion. A
   project needs some answer from day one, and the answer shapes half the other artifacts.
4. **Where does execution state live — and what forces anyone through it?** The tracker, or nothing
   yet. This sets `[ledger] adapter`. If they have no tracker, say plainly what the `markdown`
   adapter costs them. Then the question most projects are never asked: **for each record they
   declare, what part of the work forces anyone through it?** Chat answers because the PO asks; the
   bus answers because a peer is blocked; git answers because the change doesn't exist until
   committed — a tracker is often forced by *nothing*, and *a record either sits on a forced path
   or needs a named trigger; "discipline" is the name of the missing trigger* (`plumb ledger
   guide` has the full treatment). What the ledger will and won't hold goes in the manifest as
   `[ledger] scope`, in their words — **don't declare what they won't carry.**
5. **Where does design memory live?** Which documents exist, which are load-bearing, which are
   fiction. This sets `[artifacts]`.
6. **Who do you depend on, and who depends on you?** Other teams, upstream providers, downstream
   consumers. Structural, and it decides whether the cross-team half of the tooling matters at all —
   which is exactly what the `markdown` adapter cannot give them.
7. **What is already dead?** The highest-value question in the interview, and the one nobody thinks
   to ask. *"What have you tried and stopped doing? What document does nobody maintain?"* Every
   answer becomes an `[artifacts.retired]` entry **with its reason**, and that entry is a permanent
   guard against the thing coming back attached to a tool.
8. **What do you do repeatedly that you would want shorthand for, and what has gone wrong more than
   once?** The first feeds Step 4. The second tells you what this project's guards should watch and
   what its failure catalog will open with.

---

## Step 3 — Write the manifest and the document

```bash
plumb init --document <path they chose>   # scaffolds both; skips an existing document
plumb doctor                              # then make it pass
```

Both files come out of the scaffold **deliberately empty** — no roles, no artifacts, no pre-written
process. That is the design, not an omission: a declaration nobody made is a suggestion, and
suggestions become obligations. Everything you now add comes from the conversation. Rules:

- **`[artifacts]` contains only roles this project actually has.** Every entry you write should
  trace to something the PO named in Step 2. If you cannot say who told you a role exists, it
  does not go in.
- **`[artifacts.retired]` carries reasons, in the PO's own words where possible.** The reason is what
  makes the refusal teach instead of merely block.
- **The process document holds only what they actually said.** Do not fill sections to make it look
  complete. An empty Norms section with a live Reflection Log is *correct* on day one.
- Set `process_version = 1`. It moves when the process moves, not when PLUMB does.

Show them the retired list explicitly and explain what it will do. It is the least obvious part of
the manifest and the one with the sharpest teeth.

---

## Step 3½ — Offer patterns, one at a time, against what they told you

**Only now.** The PO has described their project; you have written down what they said. This step
asks whether anything learned elsewhere addresses a problem *they named*.

```bash
plumb patterns                  # the list
plumb patterns <name>           # the full entry
```

How to offer one, and the shape matters more than the content:

1. **Anchor it to something they said.** *"You mentioned nobody can tell which checklist ticks were
   actually verified — there's a practice for that."* Never *"most projects do X."*
2. **Lead with the scar, not the practice.** What it cost when it was absent is the evidence; the
   practice is just the response to it.
3. **Read them the cost, and the 'how you'd know it's wrong for you' field.** Out loud. A pattern
   that cannot tell you how to reject it is a template, and that field is the reason these are not
   templates.
4. **One at a time.** Never present the list as a set to pick from — that is a menu, and a menu gets
   taken wholesale.
5. **Record the outcome either way.** Adopted → the process document says *why*, in their words, so
   that later someone **can** point to when it was chosen. Declined → note it, so a re-run does not
   re-offer it and teach them to stop reading.

> **A practice adopted without a recorded reason is indistinguishable from scaffolding within one
> sprint.** The reason is not paperwork; it is the thing that makes the practice *theirs*.

The evidence base is deep but **narrow** — one team, one domain, one shape of product. Say so. A PO
who knows the sample size weights the advice correctly; one who does not hears it as settled.

**Offering nothing is a legitimate outcome.** If nothing they described matches a pattern, say that
and move on.

---

## Step 4 — Author the project's own skills

**This is the half that distinguishes PLUMB from MAMA, and it is easy to skip.** It is also where
the way of working stays *present*: the wow is a document, and a document not in the room loses to
whatever is — but skills are surfaced by the harness at matched moments. **A project's own skills
are the wow's ambient surface.** Skimping here is how a process becomes something a session once
wrote instead of something it does.

Project skills come in **two genres**, and the first is the one every new project skips:

**Instruments — recurring lenses over a surface the wow declares.** Not rare, not ceremonial: the
regular act of *looking at something you own and reporting what you see against what the wow says
should be true*. A board-review ("for every waiting issue, name who it's waiting on"), a
roadmap look ("where are we, what moved"), a drift check, a ledger-truth pass before a status
report. **The roster derives itself — don't ask the team what lenses they want.** Apply the
forced-path test (Step 2, question 4) to *every* declared record: each one the work does not
force anyone through gets its instrument, and the ones that pass need none. (The project that
first ran this derivation found three of its six declared records failed the test — including
two its own drift report had never thought to check.) **The declaration and its instrument
arrive together, or the declaration doesn't.**

Two shapes, split by trigger:
- **Judgment-moment → a skill.** Deciding what is genuinely done, what is missing, what the gaps
  mean. Write the description as the trigger condition ("use before any status summary to the
  PO") — the description is what the harness matches on.
- **Lifecycle-moment → a hook, not a skill.** *"Look at X at moment Y"* with no judgment in the
  look wants `.claude/settings.json`, not `.claude/skills/` — hooks can run scripts *and call MCP
  tools directly* (`type: "mcp_tool"`: an inbox check at every Stop, a mirror refresh on every
  decision write — see `plumb ledger guide`). A hook beats a norm for the same reason a mechanism
  beats a trigger. And where the moment is *while you are idle* — the one moment no project hook
  can reach — a `[tickers.<name>]` entry in `.plumb.toml` runs your script inside plumb's monitor
  and its output wakes you (see the `bus` skill).

**Ceremonies — ordered sequences, run rarely.** The release sequence, the grain change, onboarding
a data source. These usually *cannot* be written on day one, and should not be forced — they arrive
by recurrence (`plumb:ceremony`, the second time you run something).

Both live in the project's own `.claude/skills/`, invocable by name, so the PO gets shorthand
through *their* workflow rather than ours.

**This is where the project's *rhythm* becomes real.** PLUMB deliberately does **not** ship skills
for planning an arc, kicking one off, or closing one — because what an arc *is*, what a kickoff
contains, and what "closed" means are all project-defined. Shipping those would rebuild the exact
template-attached-to-a-tool failure PLUMB exists to prevent. They belong here, authored by this
project, in this project's words.

So if Step 2's question 3 produced a rhythm, this is where it gets a home:

- a skill for **opening** a unit of work — whatever this project calls one
- a skill for **closing** one, including whatever their reconciliation actually is
- a skill for the **kickoff**, if roles are split (and remember: a kickoff is a *message*; a skill
  that writes it to a file has already misunderstood it)

**Before writing the first one, read an exemplar** — `plumb exemplars` shows two real-shaped
ceremony skills from one (illustrative) project, with the checklist of properties that make a
ceremony skill good. They exist to calibrate your sense of grain and discipline — how thin, how
much doc-pointing, what an in-place amendment looks like. **They are not starters**: the first
draft of your project's skill comes from your project's reality, in your project's vocabulary, or
it is inherited rather than owned. If the PO says "batch" or "cycle" or "chunk", the skill says
that — and a pattern from `plumb patterns` may inform *what* a ceremony covers, never its words.

Plus whatever came out of Step 2's question 8, and what `git log` showed you:

```bash
plumb ceremony new <name> --description "<when to reach for it>"
```

Then fill it in **with them**. Two rules the scaffold states and you must enforce:

1. **Address artifacts by role, never by filename.** Project-authored skills are *more* likely to
   smuggle a template than PLUMB's own, not less — they are written close to the work, in a hurry,
   by someone who knows the filename. This is where the drift will come back if it comes back.
2. **Carry sequence, not standing behaviour.** If a step is really *"always do X"*, it is a norm —
   move it to the document.

**Do not invent ceremonies — but do not leave the instruments empty.** Ceremonies arrive by
recurrence; if none come to mind, write none and say what will prompt one. Instruments are the
opposite case: they are derivable from the surfaces the wow just declared, and an empty instrument
roster means the wow has no ambient presence — the first evidence project produced its real roster
only after its PO caught the drift an instrument would have seen. One instrument per declared
surface is the honest day-one floor.

---

## Step 5 — If this is an existing MAMA project

Switch to the `plumb:migrate` skill — it runs this same establish conversation *plus* the
MAMA-specific work: inventorying the old artifacts, separating what was chosen from what arrived as
scaffolding (the distinguishing question: **can anyone point to when this was decided?**), and
emitting the `[artifacts.retired]` entries the project has earned (`plumb migrate retired`).

Do **not** delete MAMA state or disable the plugin. Both can coexist; say so.

---

## Step 6 — If this is a RE-run

Different conversation, and the more important one. The project has been working; the document has
been sitting still. Assume drift and go looking for it.

- **Diff the document against reality.** What does it say that is no longer true? What is everyone
  doing that it never mentions?
- **Ask what died since last time** — retired entries are additive, and this is when most of them
  get added.
- **Run `plumb:promote`** if reflection-log entries have recurred enough to become norms. That is the
  mechanism by which this document is *supposed* to grow.
- **Bump `process_version`** if the shape changed, and note what moved.

The tell that a re-run was overdue: *nobody can point to when the current way of working was
decided.*

And one bias to watch in the room, especially when the re-run was prompted by a failure: **the
author of a diagnosis over-corrects toward it, and over-correction looks like modesty — which is
why it survives review.** The specific shape observed: narrowing a claim to whatever was recently
failed. The PO may correctly push the other way; a wider claim can put a record on more of the
work's forced paths.

---

## Done when

- [ ] `plumb doctor` passes
- [ ] Every role in `[artifacts]` is one the project actually has
- [ ] `[artifacts.retired]` has at least one entry, with a reason — a project with nothing dead has
      either not been asked, or is genuinely new, and you should know which
- [ ] The process document says only what the PO said
- [ ] The reflection log exists and its purpose was explained
- [ ] Project skills authored, or explicitly none with a note on what would prompt one
- [ ] Both files committed
- [ ] The PO knows this skill is **re-runnable**, and roughly when to re-run it
