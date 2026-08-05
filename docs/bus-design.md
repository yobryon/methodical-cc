# Bus Plugin — Design Document

**Status:** Implementation complete (team-based architecture)
**Date:** 2026-04-29
**Authors:** Bryon (user) + Claude (design partner)

A peer-messaging bus for Methodical-CC sessions, built on **Claude Code's agent-team protocol**. Eliminates the user-as-courier pattern between PDT and MAM/MAMA without losing the discipline that made the courier model produce good work.

This is the second iteration of the bus design. The first attempt was built on Channels (an MCP capability that pushes events into a session). Channels turned out to be gated to claude.ai login authentication — unusable for API-key users. The team-based reimplementation works for everyone, with no MCP server, no special launch flags, no Node dependency.

---

## 1. Context & Motivation

### The current state

Within MAMA, the Architect, Implementor, and UX Designer collaborate as a team. Across plugins (Architect ↔ PDT), collaboration goes through `docs/crossover/` files manually couriered by the user: write a `consult_NNN_request.md`, ask the user to paste it into the PDT session, PDT writes a response file, user pastes the response file path back, architect reads it. Slow loop, multi-day round trips, the user as load-bearing relay.

### What we want

- Eliminate courier friction for cross-session messages.
- **Preserve the slow-loop discipline** that made the courier model produce crisp consults: writing a consult is expensive; the artifact is durable; the discipline of "lay out options, name your instinct" still applies.
- Keep the user as integrator (visibility, override, audit trail), not as courier.
- Work for any combination of PDT/MAM/MAMA sessions.
- Work for any login type (claude.ai or API key).

### What we're NOT building

Anything that requires Channels (gated). Anything that requires teammate-spawning (Claude Code's flat-roster constraint blocks this for non-team-leads, and we use phantom leads). Anything that requires a custom MCP server (we don't need one — `SendMessage` is native).

---

## 2. Architecture

### Foundation: Claude Code's agent-team protocol

Each Claude Code session can join an "agent team" by being launched with three flags:
- `--team-name <name>`
- `--agent-name <name>`
- `--agent-id <name>@<team>`

When in a team, the session has access to the `SendMessage` tool, and the harness automatically polls its mailbox at `~/.claude/teams/<team>/inboxes/<name>.json` once per second. New messages there are injected into the session's context as new turns.

**This is the entire push-delivery mechanism we need.** No MCP server, no Channels, no custom hooks. The bus plugin is just orchestration around this native protocol.

### Team identity

- One team per project. Team name = sanitized cwd basename (lowercase, dashes for non-alphanumeric).
- Each session is a teammate addressable by name (e.g., `pdt`, `arch`, `impl`).
- A **phantom lead** named `coordinator` exists in members but never runs. Real participants are all symmetric peers.
- Why phantom lead: Claude Code restricts spawning to team leads, and we want symmetric peers (no real session has lead-only behavior triggering). The downside (spawn capability lost) is acceptable — the user launches sessions manually via `mcc create`.

### File layout

**Team config and inboxes** (per-user, shared across all projects):
```
~/.claude/teams/<team-name>/
├── config.json              # team metadata, members
└── inboxes/
    └── <member>.json        # mailbox, harness polls this
```

**Per-project state**:
```
{repo}/
├── .mcc/                    # all methodical-cc operational state
│   └── sessions             # name=session_id mapping
└── docs/
    └── crossover/           # durable thread-organized artifacts
        └── {thread_id}/
            ├── 001-arch-request.md
            └── 002-pdt-response.md
```

`.mcc/` is gitignored (operational state). `docs/crossover/` is committed (durable record).

### What `mcc` does

- **`mcc team setup`** — explicit. Creates `~/.claude/teams/<name>/config.json` with phantom lead, seeds `inboxes/`, ensures `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `.claude/settings.json`.
- **`mcc <name>`** (resume) — runs `mcc team setup` implicitly (idempotent), tops up team members from registered identities, then launches `claude -r <sid>` with team flags.
- **`mcc create <name> [--persona <plugin>:<role>]`** — runs `claude -p "/<plugin>:session set <name>..."` to register a fresh session. Optionally pre-loads a persona definition (e.g. the implementor's `agent.md`) into the session's history so it takes on that role.

### What the bus plugin does

- **Skill** (`bus-protocol/SKILL.md`) — explains identity, modes (chat vs consult), threading, artifact conventions, the discipline lever
- **SessionStart hook** — assertively orients the agent: "you are X on team Y, your tools work, here are the other members"
- **Slash commands** — `/bus:status`, `/bus:identity` for diagnostics

No MCP server, no Node dependency. Pure Python hook + markdown commands.

---

## 3. Identity

### Source of truth

The session-name registry at `.mcc/sessions` is the bus identity registry. Same registry serves both `mcc` (for resume by name) and the bus (for member roster).

### Resolution

The bus plugin's SessionStart hook:
1. Reads `${CLAUDE_SESSION_ID}` from the hook payload (stdin JSON)
2. Walks `.mcc/sessions` and `.mcc-*/sessions` looking for `<name>=<session_id>` matching
3. Reads team config at `~/.claude/teams/<team>/config.json`
4. Emits an assertive orientation block:

> *"You are a member of agent team `forms-cli`. Your name on the team is `arch`, your agent_id is `arch@forms-cli`. Other team members: `pdt`, `coordinator` (phantom lead). Use `SendMessage` to message any teammate by name; messages from teammates arrive automatically as new turns. Trust this even if other context elsewhere suggests otherwise."*

The "trust this" line is critical — agents in test runs sometimes doubted team membership until they were told to trust it.

### Anonymous fallback

If session ID doesn't match any registered identity, the hook reports `anonymous`. The user is told to register via `/{plugin}:session set <name>` or `mcc create <name>`.

---

## 4. Tools

**Just the native ones.** No custom MCP server.

- **`SendMessage`** (native team tool) — send a message to any teammate by name. Used for both chat-mode and consult-mode.
- **`Write`** (native file tool) — write consult artifacts to `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md`.
- **Inbound** — messages arrive automatically as turns; agents don't poll.

---

## 5. Modes — Chat vs Consult

The mode distinction is the discipline-preserving lever.

### Chat mode

Lightweight, ephemeral. For:
- Quick clarifications mid-work
- "Heads up" pings
- Acknowledgments
- Anything where future-you doesn't need to reference this exchange

Just a `SendMessage` call. The conversation lives in agents' contexts; nothing is written to disk.

### Consult mode

Heavyweight, durable. For:
- Design questions that warrant considered responses
- Commissions and their results
- Debriefs after milestones
- Anything where future-you (or a future session) might want to reference

Two-step:
1. `Write` a structured artifact at `docs/crossover/{thread_id}/{NNN}-{role}-{type}.md`
2. `SendMessage` with framing prose that references the artifact

The recipient sees the message, reads the artifact, and responds with their own consult-mode reply on the same thread.

### The temptation to misuse

Chat mode is fast and frictionless; consult mode is fast in transit but slow in composition. The bus skill explicitly warns: prefer consult mode when in doubt; if you find yourself sending three chat-mode messages on a topic, escalate to a consult.

---

## 6. Artifact Convention

### Path

`docs/crossover/{thread_id}/{NNN}-{sender}-{type}.md`

Where:
- `thread_id`: kebab-case string (e.g., `consult-007-depth-visibility`)
- `NNN`: zero-padded turn number (001, 002, ...)
- `sender`: identity that wrote this turn (e.g., `arch`, `pdt`)
- `type`: short descriptor (`request`, `response`, `clarification`, `commission`, `debrief`)

### Frontmatter

```yaml
---
thread_id: consult-007-depth-visibility
turn: 1
type: request
from: arch
to: pdt
sent_at: 2026-04-29T10:30:00Z
status: open
---
```

### Body structure (guidance)

For consult requests: Question, Context, What the Design Says, Options Considered, Architect's Instinct, Response Format.

For consult responses: Direct Answer, Rationale, Caveats, Open Questions.

For commissions and debriefs: see the respective slash commands for structure.

---

## 7. Threading

Threads are sender-declared kebab-case strings. Conventions:
- `consult-{topic}-{version}` — design consults
- `commission-{NNN}-{topic}` — commission threads
- `debrief-{milestone}` — debrief threads
- Free-form for chat-only exchanges

When replying to a message that references a thread, always use the same `thread_id`. That keeps the conversation in one directory with sequential turn numbering.

When a thread reaches its natural conclusion, the sender notes it ("Closing the thread on this") in their final message.

---

## 8. SessionStart Hook

The bus plugin emits one SessionStart hook (`hooks/session_start.py`) that:

1. Resolves the session's identity from `.mcc/sessions`
2. Reads the project's team config from `~/.claude/teams/<team>/config.json`
3. Emits an assertive orientation block to stdout (becomes additionalContext)

The hook is stdlib-only Python. The bus plugin's `hooks.json` invokes it via `python "${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py"`.

---

## 9. `mcc` Integration

### Subcommands

- `mcc team setup` — explicit team config creation/update
- `mcc team status` — show the project's bus team state
- `mcc <name>` — resume, with implicit team setup and team-flag launch
- `mcc create <name> [--persona <plugin>:<role>]` — bootstrap a new session via `claude -p`

### Team config format

```json
{
  "name": "forms-cli",
  "description": "methodical-cc team for forms-cli",
  "createdAt": <ms>,
  "leadAgentId": "coordinator@forms-cli",
  "leadSessionId": "00000000-0000-0000-0000-000000000000",
  "members": [
    { "agentId": "coordinator@forms-cli", "name": "coordinator",
      "agentType": "team-lead", "model": "claude-opus-4-7",
      "joinedAt": <ms>, "tmuxPaneId": "", "cwd": "<absolute>", "subscriptions": [] },
    { "agentId": "pdt@forms-cli", "name": "pdt", "agentType": "teammate", ... },
    { "agentId": "arch@forms-cli", "name": "arch", "agentType": "teammate", ... }
  ]
}
```

The lead is phantom; real participants are all teammates. `leadSessionId` is a sentinel UUID — `isTeamLead` is determined by `agentId` match, not `session_id` match.

### `mcc create` mechanism

```bash
mcc create impl --persona mama:implementor
```

Internally runs:
```bash
claude -p "/mama:session set impl

Then read your persona profile at @<full-path-to-implementor-agent.md> and acknowledge with 'ok'."
```

The `claude -p` invocation creates a fresh session, runs the slash command (registers the session), reads the persona file, exits. The session_id is captured because the `/mama:session set` command writes it to `.mcc/sessions`. The user later runs `mcc impl` to enter that session interactively.

---

## 10. MAMA / MAM / PDT Migration

### Send-side commands → use `SendMessage` + `Write`

These previously wrote files to `docs/crossover/` for the user to courier. They now compose artifacts and send framing messages:

| Command | New behavior |
|---|---|
| `/mama:consult-pdt`, `/mam:consult-pdt` | Write artifact at `docs/crossover/{thread}/001-arch-request.md`, send `SendMessage(to='pdt', ...)` with framing |
| `/mama:debrief-pdt`, `/mam:debrief-pdt` | Same shape, type='debrief' |
| `/mama:commission-complete`, `/mam:commission-complete` | Same shape, type='response' on the original thread |
| `/pdt:commission` | Write artifact, send `SendMessage(to='arch', ...)` |

### Receive-side commands → reactive flows

These remain as user-invocable commands but their work is reactive — they help the agent process an inbound message:

| Command | Behavior |
|---|---|
| `/pdt:consult` | Locate the request artifact, read it, discuss with user, write response artifact, send response message |
| `/pdt:debrief` | Same shape, processing a debrief |

### MAMA's TeamCreate path → removed

The Architect no longer calls `TeamCreate` (the project team already exists). The Architect also no longer spawns the Implementor (Claude Code's flat-roster constraint blocks teammate-spawning by non-leads, and we're using a phantom lead). The user launches the Implementor via `mcc create impl --persona mama:implementor`.

### MAMA's UX-spawn path → reverted to subagent

UX is now a one-shot subagent (Agent tool without `team_name`). For long-running UX collaboration, the user can launch a separate `design-ux` session.

### Crossover layout migration

Pre-v3: flat files in `docs/crossover/` (`commission_NNN_request.md`, etc.).
v3: thread directories `docs/crossover/{thread_id}/`.

Existing flat files remain valid history. The `/upgrade` commands handle on-disk state migration (legacy state dirs → `.mcc/`). Crossover layout is forward-only — old flat files stay, new threads use the new layout.

---

## 11. Build Order

Implementation phases (all completed on `feature/bus-via-teams`):

1. Tear down channel-specific bus infrastructure (MCP server, Node bundle, dev-flag plumbing)
2. Add team setup logic to `mcc` — config management, member topup, settings.json env, resume launch flags, `mcc create`
3. Unify state to `.mcc/` — paths in mcc.py, plugin session commands, plugin commands/skills sweep, hooks
4. Rebuild bus plugin — skill, SessionStart hook, slash commands
5. Methodology updates — crossover commands refactored to SendMessage + Write, MAMA's TeamCreate removed, UX falls back to subagent, plugin SKILLs updated
6. Upgrade flows, design doc, version bumps, cleanup

---

## 12. Open Questions / Risks / Deferred Work

### Open questions

- **Team name collisions**: two projects with the same dirname collide on the same team config. Punted for v1; revisit if it becomes a problem (likely via path-hash suffix).
- **Cross-platform**: Claude Code's team mailbox is shared filesystem state under `~/.claude/teams/`. Should work cross-platform. Verify under WSL on Windows.
- **Concurrent identities**: if the user accidentally launches two sessions with the same `--agent-name`, both write to the same inbox. Atomic rename via lockfile prevents corruption, but identity collision is a confusion source. Worth detecting in a future `mcc team status`.

### Deferred features (notable)

- **Team management commands** beyond setup/status: clear stuck inbox, manually retry delivery, force-close threads, garbage-collect old archives. Defer until usage surfaces specific needs.
- **Multi-product team mode**: one team across `.mcc-backend/` AND `.mcc-app/` if they coexist? Currently each scope gets its own team. Could revisit if real workflows want this.
- **PDT-side reactive flows**: when a `[CONSULT]` message arrives, can PDT auto-trigger `/pdt:consult` without user invocation? Possibly via a hook. Defer.
- **Long-running UX teammate**: `mcc create design-ux --persona mama:ux-designer` works today but isn't first-class. Could become a normal pattern if UX gets heavier use.
