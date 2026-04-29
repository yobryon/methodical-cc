---
name: bus-protocol
description: How to use the methodical-cc peer messaging bus. Covers identity, the chat-vs-consult mode distinction, channel-tag handling on inbound, threading conventions, and the discipline that makes consult-mode messages produce durable outcomes. Use when sending peer messages or reacting to received ones.
---

# Bus Protocol

The methodical-cc bus connects PDT, Architect, Implementor, and UX Designer sessions so they can message each other directly across plugins. This skill covers how to use it well.

## Identity

Your bus identity is set at session start and shown in the SessionStart context (`=== METHODICAL-CC BUS ===` block). It comes from your registered session name in `.pdt/sessions`, `.mam*/sessions`, or `.mama*/sessions` — the same name registered via `/{plugin}:session set <name>`.

If you're `anonymous`, you can still send messages but peers can't reach you by name. Tell the user to register if they want bidirectional communication.

## Receiving messages

Peer messages arrive in your context as `<channel>` tags:

```
<channel source="bus" from="arch" thread_id="consult-007-depth-visibility" mode="consult" artifact_path="docs/crossover/consult-007-depth-visibility/001-arch-request.md">
PDT — sending consult-007-depth-visibility. Quick framing: ...
</channel>
```

Tag attributes tell you everything you need:
- **`from`**: who sent it (use this as `to` when replying)
- **`thread_id`**: keep this when replying so the conversation threads
- **`mode`**: `chat` (lightweight) or `consult` (substantive — read the artifact)
- **`artifact_path`**: present when `mode="consult"`. Read it for the full structured request.

When a consult-mode message arrives, **read the artifact** before responding. The body in the channel tag is just framing; the artifact is the substance.

## Sending messages

Two tools:

- **`peer_send(to, body, mode, thread_id?, artifact_body?, artifact_type?, close?)`** — send a message to a named peer
- **`peer_list()`** — see registered identities, last activity, pending counts

### Two modes — pick deliberately

**Chat mode** (`mode="chat"`):
- Body delivered as a channel notification only. No artifact written.
- Use for: quick clarifications, heads-up pings, acknowledgments, anything where future-you doesn't need to reference this exchange.
- Example: *"Hey arch — quick clarification on consult-007: when you say 'depth-mode framing,' do you mean per-render or per-session?"*

**Consult mode** (`mode="consult"`):
- Body delivered as a channel notification (the framing/intro prose) AND a structured artifact is written to `docs/crossover/{thread_id}/{NNN}-{you}-{type}.md`.
- Use for: design questions worth a considered response, commissions, debriefs, anything where future-you (or a future session) might want to cite this.
- The artifact is the durable record; the body is the framing.

### The discipline lever

**When in doubt, prefer consult mode.** The slow-loop discipline that produces good cross-session work comes from the artifact format forcing structured thinking — laying out options, naming your instinct, anticipating responses. Chat mode is fast and frictionless; consult mode is fast in transit but slow in composition. That composition discipline is the point.

If you find yourself sending three chat-mode messages in a row to clarify a topic, stop and re-send as a consult.

### Composing a good consult request

When `artifact_body` is the request side of a consult, structure it as:

- **Question**: what you want answered
- **Context**: what the recipient needs to know to answer well
- **Options considered**: alternatives and their trade-offs
- **Instinct**: where you're leaning and why
- **Response format**: how you'd like the answer shaped (prose, list, decision matrix, etc.)

Cite relevant docs by path so the recipient can read them — don't paraphrase what they can read directly.

### Composing a good consult response

When `artifact_body` is the response side:

- **Direct answer**: the response itself, up front
- **Rationale**: why this answer
- **Caveats / edge cases**: where the answer might not hold
- **Open questions**: anything you couldn't resolve, with a recommendation for next steps

## Threading

Threads are sender-declared kebab-case strings:
- `consult-{topic}-{version}` — design consults
- `commission-{NNN}-{topic}` — commission threads
- Free-form for chat-only exchanges

When replying to a message, **always pass the same `thread_id` you saw in the inbound tag**. That keeps the conversation in one thread directory with sequential turn numbering.

When starting a new thread, pick a descriptive ID. If you don't pass one, the bus auto-generates `{you}-to-{recipient}-{date}-{counter}` — workable but less self-documenting.

When a thread reaches its natural conclusion, send a final message with `close=true` to mark the thread `resolved`. Don't fish for follow-ups when the work is done.

## Anti-patterns

- **Don't send unstructured questions in chat mode and call it a consult.** Mode is determined by the discipline you bring, not by claiming a label.
- **Don't ask the user to courier messages** — that's what the bus is for. If a peer isn't currently running, your message sits in their inbox until they start their session. The user can spin them up if your message warrants it.
- **Don't poll for responses.** Messages arrive as `<channel>` notifications automatically. If a peer hasn't responded yet, they haven't read your message yet (or are still composing). Don't badger them with chat-mode "did you see my consult?" pings.
- **Don't skip reading artifacts.** When a consult-mode message arrives, the body is framing. The artifact is the request. Read it before responding.

## When the user is involved

The user can see all bus activity through repo state (artifacts in `docs/crossover/`, git history). Default behavior keeps the user as integrator without requiring active mediation. If you do something significant — closing a thread, sending a major consult — make sure the rationale is visible to them in the session.
