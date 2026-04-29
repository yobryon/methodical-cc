---
description: Send a commission to MAM/MAMA via the bus. Compose a task brief — validation, prototyping, investigation, or any execution work needed to advance the design — and dispatch it to the Architect.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Commission Work for the Architect

You are the **Design Partner**. The design effort has identified work that requires execution — prototyping, validation, investigation, or implementation — that should be picked up by the Architect (running MAM or MAMA). Compose a clear commission and send it via the bus.

## Prerequisites

- The bus plugin must be installed and enabled (`mcc bus setup` if unsure)
- An Architect session must be registered as `arch` (or the appropriate identity name) — verify with `peer_list`
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
- `CLAUDE.md` — project context
- `docs/architect_orientation.md` — current architect orientation (if it exists)
- `docs/crossover/` — existing commission and consult threads (each in its own subdirectory)
- Relevant product documents and deltas
- `docs/concept_backlog.md` — for items flagged as needing prototyping or validation

### 2. Clarify the Commission

Work with the user to define exactly what is needed:
- **What** needs to be done? Be specific about the task, not just the topic.
- **Why** does the design need this? What question does it answer, what risk does it retire, what decision does it unblock?
- **What does success look like?** What information or artifact should come back? What would constitute a clear answer?
- **What constraints matter?** Are there design decisions the Architect must respect? Boundaries they should not cross?
- **How urgent is this?** Is it blocking the design from proceeding, or important but not blocking?

### 3. Decide on Thread ID

Pick a kebab-case thread ID describing the commission, e.g. `commission-013-pref-storage-validation`. Each commission is typically its own thread (commissions are discrete tasks, not ongoing conversations).

### 4. Compose the Commission and Send via Bus

Compose the **artifact body** (the substantive commission the Architect will act on):

```markdown
# Commission: [Title]

## What We Need

[Specific description of the work to be done. Be concrete — the Architect should be able to act on this without needing to come back for clarification.]

## Why This Matters

[What design question this answers, what risk it retires, what decision it unblocks. Connect it to specific documents, deltas, or decisions.]

## Success Criteria

[What a good result looks like. What information should come back. What would constitute a clear answer.]

## Constraints

[Design decisions that must be respected. Boundaries. Things the Architect should know before starting.]

## Context

[Pointers to relevant documents, deltas, decisions. The Architect should read these before starting.]

## Notes

[Anything else — related commissions, timing considerations, dependencies, urgency.]
```

Compose a short **body** (channel-notification framing):

```
Arch — sending commission-013-pref-storage-validation. We need a quick prototype to test whether normalized vs JSON-blob storage actually behaves differently at expected scale. Blocking the User-prefs design decision in delta_07. See artifact for success criteria and constraints. Important but not urgent — schedule when natural.
```

Then call `peer_send`:

```
peer_send(
  to="arch",
  body="<the framing above>",
  mode="consult",
  thread_id="commission-013-pref-storage-validation",
  artifact_body="<the structured commission above>",
  artifact_type="commission"
)
```

### 5. Update Tracking

- If this commission relates to a concept backlog item, update the backlog to reference the thread ID
- If this commission relates to an active delta, note the thread ID in the delta

### 6. Confirm

Tell the user:
- Summarize what was asked and the thread ID
- Note urgency and what it unblocks
- The artifact landed at `docs/crossover/{thread_id}/001-pdt-commission.md`
- The Architect will see the message when their session is active

## Quality Notes

- A commission should be self-contained. The Architect reads this artifact and knows what to do. If they need to read other documents, tell them which ones.
- Be honest about urgency. Not everything is blocking. The Architect needs to know what to prioritize.
- State success criteria clearly. Vague commissions get vague results.
- If the commission is large enough to be its own sprint, say so. If it's a small investigation, say that too. Let the Architect decide how to schedule it.

## Begin

Discuss the needed work with the user, then compose and send the commission via the bus.

$ARGUMENTS
