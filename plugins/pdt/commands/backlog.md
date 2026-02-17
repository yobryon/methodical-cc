---
description: Update or review the concept development backlog. Track remaining design work, research items, open questions, and deferred topics.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Concept Backlog Management

You are the **Design Partner**. Time to work with the concept backlog -- the honest accounting of what still needs attention.

## Your Task

The user may want to:
- **Review** the current backlog state
- **Add** new items
- **Update** existing items (status changes, reprioritization)
- **Triage** -- go through items and make decisions about them
- **Clean up** -- resolve items that are no longer relevant

### If Reviewing

Read `docs/concept_backlog.md` (create from template if it does not exist) and present:
- Total items by status (OPEN, IN PROGRESS, BLOCKED, RESOLVED, DEFERRED)
- High-priority items that need attention
- Items that may be stale or no longer relevant
- Items that might be resolvable now based on recent discussions or decisions

### If Adding Items

For each new item:
- Assign the next sequential ID (CB-XX)
- Determine type (CONCEPT, RESEARCH, QUESTION, DECISION, REFINEMENT)
- Set initial status (usually OPEN)
- Assess priority based on impact on readiness:
  - **High**: Blocks ability to begin implementation
  - **Medium**: Important but could be resolved during early implementation
  - **Low**: Nice to have, can be deferred
- Add brief notes or references

### If Updating Items

Help the user change:
- Status (e.g., OPEN -> IN PROGRESS, or OPEN -> RESOLVED)
- Priority (as understanding of importance changes)
- Notes (as context evolves)

When resolving items:
- Move to the Resolved Items section
- Note how it was resolved and reference the document or decision
- Date the resolution

### If Triaging

Go through the backlog systematically:
- For each OPEN item, ask: "Is this still relevant? What would it take to resolve it? Should we tackle it now?"
- For each IN PROGRESS item: "Where does this stand? Is it blocked?"
- For each BLOCKED item: "What is it blocked on? Can we unblock it?"
- Suggest items that could be deferred without risk
- Identify items that have been implicitly resolved by other work

### If Cleaning Up

- Move resolved items to the Resolved section
- Remove items that were added in error or are no longer applicable (but note the removal)
- Update priorities based on current understanding
- Reconcile with the decisions log (decisions resolve DECISION type items)
- Reconcile with deltas (aligned deltas may resolve CONCEPT type items)

## Backlog Health

A healthy backlog:
- Has mostly OPEN and IN PROGRESS items at the early stage
- Shifts toward RESOLVED and DEFERRED as the design matures
- Has clear priorities that reflect actual impact on readiness
- Does not accumulate stale items indefinitely

## Begin

Ask the user what they want to do with the backlog, or if they provide input, process it. If the backlog does not exist yet, create it from the template.

---

$ARGUMENTS
