---
description: Show the current state of the docs publishing system - manifest config, pending feedback, recent activity.
allowed-tools: Read, Bash, Glob
---

# Docs Status

Run `mcc docs status` and relay the output.

If the user has questions about specific aspects (e.g., "why is publish_path missing?"), read the manifest at `.mcc/docs-publish.yml` and the relevant filesystem state to give a concrete answer.

If the manifest is missing, tell the user to run `mcc docs setup`.

$ARGUMENTS
