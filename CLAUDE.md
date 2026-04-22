# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains Claude Code plugins for structured product design and implementation workflows. Three plugins: PDT for pre-implementation product design thinking, MAM and MAMA for sprint-based implementation with distinct Architect and Implementor roles.

## Plugin Structure

This plugin follows the Claude Code plugin specification:

```
methodical-cc/
├── .claude-plugin/
│   └── marketplace.json         # Marketplace advertising all three plugins
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
│   └── mama/                    # Team-based implementation
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── skills/
│       ├── commands/
│       ├── agents/
│       │   ├── ux-designer/     # UX Designer teammate definition
│       │   └── implementor/     # Implementor teammate definition
│       └── hooks/
├── tools/                       # Migration and utility scripts
├── docs/                        # Design-time documentation (not part of plugins)
└── README.md
```

**Critical**: `commands/`, `skills/`, `hooks/`, and `agents/` must be at the **plugin root**, NOT inside `.claude-plugin/`.

## Three Plugin Variants

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
- Commands namespaced as `/mama:arch-init`, `/mama:impl-begin`, etc.
- User can interact directly with Implementor and UX Designer teammates
- Implementor maintains persistent working knowledge via compacted state document
- MAMA internal state kept in `.mama/` (or `.mama-{scope}/` for multi-product)
- Sprint artifacts organized hierarchically: `docs/sprint/X/`
- Requires agent teams feature enabled

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
- `/arch-sprint-start` - Lock scope, write plan and brief
- `/arch-sprint-complete` - Process completed sprint, reconcile docs (auto-loads context)
- `/arch-review` - Architectural review of codebase against design intent
- `/consult-pdt` - Formalize a design question for PDT, write a consultation request
- `/commission-complete` - Report results of a PDT commission
- `/debrief-pdt` - Report back to PDT after a milestone with implementation assessment
- `/ux-consult` - Collaborate with UX Designer teammate

### Implementor Commands
- `/impl-begin` - Begin implementation (MAM: read brief; MAMA: spawn Implementor teammate)
- `/impl-end` - Wrap up implementation, write state, shut down Implementor

### Shared Commands
- `/pattern-add` - Add or update a project pattern in CLAUDE.md

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
- **Implementor Brief**: Context handoff document
- **Implementation Log**: Running journal of actual work

### Sprint Lifecycle
1. Prep → 2. Discuss → 3. Start → 4. Begin (implementation) → 5. End (implementation) → 6. Complete

## Advanced Features

### SessionStart Hook
On session start, the plugin auto-detects project state:
- Checks for `.mama/` or `.mama-{scope}/` state directories
- Reads architect state for sprint history
- Falls back to scanning `CLAUDE.md` and `docs/` if no state directory exists
- Displays detected state and invites correction ("We're actually in sprint X")

### MAMA State Directory
MAMA keeps its internal state in `.mama/` (or `.mama-{scope}/` for multi-product projects):
- `architect_state.md` - Architect's running project knowledge and sprint history
- `implementor_state.md` - Implementor's compacted working memory across sprints
- `sprint_log.md` - Chronological sprint record

### Agent Teams
MAMA uses agent teams for orchestration:
- Architect is the team lead
- Implementor and UX Designer are spawned as teammates
- User can interact directly with any teammate (Shift+Down to cycle, or split panes)
- Teammates communicate directly via SendMessage
- Shared task list provides live sprint progress visibility
- Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

### Implementor Persistent Working Knowledge
The Implementor accumulates expertise across sprints via `implementor_state.md`:
- Written at sprint end (impl-end), compacting everything learned
- Loaded automatically at sprint start via SessionStart hook in the agent definition
- Rewritten (not appended) each sprint -- stays bounded through compaction

### Context Loading
Key commands prompt Claude to read relevant files before proceeding:
- `arch-sprint-prep` - Reads architect state, roadmap, active deltas
- `arch-sprint-complete` - Reads implementation log, updates architect state and sprint log
- `impl-begin` - Spawns Implementor teammate with brief, plan, and state references
- `arch-resume` - Reads `.mama*/` state for session resumption

## Development Notes

- The `docs/` directory contains the original design documents from the design session (kept for reference)
- Plugin names are `pdt`, `mam`, and `mama` for brevity, so commands are invoked as `/pdt:init`, `/mam:arch-init`, `/mama:arch-init` etc.
- To test changes, restart Claude Code with `claude --plugin-dir ./`
