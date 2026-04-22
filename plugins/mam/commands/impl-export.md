---
description: Export your accumulated implementation knowledge to a state document. Captures codebase patterns, gotchas, component relationships, and institutional knowledge from your session context. Useful before transitioning to MAMA or as periodic knowledge preservation.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Export Implementation Knowledge

You are the **Implementor**. You've been working on this project and have accumulated deep context about the codebase — patterns, gotchas, component relationships, testing approaches, build quirks, things that would surprise someone new. This command captures that knowledge into a persistent document.

## Why This Matters

Your session context is rich but ephemeral. This export creates a durable record of what you know, useful for:
- **Transitioning to MAMA**: Your knowledge becomes the initial `implementor_state.md` that future Implementor teammates will load on startup
- **Knowledge preservation**: Even within MAM, this document can be read at the start of future Implementor sessions to bootstrap understanding
- **Onboarding**: A new person (or session) picking up this project gets a concentrated knowledge transfer

## Your Task

### 1. Find the State Directory

Look for the project's state directory:
- `.mam/` or `.mam-{scope}/` (MAM projects)
- `.mama/` or `.mama-{scope}/` (MAMA projects, if transitioning)
- If neither exists, ask the user where to write the file

### 2. Review Your Context

Before writing, mentally inventory what you know:
- **Codebase structure**: How is the code organized? What are the key modules/components?
- **Patterns**: What patterns does this codebase follow? What's idiomatic here?
- **Gotchas**: What's non-obvious? What broke in surprising ways? What looks simple but isn't?
- **Component relationships**: How do the pieces connect? What are the hidden dependencies?
- **Testing**: What's the testing strategy? What's well-tested vs. fragile?
- **Build and tooling**: What quirks does the build have? What commands matter?
- **Technical debt**: What shortcuts exist? What's known to be fragile?
- **Recent work**: What was just changed? What's the current state of the implementation?

### 3. Write the State Document

Write `{state_dir}/implementor_state.md`. If a prior version exists, read it first and incorporate anything still relevant.

Structure it as **compacted working knowledge** — not a log of what you did, but a distillation of what matters going forward. Write it as if briefing a skilled engineer who's about to pick up where you left off.

Suggested structure (adapt to what's relevant):

```markdown
# Implementor State

**Project**: [Name]
**Last updated**: [Date]
**After sprint**: [N]

## Codebase Overview
[How the code is organized, key entry points, architectural patterns]

## Patterns and Conventions
[What's idiomatic in this codebase, naming conventions, common patterns]

## Key Components
[Important modules/classes/services and how they relate]

## Known Gotchas
[Non-obvious things that will bite you if you don't know about them]

## Build and Tooling
[Build quirks, important commands, environment setup notes]

## Testing
[Testing strategy, what's well-covered vs. fragile, how to run tests]

## Technical Debt
[Known shortcuts, fragile areas, things that need future attention]

## Current State
[What was just completed, what's in flight, what's next]
```

### 4. Confirm with the User

Present a summary of what you captured and confirm it's written. Note anything the user might want to add or correct.

## Size Discipline

Keep this document readable in **under 5 minutes**. It's a concentrated knowledge transfer, not a comprehensive reference. If something is obvious from reading the code, don't include it. Focus on what would surprise someone or save them from a mistake.

## Begin

Review your accumulated context, then write the implementation state document. If a prior version exists, read it first and incorporate what's still relevant.

$ARGUMENTS
