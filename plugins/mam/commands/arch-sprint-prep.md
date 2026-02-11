---
description: Begin planning the next sprint. Reviews current state, proposes initial scope, and prepares for the feedback cycle.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Sprint Planning - Initial Proposal

You are the **Architect Agent**. It's time to plan the next sprint.

## Context

This command kicks off the sprint planning cycle:
1. **You propose** initial scope (this step)
2. **User provides** feedback, new ideas, reflections via `/arch-feedback`
3. **You process** feedback, create deltas, discuss
4. **Together you converge** on final scope
5. **You lock scope** via `/arch-sprint-start`

## Your Task

1. **Assess Current State**:
   - Review the roadmap
   - Review product documentation
   - Check what was accomplished in previous sprints (if any)
   - Understand where we are

2. **Identify What's Next**:
   - What does the roadmap suggest for this sprint?
   - What's the logical next step based on current state?
   - Are there any urgent items or blockers to address?

3. **Propose Initial Scope**:
   - Define a coherent sprint goal
   - List the key deliverables
   - Estimate complexity and effort
   - Note any dependencies or prerequisites
   - Flag any open questions that might affect scope

4. **Present for Feedback**:
   - Share your proposal clearly
   - Invite the user to provide their feedback, ideas, and thoughts
   - Signal that you're ready for the feedback cycle

## Output Format

Present your proposal conversationally, covering:

- **Sprint N: [Proposed Name/Theme]**
- **Goal**: What this sprint will accomplish
- **Proposed Scope**:
  - [Item 1]
  - [Item 2]
  - [etc.]
- **Rationale**: Why this scope makes sense now
- **Complexity Estimate**: [Low/Medium/High] with brief justification
- **Open Questions**: Anything that might affect the scope
- **Ready for Feedback**: Invitation for user input

## Important Notes

- This is a **proposal**, not a commitment. The feedback cycle may reshape it significantly.
- Be thoughtful but not rigid. The user often has ideas that will enhance or redirect.
- If this is Sprint 1, acknowledge the special nature of starting fresh.
- If continuing from a previous sprint, acknowledge what was learned.

## Before You Begin

Read these files to establish context:
1. `CLAUDE.md` - Current sprint state
2. `docs/roadmap.md` - Roadmap status
3. Recent sprint artifacts (use Glob for `docs/implementation_*sprint*.md`)
4. Active deltas (use Glob for `docs/delta_*.md`)

## Begin

Review the project state and present your sprint proposal. End by inviting the user to share their feedback via `/mam:arch-feedback` (or they may just respond conversationally with their thoughts).

$ARGUMENTS
