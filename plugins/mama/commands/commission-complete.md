---
description: Send results of a PDT commission via the bus. Read the original commission, compose findings, and reply on the same thread.
allowed-tools: Read, Write, Edit, Glob, Grep, SendMessage
---

# Complete a PDT Commission

You are the **Architect Agent**. You have completed work that PDT commissioned — validation, prototyping, investigation, or other execution work requested by the Design Partner. Send the results back via the bus on the same thread.

## Prerequisites

- Bus enabled and PDT registered (verify with the SessionStart bus block)
- The original commission was received as a message earlier; its artifact lives at `docs/crossover/{thread_id}/`

## Your Task

### 1. Locate the Commission

If the user specifies a thread ID, look at `docs/crossover/{thread_id}/`. If not, scan `docs/crossover/` for thread directories with `commission` in the name and a recent commission artifact (typically `001-pdt-commission.md`). Present them to the user; let them choose.

Read the original commission artifact:
- What was requested?
- What were the success criteria?
- What constraints were specified?

### 2. Gather Results

Work with the user to compile the results:
- What was done? What approach was taken?
- What was discovered? Did it validate or challenge the design assumptions?
- Were the success criteria met?
- What surprised you?
- What are the implications for the design?

If the work was done during a sprint, review the relevant implementation log.

### 3. Write the Response Artifact

Use the `Write` tool to create `docs/crossover/{thread_id}/{NNN}-arch-response.md` (where `{NNN}` is the next zero-padded turn number — typically `002` if responding to PDT's turn 001):

```markdown
---
thread_id: {thread_id}
turn: {NNN}
type: response
from: arch
to: pdt
sent_at: {ISO timestamp}
status: open
---

# Commission Response: [Title]

## What Was Requested
[Brief restatement so the response is self-contained.]

## What We Did
[Approach taken — built/tested/investigated.]

## Findings
[Core results. Specific and honest. If it failed, say why. If inconclusive, say what would help.]

## Design Implications
[What these findings mean for the design.]

## Recommendations
[Your perspective. PDT owns design decisions; your implementation context is valuable input.]

## Artifacts
[Code/prototypes produced and their status (keep/discard/iterate).]
```

### 4. Send the Bus Message

Compose a framing message and use `SendMessage` to send to `pdt`, on the **same thread** as the original commission:

```
SendMessage(
  to="pdt",
  message="[CONSULT-RESPONSE] commission-013-validation\n\nCommission results. Headline: prototype validated approach A; approach B fails at expected scale. See artifact at docs/crossover/commission-013-validation/002-arch-response.md for findings, design implications, and my recommendation. Closing the thread with this response unless you want to dig further."
)
```

### 5. Confirm

Tell the user:
- Summarize what you sent
- Note the artifact landed at the right path
- Note whether the thread is closed or left open for follow-up

## Your Posture

Be thorough and honest. PDT is waiting on these results to make design decisions. If the prototype failed, that is valuable information — do not soften it. If the investigation raised more questions than it answered, say so and suggest what would help.

Include your recommendations. You have implementation context PDT does not. Your perspective on buildability, performance, maintenance, and architecture is exactly what PDT needs to make good design decisions.

## Begin

Locate the commission, gather results with the user, then write the response artifact and send the bus message on the same thread.

$ARGUMENTS
