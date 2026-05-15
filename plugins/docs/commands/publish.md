---
description: Publish selected docs as docx to the configured publish_path. Runs a readiness check first, then invokes `mcc docs publish`.
allowed-tools: Read, Bash, Glob, Grep
---

# Docs Publish — Readiness Check + Publish

You are helping the user publish project documentation to the stakeholder-facing surface (typically a SharePoint folder synced via OneDrive). The mechanical work is `mcc docs publish`; your job is the **readiness check** before that command runs.

## Inputs

- The manifest at `.mcc/docs-publish.yml` declares which docs are in scope. Read it.
- `$ARGUMENTS` may contain a narrower pattern set (e.g., `docs/pdt`, `docs/**/spec.md`) to publish only a subset. Pass `$ARGUMENTS` through verbatim to the CLI — empty means "everything in the manifest".

## Readiness check

Before invoking the CLI, briefly survey for things the user should know about *before* docs go to outside reviewers:

1. **In-flight work.** Are there active deltas (`docs/delta_*.md`) that touch any docs in publish scope? If so, the published version may not reflect a recent direction.
2. **Drafts marked as such.** Skim front-matter and headings for `[DRAFT]`, `WIP`, `TODO`, or similar markers in any docs about to publish.
3. **Recent uncommitted changes.** Run `git status` and look at diffs touching publish-scope docs. If the user is mid-edit, ask whether they want to commit/finish first.

You do **not** need to check feedback status here — `mcc docs publish` does that itself (and will abort with a precise per-source breakdown of pending dispositions if any are unresolved). Don't pre-empt; let the CLI surface its own preflight.

Surface findings concisely. Do **not** block — the user decides whether to proceed.

## Publish

After the readiness check, ask the user whether to proceed. If yes:

```bash
mcc docs publish $ARGUMENTS
```

### Interpreting the preflight outcome

The CLI does its own preflight scan of `docs/feedback/` and reacts to pending dispositions in one of three ways:

- **No pending dispositions for the docs in scope** → publishes normally. Each published source ships alongside a regenerated `*-responses.docx` sidecar carrying the full disposition history.
- **Pending dispositions exist** and the user didn't pass a flag → the CLI **aborts with exit 1** and prints a per-source pending count plus the two override flags. Relay the output to the user and help them choose:
  - `mcc docs publish --skip-pending` — publish only the docs whose feedback is fully addressed; silently exclude the rest.
  - `mcc docs publish --include-pending` — publish everything, accepting that some dispositions will ship marked `PENDING` in the response sidecar.
  - Or: address the pending items first via `/docs:address` and re-publish.
- **`--include-pending` was passed and pending exists** → the CLI warns and proceeds. The response sidecars for affected sources will include the comment with a `PENDING` marker and a placeholder disposition.

Pick the path that matches user intent. If the user didn't realize feedback was unaddressed, gently steer them toward `/docs:address` first — the response companion is more useful when it's complete.

## After publish

Report concisely: how many files published, how many response sidecars generated, any errors. If the publish_path is a symlink to a synced folder, remind the user that the sync may take a moment to push outward, and that they should notify reviewers (out of scope — Teams, email, etc.) once the sync settles.

## Edge cases

- **No manifest.** If `.mcc/docs-publish.yml` doesn't exist, tell the user to run `mcc docs setup` first. Don't try to set it up for them — setup is interactive.
- **publish_path missing.** If the path doesn't exist, tell the user they need to create it (typically a symlink to their synced folder). Don't create it yourself — the user owns the outward-sync mechanism.
- **pandoc missing.** The CLI will surface this with a clear error. Just relay it.

## Output format

Keep it short:

- Readiness summary (a few bullets, or "nothing flagged")
- Confirm intent
- Run command, relay result (including any preflight abort + the three options)

$ARGUMENTS
