---
description: Register or recall session IDs for quick resumption by persona name. Run "set <name>" to register the current session, "list" to show registered sessions, or "clear <name>" to remove one.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          shell: bash
          command: "echo \"Current session ID: $(cat /dev/stdin | sed -n 's/.*\"session_id\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p')\""
---

# Session Management

You have access to the current session's ID via the hook output in your context (look for "Current session ID: ...").

## Your Task

Parse the user's arguments and perform the requested action.

### `set <name>`

Register the current session under the given name (e.g., `design`, `pdt`).

1. Create `.pdt/` if it doesn't exist
2. Read the current session ID from the hook context above
3. Read `.pdt/sessions` if it exists (simple `name=id` format, one per line)
4. Add or update the line for the given name
5. Write the file back

### `list`

Show all registered sessions for this project.

1. Read `.pdt/sessions`
2. Display each name and its session ID
3. Note which ones can be resumed with: `cc <name>` (or whatever the resume script is named)

### `clear <name>`

Remove a registered session.

1. Read `.pdt/sessions`
2. Remove the line matching the given name
3. Write the file back

### No arguments

Show usage: `set <name>`, `list`, `clear <name>`

## Sessions File Format

```
design=c4b062d8-dd97-4ef8-a99c-19cb6416f991
```

Simple, one per line, no quoting needed. Names are freeform — the user picks whatever makes sense to them.

## Begin

$ARGUMENTS
