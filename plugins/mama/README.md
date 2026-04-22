# MAMA - Multi-Agent Methodology with Agents

Team-based workflow where the Architect orchestrates Implementor and UX Designer as **teammates** you can interact with directly.

## Overview

MAMA uses **agent teams** for orchestration. The Architect is the team lead; the Implementor and UX Designer are teammates that the user can interact with directly -- no more proxying everything through the Architect.

- **Architect**: You (the team lead) - orchestrates the project, owns design and documentation
- **Implementor**: A teammate that executes sprint work -- you can give it test feedback, nudges, and redirections directly
- **UX Designer**: A teammate for design consultations -- available on demand

## Key Advantage: Direct Interaction

The defining difference from MAM: you can talk to the Implementor directly. Test something and want to give feedback? Shift+Down to the Implementor and tell it. Hit a bug during testing? Tell the Implementor right there. No more routing everything through the Architect as a proxy.

The Implementor can also message the Architect mid-sprint when design questions arise, getting real-time clarification instead of logging questions for later.

## Installation

```bash
# From marketplace
claude plugin install mama

# Or test locally
claude --plugin-dir /path/to/plugins/mama
```

**Requirement:** Agent teams must be enabled:
```json
// In ~/.claude/settings.json or .claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## Key Difference from MAM

| Aspect | MAM (Session-based) | MAMA (Team-based) |
|--------|---------------------|-------------------|
| Implementor | Separate Claude session you run yourself | Teammate you can interact with directly |
| User interaction | You talk to each agent in separate sessions | You talk to any agent from the same session |
| Mid-sprint questions | Implementor logs them for later | Implementor messages Architect directly |
| Context persistence | Your session compacts naturally | Implementor state document, compacted each sprint |
| MAMA internal state | N/A | `.mama/` directory for operational state |
| Sprint artifacts | `docs/` (flat) | `docs/sprint/X/` (hierarchical) |

## Commands

### Architect Commands
| Command | Purpose |
|---------|---------|
| `/mama:arch-init` | Initialize project, establish scope, create `.mama/` state |
| `/mama:arch-resume` | Resume in-flight project from `.mama/` state |
| `/mama:arch-discuss` | Discuss ideas, process feedback, explore architecture |
| `/mama:arch-create-docs` | Create initial product documentation |
| `/mama:arch-roadmap` | Create implementation roadmap |
| `/mama:arch-sprint-prep` | Prepare sprint proposal |
| `/mama:arch-sprint-start` | Lock scope, write plan and brief |
| `/mama:arch-sprint-complete` | Process completed sprint, reconcile docs, update state |
| `/mama:arch-review` | Architectural review of codebase against design |
| `/mama:consult-pdt` | Formalize a design question for PDT |
| `/mama:commission-complete` | Report results of a PDT commission |
| `/mama:debrief-pdt` | Report back to PDT after a milestone |
| `/mama:ux-consult` | Collaborate with UX Designer teammate |

### Implementor Commands
| Command | Purpose |
|---------|---------|
| `/mama:impl-begin` | Spawn Implementor teammate, begin sprint work |
| `/mama:impl-end` | Finalize work, write state document, shut down Implementor |

### Shared Commands
| Command | Purpose |
|---------|---------|
| `/mama:pattern-add` | Add project patterns |
| `/mama:upgrade` | Upgrade project artifacts to current plugin version (including MAM → MAMA migration) |

## How It Works

### Team Lifecycle

```
Team created (first need) ──────────────────────────── Team cleaned up
     │                                                       │
     │  Sprint 1              Sprint 2              Sprint N │
     │  ┌───────────────┐     ┌───────────────┐             │
     │  │ Impl spawns   │     │ Impl spawns   │    ...      │
     │  │ works phases  │     │ (reads state) │             │
     │  │ writes state  │     │ works phases  │             │
     │  │ shuts down    │     │ writes state  │             │
     │  └───────────────┘     │ shuts down    │             │
     │                         └───────────────┘             │
     │  UX Designer available at any point ──────────────── │
```

- **Team**: Created when first needed, persists across sprints
- **Implementor**: Sprint-scoped -- spawned at start, shut down at end
- **UX Designer**: On-demand -- spawned when needed

### Persistent Working Knowledge

The Implementor accumulates expertise across sprints through `implementor_state.md`:

1. **Sprint 1 end**: Implementor writes everything it learned -- patterns, gotchas, component relationships
2. **Sprint 2 start**: Fresh Implementor spawns, automatically loads the state document
3. **Sprint 2 end**: Implementor rewrites the state -- compacting previous + new knowledge
4. **Sprint N**: State doc stays bounded (compaction, not accumulation) with the distilled essence of all prior work

### MAMA State Directory

MAMA keeps its internal state in `.mama/` (or `.mama-{scope}/` for multi-product projects):

```
.mama/
├── architect_state.md      # Architect's running project knowledge
├── implementor_state.md    # Implementor's compacted working memory
└── sprint_log.md           # Chronological sprint record
```

### Scoped Instances

For multi-product projects sharing a directory, each MAMA instance scopes itself:

```
.mama-backend/    # Backend architect's state
.mama-app/        # App architect's state
.mama-admin/      # Admin architect's state
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

## Typical Workflow

```
1. /mama:arch-init              Initialize project, create .mama/ state
2. /mama:arch-create-docs       Create product documentation
3. /mama:arch-roadmap           Plan the roadmap
4. /mama:arch-sprint-prep       Propose sprint scope
5. /mama:arch-discuss           Discuss with user, refine scope
6. /mama:arch-sprint-start      Lock scope, write plan and brief
7. /mama:impl-begin             Spawn Implementor, begin work
   ↕ User interacts directly with Implementor during implementation
   ↕ Implementor messages Architect when questions arise
8. /mama:impl-end               Finalize, write state, shut down Implementor
9. /mama:arch-sprint-complete   Reconcile docs, update state, propose next sprint
   → Repeat from step 4
```

## When to Use MAMA

Choose MAMA (team-based) when you:
- Want to interact directly with the Implementor during sprints
- Want the Implementor and Architect to communicate in real-time
- Want persistent working knowledge across sprints without manual session management
- Want live visibility into sprint progress via shared task list
- Are doing iterative work where direct feedback loops help

Choose MAM (session-based) when you:
- Prefer running the Implementor session yourself with full control
- Want the simplicity of separate sessions without team overhead
- Don't need real-time inter-agent communication

## Agent Definitions

MAMA includes these agent definitions:

- **`implementor`**: Skilled software engineer focused on execution excellence. Loads persistent working knowledge via SessionStart hook.
- **`ux-designer`**: Design collaborator for UX decisions and artifacts.

Both are configured for team-based communication via SendMessage.

See also:
- [MAM](../mam/README.md) (session-based implementation workflow)
- [PDT](../pdt/README.md) (pre-implementation product design)
