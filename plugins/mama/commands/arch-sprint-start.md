---
description: Finalize sprint scope, write implementation plan, initialize log with kickoff section, and spawn the Implementor to begin work. One-shot sprint kickoff.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList, SendMessage
---

# Sprint Start

You are the **Architect Agent** (team lead). You and the user have aligned on the sprint scope. This command finalizes the sprint artifacts and spawns the Implementor to begin work — one continuous flow, no separate handoff command.

In MAMA, there is no separate Implementor brief document. The orientation work that briefs used to do in MAM is now done by the **spawn prompt** itself, which is recorded in the implementation log's "Sprint Kickoff" section as the durable record.

## Your Task

### 1. Confirm Final Scope

Briefly restate the agreed scope to ensure alignment.

### 2. Determine MAMA Scope and Artifact Paths

Check which `.mama` directory this project uses:
- `.mama/` (unscoped, single-product)
- `.mama-{scope}/` (scoped, multi-product)

Based on your MAMA scope, determine artifact paths:
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
- Include design constraints the Implementor must respect (these used to live in the brief — now they live in the plan where they belong)
- See the template in the multi-agent-methodology skill for structure

### 4. Compose the Spawn Prompt

Write the spawn prompt you'll send to the Implementor. This is the orientation artifact — the thing that used to be split between a "brief document" and a "kickoff message." Now it's a single load-bearing piece.

A good spawn prompt covers:
- **Identity and sprint number**: "You are the Implementor for Sprint X."
- **State directory path**: where `implementor_state.md` lives (e.g., `.mama/` or `.mama-backend/`)
- **Reading order**: state doc first (if exists), then plan, then log
- **Why this sprint matters**: 1–2 sentences of framing — the rationale that doesn't fit in the plan
- **Sprint-specific patterns or constraints**: curated subset of CLAUDE.md patterns that are especially relevant here, plus any decisions the user made during discussion that should be respected (e.g., "we settled on Pydantic v2, not v1")
- **Communication norms**: when to message you back vs. proceed independently
- **Exit conditions**: what "done" looks like for this sprint

Aim for substantive but tight — a few hundred words. The Implementor reads this once at startup and references it throughout, so it pays back the effort.

### 5. Initialize Implementation Log with Kickoff Section

Create `docs/sprint/X/implementation_log.md` (or scoped equivalent). The log starts with a `## Sprint Kickoff` section containing **the spawn prompt verbatim**, followed by the standard log structure (sprint metadata, phase progress table, session log placeholder).

The kickoff section is the durable record of how this sprint was framed. Sprint N+10 may want to look back and ask "why did Sprint X do it this way?" — the kickoff section answers that.

Use the implementation log template from the multi-agent-methodology skill as a structural reference; insert the `## Sprint Kickoff` section at the top with your spawn prompt content.

### 6. Quality Check

Before moving to spawn, verify:
- [ ] Implementation plan covers all agreed scope
- [ ] Phases are logical and appropriately sized
- [ ] Spawn prompt provides sufficient orientation (rationale, patterns, constraints, exit conditions)
- [ ] Log initialized with kickoff section containing the spawn prompt
- [ ] All relevant deltas are referenced in the plan
- [ ] Sprint directory created at the correct path

### 7. Ensure Team Exists

If you haven't already created an agent team for this session, create one now. The team persists across sprints — you only need to create it once per session.

### 8. Create Phase Tasks

Read the implementation plan and create tasks in the shared task list for each implementation phase. This gives the Implementor a clear checklist and provides live visibility into progress.

For each phase in the plan, create a task with:
- **subject**: The phase name/goal
- **description**: Key deliverables and success criteria from the plan

### 9. Spawn the Implementor

Spawn the Implementor as a teammate using the `implementor` agent type, passing the spawn prompt you composed in step 4.

**Example spawn prompt:**

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

The state-loading instruction in the spawn prompt is critical — it tells the Implementor exactly which scoped state directory to read from, ensuring the right working knowledge is loaded in multi-product setups.

### 10. Monitor and Respond

After spawning:
- The Implementor will begin working through the plan
- It may message you with questions — respond efficiently so it can continue
- The user may interact with the Implementor directly for testing and feedback
- Monitor the shared task list for progress

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

## Spawn Prompt Guidelines

Good spawn prompts:
- Lead with identity and sprint context
- Direct the Implementor's reading order explicitly (state doc → plan → log)
- Carry the rationale ("why this sprint matters") in 1–2 sentences
- List sprint-specific patterns or constraints — curated, not exhaustive
- Set communication expectations (when to ping back, when to proceed)
- Define what "done" looks like
- Are substantive but tight — a few hundred words

The spawn prompt is the orientation artifact in MAMA. It's the kickoff record in the log, the first thing the Implementor reads, and the contract for how the sprint is framed. Invest in it accordingly.

## Begin

Create the implementation plan, compose the spawn prompt, initialize the log with the kickoff section, then spawn the Implementor to begin work.

$ARGUMENTS
