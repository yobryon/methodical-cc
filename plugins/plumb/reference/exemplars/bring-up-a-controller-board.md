<!-- EXEMPLAR from Kiln (an illustrative project — see README.md in this
     directory). One project's answer to a pure DOMAIN ceremony — a procedure
     with no methodology in it at all, which is most of what a project's own
     skills turn out to be. Calibrate against its shape; do not copy its
     content. -->

---
name: bring-up-a-controller-board
description: Bring up a new controller board revision — from unboxing to trusted telemetry. Run when a new hardware revision (or a repaired board) arrives at the bench, before any firing data from it is treated as real. The order is load-bearing; do not run steps opportunistically.
---

# Bring up a controller board

New silicon lies politely: it boots, it reports, and nothing it says is yet
evidence. This sequence ends when the board's telemetry has *earned* trust,
which is a different event from the board working. Run it in order — the
order exists because we once trusted a reading at step 5 that step 3 would
have disqualified.

## Steps

1. **Record the revision before powering anything.** Board rev, firmware hash,
   thermocouple lot numbers → bench log (`process_path bench_log`). A reading
   without its hardware identity attached cannot be compared with anything
   later, and comparisons are the entire product.

2. **Flash the current release, not the working tree.** Bring-up validates
   *hardware*; a dev build makes every anomaly ambiguous between the board and
   your uncommitted change. If bring-up needs an unreleased fix, that fix
   ships first.

3. **Inject a thermocouple fault before trusting a temperature.** Disconnect
   TC1 mid-read and confirm the board *reports the fault* rather than holding
   the last value. **A gate's green means nothing until you have seen its
   red** — a board that fails this check produces flat plausible curves that
   are indistinguishable from a healthy hold.
   *(This step is the ceremony's reason to exist: rev C boards held last-value
   on open circuit for 11 seconds. Two firing curves from that bench week are
   still quarantined in the atlas — `process_path firing_atlas`, entry 9.)*

4. **Run the reference burn against the known kiln.** The bench kiln's
   reference profile has published checkpoints; the new board's curve is
   compared checkpoint-by-checkpoint against the *published* numbers, read
   from the atlas at comparison time — never against what anyone remembers
   the reference doing.

5. **Enumerate what derives from the calibration constants before saving
   them.** Offsets feed the drift monitor, the cone-equivalence table, and
   the export pipeline; a constant changed in one place with three consumers
   is a defect with a delay on it. The enumeration is written into the bench
   log entry, by name.
   *(Amended after rev D bring-up, when a saved offset silently re-based the
   drift monitor and a week of alerts measured the calibration, not the
   kilns.)*

6. **Mark the board trusted, in the log, with the evidence linked.** From this
   entry forward its telemetry is real. Boards without this entry do not
   feed production data — the export pipeline checks.

## Done when

- [ ] Identity recorded before first power
- [ ] Release firmware, hash logged
- [ ] Fault injection observed failing — the red seen, not assumed
- [ ] Reference burn within checkpoint tolerances, compared against published
      numbers read at comparison time
- [ ] Calibration consumers enumerated by name in the log entry
- [ ] Trusted-mark entry written; export pipeline accepts the board
