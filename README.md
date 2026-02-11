# Multi-Agent Architecture Methodology

Claude Code plugins for managing complex software projects using distinct Architect and Implementor agent roles.

## Two Plugin Variants

| Plugin | Description | Best For |
|--------|-------------|----------|
| **MAM** | Session-based - Architect and Implementor as separate Claude sessions | Explicit context separation, document-based handoffs |
| **MAMA** | Subagent-based - Architect orchestrates persistent Implementor subagent | Context continuity, iterative work |

## Features

- **Clear role separation**: Architect owns design and orchestration; Implementor owns execution
- **Incremental design via deltas**: Explore changes before committing to documentation
- **Structured handoffs**: Briefs and plans transfer context between agents
- **Feedback loops**: Implementation logs and feedback cycles drive evolution
- **Sprint-based development**: Coherent chunks of work with clear outcomes
- **Auto-detection of project state**: SessionStart hook detects current sprint and artifacts
- **Smart context loading**: Commands prompt reading of relevant documents
- **UX Designer subagent**: Persistent-context design collaborator

## Installation

### From Marketplace

```bash
# Session-based workflow
claude plugin install mam

# Subagent-based workflow
claude plugin install mama
```

### Test Locally

```bash
# MAM (session-based)
claude --plugin-dir /path/to/cc-methodology/plugins/mam

# MAMA (subagent-based)
claude --plugin-dir /path/to/cc-methodology/plugins/mama
```

## Quick Start (MAM - Session-based)

1. **Initialize** (Architect session):
   ```
   /mam:arch-init
   [Provide your initial design documents, research, ideas]
   ```

2. **Prep Sprint**:
   ```
   /mam:arch-sprint-prep
   ```

3. **Process Feedback & Start Sprint**:
   ```
   /mam:arch-feedback [your thoughts]
   /mam:arch-sprint-start
   ```

4. **Switch to Implementor Session**:
   ```
   /mam:impl-begin
   ```

5. **Complete & Return to Architect**:
   ```
   /mam:impl-end
   /mam:arch-sprint-complete
   ```

## Quick Start (MAMA - Subagent-based)

1. **Initialize** (you are the Architect):
   ```
   /mama:arch-init
   ```

2. **Prep Sprint**:
   ```
   /mama:arch-sprint-prep
   ```

3. **Delegate to Implementor Subagent**:
   ```
   /mama:impl-begin Sprint 1
   ```
   → Implementor works as subagent, maintains context via resume

4. **Complete Sprint**:
   ```
   /mama:impl-end
   /mama:arch-sprint-complete
   ```

## Commands

Both plugins share the same command names, just with different namespaces (`/mam:` vs `/mama:`):

### Architect Commands
| Command | Purpose |
|---------|---------|
| `arch-init` | Initialize project, set patterns |
| `arch-resume` | Resume in-flight project |
| `arch-discuss` | Architectural discussion |
| `arch-create-docs` | Create product documentation |
| `arch-roadmap` | Create implementation roadmap |
| `arch-sprint-prep` | Prepare sprint proposal |
| `arch-feedback` | Process user feedback |
| `arch-sprint-start` | Lock scope, write plan and brief |
| `arch-sprint-complete` | Complete sprint, reconcile docs |
| `arch-user-story` | Capture user stories |
| `ux-consult` | Collaborate with UX Designer |

### Implementor Commands
| Command | MAM Behavior | MAMA Behavior |
|---------|--------------|---------------|
| `impl-begin` | Read brief, begin work | Delegate to Implementor subagent |
| `impl-end` | Write retrospective | Have subagent write retrospective |

### Shared Commands
| Command | Purpose |
|---------|---------|
| `pattern-add` | Add project patterns to CLAUDE.md |

## Project Structure

After initialization, projects typically have:

```
your-project/
├── .claude/
│   └── CLAUDE.md          # Project patterns and context
├── docs/
│   ├── [product_docs]     # Product documentation
│   ├── roadmap.md         # Implementation roadmap
│   ├── delta_XX_*.md      # Design deltas
│   ├── implementation_plan_sprintX.md
│   ├── implementor_brief_sprintX.md
│   └── implementation_log_sprintX.md
└── [source code]
```

## Philosophy

This methodology embraces that:
- Complex projects need more structure than a single conversation
- Design and implementation are different modes of thinking
- Feedback and reflection drive evolution
- Documentation should reflect reality, not aspirations
- Claude is damn smart and can recognize what's needed

Work with Claude as a thinking partner, not just a tool.

## Repository Structure

```
cc-methodology/
├── plugins/
│   ├── mam/              # Session-based plugin
│   └── mama/             # Subagent-based plugin
├── tools/                # Migration utilities
└── docs/                 # Design documentation
```

See individual plugin READMEs for detailed documentation:
- [MAM README](plugins/mam/README.md)
- [MAMA README](plugins/mama/README.md)

## License

MIT
