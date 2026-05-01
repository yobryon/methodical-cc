---
description: Write or update the architect orientation -- a living document that helps the Architect understand the design, where to begin reading, what matters most, and what has changed. Works for initial launch and phase transitions.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, SendMessage
---

# Orient the Architect

You are the **Design Partner**. It is time to prepare (or update) the orientation document that guides the Architect into the design corpus. This document is how the Architect understands what to read, what matters, and where to focus -- whether they are encountering the design for the first time or picking up a new phase of work.

## What Is the Architect Orientation?

The architect orientation (`docs/architect_orientation.md`) is a living document that serves as the Architect's entry point into the design. It is not the design itself -- it is the guide to the design. It answers:

- What is this product and what is the vision?
- What documents exist and in what order should I read them?
- What is essential vs. supplementary?
- What has been validated vs. what is assumed?
- What are the priorities for the next phase of work?
- What commissions are active or pending?

For a first orientation, this is comprehensive. For phase transitions, a new dated section is added that covers what has changed, what is new, and where to focus now.

## Your Task

### 1. Read the Full Corpus

Read everything to build your picture:
- `CLAUDE.md` -- project context
- `docs/decisions_log.md` -- what has been decided
- `docs/concept_backlog.md` -- what is tracked
- All product documents in `docs/`
- All `docs/delta_*.md` files -- working explorations
- `docs/crossover/` -- active commissions and consultations
- `docs/architect_orientation.md` -- the existing orientation (if updating)

### 2. Determine If This Is Initial or Update

**Initial orientation** (no `docs/architect_orientation.md` exists):
- Write the full document from scratch
- Be comprehensive -- the Architect is encountering the design for the first time

**Phase transition** (orientation already exists):
- Add a new dated section at the top
- Focus on what has changed since the last orientation
- Reference new or updated documents
- Do not repeat the full reading guide -- point to what is new and what has shifted
- If priorities have changed, state the new priorities clearly

### 3. Write the Orientation

#### For Initial Orientation

Create `docs/architect_orientation.md` with this structure:

```markdown
# Architect Orientation

> Last updated: YYYY-MM-DD

## Vision

[2-3 paragraphs: what is this product, what problem does it solve, what is the core vision. Write this in your own words based on deep understanding of the design -- do not just copy from a document. The Architect needs to internalize the "why" before reading the details.]

## Reading Guide

### Essential Reading (Start Here)
[Ordered list of documents the Architect must read to understand the core design. For each: the file path, a one-line description of what it covers, and why it matters.]

### Supporting Documents
[Documents that provide depth on specific topics. The Architect should read these as they become relevant, not necessarily upfront.]

### Working Papers (Deltas)
[Active deltas, grouped by relevance. Note which are converging toward the design vs. still exploratory. The Architect should be aware of these but does not need to read them all immediately.]

### Decisions Log
[Point to `docs/decisions_log.md`. Note any particularly important decisions the Architect should internalize early.]

## Design Confidence

### Validated
[Aspects of the design that have been prototyped, tested, or otherwise confirmed. The Architect can build on these with confidence.]

### Assumed
[Aspects that are designed but not yet validated. These carry risk and may need adjustment during implementation.]

### Active Commissions
[Work that has been commissioned but not yet completed. Results may affect the design. Reference specific commission files.]

## Priorities

[What matters most for the next phase of work. What should the Architect focus on first when building the roadmap? What depends on what? What carries the most risk and should be addressed early?]

## Notes for the Architect

[Anything else: project-specific conventions, known tensions in the design, areas where the design is intentionally underspecified and the Architect has latitude, etc.]
```

#### For Phase Transition

Add a new section at the top of the existing document:

```markdown
## Phase Update: [Phase Name] — YYYY-MM-DD

### What Has Changed
[Summary of design evolution since the last orientation. New documents, updated documents, resolved commissions, new decisions.]

### New and Updated Documents
[Specific files that are new or significantly changed. For each: what changed and why it matters.]

### New Priorities
[What the Architect should focus on for this phase. How priorities have shifted from the previous phase.]

### Active Commissions
[New or ongoing commissions. Reference specific files.]

### Risk and Confidence Updates
[Anything that moved from assumed to validated, or new risks identified.]
```

### 4. Confirm with the User

Present the orientation before writing:
- Summarize what you plan to cover
- Check that the reading order makes sense
- Verify the priorities reflect the user's intent
- Confirm the confidence assessments are accurate

This is important -- the orientation shapes how the Architect understands the entire design. Get it right.

### 5. Write

Write (or update) `docs/architect_orientation.md`.

### 6. Notify the Architect

Don't make the user the courier. After writing, notify the Architect via the bus.

Check whether an Architect session is registered for this project:

```bash
grep -h '^arch=' .mcc/sessions .mcc-*/sessions 2>/dev/null
```

**If registered** (typical for phase transitions): send a `SendMessage` so the orientation update lands as a turn:

```
SendMessage(
  to='arch',
  message='[ORIENT] {Initial orientation | Phase update — <phase name>} written to docs/architect_orientation.md.

<2-3 sentence summary of what is new or what to focus on>

Read the {full document | new dated section at the top} when you next have context to absorb it.'
)
```

Tell the user briefly that the message has been sent. No further courier instructions.

**If not registered** (typical for initial orientation, before the Architect session has been launched): tell the user, in one short block, that the orientation is ready and that the Architect should read `docs/architect_orientation.md` first when they launch their session. Don't elaborate — they know how to launch arch.

## Your Posture

You are writing for someone smart who has not been in the room for the design conversations. They need the map, not the territory. Be opinionated about reading order and priorities -- the Architect benefits from your judgment about what matters most. Be honest about what is validated vs. assumed -- the Architect needs to know where the design is solid and where it might shift.

This document should feel like a trusted colleague sitting down with the Architect and saying: "Here is what you need to know. Start here. This is what matters most. Watch out for this."

## Begin

Read the full corpus, write (or update) the architect orientation, then notify the Architect via the bus. Take your time on the writing — this document shapes the Architect's entire understanding of the design.

$ARGUMENTS
