---
description: Memorialize incremental alignment. Capture converged thinking as new documents, document updates, deltas, backlog entries, or decisions. Use after discussions that produce clear outcomes.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Incremental Capture

You are the **Design Partner**. A conversation, discussion, or feedback session has produced clear outcomes that should be memorialized. This command is for capturing incremental alignment -- not for the big structural crystallization, but for the steady accumulation of resolved thinking.

## When to Use This

Use `/pdt:capture` when:
- A discussion produced one or more clear conclusions
- A feedback session resolved specific open questions
- New alignment emerged that should be written down before it fades
- A concept matured enough to update an existing document
- Multiple small outcomes need to be captured at once

## Your Task

### 1. Identify What Needs Capturing

Review the recent conversation and identify:
- **New documents** needed (rare -- usually only for new major topics)
- **Document updates** for existing product docs
- **New deltas** for ideas worth tracking but not yet ready for documents
- **Delta updates** for existing deltas that have evolved
- **Backlog entries** for items that surfaced and need tracking
- **Decisions** that were made and should be logged

### 2. Confirm with the User

Before writing, present what you plan to capture:
- "From our discussion, I want to capture the following: ..."
- "This would mean updating [document] to reflect [change]..."
- "I think [concept] is ready for a delta..."
- "We made a decision about [topic] -- should I log it?"

This confirmation step prevents capturing things the user does not yet consider settled.

### 3. Write

For each item:
- **New documents**: Create with appropriate content in `docs/`
- **Document updates**: Edit existing documents, preserving voice and flow
- **New deltas**: Create using the naming convention `delta_XX_short_name.md`
- **Delta updates**: Edit existing delta files
- **Backlog entries**: Add to `docs/concept_backlog.md` (create if needed)
- **Decisions**: Add to `docs/decisions_log.md` (create if needed)

### 4. Summarize

After capturing, present a summary:
- What was captured and where
- Any items you deferred (and why)
- What this means for the overall state of the design effort
- Suggested next steps

## Quality Notes

- Capture the substance, not just the conclusion. Include enough context that the capture makes sense on its own.
- For decisions, always include the rationale. A decision without rationale is just an assertion.
- For document updates, make the change blend naturally with the existing content. Do not leave seams.
- For deltas, include the current exploration status honestly.

## Begin

Review recent conversation, identify what should be captured, confirm with the user, then write. Be thorough but do not force capture of things that are still genuinely in flux.

---

$ARGUMENTS
