---
description: Commit the current changes with an appropriate message. Checks sprint context for intent, stages relevant files, and writes a message that reflects what changed and why.
allowed-tools: Read, Bash, Glob, Grep
---

# Commit Changes

Commit the current work with a well-crafted message.

## Your Task

### 1. Understand the Context

Check for sprint context that explains the *intent* behind the changes:
- Look for an active implementation log in `docs/sprint/*/` or `docs/*/sprint/*/` (most recent)
- Glance at `.mcc*/architect_state.md` for current sprint goal if available
- If the user provided arguments describing what this commit is about, use that

This context helps you write a message about *why*, not just *what*.

### 2. Review the Changes

Run `git status` and `git diff` (staged and unstaged) to understand what changed.

### 3. Stage and Commit

Stage the relevant files and commit with a message that reflects the work.

If the user provided specific instructions (e.g., "commit the refactor" or "commit everything except the tests"), follow them.

## Begin

Review the changes, pick up any sprint context, and commit.

$ARGUMENTS
