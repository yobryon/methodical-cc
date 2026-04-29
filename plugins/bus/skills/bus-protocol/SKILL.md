---
name: bus-protocol
description: How to use the methodical-cc peer messaging bus. Built on Claude Code's agent-team protocol — each project has a team, each session is a teammate addressable by name, messages flow via SendMessage and arrive automatically. Covers identity, the chat-vs-consult mode distinction, threading conventions, and the discipline that makes consult-mode messages produce durable outcomes.
---

# Bus Protocol

The methodical-cc bus connects PDT, Architect, Implementor, and UX Designer sessions so they can message each other directly. It's built on Claude Code's native agent-team protocol — each project has its own team, each session joins as a teammate, and messages flow via the standard `SendMessage` tool.

## Mechanics underneath (non-essential for using it, but useful to know)

- The user's `mcc` tool maintains a team config at `~/.claude/teams/<project>/config.json` and seeds members from registered session identities
- When `mcc <name>` resumes a session, it passes `--team-name`, `--agent-name`, and `--agent-id` flags to claude
- Each session's harness polls `~/.claude/teams/<project>/inboxes/<your-name>.json` once per second; new messages there are injected into your context as new turns
- `SendMessage` writes to the recipient's inbox file (with a lockfile, atomically)

You don't manage any of this directly — `SendMessage` is a normal tool call, and inbound messages arrive as natural turns. The mechanics matter only when something looks wrong.

## Identity

Your bus identity is set when you launch (via `--agent-name <name>`). The bus plugin's SessionStart hook tells you your name explicitly — look for the `=== METHODICAL-CC BUS ===` block in your context. It looks like:

> *"You are a member of agent team `forms-cli`. Your name on the team is `arch`, your agent_id is `arch@forms-cli`. Other team members: `pdt`, `coordinator` (phantom lead). Use `SendMessage` to message any teammate by name; messages from teammates arrive automatically as new turns."*

Trust this even if other context elsewhere suggests you're not in a team. The team is real, the tools work.

If the SessionStart hook reports `anonymous` or no team membership block appears, the launch flags weren't set — the user should resume via `mcc <name>` rather than plain `claude -r <id>`.

## Receiving messages

Peer messages arrive in your context **as turns** — they look like the user wrote them, but they're actually messages from teammates. They typically come prefaced with the sender's name. The Claude Code harness handles the injection automatically.

For consult-mode messages, the body will reference an artifact at a known path under `docs/crossover/{thread_id}/`. Read it for the full structured content.

## Sending messages

Use the standard `SendMessage` tool:

```
SendMessage(to="pdt", message="Quick question: ...")
```

For substantive design messages (consults), use a structured pattern (described below) — but `SendMessage` is the tool, regardless of mode.

## Two modes — pick deliberately

**Chat mode** (lightweight):
- Just a `SendMessage` call. No artifact written.
- Use for: quick clarifications, heads-up pings, acknowledgments, anything where future-you doesn't need to reference this exchange.
- Example: *"Hey arch — quick clarification on consult-007: when you say 'depth-mode framing,' do you mean per-render or per-session?"*

**Consult mode** (durable):
- Write a structured artifact to `docs/crossover/{thread_id}/{NNN}-{your-name}-{type}.md` using the `Write` tool
- Then `SendMessage` to the recipient with framing/intro prose that references the artifact path
- Use for: design questions worth a considered response, commissions, debriefs, anything where future-you (or a future session) might want to cite this.
- The artifact is the durable record; the message is the framing.

### The discipline lever

**When in doubt, prefer consult mode.** The slow-loop discipline that produces good cross-session work comes from the artifact format forcing structured thinking — laying out options, naming your instinct, anticipating responses. Chat mode is fast and frictionless; consult mode is fast in transit but slow in composition. That composition discipline is the point.

If you find yourself sending three chat-mode messages in a row to clarify a topic, stop and re-send as a consult.

### Composing a good consult request

When the consult is a request side, structure the artifact body as:

- **Question**: what you want answered
- **Context**: what the recipient needs to know to answer well
- **Options considered**: alternatives and their trade-offs
- **Instinct**: where you're leaning and why
- **Response format**: how you'd like the answer shaped (prose, list, decision matrix, etc.)

Cite relevant docs by path so the recipient can read them — don't paraphrase what they can read directly.

### Composing a good consult response

When the consult is a response:

- **Direct answer**: the response itself, up front
- **Rationale**: why this answer
- **Caveats / edge cases**: where the answer might not hold
- **Open questions**: anything you couldn't resolve, with a recommendation for next steps

## Threading

Threads are sender-declared kebab-case strings:
- `consult-{topic}-{version}` — design consults
- `commission-{NNN}-{topic}` — commission threads
- Free-form for chat-only exchanges

When replying to a message that references a thread, **always pass the same thread_id** in your reply (in your message body and in the artifact filename). That keeps the conversation in one thread directory with sequential turn numbering.

When starting a new thread, pick a descriptive ID. The artifact path becomes `docs/crossover/{thread_id}/{NNN}-{your-name}-{type}.md` where `{NNN}` is the zero-padded turn number (001, 002, ...).

When a thread reaches its natural conclusion, you can note this in your final message ("Closing the thread on this") so the recipient knows not to expect further follow-up. Don't fish for follow-ups when the work is done.

## Anti-patterns

- **Don't send unstructured questions in chat mode and call it a consult.** Mode is determined by the discipline you bring, not by claiming a label.
- **Don't ask the user to courier messages** — that's what the bus is for. If a peer isn't currently running, your message sits in their inbox until they start their session. The user can spin them up via `mcc <name>` if your message warrants it.
- **Don't poll for responses.** Messages arrive as turns automatically. If a peer hasn't responded yet, they haven't read your message yet (or are still composing). Don't badger them with chat-mode "did you see my consult?" pings.
- **Don't skip reading artifacts.** When a consult-mode message arrives, the body is framing. The artifact at the referenced path has the substance. Read it before responding.

## When the user is involved

The user can see all bus activity through repo state (artifacts in `docs/crossover/`, git history) and through their own session interactions with each teammate. Default behavior keeps the user as integrator without requiring active mediation. If you do something significant — closing a thread, sending a major consult — make sure the rationale is visible to them in the session.
