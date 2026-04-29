---
description: Upgrade a project's MAM artifacts to the current plugin version. Migrates state directories, sprint artifact layout, organizational patterns, and methodology shifts. Safe to run multiple times — skips already-completed transitions.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# MAM Upgrade

You are the **Architect Agent**. This command upgrades a project's MAM artifacts to match the current plugin version (3.0.0).

Upgrades are **cumulative** — if a project is several versions behind, all intermediate transitions are applied in order. Each transition is **idempotent** — already-completed steps are skipped.

## Your Task

### 1. Detect Current Version

Look for the project's state directory:
- Check for `.mam/` or `.mam-{scope}/` directories
- If found, read `architect_state.md` and look for a `MAM Version:` line
- Also check for `.mama/` or `.mama-{scope}/` directories (MAMA → MAM migration)
- If no state directory exists, the project is **pre-2.0.0**

Record the detected version. If no version is found, treat it as `0.0.0` (pre-versioning).

Also check: does the user want to establish a scope? If they're in a multi-product setup but don't have scoped directories yet, ask.

### 2. Apply Transitions

Apply each transition in order, skipping any that are already complete:

---

#### Transition: MAMA → MAM

**Conditions**: `.mama/` or `.mama-{scope}/` exists but `.mam/` or `.mam-{scope}/` does not. The user is migrating from team-based to session-based workflow.

**Steps:**
- Rename `.mama/` → `.mam/` (or `.mama-{scope}/` → `.mam-{scope}/`)
- Use `git mv` if the project is a git repository
- Update the version reference in `architect_state.md` from `MAMA Version` to `MAM Version`
- **Keep `implementor_state.md`** — in MAM, the user runs the Implementor session directly, but this document is still valuable as a knowledge reference. The updated `/mam:impl-begin` checks for it and reads it at sprint start.
- Proceed to the 2.0.0 transition for any remaining steps

---

#### Transition: pre-2.0.0 → 2.0.0

**Conditions**: No `.mam*/` directory exists, OR `architect_state.md` has no version stamp or version < 2.0.0.

**Step A — Create state directory** (if not exists):
- Determine scope: ask the user if this is a multi-product project needing a scope, or use `.mam/` for single-product
- Create `.mam/` or `.mam-{scope}/`
- Initialize `sprint_log.md` (empty or bootstrapped from existing artifacts)

**Step B — Migrate sprint artifacts to hierarchical layout**:
- Scan `docs/` for flat sprint artifacts matching old patterns:
  - `docs/implementation_plan_sprint*.md`
  - `docs/implementor_brief_sprint*.md`
  - `docs/implementation_log_sprint*.md`
- For each sprint number found:
  - Create `docs/sprint/{N}/` (or `docs/{scope}/sprint/{N}/`)
  - Move `docs/implementation_plan_sprint{N}.md` → `docs/sprint/{N}/implementation_plan.md`
  - Move `docs/implementor_brief_sprint{N}.md` → `docs/sprint/{N}/implementor_brief.md`
  - Move `docs/implementation_log_sprint{N}.md` → `docs/sprint/{N}/implementation_log.md`
- Use `git mv` if the project is a git repository (preserves history)
- If no flat artifacts exist, skip this step

**Step C — Bootstrap architect_state.md**:
- If `architect_state.md` doesn't exist, create it by inferring from available artifacts:
  - Read existing implementation logs and plans to reconstruct sprint history
  - Read `CLAUDE.md` for project context
  - Read `docs/roadmap.md` if it exists
  - Build the sprint history section from what's available
  - Set `MAM Version: 2.0.0`
  - Set current status based on latest sprint state
- If `architect_state.md` exists but has no version stamp, add `MAM Version: 2.0.0`
- Present the bootstrapped state to the user for review and correction before writing

**Step D — Update CLAUDE.md references** (if needed):
- If `CLAUDE.md` references old flat artifact paths, update them to the new hierarchical pattern
- If `CLAUDE.md` tracks sprint state that now lives in `architect_state.md`, note the duplication but don't remove it (the user may want to keep both during transition)

---

#### Transition: pre-3.0.0 → 3.0.0 — Crossover via the Bus

**Conditions**: Apply this transition for any project whose `architect_state.md` shows version < 3.0.0 (or whose mental model predates the bus). This is a **methodology shift, not a state migration** — there are no on-disk changes required, but the agent's behavior should re-orient.

**What changed.** PDT and MAM used to communicate through discrete files in `docs/crossover/` (`commission_NNN_request.md`, `consult_NNN_request.md`, `debrief_NNN.md`), with the user as the manual courier between sessions. Starting in v3.0.0, that crossover happens over the **bus** plugin — a Channels-based MCP server that lets sessions message each other directly.

**What still works.**
- Existing flat crossover files remain valid history — readable, citable, part of the project's record. Don't delete or migrate them unless the user explicitly asks.
- The conceptual structure — commissions, consults, debriefs — is unchanged.

**What's different now.**
- Sending: `/mam:consult-pdt`, `/mam:debrief-pdt`, and `/mam:commission-complete` now call `peer_send(to='pdt', mode='consult', ...)` instead of writing files
- Receiving: when PDT sends a commission, you receive a `<channel from='pdt' mode='consult'>` notification automatically — no polling for files in `docs/crossover/`
- Storage: new crossover lives in **thread directories** at `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md` (one directory per ongoing thread, sequentially numbered turns)
- Threading: each conversation has a sender-declared kebab-case `thread_id` (e.g. `consult-013-pref-storage-shape`); responses go on the same thread
- Identity: you're addressable on the bus by your registered session name — set via `/mam:session set <name>` (typically `arch` or similar)

**Action items for the user.**
1. Install and enable the bus plugin if not already: `mcc bus setup` in this project's directory
2. Register the Architect session's identity: `/mam:session set arch`
3. The Implementor session, when running, should also register: `/mam:session set impl`
4. Verify PDT's session has registered an identity too (typically `design`) — `peer_list` will show registered identities
5. Note: Channels are in research preview — Claude Code must be launched with `--dangerously-load-development-channels plugin:bus@methodical-cc` for the bus to function

**Reorientation cue for you (the agent).**
- If your `architect_state.md` or `sprint_log.md` references the file-based pattern (e.g., notes about awaiting `consult_NNN_response.md`), that's legacy context. Your current behavior follows the bus protocol. When you next need to consult PDT, use `peer_send` rather than writing a crossover file directly.
- If you find yourself about to write a `consult_NNN_request.md` file: stop. Use the bus. Old files stay where they are; new ones go through `peer_send`.
- The `bus-protocol` skill (in the bus plugin) covers the full protocol. Read it if you need the full reference.

**Step — Update version stamp**:
- Update `architect_state.md` to reflect `MAM Version: 3.0.0`

---

*Future transitions will be added here as the methodology evolves.*

---

### 3. Present Summary

After applying transitions:
- List what was migrated
- List what was created
- List what was skipped (already current)
- Show the current version stamp
- Note any manual follow-up needed (e.g., "review the bootstrapped architect_state.md and flesh out any missing context")

## Important Notes

- **Never delete original files without moving them first.** Use `git mv` when possible.
- **Always confirm destructive operations** with the user before proceeding.
- **The bootstrapped architect_state.md is a starting point** — it will be incomplete. The Architect should flesh it out during the next `arch-resume`.
- **This command is safe to run multiple times.** It checks what's already done and skips completed transitions.

## Begin

Detect the current version, determine what transitions are needed, and walk through them with the user.

$ARGUMENTS
