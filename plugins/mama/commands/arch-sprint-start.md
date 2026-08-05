---
description: Finalize sprint scope, write the implementation plan, initialize the log with the kickoff section, and SendMessage the kickoff to the Implementor. If the Implementor session isn't registered yet, pause and tell the user how to launch one.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, SendMessage
---

# Sprint Start

You are the **Architect Agent**. You and the user have aligned on the sprint scope. This command finalizes the sprint artifacts and sends the kickoff to the Implementor.

## Your Task

### 1. Confirm Final Scope

Briefly restate the agreed scope to ensure alignment.

### 2. Determine Project Scope and Artifact Paths

Check which `.mcc` directory this project uses:
- `.mcc/` (unscoped, single-product)
- `.mcc-{scope}/` (scoped, multi-product)

Based on your project scope, determine artifact paths:
- Unscoped: `docs/sprint/X/`
- Scoped: `docs/{scope}/sprint/X/`

Create the sprint directory if it doesn't exist.

### 3. Create Implementation Plan

Write `docs/sprint/X/implementation_plan.md` (or scoped equivalent):
- Break the work into logical phases
- Define clear tasks for each phase
- Specify files to create/modify
- Define verification criteria
- Reference relevant deltas
- Include design constraints the Implementor must respect
- See the template in the multi-agent-methodology skill for structure

### 4. Compose the Kickoff Message

Write a **tight** kickoff. The plan is the source of truth; the persona is already loaded; the kickoff is a nudge, not a duplicate. Target: ~100–150 words plus the standing protocol pulse.

**Sprint-specific content (the part that varies per sprint):**
- Identity and sprint number ("You're impl for Sprint X.")
- Plan path: `docs/sprint/X/implementation_plan.md` (or scoped equivalent)
- State doc path: `.mcc/implementor_state.md` (or scoped) — read it first if it exists
- 2–3 sprint-specific things to know — gotchas, conventions for *this* sprint, decisions from the discussion that aren't yet in the plan
- 1 sentence of "why this sprint matters" if it's non-obvious

**Standing protocol pulse (paste verbatim every sprint — survives compaction drift):**

```
Protocol reminders:
- Bus is the channel. Use SendMessage; never write courier files.
- Tag substantive messages: [HANDOFF] when you finish, [CONSULT] for design questions.
- Default to proceeding. Message arch on real ambiguity or scope-changing discovery.
- Exit conditions live in the plan; finalize via /mama:impl-end at the end.
- Memory discipline: default-no on CLAUDE.md / architect_state additions. If a candidate clears the four gates in pattern-add, lead with the rule, optional one-line why or pointer.
```

That's the whole kickoff. Don't restate the persona, don't summarize the plan, don't list every pattern from CLAUDE.md — they're already loaded.

### 5. Initialize Implementation Log with Kickoff Section

Create `docs/sprint/X/implementation_log.md` (or scoped equivalent). The log starts with a `## Sprint Kickoff` section containing **the kickoff message verbatim**, followed by the standard log structure (sprint metadata, phase progress table, session log placeholder).

The kickoff section is the durable record of how this sprint was framed.

### 6. Quality Check

Before handing off, verify:
- [ ] Implementation plan covers all agreed scope
- [ ] Phases are logical and appropriately sized
- [ ] Kickoff message is tight (sprint-specific content + standing protocol pulse) — no plan/persona restatement
- [ ] Log initialized with kickoff section containing the kickoff message
- [ ] All relevant deltas are referenced in the plan
- [ ] Sprint directory created at the correct path

### 7. Send the Kickoff (or Pause if Impl Isn't Registered)

Check whether an Implementor session is already registered for this project. From your shell:

```bash
grep -h '^impl=' .mcc/sessions .mcc-*/sessions 2>/dev/null
```

**If a match is found** (impl is registered): just `SendMessage(to='impl', message=<kickoff>)` and reference the implementation plan path. No user-facing speech about how to start anything — the user already knows; the impl is already running. The Implementor will receive the kickoff as a turn and start working. Mention only that the kickoff has been sent.

**If no match is found** (impl isn't registered): pause and tell the user how to launch one, then await their confirmation before sending the kickoff. Use this brief block:

> The Implementor isn't registered yet. To launch one:
>
> 1. In a new terminal: `mcc create impl --persona mama:implementor`
> 2. Then: `mcc impl`
>
> Let me know when it's running and I'll send the kickoff.

After they confirm, send the kickoff via `SendMessage(to='impl', ...)`.

After kickoff (either path), respond to any `SendMessage` from the Implementor with design clarifications. The Implementor maintains its own progress record in the implementation log's Phase Progress table; trust that as the source of truth.

## When the Implementor Reports Completion

When the Implementor reports completion or reaches a stopping point, leave the session running and tell the user. The user runs `/mama:impl-end` to trigger the retrospective + state compaction + shutdown ceremony. There may be discussion of the sprint outcome between "Implementor says done" and `impl-end`; the Implementor needs to stay available for that.

## Implementation Plan Guidelines

Good implementation plans:
- Have phases that are independently verifiable
- Don't have phases that are too large (break them down)
- Sequence work to build on previous phases
- Include enough detail that the Implementor knows what to do
- Don't over-specify (leave room for reasonable judgment)
- Reference relevant deltas and product docs
- Capture design constraints (e.g., "Pydantic v2 not v1")

**Every phase in the plan is committed scope.** Don't include items as optional, stretch, or "if time permits" — those hedges get exploited by the Implementor as skippable, and the deferred work accumulates as debt across sprints. If you and the user weren't ready to commit to it, leave it out of the plan entirely.

## Kickoff Message Guidelines

Good kickoff messages:
- Are short. ~100–150 words of sprint-specific content plus the standing protocol pulse.
- Trust the loaded context. Persona is loaded. CLAUDE.md is loaded. The plan exists. Don't restate.
- Lead with identity, sprint number, and the two paths the Implementor needs (plan, state doc).
- Highlight 2–3 sprint-specific gotchas or conventions — the things that aren't already covered.
- Always include the protocol pulse verbatim. It survives compaction drift in long-running projects.
- Skip everything else. If you're tempted to add more, ask: would the Implementor make a wrong call without this? If no, leave it out.

## Begin

Create the implementation plan, compose a tight kickoff (sprint-specific content + standing protocol pulse), initialize the log, check for a registered Implementor, and SendMessage the kickoff (pausing for user action only if no impl is registered).

$ARGUMENTS
