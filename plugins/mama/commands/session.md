---
description: Register or recall session IDs for quick resumption by persona name. Run "set <name>" to register the current session, "list" to show registered sessions, or "clear <name>" to remove one.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Session Management

The current session ID is: **${CLAUDE_SESSION_ID}**

## Your Task

Parse the user's arguments and perform the requested action. All session registry data lives at `.mcc/sessions` in the project root (or `.mcc-{scope}/sessions` for scoped projects).

### `set <name> [--scope <s>]`

Register the current session under the given name (e.g., `arch`, `impl`, `design`).

Run the helper, which handles state-dir picking (including `.mcc-{scope}/` disambiguation in multi-project repos):

```
mcc session set <name> ${CLAUDE_SESSION_ID} [--scope <s>]
```

If `--scope` was passed, forward it through. If not and the project has multiple `.mcc-{scope}/` directories, the helper will refuse with a hint to pass `--scope`.

After the helper succeeds, also report: `Registered <name>=<id>. Resume with: mcc <name>` so a calling shell (e.g. `mcc create`) can verify.

### `list`

Show all registered sessions for this project.

1. Find the state directory (`.mcc/` or `.mcc-{scope}/`)
2. Read `{state_dir}/sessions`
3. Display each name and its session ID
4. Note which ones can be resumed with: `mcc <name>` (the methodical-cc helper, found in `tools/mcc`)

### `clear <name>`

Remove a registered session.

1. Find the state directory
2. Read `{state_dir}/sessions`
3. Remove the line matching the given name
4. Write the file back

### No arguments

Show usage: `set <name>`, `list`, `clear <name>`

## Sessions File Format

```
arch=c4b062d8-dd97-4ef8-a99c-19cb6416f991
impl=f1904c21-8490-49ab-88ed-d4fc6295f80f
```

Simple, one per line, no quoting needed. Names are freeform — the user picks whatever makes sense to them.

## Begin

$ARGUMENTS
