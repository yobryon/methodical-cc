---
description: Upgrade a project's MAM artifacts to the current plugin version. Migrates state directories, sprint artifact layout, and organizational patterns. Safe to run multiple times — skips already-completed transitions.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# MAM Upgrade

You are the **Architect Agent**. This command upgrades a project's MAM artifacts to match the current plugin version (2.0.0).

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

*Future transitions (2.0.0 → 2.1.0, etc.) will be added here as the methodology evolves.*

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
