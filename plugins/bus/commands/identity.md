---
description: Show the current session's resolved bus identity. If anonymous, explain how to register.
allowed-tools: Read, Bash, Glob, Grep
---

# Bus Identity

Tell the user who they are on the methodical-cc bus right now.

## Your Task

1. Look at the `=== METHODICAL-CC BUS ===` block in your SessionStart context (it tells you your resolved identity).
2. If identity is registered: tell the user their identity name and which sessions file it came from. Mention they can `peer_send` and be addressed by name.
3. If identity is `anonymous`: tell the user they can still send messages but peers can't reach them. Show them the registration commands:
   - `/pdt:session set <name>` (PDT)
   - `/mam:session set <name>` (MAM)
   - `/mama:session set <name>` (MAMA)
4. If the bus context block is missing entirely: the bus plugin may not be enabled or set up. Recommend `mcc bus setup`.

Keep the response short and concrete — this is a diagnostic command.

$ARGUMENTS
