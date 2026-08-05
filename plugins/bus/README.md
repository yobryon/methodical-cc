# Bus — Peer Messaging for Methodical-CC

A peer-messaging bus that lets PDT, Architect, Implementor, and UX Designer sessions message each other directly. No more user-as-courier for cross-session collaboration.

## Why

In MAMA, the team-based model (Architect + Implementor + UX) gives you real-time collaboration with a shared task list and `SendMessage` between teammates — it's a quality unlock. But across plugins (Architect ↔ PDT), collaboration historically went through `docs/crossover/` files manually couriered by the user. That's slow, lossy, and leans hard on the user.

The bus eliminates the courier without losing the discipline that made the courier model produce crisp consults. Two modes:
- **Chat** — lightweight, ephemeral, no artifact written
- **Consult** — durable, structured artifact in `docs/crossover/{thread_id}/`, citable forever

## How it works

The bus is built on Claude Code's native **agent-team mailbox protocol** — there's no MCP server, no Node, no extra dependencies. Sessions in a project join a shared team (under `~/.claude/teams/<team>/`) and message each other via the standard `SendMessage` tool. Claude Code's harness polls each session's mailbox once a second and delivers new messages as turns automatically.

A phantom "coordinator" lead satisfies the team protocol's flat-roster requirement; all real participants (PDT, Architect, Implementor, UX) are symmetric peers, each launched as its own user-driven session.

## Install

```bash
mcc team setup
```

This:
1. Ensures the bus plugin is enabled at user scope
2. Sets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in the project's `.claude/settings.json`
3. Creates the team config under `~/.claude/teams/<team>/` with the phantom lead
4. Adds `.mcc/` to `.gitignore`

Most users never need to call this directly — `mcc <name>` and `mcc create <name>` invoke it implicitly.

## Identity

The bus uses your registered session name as your identity. Register from inside Claude Code:
```
/pdt:session set design
/mam:session set arch
/mama:session set arch
```

That name (`design`, `arch`, etc.) is your bus identity — peers address you by it via `SendMessage(to=...)`. If you don't register, you're `anonymous` and can send messages but can't be addressed back.

## Sending a message

Use Claude Code's native `SendMessage` tool:

```
SendMessage(to="pdt", message="...")
```

For **consult mode**, also Write the structured artifact:

```
Write("docs/crossover/consult-007-depth-visibility/001-arch-request.md", ...)
SendMessage(to="pdt", message="PDT — sending consult-007. See artifact at docs/crossover/consult-007-depth-visibility/001-arch-request.md")
```

The `bus-protocol` skill covers the full convention.

## Receiving a message

Inbound messages arrive automatically as new turns — Claude Code's harness polls each session's mailbox once a second. No explicit receive call needed.

## Threading

Threads are sender-declared kebab-case strings (`consult-007-depth-visibility`, `commission-013-validation`). Each thread gets a directory under `docs/crossover/{thread_id}/` with sequentially-numbered turn files (`001-arch-request.md`, `002-pdt-response.md`, ...).

## Inspect

From the terminal:
```bash
mcc team status
```

Inside a Claude session:
```
/bus:status
/bus:identity
```

Each session also gets a `=== METHODICAL-CC BUS ===` block at session start showing team identity and membership.

## File layout (per repo)

```
{repo}/
├── .mcc/
│   ├── sessions                 # Registered session identities
│   └── bus/
│       └── inbox/
│           └── {identity}/      # Per-session staging (legacy/diagnostic)
└── docs/
    └── crossover/
        └── {thread_id}/
            ├── 001-arch-request.md
            ├── 002-pdt-response.md
            └── ...
```

The team mailbox itself lives outside the repo at `~/.claude/teams/<team>/inboxes/<name>.json`. `.mcc/` is internal coordination state (gitignored). `docs/crossover/` is durable record (commit it).

## Troubleshooting

**Identity shows `anonymous` or no team block at SessionStart.** The launch flags weren't set. Resume sessions via `mcc <name>` rather than plain `claude -r <id>`.

**`SendMessage` says recipient not in team.** The target session hasn't registered with this team. Have the recipient run `mcc create <name>` (or register via `/pdt:session set <name>` etc.) so they join the team.

**Messages not arriving.** Verify the recipient's session is actually open and on the same team — `mcc team status` lists active members.

## See Also

- [Full design document](../../docs/bus-design.md)
- [`bus-protocol` skill](skills/bus-protocol/SKILL.md) — the full protocol reference for agents using the bus
