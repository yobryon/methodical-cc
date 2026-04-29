---
description: Send a commission to MAM/MAMA via the bus. Compose a task brief — validation, prototyping, investigation, or any execution work needed to advance the design — and dispatch it to the Architect.
allowed-tools: Read, Write, Edit, Glob, Grep, SendMessage
---

# Commission Work for the Architect

You are the **Design Partner**. The design effort has identified work that requires execution — prototyping, validation, investigation, or implementation — that should be picked up by the Architect (running MAM or MAMA). Compose a clear commission and send it via the bus.

## Prerequisites

- The bus plugin must be enabled and the project's team set up (`mcc team setup` or any `mcc <name>` does this)
- An Architect session must be registered as `arch` (or whatever name was established) — check the SessionStart bus block for current members
- If the Architect isn't running right now, the message still queues for them

## What Is a Commission?

A commission is a formal request from PDT to the Architect. It says: "We need this done to advance the design. Here is exactly what we need, why we need it, and what a good result looks like." Commissions are how PDT directs execution work without owning the execution.

Common commission types:
- **Validation**: "Test whether X actually works the way we designed it"
- **Prototyping**: "Build a minimal version of Y to prove the concept"
- **Investigation**: "We need to understand the constraints of Z before we can finalize the design"
- **Enhancement**: "The implementation needs to support X, which requires changes to Y"

## Your Task

### 1. Read Current State

Review the design corpus to ground yourself:
- `CLAUDE.md`
- `docs/architect_orientation.md` (if it exists)
- `docs/crossover/` — existing commission and consult threads
- Relevant product documents and deltas
- `docs/concept_backlog.md` — for items flagged as needing prototyping or validation

### 2. Clarify the Commission

Work with the user to define exactly what is needed:
- **What** needs to be done? Be specific about the task, not just the topic.
- **Why** does the design need this? What question does it answer, what risk does it retire, what decision does it unblock?
- **What does success look like?** What information or artifact should come back?
- **What constraints matter?**
- **How urgent is this?**

### 3. Decide on Thread ID

Pick a kebab-case thread ID, e.g. `commission-013-pref-storage-validation`. Each commission is typically its own thread.

### 4. Write the Commission Artifact

Use the `Write` tool to create `docs/crossover/{thread_id}/001-pdt-commission.md`:

```markdown
---
thread_id: {thread_id}
turn: 1
type: commission
from: pdt
to: arch
sent_at: {ISO timestamp}
status: open
---

# Commission: [Title]

## What We Need
[Specific description of the work. Be concrete — the Architect should be able to act without coming back for clarification.]

## Why This Matters
[What design question this answers. Connect to specific documents, deltas, or decisions.]

## Success Criteria
[What a good result looks like.]

## Constraints
[Design decisions to respect. Boundaries.]

## Context
[Pointers to relevant documents. The Architect should read these before starting.]

## Notes
[Related commissions, timing, dependencies, urgency.]
```

### 5. Send the Bus Message

Compose a framing message and use `SendMessage`:

```
SendMessage(
  to="arch",
  message="[CONSULT] commission-013-pref-storage-validation\n\nCommission for prototype validation. We need to test whether normalized vs JSON-blob storage actually behaves differently at expected scale. Blocking the User-prefs design decision in delta_07. See docs/crossover/commission-013-pref-storage-validation/001-pdt-commission.md for success criteria and constraints. Important but not urgent — schedule when natural."
)
```

### 6. Update Tracking

- If this commission relates to a concept backlog item, update the backlog to reference the thread ID
- If this commission relates to an active delta, note the thread ID in the delta

### 7. Confirm

Tell the user:
- Summarize what was asked and the thread ID
- Note urgency and what it unblocks
- The Architect will see the message when their session is active

## Quality Notes

- A commission should be self-contained. The Architect reads this artifact and knows what to do.
- Be honest about urgency. Not everything is blocking.
- State success criteria clearly. Vague commissions get vague results.
- If the commission is large enough to be its own sprint, say so. If it's a small investigation, say that too.

## Begin

Discuss the needed work with the user, then compose and send the commission via the bus.

$ARGUMENTS
