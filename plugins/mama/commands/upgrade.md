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

#### Transition: pre-3.1.0 → 3.1.0 — codification gates, mama:reflect, slim kickoffs

**Conditions**: Apply this transition for any project that ran on mama < 3.1.0. There is no on-disk migration — this transition is a **methodology brief** about the codification-and-reflection refinements, plus an explicit "behaviors to unlearn" pass.

**What changed in v3.1.0.**

1. **Codification gates added to `pattern-add`.** CLAUDE.md additions now go through four explicit gates: (a) is the rule already enforced by a test/type/lint? (b) does it duplicate sprint_log / decisions_log / concept_backlog content? (c) would a fresh session six sprints from now actively *miss* something without it? (d) is this sprint-specific lesson rather than evergreen rule? **Default answer is no.**
2. **Style guide for codified bullets.** Lead with the rule. Optional second line: why or where (not both). Cap at 3 lines. No diagnostic backstory. Group by topic.
3. **`mama:reflect` ritual** added — periodic memory audit (CLAUDE.md, architect_state, concept_backlog, decisions_log) with "still load-bearing?" questions, plus open methodology reflection and optional feedback artifact. Recommended cadence: every 5–10 sprints.
4. **Slim sprint kickoffs.** Target ~100–150 words sprint-specific content + a small standing protocol pulse. The plan is the source of truth; the persona is loaded; the kickoff doesn't restate them.
5. **`TaskCreate` removed from arch-side ritual.** Implementation log's Phase Progress table is canonical sprint progress. Impl manages own todos; arch reads the log.

**Behaviors to unlearn (you've probably built muscle memory on these).**

If this project ran for many sprints under earlier mama versions, you almost certainly carry patterns that are now anti-patterns. Read these once, recalibrate:

- **Don't reflexively add a Key Learning to CLAUDE.md every sprint.** The four gates apply. Default-no. If a candidate fails any gate (test enforces it / duplicates a sprint_log entry / wouldn't be missed in 6 sprints / is sprint-specific narrative), don't write it. Most candidates fail.
- **Don't restate the implementation log retrospective in CLAUDE.md's Sprint Status block** (or anywhere in CLAUDE.md). The log is the durable record. CLAUDE.md is forward-facing rules only. If you find a "Sprint X shipped <bullets>" section in CLAUDE.md from earlier work, prune it.
- **Don't write Key Learnings into both CLAUDE.md and architect_state.md.** Memorialization ownership is now explicit (see arch-sprint-complete after this update lands): CLAUDE.md = arch owns evergreen rules; architect_state = arch's running project knowledge; impl_state = impl's tacit knowledge; sprint_log = chronicle. One canonical home per content type.
- **Don't treat sprint-complete as purely additive.** Older guidance was "Apply Implemented Deltas, Capture Discoveries, Update Success Criteria" — all additive. The new posture also asks: "what could shrink because of what shipped?" Even before per-sprint prune-prompts land, default to that posture.
- **Don't fight the harness's TaskCreate reminder by overriding it.** `TaskCreate`/`TaskUpdate` are team-coordination tools with legitimate uses (parallel impls, cross-session handoffs, dependency tracking). Use them when the work shape calls for them; ignore the reminder when it doesn't. The decision rule: *does this work need cross-teammate or cross-session task coordination beyond what the implementation log provides?*
- **Don't compose sprint kickoffs as 600-word recaps of the persona + plan + CLAUDE.md.** Trust the loaded context. ~100–150 words sprint-specific + the standing protocol pulse is the target shape.

**Action items for the user.**

- No code action required. The agent re-reads this transition section, recalibrates, and applies the new defaults going forward.
- Optional: run `/mama:reflect` at the next sprint close as a one-time deep-clean pass over accumulated memory surfaces. The audit catches what muscle-memory drift has already accreted.

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
