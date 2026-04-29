# Bus Plugin — Design Document

**Status:** Design captured, ready to implement
**Date:** 2026-04-29
**Authors:** Bryon (user) + Claude (design partner)

A peer-messaging bus for Methodical-CC sessions. Eliminates the user-as-courier pattern between PDT and MAM/MAMA without losing the discipline that made the courier model produce good work.

---

## 1. Context & Motivation

### The current state

Within MAMA, the Architect, Implementor, and UX Designer collaborate as a team — `SendMessage` between them, shared task list, low-friction back-and-forth. This works well; the architect's reflection (`tmp/architect_reflection_peer_messaging.md`) called it "a genuine unlock."

Across plugins (Architect ↔ PDT), collaboration goes through `docs/crossover/` files manually couriered by the user: write a `consult_NNN_request.md`, ask the user to paste it into the PDT session, PDT writes a response file, user pastes the response file path back, architect reads it. Slow loop, multi-day round trips, the user as load-bearing relay.

### What we want

- Eliminate courier friction for cross-session messages.
- **Preserve the slow-loop discipline** that made the courier model produce crisp consults. The architect's reflection names this: "writing a consult is expensive; the artifact is durable; the discipline of 'lay out options, name your instinct' still applies." We must not let frictionless messaging erode that.
- Keep the user as integrator (visibility, override, audit trail), not as courier.
- Work for any combination of PDT/MAM/MAMA sessions — not just architect-to-PDT.

### What we're not building (yet)

Items deferred to future iterations are listed in §12. Notable: no broadcast, no role-based addressing, no real-time online/offline presence, no permission relay, no separate artifact-publish notification.

---

## 2. Architecture

### Shape

A new peer plugin in this marketplace named **`bus`**. Installs alongside `pdt`/`mam`/`mama`; any session in any of those (or none) can use the bus.

The plugin bundles a **Channel-style MCP server** (per `code.claude.com/docs/en/channels-reference`) that:
- Pushes peer messages into a Claude Code session as `<channel source="bus" ...>` notifications
- Exposes a `peer_send` reply tool so the session can send back

Each Claude Code session spawns its own MCP server subprocess (standard MCP behavior). Multiple sessions in the same repo coordinate through **shared filesystem state** under `.mcc/bus/`.

### No daemon

We don't run a long-lived bus daemon. State lives in files; each session's MCP server `fs.watch`es the inbox directory it cares about. This is cross-platform, has acceptable latency (tens of milliseconds), and avoids daemon lifecycle complexity.

### Runtime

Node ≥ 20 with `@modelcontextprotocol/sdk`. The official MCP TypeScript/JavaScript SDK is the only library that today exposes the `claude/channel` capability declaration and `notifications/claude/channel` notification emission that the bus depends on. Python's FastMCP 2 was the initial choice but lacks these primitives.

The `mcc` CLI tool itself remains Python (stdlib only) for now. Future work converts `mcc` to Node so the project has a single runtime; that's tracked separately and is not part of bus v1.

### File layout (per repo)

```
{repo}/
├── .mcc/
│   └── bus/
│       └── inbox/
│           └── {identity}/
│               ├── {timestamp}_{sender}_{thread_id}_{nonce}.json   # pending
│               └── .consumed/
│                   └── {timestamp}_{sender}_{thread_id}_{nonce}.json   # archived
└── docs/
    └── crossover/
        └── {thread_id}/
            ├── 001-arch-request.md
            ├── 002-pdt-clarification.md
            ├── 003-arch-followup.md
            ├── 004-pdt-response.md
            └── .bus-state.json
```

`.mcc/bus/` is internal coordination state (gitignore). `docs/crossover/` is durable record (committed).

---

## 3. Identity

### Source of truth

The session-name registry we already built — `.pdt/sessions`, `.mam*/sessions`, `.mama*/sessions` — is the bus identity registry. No separate registration step. Users register a session via existing `/{plugin}:session set <name>` and that name is its bus identity.

### Resolution

The bus plugin's **SessionStart hook** runs at session start:
1. Reads `${CLAUDE_SESSION_ID}`
2. Walks `.pdt/sessions`, `.mam*/sessions`, `.mama*/sessions` in cwd, looking for `<name>=<session_id>` matching its own session
3. Emits to context:

> *"You are operating on the methodical-cc bus as identity `arch` (registered in `.mama-backend/sessions`). Use `peer_send` to message peers; received messages arrive as `<channel source="bus" from="...">` tags. Active threads with you involved: ..."*

### Anonymous fallback

If no session-name match is found, identity is `anonymous`:
- The session can still call `peer_send` to message named peers
- Peers cannot address messages to it
- Hook context tells the user how to fix this: *"Run `/{plugin}:session set <name>` to register and become addressable."*

### Why this design

- Reuses existing UX patterns (no new concept introduced)
- Single registry (sessions files) — no drift between session-name and bus-identity
- Anonymous fallback means the bus is useful even before identity setup, but pushes toward identification

---

## 4. Tools

Two MCP tools. That's the entire tool surface.

### `peer_send`

```
peer_send(
  to: str,                   # target identity (e.g. "pdt", "arch")
  body: str,                 # the message body, always present
  mode: "chat" | "consult",  # required
  thread_id: str | None,     # if continuing a thread or starting a named one
  artifact_body: str | None, # consult mode only — structured artifact content
  close: bool = False        # mark this message as the close of the thread
)
```

**Semantics:**
- `mode='chat'` — body delivered as channel notification to recipient. No artifact.
- `mode='consult'` — body delivered as channel notification (the framing/intro prose) AND an artifact is written to `docs/crossover/{thread_id}/{NNN}-{sender_role}-{type}.md` containing `artifact_body`. Recipient sees both.
- `thread_id` is sender-declared, kebab-case (e.g. `consult-spawning-discipline-v2`). If absent on first message, auto-generated as `{sender}-to-{recipient}-{yyyy-mm-dd}-{nn}`.
- `close=true` marks the thread closed in `.bus-state.json` after this message is delivered.

**Behavior:**
1. Validate recipient exists in identity registry. If not, return error with hint to check `peer_list`.
2. If mode=consult: write artifact file to `docs/crossover/{thread_id}/`, atomic rename pattern.
3. Write inbox file to `{repo}/.mcc/bus/inbox/{recipient}/{timestamp}_{sender}_{thread_id}_{nonce}.json`.
4. Update `.bus-state.json` for the thread (participants, last activity, status).

### `peer_list`

```
peer_list() → [
  {
    identity: str,
    sessions_file: str,        # which file declared this identity
    last_activity: timestamp,  # most recent inbox write or consume
    pending_messages: int      # count in their inbox
  }, ...
]
```

Read from sessions files (canonical registry). Last activity from inbox file mtimes. Pending count from inbox directory listing.

**Note on presence:** We deliberately don't show "online/offline." Last-activity timestamps are informational. A peer's session not running right now is not a reason to skip messaging them — the user can spin them up in response. The send primitive always works regardless of whether the recipient's session is currently running.

---

## 5. Modes — Chat vs Consult

The mode distinction is the discipline-preserving lever. Treat it seriously in skill guidance.

### Chat mode

Lightweight, ephemeral. For:
- Quick clarifications mid-work
- "Heads up" pings
- Acknowledgments
- Anything where future-you doesn't need to reference this exchange

No artifact. Just a channel notification. The conversation lives in agents' contexts and the consumed-inbox archive (subject to culling).

### Consult mode

Heavyweight, durable. For:
- Design questions that warrant considered responses
- Commissions and their results
- Debriefs after milestones
- Anything where future-you (or a future session) might want to reference "what we decided in consult-007"

Produces an artifact file in `docs/crossover/`. The artifact is structured (see §7). Both peers' filesystems get the artifact (same repo). Citable, durable, reviewable.

### The temptation to misuse

The architect's reflection names the failure mode: *"if `peer.send(mode='chat')` is too easy and too cheap, I'll start using it for things that should be artifacts."* The bus skill (§9) gives explicit guidance: when in doubt, prefer consult mode. Chat is for quick conversational exchanges, not for design decisions.

---

## 6. Inbox Protocol

### File format

Inbox file is JSON, written atomically (write to `.tmp` then rename):

```json
{
  "from": "arch",
  "to": "pdt",
  "thread_id": "consult-spawning-discipline-v2",
  "mode": "consult",
  "sent_at": "2026-04-29T10:30:00Z",
  "body": "PDT — sending consult-spawning-discipline-v2. Quick framing: the architect kept tripping over Agent-tool subagent vs teammate distinction. Looking at the artifact for the structured request and three options I want your read on.",
  "artifact_path": "docs/crossover/consult-spawning-discipline-v2/001-arch-request.md",
  "close": false
}
```

For chat mode, `artifact_path` is `null` and `body` is the full message.

### Filename

`{timestamp_iso}_{sender}_{thread_id}_{4-char-nonce}.json`

Sortable by mtime AND by filename, prevents collisions, decodes at a glance.

### Consumption

When the MCP server emits the channel notification for a message, it moves the inbox file to `inbox/{identity}/.consumed/`. The artifact (if any) stays in `docs/crossover/`.

### Culling

Consumed pointers are deleted after a retention window (default 30 days, configurable via env var `MCC_BUS_RETENTION_DAYS` or `mcc bus setup`). Artifacts in `docs/crossover/` are never culled by the bus — they're durable record under user/git control.

### Startup processing

On MCP server startup:
1. Scan `inbox/{identity}/` for unconsumed pointers
2. Sort by `sent_at` (chronological)
3. For each, emit `notifications/claude/channel` to push it as a `<channel>` tag, then move to `.consumed/`
4. Prepend a "while you were away" preamble to the first one if there are any: *"You have N unread messages from your last session. Processing in chrono order..."*

### Channel tag format

```text
<channel source="bus" from="arch" thread_id="consult-spawning-discipline-v2" mode="consult" artifact_path="docs/crossover/consult-spawning-discipline-v2/001-arch-request.md">
PDT — sending consult-spawning-discipline-v2. Quick framing: the architect kept tripping over Agent-tool subagent vs teammate distinction. Looking at the artifact for the structured request and three options I want your read on.
</channel>
```

Tag attributes give the agent everything it needs to react: who sent it, what thread, what mode, where the artifact lives if any.

---

## 7. Artifact Convention

### Path

`docs/crossover/{thread_id}/{NNN}-{sender}-{type}.md`

Where:
- `thread_id`: kebab-case string from `peer_send`
- `NNN`: zero-padded turn number (001, 002, ...)
- `sender`: identity that wrote this turn (e.g. `arch`, `pdt`)
- `type`: short descriptor (`request`, `response`, `clarification`, `followup`, `commission`, `debrief`)

Example progression:
```
docs/crossover/consult-007-depth-visibility/
├── 001-arch-request.md
├── 002-pdt-clarification.md
├── 003-arch-clarification-response.md
├── 004-pdt-response.md
├── .bus-state.json
```

### Frontmatter (consult mode artifacts)

```yaml
---
thread_id: consult-007-depth-visibility
turn: 1
type: request
from: arch
to: pdt
sent_at: 2026-04-29T10:30:00Z
status: open  # open | resolved
---
```

### Body structure (guidance, not enforcement)

Skill-level guidance for consult requests:
- **Question**: what you want answered
- **Context**: what the recipient needs to know
- **Options considered**: alternatives and their trade-offs
- **Instinct**: where you're leaning and why
- **Response format**: how you'd like the answer shaped

For consult responses:
- **Direct answer**: the response itself
- **Rationale**: why this answer
- **Caveats / edge cases**: where the answer might not hold
- **Open questions**: anything you couldn't resolve

This format is what made today's consults produce load-bearing answers. We preserve it through skill instruction, not through tool-level enforcement (we want flexibility for non-design consults).

---

## 8. Threading

### Thread IDs

Sender-declared, kebab-case strings. Conventions:
- `consult-{topic}-{version}` — design consults (`consult-spawning-discipline-v2`)
- `commission-{NNN}-{topic}` — commission threads (`commission-013-validation`)
- Free-form for chat-only threads (`quick-q-pydantic-version`)

Auto-generation: if sender omits `thread_id` on first message, generate `{sender}-to-{recipient}-{yyyy-mm-dd}-{counter}`.

### Thread state file

`docs/crossover/{thread_id}/.bus-state.json`:

```json
{
  "thread_id": "consult-007-depth-visibility",
  "participants": ["arch", "pdt"],
  "started_at": "2026-04-29T10:30:00Z",
  "last_activity_at": "2026-04-30T14:22:00Z",
  "status": "open",
  "turn_count": 4,
  "awaiting": "pdt"  # whose response we're waiting for, if anyone
}
```

Updated by the bus on every send.

### Closure

Explicit `close=true` on a `peer_send` flips `status` to `resolved` and clears `awaiting`. No automatic closure based on inactivity.

### Active-threads digest

The bus plugin's SessionStart hook surfaces threads where the current identity is a participant and the thread is `open`:

> *"Active threads:*
> *  - consult-007-depth-visibility (with pdt) — last: pdt 2h ago, awaiting your response*
> *  - commission-013-validation (with arch) — last: arch 1d ago, awaiting pdt"*

Keeps thread state visible without needing a `peer_thread_history` tool.

---

## 9. SessionStart Hook

The bus plugin emits one SessionStart hook that combines:

1. **Identity resolution** (§3) — "you are `arch` on the bus"
2. **Active-threads digest** (§8) — open threads involving you
3. **Unread queue notice** (if any) — "you have N unread messages, will deliver in chrono order"

The hook itself is a small Python script (re-used logic from the MCP server). It writes to stdout, which becomes additional context per Channels conventions.

---

## 10. `mcc` Integration

Two new subcommands:

### `mcc bus setup`

Project-scoped:
- Ensures the `bus` plugin is installed at user scope (installs if absent, disabled at user scope by default — same pattern as `mcc setup`)
- Enables `bus` for the current project
- Creates `.mcc/bus/inbox/` if absent
- Adds `.mcc/bus/` to `.gitignore` if not already present
- Reports identity status for any registered sessions in the project

### `mcc bus status`

Reports:
- Bus enabled state for current project
- Registered identities (read from sessions files across plugins)
- Last activity timestamps per identity
- Pending message counts per identity
- Active thread count
- Retention setting

Idempotent and read-only.

---

## 11. MAMA / MAM / PDT Migration Plan

### Send-side commands (refactor to use `peer_send`)

These currently write request files for the user to courier. They should call `peer_send` directly:

| Command | New behavior |
|---|---|
| `/mama:consult-pdt`, `/mam:consult-pdt` | `peer_send(to='pdt', mode='consult', thread_id, body, artifact_body)` |
| `/mama:debrief-pdt`, `/mam:debrief-pdt` | `peer_send(to='pdt', mode='consult', thread_id, body, artifact_body)` |
| `/pdt:commission` | `peer_send(to='arch', mode='consult', thread_id, body, artifact_body)` |

The command's instructional content (how to compose a good consult/commission/debrief) is preserved. The output mechanism shifts from file-write-to-crossover to peer_send.

### Receive-side commands (likely deprecated as slash commands)

These currently process incoming files. With the bus, they're reactive flows triggered by inbound `<channel>` notifications. Skill guidance replaces the slash command:

| Old command | Replaced by |
|---|---|
| `/pdt:consult` (process incoming) | Skill guidance: "when a `<channel mode='consult' from='arch'>` arrives, read carefully, compose a structured response, `peer_send` back" |
| `/pdt:debrief` (process incoming) | Skill guidance equivalent |
| `/mama:commission-complete` (responding TO pdt with commission result) | This is actually send-side from the agent's perspective — refactor to `peer_send(to='pdt', mode='consult', ...)` |
| `/mam:commission-complete` | Same |

The existing slash commands can stay for one cycle as transitional aids that explicitly call `peer_send` — gives the user a familiar invocation path while the muscle memory updates. Ultimately they may be removed.

### Skill updates

Each plugin's SKILL.md gets a "Working over the bus" section that explains:
- The two modes and when to use each
- That consult mode produces durable artifacts; chat mode does not
- Channel-tag handling: when one arrives, what to do based on `mode` and `from`
- Threading conventions
- The discipline-preserving framing — why consult mode is more than just "fancy chat"

### Crossover layout migration

Current: flat files in `docs/crossover/` (`commission_NNN_request.md`, etc.)
New: thread directories in `docs/crossover/{thread_id}/`

Migration is optional — existing flat files stay readable and citable. New threads use the new layout. An `mcc bus migrate-crossover` command could fold flat files into thread directories if a user wants tidiness.

### Phasing

**Build the bus first. Don't refactor yet.** Once the bus is shipped and we've used it for one or two real consults, we'll know what hurts in the migration. Premature refactor would lock in assumptions we haven't validated.

---

## 12. Deferred Features (with rationale)

These appeared in the architect's wishlist but aren't in the MVP. Each is deferred because we want to see how usage evolves before committing to a shape.

| Feature | Why deferred |
|---|---|
| `peer_publish_artifact` | Claude Code already notifies sessions of repo changes. If A wants B to read a doc, A sends a chat-mode message saying so. Redundant with existing repo awareness. |
| `peer_thread_history` tool | Threads are filesystem directories. Agent can read them directly. Don't burn a tool on a `ls` + `cat`. |
| `peer_whoami` tool | Identity injected via SessionStart hook. Agent learns it once at startup and remembers. |
| `peer_subscribe` | Assumes a noise problem we don't have. All threads visible by default through the active-threads digest. |
| `peer_broadcast(role, ...)` | Speculative — no current scenario has multiple sessions claiming one role. Add when that scenario emerges. |
| `peer_propose_sync` | Cute but low-value; a chat-mode `peer_send` does the same thing. |
| Real-time online/offline presence | Misleading signal (a 2h-old timestamp doesn't mean offline; a 2m-old timestamp doesn't mean online). Send always works regardless. Activity timestamps are informational only. |
| Permission relay | Channels supports it for chat platforms. Not relevant for peer Claude sessions — each session approves its own tool use. |
| Supervisor / interception controls | The user already sees every artifact in the repo (gitignore-aware) and every chat in real-time via Claude Code's UI. Explicit interception adds complexity without addressing a felt need yet. |
| Selective context attachments | Sender includes the path in the message body; recipient reads it. The repo is shared — no need for an explicit attachment mechanism. |

---

## 13. Build Order

1. **Bus plugin skeleton** — `plugins/bus/.claude-plugin/plugin.json`, README stub
2. **FastMCP server** at `plugins/bus/server/server.py` — implements `peer_send`, `peer_list`, channel notifications, inbox protocol
3. **SessionStart hook** at `plugins/bus/hooks/` — identity resolution, active threads digest, unread delivery
4. **Bus skill** at `plugins/bus/skills/bus-protocol/SKILL.md` — modes, channel-tag handling, consult discipline
5. **Slash commands** at `plugins/bus/commands/` — `/bus:status`, `/bus:identity` for diagnostics
6. **`mcc bus setup` and `mcc bus status`** in `tools/mcc.py`
7. **README and marketplace entry** — version 1.0.0
8. **Smoke test** — two terminals, two sessions in this repo, send a consult, verify the cycle end-to-end
9. **MAMA/MAM/PDT migration** — refactor send-side commands, update skills (separate work item, after MVP validation)

---

## 14. Distribution & Dependencies

### Repo location

The bus plugin lives in this repo at `plugins/bus/`, alongside `pdt`/`mam`/`mama`. Single-repo design: the bus shares conventions, identity registry, and the `.mcc/` state surface with `mcc`. Splitting it into a separate repo would create artificial separation and a second release cadence with no upside.

### Distribution form

Source, not a compiled binary. The marketplace clone delivers the source to user machines; the MCP server runs from there. PyInstaller-style bundling would mean per-platform builds and binary blobs in git for no security/sandboxing gain (the server runs locally on the user's machine anyway).

### Dependency management — pre-built bundle (zero install at user time)

The bus server is **bundled with esbuild** before commit, producing a single self-contained file `plugins/bus/server/server.bundle.js` that includes the MCP SDK and all transitive deps. The bundle is committed to the repo and ships with the marketplace clone.

This means **users never run `npm install`**. The marketplace clone delivers a ready-to-run bundle; `mcc bus setup` just verifies Node ≥ 20 is on PATH and that the bundle is present.

Source layout:

```
plugins/bus/server/
├── server.js               # source — what we edit
├── server.bundle.js        # generated — what ships and runs (committed)
├── package.json            # declares MCP SDK dep + esbuild devDep + build script
├── package-lock.json       # for reproducible dev installs
└── node_modules/           # gitignored, only present for local dev
```

The plugin's MCP entry runs the bundle directly:

```json
{
  "mcpServers": {
    "bus": { "command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/server/server.bundle.js"] }
  }
}
```

### Keeping the bundle in sync

A pre-commit hook at `tools/git-hooks/pre-commit` watches for staged changes under `plugins/bus/server/` (excluding `server.bundle.js` itself and `node_modules/`). When it detects them, it runs `npm run build` and stages the resulting bundle as part of the commit.

The hook is enabled per-clone via:

```bash
git config core.hooksPath tools/git-hooks
```

This is the only one-time setup contributors do. The hook fails clearly if Node or `node_modules/` are missing, so first-time contributors get a helpful nudge instead of silent staleness.

### Why bundle vs. install at user time

| Approach | User does | Pros | Cons |
|---|---|---|---|
| `npm install` at user time | `mcc bus setup` runs `npm install` | Standard Node workflow | Needs npm available, leaves `node_modules/` in marketplace clone, slow first-run |
| `npx` from published package | `npx -y @methodical-cc/bus` | Clean | Need to publish to npm registry, separate release process |
| **Pre-built bundle** (chosen) | Nothing — bundle ships with the marketplace | Zero install friction, self-contained, no extra release process | Committed binary artifact (~700 KB), build step in dev workflow |

The bundle's size (~700 KB) is acceptable to commit, and the dev tax (run `npm run build` or rely on the pre-commit hook) is light.

### Why Node 20+

The MCP SDK uses modern ESM patterns and recent Node features. Pinning to ≥20 (LTS) keeps the floor reasonable. `mcc bus setup` checks the version and bails with a clear message if older.

### Why hybrid

- **uv path** gives the smoothest UX — `uv` is becoming the standard Python tool and is one-line install. Users who have it (an increasingly common case) get zero-friction setup.
- **venv path** keeps the bus working for anyone with just Python+pip. We don't gate adoption on a tool the ecosystem hasn't fully converged on yet.
- Two paths is mildly more maintenance, but the surface is small (one wrapper script per platform, one `requirements.txt` to keep in sync with PEP 723 metadata).

### Cross-platform notes

- Node's built-in `fs.watch` handles inbox monitoring portably (inotify on Linux, FSEvents on macOS, ReadDirectoryChangesW on Windows). Some platforms coalesce duplicate events; the server debounces by filename briefly to handle that.
- Atomic rename works on all major OSes within a single volume (the inbox always lives on the same volume as the repo).
- No per-platform shim required: `node` is invoked directly by the plugin's MCP config and resolves the same way everywhere.

---

## 15. Open Questions / Risks / Deferred Work

### Open questions

- **Channel research-preview status.** Channels currently require `--dangerously-load-development-channels` for non-allowlisted plugins. Document this in the README; users will need to launch Claude Code with the dev flag until our channel is allowlisted (or we submit it for approval).
- **MCP server discovery within plugin.** The plugin.json `mcpServers` entry is the documented mechanism, but its exact substitution rules (e.g. `${CLAUDE_PLUGIN_ROOT}`) need confirmation in practice during smoke testing.
- **Cross-platform `fs.watch`.** Node's built-in `fs.watch` works across Linux/macOS/Windows but has known platform quirks (event coalescing on macOS, no recursive watch by default on Linux). The server debounces by filename to handle the macOS case; we watch a flat directory only, so Linux's lack of recursive watch is moot. Verify under real load during smoke testing.
- **Concurrent writes.** Two senders writing to the same recipient's inbox simultaneously — handled via atomic rename (write to `.tmp`, rename to final). Filesystem rename is atomic on the same volume on all major OSes; the inbox always lives on the same volume as the repo.
- **Thread ID collisions.** If two senders independently pick the same kebab-case ID — bus auto-suffixes with a counter for auto-generated IDs. For sender-declared IDs, no current protection — convention assumes uniqueness, race is rare in practice.

### Deferred work (notable)

- **Exception management commands.** When usage surfaces specific needs, we may want CLI affordances for: clearing a stuck inbox, manually retrying delivery, inspecting consumed archives, force-resending a message, force-closing a thread, garbage-collecting old archived messages on demand. Ship without these; add as the use case actually emerges from real bus traffic.
- **Methodology migration tooling.** Existing repos with flat `commission_NNN_request.md` style crossover files predate the thread-directory layout. Optional `mcc bus migrate-crossover` could fold flat files into thread directories. Defer until someone has flat-file legacy and wants the cleanup.
- **Identity discovery without `CLAUDE_PROJECT_DIR`.** The bus relies on `CLAUDE_PROJECT_DIR` to find the transcript dir for session-id discovery. If that env var ever goes away or changes shape, we'll need a different mechanism (e.g., Claude Code passing session id to the MCP subprocess directly).
