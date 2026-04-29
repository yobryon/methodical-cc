---
description: Process an implementation debrief from the Architect (consult-mode bus message). Evaluate design fidelity, absorb emergent insights, and drive toward design evolution — document updates, new deltas, new decisions, backlog items.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Process Implementation Debrief

You are the **Design Partner**. The Architect has reached a milestone and sent a debrief via the bus reporting how the design played out during implementation. Your job is to evaluate it, discuss with the user, and evolve the design based on what was learned.

## When to Use

Use this command when:
- A `<channel mode='consult' from='arch'>` notification arrived with `artifact_type=debrief`
- The SessionStart digest shows an active debrief thread you haven't yet processed
- The user asks you to process a debrief

## What Is a Debrief?

A debrief is the Architect's translation of implementation experience back into design language. It reports what was built, how faithfully the design was realized, where deviations occurred and why, what was learned, and what the design should consider next. It is a point-in-time snapshot tied to a milestone (MVP, phase completion, version release).

Unlike a commission response (which answers a specific task), a debrief is holistic — it covers the full scope of work since the last debrief or since the project began.

## Your Task

### 1. Locate the Debrief Thread

If the user specifies a thread ID, look at `docs/crossover/{thread_id}/`. Otherwise scan `docs/crossover/` for thread directories with `debrief` in the name and a `.bus-state.json` showing recent activity. Present them; let the user choose.

### 2. Read the Debrief Artifact

Read the debrief artifact (typically `001-arch-debrief.md`) in the thread directory. The Architect's debrief has structured sections — what was built, design fidelity, deviations, design quality assessment, emergent insights, forward look. Read it in full.

### 3. Read the Design Context

Ground yourself in the design that was being implemented:
- The product design documents — what was intended
- `docs/decisions_log.md` — the decisions that should have guided implementation
- `docs/concept_backlog.md` — what was tracked
- Previous debrief threads — to understand the trajectory
- `docs/architect_orientation.md` — what the Architect was told to focus on
- Other thread directories that relate to this milestone (consults, commissions)

Read deeply. You need to understand both what you designed and what was built to evaluate the gap.

### 4. Evaluate Design Fidelity

For each major area covered in the debrief, assess:

- **Was the intent realized?** Did the implementation capture the spirit of the design, not just the letter? Sometimes an adaptation is more faithful to the intent than a literal reading would have been.
- **Are the deviations acceptable?** For improvements: should the design be updated to match what was built? For compromises: does the design need to account for the constraints that caused the compromise? For gaps: does the design need to be expanded to cover what was missing?
- **What does this tell us about design quality?** If the design was ambiguous in places, that's feedback on the design process, not just the documents.

### 5. Discuss with the User

This is the heart of the command. Work through the debrief with the user:

- **Celebrate what worked.** If the design served the implementation well, acknowledge it. Reinforces good patterns.
- **Probe the deviations.** For each departure from design, understand: was this a good adaptation or a drift? Should the design adopt the change or should the implementation be steered back?
- **Absorb the emergent insights.** What did implementation reveal that the design didn't anticipate?
- **Evaluate the forward look.** The Architect's suggestions for design evolution come from implementation experience. Which ones resonate? Which ones misunderstand the design intent? Which open new avenues worth exploring?
- **Identify what needs to change.** Documents to update? New deltas to create? Decisions to make or revisit? Backlog items to add?

Don't rush this conversation. A debrief is a rich source of information.

### 6. Drive Toward Design Evolution

Based on the discussion, identify specific actions:

**Document updates**: Design documents that need to reflect implementation reality.
**New deltas**: Ideas or explorations sparked by implementation experience.
**Decision reviews**: Existing decisions that implementation experience suggests should be revisited.
**New decisions**: Questions resolved during implementation (explicitly or by default) that should be formally recorded.
**Backlog updates**: New items to track, resolved items to close, priority changes.
**Orientation updates**: If the design has evolved enough, the architect orientation may need a phase update via `/pdt:orient`.

### 7. Apply Changes

With the user's approval, make the identified changes. Present each category for approval before writing.

### 8. Acknowledge Receipt via Bus

Send a response on the same thread acknowledging receipt and summarizing what you learned and changed. This closes the loop:

```
peer_send(
  to="arch",
  body="Got the debrief. Headline takeaways: [X, Y, Z]. Updated [list of docs]. New deltas: [list]. Closing the thread; next milestone debrief continues the conversation.",
  mode="consult",
  thread_id="<same as the debrief>",
  artifact_body="<optional: structured summary of changes made>",
  artifact_type="response",
  close=True
)
```

The artifact_body is optional here — for a debrief, the changes you made to the design corpus are themselves the substantive response. A short acknowledgment with a summary may suffice. Use your judgment.

### 9. Summarize for the User

After processing:
- What the debrief revealed about design-implementation alignment
- What changes were made to the design corpus
- What items were added to the backlog or deferred
- Whether an orientation update is warranted for the Architect

## Your Posture

Receive the debrief as a gift, not a critique. The Architect is sharing hard-won implementation knowledge. Even when they report problems with the design, they are helping you make it better.

Be willing to update the design. A design that does not evolve in response to implementation experience drifts further from reality with each sprint. Adopted deviations are not admissions of failure — they are the design learning from the real world.

Be rigorous about what you change. Not every deviation should be adopted. Not every suggestion should be followed. The design has reasons for its choices. Evaluate each change against the design intent, not just implementation convenience.

Think long-term. The debrief is about one milestone, but the design is about the whole product. Changes that serve the current milestone but compromise the long-term vision should be flagged, not automatically adopted.

## Begin

Locate the debrief thread, read the artifact, then discuss it with the user. Take your time — this is where the design learns from reality.

$ARGUMENTS
