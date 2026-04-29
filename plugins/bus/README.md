# Bus — Peer Messaging for Methodical-CC

A peer-messaging bus that lets PDT, Architect, Implementor, and UX Designer sessions message each other directly. No more user-as-courier for cross-session collaboration.

## Why

In MAMA, the team-based model (Architect + Implementor + UX) gives you real-time collaboration with a shared task list and `SendMessage` between teammates — it's a quality unlock. But across plugins (Architect ↔ PDT), collaboration goes through `docs/crossover/` files manually couriered by the user. That's slow, lossy, and leans hard on the user.

The bus eliminates the courier without losing the discipline that made the courier model produce crisp consults. Two modes:
- **Chat** — lightweight, ephemeral, no artifact written
- **Consult** — durable, structured artifact in `docs/crossover/`, citable forever

## Install

**Prerequisite:** Node.js ≥ 20 on your PATH. Install from https://nodejs.org/ if needed.

```bash
mcc bus setup
```

This:
1. Installs the plugin at user scope
2. Enables it for the current project
3. Verifies Node ≥ 20 is available and the server bundle is present
4. Adds `.mcc/` to `.gitignore`

The bus server ships as a pre-built bundle (`server.bundle.js`) — there's no `npm install` step at user time. Just enable and go.

> **Channels are in research preview.** Until the bus is on Anthropic's approved allowlist, you'll need to launch Claude Code with the dev flag:
> ```bash
> claude --dangerously-load-development-channels plugin:bus@methodical-cc
> ```

## Identity

The bus uses your registered session name as your identity. Register from inside Claude Code:
```
/pdt:session set design
/mam:session set arch
/mama:session set arch
```

That name (`design`, `arch`, etc.) is your bus identity — peers address you by it. If you don't register, you're `anonymous` and can send messages but can't be addressed back.

## Sending a message

Two MCP tools are available to Claude:

**`peer_send`** — send to a named peer
```
peer_send(
  to="pdt",
  body="PDT — sending consult-007. See artifact for the request.",
  mode="consult",
  thread_id="consult-007-depth-visibility",
  artifact_body="...full structured request..."
)
```

**`peer_list`** — see registered identities and pending counts

## Receiving a message

Messages arrive automatically as `<channel source="bus" from="..." mode="..." thread_id="..." artifact_path="...">` tags in the recipient's context. No polling needed. When `mode="consult"`, the artifact at `artifact_path` has the full structured content.

## Threading

Threads are sender-declared kebab-case strings (`consult-007-depth-visibility`, `commission-013-validation`). Each thread gets a directory under `docs/crossover/{thread_id}/` with sequentially-numbered turn files (`001-arch-request.md`, `002-pdt-response.md`, ...).

Mark a thread closed with `close=true` on the final message.

## Inspect

From the terminal:
```bash
mcc bus status
```

Inside a Claude session:
```
/bus:status
/bus:identity
```

Each session also gets an `=== METHODICAL-CC BUS ===` block at session start showing identity, active threads, and any unread messages.

## File layout (per repo)

```
{repo}/
├── .mcc/
│   └── bus/
│       └── inbox/
│           └── {identity}/
│               ├── {timestamp}_{sender}_{thread_id}_{nonce}.json   # pending
│               └── .consumed/
│                   └── ...                                         # archived
└── docs/
    └── crossover/
        └── {thread_id}/
            ├── 001-arch-request.md
            ├── 002-pdt-response.md
            └── .bus-state.json
```

`.mcc/` is internal coordination state (gitignored). `docs/crossover/` is durable record (commit it).

## Troubleshooting

**`server.bundle.js` missing.** The marketplace clone is incomplete or out of date. Run `mcc update` to refresh.

**Node not found / version too old.** Install Node ≥ 20 from https://nodejs.org/.

**Channel notifications not appearing.** Check that you launched with `--dangerously-load-development-channels plugin:bus@methodical-cc`. Until the bus is on the approved allowlist, this flag is required.

**`peer_send` says "unknown recipient".** The target identity isn't registered in this repo's sessions files. Have the recipient run `/pdt:session set <name>` (or `/mam:session set <name>`, `/mama:session set <name>`) in their session, or run `mcc bus status` to see who is registered.

**Anonymous identity at session start.** Your session ID isn't matched in any `sessions` file. Register with `/pdt:session set <name>` etc.

## See Also

- [Full design document](../../docs/bus-design.md)
- [`bus-protocol` skill](skills/bus-protocol/SKILL.md) — the full protocol reference for agents using the bus
