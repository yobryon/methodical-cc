# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains Claude Code plugins for structured product design and implementation workflows. Four plugins: PDT for pre-implementation product design thinking, MAM and MAMA for sprint-based implementation with distinct Architect and Implementor roles, and Bus for peer messaging across Claude Code sessions (eliminates user-as-courier between PDT and MAM/MAMA).

## Plugin Structure

This plugin follows the Claude Code plugin specification:

```
methodical-cc/
├── .claude-plugin/
│   └── marketplace.json         # Marketplace advertising all four plugins
├── plugins/
│   ├── pdt/                     # Product Design Thinking
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/
│   │   ├── commands/
│   │   └── hooks/
│   ├── mam/                     # Session-based implementation
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/
│   │   ├── commands/
│   │   ├── agents/
│   │   │   └── ux-designer/
│   │   └── hooks/
│   ├── mama/                    # Team-based implementation
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/
│   │   ├── commands/
│   │   ├── agents/
│   │   │   ├── ux-designer/     # UX Designer teammate definition
│   │   │   └── implementor/     # Implementor teammate definition
│   │   └── hooks/
│   └── bus/                     # Peer messaging bus (agent-team mailbox)
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── hooks/               # SessionStart hook for team membership orientation
│       ├── skills/
│       └── commands/
├── tools/                       # Migration and utility scripts (mcc, etc.)
├── docs/                        # Design-time documentation (not part of plugins)
└── README.md
```

**Critical**: `commands/`, `skills/`, `hooks/`, and `agents/` must be at the **plugin root**, NOT inside `.claude-plugin/`.

## Four Plugin Variants

### PDT (Product Design Thinking)
Pre-implementation product design workflow with a Socratic Design Partner.
- Commands namespaced as `/pdt:init`, `/pdt:discuss`, `/pdt:capture`, etc.
- Single role: Design Partner (no Architect/Implementor split)
- Produces design documents, decisions log, concept backlog
- Natural predecessor to MAM/MAMA -- design first, then implement

### MAM (Multi-Agent Methodology)
Session-based workflow where you run Architect and Implementor as separate Claude sessions.
- Commands namespaced as `/mam:arch-init`, `/mam:impl-begin`, etc.
- Handoff via document files (briefs, plans, logs)
- Good for explicit context separation

### MAMA (Multi-Agent Methodology with Agents)
Team-based workflow where Architect orchestrates Implementor and UX Designer as agent teammates.
- Commands namespaced as `/mama:arch-init`, `/mama:arch-sprint-start`, etc.
- User can interact directly with Implementor and UX Designer teammates
- Implementor maintains persistent working knowledge via compacted state document
- All operational state unified under `.mcc/` (or `.mcc-{scope}/` for multi-product)
- Sprint artifacts organized hierarchically: `docs/sprint/X/`
- Requires agent teams feature enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)

### Bus (Peer Messaging)
Built on Claude Code's native agent-team mailbox protocol. Sessions in a project join a shared team and message each other via the standard `SendMessage` tool — no MCP server, no extra dependencies.
- Replaces user-as-courier between PDT and MAM/MAMA workflows
- Two modes: `chat` (lightweight, ephemeral) and `consult` (durable, produces artifact in `docs/crossover/{thread_id}/`)
- Identity comes from existing session-name registry in `.mcc/sessions` (`/{plugin}:session set <name>`)
- Send: native `SendMessage`. Receive: harness polls each session's mailbox automatically once a second
- Set up implicitly when launching any session via `mcc <name>` or `mcc create <name>`; manual setup via `mcc team setup`
- Full design at `docs/bus-design.md`

## Commands

### PDT Commands
- `/init` - Survey existing materials, classify, produce reading guide
- `/read` - Deep-read materials, produce synthesis
- `/discuss` - Discuss ideas, process feedback, explore concepts with the Design Partner
- `/capture` - Write things down -- deltas, document updates, decisions, or the full documentation bundle
- `/decide` - Record a resolved decision with rationale
- `/research` - Research a topic in-session or write a brief for external research
- `/gaps` - Assess what is done, partial, open, deferred
- `/backlog` - Update/review concept development backlog
- `/next` - Figure out what's workable and highest-value for this session
- `/coherence` - Cross-document consistency audit with optional fix application
- `/commission` - Commission work from MAM (validation, prototyping, investigation)
- `/orient` - Write/update architect orientation for initial launch or phase transitions
- `/consult` - Process a design question from the Architect, write a formal response
- `/debrief` - Process an implementation debrief from the Architect, evaluate and evolve the design
- `/resume` - Re-establish context on in-flight design effort

### Architect Commands
- `/arch-init` - Initialize project, set patterns, establish Architect role (reads PDT orientation if present)
- `/arch-resume` - Resume in-flight project, establish/correct current state (checks crossover for new items)
- `/arch-discuss` - Discuss ideas, process feedback, explore architecture with the user
- `/arch-create-docs` - Create initial product documentation
- `/arch-roadmap` - Create implementation roadmap
- `/arch-sprint-prep` - Prepare sprint proposal (auto-loads context, checks for PDT commissions)
- `/arch-sprint-start` - Lock scope, write plan and brief (MAMA: also spawns Implementor and begins work)
- `/arch-sprint-complete` - Process completed sprint, reconcile docs (auto-loads context)
- `/arch-review` - Architectural review of codebase against design intent
- `/consult-pdt` - Formalize a design question for PDT, write a consultation request
- `/commission-complete` - Report results of a PDT commission
- `/debrief-pdt` - Report back to PDT after a milestone with implementation assessment
- `/ux-consult` - Collaborate with UX Designer teammate

### Implementor Commands
- `/mam:impl-begin` - Begin implementation (MAM only: read brief, start execution in Implementor session)
- `/impl-end` - Wrap up implementation, write state, shut down Implementor
- `/mam:impl-export` - Export accumulated implementation knowledge to state document (MAM only)

### Shared Commands
- `/pattern-add` - Add or update a project pattern in CLAUDE.md
- `/upgrade` - Upgrade project artifacts to current plugin version (MAMA also handles MAM → MAMA migration)
- `/session` - Register or recall session IDs for quick resumption by persona name (uses UserPromptSubmit hook to capture session ID)

## Command File Format

Commands are markdown files with YAML frontmatter:

```markdown
---
description: Brief description for Claude's context
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Command Title

Instructions for Claude when this command is invoked.

$ARGUMENTS
```

- `$ARGUMENTS` is replaced with user input when invoked
- `allowed-tools` restricts which tools Claude can use during command execution

## Testing the Plugins

```bash
# Test PDT locally
claude --plugin-dir ./plugins/pdt

# Test MAM locally
claude --plugin-dir ./plugins/mam

# Test MAMA locally
claude --plugin-dir ./plugins/mama

# Invoke commands
/pdt:init         # for PDT
/mam:arch-init    # for MAM
/mama:arch-init   # for MAMA
```

## Key Concepts

### Two-Agent Model
- **Architect**: Design partner - maintains docs, creates deltas, plans sprints, writes briefs
- **Implementor**: Execution partner - follows plans, maintains logs, flags questions

### Document Types
- **Product Docs**: Source of truth (in target project's `docs/`)
- **Deltas**: Design explorations (`delta_XX_name.md`) - working papers, not commitments
- **Implementation Plan**: Phase-by-phase breakdown for sprints
- **Implementor Brief**: Context handoff document (MAM only — MAMA replaces this with the spawn prompt recorded in the log's Sprint Kickoff section)
- **Implementation Log**: Running journal of actual work (MAMA: opens with Sprint Kickoff section containing the spawn prompt)

### Sprint Lifecycle
1. Prep → 2. Discuss → 3. Start → 4. Begin (implementation) → 5. End (implementation) → 6. Complete

## Advanced Features

### SessionStart Hook
On session start, the plugin auto-detects project state:
- Checks for `.mcc/` or `.mcc-{scope}/` state directories
- Reads architect state for sprint history
- Falls back to scanning `CLAUDE.md` and `docs/` if no state directory exists
- Displays detected state and invites correction ("We're actually in sprint X")

### Unified `.mcc/` State Directory
All operational state lives under `.mcc/` (or `.mcc-{scope}/` for multi-product projects):
- `sessions` - registered session identities for the project
- `architect_state.md` - Architect's running project knowledge and sprint history
- `implementor_state.md` - Implementor's compacted working memory across sprints
- `sprint_log.md` - Chronological sprint record
- `bus/inbox/` - per-session inbox staging used by the bus plugin

### Agent Teams
The bus plugin uses a phantom-lead team pattern:
- All real participants (PDT, Architect, Implementor, UX) are symmetric peers
- A non-running phantom "coordinator" satisfies Claude Code's flat-roster requirement
- Teammates cannot spawn other teammates — the user launches each session via `mcc create <name>` and resumes via `mcc <name>`
- For long-running UX work, launch a separate `design-ux` session; for one-shots the Architect uses the Agent tool (subagent semantics)
- Shared task list provides live sprint progress visibility
- Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (set automatically by `mcc team setup`)

### Implementor Persistent Working Knowledge
The Implementor accumulates expertise across sprints via `implementor_state.md`:
- Written at sprint end (impl-end), compacting everything learned
- Loaded automatically at sprint start via SessionStart hook in the agent definition
- Rewritten (not appended) each sprint -- stays bounded through compaction

### Context Loading
Key commands prompt Claude to read relevant files before proceeding:
- `arch-sprint-prep` - Reads architect state, roadmap, active deltas
- `arch-sprint-complete` - Reads implementation log, updates architect state and sprint log
- `arch-sprint-start` (MAMA) - Writes sprint artifacts and sends kickoff `SendMessage` to the user-launched Implementor session
- `mam:impl-begin` - Reads brief, plan, and state references in the Implementor session
- `arch-resume` - Reads `.mcc*/` state for session resumption

## Development Notes

- The `docs/` directory contains the original design documents from the design session (kept for reference)
- Plugin names are `pdt`, `mam`, `mama`, and `bus` for brevity, so commands are invoked as `/pdt:init`, `/mam:arch-init`, `/mama:arch-init`, `/bus:status`, etc.
- To test changes, restart Claude Code with `claude --plugin-dir ./`

## Contributing

The bus plugin is now pure-Python/shell — no Node, no MCP server, no build step. Plugin changes can be tested directly with `claude --plugin-dir ./`.
