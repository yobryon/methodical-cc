---
description: Upgrade a project's MAMA artifacts to the current plugin version. Migrates state directories, sprint artifact layout, agent configurations, organizational patterns, and methodology shifts. Safe to run multiple times — skips already-completed transitions.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# MAMA Upgrade

You are the **Architect Agent**. This command upgrades a project's MAMA artifacts to match the current plugin version (3.0.0).

Upgrades are **cumulative** — if a project is several versions behind, all intermediate transitions are applied in order. Each transition is **idempotent** — already-completed steps are skipped.

## Your Task

### 1. Detect Current Version

Look for the MAMA state directory:
- Check for `.mama/` or `.mama-{scope}/` directories
- If found, read `architect_state.md` and look for a `MAMA Version:` line
- If no state directory exists, check for `.mam/` or `.mam-{scope}/` directories (MAM → MAMA migration)
- If neither exists, the project is **pre-2.0.0**

Record the detected version. If no version is found, treat it as `0.0.0` (pre-versioning).

Also check: does the user want to establish a scope? If they're in a multi-product setup but don't have scoped directories yet, ask.

### 2. Apply Transitions

Apply each transition in order, skipping any that are already complete:

---

#### Transition: MAM → MAMA

**Conditions**: `.mam/` or `.mam-{scope}/` exists but `.mama/` or `.mama-{scope}/` does not. The user is migrating from session-based to team-based workflow.

**Before migrating**, check whether `implementor_state.md` already exists in the `.mam*/` directory. If it does not, suggest the user run `/mam:impl-export` first to capture their accumulated implementation knowledge — this becomes the Implementor teammate's starting context in MAMA. If they want to skip this, proceed without it.

**Steps:**
- Rename `.mam/` → `.mama/` (or `.mam-{scope}/` → `.mama-{scope}/`)
- Use `git mv` if the project is a git repository
- If `implementor_state.md` doesn't exist, create an empty one in the state directory
- Update the version reference in `architect_state.md` from `MAM Version` to `MAMA Version`
- Proceed to the 2.0.0 transition for any remaining steps

---

#### Transition: pre-2.0.0 → 2.0.0

**Conditions**: No `.mama*/` directory exists, OR `architect_state.md` has no version stamp or version < 2.0.0.

**Step A — Create state directory** (if not exists):
- Determine scope: ask the user if this is a multi-product project needing a scope, or use `.mama/` for single-product
- Create `.mama/` or `.mama-{scope}/`
- Initialize `sprint_log.md` (empty or bootstrapped from existing artifacts)
- Create empty `implementor_state.md`

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
  - Set `MAMA Version: 2.0.0`
  - Set current status based on latest sprint state
- If `architect_state.md` exists but has no version stamp, add `MAMA Version: 2.0.0`
- Present the bootstrapped state to the user for review and correction before writing

**Step D — Update CLAUDE.md references** (if needed):
- If `CLAUDE.md` references old flat artifact paths, update them to the new hierarchical pattern
- If `CLAUDE.md` tracks sprint state that now lives in `architect_state.md`, note the duplication but don't remove it (the user may want to keep both during transition)

---

#### Transition: pre-3.0.0 → 3.0.0 — Crossover via the Bus

**Conditions**: Apply this transition for any project whose `architect_state.md` shows version < 3.0.0 (or whose mental model predates the bus). This is a **methodology shift, not a state migration** — there are no on-disk changes required, but the agent's behavior should re-orient.

**What changed.** PDT and MAMA used to communicate through discrete files in `docs/crossover/` (`commission_NNN_request.md`, `consult_NNN_request.md`, `debrief_NNN.md`), with the user as the manual courier between sessions. Starting in v3.0.0, that crossover happens over the **bus** plugin — a Channels-based MCP server that lets sessions message each other directly.

**What still works.**
- Existing flat crossover files remain valid history — readable, citable, part of the project's record. Don't delete or migrate them unless the user explicitly asks.
- The conceptual structure — commissions, consults, debriefs — is unchanged.

**What's different now.**
- Sending: `/mama:consult-pdt`, `/mama:debrief-pdt`, and `/mama:commission-complete` now call `peer_send(to='pdt', mode='consult', ...)` instead of writing files
- Receiving: when PDT sends a commission, you receive a `<channel from='pdt' mode='consult'>` notification automatically — no polling for files in `docs/crossover/`
- Storage: new crossover lives in **thread directories** at `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md` (one directory per ongoing thread, sequentially numbered turns)
- Threading: each conversation has a sender-declared kebab-case `thread_id` (e.g. `consult-013-pref-storage-shape`); responses go on the same thread
- Identity: you're addressable on the bus by your registered session name — set via `/mama:session set <name>` (typically `arch` or similar)

**Action items for the user.**
1. Install and enable the bus plugin if not already: `mcc bus setup` in this project's directory
2. Register the Architect session's identity: `/mama:session set arch`
3. Verify PDT's session has registered an identity too (typically `design`) — `peer_list` will show registered identities
4. Note: Channels are in research preview — Claude Code must be launched with `--dangerously-load-development-channels plugin:bus@methodical-cc` for the bus to function

**Reorientation cue for you (the agent).**
- If your `architect_state.md` or `sprint_log.md` references the file-based pattern (e.g., notes about awaiting `consult_NNN_response.md`), that's legacy context. Your current behavior follows the bus protocol. When you next need to consult PDT, use `peer_send` rather than writing a crossover file directly.
- If you find yourself about to write a `consult_NNN_request.md` file: stop. Use the bus. Old files stay where they are; new ones go through `peer_send`.
- The `bus-protocol` skill (in the bus plugin) covers the full protocol. Read it if you need the full reference.

**Step — Update version stamp**:
- Update `architect_state.md` to reflect `MAMA Version: 3.0.0`

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
- **MAM → MAMA migration**: Consider running `/mam:impl-export` before migrating to capture accumulated implementation knowledge. The Implementor teammate will load this knowledge automatically on sprint start.

## Begin

Detect the current version, determine what transitions are needed, and walk through them with the user.

$ARGUMENTS
