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

MAMA uses Claude Code's **agent-team mailbox protocol** for cross-session orchestration. The team is created and maintained by `mcc` (the methodical-cc helper) — each project has its own team with a non-running phantom "coordinator" lead and a flat roster of real participants. The Architect, the Implementor, and PDT (when present) are **symmetric peers**, each running as its own user-launched Claude Code session.

### Critical: Sessions Are User-Launched, Not Architect-Spawned

Claude Code's flat-roster team protocol prevents teammates from spawning teammates. The Architect therefore does **not** call `TeamCreate` and does **not** call the `Agent` tool to spawn the Implementor. Instead:

> The user launches each session in its own terminal via `mcc create <name> --persona <plugin>:<persona>`, then enters it via `mcc <name>`. Once the Implementor session is running and registered in the team, the Architect addresses it by name with the standard `SendMessage` tool.

**Concrete flow at sprint start:**
1. Architect writes the sprint artifacts (`implementation_plan.md`, kickoff section in `implementation_log.md`)
2. Architect prompts the user to launch the Implementor session: `mcc create impl --persona mama:implementor`
3. User opens a separate terminal, runs the create command, then `mcc impl` to enter the session
4. Architect confirms the Implementor is online (e.g. via `mcc team status` or by sending a ping)
5. Architect sends the kickoff via `SendMessage(to='impl', message='...')` — the Implementor receives it as a turn and starts work

**The UX Designer is a one-shot subagent.** For ad-hoc UX consultation, the Architect calls the `Agent` tool with `subagent_type='ux-designer'` and *no* `team_name`. The result is a single response, not a persistent teammate. If the user wants long-running UX work, they launch a separate `design-ux` session the same way they launch the Implementor.

### Why Sessions Instead of Spawned Teammates

- The **user owns each session's lifecycle** — they can switch terminals, resume independently, and shut down cleanly without orchestration from the Architect
- Each session has its own **full context window** and can be paused/resumed across days
- Sessions communicate via the standard `SendMessage` tool — Claude Code's harness polls each mailbox once a second and delivers messages as turns automatically
- The implementation log's **Phase Progress table** is the durable record of sprint progress (the Implementor maintains it)
- The user can interact with the Implementor directly in its own terminal — no proxying through the Architect

### Team Lifecycle

```
Team set up by mcc (idempotent) ─────────────────────────── Team persists indefinitely
     │                                                                │
     │  Sprint 1                  Sprint 2                Sprint N    │
     │  ┌─────────────────┐       ┌─────────────────┐                 │
     │  │ User launches   │       │ User relaunches │                 │
     │  │ impl session    │       │ impl session    │     ...         │
     │  │ Arch sends      │       │ Arch sends      │                 │
     │  │   kickoff via   │       │   kickoff via   │                 │
     │  │   SendMessage   │       │   SendMessage   │                 │
     │  │ Impl works,     │       │ Impl works,     │                 │
     │  │   writes state  │       │   writes state  │                 │
     │  │ User exits impl │       │ User exits impl │                 │
     │  └─────────────────┘       └─────────────────┘                 │
     │                                                                 │
     │  UX subagent calls happen on demand from the Architect ──────── │
```

- **Team**: Set up once (by `mcc team setup` or implicitly on first `mcc create`/`mcc <name>`); persists across sprints and across days
- **Implementor session**: Often spans many sprints — the user keeps it open and runs `/mama:impl-end` at the end of each sprint, but the underlying Claude Code session can persist across sprints (compaction handles in-session context). The on-disk `implementor_state.md` is written on demand (e.g., before closing the session for an extended break or starting a fresh session), not every sprint.
- **UX Designer**: One-shot subagent for routine consults; user-launched `design-ux` session for sustained design work

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

**Channel taxonomy.** Three channels for inter-agent communication, each with a different latency and disruption profile:

- **chat-mode `SendMessage`**: urgent clarification or quick acknowledgment. Interrupts the recipient's flow as a new turn. Use when the answer is needed *now*.
- **consult-mode `SendMessage` + Write**: substantive design question worth a structured artifact. The artifact lives at `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md`; the framing message references it. Use for design questions that deserve considered responses and a durable record.
- **Implementation-log sub-entry (architect → implementor only)**: non-urgent followup that doesn't need to interrupt mid-flow. The Architect queues it as a sub-bullet under the relevant phase entry in the implementation log; the Implementor picks it up at sprint-close cleanup. Use when the followup can wait until natural cleanup time and shouldn't pull impl out of flow state.

Examples of items that fit the implementation-log sub-entry channel: a tooling fix the architect notices mid-sprint, a constraint the user lifts mid-flow, a small cleanup item that emerged from architect dogfood. None of these are urgent enough to warrant a SendMessage round-trip; queueing them under the relevant phase entry preserves impl's focus and ensures they're not forgotten.

### Task tooling under MAMA

The implementation log's **Phase Progress table** is the canonical sprint progress record (impl owns it; arch reads it). It's the durable record of "did each phase land, and how" — visible to all teammates via the file, persisted across sessions.

Claude Code's **team task tools** (`TaskCreate`/`TaskUpdate`/`TaskList`) are a separate coordination surface with different semantics: tasks have owners, dependencies, and cross-session persistence. They're appropriate when the work shape calls for them:

- Parallel implementors working on independent phases simultaneously
- Cross-session task handoffs where progress visibility across conversation gaps is the bottleneck
- Explicit dependency tracking across teammates ("phase B blocked by phase A's API decision")

They're **unnecessary** for sequential single-conversation sprints where the implementation log already captures progress. Claude Code's "consider TaskCreate" reminder is conditional ("if your work would benefit"); it's appropriately ignored when the work doesn't fit the team-coordination shape.

The decision rule: *does this work actually need cross-teammate or cross-session task coordination beyond what the implementation log provides?* If yes, use Tasks; if no, the nudge is informational and you can move on.

## The Two Agents

### The Architect Agent (Team Lead)

The Architect is the design partner and team lead. Maintains comprehensive understanding, creates deltas, orchestrates implementation, and evolves the product vision.

**Responsibilities:**
- Maintain product documentation (the source of truth)
- Create delta documents for design exploration and capturing new ideas
- Create implementation plans for each sprint
- Write briefs for the Implementor
- Coordinate the team -- prompt the user to launch teammate sessions, send kickoffs and clarifications via `SendMessage`, respond to incoming questions
- Review implementation logs
- Reconcile deltas and discoveries back into product documentation
- Facilitate alignment discussions with the User
- Maintain the Architect state and sprint log in `.mcc/`

**Key Artifacts the Architect Produces:**
- Product documentation (structure appropriate to the project)
- `delta_XX_topic.md` - Incremental design explorations and captured ideas
- `docs/sprint/X/implementation_plan.md` - Phase breakdowns for implementors
- The spawn prompt (recorded as the `## Sprint Kickoff` section at the top of `implementation_log.md`) - orientation, rationale, sprint-specific constraints
- `.mcc/architect_state.md` - Running project knowledge and sprint history
- `.mcc/sprint_log.md` - Chronological sprint record

### The Implementor Agent (Teammate)

The Implementor executes. Focused on code, not design decisions.

**Responsibilities:**
- Read the spawn prompt (durable record in the log's `## Sprint Kickoff` section) and the implementation plan
- Execute phases in order
- Maintain an implementation log with decisions, discoveries, bugs/fixes, and reflections
- Communicate with the Architect when genuine questions arise
- Update the Phase Progress table in the implementation log as phases are completed (and optionally use `TaskCreate` for your own private todos if helpful)
- Report completion status with honest reflection on what went well and what didn't
- Write/update the implementor state document at sprint end

**Key Artifacts the Implementor Produces:**
- Working code
- `docs/sprint/X/implementation_log.md` - Running journal of work done
- `.mcc/implementor_state.md` - Compacted working knowledge (updated at sprint end)

**Key Constraint:** The Implementor should NOT make design decisions. When facing ambiguity, message the Architect for clarification, document the question in the log, proceed with a reasonable default, or pause for input.

### The UX Designer (Teammate)

The UX Designer collaborates with the Architect on user experience aspects.

**Responsibilities:**
- Contemplate product documentation and extract UX implications
- Propose design patterns, interaction flows, and visual systems
- Create design documentation appropriate to the project
- Challenge assumptions about user needs and behaviors

## MAMA State Directory

MAMA maintains its internal state in a `.mcc/` directory at the project root (alongside `.claude/`). This keeps MAMA's operational state separate from project documentation.

### Structure

```
.mcc/
├── architect_state.md      # Architect's running project knowledge
├── implementor_state.md    # Implementor's compacted working memory
└── sprint_log.md           # Chronological sprint record
```

### Scoped Instances

When multiple MAMA instances operate in the same directory (e.g., a multi-product project with separate architects for backend, app, and admin), each instance scopes itself:

```
.mcc-backend/
├── architect_state.md
├── implementor_state.md
└── sprint_log.md

.mcc-app/
├── architect_state.md
├── implementor_state.md
└── sprint_log.md
```

Scoping is established during `arch-init` when the Architect identifies itself as responsible for a specific component. An unscoped MAMA uses `.mcc/` (the default for single-product projects).

### Architect State

The `architect_state.md` file is the Architect's running project knowledge -- similar to the Vesper `.mcc/project_state.md` pattern. It contains:
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
2. **Sprint 2 (arch-sprint-start)**: User relaunches the Implementor session; SessionStart hook loads `implementor_state.md`, priming it with accumulated knowledge before the Architect's kickoff `SendMessage` arrives
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
└── implementation_log.md     # Running journal — opens with the Sprint Kickoff section (the spawn prompt verbatim)
```

In MAMA there is no separate brief document. Orientation that briefs used to provide is now the **spawn prompt**, sent directly to the Implementor and recorded as the `## Sprint Kickoff` section at the top of the implementation log. This eliminates duplication and concentrates effort on the artifact the Implementor actually engages with first.

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

**Sprint Kickoff (the prompt, recorded in the log):**

Two parts: sprint-specific content + a standing protocol pulse.

*Sprint-specific (varies):*
- Identity and sprint number
- Plan path and state doc path
- 2–3 sprint-specific gotchas or conventions
- 1 sentence of "why this sprint matters" if non-obvious

*Standing protocol pulse (paste verbatim every sprint):*
- Bus is the channel — SendMessage, never courier files
- Tag substantive messages: `[HANDOFF]`, `[CONSULT]`
- Default to proceeding; message arch on real ambiguity
- Finalize via `/mama:impl-end`; exit conditions live in the plan
- Memory discipline: default-no on CLAUDE.md / architect_state additions; clear the four `pattern-add` gates first; lead with the rule

Target: ~100–150 words of sprint-specific content. The plan, persona, and CLAUDE.md are already loaded — the kickoff doesn't restate them. The protocol pulse is small and important: it's the per-sprint drumbeat that keeps long-running projects from drifting on bus conventions across compactions.

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

**3. Finalization & Kickoff (Architect)**
- Converge on final sprint scope
- Write implementation plan with phases
- Compose the spawn prompt and record it as the `## Sprint Kickoff` section at the top of the implementation log
- (Skip task creation — the Implementor manages its own progress in the implementation log's Phase Progress table)
- Prompt the user to launch the Implementor session; once it's online, send the kickoff via `SendMessage(to='impl', ...)` (`arch-sprint-start`)
- Output: Sprint artifacts in `docs/sprint/X/`, Implementor running in its own session

**4. Implementation (Implementor Teammate)**
- Implementor reads state + plan + log (kickoff section)
- Executes phases in order, updating the Phase Progress table in the log
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
- Update `.mcc/architect_state.md` and `.mcc/sprint_log.md`
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

### Crossover via the Bus

PDT and MAMA communicate over the **bus** plugin — built on Claude Code's agent-team protocol. Each project has its own team (managed by `mcc`); each session joins as a teammate addressable by name; messages flow via the standard `SendMessage` tool. The bus must be enabled in the project (`mcc team setup`, or any `mcc <name>` does it implicitly) and both sessions must have registered identities (via `/{plugin}:session set <name>` or `mcc create <name>`).

Three categories of crossover, all using `SendMessage` for the channel and the `Write` tool for durable artifacts:

- **Commissions** (PDT→Architect): PDT writes a commission artifact at `docs/crossover/{thread_id}/001-pdt-commission.md` and sends a framing `SendMessage(to='arch', message='[CONSULT] {thread_id}\\n\\n...')`. The Architect receives it as a turn and acts on it. Check for active commission threads during sprint prep.
- **Consultations** (Architect→PDT): Use `/mama:consult-pdt` when you hit a design flaw, ambiguity, or trade-off that needs PDT's input. The command composes a structured artifact and sends a framing message. PDT responds on the same thread.
- **Debriefs** (Architect→PDT): Use `/mama:debrief-pdt` when you reach a milestone (MVP, phase completion, version release). Same mechanism.

All consult-mode crossover produces **durable artifacts** in `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md` — citable forever, separate from the bus message body. Threading is sender-declared kebab-case (e.g. `consult-013-pref-storage-shape`).

Inbound bus messages arrive automatically as new turns (the harness polls each session's inbox at `~/.claude/teams/<team>/inboxes/<your-name>.json`); no polling needed on your part. The `bus-protocol` skill (in the bus plugin) covers full protocol details, including the chat-vs-consult discipline distinction.

### Phase Transitions

PDT may update `docs/architect_orientation.md` with new priorities and reading guidance when a new design phase is ready. Check for orientation updates during `arch-resume`.

## Best Practices

### For Architects
1. Keep product docs current -- stale docs lose trust
2. Create deltas liberally -- better to explore and discard than commit prematurely
3. Write briefs that save time -- good context reduces back-and-forth
4. Read implementation logs carefully -- reality often differs from plan
5. Reconcile promptly -- don't let sprints pile up
6. Check the SessionStart bus block and `mcc team status` for active threads -- PDT may have sent commissions or there may be open consults awaiting your response
7. Run architectural reviews periodically (every 5-10 sprints) -- codebases fragment faster than you expect
8. Maintain `.mcc/architect_state.md` -- your future self needs this context
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
