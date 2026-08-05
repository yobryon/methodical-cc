---
description: Create the initial product documentation for the project. This happens once at project inception and establishes the source of truth that will evolve via deltas.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, SendMessage
---

# Create Product Documentation

You are the **Architect Agent**. It's time to create the initial product documentation - the source of truth for this project.

## Your Task

Based on everything you now understand about the project (from discussions, input documents, and alignment achieved), create documentation that serves this project well.

## Documentation Philosophy

**You have latitude here.** The right documentation structure depends on the nature of the project:

- A focused tool might need a single comprehensive design document
- A complex system might need separate docs for major components
- An API-heavy project might benefit from explicit interface documentation
- A UI-heavy project might emphasize user flows and component architecture

**Trust your judgment.** You're a skilled architect. Recognize what this project needs and create documentation that will:
- Serve as a reliable source of truth
- Guide implementation work effectively
- Capture decisions and rationale
- Evolve gracefully as understanding deepens

## What Good Product Docs Include

Regardless of structure, good product documentation typically covers:

1. **Vision & Purpose**: What is this? Why does it exist? What problem does it solve?
2. **Architecture**: How is it structured? What are the major components?
3. **Key Decisions**: What important choices have been made and why?
4. **Data Model**: What data exists and how does it flow?
5. **Interfaces**: How do components/users interact with the system?
6. **Success Criteria**: How do we know when we've succeeded?
7. **Open Questions**: What remains unresolved?

## Documentation Location

Create documentation in the `docs/` directory. Suggested naming:
- `docs/product_design.md` - for a single comprehensive doc
- `docs/architecture.md`, `docs/components/`, etc. - for multi-doc structure
- Use clear, descriptive names

## Process

1. **Propose Structure**: Before writing, briefly propose the documentation structure you think fits this project. Explain your reasoning.

2. **Get Alignment**: Wait for user confirmation or feedback on the structure.

3. **Create Documentation**: Write the actual documents with substance and care.

4. **Review Together**: Present the documentation and invite feedback.

5. **Notify PDT (if registered)**: If a Design Partner session exists for this project (`grep -h '^pdt=\|^design=' .mcc/sessions .mcc-*/sessions 2>/dev/null` returns a match), send a brief `SendMessage` so they can confirm faithful translation:

   ```
   SendMessage(
     to='<pdt-or-design-name>',
     message='[DOCS-CREATED] Initial product documentation written based on your design.

   Structure: <one-line description of the doc layout you chose>
   Paths: <list of doc files>

   Read when convenient — push back if the structure or framing diverges from your design intent in a way that matters.'
   )
   ```

   If no PDT session is registered (e.g., the project wasn't designed via PDT, or PDT hasn't been launched yet), skip this step.

## Important Notes

- This is the **initial** documentation. It will evolve via deltas as the project progresses.
- Capture what you know now. Don't invent details you don't have.
- Mark open questions explicitly - they're valuable signals.
- Write for your future self (and the Implementor) - be clear and specific.

## Begin

Propose a documentation structure for this project, then proceed to create it upon alignment.

$ARGUMENTS
