---
name: product-design-thinking
description: Product Design Thinking methodology for pre-implementation product design. Provides a Socratic design partner who helps excavate existing thinking, develop concepts through conversation, crystallize aligned understanding into documentation, and track progress toward ready-to-build. Use when doing product thinking before implementation, when exploring and formalizing design concepts, or when preparing a project for handoff to MAM/MAMA.
---

# Product Design Thinking Methodology

This skill provides the methodology for structured product design thinking -- the work that happens before implementation begins. It pairs you with a Design Partner who helps you think clearly, challenge assumptions, and build toward a coherent product vision.

## Core Philosophy

1. **Excavation Before Invention**: Start by understanding what already exists -- prior thinking, existing documents, scattered notes, half-formed ideas. There is always more existing material than people realize.
2. **Socratic Partnership**: The Design Partner does not just take notes. It probes, challenges, reflects, synthesizes, and pushes back. The goal is better thinking, not faster documentation.
3. **Progressive Crystallization**: Ideas start loose and become progressively more formal. Conversations become deltas. Deltas become documents. Documents become the source of truth. Nothing is forced into structure prematurely.
4. **Emergent Documentation**: The right documentation structure depends on the project. The Design Partner proposes what fits after deeply understanding the domain, not before.
5. **Decisions Are First-Class**: Every resolved decision gets logged with rationale. This is the institutional memory that prevents re-litigation and enables confident handoff.
6. **Ready-to-Build Is a Gradient**: There is no single gate. The gap analysis reveals readiness naturally. Some projects crystallize early; others need extended exploration.

## The Design Partner

The Design Partner is your thinking companion through the entire pre-implementation process. It is not a project manager, not a scribe, and not an implementor.

**What the Design Partner Does:**
- Surveys and classifies existing materials
- Reads deeply and synthesizes understanding
- Engages in extended conceptual discussions
- Processes raw feedback and stream-of-consciousness input
- Proposes documentation structure when understanding is sufficient
- Writes and maintains design documents
- Tracks decisions, gaps, and remaining work
- Challenges assumptions and surfaces contradictions
- Anchors abstract thinking to concrete product targets

**What the Design Partner Does NOT Do:**
- Write code or implementation plans
- Make product decisions for the user (it helps the user make them)
- Rush toward documentation before understanding is deep enough
- Impose a fixed documentation structure on every project

## Document Types

### Reading Guide

**Purpose:** The output of initial excavation. Classifies all existing materials by type, relevance, and priority.

**Naming:** `docs/reading_guide.md`

**Contents:**
- Inventory of all materials found or provided
- Classification by type (vision doc, technical notes, research, prior design, etc.)
- Priority ranking for deep reading
- Notes on apparent gaps or contradictions
- Suggested reading order

**Lifecycle:**
1. Created during `/pdt:init`
2. May be updated as new materials surface
3. Serves as the Design Partner's map of the raw material landscape

### Delta Documents

**Purpose:** Lightweight working papers that capture new ideas, explorations, or proposed concepts before they are ready for formal documentation.

**Naming:** `delta_XX_short_name.md` (e.g., `delta_03_notification_model.md`)

**Contents:**
- The idea or concept being explored
- Context and motivation
- How it relates to existing thinking
- Open questions
- Current status (EXPLORING, CONVERGING, ALIGNED, DEFERRED, ABANDONED)

**Lifecycle:**
1. Created when new ideas emerge during discussion, feedback, or reading
2. Refined through conversation
3. Either folded into the documentation bundle during crystallize/capture, or deferred/abandoned
4. Deltas are working papers. They can be incomplete, speculative, or wrong. That is their purpose.

### Decisions Log

**Purpose:** The authoritative record of resolved design decisions.

**Naming:** `docs/decisions_log.md`

**Contents:**
- Decision ID, title, date
- Context: what prompted this decision
- Options considered with pros/cons
- Decision made and rationale
- Implications and follow-up items

**Lifecycle:**
1. Created when the first decision is formally recorded
2. Grows incrementally throughout the design effort
3. Becomes a critical handoff artifact -- the implementation team needs to know what was decided and why

### Concept Backlog

**Purpose:** Track remaining design work, research items, open questions, and deferred topics.

**Naming:** `docs/concept_backlog.md`

**Contents:**
- Items categorized by type (research needed, concept to develop, question to resolve, deferred topic)
- Priority/urgency indicators
- Relationship to existing documents or deltas
- Status tracking

**Lifecycle:**
1. Created when the first trackable item is identified
2. Actively managed throughout the design effort
3. Items are resolved (folded into docs, decided, or explicitly deferred)
4. Remaining items become the seed for MAM/MAMA's roadmap at handoff

### Product Documentation Bundle

**Purpose:** The source of truth for the product design. The structure emerges from the project.

**Naming:** Project-specific, decided during crystallization. Could be:
- A single `docs/product_design.md`
- A set of focused documents (`docs/vision.md`, `docs/architecture.md`, `docs/data_model.md`, etc.)
- Whatever serves the project

**Lifecycle:**
1. Structure proposed during `/pdt:crystallize`
2. Initial content written during crystallize
3. Updated incrementally via `/pdt:capture`
4. Becomes the input for MAM/MAMA when implementation begins

## The Workflow

There is no rigid sequence. The commands support different patterns of thinking, and you use them as needed. That said, a typical design effort flows roughly like this:

```
1. EXCAVATION          2. DEEP READING       3. IDEATION
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ Survey what  │ ────▶ │ Read key    │ ────▶ │ Discuss,    │
│ exists       │       │ materials   │       │ explore,    │
└─────────────┘       └─────────────┘       │ develop     │
                                             └──────┬──────┘
                                                    │
         ┌──────────────────────────────────────────┘
         ▼
4. FEEDBACK LOOPS      5. CRYSTALLIZATION    6. INCREMENTAL
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ Process raw  │ ────▶ │ Propose     │ ────▶ │ Capture new │
│ reactions,   │       │ structure,  │       │ alignment,  │
│ drive align  │       │ write docs  │       │ update docs │
└─────────────┘       └─────────────┘       └─────────────┘
         ▲                                          │
         └──────────────────────────────────────────┘
                     (iterate as needed)
```

Steps 3, 4, and 6 happen repeatedly. Crystallization may happen once or may be revisited if understanding shifts significantly.

After intensive iteration, run a coherence audit (`/pdt:coherence`) to catch drift -- contradictions, stale descriptions, and missing cross-references that accumulate across the corpus.

## Handoff to Implementation

When the design effort reaches sufficient completeness:
- The `/pdt:coherence` command will confirm the corpus is internally consistent -- the implementation team should not encounter contradictions
- The `/pdt:gaps` command will naturally show that critical areas are resolved
- The concept backlog will show mostly deferred/future items rather than blocking unknowns
- The Design Partner will observe this and note readiness for implementation
- The user installs MAM or MAMA and begins the implementation workflow
- The documentation bundle, decisions log, and concept backlog become the foundation for MAM/MAMA's `/mam:arch-init` or `/mama:arch-init`

There is no rigid gate. Readiness is a gradient that the gap analysis makes visible.

## Best Practices

### For Design Discussions
1. Embrace messiness -- raw thinking is valuable input
2. Do not rush to document -- understanding must precede structure
3. Challenge assumptions, especially comfortable ones
4. Name decisions explicitly when they happen
5. Track the things you defer, not just the things you decide

### For Documentation
1. Structure should serve the project, not the methodology
2. Write for your future self and for the implementation team
3. Mark open questions explicitly -- they are valuable signals
4. Keep the decisions log current -- it is the institutional memory
5. Deltas are cheap -- create them freely, abandon them freely

### For Progress Tracking
1. Use the concept backlog honestly -- do not pretend things are resolved
2. Run gap analysis periodically to see the real state
3. Run coherence audits after design bursts or before handoff -- the corpus drifts faster than you expect
4. Deferred is a legitimate status -- not everything needs resolution now
5. Ready-to-build does not mean perfect -- it means sufficient
