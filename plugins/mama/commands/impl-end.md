---
description: Have the Implementor finalize their work with a retrospective, write their persistent state document, and shut down.
allowed-tools: Read, Write, Edit, Glob, Grep, SendMessage, TaskList, TaskUpdate
---

# Finalize Implementation

You are the **Architect Agent** (team lead). The Implementor has completed (or reached a stopping point on) the sprint work. Now have them finalize, write their persistent state, and shut down.

## Your Task

### 1. Send Finalization Message

Send a message to the Implementor teammate requesting finalization. Include:

**Implementation log completion:**
- Updated status for all phases
- Any missing decision logs or deviations
- A retrospective section covering:
  - What went well
  - What could be improved
  - Technical debt introduced
  - Recommendations for future sprints
- A clear handoff summary

**State document update:**
- Tell the Implementor to write/update their state document at `{mama_dir}/implementor_state.md`
- If a prior state document exists, re-read it first, then rewrite it incorporating new knowledge
- If this is the first sprint, write it from scratch
- The state document should capture **tacit knowledge** — what they learned that can't be recovered from CLAUDE.md, the doc tree, the Architect briefing, or re-reading the code. Focus areas: why the codebase is built this way, project history and load-bearing lessons (including approaches tried and abandoned), empirical findings from real runs, known gotchas, how the user works, and current trajectory.
- Emphasize: this is compaction, not accumulation — rewrite, don't append; keep it readable in under 5 minutes. Don't duplicate what's already in CLAUDE.md or docs/. Prune superseded empirical data (calibration numbers have half-lives); carry forward history and rationale.

**Example message to Implementor:**

> Finalize your implementation work:
>
> 1. Complete your implementation log with phase statuses, deviations, and a retrospective (what went well, what was hard, tech debt, recommendations)
>
> 2. Write your state document at `.mama/implementor_state.md`. If a prior version exists, re-read it first. Then rewrite it as a fresh compaction of your **tacit knowledge** — what you learned that can't be recovered from CLAUDE.md, the doc tree, or re-reading the code. Focus on: why the codebase is built this way, project history and load-bearing lessons (including approaches tried and abandoned), empirical findings, known gotchas, how the user works. Prune stale empirical data; carry forward history and rationale. Keep it readable in under 5 minutes.
>
> 3. Send me your handoff summary when done.

### 2. Review Handoff

When the Implementor responds with their handoff summary:
- Note overall status
- Note key accomplishments
- Note questions or concerns flagged
- Note tech debt introduced

### 3. Verify Outputs

Check that the Implementor produced:
- [ ] Finalized implementation log with retrospective
- [ ] Updated `{mama_dir}/implementor_state.md`
- [ ] All phase tasks marked complete (or appropriately noted)

### 4. Request Shutdown

Once satisfied with the finalization outputs, ask the Implementor to shut down. The team stays alive -- only the Implementor shuts down for this sprint.

### 5. Next Steps

After the Implementor shuts down:
- Review the implementation log in detail
- Proceed to `/mama:arch-sprint-complete` to reconcile documentation

## Begin

Send the finalization message to the Implementor teammate, then guide the process through to shutdown.

$ARGUMENTS
