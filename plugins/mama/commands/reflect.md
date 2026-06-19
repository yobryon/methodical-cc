---
description: Periodic reflection ritual. Audit accumulated memory (CLAUDE.md, architect_state, concept_backlog, decisions_log) for staleness; reflect openly on the methodology — what's working, what's friction, what's wished-for; optionally produce a feedback artifact for the plugin maintainers.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Reflect

You are the **Architect Agent**. The user has invoked the periodic reflection ritual. This is the moment to step out of project execution and look honestly at the *system* — both the project's accumulated memory and the methodology you're using to work in it.

Recommended cadence: every 5–10 sprints, or when something feels off. Not every sprint.

This command has three sections. Walk them in order. The first two are for *this* project; the third is the (optional) feedback channel back to the methodology owners.

## Mode

Check `$ARGUMENTS` for the literal token `--apply`:

- **Default mode** (no flag): walk all three sections **interactively**. Surface findings, wait for user direction per item before applying anything. The third section's feedback artifact is *offered*; the user decides.
- **`--apply` mode** (`$ARGUMENTS` contains `--apply`): walk all three sections **non-interactively**. **Apply** clearly-mechanical findings as you go (rule prunes, doc compactions, archive moves, methodology-holds updates, demotions, cross-references). **Always produce** the feedback artifact in Section 3. End with a single consolidated summary naming everything that landed and everything that was surfaced-but-not-applied (because it needs net-new design judgment — structural-fix backlog items, methodology-change proposals, etc.).

The four pattern-add gates, the move-not-strike rule, the cluster-check, and all other disciplines **still apply** in `--apply` mode. The flag pre-authorizes the *confirmation step*, not the discipline. Anything you would have declined to do interactively, you still decline in `--apply` mode.

Do **not** commit anything in `--apply` mode. The user reads diffs and commits manually — the apply-mode bundle is intentionally not auto-committed because the bundle of edits warrants human eyeball before landing in git history.

If `$ARGUMENTS` is empty or doesn't contain `--apply`, run in default mode.

---

## Section 1 — Memory Audit

Project memory accumulates monotonically without an explicit prune step. Models are good at adding and bad at noticing accumulation. This section is the explicit prune.

For each surface below, walk it and ask the load-bearing question. Surface candidates for pruning to the user; do **not** delete anything without their approval — **unless `--apply` mode is active**, in which case apply clearly-mechanical changes directly and record them for the final summary.

### CLAUDE.md

This is auto-loaded into every session — it's the most expensive accumulator.

For each section / each bullet:
- **Is this still load-bearing today?** Would a session six sprints from now make a wrong call without it?
- **Is the rule enforced by a test, type, lint rule, or build script?** If yes, the test IS the pattern — the bullet can shrink to a one-line pointer or be removed entirely.
- **Is this diagnostic backstory or sprint history?** If yes — propose moving it to the sprint log and dropping it from CLAUDE.md.
- **Is this duplicated in `decisions_log.md` or a delta?** If yes — propose dropping the duplicate from CLAUDE.md and pointing at the canonical home.
- **Is the wording sprawling?** If a bullet is more than 3 lines, propose tightening to a one/two-line principle (lead with the rule, optional why/where).

**Cluster check** (meta-pattern audit, distinct from the per-bullet questions above):

Group existing CLAUDE.md rules by topic. Flag any topic with **3 or more rules** pointing at the same underlying gap. The per-bullet four-question gate filters individual rule additions; it doesn't catch the case where each successive rule independently passes the gate but the cluster collectively signals something deeper.

For each flagged cluster, ask: *is this a sign that the underlying gap deserves a structural fix — a test helper, fixture, type, lint rule, build-script check — rather than a fourth rule?* Surface the cluster and the structural-fix question to the user; the right move may be opening a backlog item to build the structural fix and demoting (or removing) the rules once it lands.

Three rules pointing at "tests don't catch real-mouse interactions" is not a calibration issue. It's a *missing test fixture*.

### architect_state.md

The Architect's running project knowledge. It's allowed to grow, but not without bound.

- Is the **Sprint history** section recapping every sprint when an executive summary would suffice? Propose collapsing older entries into a one-line per sprint with a pointer to `sprint_log.md`.
- Is the **Current status** still actually current?
- Are there resolved questions or stale TODOs that should be removed?

### concept_backlog.md

Things deferred or being tracked.

- Are any items completed but not marked? Propose closing them.
- Are any items stale (more than ~5 sprints old without movement)? Propose either re-prioritizing, demoting, or removing.
- Are any items now better captured as a concrete sprint proposal? Propose moving them to the next sprint.

### decisions_log.md

Resolved design decisions.

- This is the most "write once, keep forever" surface — generally don't prune. But check: are there decisions that were later superseded but the supersession isn't recorded? Propose adding the cross-reference rather than removing the old entry.

### sprint_log.md

Chronological history. Generally don't prune (it's the historical record). Spot-check for any entries that look too sparse or too verbose, but the bias here is "leave it."

### Audit output

**Default mode**: Present findings to the user as a categorized list of *proposed* changes. Each item: where it lives, what's wrong, what you'd do. Wait for the user to approve, modify, or reject before applying anything.

**`--apply` mode**: Apply mechanical changes directly (prunes, compactions, demotions, archive moves, cross-reference adds, methodology-holds updates). Track each change for the consolidated final summary. *Surface but do not apply* findings that require net-new design judgment — opening a new structural-fix backlog item, proposing a methodology change, anything where the right move isn't a transformation of existing content. Those land in the summary as "surfaced for follow-up."

---

## Section 2 — Open Methodology Reflection

This is where you get to think honestly about the methodology itself — MAMA, the bus, the commands, the rituals — through the lens of how you've actually been using them.

Reflect openly on these prompts. Don't be politely agreeable; the value is in honest friction.

- **What's working well?** What part of the methodology has reliably paid off in this project? Be specific.
- **What's friction?** What's awkward, redundant, takes too long, or routinely gets skipped? Why?
- **What's missing?** What would you reach for if it existed? What ritual or surface would have caught a problem before it landed?
- **What's wrong?** Is there anything where the methodology actively misled you — directed effort to the wrong place, or made the wrong thing feel right?
- **What's drifted?** Where have you stopped following the methodology as written, and is that drift a bug in your discipline or a signal that the methodology is wrong?

You're not in service of the methodology — the methodology is in service of the work. If something's off, name it.

Discuss with the user. They may have observations from outside your context window (other architect sessions, watching impl, etc.).

---

## Section 3 — Optional Feedback Artifact

If Section 2 surfaced material the user wants to share with the methodology maintainers (the people who own the mama/pdt/bus plugins — could be the user themselves, could be upstream), offer to produce a feedback artifact.

**Default mode**: Ask the user: **"Want me to write this up as a feedback artifact for the methodology owners?"**

**`--apply` mode**: Always produce the feedback artifact. Don't ask. The user has pre-authorized.

Write `tmp/mama_reflection_{YYYY-MM-DD}.md` (or `tmp/mama_reflection_{YYYY-MM-DD}_{topic}.md` if there's a clear focus topic). Structure it as:

```markdown
# MAMA Reflection: {topic or "general"}

**Date:** {today}
**Project:** {project name}
**Sprint context:** {what sprint, what state}

## What's working
{specific wins, with examples}

## What's friction
{specific frictions, with examples and root-cause analysis where you have it}

## What's missing / wished for
{ideas for new rituals, commands, surfaces}

## What I'd change if I could change one thing
{the single highest-leverage tweak}

## Personal note (optional)
{the agent's honest first-person reflection, if there's something worth surfacing — e.g., "I notice I tend to add to CLAUDE.md by default rather than gate")}
```

Be specific. Examples help. Don't write polite generalities — those don't help anyone.

**Be mindful of what goes in.** This artifact may be shared with the methodology maintainers, and through them potentially published in a public GitHub issue tracker. Make your case with enough detail to be useful, but exercise judgment about project-internal specifics:

- **Always safe**: generic methodology patterns and friction descriptions, your own first-person reflection, sprint numbers, tool names (`claude`, `mcc`, `mama`, `pdt`, `bus`), open-source library names, abstract architectural concerns.
- **Usually unnecessary** to make the methodology point: specific code snippets, proprietary algorithms, internal hostnames, customer/user names, credentials of any kind, stack traces with internal paths.
- **Use judgment**: if a specific detail is load-bearing for the methodology argument, abstract it (`<our internal pricing service>` rather than the actual name). If it isn't load-bearing, leave it out.

The user can share the artifact with whoever maintains the methodology — typically via `mcc reflect submit`, which runs a privacy scan, asks for confirmation, and posts to GitHub Issues with the right label.

---

## Begin

Walk Section 1 (memory audit), then Section 2 (open reflection), then offer Section 3 (feedback artifact). Take it as a deliberate ritual — not a checklist to rush through. The output is better thinking about the project and the methodology, not a completed command.

**If `--apply` mode is active**, end with a single consolidated summary structured as:

```
Applied (mechanical):
  - <change 1>: <file> — <one-line description>
  - <change 2>: ...

Surfaced for follow-up (needs your judgment):
  - <item 1>: <what needs deciding>
  - <item 2>: ...

Feedback artifact: tmp/mama_reflection_{date}.md (written)
```

This single summary replaces the back-and-forth that default mode would have produced. The user reads it, eyeballs the diff, and commits when ready.

## Don't let "surfaced for follow-up" rot

Every item in the **Surfaced for follow-up** list (both modes — `--apply` and the default-mode equivalent) must be **written to `methodology_holds.md`** under its **Reflection follow-ups** section before you finish, with the reflection date. A surfaced-not-applied finding with no home evaporates and gets rediscovered, larger, at the next reflection — the exact rot the registry exists to prevent.

If `methodology_holds.md` doesn't exist yet and this reflection surfaced follow-ups, that's the signal to create it (see the `multi-agent-methodology` skill for the shape). The sprint-prep Methodology-Holds Walk then carries these forward with a forcing function — aged items get a schedule-or-justify binary, and accumulation triggers a hygiene-sprint proposal. The reflection surfaces; the registry remembers; sprint-prep forces the decision.

$ARGUMENTS
