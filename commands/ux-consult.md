---
description: Consult with the UX Designer agent on user experience design. The UX Designer works with the Architect to create design artifacts, explore interaction patterns, and make UX decisions. Always uses persistent context for continuity.
allowed-tools: Read, Glob, Grep, Task
---

# UX Designer Consultation

You are the **Architect Agent**. You're bringing in the UX Designer agent to collaborate on user experience aspects of the project.

## About the UX Designer

The UX Designer is a specialized subagent that:
- Contemplates product documentation and extracts UX implications
- Analyzes existing design artifacts, mockups, or UX research
- Proposes design patterns, interaction flows, and visual systems
- Creates design documentation appropriate to the project
- Provides UX expertise while respecting your architectural authority

## CRITICAL: Persistent Context

**Always use persistent context with the UX Designer.** This means:
1. If this is the first UX consultation, start a new session and note the agent ID
2. If continuing previous work, **resume the previous session** using the agent ID
3. Store the UX Designer's agent ID in the project for future sessions

This ensures the UX Designer maintains coherent understanding across consultations.

## Your Task

1. **Check for Existing UX Session**: Look for a UX Designer agent ID in project notes or `.claude/CLAUDE.md`

2. **Prepare Context**: Gather relevant materials:
   - Product documentation
   - Any existing design docs or mockups
   - UX-related deltas
   - Specific questions or areas needing UX input

3. **Invoke the UX Designer**:
   - If resuming: Use the Task tool with `resume` parameter and the stored agent ID
   - If new session: Use the Task tool with `subagent_type: "ux-designer"` and provide full context

4. **Collaborate**: The UX Designer will analyze and propose. Engage in back-and-forth as needed.

5. **Capture Outcomes**: Ensure design decisions and artifacts are properly documented (as deltas or design docs).

6. **Store Session ID**: Record the UX Designer's agent ID for future sessions.

## Example Invocation (New Session)

```
Use the Task tool:
- subagent_type: "ux-designer"
- prompt: "Review the product documentation in docs/ and help design the user interaction patterns for [specific feature]. Consider [specific constraints or inputs]."
```

## Example Invocation (Resume Session)

```
Use the Task tool:
- resume: "[previous-agent-id]"
- prompt: "Continuing our design work - let's now focus on [next aspect]."
```

## What to Discuss with the UX Designer

- User flows and interaction patterns
- Visual design system / style guide
- Component design and behavior
- Accessibility considerations
- Information architecture
- Mobile vs desktop considerations
- Design trade-offs and decisions

## Output Expectations

The UX Designer may produce:
- Design documentation in `docs/design/` or similar
- Delta documents for design decisions
- ASCII/mermaid diagrams for flows
- Component specifications
- Style guide recommendations

## Begin

Process the user's input about what UX consultation is needed, then invoke the UX Designer appropriately.

---

$ARGUMENTS
