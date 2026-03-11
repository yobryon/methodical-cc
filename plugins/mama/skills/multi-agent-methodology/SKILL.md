---
name: multi-agent-methodology
description: Multi-Agent Architecture methodology for complex software projects. Provides guidance on role separation (Architect/Implementor), incremental design via deltas, structured context handoffs, feedback loops, and sprint-based development. Use when working on projects following this methodology, when planning sprints, creating implementation plans, or managing product documentation.
---

# Multi-Agent Architecture Methodology

This skill provides the foundational methodology for managing complex software projects using a multi-agent approach with distinct Architect and Implementor roles.

## Core Philosophy

1. **Clear Role Separation**: The Architect owns design, documentation, and orchestration. The Implementor owns code execution and implementation logging.
2. **Incremental Design via Deltas**: Explore design changes in delta documents before committing to the source of truth.
3. **Structured Context Handoffs**: Use briefs and implementation plans to transfer context between agents.
4. **Feedback Loops**: Implementation logs capture reality; feedback cycles capture evolution of thinking.
5. **Reconciliation**: Keep documentation current with reality after each sprint.

## The Two Agents

### The Architect Agent

The Architect is the design partner. Maintains comprehensive understanding, creates deltas, orchestrates implementation, and evolves the product vision.

**Responsibilities:**
- Maintain product documentation (the source of truth)
- Create delta documents for design exploration and capturing new ideas
- Create implementation plans for each sprint
- Write briefs for the Implementor
- Review implementation logs
- Reconcile deltas and discoveries back into product documentation
- Facilitate alignment discussions with the User

**Key Artifacts the Architect Produces:**
- Product documentation (structure appropriate to the project)
- `delta_XX_topic.md` - Incremental design explorations and captured ideas
- `implementation_plan_sprintX.md` - Phase breakdowns for implementors
- `implementor_brief_sprintX.md` - Context and instructions for the Implementor

### The Implementor Agent

The Implementor executes. Focused on code, not design decisions.

**Responsibilities:**
- Read the implementation plan and brief
- Execute phases in order
- Maintain an implementation log with decisions, discoveries, bugs/fixes, and reflections
- Flag questions or blockers for the Architect
- Report completion status with honest reflection on what went well and what didn't

**Key Artifacts the Implementor Produces:**
- Working code
- `implementation_log_sprintX.md` - Running journal of work done

**Key Constraint:** The Implementor should NOT make design decisions. When facing ambiguity, document the question in the log, proceed with a reasonable default, or pause for Architect input.

## Document Types

### Product Documentation

The source of truth for the project. Structure and composition depend on the nature of the product:
- Could be a single comprehensive design document
- Could be multiple focused documents for major components
- Could include user stories, architecture docs, API specs, etc.

**The Architect should recognize what documentation structure serves the project best and propose accordingly.**

**Lifecycle:**
1. Created at project inception via `/mama:arch-create-docs`
2. Updated ONLY during reconciliation after sprint completion
3. Preserves decision history (don't delete, annotate or supersede)

**Key Rule:** Never update product docs during active implementation. Updates happen during reconciliation.

### Delta Documents

**Purpose:** Capture new ideas, design changes, and discoveries before committing to the source of truth.

**Naming:** `delta_XX_short_name.md` (e.g., `delta_05_event_system.md`)

**Contents:**
- Problem statement or idea description
- Proposed solution or change
- Design details
- Impact on existing components
- Open questions

**Lifecycle:**
1. Created when new ideas emerge (from feedback, implementation discoveries, etc.)
2. Discussed and refined with User
3. Either approved and queued for implementation, or deferred/discarded
4. Merged into product docs after implementation validates the approach

**Key Rule:** Deltas are working papers. They can be wrong, incomplete, or abandoned. Product docs are the commitment.

### Implementation Plan

**Purpose:** Break a sprint into executable phases for the Implementor.

**Naming:** `implementation_plan_sprintX.md`

**Contents:**
- Sprint overview and goals
- Phase list with descriptions
- Task checklists per phase
- File creation/modification expectations
- Dependencies between phases
- Success criteria
- References to relevant deltas

### Implementation Log

**Purpose:** Record what actually happened during implementation.

**Naming:** `implementation_log_sprintX.md`

**Contents:**
- Phase-by-phase progress notes
- Decisions made (with rationale)
- Deviations from plan (with reasons)
- Bugs encountered and fixed, with reflection on root cause
- Questions for Architect
- Technical discoveries
- Honest reflection on what could have been done better

**Key Rule:** The Implementor owns this document. The Architect reads it but doesn't edit it.

### Implementor Brief

**Purpose:** Provide context to the Implementor without requiring them to read everything.

**Naming:** `implementor_brief_sprintX.md`

**Contents:**
- Preamble establishing the Implementor's role and expertise expectations
- Project context (minimal, relevant)
- Current state summary
- What has already been decided
- What files/systems are relevant
- What NOT to touch
- Reference to the implementation plan
- Instructions for maintaining the implementation log

## The Sprint Lifecycle

### Sprint Structure

A sprint is a coherent chunk of work with a clear outcome:
- Large enough to require multiple implementation phases
- Small enough to complete before major design pivots
- Named and numbered (Sprint 1, Sprint 2, etc.)

### Sprint Phases

```
1. PLANNING           2. FEEDBACK           3. FINALIZATION
┌─────────────┐      ┌─────────────┐       ┌─────────────┐
│ Arch proposes│ ───▶ │User feedback│ ────▶ │ Converge &  │
│ initial scope│      │ + new ideas │       │ write plan  │
└─────────────┘      └─────────────┘       └─────────────┘
                                                  │
                                                  ▼
6. RECONCILIATION    5. REVIEW            4. IMPLEMENTATION
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│Update docs, │ ◀─── │Arch reads   │ ◀─── │ Implementor │
│apply deltas │      │impl log     │      │ executes    │
└─────────────┘      └─────────────┘      └─────────────┘
```

### Phase Details

**1. Planning (Architect + User)**
- Architect proposes initial scope for the sprint
- Based on roadmap, previous sprint outcomes, and project state
- Output: Initial scope proposal

**2. Feedback (User → Architect)**
- User provides feedback essay: reactions, new ideas, reflections
- Can include retrospective on previous sprint AND forward-looking thoughts
- Architect untangles, organizes, extracts deltas
- Discussion to clarify and align
- Output: Delta documents, refined scope understanding

**3. Finalization (Architect)**
- Converge on final sprint scope
- Write implementation plan with phases
- Write Implementor brief
- Output: `implementation_plan_sprintX.md`, `implementor_brief_sprintX.md`

**4. Implementation (Implementor)**
- Read brief and plan
- Execute phases in order
- Maintain implementation log
- Flag blockers or questions
- Output: Working code, `implementation_log_sprintX.md`

**5. Review (Implementor + User)**
- Test and verify implementation
- Debug cycle as needed
- Implementor finalizes log with reflections
- Output: Finalized implementation log

**6. Reconciliation (Architect)**
- Read implementation log
- Update product docs with validated changes
- Apply deltas that were implemented
- Capture discoveries worth preserving
- Propose scope for next sprint
- Output: Updated product docs, next sprint proposal

## The Feedback Cycle

The feedback cycle is where evolution happens. After implementation:

1. User collects thoughts during implementation (notes, reactions, ideas)
2. User presents these to the Architect as a feedback essay
3. Architect processes the feedback:
   - Untangles and organizes the content
   - Identifies new ideas → creates deltas
   - Identifies feedback on existing decisions → notes for discussion
   - Identifies architectural implications → flags for discussion
   - Identifies scope candidates → adds to sprint planning
4. Discussion to clarify and converge
5. Decisions on what to tackle now vs. backlog vs. roadmap

**Key Insight:** The feedback essay often mixes retrospective reflection with forward-looking ideas. This is natural and efficient. The Architect should embrace this and sort it out.

## Roadmap Management

The roadmap is a directional guide, not a contract:
- Created early to capture the anticipated work
- Blocked out and sequenced sensibly
- Evolves sprint by sprint as understanding deepens
- Serves as an anchor point to remember original thinking

## Working with PDT

When a project was designed using PDT (Product Design Thinking), the Architect works as a peer with the Design Partner rather than starting from scratch.

### Initialization from PDT

If `docs/architect_orientation.md` exists, the project was designed with PDT. The orientation is your guided entry point — it provides reading order, priorities, confidence assessments, and active commissions. Read it first during `arch-init`.

### Crossover Channel

PDT and MAM communicate through discrete files in `docs/crossover/`:
- **Commissions** (PDT→MAM): `commission_NNN_request.md` / `commission_NNN_response.md` — PDT requests execution work (validation, prototyping, investigation). Check for open commissions during sprint prep.
- **Consultations** (MAM→PDT): `consult_NNN_request.md` / `consult_NNN_response.md` — When you encounter a design flaw, ambiguity, or trade-off that needs the Design Partner's input, formalize the question via `ask-pdt`.

### Phase Transitions

PDT may update `docs/architect_orientation.md` with new priorities and reading guidance when a new design phase is ready. Check for orientation updates during `arch-resume`.

## Best Practices

### For Architects
1. Keep product docs current - stale docs lose trust
2. Create deltas liberally - better to explore and discard than commit prematurely
3. Write briefs that save time - good context reduces back-and-forth
4. Read implementation logs carefully - reality often differs from plan
5. Reconcile promptly - don't let sprints pile up
6. Check the crossover folder during resume and sprint prep - PDT may have new commissions or orientation updates

### For Implementors
1. Log decisions, not just actions - "why" matters more than "what"
2. Note deviations immediately - don't hide them
3. Ask questions via the log - creates a record
4. Complete phases fully - don't leave partial work
5. Reflect honestly - what went wrong and how to avoid it next time

## Project Patterns

Each project may have specific patterns that should be respected:
- Build tool preferences (bun vs npm, uv for python, etc.)
- Container/deployment patterns
- Testing conventions
- Code style preferences

These are captured in the project's `CLAUDE.md` file and should be honored by both agents.
