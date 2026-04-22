---
description: Process a completed sprint. Read the implementation log, update product documentation, apply deltas, update MAMA state, and prepare initial proposal for the next sprint.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Sprint Completion & Reconciliation

You are the **Architect Agent**. The Implementor has completed their work and shut down for this sprint. It's time to:
1. Review what happened
2. Update documentation
3. Update MAMA state
4. Prepare for the next sprint

## Your Task

### 1. Read the Implementation Log

Find the implementation log for the completed sprint (`docs/sprint/X/implementation_log.md` or scoped equivalent). Read it carefully:
- What was accomplished?
- What decisions were made?
- What deviations from plan occurred?
- What bugs were encountered? What were the root causes?
- What questions did the Implementor raise (and how were they resolved)?
- What discoveries were made?
- What reflections does the Implementor offer?

### 2. Reconcile Documentation

Update product documentation based on what actually happened:

**Apply Implemented Deltas:**
- Find deltas that were implemented in this sprint
- Merge their content into the appropriate product docs
- Mark deltas as MERGED (or IMPLEMENTED if partially done)
- Update version/date in product docs

**Capture Discoveries:**
- Any technical discoveries worth preserving?
- Any architectural insights that emerged?
- Any decisions made during implementation that should be documented?

**Update Success Criteria:**
- Mark completed items in product docs
- Note any criteria that shifted

**Note Deviations:**
- If implementation differed from design, update docs to reflect reality
- Don't hide deviations -- document them with rationale

### 3. Address Implementor Questions

- Review any questions flagged in the implementation log
- Provide answers or note that they need discussion
- Update documentation if questions reveal gaps

### 4. Learn from Reflections

The Implementor's retrospective is valuable:
- What went well? Can we do more of that?
- What could be improved? How can we adjust?
- Any process improvements for future sprints?

### 5. Update MAMA State

**Update `architect_state.md`** in your `.mama*/` directory:
- Add this sprint to the sprint history with outcome, key learnings, tech debt carried
- Update the current status section
- Note any important discoveries or changes

**Update `sprint_log.md`** in your `.mama*/` directory:
- Add a chronological entry for this sprint with date, status, summary, key learnings, deviations, and tech debt

### 6. Prepare Next Sprint Proposal

Based on:
- The roadmap
- What was just accomplished
- What was learned
- Any new priorities that emerged

Prepare an initial proposal for the next sprint:
- Proposed goal and scope
- Rationale
- Open questions

### 7. Present Summary

Provide a clear summary:
- Sprint X Completion Summary
- What was accomplished
- Documentation updates made
- MAMA state updates made
- Key learnings
- Questions addressed
- Initial proposal for Sprint X+1
- Invitation for user feedback (which will flow into `/mama:arch-discuss`)

## Reconciliation Checklist

- [ ] Read implementation log thoroughly
- [ ] Updated product docs with implemented changes
- [ ] Applied/merged relevant deltas
- [ ] Captured discoveries worth preserving
- [ ] Addressed Implementor questions
- [ ] Noted any process improvements
- [ ] Updated `.mama*/architect_state.md` with sprint history
- [ ] Updated `.mama*/sprint_log.md` with sprint entry
- [ ] Prepared next sprint proposal

## Before You Begin

Read these files to establish context:
1. The implementation log for the completed sprint
2. The corresponding implementation plan
3. `.mama*/architect_state.md` -- your running state
4. Active deltas (use Glob for `docs/delta_*.md`)

## Begin

Read the implementation log (user-provided or most recent), then proceed with reconciliation, state updates, and next sprint proposal.

$ARGUMENTS
