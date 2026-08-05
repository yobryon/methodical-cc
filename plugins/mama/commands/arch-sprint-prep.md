---
description: Begin planning the next sprint. Reviews current state, proposes initial scope, and prepares for the feedback cycle.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Sprint Planning - Initial Proposal

You are the **Architect Agent**. It's time to plan the next sprint.

## Context

This command kicks off the sprint planning cycle:
1. **You propose** initial scope (this step)
2. **User provides** feedback, new ideas, reflections via `/mama:arch-discuss`
3. **You process** feedback, create deltas, discuss
4. **Together you converge** on final scope
5. **You lock scope** via `/mama:arch-sprint-start`

## Your Task

### 1. Determine Sprint Number and Paths

- Read your `.mcc*/architect_state.md` for sprint history
- Determine the next sprint number
- Determine artifact paths: `docs/sprint/X/` (or `docs/{scope}/sprint/X/` for scoped instances)

### 2. Assess Current State

- Review the roadmap
- Review product documentation
- Check what was accomplished in previous sprints (read `.mcc*/sprint_log.md`)
- Understand where we are

### 3. Identify What's Next

- What does the roadmap suggest for this sprint?
- What's the logical next step based on current state?
- Are there any urgent items or blockers to address?
- Check `docs/crossover/` for open PDT commissions -- if PDT has commissioned validation, prototyping, or investigation work, consider whether to fold it into this sprint or schedule it separately

### 4. Propose Initial Scope

- Define a coherent sprint goal
- List the key deliverables
- Estimate complexity and effort
- Note any dependencies or prerequisites
- Flag any open questions that might affect scope

### 5. Methodology-Holds Walk

**Before locking the proposal**, walk `.mcc*/methodology_holds.md` (if the project uses it; see the `multi-agent-methodology` skill for the artifact's shape). The registry carries three kinds of held items: pattern-instance counts approaching rule-of-three promotion, structural-fix candidates flagged in CLAUDE.md rules but not yet scheduled, and reflection follow-ups (findings a `/mama:reflect` surfaced but didn't apply).

For each entry:

- **Pattern-instance counts at threshold (typically 3)**: this is the moment to evaluate promotion to CLAUDE.md against the four pattern-add gates. Promote, defer to a later reflect with rationale, or retire if the pattern no longer holds.
- **Structural-fix candidates whose trigger condition now fires**: lift to this sprint's scope, re-justify as carried (with reason — what's gating it), or retire as no-longer-relevant.
- **Reflection follow-ups**: findings written here by `/mama:reflect` (the surfaced-not-applied items). Each carries the reflection it came from and an age. Treat the same as structural-fix candidates — schedule, re-justify, or retire.

**The registry detects; this step forces.** The registry is good at remembering and bad at scheduling — left alone, structural-fix candidates and reflection follow-ups accumulate into a tidy list of debt that never gets paid, because feature work (correctly) outranks hygiene every single sprint. Detection without scheduling is the failure mode the registry exists to prevent, and it only works if this walk *forces a decision*:

- **Forced binary on stale items.** Any structural-fix candidate or reflection follow-up carried **3 sprints (or 3 reflects)** without movement gets a forced choice: schedule it this sprint, OR explicitly record why it's still being carried (the concrete gate — not "didn't get to it"). No silent perpetual deferral.
- **Hygiene-sprint trigger.** When **3+ structural-fix candidates / follow-ups** are open simultaneously, surface a **hygiene sprint as a first-class proposal** — not a footnote, not "maybe next time." The accumulation is itself the signal; the methodology schedules the hygiene work because the architect reliably (and correctly) won't rank it above a real user feature.
- **Cross-lane items get commissioned, not re-flagged.** If a held item is owned by another teammate (e.g. a PDT design-guide promotion), don't just re-flag it in your own state every cycle — **commission it now** via the bus (a `SendMessage` to the owning teammate). Re-surfacing a cross-lane item without handing it off is how it sits for many reflects with no motion.

Items earning this sprint's slot get added to the proposed scope before plan is locked. Items being carried get their carry-justification updated in the registry.

If `.mcc*/methodology_holds.md` doesn't exist yet, this step is a no-op for now — but consider whether the project would benefit from introducing it (the artifact pays for itself once pattern-counts, structural-fix candidates, or reflection follow-ups start accumulating across sprints).

### 6. Plan-Component Reality Check

**Before the proposal goes to the user (and well before kickoff goes to impl), verify the plan's named components against the codebase.**

Architect plans regularly cite filenames, symbols, function names, or component locations that don't match reality on disk. Each mismatch costs impl reaction time at sprint open and signals that arch-side planning isn't carrying its weight.

For each filename, symbol, function, or component named in the proposed scope:

- Confirm it exists on disk (`Glob` for paths, `Grep` for symbols).
- If a named element doesn't exist, either:
  - The plan is wrong about its own scope — fix the plan before proceeding, **or**
  - The element is being newly created in this sprint — note this explicitly in the plan ("new file", "new export", etc.) so impl knows it's expected to be absent.

Flag any "I think this lives in X" assumptions. If you're not certain, grep before you commit the plan to text.

This is a discipline pass, not tooling — but if the named-element list is large enough that grepping each by hand is tedious, the friction is itself a signal that the plan may be over-specified.

**Plan-outcome reachability — the symmetric partner.** The component check verifies the plan's *nouns* (the files/symbols exist). It does not verify the plan's *verbs* (the stated outcomes are reachable). A plan can be component-correct and outcome-incoherent at the same time — and the second error hides behind the first passing, because once the nouns all resolve the plan *feels* verified.

For each success criterion / verification gate in the plan, trace the steps required to *reach* it, and confirm every one is either (a) in this sprint's scope, or (b) already shipped:

- If reaching a stated outcome requires a step the plan itself **defers to a later sprint**, that's a latent inconsistency. Reframe the gate to what *is* reachable this sprint (e.g. "yields the registerable artifact via the external bridge; in-adapter scaling is next sprint") rather than asking for an outcome the plan can't deliver with what it's holding.
- Heuristic that catches most cases cheaply: **any verification gate that names a capability the plan itself defers is suspect.** Read the gate statement and the deferral statement together — if the gate needs the deferred thing, the plan is promising a result it pushed out of scope.

Like the component check, this is a read-through, not tooling. It catches the subtler error: not "the plan points at a thing that isn't there," but "the plan promises a result it can't reach with what it's holding."

### 7. Present for Feedback

- Share your proposal clearly
- Invite the user to provide their feedback, ideas, and thoughts
- Signal that you're ready for the feedback cycle

## Output Format

Present your proposal conversationally, covering:

- **Sprint N: [Proposed Name/Theme]**
- **Goal**: What this sprint will accomplish
- **Proposed Scope**:
  - [Item 1]
  - [Item 2]
  - [etc.]
- **Rationale**: Why this scope makes sense now
- **Complexity Estimate**: [Low/Medium/High] with brief justification
- **Open Questions**: Anything that might affect the scope
- **Ready for Feedback**: Invitation for user input

## Important Notes

- This is a **proposal**, not a commitment. The feedback cycle may reshape it significantly.
- Be thoughtful but not rigid. The user often has ideas that will enhance or redirect.
- If this is Sprint 1, acknowledge the special nature of starting fresh.
- If continuing from a previous sprint, acknowledge what was learned.
- **Don't hedge with optional or stretch items.** Each item in your proposed scope is something we'll commit to doing in this sprint. If you're unsure whether an item belongs, propose without it — the user can ask to add it during discussion. Items marked as "optional" or "stretch" tend to be skipped by the Implementor, accumulating debt that carries into future sprints. Plan the sprint you actually intend to complete.

## Before You Begin

Read these files to establish context:
1. `.mcc*/architect_state.md` - Project state and sprint history
2. `docs/roadmap.md` - Roadmap status
3. Recent sprint logs (`.mcc*/sprint_log.md`)
4. Active deltas (use Glob for `docs/delta_*.md`)
5. PDT crossover (use Glob for `docs/crossover/commission_*_request.md`) - check for open commissions

## Begin

Review the project state and present your sprint proposal. End by inviting the user to share their feedback via `/mama:arch-discuss` (or they may just respond conversationally with their thoughts).

$ARGUMENTS
