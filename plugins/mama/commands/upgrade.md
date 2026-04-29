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

#### Transition: pre-3.0.0 → 3.0.0 — `.mcc/` unification + team-based bus + Implementor as user-launched

**Conditions**: Apply this transition if any of the legacy state directories exist (`.mam/`, `.mama/`, `.pdt/`, or scoped equivalents like `.mama-backend/`), OR `architect_state.md` shows version < 3.0.0.

**What changed in v3.0.0.**

1. **State directories unified to `.mcc/`.** All operational state — sessions registry, architect_state.md, sprint_log.md, implementor_state.md — now lives in a single `.mcc/` directory (or `.mcc-{scope}/` for scoped projects). The unified layout matches `.mcc/bus/` (which has been there from the start).

2. **Crossover via the bus.** PDT and MAMA used to communicate through discrete files in `docs/crossover/` with the user as manual courier. Starting in v3.0.0, that crossover happens via the bus plugin — built on Claude Code's agent-team protocol. Sessions in a project join a shared team and message each other via `SendMessage`.

3. **Implementor is now user-launched, not Architect-spawned.** Claude Code's flat-roster team protocol prevents teammates from spawning teammates, so the Architect no longer calls `TeamCreate` or spawns the Implementor via the Agent tool. The user launches the Implementor as a separate session via `mcc create impl --persona mama:implementor`, then enters it via `mcc impl`. The Architect uses `SendMessage` to send the kickoff once the Implementor is online.

4. **UX Designer falls back to subagent semantics.** Same constraint — UX is now a one-shot subagent (Agent tool without `team_name`) by default. For long-running UX, the user can launch a separate `design-ux` session.

**What still works.**
- Existing flat crossover files remain valid history. Don't delete unless the user explicitly asks.
- The conceptual structure — commissions, consults, debriefs — is unchanged.
- `arch-sprint-start` still writes the implementation plan and kickoff message; just doesn't spawn the Implementor anymore.

**Step A — Migrate state directory** (if not already done):
- Detect the existing state directory: `.mam/`, `.mama/`, `.pdt/`, or scoped variants
- Determine target name:
  - `.mam/` or `.mama/` or `.pdt/` → `.mcc/`
  - `.mam-{scope}/` or `.mama-{scope}/` or `.pdt-{scope}/` → `.mcc-{scope}/`
- Move all files inside the legacy dir into the new `.mcc[-scope]/` dir using `git mv` (preserves history)
- After moving, the legacy directory should be empty — remove it
- If multiple legacy directories exist, ask the user which is current and migrate that one

**Step B — Update version stamp**:
- Update `architect_state.md` (now in `.mcc/`) to reflect `MAMA Version: 3.0.0`

**Step C — Bus methodology brief** (no on-disk migration; the agent re-orients):

The methodology now uses the bus for cross-session communication:
- Sending: `/mama:consult-pdt`, `/mama:debrief-pdt`, and `/mama:commission-complete` now compose a structured artifact in `docs/crossover/{thread_id}/` and send a framing `SendMessage(to='pdt', ...)` instead of writing courier files
- Receiving: messages from teammates arrive as turns automatically (the harness polls your team mailbox)
- Storage: new crossover lives in **thread directories** at `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md`
- Identity: you're addressable on the bus by your registered session name — set via `/mama:session set <name>` or `mcc create <name>`

**Action items for the user.**
1. The bus plugin should be enabled: `mcc team setup` (or any `mcc <name>` does it implicitly)
2. Register the Architect session's identity: `/mama:session set arch` (if not already done)
3. For sprint work: launch the Implementor via `mcc create impl --persona mama:implementor` in a new terminal, then `mcc impl` to enter it
4. Verify PDT's session has registered (typically `design`) — `mcc team status` from the shell shows registered members

**Reorientation cue for you (the agent).**
- If your `architect_state.md` or `sprint_log.md` references the file-based courier pattern, that's legacy context. Your current behavior follows the bus protocol.
- If you find yourself about to call `TeamCreate` or `Agent(team_name=..., subagent_type=implementor, ...)`: stop. The team already exists (mcc maintains it). The user starts the Implementor session via `mcc create impl`.
- The `bus-protocol` skill (in the bus plugin) covers the full protocol.

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
