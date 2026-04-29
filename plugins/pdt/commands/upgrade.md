---
description: Brief the Design Partner on methodology changes when upgrading to a new PDT version. Currently covers the pre-2.0.0 → 2.0.0 transition (bus-based crossover with MAM/MAMA).
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# PDT Upgrade

You are the **Design Partner**. This command briefs you on methodology changes that came with new PDT versions, so you (and any accumulated state in this project) can re-orient your thinking accordingly.

PDT doesn't have versioned state directories the way MAM/MAMA do — there's no on-disk migration. This command's job is purely to **update your mental model** of how PDT works given changes since the last time you (or a prior session) operated in this project.

Upgrades are **cumulative**: if you're several versions behind, work through each transition in order.

## Your Task

### 1. Determine Current Version

Ask the user what PDT version they were last using on this project (if known). If unsure, default to "pre-2.0.0" — the transition below applies to anyone whose mental model predates the bus.

### 2. Apply Transitions

Walk through each applicable transition with the user, then internalize it.

---

#### Transition: pre-2.0.0 → 2.0.0 — Crossover via the Bus

**What changed.** PDT and MAM/MAMA used to communicate through discrete files in `docs/crossover/` (`commission_NNN_request.md`, `consult_NNN_request.md`, `debrief_NNN.md`), with the user as the manual courier between sessions. Starting in v2.0.0, that crossover happens over the **bus** plugin — a Channels-based MCP server that lets sessions message each other directly.

**What still works.**
- Existing flat crossover files (`commission_NNN_*.md`, `consult_NNN_*.md`, `debrief_NNN.md`) remain valid history. They're readable, citable, and part of the project's record. Don't delete or migrate them unless the user explicitly asks.
- The conceptual structure — commissions, consults, debriefs — is unchanged. The same kinds of work flow between PDT and the Architect.

**What's different now.**
- Sending: commands like `/pdt:commission` now call `peer_send(to='arch', mode='consult', ...)` instead of writing a request file
- Receiving: when the Architect sends a consult or debrief, you receive a `<channel from='arch' mode='consult' ...>` notification automatically — no polling for new files
- Storage: new crossover lives in **thread directories** at `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md` (one directory per ongoing thread, sequentially numbered turns)
- Threading: each conversation has a sender-declared kebab-case `thread_id` (e.g. `consult-013-pref-storage-shape`); responses go on the same thread to keep the conversation linked
- Identity: you're addressable on the bus by your registered session name — set via `/pdt:session set <name>` (typically `design` or similar)

**Action items for the user.**
1. Install and enable the bus plugin if not already: `mcc bus setup` in this project's directory
2. Register PDT's session identity: `/pdt:session set design` (or another name they prefer) — this becomes your bus identity
3. Verify the Architect's session has registered an identity too (typically `arch`) — `peer_list` will show registered identities once both sides are set up
4. Note: Channels are in research preview — Claude Code must be launched with `--dangerously-load-development-channels plugin:bus@methodical-cc` for the bus to function

**Reorientation cue for you (the agent).**
- If your accumulated state references the file-based pattern (e.g., `concept_backlog.md` mentions waiting for `commission_NNN_response.md`), that's legacy context. The current behavior follows the bus protocol. When you next interact with the Architect, use `peer_send` rather than writing crossover files directly.
- If you find yourself about to write a `consult_NNN_request.md` file: stop. Use the bus. Old files stay where they are; new ones go through `peer_send`.
- The `bus-protocol` skill (in the bus plugin) covers the full protocol — modes (chat vs consult), threading conventions, response composition discipline. Read it if you need the full reference.

**Verify the bus is working.**
- After setup, run `peer_list` (the bus MCP tool) — it should show registered identities and any pending messages
- Check the SessionStart context for the `=== METHODICAL-CC BUS ===` block — it shows your resolved identity, active threads, and unread counts at session start

---

*Future transitions will be added here as the methodology evolves.*

---

### 3. Present Summary

After working through applicable transitions:
- Confirm with the user which transitions applied
- Note any action items still pending (e.g., "you still need to run `mcc bus setup` and `/pdt:session set design`")
- Offer to proceed with `/pdt:resume` next so you can re-establish full project context with the new methodology in mind

## Begin

Discuss the project's PDT version history with the user, then walk through applicable transitions.

$ARGUMENTS
