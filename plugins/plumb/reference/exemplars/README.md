# Exemplars — what a project-authored ceremony skill looks like

Two real-shaped ceremony skills from **Kiln**, an illustrative project: a
cloud-plus-embedded platform that runs firing schedules for industrial ceramic
kilns. Kiln is fictional — these were authored by the PLUMB team to set a
quality bar until real projects contribute real ones — but everything about
their *shape* is drawn from practices run at scale, and nothing about their
*content* is meant for your project.

**That is the point. Calibrate against these; do not copy them.**

Kiln's vocabulary is deliberately not yours: they bound work into "batches",
their failure catalog is the "firing atlas", their roles include `bench_log`
and `batch_plan`. If those words appeared in your skills, something went wrong
— your ceremonies should be written in *your* project's words, from *your*
project's reality, with a first draft that came from you. A pre-written
ceremony adapted is a ceremony inherited; the exemplars exist so you can see
the grain and the discipline, then write your own.

## What to calibrate on

Read the exemplars with these questions, which are also the checklist for any
ceremony skill you author:

1. **Does it point at the document rather than restating it?** Kiln's skills
   read their way-of-working for judgment (`process_read`) and carry only
   sequence themselves. A norm restated in a skill is a norm that will drift
   from its source.
2. **Does it name the scar or the need that justifies it?** Every step that
   exists because something went wrong says so, with what it cost. A step
   whose price is recorded gets followed; ceremony without provenance decays
   into superstition.
3. **Is it addressed by role, never by filename?** `process_path bench_log`,
   not `docs/bench/log.md`. A skill that cannot name a file cannot resurrect
   a file the project retired.
4. **Is the trigger a condition, not a slot?** "When a new controller board
   revision arrives" survives reorganization; "in batch 12" does not.
5. **Is "done when" checkable, not felt?** For each step: what would it look
   like if this step were skipped, and would anyone notice?
6. **Is it meaningfully invocable by the PO and by any teammate?** A ceremony
   is shared vocabulary — the PO pointing at it and an agent running it should
   be the same act.
7. **Was it amended in place when reality corrected it?** Both exemplars carry
   dated amendments. A correction written into a retro while the ceremony
   stays unchanged is the failure this whole surface exists to end.
8. **Will you still be the ones running this in a year — or are you standing
   in for a user who will?** A project ceremony asserts *this is how we work*;
   a sequence you perform only because you currently occupy a chair your
   product will hand to its users belongs in a runbook or the product, not in
   your skills. The first project to migrate authored a ceremony that passed
   the other seven checks and failed only this one — their PO caught it, and
   for any project building a platform this is the check that will catch the
   most.
9. **Does it run at a moment when the person has the material but not the
   patience?** A procedure whose trigger is a moment of *insight* rather than
   a moment of *decision* gets bypassed — insight does not wait for ceremony,
   and a bypassed ceremony looks like coverage. If the answer is yes, **it
   wants to be a REVIEW of what they wrote, not a PROCEDURE for writing it**:
   let the moment produce the artifact, and let the skill check it afterward.
   The first project found this with their catalogue ceremony — two entries
   written, one rewritten, zero invocations, all correctly.

## Contributing real ones

When your project has a ceremony skill that has survived several runs and at
least one in-place amendment, it is exactly what should replace these. Strip
anything confidential, keep the amendments and their costs — the history is
the valuable part — and send it via `mcc reflect submit` or a PR.
