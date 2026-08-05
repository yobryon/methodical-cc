---
description: Show the current state of the docs publishing system - manifest config, pending dispositions by source, and recent activity.
allowed-tools: Read, Bash, Glob
---

# Docs Status

Run `mcc docs status` and relay the output. The output covers:

- Where the manifest lives and the publish/feedback paths
- How many docs are declared in the manifest
- How many feedback comments have been pulled, how many are addressed vs pending
- A per-source breakdown of which docs have pending dispositions (when any do)

If the user has questions about specific aspects (e.g., "why is publish_path missing?" or "which comment is still pending for spec.md?"), read the manifest at `.mcc/docs-publish.yml` and the relevant feedback file(s) under `docs/feedback/` to give a concrete answer. The per-comment files use frontmatter `status: pending|addressed` as the canonical flag — that's what to look at.

If the manifest is missing, tell the user to run `mcc docs setup`.

If status surfaces legacy feedback files (files lacking a `comment_id` in frontmatter), tell the user that re-pulling via `mcc docs pull --resync` will re-emit them as per-comment files compatible with the response-sidecar flow. Old files can be deleted or kept as archaeology.

$ARGUMENTS
