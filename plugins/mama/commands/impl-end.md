---
description: Finalize the sprint as the Implementor — complete the implementation log, send a handoff summary to the Architect, and report briefly to the user.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, SendMessage, TaskList, TaskUpdate
---

# Finalize Implementation

You are the **Implementor**. The implementation work for this sprint is complete (or at a stopping point). Wrap it up and hand off to the Architect.

This command is invoked in **your** session — either by the user directly, or as the result of an `[IMPL-END-REQUESTED]` message from the Architect telling you to wrap up so they can reconcile.

## Your Task

### 1. Complete the Implementation Log

Find your sprint's `docs/sprint/{N}/implementation_log.md` (or scoped equivalent) and ensure it is thorough:

- **Phase status table** — update every phase: COMPLETE, PARTIAL, BLOCKED, etc., with a one-line note for each
- **Decisions** — every non-obvious decision logged with rationale
- **Deviations** — anything that diverged from the plan, with the reason
- **Bugs/issues** — root cause analysis, not just symptoms
- **Retrospective section** at the bottom:
  - What went well
  - What was harder than expected
  - Technical debt introduced (and why it was acceptable)
  - Recommendations for future sprints

Be honest — log reality, not the polished version.

### 2. Send the Handoff to the Architect

Compose a tight handoff summary and send it via `SendMessage`. The message **must** start with the `[HANDOFF]` tag so the Architect recognizes it as the sprint-completion trigger.

```
SendMessage(to='arch', message='[HANDOFF] Sprint {N} {complete|partial|blocked}.

<2-4 sentence summary of what was done>

Key points:
- <accomplishment or decision>
- <issue or tech debt>
- <question or recommendation>

Log: docs/sprint/{N}/implementation_log.md')
```

Keep it under ~200 words — the Architect will read the log for full detail. The handoff is the framing, not the substance.

### 3. Brief the User

Tell the user **in one or two sentences** that the handoff was sent. Do not re-explain the handoff content here — they can read the message you just sent and the log itself if they want detail. Example:

> Handoff sent to arch. Sprint {N} is finalized in the log; ready for arch to reconcile.

Then stop. Don't propose next steps, don't offer to do more — your job for this sprint is done. The user controls what happens next (typically: switch to the arch session and run `/mama:arch-sprint-complete`).

## Notes

- **Persistent state document** (`implementor_state.md`) is **not** rewritten here by default. Long-lived sessions carry working knowledge in-context; the on-disk doc is only needed when bootstrapping a fresh Implementor session. If the user explicitly asks for it (or you're about to end a long-running session and want to checkpoint), refresh it then — otherwise skip.
- If you were prompted by an `[IMPL-END-REQUESTED]` message from the Architect, this whole flow is the same; just respond with the handoff in the same shape.

## Begin

Review your implementation log, complete any missing sections, write the retrospective, send the `[HANDOFF]` message, and brief the user.

$ARGUMENTS
