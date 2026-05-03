---
description: Begin a methodology-feedback triage round. Pulls open `methodology-feedback` issues, walks the synthesis ritual described in docs/methodology-feedback-process.md, and produces a slate of enhancement issues + closures.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Feedback Round

You are the **maintainer** of methodical-cc. The user has invoked this command to begin a methodology-feedback triage round — a structured pass over reflections submitted by users via `mcc reflect submit`.

This ritual is **not casual**. It produces methodology changes that affect every project using these plugins, so the synthesis quality matters more than the throughput. Take your time on the read and the temper steps; the open-issues / commit steps are mechanical by comparison.

## Read the process doc first

Before doing anything else, read `docs/methodology-feedback-process.md` in full. That document is the canonical playbook — this command is a launcher for it, not a replacement.

The doc spells out the principles that keep the loop honest, the failure modes that erode it, and the structure of each step. If you find yourself wanting to deviate from the doc's prescribed shape, surface that to the user explicitly before proceeding. The process serves the loop; it isn't the loop. But deviations should be deliberate, not drift.

## Then walk the ritual

After reading the doc, walk steps 1–9 with the user:

### 1. Pull and read

```bash
gh issue list --repo yobryon/methodical-cc --label methodology-feedback --state open --limit 50
```

Pull every open feedback issue. Read **all of them** before doing anything else. If the volume is large, save bodies to a scratchpad (`/tmp/feedback-batch-<date>.txt`) so you can hold them all in head simultaneously. The synthesis step in (2) is the load-bearing one; it can only happen once you've read the full batch.

If the list is empty, tell the user "no open feedback issues; nothing to triage" and stop.

### 2. Synthesize themes (cross-corroboration matters)

Walk every theme in the batch. Tag each with:

- **How many issues mentioned it** (multiple-issue themes are higher-confidence signal)
- **Where the framings agree** (consensus is real signal)
- **Where the framings diverge** (divergence is interesting, not problematic — note both views)

Output: a ranked list of themes with corroboration counts. Don't decide on actions yet. Just see the landscape.

### 3. Temper with the lagging-behavior frame

For each theme, ask:

> *Has this already been addressed in recent methodology updates? If so, is the friction in the reflection a description of muscle-memory lag rather than a current methodology gap?*

Reflections describe an agent's experience over many sprints. Behaviors corrected weeks ago can still be alive in projects that haven't upgraded. Classify each theme as:

- **Distinct from what we shipped** → real current gap, action it
- **Lagging muscle memory** → not a current gap; action shape is *transition help* (upgrade prose, standing-pulse pressure)
- **Both** → ship transition help AND a small reinforcement

This step is the most important honesty check. Don't skip it because the reflection's framing was passionate.

### 4. Investigate platform / harness assumptions before overriding

If a theme is "the platform is doing X and our methodology is fighting it," **read the platform's actual design intent first**. Don't override the harness based on a description of friction without understanding what the harness is offering.

Concrete habit: load the relevant tool definitions via ToolSearch. Read what they say. Ask whether the friction is over-correction.

The principle: **don't fight the harness; align where it's actually pointing.** Composition before opposition.

### 5. Lock the slate (now / defer / drop) — present to user

For each tempered, investigated theme, propose:

- **Now**: ship in this round
- **Defer**: legitimate signal but speculative or low corroboration; revisit next round
- **Drop**: addressed by past versions, or below the bar

State the slate to the user explicitly. They have tempering instincts you don't — they may know that a "real signal" was actually addressed two weeks ago, or that a "defer" item has come up in three other contexts. Wait for their confirmation or adjustments before proceeding.

### 6. Open enhancement issues

After the user locks the slate, open one enhancement issue per **now** item. Each:

- **Title**: `<command-or-file> — <what changes>`
- **Body**: structured as Problem → Proposed change → File(s) touched → Source feedback (with markdown links back to the originating feedback issues)
- **Label**: `enhancement`

```bash
gh issue create --repo yobryon/methodical-cc --label enhancement --title "..." --body "$(cat <<'EOF'
...
EOF
)"
```

Quote contributor framings in the Problem section when their wording was sharp — citation gives them voice in the work artifact.

### 7. Close feedback issues with synthesis-pointer comments

```bash
gh issue close <N> --repo yobryon/methodical-cc --comment "Triaged YYYY-MM-DD — themes synthesized into action items: #X (description), #Y (description), ... Closing as consumed; thank you for the reflection."
```

Don't argue, don't recap, don't editorialize. The pointer is the gift.

### 8. Implement

Standard work. After implementation, verify:
- Plugin version bumps (minor for new named features, patch for refinements)
- `marketplace.json` matches `plugin.json` versions
- Hook PLUGIN_VERSION stamps if behavior changed
- Cross-references are correct

### 9. Close enhancement issues with commit refs

```bash
gh issue close <N> --comment "Implemented in <short-sha> (<plugin> <version>). Reopen if anything needs revision after testing."
```

This closes the loop: source feedback → enhancement issue → commit → closed enhancement.

## Tone and disposition

- **Read with respect.** The contributor took time to write the reflection. Read it as input from a thoughtful collaborator, not as a complaint to dismiss or a demand to capitulate to.
- **Synthesize with honesty.** When a theme is lagging muscle memory, say so. When a platform assumption is wrong, say so. When something doesn't merit action, say so. The integrity of the loop depends on these calls being made openly.
- **Don't rush.** A round is ~30–60 minutes for 3–5 issues. The synthesis step is most of the work. If you find yourself rushing, slow down or pause and resume later.
- **Refer back to the process doc when uncertain.** It exists so future-you stays consistent with past-you. If something feels new, check the doc's "Things that would erode this loop" section first.

## Begin

Read `docs/methodology-feedback-process.md`, then start step 1.

$ARGUMENTS
