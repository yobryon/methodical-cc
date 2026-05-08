# docs — Stakeholder Documentation Sharing

Companion plugin for sharing project documentation with non-repo stakeholders and ingesting their feedback as anchored, repo-local artifacts. Orthogonal to PDT/MAM/MAMA — opt-in, complements without being load-bearing.

## What it does

- **Publish** selected markdown docs as `.docx` to a local folder you've configured to sync outward (typically OneDrive → SharePoint).
- **Pull** Word inline comments back as structured `docs/feedback/<doc>-<timestamp>.md` files with author, anchored excerpt, and section context.
- **Address** the feedback inside any active session — Claude reads the feedback file, proposes edits to source markdown, and graduates the file to `processed/` on completion.

## Quickstart

```bash
mcc docs setup           # interactive: writes .mcc/docs-publish.yml
# (manually) symlink .mcc/publish/ → your synced SharePoint folder
mcc docs publish         # convert and write to .mcc/publish/
# ... reviewers comment in Word ...
mcc docs pull            # parse comments → docs/feedback/*.md
```

In any active Claude Code session: `/docs:publish` runs a readiness check before invoking the CLI; `/docs:address` triages pending feedback.

## Design

See `docs/docs-design.md` in this repo for the design document.

## Requirements

- `pandoc` on PATH. `mcc docs setup` detects and prompts.
- Python 3.8+ (stdlib only).
- A folder you control that syncs outward to your stakeholders' surface (OneDrive / SharePoint / Dropbox / etc.). The plugin doesn't manage this; you set up the symlink (or the path) yourself.

## Status

v1.0.0. Markdown-in, docx-out only. PDF, SharePoint Pages, and direct Graph API integration are deferred to future versions if patterns emerge.
