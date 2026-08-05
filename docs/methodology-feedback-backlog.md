# Methodology Feedback — Deferred Backlog

Maintainer-side backlog of feedback themes that surfaced in triage rounds, were judged legitimate signal, but were **deferred** rather than actioned in their round (per the now/defer/drop slate discipline in `methodology-feedback-process.md`).

This file exists because deferred themes with no home rot — the same failure mode the reflections themselves keep describing (a surfaced-but-unacted finding evaporates until rediscovered). Writing them down with a **promotion trigger** lets us pull each forward at the right moment instead of re-deriving it every round.

## How this backlog works

- **One entry per deferred theme.** Source feedback issues linked. Corroboration noted (how many *independent projects*, not raw issue count — serial reflections of one project are weaker signal).
- **Promotion trigger**: the concrete signal that should move this from defer → now. Usually "corroborated by a 2nd/3rd independent project," "the design shape converges," or "a NOW item it overlaps with ships and this becomes the natural follow-on."
- **Review cadence**: walk this file at the **start of each feedback round's synthesis** (Phase D, step 2-ish). Anything whose trigger has fired joins that round's NOW candidates. Anything stale (3+ rounds, trigger never fired, no new corroboration) gets re-evaluated for drop.
- This is the maintainer analog of the per-project `methodology_holds.md` registry — same shape (detect → hold → force a decision at the next natural beat), applied to our own methodology backlog.

---

## Deferred — Round 3 (2026-06-19, issues #37–#54)

### post-handoff verify / ratify / iterate loop has no named beat
- **Sources**: [#53](https://github.com/yobryon/methodical-cc/issues/53) (`mama:ratify`), [#46](https://github.com/yobryon/methodical-cc/issues/46) (external-artifact gate + arch-runs-the-probe), [#44](https://github.com/yobryon/methodical-cc/issues/44) (dogfood-round lifecycle step)
- **Corroboration**: 3 independent projects (EasyVista, Submatrix, Hew)
- **Shape**: the methodology models `handoff → reconcile → commit`; real interactive/empirical/physical work is `handoff → dogfood/ratify/iterate → commit`. No first-class beat for the verification loop between handoff and close.
- **Why deferred**: strong signal, but the three proposals diverge (a named ritual vs. a lifecycle step vs. a gate-interpretation discipline). Needs a convergence/design pass before it's actionable.
- **Promotion trigger**: a 4th project corroborates, OR we do a focused design pass that reconciles the three shapes into one. High likelihood of promotion — this is the strongest DEFER item.

### in-advance design CONSULT as a named methodology step
- **Sources**: [#44](https://github.com/yobryon/methodical-cc/issues/44), [#45](https://github.com/yobryon/methodical-cc/issues/45), [#46](https://github.com/yobryon/methodical-cc/issues/46) (Submatrix); adjacent: [#54](https://github.com/yobryon/methodical-cc/issues/54) "impl-judgment-hedge" ratchet
- **Corroboration**: mainly 1 project (Submatrix serial), 1 adjacent
- **Shape**: impl sends a `[CONSULT]` describing the shape it intends *before building* novel-shape work; arch reviews; converge in one round-trip; then build. Prevents rework rather than catching it after. Currently emergent-only, unprotected against compaction.
- **Why deferred**: well-argued but mostly single-project. The plan could mark phases "novel-shape — CONSULT before building."
- **Promotion trigger**: a 2nd independent project names the pre-build CONSULT (not just the arch↔pdt prep loop, which is distinct) as high-value.

### two-track / multi-implementor sprint pattern
- **Sources**: [#49](https://github.com/yobryon/methodical-cc/issues/49) (Hestia)
- **Corroboration**: 1 project, well-shaped
- **Shape**: split a sprint across 2 implementors along a contract seam (per-track logs, re-sync-on-every-contract-addition handshake, two handoff-reviews, mock-until-contract, trim-FE-heavy-track-first).
- **Why deferred**: single project; codifying a whole multi-implementor sprint shape is a large surface for one project's evidence.
- **Promotion trigger**: a 2nd project runs (or wants to run) parallel implementors and hits the same need.

### bus discipline: converge-before-relay / "decision parked with human" / terse-ack on cross-traffic
- **Sources**: [#47](https://github.com/yobryon/methodical-cc/issues/47) (converge-before-relay), [#50](https://github.com/yobryon/methodical-cc/issues/50)/[#51](https://github.com/yobryon/methodical-cc/issues/51) (decision-parked + terse-ack), [#53](https://github.com/yobryon/methodical-cc/issues/53) (messages-crossed convention)
- **Corroboration**: 3 independent projects (Hew, Hestia, EasyVista)
- **Shape**: the bus's low latency invites premature relay of a still-moving decision, and teammate cross-traffic triggers re-prompting the human on a parked decision.
- **Why deferred**: needs to separate the **methodology-discipline** part (converge before relaying; terse-ack; latest-HANDOFF-is-authoritative) — which could be a kickoff protocol-pulse line — from the **bus-feature** part ("decision parked with human" as a first-class bus state), which is a harness/protocol ask we can't satisfy.
- **Promotion trigger**: ready now for the discipline half — bundle into a future kickoff-protocol-pulse refinement. The bus-state half stays parked (not our surface).

### reconciliation checklist + arch-sprint-complete → arch-sprint-prep overlap
- **Sources**: [#47](https://github.com/yobryon/methodical-cc/issues/47) (6-surface sweep needs a checklist), [#49](https://github.com/yobryon/methodical-cc/issues/49)/[#50](https://github.com/yobryon/methodical-cc/issues/50)/[#51](https://github.com/yobryon/methodical-cc/issues/51) (complete drafts next proposal that prep re-derives)
- **Corroboration**: 2 independent projects (Hew, Hestia)
- **Shape**: sprint-close touches many surfaces with no template making the sweep mechanical; and `arch-sprint-complete`'s "prepare next sprint proposal" step overlaps with `arch-sprint-prep` when chained.
- **Why deferred**: organizing tweak; mild. Worth folding into a future "reconciliation ergonomics" pass.
- **Promotion trigger**: the NOW arch-sprint-complete refinements ship and this becomes the natural follow-on cleanup; or a 3rd project flags the overlap.

### arc-close ritual/checklist + "arc ledger"
- **Sources**: [#48](https://github.com/yobryon/methodical-cc/issues/48) (arc-retro template), [#49](https://github.com/yobryon/methodical-cc/issues/49)/[#50](https://github.com/yobryon/methodical-cc/issues/50) (arc-close ritual distinct from sprint-close), [#37](https://github.com/yobryon/methodical-cc/issues/37)/[#38](https://github.com/yobryon/methodical-cc/issues/38) (one-line-per-sprint arc ledger)
- **Corroboration**: 2 independent projects (Hew, Hestia)
- **Shape**: the arc-close *trigger* (3.4) fires, but there's no arc-close *content/checklist* (refresh orientation, re-confirm next-phase resolution, consolidate cross-role confidence) and no "arc ledger" tracking an arc's shape across its sprints.
- **Promotion trigger**: a 3rd project corroborates, or pairs naturally with the post-handoff-loop design pass (both are "named beats the methodology is missing").

### retro-insight promotion at sprint-start
- **Sources**: [#42](https://github.com/yobryon/methodical-cc/issues/42) (Submatrix; 20-sprint latent gotcha lived in a log nobody re-read)
- **Corroboration**: 1 project, concrete
- **Shape**: a sprint-start scan of recent implementation-log retrospectives, surfacing insights for promotion (to CLAUDE.md / methodology_holds / backlog).
- **Why deferred**: overlaps with methodology_holds + the reflection-findings carry-forward (NOW item #1). May be partly subsumed once that ships.
- **Promotion trigger**: re-evaluate after NOW item #1 ships — what's left unaddressed, if anything.

### joint arch+PDT reflect ritual
- **Sources**: [#39](https://github.com/yobryon/methodical-cc/issues/39)/[#40](https://github.com/yobryon/methodical-cc/issues/40) (Hew; both arch and PDT sides)
- **Corroboration**: 1 project
- **Shape**: a `joint:reflect` (or equivalent) that triggers `/mama:reflect` and `/pdt:reflect` in parallel and synthesizes into one feedback artifact. Done organically via SendMessage CONSULT.
- **Promotion trigger**: a 2nd project runs a joint reflect, or PDT-side reflection volume grows enough to justify the cross-plugin surface.

---

## Standing non-actionable (acknowledged, not in backlog rotation)

- **TaskCreate reminder noise** — flagged in every round by nearly every project; harness-shaped, not methodology-addressable. We've declined 4 rounds running. The fix lives in the harness (work-shape-aware firing, per-session silence). Documented here so we stop re-triaging it: **there is no methodology-side action**. If the harness ever exposes a per-session/per-persona suppression, revisit.
- **Architect/teammate verbosity** — recurring self-observation in personal notes (message length vs. decision weight). Self-discipline, not a methodology gate. Not actioning.
