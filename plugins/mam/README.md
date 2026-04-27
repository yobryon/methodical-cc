# MAM - Multi-Agent Methodology

Session-based Architect/Implementor workflow for complex software projects.

## Overview

MAM provides a structured methodology where you work with Claude in two separate sessions:
- **Architect Session**: Design partner — maintains docs, creates deltas, plans sprints, writes briefs
- **Implementor Session**: Execution partner — follows plans, maintains logs, flags questions

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
| Command | Purpose |
|---------|---------|
| `/mam:arch-init` | Initialize project, establish scope, create `.mam/` state |
| `/mam:arch-resume` | Resume in-flight project from `.mam/` state |
| `/mam:arch-discuss` | Discuss ideas, process feedback, explore architecture |
| `/mam:arch-create-docs` | Create product documentation |
| `/mam:arch-roadmap` | Create implementation roadmap |
| `/mam:arch-sprint-prep` | Prepare sprint proposal |
| `/mam:arch-sprint-start` | Lock scope, write plan and brief |
| `/mam:arch-sprint-complete` | Process completed sprint, reconcile docs, update state |
| `/mam:arch-review` | Architectural review of codebase against design |
| `/mam:consult-pdt` | Formalize a design question for PDT |
| `/mam:commission-complete` | Report results of a PDT commission |
| `/mam:debrief-pdt` | Report back to PDT after a milestone |
| `/mam:ux-consult` | Collaborate with UX Designer |

### Implementor Commands
| Command | Purpose |
|---------|---------|
| `/mam:impl-begin` | Begin implementation (read brief, execute plan) |
| `/mam:impl-end` | Complete implementation with retrospective |
| `/mam:impl-export` | Export accumulated implementation knowledge to state document |

### Shared Commands
| Command | Purpose |
|---------|---------|
| `/mam:pattern-add` | Add project patterns to CLAUDE.md |
| `/mam:upgrade` | Upgrade project artifacts to current plugin version |
| `/mam:session` | Register or recall session IDs for quick resumption (`set arch`, `set impl`, `list`, `clear`) |

## MAM State Directory

MAM keeps its internal state in `.mam/` (or `.mam-{scope}/` for multi-product projects):

```
.mam/
├── architect_state.md      # Architect's running project knowledge
└── sprint_log.md           # Chronological sprint record
```

This separates MAM's bookkeeping from the project's `docs/` directory.

### Scoped Instances

For multi-product projects sharing a directory, each MAM instance scopes itself:

```
.mam-backend/     # Backend architect's state
.mam-app/         # App architect's state
.mam-admin/       # Admin architect's state
```

Sprint artifacts follow the same pattern:
```
docs/backend/sprint/1/{implementation_plan,implementor_brief,implementation_log}.md
docs/app/sprint/1/{implementation_plan,implementor_brief,implementation_log}.md
```

## Sprint Artifact Organization

Sprint artifacts use a hierarchical layout:

```
docs/sprint/1/
├── implementation_plan.md
├── implementor_brief.md
└── implementation_log.md

docs/sprint/2/
├── implementation_plan.md
├── implementor_brief.md
└── implementation_log.md
```

## Session Resumption

MAM runs Architect and Implementor as separate sessions. Use `/mam:session` to register each one for quick resumption:

```
# In your Architect session:
/mam:session set arch

# In your Implementor session:
/mam:session set impl

# Later, from any terminal:
mcc arch              # resumes the Architect session
mcc impl              # resumes the Implementor session
mcc list              # shows all registered sessions
mcc status            # show plugin state, version, and registered sessions
```

The `mcc` script is in `tools/mcc` (with `mcc.cmd` for Windows). Add it to your PATH or copy it to a location that's already on your PATH. It requires Python 3.6+ — most platforms ship this; on Windows you may need to install it from python.org.

`mcc` also handles plugin management — see `mcc help` for `setup`, `enable`, `disable`, and `switch` (for swapping between MAM and MAMA per-project).

## Typical Workflow

```
Architect Session:
1. /mam:arch-init              Initialize project, create .mam/ state
2. /mam:arch-create-docs       Create product documentation
3. /mam:arch-roadmap           Plan the roadmap
4. /mam:arch-sprint-prep       Propose sprint scope
5. /mam:arch-discuss           Discuss with user, refine scope
6. /mam:arch-sprint-start      Lock scope, write plan and brief

Implementor Session:
7. /mam:impl-begin             Read brief, begin implementation
8. /mam:impl-end               Complete log with retrospective

Architect Session:
9. /mam:arch-sprint-complete   Reconcile docs, update state, propose next sprint
   → Repeat from step 4
```

## When to Use MAM

Choose MAM (session-based) when you:
- Prefer running the Implementor session yourself with full control
- Want explicit context separation between design and implementation
- Want to review handoff documents before switching roles
- Are working on longer sprints where session separation helps focus

Choose MAMA (team-based) when you:
- Want to interact directly with the Implementor during sprints
- Want real-time inter-agent communication
- Want persistent working knowledge across sprints without manual session management

See also:
- [MAMA](../mama/README.md) (team-based implementation workflow)
- [PDT](../pdt/README.md) (pre-implementation product design)
