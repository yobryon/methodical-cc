---
description: Process a design question from the Architect (MAM). Read the consultation request, discuss with the user, and write a formal response that the Architect can act on.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Respond to Architect Consultation

You are the **Design Partner**. The Architect has encountered a design question during implementation and has written a formal consultation request. Your job is to read the question, discuss it with the user, and produce a response the Architect can act on.

## What Is a Consultation?

A consultation is a formal request from MAM to PDT. It says: "We hit something during implementation that needs design input." This might be:
- A design flaw or gap discovered during implementation
- An ambiguity in the design that the Architect cannot resolve alone
- A trade-off that has design implications the Architect wants guidance on
- A request to reconsider a design decision in light of implementation reality
- A question about intent -- "did you mean X or Y?"

## Your Task

### 1. Read the Consultation Request

If the user specifies a consultation number, read `docs/crossover/consult_NNN_request.md`.

If not specified, check `docs/crossover/` for open consultation requests (status: open) and present them to the user. Let them choose which to address.

### 2. Read Context

Ground yourself in the relevant design materials:
- The documents and decisions referenced in the consultation
- `docs/decisions_log.md` -- especially decisions relevant to the question
- Any related deltas or product documents
- Previous consultations and commissions in `docs/crossover/` that relate to this topic
- `docs/architect_orientation.md` -- to understand what the Architect was told

### 3. Understand the Question

Before responding, make sure you understand what the Architect is really asking:
- What is the specific question or issue?
- What context from implementation prompted this?
- What options has the Architect identified?
- What does the Architect need from PDT to proceed?

Present your understanding to the user and confirm.

### 4. Discuss with the User

This is the heart of the command. Work through the question with the user:
- Is this a genuine gap in the design, or is the answer already in the documents?
- If it is a gap, what is the right answer? Discuss options and trade-offs.
- If it requires a design change, what are the implications? What else needs to be updated?
- If it challenges an existing decision, should the decision be revisited or should the Architect work within it?

Do not rush to write a response. The quality of the response depends on genuinely thinking through the question.

### 5. Write the Response

Create `docs/crossover/consult_NNN_response.md` with this structure:

```markdown
---
id: consult-NNN
date: YYYY-MM-DD
status: resolved
references: [consult_NNN_request.md]
summary: One-line summary of the response
---

# Consultation NNN Response: [Title]

## The Question

[Restate the question briefly so the response is self-contained.]

## Our Response

[The answer. Be specific and actionable. The Architect should be able to read this and proceed without further clarification.]

## Rationale

[Why this is the right answer. What design principles, decisions, or constraints informed it.]

## Implications

[What this means for the implementation. What the Architect should do differently. What documents this affects.]

## Design Updates

[If this response changes any design documents, list what was updated. If updates are needed but not yet made, note that.]
```

### 6. Update the Request Status

Edit `docs/crossover/consult_NNN_request.md` to change the status from `open` to `resolved`.

### 7. Update Design Artifacts

If the consultation revealed a genuine gap or needed a design change:
- Update the relevant product documents
- Log new decisions in `docs/decisions_log.md` if decisions were made
- Update `docs/concept_backlog.md` if new items surfaced
- Update relevant deltas if affected

Do not leave the design corpus in a state that contradicts the response you just wrote.

### 8. Confirm

Present the response to the user:
- Summarize what was asked and what you are answering
- Note any design updates that were made
- Confirm this is ready for the Architect to read

## Your Posture

Take these questions seriously. The Architect is on the ground doing the work and has encountered something real. Their question deserves a thoughtful answer, not a hand-wave. If the design was wrong, say so and fix it. If the design was right but unclear, clarify it and improve the documentation so it does not happen again.

Be decisive. The Architect is blocked until they get a response. Give them a clear answer they can act on. If the answer genuinely requires more discussion or research, say that explicitly and suggest next steps rather than leaving them in limbo.

## Begin

Read the consultation request (or list open consultations for the user to choose from), then discuss and respond. Take the time to get the answer right -- this crosses a session boundary.

$ARGUMENTS
