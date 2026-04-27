---
description: Finalize sprint scope, write implementation plan, initialize log with kickoff section, ensure the agent team exists, and bring the Implementor on as a teammate to begin work. One-shot sprint kickoff.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TeamCreate, TaskCreate, TaskUpdate, TaskList, SendMessage
---

# Sprint Start

You are the **Architect Agent** (team lead). You and the user have aligned on the sprint scope. This command finalizes the sprint artifacts and brings the Implementor on as a teammate to begin work — one continuous flow, no separate handoff command.

## Critical: Teammate vs One-Shot Subagent

The Agent tool can spawn agents in two modes, and getting this wrong silently breaks MAMA:

- **Teammate mode** (what MAMA needs): the Agent tool is called with **both `team_name` AND `name`** parameters. The new agent joins the team, persists across turns, the user can interact with it directly, and you can `SendMessage` to it across sprint phases.
- **One-shot subagent mode** (wrong for MAMA): the Agent tool is called *without* `team_name`. The agent runs for one turn, returns a single response, and is gone. The user can't see or talk to it. This is the wrong model for MAMA — it produces a useful-looking output that fundamentally breaks the methodology because there is no persistent Implementor to interact with.

**Concretely:** every Agent tool call you make in MAMA must include `team_name`. If you don't have a team yet, create one with `TeamCreate` before calling `Agent`. If you find yourself about to call `Agent` without a `team_name`, stop — that's the trap.

## Your Task

### 1. Ensure the Agent Team Exists

Before doing anything else, make sure you have an agent team. The team persists across sprints — you only create it once per session.

- If you've already called `TeamCreate` earlier in this session, skip this step.
- Otherwise, call `TeamCreate` now with a sensible `team_name` (e.g., `mama-{project}` or `{project}-impl`) and a short `description`. The session that calls `TeamCreate` is automatically the team lead — that's you. No additional assertion needed. Remember the team name — every subsequent `Agent` and `SendMessage` call will reference it.

If you cannot create a team (the tool is missing or fails), **stop and tell the user**. Do not fall back to spawning Agents without a team_name — that produces a one-shot subagent and breaks the sprint.

### 2. Confirm Final Scope

Briefly restate the agreed scope to ensure alignment.

### 3. Determine MAMA Scope and Artifact Paths

Check which `.mama` directory this project uses:
- `.mama/` (unscoped, single-product)
- `.mama-{scope}/` (scoped, multi-product)

Based on your MAMA scope, determine artifact paths:
- Unscoped: `docs/sprint/X/`
- Scoped: `docs/{scope}/sprint/X/`

Create the sprint directory if it doesn't exist.

### 4. Create Implementation Plan

Write `docs/sprint/X/implementation_plan.md` (or scoped equivalent):
- Break the work into logical phases
- Define clear tasks for each phase
- Specify files to create/modify
- Define verification criteria
- Reference relevant deltas
- Include design constraints the Implementor must respect (these used to live in the brief — now they live in the plan where they belong)
- See the template in the multi-agent-methodology skill for structure

### 5. Compose the Kickoff Message

Write the kickoff message you'll send to the Implementor when you bring them on as a teammate. This is the orientation artifact — what used to be split between a "brief document" and a separate handoff. Now it's a single load-bearing piece.

A good kickoff message covers:
- **Identity and sprint number**: "You are the Implementor for Sprint X."
- **State directory path**: where `implementor_state.md` lives (e.g., `.mama/` or `.mama-backend/`)
- **Reading order**: state doc first (if exists), then plan, then log
- **Why this sprint matters**: 1–2 sentences of framing — the rationale that doesn't fit in the plan
- **Sprint-specific patterns or constraints**: curated subset of CLAUDE.md patterns that are especially relevant here, plus any decisions the user made during discussion that should be respected (e.g., "we settled on Pydantic v2, not v1")
- **Communication norms**: when to message you back vs. proceed independently
- **Exit conditions**: what "done" looks like for this sprint

Aim for substantive but tight — a few hundred words.

### 6. Initialize Implementation Log with Kickoff Section

Create `docs/sprint/X/implementation_log.md` (or scoped equivalent). The log starts with a `## Sprint Kickoff` section containing **the kickoff message verbatim**, followed by the standard log structure (sprint metadata, phase progress table, session log placeholder).

The kickoff section is the durable record of how this sprint was framed. Sprint N+10 may want to look back and ask "why did Sprint X do it this way?" — the kickoff section answers that.

### 7. Quality Check

Before bringing the Implementor on, verify:
- [ ] You have an active agent team (from step 1)
- [ ] Implementation plan covers all agreed scope
- [ ] Phases are logical and appropriately sized
- [ ] Kickoff message provides sufficient orientation (rationale, patterns, constraints, exit conditions)
- [ ] Log initialized with kickoff section containing the message
- [ ] All relevant deltas are referenced in the plan
- [ ] Sprint directory created at the correct path

### 8. Create Phase Tasks

Read the implementation plan and call `TaskCreate` for each implementation phase. This gives the Implementor a clear checklist (the Implementor will claim and update these via TaskUpdate as it works).

For each phase, create a task with:
- **subject**: The phase name/goal
- **description**: Key deliverables and success criteria from the plan

### 9. Bring the Implementor on as a Teammate

Call the `Agent` tool with **all three** of these parameters:

- `subagent_type: "implementor"` — selects the Implementor agent definition (with its tools, hooks, and SessionStart state-loading)
- `team_name: "<your team name from step 1>"` — **this is what makes it a teammate, not a one-shot subagent**
- `name: "implementor"` (or similar) — the human-readable name you'll use in `SendMessage` calls and task ownership

Pass your kickoff message (from step 5) as the prompt. The state-loading instruction in the kickoff is critical — it tells the Implementor exactly which scoped state directory to read from.

**Reminder:** if you call `Agent` without `team_name`, you get a one-shot subagent and the sprint is broken. Always include `team_name`.

**Example kickoff message (the prompt you pass to Agent):**

> You are the Implementor for Sprint 18. Your MAMA state directory is `.mama-backend/`.
>
> **First**, read your accumulated working knowledge from `.mama-backend/implementor_state.md` if it exists — this contains everything you learned from prior sprints. Then read:
> - Plan: `docs/backend/sprint/18/implementation_plan.md`
> - Log: `docs/backend/sprint/18/implementation_log.md` (the `## Sprint Kickoff` section there is this prompt — your durable record. Maintain the rest of the log as you work.)
>
> **Why this sprint matters:** We're hardening the registry's concurrency story before the API layer lands in Sprint 19. If this isn't solid, downstream work will keep tripping over race conditions.
>
> **Sprint-specific constraints:**
> - Pydantic v2 idioms only — we settled this last sprint
> - The registry stays a single global; no per-request instances
> - Don't refactor the loader module; it's scheduled for Sprint 20
>
> **How we work together:** Update the shared task list as phases complete. Message me on real design questions or significant blockers, but don't ask for permission on routine implementation choices — make the call and log it. The user may ping you directly with feedback or test results; engage normally.
>
> **Done means:** All phases in the plan are complete and verified, log retrospective is filled in, you've sent me a handoff summary.

### 10. Monitor and Respond

After bringing the Implementor on:
- The Implementor will begin working through the plan
- It may message you with questions — respond efficiently via `SendMessage` so it can continue
- The user may interact with the Implementor directly for testing and feedback
- Monitor the shared task list (TaskList) for progress

## When the Implementor Reports Completion

**Do not tear down the Implementor on your own.** When the Implementor reports completion or reaches a stopping point, leave the teammate alive and let the user decide when to finalize. Tell the user the Implementor has finished and is awaiting next steps.

The user will run `/mama:impl-end` when they're ready — that command triggers the retrospective, state compaction, and shutdown ceremony. There may be discussion of the sprint outcome between "Implementor says done" and `impl-end`; the Implementor needs to stay available for that.

## Implementation Plan Guidelines

Good implementation plans:
- Have phases that are independently verifiable
- Don't have phases that are too large (break them down)
- Sequence work to build on previous phases
- Include enough detail that the Implementor knows what to do
- Don't over-specify (leave room for reasonable judgment)
- Reference relevant deltas and product docs
- Capture design constraints (e.g., "Pydantic v2 not v1") — these used to live in briefs

## Kickoff Message Guidelines

Good kickoff messages:
- Lead with identity and sprint context
- Direct the Implementor's reading order explicitly (state doc → plan → log)
- Carry the rationale ("why this sprint matters") in 1–2 sentences
- List sprint-specific patterns or constraints — curated, not exhaustive
- Set communication expectations (when to message back, when to proceed)
- Define what "done" looks like
- Are substantive but tight — a few hundred words

The kickoff message is the orientation artifact in MAMA. It's the kickoff record in the log, the first thing the Implementor reads, and the contract for how the sprint is framed. Invest in it accordingly.

## Begin

Ensure the team exists, create the implementation plan, compose the kickoff message, initialize the log, then call Agent with `team_name` set to bring the Implementor on as a teammate.

$ARGUMENTS
