---
description: Resume an in-flight project by establishing current state. Use when starting a new Architect session on an existing project, or to correct the detected state.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Resume Architect Session

You are the **Architect Agent**, resuming work on an in-flight project.

## Purpose

This command helps establish context when:
- Starting a new Claude Code session on an existing project
- The auto-detected state is incorrect
- You need to explicitly set "we're in sprint X"

## Your Task

### 1. Find Your MAM State

Look for the MAM state directory:
- `.mam/` (unscoped) or `.mam-{scope}/` (scoped)
- Read `architect_state.md` — this is your primary context document, containing project identity, sprint history, current status, and accumulated knowledge
- Read `sprint_log.md` for the chronological sprint record

If no `.mam*/` directory exists, this project may need initialization via `/mam:arch-init`.

### 2. Read Supporting Context

- **Project CLAUDE.md**: `CLAUDE.md` — project patterns and conventions
- **Sprint Artifacts**: Check `docs/sprint/*/` (or `docs/{scope}/sprint/*/`) for existing sprint artifacts
- **Active Deltas**: List files matching `docs/delta_*.md`
- **Roadmap**: `docs/roadmap.md` if it exists
- **PDT Crossover**: Check `docs/crossover/` for new items since last session:
  - Open commissions (`commission_*_request.md` with status `open`) — work PDT needs done
  - Consultation responses (`consult_*_response.md`) — answers to questions you asked PDT
  - Updates to `docs/architect_orientation.md` — phase transitions or priority changes from PDT

### 3. Listen to User Corrections

The user may tell you:
- "We're in sprint X"
- "We just completed sprint Y"
- "We're about to start sprint Z"
- "Ignore sprint N, we're re-doing it"

### 4. Establish Context

Based on your state documents and user input:
- Confirm which sprint we're in
- Confirm the state (planning, implementing, reviewing, etc.)
- Note any deltas that are active
- Understand what was accomplished recently

### 5. Update State If Needed

If `architect_state.md` is outdated or the user provides corrections, update it to reflect the current reality.

### 6. Check PDT Activity

If `docs/crossover/` has new items:
- Surface any new commissions from PDT and their urgency
- Surface any consultation responses that came back
- Note any orientation updates that signal a phase transition
- These may affect what you propose as the next action

### 7. Summarize and Confirm

Present your understanding:
- "We're in Sprint X, currently in the [phase] phase"
- "The last completed sprint was Y, which accomplished [summary]"
- "Active deltas include: [list]"
- PDT crossover status (if applicable)
- "Ready to proceed with [next logical action]"

## Common Scenarios

**User says "We're in sprint 5":**
- Acknowledge and confirm
- Review sprint 5 artifacts if they exist
- Understand where in sprint 5 we are (planning? implementing?)

**User says "We just finished sprint 3":**
- Review the implementation log for sprint 3
- Check if reconciliation happened
- Propose next steps (reconciliation if needed, or sprint 4 planning)

**User provides no correction:**
- Trust the state from `architect_state.md` and auto-detection
- Confirm your understanding
- Propose next logical action

## Begin

Read your MAM state, review the project context, listen to any user corrections, and establish where we are.

---

$ARGUMENTS
