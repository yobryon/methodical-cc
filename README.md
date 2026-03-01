# Multi-Agent Architecture Methodology

Claude Code plugins for structured product design and implementation workflows.

## Three Plugins

| Plugin | Description | Best For |
|--------|-------------|----------|
| **PDT** | Product Design Thinking - Socratic design partner for pre-implementation thinking | Product vision, concept development, documentation crystallization |
| **MAM** | Session-based - Architect and Implementor as separate Claude sessions | Explicit context separation, document-based handoffs |
| **MAMA** | Subagent-based - Architect orchestrates persistent Implementor subagent | Context continuity, iterative work |

PDT is the natural predecessor to MAM/MAMA. Design your product with PDT, then build it with MAM or MAMA.

## Features

- **Socratic design partnership**: PDT probes, challenges, and develops ideas alongside you
- **Progressive crystallization**: Ideas evolve from conversations to deltas to formal documents
- **Clear role separation**: Architect owns design and orchestration; Implementor owns execution
- **Incremental design via deltas**: Explore changes before committing to documentation
- **Structured handoffs**: Briefs and plans transfer context between agents
- **Feedback loops**: Implementation logs and feedback cycles drive evolution
- **Sprint-based development**: Coherent chunks of work with clear outcomes
- **Auto-detection of project state**: SessionStart hook detects current state and artifacts
- **Smart context loading**: Commands prompt reading of relevant documents
- **Decisions as first-class artifacts**: Every resolved decision logged with rationale

## Installation

### Adding the Marketplace

```bash
claude plugin marketplace add yobryon/methodical-cc
```

### From Marketplace

```bash

# Product design thinking
claude plugin install pdt@methodical-cc

# Session-based implementation workflow
claude plugin install mam@methodical-cc

# Subagent-based implementation workflow
claude plugin install mama@methodical-cc
```

### Test Locally

```bash
# PDT (product design thinking)
claude --plugin-dir /path/to/methodical-cc/plugins/pdt

# MAM (session-based)
claude --plugin-dir /path/to/methodical-cc/plugins/mam

# MAMA (subagent-based)
claude --plugin-dir /path/to/methodical-cc/plugins/mama
```

## Quick Start (PDT - Product Design Thinking)

1. **Initialize** (survey existing materials):
   ```
   /pdt:init
   [Provide file paths, URLs, or describe what you have]
   ```

2. **Deep Read** priority materials:
   ```
   /pdt:read [file or topic]
   ```

3. **Discuss** and develop concepts:
   ```
   /pdt:discuss [topic or idea]
   ```

4. **Crystallize** into formal documentation:
   ```
   /pdt:crystallize
   ```

5. **Assess readiness** and hand off:
   ```
   /pdt:gaps
   → When ready, switch to MAM or MAMA for implementation
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

### PDT Commands (`/pdt:`)
| Command | Purpose |
|---------|---------|
| `init` | Survey existing materials, produce reading guide |
| `read` | Deep-read materials, produce synthesis |
| `discuss` | Open-ended conceptual discussion |
| `feedback` | Process raw feedback, drive toward alignment |
| `crystallize` | Propose doc structure, write documentation bundle |
| `capture` | Memorialize incremental alignment |
| `delta` | Capture a new idea as a working paper |
| `decide` | Record a resolved decision with rationale |
| `research` | Research a topic, synthesize findings for discussion |
| `research-brief` | Write a research prompt for an external agent |
| `gaps` | Assess what is done, partial, open, deferred |
| `backlog` | Update/review concept development backlog |
| `next` | Figure out what's workable and highest-value for this session |
| `coherence` | Cross-document consistency audit with optional fix application |
| `resume` | Re-establish context on in-flight design effort |

### MAM/MAMA Architect Commands (`/mam:` or `/mama:`)
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
methodical-cc/
├── plugins/
│   ├── pdt/              # Product design thinking plugin
│   ├── mam/              # Session-based implementation plugin
│   └── mama/             # Subagent-based implementation plugin
├── tools/                # Migration utilities
└── docs/                 # Design documentation
```

See individual plugin READMEs for detailed documentation:
- [PDT README](plugins/pdt/README.md)
- [MAM README](plugins/mam/README.md)
- [MAMA README](plugins/mama/README.md)

## License

MIT
