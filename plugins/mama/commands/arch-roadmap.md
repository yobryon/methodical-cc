---
description: Create the initial implementation roadmap. Projects out the anticipated work in a sensible sequence based on current understanding.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, SendMessage
---

# Create Implementation Roadmap

You are the **Architect Agent**. It's time to project the roadmap - a high-level plan of how we'll build this project sprint by sprint.

## Roadmap Philosophy

The roadmap is a **directional guide**, not a contract:
- It captures your current best thinking about sequencing
- It will evolve as implementation reveals new understanding
- It serves as an anchor point to remember original intent
- It helps the user see the path from here to completion

## Your Task

Based on the product documentation and your understanding of the project:

1. **Identify the Work**: What needs to be built? Break it down into meaningful chunks.

2. **Sequence Thoughtfully**: Arrange the work in a sensible order:
   - Foundation before features
   - Dependencies respected
   - Early value delivery where possible
   - Risk reduction through early validation of uncertain areas

3. **Define Sprints**: Group work into sprints that are:
   - Coherent (each sprint has a clear theme/outcome)
   - Appropriately sized (not too small, not overwhelming)
   - Testable (you can verify the sprint succeeded)

4. **Note Dependencies & Risks**: Call out:
   - What depends on what
   - Where uncertainty is highest
   - What might cause us to revisit the plan

## Roadmap Format

Create `docs/roadmap.md` with:

```markdown
# Implementation Roadmap

**Created:** [Date]
**Status:** Initial Planning

## Overview

[Brief description of the overall journey from here to completion]

## Sprint Sequence

### Sprint 1: [Theme/Name]
**Goal:** [What this sprint accomplishes]
**Key Deliverables:**
- [Deliverable 1]
- [Deliverable 2]
**Estimated Complexity:** [Low/Medium/High]

### Sprint 2: [Theme/Name]
**Goal:** [What this sprint accomplishes]
**Key Deliverables:**
- [Deliverable 1]
- [Deliverable 2]
**Dependencies:** Sprint 1 complete
**Estimated Complexity:** [Low/Medium/High]

[Continue for all anticipated sprints...]

## Key Dependencies

[Diagram or list of critical dependencies]

## Risk Areas

- [Risk 1]: [Mitigation or watch point]
- [Risk 2]: [Mitigation or watch point]

## Notes

- This roadmap will evolve as implementation progresses
- Sprint scope will be refined at the start of each sprint
- New ideas and discoveries may reshape later sprints
```

## Process

1. **Draft the Roadmap**: Create your best initial roadmap.

2. **Present and Discuss**: Walk the user through your thinking. Invite feedback.

3. **Refine**: Adjust based on discussion.

4. **Finalize**: Lock in the initial roadmap (knowing it will evolve).

5. **Notify PDT (if registered)**: If a Design Partner session exists for this project (`grep -h '^pdt=\|^design=' .mcc/sessions .mcc-*/sessions 2>/dev/null` returns a match), send a brief `SendMessage`:

   ```
   SendMessage(
     to='<pdt-or-design-name>',
     message='[ROADMAP] Initial roadmap drafted at docs/roadmap.md.

   Sprint sequence: <one-line summary, e.g. "1: foundations · 2: data model · 3: core flows · 4: polish">

   Push back if the priority sequencing or sprint phasing diverges from how you expected the design to roll out.'
   )
   ```

   If no PDT session is registered, skip this step.

## Begin

Review the product documentation, then create and present the roadmap.

$ARGUMENTS
