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
| `/pdt:discuss` | Open-ended conceptual discussion |
| `/pdt:feedback` | Process raw feedback -- untangle, organize, drive toward alignment |
| `/pdt:crystallize` | The big moment: propose doc structure, write the documentation bundle |
| `/pdt:capture` | Memorialize incremental alignment (doc updates, deltas, decisions) |
| `/pdt:delta` | Capture a single new idea as a lightweight working paper |
| `/pdt:decide` | Record a resolved decision with full rationale |
| `/pdt:research` | Research a topic -- search, read, synthesize findings for discussion |
| `/pdt:research-brief` | Write a self-contained research prompt for an external agent |
| `/pdt:gaps` | Assess what is done, partial, open, deferred |
| `/pdt:backlog` | Update/review the concept development backlog |
| `/pdt:resume` | Re-establish context on an in-flight design effort |

## Typical Workflow

```
1. /pdt:init             Survey existing materials
2. /pdt:read             Deep-read priority items
3. /pdt:discuss          Explore concepts (repeat as needed)
4. /pdt:research         Go deep on a topic (or /pdt:research-brief to commission it)
5. /pdt:feedback         Process reactions and new ideas
6. /pdt:crystallize      Write the documentation bundle
7. /pdt:capture          Capture incremental updates
8. /pdt:gaps             Assess readiness
   → Hand off to MAM or MAMA for implementation
```

The workflow is not strictly linear. Discussion, feedback, delta creation, and decision recording happen throughout. Crystallization happens when understanding is deep enough.

## Design Artifacts

After a design effort, the project typically has:

```
your-project/
├── CLAUDE.md                      # Project context
├── docs/
│   ├── reading_guide.md           # Material survey and classification
│   ├── decisions_log.md           # All resolved decisions with rationale
│   ├── concept_backlog.md         # Tracked design work and open items
│   ├── delta_XX_*.md              # Working papers for ideas
│   └── [product documentation]    # The crystallized documentation bundle
│                                  # (structure emergent per project)
```

## Philosophy

PDT embodies a few core beliefs:

- **Understanding precedes structure.** Do not template what should be discovered.
- **Raw thinking is valuable input.** Stream-of-consciousness, half-formed ideas, scattered notes -- all of it contains signal.
- **Decisions need rationale.** A decision without a recorded "why" is just an assertion that will be relitigated.
- **Ready-to-build is a gradient.** Gap analysis reveals readiness naturally. There is no artificial gate.
- **The Design Partner thinks with you, not for you.** It probes, challenges, and reflects. It does not just take dictation.

## Handoff to MAM/MAMA

PDT does not have an explicit "ready to build" command. Instead:

1. Run `/pdt:gaps` to see the current state
2. When the assessment shows readiness, install MAM or MAMA
3. Run `/mam:arch-init` (or `/mama:arch-init`) -- the Architect will consume the PDT documentation bundle as its input
4. The concept backlog's deferred items become the seed for the implementation roadmap
5. The decisions log provides the institutional memory the Architect needs

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
