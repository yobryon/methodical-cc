---
description: Export tacit implementation knowledge — the context that can't be recovered from code, docs, or briefings — to a persistent state document. Useful before transitioning to MAMA or as periodic knowledge preservation.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Export Implementation Knowledge

You are the **Implementor**. You've been working on this project and have accumulated context that lives only in your head — hard-won lessons, the "why" behind non-obvious choices, how the user works, what experiments revealed, what shaped the current design. This command captures that **tacit knowledge** into a persistent document.

The key question: **What did you learn that can't be recovered from CLAUDE.md, the doc tree, the Architect briefing, or re-reading the code?** That's what belongs here. Everything else already has a home.

## Why This Matters

Your session context is rich but ephemeral. This export creates a durable record of what would otherwise be lost, useful for:
- **Transitioning to MAMA**: Your knowledge becomes the initial `implementor_state.md` that future Implementor teammates will load on startup
- **Knowledge preservation**: Even within MAM, this document can be read at the start of future Implementor sessions to bootstrap understanding
- **Onboarding**: A new person (or session) picking up this project gets a concentrated knowledge transfer

## Your Task

### 1. Find the State Directory

Look for the project's state directory:
- `.mcc/` or `.mcc-{scope}/` (MAM projects)
- `.mcc/` or `.mcc-{scope}/` (MAMA projects, if transitioning)
- If neither exists, ask the user where to write the file

### 2. Review Your Context

Before writing, mentally inventory **what you know that has no other home**. The categories below are prompts, not a checklist — skip any that aren't relevant, and add what is.

**Historical and contextual knowledge:**
- **Project history and load-bearing lessons**: What past mistakes or pivots shaped the current design? What approaches were tried and abandoned, and why did they fail?
- **Why it's built this way**: Where the code does something non-obvious, what's the rationale? What alternative was considered and rejected, and why?
- **Working context**: How does the user work? What's their expertise, preferences, communication style? What do they care about most? How do they like to collaborate?

**Technical tacit knowledge:**
- **Gotchas and empirical findings**: What has experimentation revealed — things that broke surprisingly, behaviors that only show up at scale, calibration notes from real runs, what's actually expensive vs. cheap? What looks simple but isn't?
- **Component relationships**: How do the pieces connect? What are the hidden dependencies that aren't obvious from the code structure?
- **Build and tooling quirks**: What non-obvious things about the build, environment, or tooling would trip someone up?

**State and trajectory:**
- **Current state**: What was just completed, what's in flight, what's the trajectory?
- **Technical debt**: What shortcuts exist that aren't tracked elsewhere? What's fragile in ways the tests don't cover?

### 3. Write the State Document

Write `{state_dir}/implementor_state.md`. If a prior version exists, read it first and incorporate anything still relevant. Prune superseded empirical data — calibration numbers, performance characteristics, and "what's expensive" findings have half-lives and should be updated or dropped when they no longer reflect reality. History and rationale age better; carry those forward.

Structure it as **compacted tacit knowledge** — not a summary of the codebase or a log of what you did, but a distillation of what would be lost if this session ended. Write it as if briefing a skilled engineer who has access to CLAUDE.md, the full doc tree, and the Architect's briefing — but none of your experience.

Suggested structure (adapt to what's relevant):

```markdown
# Implementor State

**Project**: [Name]
**Last updated**: [Date]
**After sprint**: [N]

## Why It's Built This Way
[Rationale behind non-obvious architectural choices — what was considered and rejected, and why]

## Project History and Lessons Learned
[Load-bearing past mistakes or pivots that shaped current work — what you'd need to know to avoid repeating history. Include approaches tried and abandoned, with the reason they failed.]

## Empirical Findings
[What experiments and real runs have revealed — calibration data, performance characteristics, surprising behaviors, what's actually expensive vs. cheap]

## Known Gotchas
[Non-obvious things that will bite you if you don't know about them — hidden dependencies, subtle ordering requirements, things that look simple but aren't]

## Working Context
[How the user works — their expertise, preferences, working style, what they care about, how they like to collaborate]

## Build and Tooling
[Non-obvious quirks — things the README or CLAUDE.md don't cover that would trip you up]

## Current State
[What was just completed, what's in flight, trajectory and momentum]

## Technical Debt
[Known shortcuts and fragile areas not tracked elsewhere]
```

### 4. Reflect Before Finalizing

Before presenting to the user, ask yourself: **if someone only had this document plus CLAUDE.md plus the Architect briefing, would they:**
- Know *why* the codebase is the way it is?
- Avoid the mistakes that came from past painful learnings?
- Know how the user works and what they care about?
- Have the empirical calibration from real runs and experiments?

If any answer is "not really," flesh out the relevant section.

### 5. Confirm with the User

Present a summary of what you captured and confirm it's written. Note anything the user might want to add or correct.

## What NOT to Include

Don't duplicate content that lives elsewhere:
- **CLAUDE.md** is auto-loaded every session — don't repeat project patterns, conventions, or build commands that are already there
- **docs/** (roadmap, product docs, tech debt trackers) — reference by path when the state doc needs to orient the reader, don't summarize
- **Sprint logs and implementation logs** — the history is in the artifacts, don't re-narrate it
- **Anything recoverable from reading the code** — structure, APIs, type signatures

Your job is to capture the context those sources don't hold.

## Size Discipline

Keep this document readable in **under 5 minutes**. It's a concentrated knowledge transfer, not a comprehensive reference.

- If something is obvious from reading the code, don't include it.
- **Do** include things that aren't in code but would take weeks to rediscover — project history, user preferences, empirical findings from experimentation, the "why" behind architectural choices. These have no other home.

## Begin

Review your accumulated context, then write the implementation state document. If a prior version exists, read it first and incorporate what's still relevant.

$ARGUMENTS
