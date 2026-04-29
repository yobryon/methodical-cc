---
name: multi-agent-methodology
description: Multi-Agent Architecture methodology for complex software projects. Provides guidance on role separation (Architect/Implementor), incremental design via deltas, structured context handoffs, feedback loops, and sprint-based development. Use when working on projects following this methodology, when planning sprints, creating implementation plans, or managing product documentation.
---

# Multi-Agent Architecture Methodology

This skill provides the foundational methodology for managing complex software projects using a multi-agent approach with distinct Architect and Implementor roles.

## Core Philosophy

1. **Clear Role Separation**: The Architect owns design, documentation, and orchestration. The Implementor owns code execution and implementation logging.
2. **Incremental Design via Deltas**: Explore design changes in delta documents before committing to the source of truth.
3. **Structured Context Handoffs**: Use briefs and implementation plans to transfer context between sessions.
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
- Maintain the `.mam/` state directory with running project knowledge

**Key Artifacts the Architect Produces:**
- Product documentation (structure appropriate to the project)
- `delta_XX_topic.md` - Incremental design explorations and captured ideas
- `docs/sprint/X/implementation_plan.md` - Phase breakdowns for implementors
- `docs/sprint/X/implementor_brief.md` - Context and instructions for the Implementor

### The Implementor Agent

In MAM, the user runs the Implementor session directly. The Implementor executes, focused on code, not design decisions.

**Responsibilities:**
- Read the implementation plan and brief
- Execute phases in order
- Maintain an implementation log with decisions, discoveries, bugs/fixes, and reflections
- Flag questions or blockers for the Architect
- Report completion status with honest reflection on what went well and what didn't

**Key Artifacts the Implementor Produces:**
- Working code
- `docs/sprint/X/implementation_log.md` - Running journal of work done

**Key Constraint:** The Implementor should NOT make design decisions. When facing ambiguity, document the question in the log, proceed with a reasonable default, or pause for Architect input.

## MAM State Directory

MAM keeps its internal operational state in `.mam/` at the project root (or `.mam-{scope}/` for multi-product projects):

```
.mam/
├── architect_state.md      # Architect's running project knowledge
└── sprint_log.md           # Chronological sprint record
```

This separates MAM's internal bookkeeping from the project's `docs/` directory.

**`architect_state.md`** contains:
- Project identity and scope
- Sprint history with outcomes and key learnings
- Current status (which sprint, what phase)
- Tech debt carried forward
- Important architectural decisions and patterns discovered
- Version stamp for upgrade compatibility

**`sprint_log.md`** contains:
- Chronological entries for each sprint: date, status, summary, key learnings, deviations, tech debt

### Scoped Instances

For multi-product projects sharing a working directory, each MAM instance scopes itself:

```
.mam-backend/     # Backend architect's state
.mam-app/         # App architect's state  
.mam-admin/       # Admin architect's state
```

Scope is established during `arch-init` when the Architect identifies its product focus. Sprint artifacts follow the same scoping:

```
docs/backend/sprint/1/{implementation_plan,implementor_brief,implementation_log}.md
docs/app/sprint/1/{implementation_plan,implementor_brief,implementation_log}.md
```

An unscoped MAM uses `.mam/` and `docs/sprint/X/` — the default for single-product projects.

## Document Types

### Product Documentation

The source of truth for the project. Structure and composition depend on the nature of the product:
- Could be a single comprehensive design document
- Could be multiple focused documents for major components
- Could include user stories, architecture docs, API specs, etc.

**The Architect should recognize what documentation structure serves the project best and propose accordingly.**

**Lifecycle:**
1. Created at project inception via `/mam:arch-create-docs`
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

### Sprint Artifacts

Sprint artifacts are organized hierarchically under `docs/sprint/X/` (or `docs/{scope}/sprint/X/` for scoped instances):

**Implementation Plan** (`implementation_plan.md`):
- Sprint overview and goals
- Phase list with descriptions
- Task checklists per phase
- File creation/modification expectations
- Dependencies between phases
- Success criteria
- References to relevant deltas

**Implementation Log** (`implementation_log.md`):
- Phase-by-phase progress notes
- Decisions made (with rationale)
- Deviations from plan (with reasons)
- Bugs encountered and fixed, with reflection on root cause
- Questions for Architect
- Technical discoveries
- Honest reflection on what could have been done better

**Implementor Brief** (`implementor_brief.md`):
- Preamble establishing the Implementor's role and expertise expectations
- Project context (minimal, relevant)
- Current state summary
- What has already been decided
- What files/systems are relevant
- What NOT to touch
- Reference to the implementation plan
- Instructions for maintaining the implementation log

**Key Rule:** The Implementor owns the log. The Architect reads it but doesn't edit it.

## The Sprint Lifecycle

### Sprint Structure

A sprint is a coherent chunk of work with a clear outcome:
- Large enough to require multiple implementation phases
- Small enough to complete before major design pivots
- Named and numbered (Sprint 1, Sprint 2, etc.)

### Sprint Phases

```
1. PLANNING           2. DISCUSSION         3. FINALIZATION
┌─────────────┐      ┌─────────────┐       ┌─────────────┐
│ Arch proposes│ ───▶ │User + Arch  │ ────▶ │ Converge &  │
│ initial scope│      │ discuss,    │       │ write plan  │
└─────────────┘      │ align       │       └─────────────┘
                      └─────────────┘             │
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

**2. Discussion (User + Architect)**
- User shares thinking: reactions, new ideas, reflections, feedback on the proposal
- Can include retrospective on previous sprint AND forward-looking thoughts
- Architect engages, probes, organizes, extracts deltas
- Drives toward alignment on scope
- Output: Delta documents, refined scope understanding

**3. Finalization (Architect)**
- Converge on final sprint scope
- Write implementation plan with phases
- Write Implementor brief
- Create sprint directory at `docs/sprint/X/`
- Output: `docs/sprint/X/implementation_plan.md`, `docs/sprint/X/implementor_brief.md`

**4. Implementation (Implementor)**
- Read brief and plan
- Execute phases in order
- Maintain implementation log
- Flag blockers or questions
- Output: Working code, `docs/sprint/X/implementation_log.md`

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
- Update `.mam*/architect_state.md` and `sprint_log.md`
- Propose scope for next sprint
- Output: Updated product docs, updated MAM state, next sprint proposal

## The Discussion Cycle

The discussion cycle is where evolution happens. After implementation:

1. User collects thoughts during implementation (notes, reactions, ideas)
2. User presents these to the Architect via `arch-discuss`
3. Architect engages with the input:
   - Untangles and organizes the content
   - Identifies new ideas → creates deltas
   - Probes reactions to existing decisions → drives toward clarity
   - Identifies architectural implications → flags for discussion
   - Identifies scope candidates → adds to sprint planning
4. Together they clarify and converge
5. Decisions on what to tackle now vs. backlog vs. roadmap

**Key Insight:** User input often mixes retrospective reflection with forward-looking ideas. This is natural and efficient. The Architect should embrace this and sort it out.

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

### Crossover via the Bus

PDT and MAM communicate over the **bus** plugin — a Channels-based MCP server that lets sessions message each other directly. The bus must be installed and enabled in the project (`mcc bus setup`) and both sessions must have registered identities (via `/{plugin}:session set <name>`).

Three categories of crossover, all going through `peer_send` with `mode='consult'`:

- **Commissions** (PDT→Architect): PDT sends a commission via `peer_send(to='arch', mode='consult', artifact_type='commission', ...)`. The Architect receives it as a `<channel mode='consult' from='pdt'>` notification and acts on it. The artifact lives at `docs/crossover/{thread_id}/`. Check for active commission threads during sprint prep.
- **Consultations** (Architect→PDT): Use `/mam:consult-pdt` when you hit a design flaw, ambiguity, or trade-off that needs PDT's input. The command composes a structured artifact and sends via `peer_send`. PDT responds on the same thread.
- **Debriefs** (Architect→PDT): Use `/mam:debrief-pdt` when you reach a milestone (MVP, phase completion, version release). Same mechanism.

All consult-mode messages produce **durable artifacts** in `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md` — citable forever, separate from the ephemeral channel notification body. Threading is sender-declared kebab-case (e.g. `consult-013-pref-storage-shape`).

Inbound `<channel>` notifications arrive automatically; no polling needed. The `bus-protocol` skill (in the bus plugin) covers full protocol details. If the bus isn't installed, fall back to discussing with the user about manual courier — but install the bus to remove that friction.

### Phase Transitions

PDT may update `docs/architect_orientation.md` with new priorities and reading guidance when a new design phase is ready. Check for orientation updates during `arch-resume`.

## Best Practices

### For Architects
1. Keep product docs current - stale docs lose trust
2. Create deltas liberally - better to explore and discard than commit prematurely
3. Write briefs that save time - good context reduces back-and-forth
4. Read implementation logs carefully - reality often differs from plan
5. Reconcile promptly - don't let sprints pile up
6. Check the SessionStart bus digest and `peer_list` for active threads - PDT may have sent commissions or there may be open consults awaiting your response
7. Run architectural reviews periodically (every 5-10 sprints) - codebases fragment faster than you expect, and sprint-level reconciliation doesn't catch systemic drift
8. Keep `.mam*/architect_state.md` current - it is your running memory across sessions

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
