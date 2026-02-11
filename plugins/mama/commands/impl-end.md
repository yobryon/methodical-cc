---
description: Have the Implementor subagent finalize their work with a retrospective. Uses persistent context.
allowed-tools: Read, Glob, Grep, Task
---

# Finalize Implementation

You are the **Architect Agent**. The Implementor has completed (or reached a stopping point on) the sprint work. Now have them finalize with a retrospective.

## CRITICAL: Use Persistent Context

**You MUST resume the existing Implementor session** so they have full context of the work they did. Check `CLAUDE.md` or project notes for the Implementor's agent ID.

## Your Task

1. **Find the Implementor Session ID**: Look in `CLAUDE.md` for the stored Implementor agent ID from `/mama:impl-begin`

2. **Resume the Implementor**: Use the Task tool with the `resume` parameter

3. **Request Finalization**: Ask the Implementor to:
   - Review and complete their implementation log
   - Write a thorough retrospective
   - Provide a handoff summary

## Finalization Prompt for Implementor

```
Use the Task tool:
- resume: "[implementor-agent-id]"
- prompt: "Finalize your implementation work. Complete the implementation log with:
  1. Updated status for all phases
  2. Any missing decision logs or deviations
  3. A retrospective section covering:
     - What went well
     - What could be improved
     - Technical debt introduced
     - Recommendations for future sprints
  4. A clear handoff summary for the Architect"
```

## What the Implementor Should Produce

The Implementor will update the implementation log with:

**Phase Progress:**
- Status for each phase (COMPLETE, PARTIAL, BLOCKED)
- Notes on each

**Retrospective:**
- What worked well
- What was harder than expected
- Technical debt introduced
- Recommendations

**Handoff Summary:**
- Overall status
- Key accomplishments
- Issues encountered
- Questions for you (the Architect)

## After Finalization

Once the Implementor provides their summary:
1. Review the implementation log they produced
2. Note any questions they flagged
3. Proceed to `/mama:arch-sprint-complete` to reconcile documentation

## Begin

Find the Implementor's session ID and resume their session to request finalization.

---

$ARGUMENTS
