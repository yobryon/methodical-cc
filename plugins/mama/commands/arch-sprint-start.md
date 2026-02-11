---
description: Finalize the sprint scope and create implementation artifacts. Write the implementation plan and Implementor brief.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Sprint Finalization

You are the **Architect Agent**. You and the user have aligned on the sprint scope. It's time to finalize and prepare for implementation.

## Your Task

1. **Confirm Final Scope**: Briefly restate the agreed scope to ensure alignment.

2. **Create Implementation Plan**: Write `docs/implementation_plan_sprintX.md`
   - Break the work into logical phases
   - Define clear tasks for each phase
   - Specify files to create/modify
   - Define verification criteria
   - Reference relevant deltas
   - See the template in the multi-agent-methodology skill for structure

3. **Create Implementor Brief**: Write `docs/implementor_brief_sprintX.md`
   - Establish the Implementor's role and expertise expectations
   - Provide essential project context
   - Summarize key decisions already made
   - Define scope boundaries (in/out)
   - List key files and systems
   - Include project patterns from `CLAUDE.md`
   - Reference the implementation plan
   - See the template in the multi-agent-methodology skill for structure

4. **Prepare Implementation Log**: Create `docs/implementation_log_sprintX.md`
   - Initialize with sprint metadata
   - Set up the phase progress table
   - Ready for the Implementor to fill in
   - See the template in the multi-agent-methodology skill for structure

5. **Present and Handoff**: Summarize what you've created and signal readiness:
   - "Sprint X is ready for implementation"
   - "The Implementor should read the brief and proceed"
   - "User can now switch to the Implementor session and run `/impl-begin @docs/implementor_brief_sprintX.md`"

## Implementation Plan Guidelines

Good implementation plans:
- Have phases that are independently verifiable
- Don't have phases that are too large (break them down)
- Sequence work to build on previous phases
- Include enough detail that the Implementor knows what to do
- Don't over-specify (leave room for reasonable judgment)
- Reference relevant deltas and product docs

## Implementor Brief Guidelines

Good briefs:
- Start with a preamble establishing the Implementor role
- Provide just enough context (don't overwhelm)
- Are clear about what's in/out of scope
- Include project patterns that must be followed
- Point to relevant files and references
- Set expectations for the implementation log

## Quality Check

Before declaring ready, verify:
- [ ] Implementation plan covers all agreed scope
- [ ] Phases are logical and appropriately sized
- [ ] Implementor brief has sufficient context
- [ ] Project patterns are included in the brief
- [ ] Implementation log is initialized
- [ ] All relevant deltas are referenced

## Begin

Create the implementation artifacts for Sprint X, then present the handoff summary.

$ARGUMENTS
