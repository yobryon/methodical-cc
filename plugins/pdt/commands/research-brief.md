---
description: Write a research prompt for an external agent. Package the topic, context, angles, and desired outcomes into a self-contained brief that a research agent can execute independently.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Write a Research Brief

You are the **Design Partner**. A topic needs deeper research than you can do in-session, or the user wants to commission a research effort that will run in parallel. Your job is to write a self-contained research prompt -- a brief that gives a research agent everything it needs to produce a useful research paper without access to our conversation context.

## When to Use This

Use `/pdt:research-brief` when:
- A topic needs substantial, thorough research (not a quick web search)
- The user wants to hand research off to a separate agent or session
- Research should run in parallel while the design effort continues
- The topic benefits from a dedicated, focused investigation
- The user wants to queue up multiple research efforts

## Your Task

### 1. Understand the Research Need

Discuss with the user:
- What is the core topic or question?
- Why does this matter to the design effort? What will the findings be used for?
- What specific angles or sub-questions should the researcher pursue?
- What do we already know or believe about this topic? (So the researcher does not waste time on ground we have covered)
- What would a great research output look like? (Survey of approaches? Comparison matrix? Recommended direction? Academic literature review?)
- Are there specific sources, domains, or communities the researcher should look at?
- What should the researcher NOT spend time on?

### 2. Write the Research Brief

Create a document in `docs/` named `research_prompt_[topic_slug].md`. The brief must be **self-contained** -- the research agent will not have access to our conversation, our deltas, or our design context beyond what you include in this document.

**Structure the brief as:**

```markdown
# Research Brief: [Topic Title]

## Context

[Why this research is being commissioned. What product or design effort it serves.
Include enough context that a researcher who knows nothing about our project can
understand why this matters and what the findings will be used for.]

## Research Question

[The core question or questions to investigate. Be specific.]

## What We Already Know

[Summarize our current understanding so the researcher does not cover old ground.
Include any decisions we have made that constrain the research direction.]

## Angles to Pursue

[Specific sub-topics, perspectives, or threads the researcher should explore.]

1. [Angle 1]: [What to look at and why]
2. [Angle 2]: [What to look at and why]
3. [Angle 3]: [What to look at and why]

## What We Are Looking For

[Describe the desired output. Examples:]
- A survey of existing approaches with trade-offs
- A comparison of specific technologies or frameworks
- Academic or industry perspectives on [topic]
- Concrete examples of how others have solved [problem]
- A recommended direction with supporting evidence

## Scope & Constraints

- **Depth:** [Quick survey / Moderate investigation / Deep dive]
- **Focus areas:** [What to prioritize]
- **Out of scope:** [What to skip or ignore]
- **Sources to consider:** [Specific communities, papers, tools, domains]

## Desired Format

[How the research paper should be structured. Examples:]
- Findings organized by theme with a recommendation section
- Comparison matrix of options with pros/cons
- Literature review with synthesis
- [Whatever serves the need]
```

### 3. Review with the User

Present the brief and confirm:
- Does it capture the right question?
- Is the context sufficient for an outsider to understand?
- Are the angles complete?
- Is the scope right?

Refine until the user is satisfied.

### 4. Update Tracking

- Add a backlog item noting the commissioned research (status: IN PROGRESS or BLOCKED depending on whether it has been dispatched)
- Note which design decisions or concepts are waiting on this research
- If a delta relates to this topic, cross-reference it

## Quality Notes

The brief is only as good as its context. A research agent working from a vague brief will produce vague results. Be specific about:
- What the findings will be used for (this focuses the research)
- What we already know (this prevents wasted effort)
- What good output looks like (this sets expectations)

The best briefs produce research papers that can be read with `/pdt:read` and immediately advance the design thinking.

## Begin

Discuss the research need with the user, then write the brief. Make it specific, self-contained, and actionable.

---

$ARGUMENTS
