# Scenario: Early Commission Before Full Launch

## Situation

You have a project designed with PDT that is approaching ready-to-build, but has one or more validation questions that need to be answered through execution work (prototyping, investigation, technical validation) before the design can be finalized and the full implementation launched. PDT has written a commission for this work.

The key characteristics:
- PDT has produced a substantial design corpus (documents, decisions, deltas)
- The design is not yet fully ready for implementation — the commission results will feed back into further design work
- No architect orientation exists yet (PDT isn't ready to write one)
- This is the first time using MAM in this project
- You expect to continue PDT design work after the commission, then launch the full project later

## The Question

How do you pick up a PDT commission in MAM when you're not ready for the full architect initialization and orientation flow?

## Recommended Flow

### Session 1: MAM — Pick Up the Commission

Start a MAM session and run `/mam:arch-init`, pointing the architect at the commission:

```
/mam:arch-init We have a commission from PDT to pick up — see docs/crossover/commission_001_request.md
```

The architect will:
- Establish itself in the project
- Read `CLAUDE.md` (which has project context from PDT work)
- Discover there is no `docs/architect_orientation.md` — this is expected and not an error
- Read the commission request

Keep the init lightweight. The architect doesn't need to do the full pattern interview if PDT has already captured project context in CLAUDE.md. Focus on understanding the commission and doing the work.

The commission work doesn't need full sprint machinery (roadmap, sprint prep, sprint start). It's a bounded task: read the request, do the validation or prototyping, gather findings.

When done, run:

```
/mam:commission-complete 001
```

This writes `docs/crossover/commission_001_response.md` with findings, design implications, and recommendations. It also updates the request's status to `resolved`.

### Back to PDT — Process Results

Take the commission results back to the PDT session:

```
/pdt:discuss See docs/crossover/commission_001_response.md for the validation results
```

PDT processes the findings, updates the design, possibly writes more commissions, and eventually reaches the point where the design is ready for full implementation. At that point:

```
/pdt:coherence          # Ensure the corpus is consistent
/pdt:gaps               # Confirm readiness
/pdt:orient             # Write the architect orientation
```

### Session 2: MAM — Full Project Launch

Start a new MAM session and run:

```
/mam:arch-resume
```

The architect will:
- Read `CLAUDE.md` — recognize the project from the earlier session
- Find `docs/architect_orientation.md` — PDT's guided entry point to the design corpus
- Check `docs/crossover/` — see the completed commission and any new items
- Establish the full picture

Then proceed with the normal launch flow:

```
/mam:arch-roadmap       # Build the implementation roadmap
/mam:arch-sprint-prep   # Plan the first sprint
```

## Why a New Session for Full Launch

You might consider staying in the commission session and continuing into full project mode. A new session with `arch-resume` is better for several reasons:

1. **Time gap.** PDT needs time to process commission results, do further design work, and write the orientation. The commission session's context will be stale by then.

2. **Different posture.** The commission session was focused on a specific bounded task. Full launch requires the architect to absorb the entire design corpus, build a roadmap, and plan sprints. That deserves fresh attention, not a session that has been doing something else.

3. **arch-resume is designed for this.** It reads CLAUDE.md, finds the orientation (which now exists), checks the crossover folder for new items, and establishes the complete picture. It is the natural re-entry point.

4. **The arch-init wasn't wasted.** It established the Architect role and captured any project patterns not already in CLAUDE.md. Session 2's arch-resume builds on that foundation.

## The Full Picture

```
PDT Session                              MAM Session 1
───────────                              ─────────────
Design work produces corpus
/pdt:commission → writes request
                                         /mam:arch-init (lightweight, commission-focused)
                                         → reads commission, does validation work
                                         /mam:commission-complete → writes response

/pdt:discuss [commission results]
→ further design work
→ possibly more commissions

/pdt:coherence
/pdt:gaps
/pdt:orient → writes orientation
                                         MAM Session 2
                                         ─────────────
                                         /mam:arch-resume
                                         → reads orientation, full context
                                         /mam:arch-roadmap
                                         /mam:arch-sprint-prep
                                         → full project flow begins
                                         ...
                                         → reaches MVP
                                         /mam:debrief-pdt → writes debrief

/pdt:debrief [debrief results]
→ evaluates fidelity, absorbs insights
→ evolves design, updates docs
→ possibly /pdt:orient for next phase
```

## Variations

### Multiple Commissions Before Launch

If PDT writes several commissions before full launch, each can be picked up in the same MAM session. Run `arch-init` once, then work through commissions sequentially, running `/mam:commission-complete` for each.

### Commission Spawns More Commissions

If the validation results lead PDT to commission follow-up work, the same MAM session can pick those up too — or a new session can be started with `arch-resume` if enough time has passed.

### Commission During Active Implementation

If a commission arrives after the project is already in full sprint mode, the architect can fold it into sprint planning (arch-sprint-prep checks for open commissions) or handle it between sprints. No special setup needed — the crossover channel handles it naturally.
