# Changelog

## 1.1.0 — 2026-03-20

### PDT ↔ MAM Crossover Channel

Introduced a formal communication layer between PDT and MAM/MAMA. The two plugins are now peers with different domains — PDT owns design indefinitely, MAM owns execution — communicating through discrete files in `docs/crossover/`.

**New PDT commands:**
- **`/pdt:commission`** — Request execution work from MAM (validation, prototyping, investigation). Produces `docs/crossover/commission_NNN_request.md`.
- **`/pdt:orient`** — Write or update the architect orientation, a living document that guides the Architect into the design corpus with reading order, priorities, and confidence assessments. Produces `docs/architect_orientation.md`.
- **`/pdt:consult`** — Process a design question from the Architect. Reads `consult_NNN_request.md`, discusses with user, writes `consult_NNN_response.md`.
- **`/pdt:debrief`** — Process an implementation debrief from the Architect after a milestone. Evaluate design fidelity, absorb emergent insights, evolve the design.

**New MAM/MAMA commands:**
- **`/mam:consult-pdt`** — Formalize a design question for PDT when the Architect encounters a design flaw, ambiguity, or trade-off. Produces `docs/crossover/consult_NNN_request.md`.
- **`/mam:commission-complete`** — Report results of a PDT commission. Reads the original request, writes `commission_NNN_response.md`.
- **`/mam:debrief-pdt`** — Report back to PDT after a milestone (MVP, phase completion, version release) with an assessment of how the design played out in practice. Produces `docs/crossover/debrief_NNN.md`.

**Modified MAM/MAMA commands:**
- **`arch-init`** — Now checks for `docs/architect_orientation.md` as the primary entry point when a project was designed with PDT.
- **`arch-resume`** — Now checks `docs/crossover/` for new commissions, consultation responses, and orientation updates.
- **`arch-sprint-prep`** — Now checks for open PDT commissions when planning sprint scope.

### Cross-Document Coherence Audit

- **`/pdt:coherence`** — New command. Reads the full design corpus, tracks concepts across documents, cross-validates for consistency, and classifies findings by severity (contradictions, stale descriptions, missing reflections, status drift, minor). Offers to apply fixes with user approval.

### Command Consolidations

Reduced command count by merging commands that were points on a continuum rather than fundamentally different operations. The agent contextually determines the right mode based on user input and project state.

**`/pdt:capture`** now absorbs `crystallize` and `delta`:
- **Crystallization mode**: When no formal docs exist and understanding is deep enough — propose documentation structure, get alignment, write the full bundle.
- **Incremental mode**: When docs exist and recent work produced outcomes — targeted updates, new deltas, decisions, backlog items.
- **Quick capture mode**: When a single idea or small item needs writing — fast delta, decision log entry, backlog update.

**`/pdt:discuss`** now absorbs `feedback`:
- Adapts from Socratic exploration to structured feedback processing based on what the user brings. Writes at natural breaks with permission, not mid-flow.

**`/mam:arch-discuss`** now absorbs `arch-feedback`:
- Handles the full spectrum from open architectural exploration to sprint feedback processing. Sprint-aware when relevant (scope implications, proposal reactions) without forcing sprint context when it isn't.

**`/pdt:research`** now absorbs `research-brief`:
- Agent determines whether to investigate in-session (web search, read, synthesize) or write a self-contained brief for external research based on scope and user direction.

### Removed Commands

- **`/pdt:crystallize`** — Absorbed into `/pdt:capture` (crystallization mode).
- **`/pdt:delta`** — Absorbed into `/pdt:capture` (quick capture mode).
- **`/pdt:feedback`** — Absorbed into `/pdt:discuss`.
- **`/pdt:research-brief`** — Absorbed into `/pdt:research`.
- **`/mam:arch-feedback`** — Absorbed into `/mam:arch-discuss`.
- **`/mam:arch-user-story`** — Removed. User stories are handled naturally through `arch-discuss`.
- Same removals apply to MAMA equivalents.

### Terminology Updates

- Sprint Phase 2 renamed from "Feedback" to "Discussion" across SKILL.md diagrams and descriptions (both MAM and MAMA).
- "The Feedback Cycle" section renamed to "The Discussion Cycle" to reflect the collaborative model.
- CLAUDE.md sprint lifecycle updated to match.

### Documentation

- New scenario guide: `docs/scenarios/early-commission-before-full-launch.md` — how to pick up a PDT commission in MAM before the full architect initialization and orientation flow.
- All READMEs, SKILL.md files, and CLAUDE.md updated to reflect new commands, consolidations, and the crossover channel.
- PDT README restructured: "Handoff to MAM/MAMA" section replaced with "Working with MAM/MAMA" covering launch, ongoing collaboration, and phase transitions.

### Command Counts

| Plugin | Before | After |
|--------|--------|-------|
| PDT | 18 | 15 |
| MAM | 16 | 15 |
| MAMA | 16 | 15 |

More capability with fewer commands — consolidations give the agent latitude to do the right thing contextually rather than requiring the user to choose between similar commands.
