# PDT - Product Design Thinking

A Socratic design partner for pre-implementation product thinking.

## Overview

PDT provides a structured methodology for the product design phase -- the thinking that happens before implementation begins. It pairs you with a Design Partner who helps you:

- **Excavate** existing thinking from scattered documents, notes, and half-formed ideas
- **Synthesize** understanding through deep reading and reflection
- **Explore** concepts through open-ended Socratic discussion
- **Crystallize** aligned thinking into formal product documentation
- **Track** decisions, gaps, and remaining work toward ready-to-build

PDT is the natural predecessor to MAM/MAMA. When your design is ready, the documentation bundle, decisions log, and concept backlog become the foundation for implementation planning.

## Installation

```bash
# From marketplace
claude plugin install pdt

# Or test locally
claude --plugin-dir /path/to/plugins/pdt
```

## Commands

| Command | Purpose |
|---------|---------|
| `/pdt:init` | Survey existing materials, classify, produce a reading guide |
| `/pdt:read` | Deep-read materials, produce synthesis |
| `/pdt:discuss` | Discuss ideas, process feedback, explore concepts with the Design Partner |
| `/pdt:capture` | Write things down -- deltas, doc updates, decisions, or the full documentation bundle |
| `/pdt:decide` | Record a resolved decision with full rationale |
| `/pdt:research` | Research a topic in-session or write a brief for external research |
| `/pdt:gaps` | Assess what is done, partial, open, deferred |
| `/pdt:backlog` | Update/review the concept development backlog |
| `/pdt:next` | Figure out the best use of this session -- what's workable and highest-value |
| `/pdt:coherence` | Cross-document consistency audit -- surface contradictions, stale descriptions, drift |
| `/pdt:commission` | Commission work from MAM -- validation, prototyping, investigation |
| `/pdt:orient` | Write/update architect orientation for initial launch or phase transitions |
| `/pdt:consult` | Process a design question from the Architect, write a formal response |
| `/pdt:debrief` | Process an implementation debrief — evaluate fidelity, absorb insights, evolve the design |
| `/pdt:resume` | Re-establish context on an in-flight design effort |

## Typical Workflow

```
1. /pdt:init             Survey existing materials
2. /pdt:read             Deep-read priority items
3. /pdt:discuss          Explore concepts, process feedback (repeat as needed)
4. /pdt:research         Go deep on a topic (in-session or as a brief)
5. /pdt:capture          Write docs, capture updates, create deltas
6. /pdt:coherence        Audit consistency across documents, fix drift
7. /pdt:gaps             Assess readiness
8. /pdt:orient           Brief the Architect on the design corpus
9. /pdt:commission       Commission validation/prototyping work
    → Launch MAM for implementation
```

The workflow is not strictly linear. Discussion and decision recording happen throughout. Capture is used at any scale -- from a quick delta to the full documentation bundle -- whenever thinking has converged enough to write down.

After MAM launches, PDT continues to own the design. Use `/pdt:commission` to request execution work, `/pdt:consult` to respond to design questions from the Architect, and `/pdt:orient` again for phase transitions.

## Design Artifacts

After a design effort, the project typically has:

```
your-project/
├── CLAUDE.md                      # Project context
├── docs/
│   ├── reading_guide.md           # Material survey and classification
│   ├── decisions_log.md           # All resolved decisions with rationale
│   ├── concept_backlog.md         # Tracked design work and open items
│   ├── architect_orientation.md   # Architect's entry point to the design
│   ├── delta_XX_*.md              # Working papers for ideas
│   ├── [product documentation]    # The crystallized documentation bundle
│   │                              # (structure emergent per project)
│   └── crossover/                 # PDT ↔ MAM communication channel
│       ├── commission_NNN_request.md   # PDT commissions work from MAM
│       ├── commission_NNN_response.md  # MAM reports results
│       ├── consult_NNN_request.md      # MAM asks PDT a design question
│       ├── consult_NNN_response.md     # PDT responds
│       └── debrief_NNN.md             # MAM reports on a milestone
```

## Philosophy

PDT embodies a few core beliefs:

- **Understanding precedes structure.** Do not template what should be discovered.
- **Raw thinking is valuable input.** Stream-of-consciousness, half-formed ideas, scattered notes -- all of it contains signal.
- **Decisions need rationale.** A decision without a recorded "why" is just an assertion that will be relitigated.
- **Ready-to-build is a gradient.** Gap analysis reveals readiness naturally. There is no artificial gate.
- **The Design Partner thinks with you, not for you.** It probes, challenges, and reflects. It does not just take dictation.

## Working with MAM/MAMA

PDT and MAM are peers with different domains. PDT owns the design indefinitely; MAM owns execution. They run concurrently after launch, communicating through the `docs/crossover/` channel.

### Launch

1. Run `/pdt:coherence` to ensure the corpus is internally consistent
2. Run `/pdt:gaps` to see the current state
3. Run `/pdt:orient` to write the architect orientation -- the Architect's entry point to the design
4. Optionally, run `/pdt:commission` for any validation work needed before full implementation
5. Install MAM or MAMA and run `/mam:arch-init` (or `/mama:arch-init`)
6. The Architect reads `docs/architect_orientation.md` to understand the design, then builds the roadmap

### Ongoing Collaboration

- **PDT commissions MAM**: Use `/pdt:commission` to request validation, prototyping, or investigation work. Results come back via `commission_NNN_response.md`.
- **MAM consults PDT**: When the Architect hits a design question, they write a `consult_NNN_request.md`. Use `/pdt:consult` to discuss and respond.
- **Phase transitions**: When PDT is ready to hand off the next phase, use `/pdt:orient` to update the architect orientation with new priorities and reading guidance.
- **Milestone debriefs**: When MAM reaches a milestone (MVP, phase completion, version release), the Architect writes a `debrief_NNN.md`. Use `/pdt:debrief` to evaluate fidelity, absorb insights, and evolve the design.
- **Processing results**: Use `/pdt:discuss` to incorporate commission results or implementation learnings back into the design.

## When to Use PDT

Choose PDT when you:
- Are starting a new product and need to develop the vision before building
- Have scattered existing thinking that needs organization and crystallization
- Want a thinking partner, not just a note-taker
- Need to build toward a clear design before engaging MAM/MAMA for implementation
- Are doing product design work that does not involve writing code

See also:
- [MAM](../mam/README.md) (session-based implementation workflow)
- [MAMA](../mama/README.md) (subagent-based implementation workflow)
