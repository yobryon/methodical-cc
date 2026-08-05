# docs — Stakeholder Documentation Sharing

Companion plugin for sharing project documentation with non-repo stakeholders and ingesting their feedback as anchored, repo-local artifacts. Orthogonal to PDT/MAM/MAMA — opt-in, complements without being load-bearing.

## What it does

- **Publish** selected markdown docs as `.docx` to a local folder you've configured to sync outward (typically OneDrive → SharePoint). Each source ships alongside a `<doc>-responses.docx` companion that lists every comment ever received and how the author responded.
- **Pull** Word inline comments back as **one structured feedback file per comment** in `docs/feedback/`, with author, anchored excerpt, section context, and a `## Disposition` section the author fills in.
- **Address** the feedback inside any active session — Claude reads the file, helps the user decide what to do, **writes the disposition prose directly into the feedback file**, and flips its `status: pending` to `status: addressed` so the next publish ships it to reviewers.

## Quickstart

```bash
mcc docs setup           # interactive: writes .mcc/docs-publish.yml
# (manually) symlink .mcc/publish/ → your synced SharePoint folder
mcc docs publish         # convert sources to .mcc/publish/ + emit response sidecars
# ... reviewers comment in Word ...
mcc docs pull            # parse comments → one docs/feedback/<slug>__c<id>.md per comment
# ... /docs:address writes dispositions, author edits source, flips status ...
mcc docs publish         # ships updated docs + updated response sidecars
```

In any active Claude Code session: `/docs:publish` runs a readiness check before invoking the CLI; `/docs:address` triages pending feedback by walking each file and writing dispositions with you.

## The response-companion model

When you publish a source doc, you also publish a sibling `<doc>-responses.docx` with the full disposition history — every comment ever received on this source, chronologically, with each reviewer's text and your written response. Reviewers landing on an updated version don't have to dig through SharePoint version history to find out whether their input was heard; the companion doc tells them.

This is "always full history" by design: the companion isn't a per-round changelog; it's a comprehensive audit trail that grows over time.

## Publish preflight

`mcc docs publish` scans `docs/feedback/` for files with `status: pending` and **aborts by default** if any of the targets you asked to publish still have unresolved dispositions. You can:

- Resolve them first (recommended) — edit the disposition section in each feedback file, flip status to `addressed`, re-run.
- `mcc docs publish --skip-pending` — publish only docs whose feedback is fully addressed; skip the rest.
- `mcc docs publish --include-pending` — publish everything; pending dispositions ship marked `PENDING` in the response sidecar.

## Design

See `docs/docs-design.md` in this repo for the design document.

## Requirements

- `pandoc` on PATH. `mcc docs setup` detects and prompts.
- Python 3.8+ (stdlib only).
- A folder you control that syncs outward to your stakeholders' surface (OneDrive / SharePoint / Dropbox / etc.). The plugin doesn't manage this; you set up the symlink (or the path) yourself.

## Status

v1.2.0. Markdown-in, docx-out + per-comment feedback files + response sidecars. PDF, SharePoint Pages, and direct Graph API integration are deferred to future versions if patterns emerge.
