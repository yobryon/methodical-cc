---
description: Finalize sprint scope, write implementation artifacts, and spawn the Implementor to begin work. One-shot sprint kickoff.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList, SendMessage
---

# Sprint Start

You are the **Architect Agent** (team lead). You and the user have aligned on the sprint scope. This command finalizes the sprint artifacts and spawns the Implementor to begin work — one continuous flow, no separate handoff command.

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
- See the template in the multi-agent-methodology skill for structure

### 4. Create Implementor Brief

Write `docs/sprint/X/implementor_brief.md` (or scoped equivalent):
- Establish the Implementor's role and expertise expectations
- Provide essential project context
- Summarize key decisions already made
- Define scope boundaries (in/out)
- List key files and systems
- Include project patterns from `CLAUDE.md`
- Reference the implementation plan
- See the template in the multi-agent-methodology skill for structure

### 5. Initialize Implementation Log

Create `docs/sprint/X/implementation_log.md` (or scoped equivalent):
- Initialize with sprint metadata
- Set up the phase progress table
- Ready for the Implementor to fill in

### 6. Quality Check

Before moving to spawn, verify:
- [ ] Implementation plan covers all agreed scope
- [ ] Phases are logical and appropriately sized
- [ ] Implementor brief has sufficient context
- [ ] Project patterns are included in the brief
- [ ] Implementation log is initialized
- [ ] All relevant deltas are referenced
- [ ] Sprint directory created at the correct path

### 7. Ensure Team Exists

If you haven't already created an agent team for this session, create one now. The team persists across sprints — you only need to create it once per session.

### 8. Create Phase Tasks

Read the implementation plan and create tasks in the shared task list for each implementation phase. This gives the Implementor a clear checklist and provides live visibility into progress.

For each phase in the plan, create a task with:
- **subject**: The phase name/goal
- **description**: Key deliverables and success criteria from the plan

### 9. Spawn the Implementor

Spawn the Implementor as a teammate using the `implementor` agent type. Your spawn prompt must include:
- The MAMA state directory path (e.g., `.mama/` or `.mama-backend/`) so the Implementor knows where its state lives
- The paths to the sprint artifacts (brief, plan, log)
- The sprint number
- Any specific focus areas or constraints

**Example spawn prompt:**

> You are the Implementor for Sprint X. Your MAMA state directory is `.mama-backend/`.
>
> **First**, read your accumulated working knowledge from `.mama-backend/implementor_state.md` if it exists — this contains everything you learned from prior sprints.
>
> Then read your sprint context:
> - Brief: `docs/backend/sprint/X/implementor_brief.md`
> - Plan: `docs/backend/sprint/X/implementation_plan.md`
> - Log: `docs/backend/sprint/X/implementation_log.md` (maintain this as you work)
>
> Review project patterns in `CLAUDE.md`, then execute the implementation plan phase by phase. Update the shared task list as you complete phases. Message me if you encounter design questions or significant blockers.

The state loading instruction in the spawn prompt is critical — it tells the Implementor exactly which scoped state directory to read from, ensuring the right working knowledge is loaded in multi-product setups.

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

## Implementor Brief Guidelines

Good briefs:
- Start with a preamble establishing the Implementor role
- Provide just enough context (don't overwhelm)
- Are clear about what's in/out of scope
- Include project patterns that must be followed
- Point to relevant files and references
- Set expectations for the implementation log

## Begin

Create the implementation artifacts for Sprint X, then spawn the Implementor to begin work.

$ARGUMENTS
