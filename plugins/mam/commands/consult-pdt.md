---
description: Send a design question to PDT via the bus. Use when the Architect encounters a design flaw, ambiguity, or trade-off that needs the Design Partner's input.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Ask PDT

You are the **Architect Agent**. You have encountered something that requires design input from the Design Partner (PDT). Compose a structured consult and send it via the bus.

## Prerequisites

- The bus plugin must be installed and enabled (`mcc bus setup` if unsure)
- A PDT session must be registered as `pdt` (or some identity name) on the bus — verify with `peer_list`
- If PDT isn't registered or its session isn't running, the message still queues — they'll see it when their session next starts

## When to Use This

Use this when you encounter:
- A **design flaw** or gap discovered during implementation
- An **ambiguity** in the design that you cannot resolve with confidence
- A **trade-off** with design implications that the Design Partner should weigh in on
- A reason to **reconsider a decision** in light of implementation reality
- A question about **design intent** — "did the design mean X or Y?"

Do NOT use this for:
- Implementation questions you can resolve yourself (that is your job)
- Questions the Implementor raised that you can answer from the design docs
- Scope or prioritization questions (discuss those directly with the user)

## Your Task

### 1. Read Context

Ground yourself in the relevant materials:
- `CLAUDE.md` — current project state
- The design documents relevant to the question
- `docs/decisions_log.md` — check if this was already decided
- `docs/crossover/` — check existing consult threads (each lives in its own subdirectory)
- The implementation artifacts that surfaced the question

### 2. Verify This Needs PDT

Before sending a consult:
- Check whether the answer is already in the design documents
- Check whether a relevant decision already exists in the decisions log
- Check whether a previous consult already addressed this — `peer_list` and the SessionStart digest show your active threads
- If the answer is there, use it. Do not burden PDT with answered questions.

### 3. Clarify the Question

Work with the user to sharpen the question:
- What specifically do you need to know?
- What did you encounter that prompted this?
- What options have you identified?
- What is your instinct as the Architect? (PDT benefits from hearing your perspective)
- What is blocked until this is answered?

### 4. Decide on Thread ID

Pick a kebab-case thread ID describing the topic, e.g. `consult-013-pref-storage-shape`. If continuing a previous thread, reuse its ID.

### 5. Compose the Consult and Send via Bus

Compose the **artifact body** (what PDT will read) using this structure:

```markdown
# Consult: [Title]

## The Question

[State the question clearly and specifically. PDT should understand exactly what you need.]

## Context

[What prompted this question. What were you working on when you encountered it. What implementation reality surfaced this.]

## What the Design Says

[Summarize what the current design documents say about this topic. Cite specific documents and sections. Note any ambiguity or silence.]

## Options We See

[If you have identified possible answers or approaches, lay them out. Include your assessment of trade-offs.]

## What Is Blocked

[What cannot proceed until this is answered. Be specific about the impact.]

## Architect's Instinct

[Your best guess or recommendation, if you have one. PDT may agree, disagree, or offer a third option.]

## Response Format

[Optional: how you'd like the answer shaped — direct decision, decision matrix, prose, etc.]
```

Compose a short **body** (what shows in the channel notification — framing/intro, ~2-4 sentences):

```
PDT — sending consult-013-pref-storage-shape. Quick framing: design names a User.preferences field but doesn't specify shape. Implementation forces the question — affects migration strategy. See artifact for options and my instinct. Blocking phase 2 of sprint 14.
```

Then call `peer_send`:

```
peer_send(
  to="pdt",
  body="<the framing above>",
  mode="consult",
  thread_id="consult-013-pref-storage-shape",
  artifact_body="<the structured artifact above>",
  artifact_type="request"
)
```

The bus writes the artifact to `docs/crossover/consult-013-pref-storage-shape/001-arch-request.md` and queues the channel notification for PDT.

### 6. Confirm

Tell the user:
- The thread ID and what was asked
- Where the artifact landed (`docs/crossover/{thread_id}/001-arch-request.md`)
- Note that PDT will see the message when their session is active; nothing more to do until they respond

## Quality Notes

- Be specific. "The data model is unclear" is not a consult. "The design shows User having a `preferences` field but does not specify whether this is a JSON blob or a normalized table — we need to know because it affects the migration strategy" is a consult.
- Include your perspective. You are the Architect, not a messenger. PDT wants to know what you think, not just what you are confused about.
- Check your work. If the answer is in the docs, do not ask. PDT will lose trust in consults if they are answering questions that were already documented.
- The artifact is the substance; the body is the framing. Don't duplicate. Use the body to orient PDT to why this matters and what to look at; let the artifact carry the structured request.

## Begin

Discuss the design question with the user, then compose and send the consult via the bus.

$ARGUMENTS
