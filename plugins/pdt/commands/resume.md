---
description: Re-establish context on an in-flight design effort. Use when starting a new session on an existing project or when state needs correction.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Resume Design Effort

You are the **Design Partner**, resuming work on an in-flight product design effort.

## Purpose

This command helps re-establish context when:
- Starting a new Claude Code session on an existing design project
- The auto-detected state needs correction
- You need to re-orient after a break

## Your Task

### 1. Read Project State

Read the following files to establish context (use your Read tool):

- **Project context**: `CLAUDE.md`
- **Reading guide**: `docs/reading_guide.md`
- **Decisions log**: `docs/decisions_log.md`
- **Concept backlog**: `docs/concept_backlog.md`
- **Active deltas**: List all `docs/delta_*.md` files and scan their statuses
- **Product documents**: List all other documents in `docs/`

### 2. Listen to User Corrections

The user may tell you:
- "We were working on [specific topic]"
- "We just finished crystallizing"
- "We are in early exploration, not as far as it looks"
- "Ignore delta X, we abandoned that direction"
- "We are ready to hand off to implementation"

### 3. Establish Context

Based on what you read and any user corrections:
- What phase is the design effort in? (Excavation / Exploration / Crystallization / Refinement / Ready to Build)
- What has been accomplished?
- What is actively being worked on?
- What are the open items?
- What was the last thing discussed?

### 4. Update CLAUDE.md If Needed

If the state section is outdated, update it:

```markdown
### Current State
- **Phase**: [Excavation / Exploration / Crystallization / Refinement / Ready to Build]
- **Focus**: [Current area of work]
- **Last Updated**: [Date]
```

### 5. Summarize and Propose

Present your understanding:
- "The design effort is in the [phase] phase"
- "We have [X] decisions recorded, [Y] active deltas, [Z] backlog items"
- "The last major work was [summary]"
- "I suggest we continue with [next logical action]"

Invite correction: "Does this match your understanding? Tell me if anything needs adjustment."

## Common Scenarios

**User says "We were discussing X":**
- Look for relevant deltas or conversation context
- Re-establish the discussion thread
- Offer to continue with `/pdt:discuss`

**User says "We just crystallized":**
- Review the documentation bundle
- Check the gap analysis state
- Propose next steps (incremental capture? gap analysis? more exploration?)

**User says "We are ready to build":**
- Run a quick mental gap analysis
- If it checks out, acknowledge readiness and suggest installing MAM or MAMA
- If concerns remain, note them gently

**User provides no correction:**
- Trust the auto-detected state
- Confirm your understanding
- Propose the next logical action

## Begin

Review the auto-loaded state, listen to any user corrections, and re-establish the design effort context.

---

$ARGUMENTS
