# Methodology Feedback — Maintainer Process

A process guide for ourselves: how to triage, decide on, and act on methodology-feedback issues submitted via `mcc reflect submit`. Written so future-us (or any other agent picking up maintainer work) keeps the process consistent and honest.

The goal is **a trustworthy feedback loop**: contributors who submit reflections see them taken seriously, but we don't get pulled into reactive thrash. Every theme gets a clear disposition; every action is traceable back to the feedback that informed it.

---

## Two-track issue model

We maintain two distinct issue tracks. Confusing them dilutes the value of both.

| Track | Label | Lifecycle | Purpose |
|---|---|---|---|
| **Feedback** | `methodology-feedback` | Submitted via `mcc reflect submit`. Read, synthesized, closed with a reference comment. Always shrinking. | Input. Each issue is a snapshot of one user's reflection — we don't argue with it, we absorb it. |
| **Enhancement** | `enhancement` | Opened from triage. Each links to its source feedback. Closed when the implementing commit lands. | Work. The actual development tracker. |

**Don't respond to feedback issues conversationally.** Don't ask follow-up questions, don't push back on framings, don't suggest workarounds. The author has already done the thinking; the artifact is what they want us to consider. Engaging conversationally invites the maintainer to argue with the user, which inverts the loop.

**Don't merge "feedback received" into "work to do."** When you close a feedback issue, it points at the enhancement issues that emerged from triage. The two tracks stay separated even when they cross-reference.

---

## The full process

A complete pass takes ~30–60 minutes for 3–5 feedback issues. Don't try to do it piecemeal; the synthesis step needs all the issues in head simultaneously.

### 1. Pull and read

```
gh issue list --repo <repo> --label methodology-feedback --state open --limit 50
```

Read **all** of them in one sitting. Resist the urge to start opening enhancement issues mid-read — the cross-corroboration in step 2 is the load-bearing bit, and you can only do it once you've held all the artifacts in head together.

For long sessions or many issues, save full bodies to a scratchpad first:

```
for n in <ids>; do
  gh issue view $n --repo <repo>
  echo
done > /tmp/feedback-batch.txt
```

### 2. Synthesize themes (cross-corroboration is the signal)

Walk every theme in the issues and tag it with **how many issues mentioned it**. Themes that appear in multiple independent reflections are higher-confidence signal than themes that appear in one. Note where the framings agree and where they diverge — divergence is interesting, not problematic.

Output of this step: a ranked list of themes with corroboration counts, like:

> 🔴 **CLAUDE.md / memory accumulation** — all 4 issues
> 🟡 **Reflect cadence slips** — 2 issues directly, 1 endorsement
> 🟢 **Implementation-log-as-side-channel** — 1 issue (concrete proposal)
> ...

Don't decide on actions yet. The point of this step is just to see the landscape.

### 3. Temper with the lagging-behavior frame

Before treating any theme as actionable, ask:

> *Has this already been addressed in recent methodology updates? If so, is the friction in the reflection a description of muscle-memory lag rather than a current methodology gap?*

This is the most important honesty check. Reflections describe an agent's experience over many sprints, often spanning multiple methodology versions. A behavior the methodology corrected three weeks ago can still be alive in any project that hasn't done a `/mama:upgrade` or had enough sprint cycles for the muscle to repivot.

Concrete examples of how this changes the action:

- **Theme**: "Agents add to CLAUDE.md by default; no prune ritual."
  - **Past version**: no codification gates existed. Theme is a current gap.
  - **Current version**: gates exist in `pattern-add`; `mama:reflect` ritual exists. Theme is **partly current gap, partly muscle-memory lag**. Different action shape: maybe `upgrade.md` "behaviors to unlearn" prose rather than another gate.

For each theme, classify:
- **Distinct from what we shipped**: real current gap, action it.
- **Lagging muscle memory**: not the methodology's current state. Action shape is *transition help* (upgrade prose, standing-pulse pressure), not new gates.
- **Both**: ship the transition help AND a small reinforcement.

### 4. Investigate platform / harness assumptions before overriding

When a theme is "the platform is doing X and our methodology is fighting it," **read the platform's actual design intent first**. Don't override the harness based on a description of friction without understanding what the harness is offering.

Concrete pattern: agents reported friction with Claude Code's "consider TaskCreate" reminder under MAMA. Initial instinct was "tell agents to ignore it." Better instinct: load the tool definitions, read what the tools were designed for, ask whether the friction is over-correction.

Reading TaskCreate/TaskList revealed they're explicitly **team-coordination tools** with owners, dependencies, cross-session persistence — not redundant progress trackers. The friction was real but the methodology guidance had over-corrected. The right answer was a when-it-earns-its-place rubric, not a blanket "ignore."

The principle: **don't fight the harness; align where it's actually pointing.** Future maintainer work should ask "what is the platform offering, and how do we compose with it?" before defaulting to "the harness is noise; we override."

### 5. Lock the slate (now / defer / drop)

For each tempered, investigated theme, decide:

- **Now**: ship in this round. Concrete enough to specify, high enough corroboration, fits a coherent minor bump.
- **Defer**: legitimate signal, but speculative on shape, or low corroboration, or large design surface. Note it in the discussion; revisit next round.
- **Drop**: addressed by past versions; muscle-memory lag adequately covered by transition help; or below the bar.

A useful test for "now" candidates: can you write a one-sentence change description that implementer-you would accept as a clear scope? If not, push it to defer.

A useful test for "defer" vs "drop": will the next batch of reflections likely re-surface this with more shape? If yes, defer. If no (truly project-specific or one-off), drop or backlog elsewhere.

State the slate explicitly to the user (or upstream maintainer) before opening issues. The user has tempering instincts you don't have — they may know that a "real signal" was actually addressed two weeks ago, or that a "defer" item has come up in three other contexts.

### 6. Open enhancement issues (one per actionable theme)

Each enhancement issue:

- **Title**: scope-of-change describing what changes where (`<command-or-file> — <what changes>`)
- **Body**: structured as Problem → Proposed change → File(s) touched → Source feedback (with links back to the originating feedback issues)
- **Label**: `enhancement`

The body's Problem section is where you *quote the reflection* if a contributor's framing was sharp. Citation is respectful and gives the contributor their voice in the work artifact.

Example title shapes that worked well in our first pass:
- `mama:upgrade — add 'behaviors to unlearn' prose for the 3.1.0 transition`
- `arch-sprint-start — add memory-discipline line to standing protocol pulse`
- `multi-agent-methodology — replace 'don't use task tools' with when-it-earns-its-place rubric`

### 7. Close feedback issues with synthesis-pointer comments

Each feedback issue gets one comment, then closes:

> Triaged YYYY-MM-DD — themes synthesized into action items: #N (description), #M (description), ... Closing as consumed; thank you for the reflection.

This serves three audiences:

1. **The contributor**: their input was read and acted on; they can follow the enhancement issues to see what landed.
2. **Future readers**: anyone hitting similar friction can search closed feedback issues and follow the trail to the methodology change.
3. **Us**: searchable history of *why* a methodology refinement happened.

Don't argue, don't recap their argument, don't editorialize. The pointer is the gift.

### 8. Implement

Standard work — read the relevant files, make the changes, verify cross-references and version stamps.

Worth checking after:
- Plugin version bumps (typically a minor bump if the slate adds named features; patch if pure refinements)
- `marketplace.json` matches `plugin.json` versions
- Hook PLUGIN_VERSION stamps if anything changes upgrade behavior

### 9. Close enhancement issues with commit refs

```
gh issue close <N> --comment "Implemented in <short-sha> (<plugin> <version>). Reopen if anything needs revision after testing."
```

Each enhancement issue closes with a one-liner referencing the implementing commit. This closes the loop: source feedback → enhancement issue → commit → closed enhancement.

---

## Principles to keep us honest

These are the disciplines that erode if we let them. Reread them before each round.

**1. The contributor isn't in the room.**
The reflection is what they want us to consider. We're not in conversation with them; we're in conversation with the artifact. Don't compose responses you'd send back; compose actions you'd take.

**2. Corroboration weight, not first-mover weight.**
A theme one user mentioned passionately is not stronger signal than a theme three users mentioned in passing. Sort by corroboration before sorting by passion.

**3. Temper before action.**
Always ask "is this current?" before "is this true?" A friction described in a reflection from a project that hasn't upgraded since v3.0.0 may be entirely real *and* entirely solved.

**4. The platform is also the user.**
When the methodology fights the platform (Claude Code itself), check who's wrong before overriding. Often the methodology has over-corrected; the right answer is composition, not opposition.

**5. Defer is honorable. Drop is honest. Don't backlog by default.**
Some themes don't need action. Calling that out explicitly is better than opening an enhancement issue that sits forever. The slate's "drop" decisions are as important as its "now" decisions.

**6. Traceability is the gift.**
Future-us (or someone debugging a methodology change) needs to be able to walk: feedback issue → enhancement issue → commit → file. Every link in that chain matters. Don't skip the cross-references.

**7. One round, one bump.**
Resist the urge to fold "while we're in there" changes into the slate. The slate is what came from this round of feedback. Other ideas you have can become their own enhancement issues with their own slates.

**8. Reading is most of the work.**
The synthesis step is where the value is. The opening-issues and writing-commits steps are mechanical. If you find yourself rushing the read, slow down — it's the only step that changes the methodology in a way that matches what users actually need.

---

## Things that would erode this loop if we let them

Notes-to-self about failure modes to watch for:

- **Maintainer-side reactivity.** Treating every reflection as a bug report instead of input. Symptom: enhancement issues open at the same rate as feedback issues, and we're always chasing.
- **Conversational drift on feedback issues.** Asking the contributor to clarify, push back, suggest. Symptom: feedback issues stay open for weeks; the loop loses authority.
- **Slate inflation.** Bundling adjacent ideas into "while we're in there" pile-ons. Symptom: the commit message has 9 bullets and 3 of them have no source-feedback link.
- **Skipping the temper.** Treating a single passionate reflection as decisive. Symptom: an enhancement issue lands a methodology change that contradicts a methodology change from two months prior.
- **Skipping the platform check.** Methodology guidance fights the harness without understanding what the harness was offering. Symptom: a future Claude Code update reveals that a tool we told agents to ignore was load-bearing for some other case.
- **No-op closure.** Closing feedback issues without the synthesis-pointer comment, or closing enhancement issues without the commit ref. Symptom: searchable history degrades; "why did we do this?" becomes unanswerable in 6 months.

---

## When to skip this process

This process is for **batch feedback rounds** — multiple reflections accumulated, time to synthesize. It's overkill for:

- A single one-off bug report (just fix it, normal workflow)
- A reflection that's actually a question (answer it, don't action it)
- Internal observations *we* notice during plugin work (those go straight to enhancement issues)

If you're processing one issue, just process it. The two-track model and synthesis machinery exist for the case where multiple reflections need cross-referencing.

---

## Authorial note

This guide was written immediately after the first batch (issues #1–#10), while the process was fresh. It's a snapshot of practice; it should evolve. If a future round reveals a step that didn't work, this doc should be updated to reflect what we learned. The process serves the loop; it isn't the loop.
