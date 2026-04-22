# Multi-Agent Architecture Methodology

Claude Code plugins for structured product design and implementation workflows.

## Three Plugins

| Plugin | Description | Best For |
|--------|-------------|----------|
| **PDT** | Product Design Thinking - Socratic design partner for pre-implementation thinking | Product vision, concept development, documentation crystallization |
| **MAM** | Session-based - Architect and Implementor as separate Claude sessions | Explicit context separation, document-based handoffs |
| **MAMA** | Team-based - Architect orchestrates Implementor and UX Designer as teammates | Direct interaction with agents, real-time communication, persistent knowledge |

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

# Team-based implementation workflow
claude plugin install mama@methodical-cc
```

### Test Locally

```bash
# PDT (product design thinking)
claude --plugin-dir /path/to/methodical-cc/plugins/pdt

# MAM (session-based)
claude --plugin-dir /path/to/methodical-cc/plugins/mam

# MAMA (team-based)
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

4. **Capture** aligned thinking into documentation:
   ```
   /pdt:capture
   ```

5. **Assess readiness**:
   ```
   /pdt:gaps
   ```

6. **Orient the Architect** and launch MAM:
   ```
   /pdt:orient
   → Install MAM or MAMA, run /mam:arch-init or /mama:arch-init
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

3. **Discuss Feedback & Start Sprint**:
   ```
   /mam:arch-discuss [your thoughts and reactions]
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

## Quick Start (MAMA - Team-based)

1. **Initialize** (you are the Architect / team lead):
   ```
   /mama:arch-init
   ```

2. **Prep Sprint**:
   ```
   /mama:arch-sprint-prep
   ```

3. **Spawn Implementor Teammate**:
   ```
   /mama:impl-begin Sprint 1
   ```
   → Implementor spawns as teammate, you can interact directly
   → Implementor loads persistent working knowledge from prior sprints

4. **Complete Sprint**:
   ```
   /mama:impl-end          # Implementor writes state, shuts down
   /mama:arch-sprint-complete
   ```

## Commands

### PDT Commands (`/pdt:`)
| Command | Purpose |
|---------|---------|
| `init` | Survey existing materials, produce reading guide |
| `read` | Deep-read materials, produce synthesis |
| `discuss` | Discuss ideas, process feedback, explore concepts |
| `capture` | Write things down -- deltas, doc updates, decisions, or full documentation bundle |
| `decide` | Record a resolved decision with rationale |
| `research` | Research a topic in-session or write a brief for external research |
| `gaps` | Assess what is done, partial, open, deferred |
| `backlog` | Update/review concept development backlog |
| `next` | Figure out what's workable and highest-value for this session |
| `coherence` | Cross-document consistency audit with optional fix application |
| `commission` | Commission work from MAM (validation, prototyping, investigation) |
| `orient` | Write/update architect orientation for launch or phase transitions |
| `consult` | Process a design question from the Architect, write a response |
| `debrief` | Process an implementation debrief, evaluate and evolve the design |
| `resume` | Re-establish context on in-flight design effort |

### MAM/MAMA Architect Commands (`/mam:` or `/mama:`)
| Command | Purpose |
|---------|---------|
| `arch-init` | Initialize project, set patterns |
| `arch-resume` | Resume in-flight project |
| `arch-discuss` | Discuss ideas, process feedback, explore architecture |
| `arch-create-docs` | Create product documentation |
| `arch-roadmap` | Create implementation roadmap |
| `arch-sprint-prep` | Prepare sprint proposal |
| `arch-sprint-start` | Lock scope, write plan and brief |
| `arch-sprint-complete` | Complete sprint, reconcile docs |
| `arch-review` | Architectural review — DRY, fragmentation, pattern drift |
| `consult-pdt` | Formalize a design question for PDT |
| `commission-complete` | Report results of a PDT commission |
| `debrief-pdt` | Report back to PDT after a milestone |
| `ux-consult` | Collaborate with UX Designer |

### Implementor Commands
| Command | MAM Behavior | MAMA Behavior |
|---------|--------------|---------------|
| `impl-begin` | Read brief, begin work | Spawn Implementor teammate |
| `impl-end` | Write retrospective | Finalize, write state, shut down teammate |
| `impl-export` | Export implementation knowledge to state doc | *(not needed — impl-end writes state)* |

### Shared Commands
| Command | Purpose |
|---------|---------|
| `pattern-add` | Add project patterns to CLAUDE.md |
| `upgrade` | Upgrade project artifacts to current plugin version |
| `session` | Register or recall session IDs for quick resumption by persona name |

## Project Structure

After initialization, projects typically have:

```
your-project/
├── .claude/
│   └── CLAUDE.md              # Project patterns and context
├── .mama/                     # MAMA internal state (or .mama-{scope}/)
│   ├── architect_state.md     # Architect's running project knowledge
│   ├── implementor_state.md   # Implementor's compacted working memory
│   └── sprint_log.md          # Chronological sprint record
├── docs/
│   ├── [product_docs]         # Product documentation
│   ├── roadmap.md             # Implementation roadmap
│   ├── delta_XX_*.md          # Design deltas
│   └── sprint/
│       ├── 1/
│       │   ├── implementation_plan.md
│       │   ├── implementor_brief.md
│       │   └── implementation_log.md
│       └── 2/
│           └── ...
└── [source code]
```

For multi-product projects, sprint artifacts scope by component:
```
docs/backend/sprint/1/{implementation_plan,implementor_brief,implementation_log}.md
docs/app/sprint/1/{implementation_plan,implementor_brief,implementation_log}.md
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
│   └── mama/             # Team-based implementation plugin
├── tools/                # Utilities (including `cc` session resume script)
└── docs/                 # Design documentation
```

See individual plugin READMEs for detailed documentation:
- [PDT README](plugins/pdt/README.md)
- [MAM README](plugins/mam/README.md)
- [MAMA README](plugins/mama/README.md)

## License

MIT
