---
description: Show methodical-cc bus status — registered identities, recent activity, pending message counts, active threads in this project.
allowed-tools: Read, Bash, Glob, Grep
---

# Bus Status

Show the bus state for the current project: who's registered, what's pending, and what threads are active.

## Your Task

1. Call `peer_list` (the bus MCP tool) to get the registered identities, last activity, and pending message counts.
2. Walk `docs/crossover/*/` to enumerate active threads (status = "open" in `.bus-state.json`).
3. Note the current session's resolved identity (visible in the `=== METHODICAL-CC BUS ===` SessionStart context).
4. Present a compact summary:
   - **Identities**: each name → registered file, last activity, pending count
   - **Active threads**: thread_id → participants, last activity, awaiting whom
   - **You**: your resolved identity (or note that you're anonymous)

If the bus isn't enabled or the MCP tools aren't available, tell the user to run `mcc bus setup`.

$ARGUMENTS
