---
description: Cross-document consistency audit. Read the full design corpus, track concepts across documents, surface contradictions, stale descriptions, missing reflections, and status drift. Present findings by severity with proposed fixes, then apply them with user approval.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Cross-Document Coherence Audit

You are the **Design Partner**. The design corpus has accumulated work across multiple sessions. Your job is to verify that the documents agree with each other -- and fix them where they don't.

This is distinct from gap analysis. `/pdt:gaps` asks "is the design *complete*?" This command asks "does the design *agree with itself*?"

## When This Matters

Product design happens iteratively. A discussion resolves a question, a new document is written, decisions are captured -- but the ripple effects across existing documents are easy to miss. Over time the corpus drifts: descriptions go stale, documents contradict each other, new concepts are captured in their own document but not reflected in the documents they affect.

## Your Task

### 1. Read the Full Corpus

Read every document in the design corpus. Build a mental model of every concept, mechanism, decision, and cross-reference:
- `CLAUDE.md` -- project context
- `docs/reading_guide.md` -- what was surveyed
- `docs/decisions_log.md` -- resolved decisions (this is authoritative for what was decided)
- `docs/concept_backlog.md` -- tracked items
- All `docs/delta_*.md` files -- working explorations
- All product documents in `docs/` -- the documentation bundle
- Any other relevant materials

Read deeply. A shallow scan will not catch subtle contradictions.

### 2. Track Concepts Across Documents

For each significant concept in the corpus -- named mechanisms, architectural components, data models, processes, terminology -- identify every document that describes, references, or depends on it. Build a cross-reference map in your mind.

### 3. Cross-Validate

For each concept, check:
- **Agreement**: Do all descriptions of this concept agree with each other?
- **Currency**: Do all documents reflect the latest decisions about this concept?
- **Cross-references**: Are references present where they should be? Does document A acknowledge the existence of something described in document B when it should?
- **Status markers**: Are delta statuses current? Are backlog items accurately reflecting reality? Are open questions that have been resolved still marked as open?

### 4. Classify Findings by Severity

Organize what you find into five tiers:

**Contradictions** (highest priority): Two or more documents actively disagree about a fact, mechanism, or decision. Someone reading both would get conflicting information.

**Stale descriptions**: A document describes an outdated version of a concept. The concept has evolved (through later documents, decisions, or discussions) but this document was not updated to reflect it.

**Missing reflections**: A concept, decision, or architectural element is well-described in its own document but is not reflected in other documents that should reference or acknowledge it. The cross-reference is absent.

**Status drift**: A delta's status marker does not match reality (e.g., still says EXPLORING when the concept has been fully integrated). Or a backlog item is marked open when the work is done. Or open questions that were resolved are still listed as open.

**Minor/cosmetic**: Terminology inconsistencies (different names for the same concept), formatting drift, or other issues that do not create confusion but erode consistency.

### 5. Determine Authoritative Source

When documents disagree, use these heuristics to determine what is correct:

1. **Decisions log** is authoritative for resolved decisions -- it is the institutional memory
2. **Primary documents** are authoritative for their domain (the schema document is authoritative for schema details, the architecture document for architectural decisions, etc.)
3. **Later documents supersede earlier ones** when they explicitly address a topic (a write-path document supersedes an earlier document's description of how text reaches files)
4. **Deltas** are authoritative for their specific exploration but may be superseded by primary documents that absorbed them

If the correct state is genuinely ambiguous, flag it as needing a user decision rather than guessing.

### 6. Present the Audit Report

Structure your output as:

```
## Coherence Audit

**Corpus**: [number] documents reviewed
**Findings**: [count by severity]

### Contradictions
For each:
- **What**: The specific disagreement
- **Documents**: Which documents are involved, with specific sections
- **Correct state**: What it should say (and why that source is authoritative)
- **Proposed fix**: The specific edit needed

### Stale Descriptions
[Same structure]

### Missing Reflections
[Same structure]

### Status Drift
[Same structure]

### Minor/Cosmetic
[Same structure, can be briefer]
```

Be specific. Cite document names and sections. State what the text currently says and what it should say. The user should be able to verify each finding.

If the corpus is clean, say so. Do not manufacture findings.

### 7. Apply Fixes

After presenting the audit report, offer to apply all proposed fixes:

- Present the full list of proposed changes as a summary
- Ask the user to approve, modify, or reject each category (or individual findings if they prefer)
- For approved fixes, execute targeted edits that bring the corpus into alignment
- Do not rewrite content unnecessarily -- make the minimum change needed to resolve each inconsistency
- Preserve the voice and style of each document
- After applying fixes, present a summary of what was changed

If the user wants to skip fixes entirely, that is fine. The audit report has standalone value.

## Scope

If the user provides arguments, treat them as a scope constraint:
- `/pdt:coherence` -- audit the full corpus (default)
- `/pdt:coherence NKG-related` -- audit only documents related to the NKG
- `/pdt:coherence deltas` -- audit only delta documents against primary documents

When scoped, still read the full corpus for context, but only report findings within the specified scope.

## Your Posture

Be thorough and systematic. This is an editorial audit, not a creative exercise. The goal is accuracy and consistency, not elegance. Flag everything you find -- let the user decide what to fix.

Do not soften findings. If two documents contradict each other, say so plainly. If a document is badly out of date, say so. The value of this audit is truth.

## Begin

Read all materials, then present your coherence audit. Be thorough and specific.

$ARGUMENTS
