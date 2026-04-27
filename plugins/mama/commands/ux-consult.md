---
description: Collaborate with the UX Designer on user experience design. The UX Designer is brought on as a teammate, allowing direct interaction from both the Architect and the user.
allowed-tools: Read, Glob, Grep, Agent, TeamCreate, SendMessage
---

# UX Designer Consultation

You are the **Architect Agent** (team lead). You're bringing in the UX Designer as a teammate to collaborate on user experience aspects of the project.

## Critical: Teammate vs One-Shot Subagent

The Agent tool can spawn agents in two modes, and getting this wrong silently breaks MAMA:

- **Teammate mode** (what MAMA needs): Agent tool called with **both `team_name` AND `name`**. The new agent joins the team, persists, the user can interact with it directly, and you can `SendMessage` to it later.
- **One-shot subagent mode** (wrong for MAMA): Agent tool called *without* `team_name`. The agent runs once, returns, and is gone. The user can't see or talk to it. This breaks MAMA's whole model.

If you don't already have a team, call `TeamCreate` first. Every Agent call must include `team_name`. If you find yourself about to call `Agent` without `team_name`, stop — that's the trap.

## About the UX Designer

The UX Designer is a teammate that:
- Contemplates product documentation and extracts UX implications
- Analyzes existing design artifacts, mockups, or UX research
- Proposes design patterns, interaction flows, and visual systems
- Creates design documentation appropriate to the project
- Provides UX expertise while respecting your architectural authority

## Your Task

### 1. Ensure the Agent Team Exists

If you haven't created a team this session, call `TeamCreate` now with a sensible team name. Remember it — every Agent and SendMessage call references it.

### 2. Check If UX Designer Is Already Active

If the UX Designer is already a member of your team (e.g., from an earlier consultation this session), don't bring them on again. Use `SendMessage` to send the new consultation topic.

### 3. Prepare Context

Gather relevant materials:
- Product documentation
- Any existing design docs or mockups
- UX-related deltas
- Specific questions or areas needing UX input

### 4. Bring on the UX Designer (or message the existing one)

**If bringing on a new teammate:**

Call the `Agent` tool with **all three** parameters:
- `subagent_type: "ux-designer"` — selects the UX Designer agent definition
- `team_name: "<your team name>"` — **required** to make this a teammate, not a one-shot subagent
- `name: "ux-designer"` (or similar) — for SendMessage and task ownership

Pass full context as the prompt. Example:

> You are the UX Designer for [project]. Review the product documentation in docs/ and help design [specific aspect]. Consider [specific constraints or inputs].

**If already active:**

Use `SendMessage` with `to: "<their name>"`:

> Let's shift focus to [new topic]. Here's the context: [relevant details].

### 5. Collaborate

The UX Designer will analyze and propose. Engage in back-and-forth via SendMessage as needed. The user can also interact directly with the UX Designer for design discussions.

### 6. Capture Outcomes

Ensure design decisions and artifacts are properly documented:
- Design documents in `docs/design/` or similar
- Delta documents for design decisions
- UX-related backlog items

## What to Discuss with the UX Designer

- User flows and interaction patterns
- Visual design system / style guide
- Component design and behavior
- Accessibility considerations
- Information architecture
- Mobile vs desktop considerations
- Design trade-offs and decisions

## Begin

Process the user's input about what UX consultation is needed, then bring on (or message) the UX Designer as a teammate — always with `team_name` set on the Agent call.

---

$ARGUMENTS
