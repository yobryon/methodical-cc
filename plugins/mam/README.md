# MAM - Multi-Agent Methodology

Session-based Architect/Implementor workflow for complex software projects.

## Overview

MAM provides a structured methodology where you work with Claude in two separate sessions:
- **Architect Session**: Design partner - maintains docs, creates deltas, plans sprints, writes briefs
- **Implementor Session**: Execution partner - follows plans, maintains logs, flags questions

The sessions communicate through documents (briefs, plans, logs), creating natural handoff points for review.

## Installation

```bash
# From marketplace
claude plugin install mam

# Or test locally
claude --plugin-dir /path/to/plugins/mam
```

## Commands

### Architect Commands
- `/mam:arch-init` - Initialize project, set patterns
- `/mam:arch-resume` - Resume in-flight project
- `/mam:arch-discuss` - Architectural discussion
- `/mam:arch-create-docs` - Create product documentation
- `/mam:arch-roadmap` - Create implementation roadmap
- `/mam:arch-sprint-prep` - Prepare sprint proposal
- `/mam:arch-feedback` - Process user feedback
- `/mam:arch-sprint-start` - Lock scope, start sprint
- `/mam:arch-sprint-complete` - Process completed sprint
- `/mam:arch-user-story` - Capture user stories
- `/mam:ux-consult` - Collaborate with UX Designer

### Implementor Commands
- `/mam:impl-begin` - Begin implementation
- `/mam:impl-end` - Complete implementation

### Shared Commands
- `/mam:pattern-add` - Add project patterns

## When to Use MAM

Choose MAM (session-based) when you:
- Prefer explicit context separation between design and implementation
- Want to review handoff documents before switching roles
- Are working on longer sprints where session separation helps focus

See also: **MAMA** (subagent variant) for integrated subagent-based workflow.
