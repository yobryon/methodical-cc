---
description: Triage pending feedback in docs/feedback/. For each pending comment, decide on action with the user, write the disposition prose into the feedback file, and flip its status to addressed.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Docs Address — Triage Stakeholder Feedback

You are helping the user process reviewer feedback pulled into `docs/feedback/` by `mcc docs pull`. Each file is **one comment** from one published doc — and your job is to help the user disposition each comment **with the reviewer as the eventual audience**: the prose you write under `## Disposition` will ship to that reviewer in the response companion docx on the next `mcc docs publish`.

## Read the manifest

Read `.mcc/docs-publish.yml` to learn the configured `feedback_path` (default `docs/feedback`). Use that path throughout. If the manifest is missing, tell the user to run `mcc docs setup` first.

## File shape

Each feedback file is a single comment. Frontmatter carries the lifecycle flag (`status: pending | addressed`), plus enough context (source, comment_id, author, section, anchor excerpt) to render the response sidecar later. The body has two sections: `## Comment` (the reviewer's verbatim comment) and `## Disposition` (initially a stub — *your* writing target).

## Identify pending files

Pending = files where frontmatter `status:` is `pending`. Don't look at file location or subdirectory — the new flow keeps files in place; status in the frontmatter is the canonical signal.

If `$ARGUMENTS` names a specific feedback file, focus on that one. Otherwise list pending files (oldest first by `pulled_at`) and ask which to tackle, or walk them in order asking before moving to the next.

## For each pending feedback file

1. **Read the file.** Get frontmatter, the reviewer's comment, and the section/excerpt the comment was anchored to.
2. **Read the source markdown** (frontmatter `source:`). The comments may reference text that has since changed — note any drift.
3. **Discuss with the user what the disposition should be.** Common shapes:
   - **Apply** — make a clear edit to the source markdown. Show the proposed diff, apply on approval.
   - **Defer** — explicitly defer; optionally file as a delta, decision-log entry, or backlog item depending on the active plugin context (PDT vs MAMA vs neither). The disposition prose should name where it landed (or that it's queued).
   - **Reject** — explain why; nothing else to file.
   - **Discuss** — the user needs to think more; leave the file pending and move on.
4. **Write the disposition prose** into the `## Disposition` section, **replacing the `*Pending — ...*` stub**. Write for the reviewer:
   - Lead with what was done (or not done, and why).
   - Reference specific changes when applicable ("Added a §Verification subsection to address this" / "Deferred to a follow-on doc — see DocFoo §X").
   - Keep it concise. The reviewer needs to know their input was considered, not a treatise.
5. **Flip the frontmatter** `status: pending` → `status: addressed`. This is what the next `mcc docs publish` reads to decide whether the source is ready to ship.

If the user wants to stop mid-comment, **leave the file's status as `pending`** — half-written dispositions don't ship. The next session resumes the file at the same state.

## Cross-cutting themes

If multiple comments converge on the same idea (two reviewers flagging the same section, e.g.), surface that explicitly to the user — convergent feedback is stronger signal than the sum of its parts. Each comment still gets its own disposition prose in its own file (the response sidecar shows them grouped), but the user may want to apply one larger edit that resolves several at once.

## Closing summary

Per file processed, briefly note:
- The source doc and section
- What you did (applied / deferred / rejected / discussed)
- Where any deferred work landed (delta name, decision id, backlog entry)

Then: "N files addressed; M still pending."

## Edge cases

- **Source file missing.** The source markdown may have been moved or deleted. Surface this and ask the user how to proceed — don't apply edits to a doc that no longer matches the published version.
- **Source has drifted.** If the anchored excerpt no longer appears in the source (rewritten, deleted), say so explicitly. The comment may still be relevant to the *intent* even if the surface has changed; ask the user whether to apply the spirit of the comment to current text. Whatever you decide, name it in the disposition prose so the reviewer understands.
- **Author identity.** Word comment authors are whatever Word identity each reviewer has configured. Don't try to map back to org identity; treat the name as given.
- **Empty comment / no anchor.** Some comments come through without anchored text. Note and proceed — the disposition prose can call out that the comment was bare.
- **Legacy feedback files (no `comment_id` in frontmatter).** These are from a pre-2.0 pull. Tell the user to run `mcc docs pull --resync` to re-pull under the per-comment structure; old files can be removed or kept as archaeology — they won't appear in response sidecars.

## Output format

Per file: short summary of the file, then walk through the comment interactively. Don't dump the entire feedback file content — the user can read it; you focus on judgment and on writing the disposition prose.

End with the closing summary.

$ARGUMENTS
