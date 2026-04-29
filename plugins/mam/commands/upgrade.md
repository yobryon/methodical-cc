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
- Check for `.mam/` or `.mam-{scope}/` directories (legacy v2.x location)
- Check for `.mcc/` or `.mcc-{scope}/` directories (current v3+ location)
- If found, read `architect_state.md` and look for a `MAM Version:` line
- If no state directory exists, the project is **pre-2.0.0**

Record the detected version. If no version is found, treat it as `0.0.0` (pre-versioning).

Also check: does the user want to establish a scope? If they're in a multi-product setup but don't have scoped directories yet, ask.

### 2. Apply Transitions

Apply each transition in order, skipping any that are already complete:

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

#### Transition: pre-3.0.0 → 3.0.0 — `.mcc/` unification + team-based bus

**Conditions**: Apply this transition if any of the legacy state directories exist (`.mam/`, `.mama/`, `.pdt/`, or scoped equivalents like `.mam-backend/`), OR `architect_state.md` shows version < 3.0.0.

**What changed in v3.0.0.**

1. **State directories unified to `.mcc/`.** All operational state — sessions registry, architect_state.md, sprint_log.md, implementor_state.md — now lives in a single `.mcc/` directory (or `.mcc-{scope}/` for scoped projects). Previously this was split across `.mam/`, `.mama/`, `.pdt/`. The unified layout is cleaner and matches `.mcc/bus/` (which has been there from the start).

2. **Crossover via the bus.** PDT and MAM used to communicate through discrete files in `docs/crossover/` (`commission_NNN_request.md`, etc.) with the user as manual courier. Starting in v3.0.0, that crossover happens via the bus plugin — built on Claude Code's agent-team protocol. Sessions in a project join a shared team and message each other via `SendMessage`. The framing message goes through the team mailbox; consult artifacts still live in `docs/crossover/{thread_id}/` (now organized into thread directories).

**What still works.**
- Existing flat crossover files (`commission_NNN_request.md`, etc.) remain valid history — readable, citable, part of the project's record. Don't delete unless the user explicitly asks.
- The conceptual structure — commissions, consults, debriefs — is unchanged.

**Step A — Migrate state directory** (if not already done):
- Detect the existing state directory: `.mam/`, `.mama/`, `.pdt/`, or scoped variants like `.mam-backend/`
- Determine target name:
  - `.mam/` or `.mama/` or `.pdt/` → `.mcc/`
  - `.mam-{scope}/` or `.mama-{scope}/` or `.pdt-{scope}/` → `.mcc-{scope}/`
- Move all files inside the legacy dir into the new `.mcc[-scope]/` dir using `git mv` (preserves history if it's a git repo)
- After moving, the legacy directory should be empty — remove it (the user can verify with `git status` before committing)
- If multiple legacy directories exist (e.g., both `.mam/` and `.mama/`), ask the user which is current — this is unusual but possible if the project changed methodologies. Migrate the active one; let the user decide what to do with the other.

**Step B — Update version stamp**:
- Update `architect_state.md` (now in `.mcc/`) to reflect `MAM Version: 3.0.0`

**Step C — Bus methodology brief** (no on-disk migration; the agent re-orients its mental model):

The methodology now uses the bus for cross-session communication:
- Sending: `/mam:consult-pdt`, `/mam:debrief-pdt`, and `/mam:commission-complete` now compose a structured artifact in `docs/crossover/{thread_id}/` and send a framing `SendMessage(to='pdt', ...)` instead of writing courier files
- Receiving: when PDT sends a commission, you receive it as a turn (the harness polls your team mailbox automatically)
- Storage: new crossover lives in **thread directories** at `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md`
- Threading: each conversation has a sender-declared kebab-case `thread_id`
- Identity: you're addressable on the bus by your registered session name — set via `/mam:session set <name>` or `mcc create <name>`

**Action items for the user.**
1. The bus plugin should be enabled: `mcc team setup` (or any `mcc <name>` does it implicitly)
2. Register the Architect session's identity: `/mam:session set arch` (if not already done)
3. The Implementor session, when running, should also register: `/mam:session set impl`
4. Verify PDT's session has registered (typically `design`) — `mcc team status` from the shell shows registered members

**Reorientation cue for you (the agent).**
- If your `architect_state.md` or `sprint_log.md` references the file-based courier pattern (e.g., notes about awaiting `consult_NNN_response.md`), that's legacy context. Your current behavior follows the bus protocol. When you next need to consult PDT, use `SendMessage` plus a Write to `docs/crossover/{thread_id}/...` rather than writing a flat crossover file.
- If you find yourself about to write a `consult_NNN_request.md` file: stop. Use the bus. Old files stay where they are; new ones go through `SendMessage` + thread-organized artifacts.
- The `bus-protocol` skill (in the bus plugin) covers the full protocol. Read it if you need the full reference.

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
