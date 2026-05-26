---
description: Process a completed sprint. Read the implementation log, update product documentation, apply deltas, update MAMA state, and prepare initial proposal for the next sprint.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, SendMessage
---

# Sprint Completion & Reconciliation

You are the **Architect Agent**. A sprint is wrapping up and you need to reconcile. The Implementor runs in its own user-launched session, so completion of its work is signaled by an `[HANDOFF]` message from `impl` (sent at the end of `/mama:impl-end`).

## Two Paths

**Path A — Handoff already received.** Recent context contains a `[HANDOFF]` message from `impl` for the current sprint (either delivered before this command was invoked, *or* this command is itself running because the handoff just arrived as a turn). Proceed with reconciliation (steps 1–7 below).

**Path B — No handoff yet.** No `[HANDOFF]` for the current sprint is visible in your recent context, but you (and the user) believe the sprint work is done. Send a request to the Implementor and end your turn:

```
SendMessage(to='impl', message='[IMPL-END-REQUESTED] Sprint {N}: please run /mama:impl-end so I can reconcile.')
```

Then briefly tell the user: "Asked impl to wrap up. I'll resume reconciliation when the handoff lands." Then stop. **Do not proceed with reconciliation in this turn.** When `impl` finishes its `/mama:impl-end` flow, it will SendMessage you a `[HANDOFF]` — that arrival becomes a fresh turn for you, at which point you naturally re-enter this command and take Path A.

Choose the path based on whether a `[HANDOFF]` for the active sprint is present.

## Reconciliation (Path A)

### 1. Read the Implementation Log

Find the implementation log for the completed sprint (`docs/sprint/X/implementation_log.md` or scoped equivalent). Read it carefully:
- What was accomplished?
- What decisions were made?
- What deviations from plan occurred?
- What bugs were encountered? What were the root causes?
- What questions did the Implementor raise (and how were they resolved)?
- What discoveries were made?
- What reflections does the Implementor offer?

**Handoff-review verification gate.**

Plan-component reality check (`arch-sprint-prep` Step 5) catches "the plan references things that don't exist" at plan-write time. This is the symmetric gate at handoff-review time: "what shipped doesn't match what the user asked for, in ways that won't surface until they use it." For each impl decision-note explaining a divergence from the plan, or any fix to a recurring/carryover bug, walk three lenses before continuing:

1. **Intent.** Does the divergence still satisfy the user's *articulated intent*, not just the technical constraint that drove it? A constraint can be real and the divergence can still be wrong — when impl finds a wall in front of "shape A" and ships "shape B," ask whether shape B preserves what made shape A worth pursuing. The right answer is often a third shape neither party considered.

2. **Hypothesis evidence.** For fixes to recurring or carryover bugs: is the evidence for the underlying hypothesis *direct* (probe trace, reproduction with state inspection, log evidence) or *inferred* (matches a pattern, looks like X, similar to last time)? If inferred, what 30-minute observation would convert it to direct evidence — and is that observation worth doing before the fix ships? Wrong-cause fixes look identical to right-cause fixes until dogfood reveals them.

3. **Felt-state framing.** For surfaces with status, lifecycle, or any state-indicating copy: does the framing match the data model semantics, or does it imply more than the code enforces? Status copy framed as a gate ("read-only", "pending approval", "locked") creates a wall in the user's head the code didn't write — and from the user's experience, a felt gate and a code gate are indistinguishable.

If any of the three flags a concern, the sprint isn't ready to close. Push back to impl, do the empirical verification yourself, or stay open until the gap closes. The downstream reconciliation steps (apply deltas, capture discoveries, etc.) don't fire until handoff-review passes.

### 2. Reconcile Documentation

Update product documentation based on what actually happened:

**Apply Implemented Deltas:**
- Find deltas that were implemented in this sprint
- Merge their content into the appropriate product docs
- Mark deltas as MERGED (or IMPLEMENTED if partially done)
- Update version/date in product docs

**What Shrank?** (counterweight to the additive verbs in this section)

For each delta merged, success criterion updated, or tech-debt item resolved this sprint, ask explicitly:

- Did this sprint render any rule, debt entry, doc section, or pattern obsolete?
- Did the merge create redundancy in the destination doc that the older description should retire?

If yes, prune now. If no, say so explicitly in the summary so the question is visible. The default is *additive*; this prompt exists to counter it.

**Capture Discoveries:**
- Any technical discoveries worth preserving?
- Any architectural insights that emerged?
- Any decisions made during implementation that should be documented?

**Update Success Criteria:**
- Mark completed items in product docs
- Note any criteria that shifted

**Note Deviations:**
- If implementation differed from design, update docs to reflect reality
- Don't hide deviations -- document them with rationale

**Resolve Tech Debt: move, don't strike.**

When a tech-debt item carried in `CLAUDE.md` resolves this sprint:

- **Move** the item to `sprint_log.md` under the resolving sprint, preserving provenance (e.g., `Resolved S{N}: {original description} → {how it was resolved}`).
- **Delete** the entry from `CLAUDE.md`.
- **Strikethrough is not a terminal state.** Strikethrough entries auto-load into every future session as archaeology; the sprint log is the durable record.

Same rule applies when a delta merge supersedes an older doc section: replace, don't append-with-strikethrough.

**Memorialization ownership** (who writes what, where):

When both you and the Implementor observe the same lesson at sprint close, both can independently land on "this should go in CLAUDE.md." That's a real concurrent-write failure mode — independent writers each pass the four gates and the rule lands twice with different wording. To prevent it, the methodology has explicit ownership:

| Surface | Owner | What it carries |
|---|---|---|
| `CLAUDE.md` | **Architect** | Evergreen project rules every session needs (auto-loaded). Impl surfaces candidates in their handoff/retrospective; arch reviews against the four `pattern-add` gates and lands them. |
| `architect_state.md` | **Architect** | The Architect's running project knowledge across sessions. |
| `implementor_state.md` | **Implementor** | Tacit knowledge for the next-session bootstrap. Written on demand (not every sprint). |
| Implementation log | **Implementor** | Sprint-of-record narrative; arch reads but doesn't edit. |
| `decisions_log.md` | **Architect** | First-class resolved decisions with rationale. |
| `concept_backlog.md` | **Architect** | Deferred items / future-work tracking. |
| `sprint_log.md` | **Architect** | Chronological sprint history. |

When reconciling at sprint close: if the Implementor's handoff proposes CLAUDE.md additions AND you saw similar candidates while reading the log, **dedupe at this point** — pick one canonical wording, write it once, and move on. This is the moment to catch concurrent-write duplication before it lands.

**Cluster-check at memory-add time.**

The four pattern-add gates catch individual rules: load-bearing? test-enforced? would-be-missed? evergreen? They do **not** catch the cluster signal where 3+ individually-valid rules collectively point at a missing structural fix. Today that signal only fires at `/mama:reflect` cadence, so clusters sit accumulating for full reflection cycles.

Before landing any new CLAUDE.md rule (or before the moment you would), scan CLAUDE.md for related rules in the same topic area (heading, file/module name, subsystem, pattern family). If this rule would make the topic carry **3+ rules**, stop and choose:

- **Open a structural-fix backlog item** that obviates the cluster (a test fixture, a helper, a reference doc, a code-level abstraction). Defer the rule until the structural fix is judged.
- **Demote the topic to a reference doc** (e.g. `docs/<topic>.md` or `frontend/src/components/<x>/README.md`). Replace the cluster in CLAUDE.md with a one-line pointer. Auto-load surface shrinks; the knowledge stays addressable from the call site.
- **Explicitly justify adding the Nth rule** (rare). Document why the structural fix isn't the right move yet — typically because the pattern isn't stable enough or the cost-benefit doesn't pencil. The justification is the discipline check; without it, the default is one of the prior two options.

Stale clusters from subsystem retirement (e.g. CLAUDE.md still describes a substrate the sprint just evicted) also surface here: if this sprint operated on a subsystem CLAUDE.md describes as live, the corresponding rules belong in `sprint_log.md` under the retiring sprint, not in auto-loaded context.

### 3. Address Implementor Questions

- Review any questions flagged in the implementation log
- Provide answers or note that they need discussion
- Update documentation if questions reveal gaps

### 4. Learn from Reflections

The Implementor's retrospective is valuable:
- What went well? Can we do more of that?
- What could be improved? How can we adjust?
- Any process improvements for future sprints?

### 5. Update MAMA State

**Update `architect_state.md`** in your `.mcc*/` directory:
- Add this sprint to the sprint history with outcome, key learnings, tech debt carried
- Update the current status section
- Note any important discoveries or changes
- Preserve the `MAMA Version:` line (do not remove it when rewriting)

**Compact prior content before writing the new entry.**

`architect_state.md` is the next CLAUDE.md if you let it accumulate. The state-doc carries *current state + active-arc detail*; older detail belongs in `sprint_log.md`. After writing the new sprint's row and Current Status block:

- **Last Updated paragraph from the prior sprint** → demote to a one-line band entry in Sprint History. Don't carry "PRIOR (Sprint N-1 ... PRIOR (Sprint N-2 ..." chains.
- **Sprint History rows older than the current arc** → compress to one-line per band (or per arc), pointing at the relevant `sprint_log.md` section for detail.
- **Carried tech debt / open questions** → consolidate; if an item has been "carried" 5+ sprints unchanged, ask whether it's truly active or a candidate for the structural-fix registry (see Step 6).

The compaction sub-pass is a counterweight to additive-by-default — same shape as the move-not-strike rule for CLAUDE.md tech debt, applied to state-doc.

**Update `sprint_log.md`** in your `.mcc*/` directory:
- Add a chronological entry for this sprint with date, status, summary, key learnings, deviations, and tech debt

**Update `methodology_holds.md`** in your `.mcc*/` directory (if the project uses it; see `multi-agent-methodology` skill):
- Increment any pattern-instance counts observed this sprint
- File any structural-fix candidates that emerged from the cluster-check (Step 2)
- Mark items retired if this sprint resolved them

### 6. Prepare Next Sprint Proposal

Based on:
- The roadmap
- What was just accomplished
- What was learned
- Any new priorities that emerged

Prepare an initial proposal for the next sprint:
- Proposed goal and scope
- Rationale
- Open questions

### 7. Reflection Cadence Check

The reflection ritual (`/mama:reflect`) is recommended every 5–10 sprints, but architects in long-running projects are demonstrably bad at self-prompting — drift accumulates between reflections. `arch-sprint-complete` is the natural cadence beat; surface the prompt here so it triggers itself.

Determine sprints since last reflection. Two ways:
- Read `architect_state.md` for a `last_reflection_sprint:` field if present.
- Otherwise check the most recent `tmp/mama_reflection*.md` (or `tmp/pdt_reflection*.md`) artifact and infer sprint distance from sprint history.

Emit the prompt graduating by distance:

| Sprints since last | Tone | Message shape |
|---|---|---|
| 0–4 | (silent) | No prompt — within cadence |
| 5–7 | soft | "Sprint N since last reflection. Worth running `/mama:reflect` before next sprint planning?" |
| 8–9 | louder | "It's been N sprints since last reflection. Running `/mama:reflect` before continuing is recommended." |
| 10+ | overdue | "**Overdue: N sprints since last reflection.** Run `/mama:reflect` now — drift may have accumulated past the point of easy catch." |

**Arc-close inflection trigger (alongside the count-based ladder).**

Wall-clock sprint counts don't see arcs. Long arcs can pass 5–10 sprints without a true structural inflection point; fast arcs can close in 3 and still warrant reflection. Arc-close is the natural reflection beat regardless of count — the accumulated lessons from a closed arc are at their freshest right now.

If this sprint closes an arc (the architect named it as arc-close in the completion summary, or the sprint scope was the final phase of a multi-sprint thread), emit *in addition* to whatever the count ladder fires:

> **Arc-close inflection detected.** Arcs are natural reflection beats — accumulated lessons from a closed arc are at their freshest right now. Consider running `/mama:reflect` before the next sprint opens, regardless of sprint count since last reflection.

The architect can defer (small or trivially-scoped arcs may not warrant it). The point is making the question visible at the natural beat. Count-based ladder catches "we just haven't gotten to it"; arc-close trigger catches "this is the right moment regardless of count."

The prompt(s) belong in your summary (next step), not as a blocker. The architect can defer; making the question visible every sprint is what closes the cadence loop.

### 8. Present Summary

Provide a clear summary:
- Sprint X Completion Summary
- What was accomplished
- Documentation updates made (and what was *pruned* — make removals visible)
- MAMA state updates made
- Key learnings
- Questions addressed
- Reflection cadence note (if any prompt fired in step 7)
- Initial proposal for Sprint X+1
- Invitation for user feedback (which will flow into `/mama:arch-discuss`)

## Reconciliation Checklist

- [ ] Read implementation log thoroughly
- [ ] **Handoff-review verification gate passed** — intent / hypothesis evidence / felt-state framing each checked against impl decision-notes
- [ ] Updated product docs with implemented changes
- [ ] Applied/merged relevant deltas
- [ ] Asked "what shrank?" — pruned obsolete rules / docs / patterns where applicable
- [ ] **Cluster-check at memory-add time** — no CLAUDE.md topic at 3+ rules landed without structural-fix-or-demote decision
- [ ] Resolved tech debt by moving (not striking through) entries to `sprint_log.md`
- [ ] Captured discoveries worth preserving
- [ ] Addressed Implementor questions
- [ ] Noted any process improvements
- [ ] Updated `.mcc*/architect_state.md` with sprint history
- [ ] **Compacted prior content in architect_state** — Last Updated paragraph demoted; older Sprint History rows compressed
- [ ] Updated `.mcc*/sprint_log.md` with sprint entry
- [ ] Updated `.mcc*/methodology_holds.md` if present — incremented counts; filed any new structural-fix candidates
- [ ] Checked reflection cadence — emitted prompt if 5+ sprints since last, or if this sprint closed an arc
- [ ] Prepared next sprint proposal

## Before You Begin

Read these files to establish context:
1. The implementation log for the completed sprint
2. The corresponding implementation plan
3. `.mcc*/architect_state.md` -- your running state
4. Active deltas (use Glob for `docs/delta_*.md`)

## Begin

Determine which path applies (handoff received vs. not), then either dispatch the impl-end request and stop, or proceed with full reconciliation.

$ARGUMENTS
