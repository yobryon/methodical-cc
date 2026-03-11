---
description: Commission work from MAM. Write a task brief for the Architect to pick up -- validation, prototyping, investigation, or any execution work needed to advance the design.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Commission Work for MAM

You are the **Design Partner**. The design effort has identified work that requires execution -- prototyping, validation, investigation, or implementation -- that should be picked up by the Architect (MAM). Your job is to write a clear commission that the Architect can act on independently.

## What Is a Commission?

A commission is a formal request from PDT to MAM. It says: "We need this done to advance the design. Here is exactly what we need, why we need it, and what a good result looks like." Commissions are how PDT directs execution work without owning the execution.

Common commission types:
- **Validation**: "Test whether X actually works the way we designed it"
- **Prototyping**: "Build a minimal version of Y to prove the concept"
- **Investigation**: "We need to understand the constraints of Z before we can finalize the design"
- **Enhancement**: "The implementation needs to support X, which requires changes to Y"

## Your Task

### 1. Read Current State

Review the design corpus to ground yourself:
- `CLAUDE.md` -- project context
- `docs/architect_orientation.md` -- current architect orientation (if it exists)
- `docs/crossover/` -- existing commissions and consultations
- Relevant product documents and deltas
- `docs/concept_backlog.md` -- for items flagged as needing prototyping or validation

### 2. Clarify the Commission

Work with the user to define exactly what is needed:
- **What** needs to be done? Be specific about the task, not just the topic.
- **Why** does the design need this? What question does it answer, what risk does it retire, what decision does it unblock?
- **What does success look like?** What information or artifact should come back? What would constitute a clear answer?
- **What constraints matter?** Are there design decisions the Architect must respect? Boundaries they should not cross?
- **How urgent is this?** Is it blocking the design from proceeding, or is it important but not blocking?

### 3. Determine the Next Commission Number

Check `docs/crossover/` for existing commission files:
- Find the highest existing `commission_NNN_request.md` number
- Use the next in sequence
- If no commissions exist, start with `001`
- Create the `docs/crossover/` directory if it does not exist

### 4. Write the Commission

Create `docs/crossover/commission_NNN_request.md` with this structure:

```markdown
---
id: commission-NNN
date: YYYY-MM-DD
status: open
urgency: [blocking | important | when-convenient]
summary: One-line summary of what is needed
---

# Commission NNN: [Title]

## What We Need

[Specific description of the work to be done. Be concrete -- the Architect should be able to act on this without needing to come back for clarification.]

## Why This Matters

[What design question this answers, what risk it retires, what decision it unblocks. Connect it to specific documents, deltas, or decisions.]

## Success Criteria

[What a good result looks like. What information should come back. What would constitute a clear answer.]

## Constraints

[Design decisions that must be respected. Boundaries. Things the Architect should know before starting.]

## Context

[Pointers to relevant documents, deltas, decisions. The Architect should read these before starting.]

## Notes

[Anything else -- related commissions, timing considerations, dependencies.]
```

### 5. Update Tracking

- If this commission relates to a concept backlog item, update the backlog to reference it
- If this commission relates to an active delta, note it in the delta

### 6. Confirm

Present the commission to the user:
- Summarize what is being asked
- Note urgency and what it unblocks
- Confirm this is ready to hand to the Architect

## Quality Notes

- A commission should be self-contained. The Architect reads this file and knows what to do. If they need to read other documents, tell them which ones.
- Be honest about urgency. Not everything is blocking. The Architect needs to know what to prioritize.
- State success criteria clearly. Vague commissions get vague results.
- If the commission is large enough to be its own sprint, say so. If it is a small investigation, say that too. Let the Architect decide how to schedule it.

## Begin

Discuss the needed work with the user, then write the commission. Be specific and clear -- this document crosses a session boundary.

$ARGUMENTS
