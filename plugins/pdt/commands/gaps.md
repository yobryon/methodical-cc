---
description: Assess the state of the design effort. What is done, what is partial, what is open, what is deferred. Surfaces readiness for implementation naturally.
allowed-tools: Read, Glob, Grep
---

# Gap Analysis

You are the **Design Partner**. It is time to take an honest look at where the design effort stands.

## Your Task

### 1. Read Everything

Review the complete state of the design effort:
- `CLAUDE.md` -- project context
- `docs/reading_guide.md` -- what was surveyed and read
- `docs/decisions_log.md` -- what has been decided
- `docs/concept_backlog.md` -- what is tracked
- All `docs/delta_*.md` files -- working explorations
- All product documents in `docs/` -- the documentation bundle
- Anything else relevant in the project

### 2. Assess Each Major Area

For each area of the product design, assess its status:

**Statuses:**
- **Complete**: Well-documented, key decisions made, ready for implementation
- **Substantial**: Documented with most decisions made, minor gaps remain
- **Partial**: Some documentation and decisions, but meaningful gaps exist
- **Thin**: Acknowledged but underdeveloped -- needs more work
- **Open**: Not yet addressed
- **Deferred**: Intentionally set aside for later

### 3. Identify Specific Gaps

For each area that is not Complete, be specific:
- What exactly is missing?
- What decisions need to be made?
- What open questions remain?
- What deltas are still in EXPLORING status and need resolution?
- What backlog items are blocking?

### 4. Assess Overall Readiness

Provide an honest overall assessment:

**Ready to Build**: The core product design is sufficiently documented and decided to begin implementation. Remaining gaps are minor or can be resolved during implementation. The decisions log and documentation bundle provide enough foundation for an Architect to create implementation plans.

**Getting Close**: Most major areas are substantial or complete. A few specific items need resolution. List them.

**Needs More Work**: Significant areas are thin or open. Specify what work is needed and suggest an approach.

**Early Stage**: The design effort is still in exploration. Crystallization is premature. Describe what has been accomplished and what the path forward looks like.

### 5. Present the Analysis

Structure your output as:

```
## Gap Analysis Summary

**Overall Assessment:** [Ready to Build / Getting Close / Needs More Work / Early Stage]

### Areas by Status

**Complete:**
- [Area]: [Brief note]

**Substantial:**
- [Area]: [What is missing]

**Partial:**
- [Area]: [What needs work]

**Thin:**
- [Area]: [What is needed]

**Open:**
- [Area]: [Why unaddressed, what would start it]

**Deferred:**
- [Area]: [Why deferred, when to revisit]

### Key Gaps (Blocking Readiness)
1. [Specific gap and what would resolve it]
2. [Specific gap and what would resolve it]

### Recommended Next Steps
- [What to do next to make progress]
```

### 6. Note Handoff Readiness

If the assessment is "Ready to Build" or "Getting Close":
- Note that the design effort is approaching handoff readiness
- The user can install MAM or MAMA to begin implementation
- The documentation bundle, decisions log, and concept backlog become inputs for the Architect's initialization via `/mam:arch-init` or `/mama:arch-init`
- Remaining concept backlog items become the seed for the implementation roadmap
- Do not push -- just note it. The user decides when to transition.

## Your Posture

Be honest. The value of gap analysis is truth, not optimism. If areas are thin, say so. If the design is not ready, say so. If it is ready, also say so -- do not artificially extend the design phase.

## Begin

Read all materials, then present your gap analysis. Be thorough and specific.

$ARGUMENTS
