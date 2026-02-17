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
│   └── mama/                    # Subagent-based implementation
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── skills/
│       ├── commands/
│       ├── agents/
│       │   ├── ux-designer/
│       │   └── implementor/     # Implementor as subagent
│       └── hooks/
├── tools/                       # Migration and utility scripts
├── docs/                        # Design-time documentation (not part of plugins)
└── README.md
```

**Critical**: `commands/`, `skills/`, `hooks/`, and `agents/` must be at the **plugin root**, NOT inside `.claude-plugin/`.

## Three Plugin Variants

### PDT (Product Design Thinking)
Pre-implementation product design workflow with a Socratic Design Partner.
- Commands namespaced as `/pdt:init`, `/pdt:discuss`, `/pdt:crystallize`, etc.
- Single role: Design Partner (no Architect/Implementor split)
- Produces design documents, decisions log, concept backlog
- Natural predecessor to MAM/MAMA -- design first, then implement

### MAM (Multi-Agent Methodology)
Session-based workflow where you run Architect and Implementor as separate Claude sessions.
- Commands namespaced as `/mam:arch-init`, `/mam:impl-begin`, etc.
- Handoff via document files (briefs, plans, logs)
- Good for explicit context separation

### MAMA (Multi-Agent Methodology with Agents)
Subagent-based workflow where Architect orchestrates Implementor and UX Designer as persistent subagents.
- Commands namespaced as `/mama:arch-init`, `/mama:impl-begin`, etc.
- Implementor and UX Designer maintain context across sessions via resume
- Good for context continuity across sprints

## Commands

### PDT Commands
- `/init` - Survey existing materials, classify, produce reading guide
- `/read` - Deep-read materials, produce synthesis
- `/discuss` - Open-ended conceptual discussion
- `/feedback` - Process raw feedback, drive toward alignment
- `/crystallize` - Propose doc structure, write documentation bundle
- `/capture` - Memorialize incremental alignment
- `/delta` - Capture a new idea as a working paper
- `/decide` - Record a resolved decision with rationale
- `/research` - Research a topic, synthesize findings for discussion
- `/research-brief` - Write a research prompt for an external agent
- `/gaps` - Assess what is done, partial, open, deferred
- `/backlog` - Update/review concept development backlog
- `/resume` - Re-establish context on in-flight design effort

### Architect Commands
- `/arch-init` - Initialize project, set patterns, establish Architect role
- `/arch-resume` - Resume in-flight project, establish/correct current state
- `/arch-discuss` - Engage in architectural discussion
- `/arch-create-docs` - Create initial product documentation
- `/arch-roadmap` - Create implementation roadmap
- `/arch-sprint-prep` - Prepare sprint proposal (auto-loads context)
- `/arch-feedback` - Process user feedback essay
- `/arch-sprint-start` - Lock scope, write plan and brief
- `/arch-sprint-complete` - Process completed sprint, reconcile docs (auto-loads context)
- `/arch-user-story` - Capture and discuss user stories
- `/ux-consult` - Collaborate with UX Designer subagent

### Implementor Commands
- `/impl-begin` - Begin implementation (MAM: read brief; MAMA: delegate to subagent)
- `/impl-end` - Wrap up implementation with retrospective

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
1. Prep → 2. Feedback → 3. Start → 4. Begin (implementation) → 5. End (implementation) → 6. Complete

## Advanced Features

### SessionStart Hook
On session start, the plugin auto-detects project state:
- Checks for `CLAUDE.md` and current sprint info
- Scans `docs/` for sprint artifacts
- Displays detected state and invites correction ("We're actually in sprint X")

### Context Loading
Key commands prompt Claude to read relevant files before proceeding:
- `arch-sprint-prep` - Reads roadmap, recent artifacts, active deltas
- `arch-sprint-complete` - Reads implementation log, plan, deltas
- `impl-begin` - Reads brief, plan, project patterns
- `arch-resume` - Reads full project state for session resumption

### UX Designer Subagent
The `/ux-consult` command invokes a UX Designer subagent that:
- Works collaboratively with the Architect on design decisions
- Creates design artifacts (style guides, interaction patterns, etc.)
- Uses persistent context (resume capability) for continuity across sessions

To maintain UX Designer continuity:
1. First session: Note the agent ID returned
2. Later sessions: Use resume with that agent ID
3. Store agent ID in project notes or CLAUDE.md

## Development Notes

- The `docs/` directory contains the original design documents from the design session (kept for reference)
- Plugin names are `pdt`, `mam`, and `mama` for brevity, so commands are invoked as `/pdt:init`, `/mam:arch-init`, `/mama:arch-init` etc.
- To test changes, restart Claude Code with `claude --plugin-dir ./`
