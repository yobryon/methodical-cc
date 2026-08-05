---
description: Show methodical-cc bus status — current team, registered teammates, recent inbox activity, and active threads in this project.
allowed-tools: Read, Bash, Glob, Grep
---

# Bus Status

Show the bus state for the current project.

## Your Task

1. **Note your own identity** — visible in the `=== METHODICAL-CC BUS ===` SessionStart context block. If you're anonymous or no team block appeared, say so.

2. **Read the team config** at `~/.claude/teams/<team-name>/config.json` (where `<team-name>` is the project's team — derive from the cwd basename, sanitized). List the members.

3. **Check inbox state** for each member by reading `~/.claude/teams/<team-name>/inboxes/<name>.json` (if it exists). Report unread message counts.

4. **Enumerate active threads** by walking `docs/crossover/*/` for thread directories. List recent ones, especially those with the current session's identity as a participant.

5. **Present a compact summary** in this shape:
   - **You**: your resolved identity on team `<team>` (or anonymous)
   - **Members**: each name + agent_id, with unread counts
   - **Active threads**: thread_id → participants, recent activity

If the team config doesn't exist, tell the user to run `mcc team setup` (or just resume any session with `mcc <name>`, which sets it up implicitly).

$ARGUMENTS
