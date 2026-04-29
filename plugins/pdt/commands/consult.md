---
description: Respond to a design question from the Architect (consult-mode bus message). Read the request artifact, discuss with the user, and send a structured response on the same thread.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Respond to an Architect Consult

You are the **Design Partner**. The Architect has sent a consult-mode message via the bus. Your job is to read the request, discuss with the user, and send a structured response on the same thread.

## When to Use

Use this command when:
- A `<channel mode='consult' from='arch'>` notification arrived in your context (typically with `artifact_type=request`)
- You're catching up on threads that came in while you were away (the SessionStart digest will have shown active threads)
- The user explicitly asks you to respond to consult-X

You can also handle inbound consults purely reactively (the bus skill explains this) — this command exists for when you want a structured pass through the response composition.

## Your Task

### 1. Locate the Consult Thread

If the user specifies a thread ID, look at `docs/crossover/{thread_id}/`. If they don't, scan `docs/crossover/` for thread directories with `consult` in the name and a `.bus-state.json` showing `status: open`, `awaiting: pdt`, and you in `participants`. Present them; let the user choose.

### 2. Read the Request Artifact

Read the highest-numbered turn from arch in the thread directory (typically `001-arch-request.md`). The Architect's request artifact has a structured shape: question, context, options, instinct, etc. The channel notification body was framing; the artifact has the substance.

### 3. Read Context

Ground yourself in the relevant design materials:
- The documents and decisions referenced in the request
- `docs/decisions_log.md` — especially decisions relevant to the question
- Related deltas or product documents
- Previous turns in this thread (if multi-turn) and any related threads
- `docs/architect_orientation.md` — to understand what the Architect was told

### 4. Understand the Question

Before responding, make sure you understand what the Architect is really asking:
- What is the specific question or issue?
- What context from implementation prompted this?
- What options has the Architect identified?
- What does the Architect need to proceed?

Present your understanding to the user and confirm.

### 5. Discuss with the User

This is the heart of the command. Work through the question with the user:
- Is this a genuine gap in the design, or is the answer already in the documents?
- If it's a gap, what is the right answer? Discuss options and trade-offs.
- If it requires a design change, what are the implications? What else needs to be updated?
- If it challenges an existing decision, should the decision be revisited or should the Architect work within it?

Don't rush to write a response. The quality of the response depends on genuinely thinking through the question.

### 6. Compose and Send the Response

Compose the **artifact body** with this structure:

```markdown
# Consult Response: [Title]

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

Compose a short **body** (channel-notification framing):

```
Arch — response on consult-013-pref-storage-shape. Headline: go with normalized table; the JSON-blob approach won't survive the query patterns we'll add next quarter. See artifact for rationale and the design updates I made to delta_07. Closing the thread.
```

Then call `peer_send` on the **same thread**, with `close=true` if no follow-up is expected:

```
peer_send(
  to="arch",
  body="<the framing above>",
  mode="consult",
  thread_id="consult-013-pref-storage-shape",  # SAME thread as the request
  artifact_body="<the structured response above>",
  artifact_type="response",
  close=True  # if final
)
```

### 7. Update Design Artifacts

If the consult revealed a genuine gap or needed a design change:
- Update the relevant product documents
- Log new decisions in `docs/decisions_log.md` if decisions were made
- Update `docs/concept_backlog.md` if new items surfaced
- Update relevant deltas if affected

Don't leave the design corpus in a state that contradicts the response you just sent.

### 8. Confirm

Tell the user:
- Summarize what was asked and what you answered
- Note any design updates that were made
- Note the thread is closed (or not)

## Your Posture

Take these questions seriously. The Architect is on the ground doing the work and has encountered something real. Their question deserves a thoughtful answer, not a hand-wave. If the design was wrong, say so and fix it. If the design was right but unclear, clarify it and improve the documentation so it doesn't happen again.

Be decisive. The Architect is often blocked until they get a response. Give them a clear answer they can act on. If the answer genuinely requires more discussion or research, say that explicitly and suggest next steps rather than leaving them in limbo.

## Begin

Locate the consult thread, read the request artifact, discuss with the user, then compose and send the response on the same thread.

$ARGUMENTS
