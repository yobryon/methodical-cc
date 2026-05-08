---
description: Publish selected docs as docx to the configured publish_path. Runs a readiness check first, then invokes `mcc docs publish`.
allowed-tools: Read, Bash, Glob, Grep
---

# Docs Publish — Readiness Check + Publish

You are helping the user publish project documentation to the stakeholder-facing surface (typically a SharePoint folder synced via OneDrive). The mechanical work is `mcc docs publish`; your job is the **readiness check** before that command runs.

## Inputs

- The manifest at `.mcc/docs-publish.yml` declares which docs are in scope. Read it.
- `$ARGUMENTS` may contain a narrower pattern set (e.g., `docs/pdt`, `docs/**/spec.md`) to publish only a subset. If empty, publish everything in the manifest.

## Readiness check

Before invoking the CLI, briefly survey for things the user should know about *before* docs go to outside reviewers:

1. **In-flight work.** Are there active deltas (`docs/delta_*.md`) that touch any docs in publish scope? If so, the published version may not reflect a recent direction.
2. **Drafts marked as such.** Skim front-matter and headings for `[DRAFT]`, `WIP`, `TODO`, or similar markers in any docs about to publish.
3. **Recent uncommitted changes.** Run `git status` and look at diffs touching publish-scope docs. If the user is mid-edit, ask whether they want to commit/finish first.
4. **Unaddressed feedback from a prior cycle.** Check `docs/feedback/` (or whatever `feedback_path` is configured) for existing files. If any are still pending, surface them — re-publishing before addressing prior feedback can confuse reviewers.

Surface findings concisely. Do **not** block — the user decides whether to proceed.

## Publish

After the readiness check, ask the user whether to proceed. If yes:

```bash
mcc docs publish $ARGUMENTS
```

(Pass `$ARGUMENTS` through verbatim — empty string means "everything in the manifest"; otherwise it narrows.)

Report the result: how many files published, any errors. If the publish_path is a symlink to a synced folder, remind the user that the sync may take a moment to push outward, and that they should notify reviewers (out of scope — Teams, email, etc.) once the sync settles.

## Edge cases

- **No manifest.** If `.mcc/docs-publish.yml` doesn't exist, tell the user to run `mcc docs setup` first. Don't try to set it up for them — setup is interactive.
- **publish_path missing.** If the path doesn't exist, tell the user they need to create it (typically a symlink to their synced folder). Don't create it yourself — the user owns the outward-sync mechanism.
- **pandoc missing.** The CLI will surface this with a clear error. Just relay it.

## Output format

Keep it short:

- Readiness summary (a few bullets, or "nothing flagged")
- Confirm intent
- Run command, relay result

$ARGUMENTS
