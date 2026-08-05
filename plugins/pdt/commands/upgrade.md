---
description: Brief the Design Partner on methodology changes when upgrading to a new PDT version. Currently covers the pre-2.0.0 → 2.0.0 transition (.mcc/ unification + bus-based crossover with MAM/MAMA).
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# PDT Upgrade

You are the **Design Partner**. This command briefs you on methodology changes that came with new PDT versions, so you (and any accumulated state in this project) can re-orient your thinking accordingly.

PDT has minimal versioned state on disk — the only structural artifact is the sessions registry. This command's main job is to **update your mental model** of how PDT works given changes since the last time you (or a prior session) operated in this project, and to migrate the sessions registry if needed.

Upgrades are **cumulative**: if you're several versions behind, work through each transition in order.

## Your Task

### 1. Determine Current Version

Look for `.pdt/sessions` (legacy v1.x location) or `.mcc/sessions` (current v2+ location). Ask the user what PDT version they were last using on this project (if known). Default to "pre-2.0.0" if unsure.

### 2. Apply Transitions

Walk through each applicable transition with the user, then internalize it.

---

#### Transition: pre-2.0.0 → 2.0.0 — `.mcc/` unification + team-based bus

**Conditions**: Apply this transition if `.pdt/` exists (legacy state dir), OR if mental model predates the bus.

**What changed.**

1. **Sessions registry moved.** PDT's sessions registry was at `.pdt/sessions`; it's now at `.mcc/sessions` (alongside MAM/MAMA's state, all unified under `.mcc/`).

2. **Crossover via the bus.** PDT and MAM/MAMA used to communicate through discrete files in `docs/crossover/` (`commission_NNN_request.md`, `consult_NNN_request.md`, `debrief_NNN.md`), with the user as manual courier between sessions. Starting in v2.0.0, that crossover happens via the bus plugin — built on Claude Code's agent-team protocol. Sessions in a project join a shared team and message each other via `SendMessage`.

**What still works.**
- Existing flat crossover files (`commission_NNN_*.md`, `consult_NNN_*.md`, `debrief_NNN.md`) remain valid history. Don't delete unless the user explicitly asks.
- The conceptual structure — commissions, consults, debriefs — is unchanged.

**Step A — Migrate sessions registry** (if needed):
- If `.pdt/sessions` exists, move it to `.mcc/sessions` (use `git mv` if the project is a git repo, plain `mv` otherwise)
- Create `.mcc/` if it doesn't exist
- After moving, remove the now-empty `.pdt/` directory

**Step B — Bus methodology brief** (no on-disk migration; the agent re-orients):

- Sending: `/pdt:commission` now writes a commission artifact at `docs/crossover/{thread_id}/001-pdt-commission.md` and sends a framing `SendMessage(to='arch', ...)`. Same for consult responses and debrief acknowledgments.
- Receiving: when the Architect sends a commission, consult, or debrief, you receive it as a turn (the harness polls your team mailbox automatically — no polling for files).
- Storage: new crossover lives in **thread directories** at `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md`
- Threading: each conversation has a sender-declared kebab-case `thread_id`
- Identity: you're addressable on the bus by your registered session name — typically `design` or `pdt`

**Action items for the user.**
1. Install the bus plugin if not already installed (`claude plugin install bus@methodical-cc`)
2. Bus is enabled per-project via `mcc team setup` (or any `mcc <name>` does it implicitly)
3. Register PDT's session identity: `/pdt:session set design` (or another name they prefer)
4. Verify the Architect's session has registered (typically `arch`) — `mcc team status` from the shell shows registered members

**Reorientation cue for you (the agent).**
- If your `concept_backlog.md` or `decisions_log.md` references the file-based pattern (e.g., notes about waiting for `commission_NNN_response.md`), that's legacy context. The current behavior follows the bus protocol.
- If you find yourself about to write a `consult_NNN_request.md` or `commission_NNN_request.md` file: stop. Use the bus. Old files stay where they are; new ones go through `SendMessage` + thread-organized artifacts.
- The `bus-protocol` skill (in the bus plugin) covers the full protocol. Read it if you need the full reference.

**Verify the bus is working.**
- After setup, the SessionStart context should include a `=== METHODICAL-CC BUS ===` block showing your identity and team membership
- If it shows `anonymous` or no team block, the launch flags weren't set — the user should resume sessions via `mcc <name>` rather than plain `claude -r <id>`

---

*Future transitions will be added here as the methodology evolves.*

---

### 3. Present Summary

After working through applicable transitions:
- Confirm with the user which transitions applied
- Note any action items still pending (e.g., "you still need to register your session identity")
- Offer to proceed with `/pdt:resume` next so you can re-establish full project context with the new methodology in mind

## Begin

Discuss the project's PDT version history with the user, then walk through applicable transitions.

$ARGUMENTS
