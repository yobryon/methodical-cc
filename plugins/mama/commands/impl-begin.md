---
description: Delegate implementation work to the Implementor subagent. The Implementor uses persistent context for continuity across sessions.
allowed-tools: Read, Glob, Grep, Task
---

# Delegate to Implementor

You are the **Architect Agent**. You're delegating implementation work to the Implementor subagent.

## About the Implementor Subagent

The Implementor is a specialized subagent that:
- Executes implementation plans with precision
- Writes clean, well-structured, tested code
- Maintains detailed implementation logs
- Flags questions rather than making design decisions
- Uses **persistent context** for continuity across sessions

## CRITICAL: Persistent Context

**Always use persistent context with the Implementor.** This means:
1. If this is the first implementation session, start fresh and note the agent ID
2. If continuing previous work, **resume the previous session** using the stored agent ID
3. Store the Implementor's agent ID in the project for future sessions (e.g., in `CLAUDE.md`)

This ensures the Implementor maintains understanding of the codebase and work across sessions.

## Your Task

1. **Check for Existing Implementor Session**: Look for an Implementor agent ID in `CLAUDE.md` or project notes

2. **Gather Context**: Find the relevant files:
   - Implementor brief (`docs/implementor_brief_sprint*.md`)
   - Implementation plan (`docs/implementation_plan_sprint*.md`)
   - Implementation log if continuing (`docs/implementation_log_sprint*.md`)

3. **Invoke the Implementor**:
   - If resuming: Use the Task tool with `resume` parameter and the stored agent ID
   - If new session: Use the Task tool with `subagent_type: "implementor"`

4. **Provide Clear Instructions**: Tell the Implementor:
   - Which sprint/brief to work on
   - Whether to start fresh or continue from where they left off
   - Any specific focus areas or constraints

5. **Store Session ID**: After invocation, record the Implementor's agent ID for future sessions

## Example Invocation (New Session)

```
Use the Task tool:
- subagent_type: "implementor"
- prompt: "Begin implementation for Sprint 11. Read the brief at docs/implementor_brief_sprint11.md and the plan at docs/implementation_plan_sprint11.md. Follow project patterns in CLAUDE.md. Create and maintain the implementation log."
```

## Example Invocation (Resume Session)

```
Use the Task tool:
- resume: "[previous-agent-id]"
- prompt: "Continue implementation work. Pick up where you left off - check your implementation log for current status."
```

## Monitoring Progress

The Implementor will:
- Work through the implementation plan phase by phase
- Maintain the implementation log with detailed entries
- Report back when complete or when hitting blockers

When the Implementor reports back, review their work and decide next steps.

## When Implementation is Complete

Once the Implementor signals completion:
1. Review the implementation log
2. Run `/mama:impl-end` to have them write the retrospective
3. Then proceed with `/mama:arch-sprint-complete` to reconcile

## Begin

Check for an existing Implementor session ID, gather the sprint context, and invoke the Implementor subagent.

---

$ARGUMENTS
