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

#### Transition: pre-3.3.0 → 3.3.0 — shrink counterweight, move-not-strike, cadence prompt, plan-component check

**Conditions**: Apply this transition for any project that ran on mama < 3.3.0. Methodology brief; no on-disk migration.

**What changed in v3.3.0.**

1. **Shrink-counterweight prompt at `arch-sprint-complete`.** The reconciliation flow now pairs every additive verb (apply deltas, capture discoveries, update success criteria) with an explicit **What Shrank?** question — for each delta merged or criterion updated, ask whether the sprint rendered any rule, debt entry, doc section, or pattern obsolete. Default is *additive*; the prompt counters it.
2. **Tech-debt MOVE-not-strike rule.** When tech-debt items resolve, the reconciliation moves the item to `sprint_log.md` under the resolving sprint and **deletes** the entry from CLAUDE.md. Strikethrough is no longer a terminal state — it auto-loaded into every future session as archaeology.
3. **Reflection cadence prompt at `arch-sprint-complete`.** Architects in long-running projects are demonstrably bad at self-prompting `/mama:reflect`. `arch-sprint-complete` now reads sprints-since-last-reflection (from `architect_state.md` or by detecting the most recent reflection artifact) and emits a graduated prompt at ≥5 (soft), ≥8 (louder), ≥10 (overdue). The architect can defer; making the question visible every sprint is what closes the cadence loop.
4. **Plan-component reality check at `arch-sprint-prep`.** Before kickoff goes out, the architect grep-verifies filenames, symbols, and components named in the plan. Mismatches mean the plan is wrong about its own scope; new components get marked as such so impl knows they're expected to be absent.

**Behaviors to unlearn (you've probably built muscle memory on these).**

- **Don't strikethrough resolved tech debt in CLAUDE.md.** The new rule is *move* the entry to `sprint_log.md` under the resolving sprint with provenance (e.g., `Resolved S{N}: {original} → {resolution}`) and *delete* from CLAUDE.md. If you find prior strikethroughs accumulated from earlier sprints, prune them as part of the next reflection — keep the provenance in `sprint_log.md`, remove from CLAUDE.md.
- **Don't wait for the user to invoke `/mama:reflect`.** The cadence prompt fires automatically at sprint-complete now; respect it. If it fires soft and you think the timing is wrong, say so explicitly in your summary — don't silently skip.
- **Don't treat `arch-sprint-complete` as additive-only.** The "Apply Implemented Deltas / Capture Discoveries / Update Success Criteria" verbs all add. The new posture explicitly asks "what shrank?" alongside every addition. If nothing shrank this sprint, say so — make the question visible in your summary.
- **Don't ship plans with un-grep'd component names.** If your plan names files, symbols, or function references, verify them before kickoff. The "I think this lives in X" assumption costs impl reaction time at sprint open and signals plan sloppiness. New components being created in this sprint are a special case — call them out as new in the plan.
- **Don't bury the prune in the summary.** When you delete tech debt, retire a doc section, or supersede a pattern, surface it in the sprint completion summary. Removals are quiet by default; making them visible is part of the discipline.

**Action items for the user.**

- No code action required. The agent re-reads this transition section, recalibrates, and applies the new defaults going forward.
- Optional: run `/mama:reflect` at the next sprint close — even if cadence isn't due — to do a one-time deep clean of any strikethrough accumulator that's already in `CLAUDE.md`. After this pass, the move-not-strike rule prevents regrowth.

#### Transition: pre-3.4.0 → 3.4.0 — per-sprint counterweights to cadence-based audit (cluster-check, compaction, verification gate, arc-close trigger, methodology-holds registry)

**Conditions**: Apply this transition for any project that ran on mama < 3.4.0. Methodology brief; no on-disk migration (the optional `methodology_holds.md` artifact is opt-in and gets introduced when the project starts accumulating tracked items).

**What changed in v3.4.0.**

3.3.0 added per-sprint counter-additive prompts (shrink question, move-not-strike, cadence ladder, plan-component reality check). 3.4.0 extends the same direction: more of `/mama:reflect`'s cadence-based audit moves into the per-sprint workflow so accumulators get caught the moment they form, not 5–10 sprints later.

1. **Cluster-check sub-prompt at memory-add time (`arch-sprint-complete` Step 2).** Before landing any CLAUDE.md rule, scan for related rules in the same topic. If this would make the topic carry 3+ rules, choose: open a structural-fix backlog item that obviates the cluster, demote the topic to a reference doc with a one-line pointer, or explicitly justify the addition. The four pattern-add gates catch individual rules; this catches the pile.
2. **`architect_state.md` compaction sub-pass (`arch-sprint-complete` Step 5).** When writing the new sprint's state, demote the prior Last Updated paragraph to a one-line band; compress older Sprint History rows to one-line per band or per arc. State-doc carries *current state + active-arc detail*; older detail lives in `sprint_log.md`. Same shape as move-not-strike for CLAUDE.md, applied to state-doc.
3. **Handoff-review verification gate (`arch-sprint-complete` Step 1).** Symmetric to the plan-component reality check at prep time. For each impl decision-note explaining a divergence, walk three lenses: (a) **intent** — does the divergence still satisfy the user's articulated intent, not just the technical constraint? (b) **hypothesis evidence** — for recurring/carryover bug fixes, is the evidence direct or inferred? (c) **felt-state framing** — does status/lifecycle copy match the data model semantics, or does it imply gates the code doesn't enforce? If any lens flags a concern, the sprint isn't ready to close.
4. **Arc-close inflection trigger for `/mama:reflect` (`arch-sprint-complete` Step 7).** Alongside the existing sprint-count cadence ladder, an arc-close at this sprint surfaces a "consider reflecting now, regardless of count" prompt. Arc-close is the natural reflection beat — accumulated lessons are freshest right then.
5. **Optional `methodology_holds.md` registry.** First-class flat-file surface for two kinds of held items: pattern-instance counts approaching rule-of-three promotion, and structural-fix candidates filed in CLAUDE.md rules but not yet scheduled. Walked at `arch-sprint-prep` Step 5 (decide promote/defer/retire per entry); updated at `arch-sprint-complete` Step 5. Opt-in: introduce when accumulation makes it pay.

**Behaviors to unlearn.**

- **Don't wait for `/mama:reflect` to catch CLAUDE.md cluster drift.** The cluster-check now fires at memory-add time. If you're about to add a third rule on the same topic, that's the moment to ask whether a structural fix obviates the cluster — not 5 sprints later.
- **Don't append to `architect_state.md` Sprint History without compacting.** The state-doc grew as append-only in pre-3.4.0 practice. The new posture: every sprint close also compacts (or at least re-evaluates) prior content. Sprint History rows older than the current arc compress to one-line bands; PRIOR-paragraph chains demote to history rows.
- **Don't validate impl decision-notes only against the technical constraint.** The handoff-review verification gate explicitly asks about *user intent*, not just *whether the divergence makes technical sense*. Sound technical rationale can still abandon what the user articulated; the gate catches that gap before sprint-close ceremony fires.
- **Don't defer hypothesis verification to post-fix dogfood.** For fixes to recurring or carryover bugs, ask before designing the fix whether the evidence is direct or inferred. Wrong-cause fixes look identical to right-cause fixes until they ship; 30 minutes of direct evidence is cheaper than a wrong-fix sprint.
- **Don't treat status copy as polish.** Status / lifecycle copy creates felt gates in the user's head. The gate explicitly asks whether copy framing matches data model semantics; a mismatch is a load-bearing audit, not stylistic.
- **Don't wait for the count ladder when an arc closes.** Arc-close is its own reflection beat. The methodology now blesses it explicitly.
- **Don't let pattern-instance counts or structural-fix candidates scatter across state docs.** If accumulation has started, introduce `methodology_holds.md` (or a labeled section in `architect_state.md`); walk it at sprint-prep, update it at sprint-complete.

**Action items for the user.**

- No code action required. The agent re-reads this transition section, recalibrates, and applies the new defaults going forward.
- **If the project has accumulated 3+ rules in any one CLAUDE.md topic**: surface the cluster at the next reflection — the cluster-check at memory-add time prevents regrowth, but existing clusters need a one-time pass to either land their structural fix or demote to a reference doc.
- **If `architect_state.md` Sprint History has bands you haven't touched in 5+ sprints**: compact them at the next sprint close. The pre-3.4.0 append-only practice produces archaeology; the new compaction sub-pass prevents recurrence.
- **If you have pattern-instance counts or structural-fix candidates scattered across state docs or rule bodies**: introduce `methodology_holds.md` (see `multi-agent-methodology` skill for the shape). Migrate held items into the table format; clear from their prior homes.

#### Transition: pre-3.5.0 → 3.5.0 — `/mama:reflect --apply` mode (opt-in non-interactive variant)

**Conditions**: Apply this transition for any project that ran on mama < 3.5.0. Methodology brief; no on-disk migration; opt-in feature.

**What changed in v3.5.0.**

`/mama:reflect` now accepts a `--apply` argument. Default behavior (no flag) is unchanged — surface findings, wait for the user per item, *offer* the feedback artifact.

When invoked as `/mama:reflect --apply`:

- Walk all three sections non-interactively.
- Apply mechanical findings as you go: rule prunes, doc compactions, archive moves, demotions, cross-reference adds, methodology-holds updates.
- *Always* produce the feedback artifact at `tmp/mama_reflection_{date}.md`.
- *Surface but do not apply* findings that require net-new design judgment (structural-fix backlog items, methodology-change proposals).
- End with a single consolidated summary: what was applied, what was surfaced for follow-up, where the feedback artifact landed.

The four pattern-add gates, move-not-strike rule, cluster-check, and all other disciplines **still apply** — the flag pre-authorizes the per-item confirmation step, not the discipline. Nothing gets auto-committed to git; the bundle of edits warrants human eyeball before landing.

**Behaviors to unlearn.**

- Nothing. `--apply` is purely additive. The default interactive behavior is unchanged. Architects who prefer per-item interaction don't need to do anything.

**Action items for the user.**

- No code action required.
- If you frequently invoke reflect by typing "go ahead and apply all your findings and write the feedback document" (or equivalent), you can now use `/mama:reflect --apply` to encapsulate that pattern.

#### Transition: pre-3.6.0 → 3.6.0 — close the detect→schedule loop (registry forcing function, plan-outcome reachability, memory-discipline sharpening)

**Conditions**: Apply this transition for any project that ran on mama < 3.6.0. Methodology brief; no on-disk migration (the `methodology_holds.md` registry gains a third section, applied next time you write to it).

**What changed in v3.6.0.**

3.4.0 gave the `methodology_holds.md` registry good *detection*. Projects then reported, across many reflections, that detection without *scheduling* just produces a tidy list of debt that never gets paid — feature work correctly outranks hygiene every sprint, so a structural-fix candidate flagged two reflections running still never gets a slot. 3.6.0 closes that loop and sharpens the per-sprint memory passes.

1. **Registry forcing function (`arch-sprint-prep` Step 5).** The Methodology-Holds Walk now *forces decisions* instead of reviewing: stale items (carried 3 sprints / 3 reflects) get a schedule-or-justify binary; 3+ open structural-fix candidates surface a **hygiene sprint as a first-class proposal**; cross-lane items get commissioned via the bus rather than re-flagged in your own state.
2. **Reflection-findings carry-forward.** The registry gains a third section, **Reflection follow-ups**. `/mama:reflect` writes its "surfaced for follow-up" findings there (with date); the sprint-prep walk carries them with the same forcing function. This fixes reflection outputs rotting between reflections.
3. **Plan-outcome reachability check (`arch-sprint-prep`).** Symmetric partner to the plan-component reality check: for each success criterion / verification gate, confirm every step to *reach* it is in-scope or already-shipped. A gate that depends on a step the plan defers is a latent inconsistency — reframe it. Catches the "plan promises a result it can't reach with what it's holding" error that hides behind the component check passing.
4. **arch-sprint-complete memory-discipline sharpening.** (a) Current Status / Next Steps blocks must describe the *just-closed* sprint — rewrite in place (they go stale-and-misleading, not just stale); (b) write the new Sprint History band tight, and tighten the most-recent band when compacting, so dense-band gravity doesn't propagate; (c) the cluster-check is now section-budget-aware (catches the already-huge section, not just the rule that clusters); (d) Claude Code auto-memory (`MEMORY.md` + per-fact files) joins the memorialization-ownership table (arch-owned, single-writer-at-close, compaction is arch's job).

**Behaviors to unlearn.**

- **Don't re-surface a structural-fix candidate every reflection without scheduling it.** The forcing function now makes "carried 3 reflects" a schedule-or-justify decision, and accumulation a hygiene-sprint proposal. Re-flagging without acting is the failure mode the loop closes.
- **Don't let a `/mama:reflect` "surfaced for follow-up" finding live only in the summary.** Write it to the registry's Reflection follow-ups section; otherwise it evaporates and gets rediscovered (larger) next reflection.
- **Don't trust a plan because its nouns check out.** Component-existence and outcome-reachability are separate questions; a plan can be component-correct and outcome-incoherent at once. Read each gate against what the plan defers.
- **Don't append a fresh status block above a stale one.** Current Status / Next Steps get rewritten in place — move-not-strike applies to your own running-status prose, not just tech debt.
- **Don't add the Nth rule to an already-large CLAUDE.md section just because the rule itself passes the gate.** If the destination section is over budget (~40 lines / ~6 rules), the move is demote-to-reference-doc, filed as a structural-fix candidate.
- **Don't co-write the Claude Code auto-memory surface with impl uncoordinated.** It's arch-owned now, single-writer-at-close, like the other auto-loaded surfaces.

**Action items for the user.**

- No code action required. The registry's third section appears the next time `/mama:reflect` or `arch-sprint-complete` writes to it.
- **If you have structural-fix candidates that have sat across multiple reflections** (the schema-form cluster, the Cytoscape pile, etc.): the next `arch-sprint-prep` will now force a schedule-or-justify on them, and propose a hygiene sprint if 3+ are open. Expect it to surface that debt — that's the point.

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
