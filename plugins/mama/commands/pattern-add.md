---
description: Propose a project pattern for CLAUDE.md. Gates aggressively — most proposals shouldn't land. When something does land, write it as a tight one/two-line principle, not a sprint-history paragraph.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Add/Update Project Pattern

You (Architect or Implementor) want to capture a pattern in `CLAUDE.md`.

`CLAUDE.md` is auto-loaded into **every** session in this project — every Architect, every Implementor, every PDT consult, forever. That makes it expensive prompt material, not free-form documentation. Treat additions as a privilege, not a habit.

## The Default Answer Is No

Before drafting anything, run the proposal through these gates. If any answer is "yes" or "unclear," push back on the addition.

1. **Is the rule already enforced by a test, type, lint rule, or build script?**
   If yes — the test/type/rule **is** the pattern. CLAUDE.md doesn't need to re-state it. (At most: a one-line pointer naming where the rule lives.)

2. **Does this duplicate content already in `sprint_log.md`, a delta, `decisions_log.md`, or `concept_backlog.md`?**
   If yes — it belongs there, not here. Sprint history goes in the sprint log. Design rationale goes in decisions. Future-work hints go in the backlog. CLAUDE.md is for *active rules every session needs*.

3. **Would a fresh Claude session six sprints from now actively *miss* something if this weren't in CLAUDE.md?**
   Not "would it be nice to have," but: would they make a wrong call without it?
   If no — defer. If you're unsure, defer. Things that aren't load-bearing rot into noise.

4. **Is this a sprint-specific lesson, hotfix backstory, or diagnostic journey?**
   If yes — it's history, not policy. The sprint log holds those. CLAUDE.md is forward-facing.

If all four gates clear, proceed. Surface the gating outcome to the user briefly ("This passes the gates because: …") so they can push back.

## Style — Tight Principles, Not Paragraphs

When something does belong in `CLAUDE.md`, write it as a one- or two-line principle:

- **Lead with the rule.** One declarative sentence. The reader should grok it from the lead.
- **Optional second line:** the *why* in a phrase, OR a *where* (file/function reference). Not both.
- **Cap at 3 lines per bullet.** If you need more, the rule isn't crisp enough yet — sharpen it.
- **Skip diagnostic backstory.** "Sprint 14 hotfix B's bare KeyboardSensor removal …" belongs in the sprint log. The rule is what survives.
- **Sprint references only when the codification is fresh** (within ~5 sprints) AND tracing back actually helps a reader understand the *current* state. Strip them otherwise.
- **Group related bullets into topic sections** (Build & Runtime, Testing, Architecture, etc.). Don't dump bullets flat.

### Good

> ### Testing
> - Component tests live under `src/components/<name>/__tests__/`.
> - Use `userEvent` over `fireEvent` for keyboard/pointer interactions; `fireEvent` skips intermediate browser events that real users trigger.

### Bad

> ### Testing
> - In Sprint 14 we discovered that `fireEvent` was dropping intermediate events because of how the dnd-kit KeyboardSensor handles keyDown/keyUp ordering. After hotfix B (which removed the bare KeyboardSensor and replaced it with a wrapped variant), we updated tests to use `userEvent` for all interactions involving keyboard or pointer. The reasoning is that …

(That's a sprint log entry.)

## Handling Conflicts

If the new pattern conflicts with an existing one, surface the conflict, discuss which takes precedence, and update or remove the old pattern. Don't accumulate contradictions.

## Your Task

1. **Run the four gates above.** If any "yes/unclear," explain why and push back rather than adding.
2. **If the gates clear,** discuss the pattern with the user briefly to confirm wording.
3. **Write it in tight-principle style** to the appropriate `CLAUDE.md` section.
4. **Show the diff** so the user can confirm.

## Begin

Run the proposal through the gates. Default to *no*. If it clears, write it tight.

---

$ARGUMENTS
