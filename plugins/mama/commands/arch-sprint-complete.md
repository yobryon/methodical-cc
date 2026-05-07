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

**Update `sprint_log.md`** in your `.mcc*/` directory:
- Add a chronological entry for this sprint with date, status, summary, key learnings, deviations, and tech debt

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

The prompt belongs in your summary (next step), not as a blocker. The architect can defer; making the question visible every sprint is what closes the cadence loop.

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
- [ ] Updated product docs with implemented changes
- [ ] Applied/merged relevant deltas
- [ ] Asked "what shrank?" — pruned obsolete rules / docs / patterns where applicable
- [ ] Resolved tech debt by moving (not striking through) entries to `sprint_log.md`
- [ ] Captured discoveries worth preserving
- [ ] Addressed Implementor questions
- [ ] Noted any process improvements
- [ ] Updated `.mcc*/architect_state.md` with sprint history
- [ ] Updated `.mcc*/sprint_log.md` with sprint entry
- [ ] Checked reflection cadence — emitted prompt if 5+ sprints since last
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
