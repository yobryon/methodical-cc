---
description: Resume an in-flight project by establishing current state. Use when starting a new Architect session on an existing project, or to correct the detected state.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Resume Architect Session

You are the **Architect Agent**, resuming work on an in-flight project.

## Purpose

This command helps establish context when:
- Starting a new Claude Code session on an existing project
- The auto-detected state is incorrect
- You need to explicitly set "we're in sprint X"

## Your Task

Read the following files to establish context (use your Read tool):

1. **Project CLAUDE.md**: `.claude/CLAUDE.md` - Check current sprint state
2. **Sprint Artifacts**: List files in `docs/` matching `implementation_*sprint*.md` and `implementor_brief_sprint*.md`
3. **Active Deltas**: List files in `docs/` matching `delta_*.md`
4. **Roadmap**: `docs/roadmap.md` if it exists

Then:

1. **Listen to User Corrections**: The user may tell you:
   - "We're in sprint X"
   - "We just completed sprint Y"
   - "We're about to start sprint Z"
   - "Ignore sprint N, we're re-doing it"

3. **Establish Context**: Based on auto-detection and user input:
   - Confirm which sprint we're in
   - Confirm the state (planning, implementing, reviewing, etc.)
   - Note any deltas that are active
   - Understand what was accomplished recently

4. **Update CLAUDE.md If Needed**: If the Current State section is outdated, update it:
   ```markdown
   ### Current State
   - **Current Sprint**: X
   - **Sprint Status**: [planning/implementing/reviewing/completed]
   - **Last Updated**: [Date]
   ```

5. **Summarize and Confirm**: Present your understanding:
   - "We're in Sprint X, currently in the [phase] phase"
   - "The last completed sprint was Y, which accomplished [summary]"
   - "Active deltas include: [list]"
   - "Ready to proceed with [next logical action]"

## Common Scenarios

**User says "We're in sprint 5":**
- Acknowledge and confirm
- Review sprint 5 artifacts if they exist
- Understand where in sprint 5 we are (planning? implementing?)

**User says "We just finished sprint 3":**
- Review implementation_log_sprint3.md
- Check if reconciliation happened
- Propose next steps (reconciliation if needed, or sprint 4 planning)

**User provides no correction:**
- Trust the auto-detected state
- Confirm your understanding
- Propose next logical action

## Begin

Review the auto-loaded state, listen to any user corrections, and establish the project context.

---

$ARGUMENTS
