<!-- EXEMPLAR from Kiln (an illustrative project — see README.md in this
     directory). One project's answer to "how do we close a bounded body of
     work". Calibrate against its shape; do not copy its content. Your
     project's rhythm, roles and vocabulary are not Kiln's. -->

---
name: close-a-batch
description: Close a batch — verify what the batch claims against the bench, reconcile the docs to reality, and only then call it done. Run when every issue in the batch's milestone is closed or explicitly carried, and before the next batch is planned. Nothing is "shipped" until this has run.
---

# Close a batch

A batch is closed by **checking it against things that cannot flatter us** —
the bench, the docs, the decisions log — not by the last issue reaching Done.
Our way of working calls reconciliation non-negotiable; this is the sequence
that discharges it. For the standing rules this ceremony leans on (what counts
as verified, who rules on deviations), read the document — `process_read
"Norms"` — they are stated there, not here.

## Steps

1. **Walk the milestone against the batch plan** (`process_path batch_plan
   --arc <n>`). Every phase the plan committed is either delivered, or named
   in the close record as undelivered — in the same place the batch records
   what it did ship. No silent re-scoping: an undelivered commitment that
   vanishes from the record will be re-promised in some future batch by
   someone who cannot know it already slipped once.

2. **Re-fire the batch's claims on the bench.** Every "verified on bench"
   claim in the milestone gets one live re-run *today*, on the current build,
   with the controller revision named in the log (`process_path bench_log`).
   A reading from three days ago is a reading we do not have.
   *(Amended after batch 7: a thermal-hold claim verified mid-batch was
   re-verified at close and failed — a config default had moved underneath it
   two days after the original reading. One stale green cost us a field
   report; re-firing at close costs about forty minutes.)*

3. **Verify the decisions log is complete, not write it.** Decisions were
   logged when made; this step diffs the milestone's discussion threads
   against the log and flags any ruling referenced in an issue but absent
   from the log. Writing a decision *at* close means writing it from memory,
   which is what the log exists to replace.

4. **Update the product docs to reality, including deviations.** Deviations
   are recorded with their rationale, never smoothed over. If the firmware
   does something the design doc says it should not, the doc changes or the
   firmware becomes an issue — it does not stay ambiguous.

5. **Sweep the reflection log and run `plumb:promote` if it has grown.**
   Observations that recurred this batch move toward norms; norms whose
   premise died this batch get expired.
   *(Amended after batch 11, which is why this step exists at all: three
   batches of observations sat unpromoted until the same bench mistake was
   made a third time — by the person who had logged it the first time.)*

6. **Say it is closed, in one message, with the record.** The close note
   links the milestone, the amended docs, and the bench log entries. Short —
   the artifacts carry the detail.

## Done when

- [ ] Every committed phase is delivered **or named as undelivered in the
      close record** — checkable by diffing plan against milestone
- [ ] Every bench claim re-fired today, on today's build, revision named
- [ ] Decisions log verified complete against the milestone (step 3's diff
      found nothing, or what it found is now logged)
- [ ] Product docs match reality; every deviation carries its rationale
- [ ] Reflection log swept; promotions done or explicitly deferred with a date
- [ ] Close note sent, linking the records
