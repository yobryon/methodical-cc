# MAMA - Multi-Agent Methodology with Agents

Subagent-based workflow where the Architect orchestrates persistent Implementor and UX Designer agents.

## Overview

MAMA extends the Multi-Agent Methodology by running the Implementor and UX Designer as **subagents with persistent context**. This means:

- **Architect**: You (the main agent) - orchestrates the project
- **Implementor**: A subagent that maintains context across implementation sessions
- **UX Designer**: A subagent that maintains context across design consultations

The key advantage: subagents remember their previous work, building up codebase understanding over time.

## Installation

```bash
# From marketplace
claude plugin install mama

# Or test locally
claude --plugin-dir /path/to/plugins/mama
```

## Key Difference from MAM

| Aspect | MAM (Session-based) | MAMA (Subagent-based) |
|--------|---------------------|----------------------|
| Implementor | Separate Claude session | Subagent with persistent context |
| Context | Fresh each session | Maintained via resume |
| Handoff | Through document files | Direct subagent invocation |
| Workflow | Switch between sessions | Architect orchestrates subagents |

## Commands

### Architect Commands
- `/mama:arch-init` - Initialize project
- `/mama:arch-resume` - Resume in-flight project
- `/mama:arch-discuss` - Architectural discussion
- `/mama:arch-create-docs` - Create documentation
- `/mama:arch-roadmap` - Create roadmap
- `/mama:arch-sprint-prep` - Prepare sprint proposal
- `/mama:arch-feedback` - Process feedback
- `/mama:arch-sprint-start` - Lock scope, start sprint
- `/mama:arch-sprint-complete` - Complete sprint
- `/mama:arch-user-story` - Capture user stories
- `/mama:ux-consult` - Collaborate with UX Designer subagent

### Implementor Delegation
- `/mama:impl-begin` - Delegate to Implementor subagent
- `/mama:impl-end` - Have Implementor write retrospective

### Shared Commands
- `/mama:pattern-add` - Add project patterns

## Persistent Context Workflow

### First Time Using a Subagent

```
/mama:impl-begin Sprint 11

→ Claude invokes Implementor subagent
→ Implementor does the work
→ Claude receives agent ID (e.g., "agent-abc123")
→ Store this ID in CLAUDE.md for next time
```

### Resuming a Subagent

```
/mama:impl-begin Continue from where we left off

→ Claude reads stored agent ID from CLAUDE.md
→ Resumes the previous Implementor session
→ Implementor has full context of previous work
```

### Storing Agent IDs

Add to your project's `CLAUDE.md`:

```markdown
## Subagent Sessions

### Implementor
- **Agent ID**: agent-abc123
- **Last Active**: Sprint 11

### UX Designer
- **Agent ID**: agent-xyz789
- **Last Active**: Design system work
```

## When to Use MAMA

Choose MAMA (subagent-based) when you:
- Want the Implementor to build up codebase understanding over time
- Prefer a single orchestrating session rather than switching
- Want seamless context continuity across sprints
- Are doing iterative work where context carryover helps

See also: **MAM** (session variant) for explicit session separation.

## Subagent Definitions

MAMA includes these subagent definitions:

- **`implementor`**: Skilled software engineer focused on execution excellence
- **`ux-designer`**: Design collaborator for UX decisions and artifacts

Both are configured for persistent context via the resume capability.
