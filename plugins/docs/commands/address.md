---
description: Triage pending feedback files in docs/feedback/. Read each comment, propose edits to source markdown, file deferred items, and graduate the file to processed/ on completion.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Docs Address — Triage Stakeholder Feedback

You are helping the user process feedback from outside reviewers (pulled into `docs/feedback/` by `mcc docs pull`). Each file is a structured digest of Word comments on one published doc.

## Read the manifest

Read `.mcc/docs-publish.yml` to learn the configured `feedback_path` (default `docs/feedback`). Use that path throughout. If the manifest is missing, tell the user to run `mcc docs setup` first.

## Identify pending files

Pending = files at the top level of `feedback_path/`, **excluding** `feedback_path/processed/`. List them. If none are pending, say so and stop.

If `$ARGUMENTS` names a specific feedback file (path or filename), focus on that one. Otherwise, work through them in order — oldest first — and ask before moving from one file to the next, so the user can stop the session whenever they like.

## For each feedback file

1. **Read the file.** It's structured as front-matter (source path, reviewers, comment count) + a series of `## Comment N — <author>, <date>` sections, each with anchored section, excerpt, and body.
2. **Read the source markdown** (path is in the front-matter `source:` field). The comments may reference text that has since changed — note any drift.
3. **For each comment**, propose a disposition:
   - **Apply** — a clear edit to the source markdown. Show the proposed diff and ask for approval before applying.
   - **Defer** — file as a delta, decision-log entry, or concept-backlog item, depending on the active plugin context (PDT vs MAMA vs neither). Ask the user where it belongs.
   - **Reject** — note in your summary that the comment was considered and not adopted, and why. (No artifact written — the feedback file itself is the durable record.)
   - **Discuss** — comment needs the user's judgment before disposition.
4. **Track decisions** as you go so the closing summary is complete.

Cross-cutting: if multiple comments converge on the same theme (two reviewers flagging the same section, e.g.), surface that explicitly — convergent feedback is stronger signal than the sum of its parts.

## Graduate the file on completion

When all comments in a file are dispositioned (apply / defer / reject / explicitly-deferred-to-later-session), `git mv` it into `<feedback_path>/processed/`. The session-start hook surfaces only top-level feedback files; processed files are out of sight but still in the repo for archaeology.

```bash
mkdir -p <feedback_path>/processed
git mv <feedback_path>/<file>.md <feedback_path>/processed/<file>.md
```

If the user wants to stop mid-file (some comments dispositioned, others not), **leave the file in place** — don't graduate partial progress. The hook will continue to surface it next session.

## Closing summary

For each file processed, summarize:

- Source doc
- N comments total: X applied, Y deferred, Z rejected, W left for later
- Where deferred items landed (delta names, decision IDs, etc.)
- Any cross-cutting themes worth elevating to the user's attention

## Edge cases

- **Source file missing.** The source markdown may have been moved or deleted. Surface this and ask the user how to proceed — don't apply edits to a doc that no longer matches the published version.
- **Source has drifted.** If the anchored excerpt no longer appears in the source (rewritten, deleted), say so explicitly. The comment may still be relevant to the *intent* even if the surface has changed; ask the user whether to apply the spirit of the comment to current text.
- **Author identity.** Word comment authors are whatever Word identity each reviewer has configured. Don't try to map back to org identity; treat the name as given.
- **Empty comment / no anchor.** Some comments come through without anchored text. Note and proceed.

## Output format

Per file: short summary of the file, then walk through comments interactively. Don't dump the entire feedback file content — the user can read it; you focus on judgment.

End with the closing summary and the graduate-to-processed action.

$ARGUMENTS
