---
description: Show the current session's resolved bus identity and team membership. If anonymous, explain how to register.
allowed-tools: Read, Bash, Glob, Grep
---

# Bus Identity

Tell the user who they are on the methodical-cc bus right now.

## Your Task

1. Look at the `=== METHODICAL-CC BUS ===` block in your SessionStart context (it tells you your resolved identity, team name, and other members).

2. If identity is registered: tell the user their identity name (e.g. `arch`), their agent_id (`arch@<team>`), and the team they're on. Mention they can use `SendMessage` to message any teammate by name and that messages from teammates arrive automatically as new turns.

3. If identity is `anonymous`: tell the user they can still send messages (if the session was launched with team flags) but peers can't reach them by name. Show them how to register:
   - `/pdt:session set <name>` (PDT)
   - `/mam:session set <name>` (MAM)
   - `/mama:session set <name>` (MAMA)

4. If the bus context block is missing entirely: the bus plugin may not be enabled, or the team config hasn't been set up yet. Recommend `mcc team setup` — or just resume any session via `mcc <name>` which will set it up implicitly.

Keep the response short and concrete — this is a diagnostic command.

$ARGUMENTS
