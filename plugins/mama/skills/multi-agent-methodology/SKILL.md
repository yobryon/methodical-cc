---
name: multi-agent-methodology
description: Multi-Agent Architecture methodology for complex software projects. Provides guidance on role separation (Architect/Implementor), agent teams for orchestration, incremental design via deltas, structured context handoffs, feedback loops, and sprint-based development. Use when working on projects following this methodology, when planning sprints, creating implementation plans, or managing product documentation.
---

# Multi-Agent Architecture Methodology

This skill provides the foundational methodology for managing complex software projects using a multi-agent approach with distinct Architect and Implementor roles, orchestrated through **agent teams**.

## Core Philosophy

1. **Clear Role Separation**: The Architect owns design, documentation, and orchestration. The Implementor owns code execution and implementation logging.
2. **Incremental Design via Deltas**: Explore design changes in delta documents before committing to the source of truth.
3. **Structured Context Handoffs**: Use briefs and implementation plans to transfer context between agents.
4. **Direct Communication**: Teammates communicate directly when questions arise mid-sprint, rather than logging questions for later.
5. **Persistent Working Knowledge**: The Implementor accumulates expertise across sprints through a compacted state document.
6. **Feedback Loops**: Implementation logs capture reality; feedback cycles capture evolution of thinking.
7. **Reconciliation**: Keep documentation current with reality after each sprint.

## Agent Team Architecture

MAMA uses **agent teams** for orchestration. The Architect is the team lead; the Implementor and UX Designer are teammates.

### Why Teams

- The **user can interact directly** with any teammate -- give the Implementor test feedback, nudge direction, answer questions -- without proxying through the Architect
- Teammates can **message each other directly** -- the Implementor can ask the Architect for clarification mid-sprint instead of just logging the question
- A **shared task list** provides live visibility into sprint progress
- Each teammate has its own **full context window**, enabling deep focused work

### Team Lifecycle

```
Team created ─────────────────────────────────────────── Team cleaned up
     │                                                         │
     │  Sprint 1                Sprint 2              Sprint N │
     │  ┌─────────────────┐     ┌─────────────────┐           │
     │  │ Impl spawned    │     │ Impl spawned    │    ...     │
     │  │ (reads state)   │     │ (reads state)   │           │
     │  │ works phases    │     │ works phases    │           │
     │  │ writes state    │     │ writes state    │           │
     │  │ shuts down      │     │ shuts down      │           │
     │  └─────────────────┘     └─────────────────┘           │
     │                                                         │
     │  UX Designer may be active at any point ────────────── │
```

- **Team**: Created when first needed, persists across sprints for the session
- **Implementor**: Sprint-scoped -- spawned at sprint start, shut down at sprint end
- **UX Designer**: On-demand -- spawned when needed, may persist across sprints

### Inter-Agent Communication

The Implementor should message the Architect when:
- A design question arises that's too significant to guess at
- An unexpected blocker is encountered
- A discovery changes the assumptions the plan was built on
- A scope question needs clarification

The Implementor should NOT message the Architect for:
- Routine implementation decisions within their expertise
- Minor deviations that can be logged and reported at sprint end
- Questions they can answer by reading existing documentation

The Architect should expect mid-sprint messages and respond efficiently -- answer the question, provide the clarification, then let the Implementor continue.

## The Two Agents

### The Architect Agent (Team Lead)

The Architect is the design partner and team lead. Maintains comprehensive understanding, creates deltas, orchestrates implementation, and evolves the product vision.

**Responsibilities:**
- Maintain product documentation (the source of truth)
- Create delta documents for design exploration and capturing new ideas
- Create implementation plans for each sprint
- Write briefs for the Implementor
- Manage the agent team -- spawn teammates, assign work, respond to questions
- Review implementation logs
- Reconcile deltas and discoveries back into product documentation
- Facilitate alignment discussions with the User
- Maintain the Architect state and sprint log in `.mama/`

**Key Artifacts the Architect Produces:**
- Product documentation (structure appropriate to the project)
- `delta_XX_topic.md` - Incremental design explorations and captured ideas
- `docs/sprint/X/implementation_plan.md` - Phase breakdowns for implementors
- `docs/sprint/X/implementor_brief.md` - Context and instructions for the Implementor
- `.mama/architect_state.md` - Running project knowledge and sprint history
- `.mama/sprint_log.md` - Chronological sprint record

### The Implementor Agent (Teammate)

The Implementor executes. Focused on code, not design decisions.

**Responsibilities:**
- Read the implementation plan and brief
- Execute phases in order
- Maintain an implementation log with decisions, discoveries, bugs/fixes, and reflections
- Communicate with the Architect when genuine questions arise
- Update the shared task list as phases are completed
- Report completion status with honest reflection on what went well and what didn't
- Write/update the implementor state document at sprint end

**Key Artifacts the Implementor Produces:**
- Working code
- `docs/sprint/X/implementation_log.md` - Running journal of work done
- `.mama/implementor_state.md` - Compacted working knowledge (updated at sprint end)

**Key Constraint:** The Implementor should NOT make design decisions. When facing ambiguity, message the Architect for clarification, document the question in the log, proceed with a reasonable default, or pause for input.

### The UX Designer (Teammate)

The UX Designer collaborates with the Architect on user experience aspects.

**Responsibilities:**
- Contemplate product documentation and extract UX implications
- Propose design patterns, interaction flows, and visual systems
- Create design documentation appropriate to the project
- Challenge assumptions about user needs and behaviors

## MAMA State Directory

MAMA maintains its internal state in a `.mama/` directory at the project root (alongside `.claude/`). This keeps MAMA's operational state separate from project documentation.

### Structure

```
.mama/
├── architect_state.md      # Architect's running project knowledge
├── implementor_state.md    # Implementor's compacted working memory
└── sprint_log.md           # Chronological sprint record
```

### Scoped Instances

When multiple MAMA instances operate in the same directory (e.g., a multi-product project with separate architects for backend, app, and admin), each instance scopes itself:

```
.mama-backend/
├── architect_state.md
├── implementor_state.md
└── sprint_log.md

.mama-app/
├── architect_state.md
├── implementor_state.md
└── sprint_log.md
```

Scoping is established during `arch-init` when the Architect identifies itself as responsible for a specific component. An unscoped MAMA uses `.mama/` (the default for single-product projects).

### Architect State

The `architect_state.md` file is the Architect's running project knowledge -- similar to the Vesper `.mam/project_state.md` pattern. It contains:
- Project identity and description
- Sprint history with outcomes, key learnings, and tech debt carried
- Current status (phase, stack, design state)
- Anything the Architect needs to remember across sessions

This is updated during `arch-sprint-complete` and `arch-resume`.

### Implementor State

The `implementor_state.md` file captures the Implementor's **tacit knowledge** -- what was learned that can't be recovered from CLAUDE.md, the doc tree, the Architect briefing, or re-reading the code.

**What goes in:**
- Why the codebase is built this way -- rationale behind non-obvious choices, what was considered and rejected
- Project history and load-bearing lessons -- past mistakes or pivots that shaped current work, approaches tried and abandoned with the reason they failed
- Empirical findings -- what experiments and real runs revealed, calibration data, what's actually expensive vs. cheap
- Known gotchas -- non-obvious things that will bite you, hidden dependencies, subtle ordering requirements
- Working context -- how the user works, their expertise, preferences, what they care about
- Build/tooling quirks not covered in CLAUDE.md

**What does NOT go in:**
- Content already in CLAUDE.md (auto-loaded every session)
- Content in docs/ (roadmap, product docs, tech debt trackers) -- reference by path instead
- Sprint logs or implementation log narratives -- the history is in the artifacts
- Anything recoverable from reading the code -- structure, APIs, type signatures

**Lifecycle:**
1. **Sprint 1 (impl-end)**: Implementor reviews its full context and writes `implementor_state.md` from scratch -- the tacit knowledge it accumulated that has no other home
2. **Sprint 2 (impl-begin)**: A fresh Implementor spawns, SessionStart hook loads the state document, priming it with accumulated knowledge before reading the brief
3. **Sprint 2 (impl-end)**: Implementor re-reads its state doc if needed, then **rewrites** it -- a fresh compaction of previous knowledge + new knowledge. Prune superseded empirical data (calibration numbers, performance characteristics have half-lives); carry forward history and rationale (these age well).
4. **Sprint N**: The state doc stays bounded in size because it's been compacted N-1 times. It contains the distilled essence of all prior implementation experience.

**Size discipline:** Aim for a document readable in under 5 minutes. Each rewrite should be the same size or smaller, not growing. This is compaction, not accumulation.

## Document Types

### Product Documentation

The source of truth for the project. Structure and composition depend on the nature of the product.

**Lifecycle:**
1. Created at project inception via `/mama:arch-create-docs`
2. Updated ONLY during reconciliation after sprint completion
3. Preserves decision history (don't delete, annotate or supersede)

**Key Rule:** Never update product docs during active implementation. Updates happen during reconciliation.

### Delta Documents

**Purpose:** Capture new ideas, design changes, and discoveries before committing to the source of truth.

**Naming:** `delta_XX_short_name.md` (e.g., `delta_05_event_system.md`)

**Lifecycle:**
1. Created when new ideas emerge (from feedback, implementation discoveries, etc.)
2. Discussed and refined with User
3. Either approved and queued for implementation, or deferred/discarded
4. Merged into product docs after implementation validates the approach

**Key Rule:** Deltas are working papers. They can be wrong, incomplete, or abandoned. Product docs are the commitment.

### Sprint Artifacts

Sprint artifacts live in `docs/sprint/X/` (or `docs/{scope}/sprint/X/` for scoped instances):

```
docs/sprint/1/
├── implementation_plan.md    # Phase breakdown for the Implementor
├── implementor_brief.md      # Context and instructions
└── implementation_log.md     # Running journal of actual work
```

This hierarchical organization keeps sprint artifacts grouped and prevents `docs/` from getting cluttered over many sprints.

**Implementation Plan:**
- Sprint overview and goals
- Phase list with descriptions
- Task checklists per phase
- File creation/modification expectations
- Dependencies between phases
- Success criteria
- References to relevant deltas

**Implementation Log:**
- Phase-by-phase progress notes
- Decisions made (with rationale)
- Deviations from plan (with reasons)
- Bugs encountered and fixed, with reflection on root cause
- Questions for Architect (and responses received)
- Technical discoveries
- Honest reflection on what could have been done better

**Key Rule:** The Implementor owns the log. The Architect reads it but doesn't edit it.

**Implementor Brief:**
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
1. PLANNING           2. DISCUSSION         3. FINALIZATION
┌─────────────┐      ┌─────────────┐       ┌─────────────┐
│ Arch proposes│ ───> │User + Arch  │ ────> │ Converge &  │
│ initial scope│      │ discuss,    │       │ write plan  │
└─────────────┘      │ align       │       └─────────────┘
                      └─────────────┘             │
                                                  v
6. RECONCILIATION    5. REVIEW            4. IMPLEMENTATION
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│Update docs, │ <─── │Arch reads   │ <─── │ Implementor │
│apply deltas │      │impl log     │      │ executes as │
│update state │      └─────────────┘      │ teammate    │
└─────────────┘                            └─────────────┘
```

### Phase Details

**1. Planning (Architect + User)**
- Architect proposes initial scope for the sprint
- Based on roadmap, previous sprint outcomes, and project state
- Output: Initial scope proposal

**2. Discussion (User + Architect)**
- User shares thinking: reactions, new ideas, reflections, feedback on the proposal
- Architect engages, probes, organizes, extracts deltas
- Drives toward alignment on scope
- Output: Delta documents, refined scope understanding

**3. Finalization (Architect)**
- Converge on final sprint scope
- Write implementation plan with phases
- Write Implementor brief
- Create phase tasks in the shared task list
- Output: Sprint artifacts in `docs/sprint/X/`

**4. Implementation (Implementor Teammate)**
- Implementor spawned as teammate, reads state + brief + plan
- Executes phases in order, updating shared tasks as phases complete
- Messages Architect when genuine questions arise
- User may interact directly with feedback, nudges, test results
- Maintains implementation log
- Output: Working code, implementation log

**5. Review (Implementor + User)**
- Test and verify implementation
- Debug cycle as needed -- user interacts directly with Implementor
- Implementor finalizes log with reflections
- Output: Finalized implementation log

**6. Reconciliation (Architect)**
- Read implementation log
- Update product docs with validated changes
- Apply deltas that were implemented
- Capture discoveries worth preserving
- Update `.mama/architect_state.md` and `.mama/sprint_log.md`
- Propose scope for next sprint
- Output: Updated product docs, updated state, next sprint proposal

## The Discussion Cycle

The discussion cycle is where evolution happens. After implementation:

1. User collects thoughts during implementation (notes, reactions, ideas)
2. User presents these to the Architect via `arch-discuss`
3. Architect engages with the input:
   - Untangles and organizes the content
   - Identifies new ideas -> creates deltas
   - Probes reactions to existing decisions -> drives toward clarity
   - Identifies architectural implications -> flags for discussion
   - Identifies scope candidates -> adds to sprint planning
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

If `docs/architect_orientation.md` exists, the project was designed with PDT. The orientation is your guided entry point -- it provides reading order, priorities, confidence assessments, and active commissions. Read it first during `arch-init`.

### Crossover Channel

PDT and MAM communicate through discrete files in `docs/crossover/`:
- **Commissions** (PDT->MAM): `commission_NNN_request.md` / `commission_NNN_response.md` -- PDT requests execution work (validation, prototyping, investigation). Check for open commissions during sprint prep.
- **Consultations** (MAM->PDT): `consult_NNN_request.md` / `consult_NNN_response.md` -- When you encounter a design flaw, ambiguity, or trade-off that needs the Design Partner's input, formalize the question via `consult-pdt`.
- **Debriefs** (MAM->PDT): `debrief_NNN.md` -- When you reach a milestone (MVP, phase completion, version release), report back to PDT via `debrief-pdt` with an assessment of how the design played out in practice.

### Phase Transitions

PDT may update `docs/architect_orientation.md` with new priorities and reading guidance when a new design phase is ready. Check for orientation updates during `arch-resume`.

## Best Practices

### For Architects
1. Keep product docs current -- stale docs lose trust
2. Create deltas liberally -- better to explore and discard than commit prematurely
3. Write briefs that save time -- good context reduces back-and-forth
4. Read implementation logs carefully -- reality often differs from plan
5. Reconcile promptly -- don't let sprints pile up
6. Check the crossover folder during resume and sprint prep -- PDT may have new commissions or orientation updates
7. Run architectural reviews periodically (every 5-10 sprints) -- codebases fragment faster than you expect
8. Maintain `.mama/architect_state.md` -- your future self needs this context
9. Respond to Implementor messages efficiently -- they're blocked until you answer

### For Implementors
1. Log decisions, not just actions -- "why" matters more than "what"
2. Note deviations immediately -- don't hide them
3. Message the Architect for genuine design questions -- don't just guess
4. Complete phases fully -- don't leave partial work
5. Reflect honestly -- what went wrong and how to avoid it next time
6. Write your state document thoughtfully at sprint end -- your next instance depends on it

## Project Patterns

Each project may have specific patterns that should be respected:
- Build tool preferences (bun vs npm, uv for python, etc.)
- Container/deployment patterns
- Testing conventions
- Code style preferences

These are captured in the project's `CLAUDE.md` file and should be honored by both agents.
