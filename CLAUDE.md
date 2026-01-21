# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code plugin that encapsulates the Multi-Agent Architecture Methodology. The methodology enables complex software projects to be managed through distinct Architect and Implementor agent roles, with structured handoffs via briefs, plans, and logs.

## Plugin Structure

This plugin follows the Claude Code plugin specification:

```
cc-methodology/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (name, version, description)
├── skills/
│   └── multi-agent-methodology/
│       ├── SKILL.md             # Core methodology reference
│       └── templates/           # Document templates
├── commands/                    # Slash commands (*.md files)
│   ├── arch-*.md               # Architect commands
│   ├── impl-*.md               # Implementor commands
│   ├── ux-consult.md           # UX Designer collaboration
│   └── pattern-add.md          # Shared command
├── agents/
│   └── ux-designer/
│       └── agent.json           # UX Designer subagent
├── hooks/
│   └── hooks.json               # SessionStart hook for state detection
├── .mcp.json                    # MCP servers (Playwright for browser interaction)
└── docs/                        # Design-time documentation (not part of plugin)
```

**Critical**: `commands/`, `skills/`, `hooks/`, and `agents/` must be at the **plugin root**, NOT inside `.claude-plugin/`.

## Commands

### Architect Commands
- `/arch-init` - Initialize project, set patterns, establish Architect role
- `/arch-resume` - Resume in-flight project, establish/correct current state
- `/arch-discuss` - Engage in architectural discussion
- `/arch-create-docs` - Create initial product documentation
- `/arch-roadmap` - Create implementation roadmap
- `/arch-sprint-plan` - Begin planning next sprint (auto-loads context)
- `/arch-feedback` - Process user feedback essay
- `/arch-sprint-finalize` - Finalize scope, write plan and brief
- `/arch-sprint-complete` - Process completed sprint, reconcile docs (auto-loads context)
- `/arch-user-story` - Capture and discuss user stories
- `/ux-consult` - Collaborate with UX Designer subagent

### Implementor Commands
- `/impl-start` - Begin implementation, read brief (auto-loads context)
- `/impl-finalize` - Wrap up implementation with retrospective

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

## Skill File Format

Skills use the same markdown + frontmatter format in a `SKILL.md` file:

```markdown
---
name: skill-name
description: When/how to use this skill (Claude uses this to auto-invoke)
---

# Skill Content

Reference content or instructions.
```

## Testing the Plugin

```bash
# Test locally during development
claude --plugin-dir ./

# Invoke a command
/m:arch-init
```

Commands are namespaced by plugin name when installed as a plugin.

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
1. Planning → 2. Feedback → 3. Finalization → 4. Implementation → 5. Review → 6. Reconciliation

## Advanced Features

### SessionStart Hook
On session start, the plugin auto-detects project state:
- Checks for `.claude/CLAUDE.md` and current sprint info
- Scans `docs/` for sprint artifacts
- Displays detected state and invites correction ("We're actually in sprint X")

### Context Loading
Key commands prompt Claude to read relevant files before proceeding:
- `arch-sprint-plan` - Reads roadmap, recent artifacts, active deltas
- `arch-sprint-complete` - Reads implementation log, plan, deltas
- `impl-start` - Reads brief, plan, project patterns
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

### Playwright MCP Server
The plugin includes a Playwright MCP server for browser interaction. Useful for:
- Testing web apps during implementation
- UX Designer verifying interaction patterns
- Architect reviewing deployed features

Available to all agents when building web applications.

## Development Notes

- The `docs/` directory contains the original design documents from the design session (kept for reference)
- The plugin name is `m` for brevity, so commands are invoked as `/m:arch-init` etc.
- To test changes, restart Claude Code with `claude --plugin-dir ./`
