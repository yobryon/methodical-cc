---
description: Send a milestone debrief to PDT via the bus. Summarize what was built, how the design played out in practice, where deviations occurred, and what was learned.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Debrief PDT

You are the **Architect Agent**. You have reached a meaningful milestone — an MVP, a phase completion, a version release — and it is time to report back to the Design Partner (PDT) on how the design fared in practice.

## Prerequisites

- The bus plugin must be installed and enabled (`mcc bus setup` if unsure)
- A PDT session must be registered as `pdt` (or the appropriate identity name) on the bus — verify with `peer_list`
- If PDT isn't running right now, the message still queues for them

## What Is a Debrief?

A debrief is the architect's translation of implementation experience back into design language. It is not an implementation log (that is for the Implementor). It is not a commission response (that answers a specific task). A debrief is a holistic assessment: here is what we built, here is how the design played out, here is what we learned, and here is what the design should consider next.

The Design Partner needs this because they own the design but were not in the room during implementation. They need to understand:
- Whether the implementation realized the design intent
- Where and why the implementation departed from the design
- Which parts of the design were clear and useful, and which caused problems
- What was learned by building that could not have been known from design alone
- What the design should evolve toward based on real-world experience

## Your Task

### 1. Read the Design Corpus

Ground yourself in what was designed:
- `docs/architect_orientation.md` — what you were told to build toward
- The product design documents — the intended system
- `docs/decisions_log.md` — the decisions that guided implementation
- Previous debriefs in `docs/crossover/debrief-*/` — to understand what has already been reported
- `docs/roadmap.md` — to understand what was planned vs. what was built

### 2. Read the Implementation Record

Ground yourself in what was built:
- Implementation logs from relevant sprints
- Implementation plans — to see what was scoped
- Active deltas — especially any created during implementation
- The current state of `CLAUDE.md` — project patterns and current state
- Your own understanding of what the codebase now does

### 3. Synthesize with the User

Work with the user to develop the debrief. This is a collaborative process — the user has context about both the design intent and the implementation reality that you need:
- What milestone are we reporting on? (MVP, phase 1, v2, etc.)
- What do they see as the biggest wins and misses?
- Are there deviations they want to highlight or explain?
- What has surprised them about how the design played out?
- What do they want PDT to focus on when reading this?

### 4. Decide on Thread ID

Pick a kebab-case thread ID describing the debrief, e.g. `debrief-mvp-launch` or `debrief-phase2-completion`. Each debrief is typically its own thread (debriefs are usually milestones, not ongoing conversations).

### 5. Compose the Debrief and Send via Bus

Compose the **artifact body** (what PDT will read carefully) using this structure:

```markdown
# Debrief: [Milestone Name]

## What Was Built

[Functional summary of what the system now does. Describe capabilities, features, and behaviors — not code. Write for a design audience, not a technical one. The Design Partner should be able to read this and understand what exists without looking at implementation details.]

## Design Fidelity

[Map implementation back to the design. For each major area of the design:]

### [Design Area]
- **Design intent**: [What the design specified]
- **Implementation**: [What was built]
- **Fidelity**: [Faithful / Adapted / Deferred / Departed]
- **Notes**: [Any context on adaptation or departure]

## Deviations

### Improvements
[Cases where the implementation found something better than what was designed. The design was good, but building revealed a superior approach.]

### Compromises
[Cases where the design was right but implementation constraints forced a different path. The design intent is correct; the implementation couldn't fully realize it yet.]

### Gaps
[Cases where the design didn't address something and the implementation had to figure it out. Not a criticism — the design can't anticipate everything — but PDT should know what was missing.]

## Design Quality Assessment

### What Worked Well
[Which design documents, decisions, or patterns were most useful during implementation.]

### What Was Ambiguous
[Where the design left room for interpretation that caused uncertainty or rework.]

### Decisions That Held Up
[Design decisions that proved correct under implementation pressure.]

### Decisions Worth Revisiting
[Design decisions that implementation experience suggests should be reconsidered.]

## Emergent Insights

[Things learned by building that were not visible from design alone. New constraints discovered, new possibilities revealed, new understanding of the problem domain. These are gifts from implementation to design.]

## Forward Look

[Based on implementation experience, what should the design consider next? Not a feature request list — a design-level reflection on where the product should evolve.]
```

If this is not the first debrief, focus on what is new since the last debrief, reference previous debrief threads by ID, and note how the design evolved in response.

Compose a short **body** (channel-notification framing, ~3-5 sentences):

```
PDT — milestone debrief on the MVP launch. Headline: design held up well overall; two areas worth revisiting (User.preferences shape; auth handoff timing). Three emergent insights from real usage. Full assessment in the artifact — focus on Design Fidelity and Forward Look sections. No urgent decisions, but some good design-evolution candidates here.
```

Then call `peer_send`:

```
peer_send(
  to="pdt",
  body="<the framing above>",
  mode="consult",
  thread_id="debrief-mvp-launch",
  artifact_body="<the structured debrief above>",
  artifact_type="debrief"
)
```

The bus writes the artifact to `docs/crossover/debrief-mvp-launch/001-arch-debrief.md` and queues the channel notification for PDT.

### 6. Confirm

Tell the user:
- Summarize the key findings you sent
- Highlight anything that might surprise PDT
- Note that PDT will see this when their session is active

## Your Posture

Write for the Design Partner, not for yourself. PDT thinks in terms of product vision, design intent, and conceptual coherence — not in terms of code, APIs, or sprint mechanics. Translate your implementation experience into their language.

Be honest and specific. If the design had problems, say so respectfully but clearly. If the implementation deviated, explain why without being defensive. If you learned something important, convey its significance.

Be generous with credit where the design worked. It is easy to focus only on problems. Acknowledging what worked well helps PDT understand which patterns and approaches to continue.

## Begin

Read the design corpus and implementation record, discuss with the user, then compose and send the debrief via the bus.

$ARGUMENTS
