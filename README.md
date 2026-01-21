# Multi-Agent Architecture Methodology

A Claude Code plugin for managing complex software projects using distinct Architect and Implementor agent roles.

## Features

- **Clear role separation**: Architect owns design and orchestration; Implementor owns execution
- **Incremental design via deltas**: Explore changes before committing to documentation
- **Structured handoffs**: Briefs and plans transfer context between agents
- **Feedback loops**: Implementation logs and feedback cycles drive evolution
- **Sprint-based development**: Coherent chunks of work with clear outcomes
- **Auto-detection of project state**: SessionStart hook detects current sprint and artifacts
- **Smart context loading**: Commands prompt reading of relevant documents before proceeding
- **UX Designer subagent**: Persistent-context design collaborator for the Architect

## Installation

### Option 1: Test Locally

```bash
claude --plugin-dir /path/to/cc-methodology
```

### Option 2: Install from Marketplace

```
/plugin install m
```

## Quick Start

### Starting a New Project

1. **Initialize** (Architect session):
   ```
   /m:arch-init

   [Provide your initial design documents, research, ideas]
   ```

2. **Discuss Architecture**:
   ```
   /m:arch-discuss

   [Share your architectural thinking]
   ```

3. **Create Documentation**:
   ```
   /m:arch-create-docs
   ```

4. **Create Roadmap**:
   ```
   /m:arch-roadmap
   ```

5. **Plan First Sprint**:
   ```
   /m:arch-sprint-plan
   ```

6. **Process Feedback** (when you have thoughts/reactions):
   ```
   /m:arch-feedback

   [Share your feedback essay]
   ```

7. **Finalize Sprint**:
   ```
   /m:arch-sprint-finalize
   ```

8. **Switch to Implementor Session**:
   ```
   /m:impl-start @docs/implementor_brief_sprint1.md
   ```

9. **Complete Implementation Work**:
   ```
   /m:impl-finalize
   ```

10. **Back to Architect Session**:
    ```
    /m:arch-sprint-complete @docs/implementation_log_sprint1.md
    ```

Then repeat the sprint cycle as needed.

## Commands

### Architect Commands

| Command | Purpose |
|---------|---------|
| `arch-init` | Initialize project, set patterns, establish Architect role |
| `arch-resume` | Resume in-flight project, establish/correct current state |
| `arch-discuss` | Engage in architectural discussion, build understanding |
| `arch-create-docs` | Create initial product documentation |
| `arch-roadmap` | Create implementation roadmap |
| `arch-sprint-plan` | Begin planning next sprint (auto-loads context) |
| `arch-feedback` | Process user feedback, extract deltas, align on scope |
| `arch-sprint-finalize` | Finalize scope, write implementation plan and brief |
| `arch-sprint-complete` | Process completed sprint (auto-loads context) |
| `arch-user-story` | Capture and discuss user stories |
| `ux-consult` | Collaborate with UX Designer subagent |

### Implementor Commands

| Command | Purpose |
|---------|---------|
| `impl-start` | Begin implementation, read brief, proceed |
| `impl-finalize` | Wrap up implementation, complete log, write retrospective |

### Shared Commands

| Command | Purpose |
|---------|---------|
| `pattern-add` | Add or update a project pattern in CLAUDE.md |

## Working with Two Sessions

This methodology works best with two separate Claude Code sessions:

1. **Architect Session**: Long-running session that maintains design context
2. **Implementor Session**: Separate session focused on execution

The sessions communicate through documents:
- Architect creates briefs and plans -> Implementor reads them
- Implementor creates logs -> Architect reads them

This separation keeps contexts focused, allows specialization, and creates natural handoff points for review.

## Project Structure

After initialization, projects typically have:

```
your-project/
├── .claude/
│   └── CLAUDE.md          # Project patterns and context
├── docs/
│   ├── [product_docs]     # Product documentation (structure varies)
│   ├── roadmap.md         # Implementation roadmap
│   ├── delta_XX_*.md      # Design deltas
│   ├── implementation_plan_sprintX.md
│   ├── implementor_brief_sprintX.md
│   └── implementation_log_sprintX.md
└── [source code]
```

## Resuming In-Flight Projects

When you start a Claude Code session on an existing project:

1. **Auto-Detection**: The plugin automatically detects project state on session start
2. **Correction**: If the detected state is wrong, tell the Architect: "We're actually in sprint 5"
3. **Explicit Resume**: Use `/m:arch-resume` for full state review and correction

The plugin scans for:
- Current sprint info in `.claude/CLAUDE.md`
- Sprint artifacts in `docs/` (plans, briefs, logs)
- Active deltas

## UX Designer Collaboration

The Architect can invoke a UX Designer subagent for design collaboration:

```
/m:ux-consult

Help me design the user interaction patterns for the dashboard feature.
```

The UX Designer:
- Analyzes product documentation for UX implications
- Proposes design patterns, flows, and visual systems
- Creates design artifacts (style guides, component specs)
- Uses **persistent context** for continuity across sessions

To maintain continuity, note the agent ID from your first UX session and use resume in subsequent sessions.

## Philosophy

This methodology embraces that:
- Complex projects need more structure than a single conversation
- Design and implementation are different modes of thinking
- Feedback and reflection drive evolution
- Documentation should reflect reality, not aspirations
- Claude is damn smart and can recognize what's needed

Work with Claude as a thinking partner, not just a tool.

## License

MIT
