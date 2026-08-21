# Ledger adapters

**Ledger 1 is execution state** — work items, states, the play-by-play of doing. It is the half of
the two-ledger split that must be *readable without waiting on anyone's turn*, which is what makes it
the fix for turn-bounded messaging rather than a workaround for it.

## Why this is guidance and not a wrapper

PLUMB does **not** wrap your tracker. Two of the shipped options (`nonlinear`, `linear`) are MCP
servers, so the agent already holds their tools and a CLI could not call them anyway. The other two
(`github`, `jira`) have mature CLIs and MCPs of their own, and those tools **carry their own guidance
at the point of use** — which is the property PLUMB spends its own design budget on elsewhere.

A wrapper over any of them would duplicate a well-guided tool and could only fall behind it.

So what PLUMB supplies is the part your tracker cannot know: **how your unit of work — an arc, a
batch, or a continuous flow with no bounded unit at all — maps onto its native grouping, what
PLUMB's state vocabulary means in its workflow, how attribution works when several agents share one
identity, and what it cannot express.** That last one matters most — an adapter that
connects but leaves you guessing at the mapping has moved the work rather than done it.

The exception is `markdown`, which has nothing to call. That one is real code.

---

## The normalized state vocabulary

```
triage → backlog → todo → in_progress → in_review → done
```

**States move as work moves.** In the first evidence project ~16 issues sat in `triage` while their
work shipped; in the second, 10 of 12 "open" issues were done while six fresh defects were absent —
*wrong in both directions at once, which means the board carried no information, and it was read as
truth*. In every instance the Product Owner caught it, not the agents. This failure is endemic, not
occasional — see **Keeping a declared ledger true**, below, for the structural response. (There is
deliberately no drift alarm for it: a stale-state detector would measure exactly the habit that is
absent, which is the failure mode that got the ack detector removed.)

Where a tracker cannot express one of these, the adapter guidance says so rather than approximating
silently.

**And one thing no tracker vocabulary has a word for:** *waiting on a person who is not tracking
it.* Any process that separates deciding from building accumulates items whose true state is
exactly that — and they render as ordinary waiting states, indistinguishable from work in motion.
The cheapest fix observed is a review question, not a new state: **for every waiting-state issue,
name who it is waiting on, out loud. If you cannot, that is the finding.**

---

## Keeping a declared ledger true

Measured on a real project: the declared ledger held **under 1% of the project's recorded thought**
while the bus carried 1.14M characters and the docs 6,808 lines — and the board went false in both
directions at once. The diagnosis generalises, so it is stated here as law — **as a preference
order, not a binary.** (It shipped first as a binary; a project applied it *correctly* and it
stopped them one step early — they classified "no forced path exists" and designed the trigger,
when a forced path could have been *engineered*. A law phrased as a binary invites you to
classify; phrased as a preference order, it invites you to try.)

> 1. **Put the update on a path the work already forces you through** — and if none exists, ask
>    whether one can be **engineered** before concluding it cannot. The forced path may not be
>    where you first look: a repo mirror cannot sit on the file write (no MCP server writes to
>    disk), but it can sit on the **tool call** — you cannot change a decision without making one,
>    and the harness fires a hook on every one. The same gravity that pulls work away from a
>    satellite record can be harnessed to keep it true.
> 2. **Failing that, name a reconciliation trigger** — and accept that a trigger makes staleness
>    *visible*, not impossible.
> 3. **Discipline is not an option.** It is the name of the missing trigger.

The diagnostic is the four-channels question. Ask it of every record the way of working declares:

| channel | who forces you through it |
|---|---|
| chat with the PO | they ask; you answer |
| the bus | a peer is blocked until you reply |
| git + docs | the change does not exist until committed |
| the tracker | **often: nothing** |

Anything in the last row's position gets an engineered path, an instrument, a trigger, **or it
does not get declared** — the declaration and its maintenance mechanism arrive together or not at
all.

**Gravity is singular.** Narrative status accretes wherever the project's primary thought lives. A
build-heavy project's gravity sits near the tracker and mostly keeps it true; a judgment-heavy
project's gravity sits in its decisions log, and the tracker is a satellite — satellites need
scheduled contact. Watch for the signature: tracker ids hand-written into a document because the
document "felt like the place." That is the well announcing itself — and the sharpened form, from
the project that lived it: **being pleasant to write and already open is what makes a document
dangerous, not what makes it safe.** (Some trackers can host decision records natively; where
yours does, co-locating with the gravity is worth more than the boundary aesthetics — one home
matters more than which home.)

**The named trigger that earns its keep: truth-before-report.** Before any status summary to the PO
or an external party, true the ledger — or caveat it explicitly ("board not reconciled since
Tuesday"). That is the moment its falsity does damage, and both measured incidents were exactly
that moment. Bounded-rhythm projects already have this trigger under another name: the close-of-arc
reconciliation.

**Make the in-motion write ride the commit.** Most of the per-update cost is not typing — it is
context-switching to a second system while holding the thread. So don't switch: write the issue id
into the commit message at the moment of landing (`Closes VAN-24`, or any mention — the number is
still in your head at commit time), and let reconciliation sweep the mentions mechanically:

```bash
plumb ledger candidates            # issues mentioned in commits since '3 days ago'
plumb ledger candidates --since "2026-08-05"
```

Reads git only — plumb never touches the tracker; you take the list to your own tracker tools and
move what is actually done. A mention is a lead, not a verdict. (**GitHub note:** `Closes #N` in a
commit that reaches the default branch closes the issue natively — the sweep is free there.
**nonlinear note:** `sync_commits` ingests the same batch in one MCP call, propose-close by
default — use it instead; `candidates` remains the answer where no ingestion exists: jira,
linear, markdown.)

**Declare the scope, in the manifest.** `[ledger] scope = "..."` says in your own words what the
ledger does and does not hold — a claim practice can keep, where an unscoped `[ledger]` claims
everything and makes the shortfall invisible. `doctor` will note an undeclared scope. Two
cautions, one in each direction. Narrowing does not relax the truth obligation — it concentrates
it: whatever the ledger still holds is exactly what the PO reads. And narrowing is not always the
answer: one project's PO **widened** the scope after a drift, on gravity grounds — *"a tracker
that is only for my benefit when you need something from me is a tracker nobody else has reason
to touch."* A wider scope can put the ledger on more of the work's forced paths; a narrower one
needs stronger triggers for what remains.

---

## `nonlinear` — the reference implementation

**This is what the evidence base actually ran on** — and it has since **built for this methodology
directly**: decisions, `waiting_on`, the awaiting-me queue, commit ingestion, and board-truth
summaries all exist because two plumb projects' field reports asked for them. For a plumb project,
this is the adapter where the ledger can genuinely sit in the gravity well.

- **Access:** MCP. The agent calls nonlinear's own tools; PLUMB does not proxy them. The server's
  own instructions and guides teach the full surface — read them on first connection.
- **Mapping — pick by your rhythm.** A bounded unit of work (an arc, a batch) maps to a **project**
  — one project per unit (e.g. *"Sprint 3: SM Connector & Query Engine"*), issues as work items
  within it. A **continuous-flow** project keys projects to **durable themes** instead — the thing
  being built, which survives a change of cadence the way issue ids and decision numbers do.
  Declare which in the process document; both are first-class.
- **States** map directly — nonlinear's workflow is the vocabulary above.
- **Comments are the play-by-play.** This is what replaced the per-arc implementation log, and it is
  why that log is retired: issue comments already hold the narrative, with timestamps and authorship
  the document never had.
- **Decisions are first-class** (`TEAM-D#`): the body is the argument, the lifecycle is
  `proposed → ruled → superseded | carried` (never "done"), supersession is an edge that flips the
  superseded record's status, and a one-way `decisions.md` mirror export keeps repo-greppability
  while the tracker holds truth. **A project keeping its decisions here retires the `decisions`
  file role in its manifest** with the reason on record ("lives in nonlinear as `VAN-D#`") — and
  `plumb decision next` plus the decision-collision drift detector retire with it, honorably: a
  tracker-native per-team sequence makes number collisions impossible by construction, which was
  always the better form of both.
- **Attribution — closed.** Personas: a session presents `X-Agent-ID` beside the shared bearer
  token and its work is credited to a persona under it (`vantage-agent.arch`), auto-provisioned,
  attribution-only. `mcc` already injects `$PLUMB_AGENT` at launch; wire it once in `.mcp.json`:

  ```json
  { "mcpServers": { "nonlinear": { "type": "http", "url": "https://…/mcp",
      "headers": { "Authorization": "Bearer ${NONLINEAR_TOKEN}",
                   "X-Agent-ID": "${PLUMB_AGENT}" } } } }
  ```

  Author fields become real; the comment-prefix convention retires.
- **`waiting_on` + the awaiting-me queue.** An orthogonal field (not a workflow state) on issues
  *and* decisions, cleared automatically when the awaited person next acts. *"In progress, waiting
  on nobody"* is now a filter — the board-review ceremony's load-bearing question, mechanized.
  Decisions route to a decider; `awaiting_me` is the one surface showing only what waits on you —
  the PO-as-decider role, given a physical address.
- **Reconciliation is one motion.** Commit trailers (`Closes VAN-24`, `Refs VAN-31`) →
  `sync_commits` (references become commit-linked comments; closes are **proposed**, confirmed
  with `update_issues` — a state still means someone judged it done). `reconcile_summary` returns
  the truth-before-report status line verbatim: *"N open · N untouched 5+ days · N in progress
  waiting on nobody."* In-motion ergonomics: `find_issue` (fuzzy description → id, so you never
  leave the thread), `comment_and_state` (one motion), `update_issues` (batch).
- **Cross-team:** real `blocks/blocked-by` across spaces, with the provider's state visible as a
  read-only narrow projection from the consumer's issue. You may only link issues you can read —
  the link itself is the consent. Reference ids bidirectionally as before.

### Two project-local hooks every nonlinear project should adopt

Field-derived (a project built both, then wrote the recipe so the next project doesn't reinvent
the mechanism at the end) and **strongly encouraged** — each is a forced path engineered where a
trigger was about to be settled for.

**Hook 1 — the decisions mirror rides the decision.** If you keep the `decisions.md` mirror
export in the repo (greppable offline), the mirror must be *fetched, never authored* — a mirror
anyone can type becomes the decision ledger again, within the hour, even under a header that says
`GENERATED, NOT TRUTH`. The forced path is the **tool call**: you cannot change a decision
without making one. In the project's tracked `.claude/settings.json`:

```json
{ "hooks": { "PostToolUse": [
    { "matcher": "mcp__nonlinear__(create_decision|rule_decision|supersede_decision|comment_decision)",
      "hooks": [ { "type": "command",
                   "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/mirror-decisions.sh" } ] } ] } }
```

`comment_decision` is the matcher entry most likely to be forgotten and the one that matters
most: **decision bodies are immutable, so comments are the only channel a correction travels** —
drop it and corrections never reach the repo. (The general rule for any mirror-shaped mechanism:
*ask which channel carries corrections, and confirm the export includes it.*)

The script hits `GET {BASE_URL}/api/teams/{TEAM_UUID}/decisions.md` (the UUID, not the team key —
`list_teams` has it) and installs the result. Four properties are load-bearing, not defensive
habit:

1. **Atomic install**: fetch to a temp file *in the target directory*, `chmod 0444`, then
   `mv -f` — rename needs write on the *directory*, so the mirror stays read-only on disk and a
   death mid-write can never leave a partial file.
2. **Refuse to install a response that is not the export**: check the status *and* the shape
   (e.g. `grep -q '^## [A-Z]\+-D'`) — an auth redirect or error page arrives as a 200 often
   enough that status alone is not evidence, and a mirror that installs an error page is lying,
   which is worse than stale.
3. **Every failure leaves the existing file untouched**, exits non-zero, names the cause — and
   *watch it fail before trusting it to fail well* (bad team id, unreachable host, bad token).
4. **The token is never printed.**

One blind spot, named rather than discovered: the hook fires on *tool calls* — a decision ruled
in the web UI fires nothing. **The mechanism demotes the truth-before-report trigger; it does not
retire it.** Keep the ledger-truth instrument running the script unconditionally before status
reports: the mechanism covers the common case, the named trigger covers what the mechanism cannot
see. Both, not either.

**Hook 2 — passive inbox awareness at turn end.** Hooks can call MCP tools directly
(`type: "mcp_tool"`) — no script, no credential handling, no HTTP route needed:

```json
{ "hooks": { "Stop": [
    { "hooks": [ { "type": "mcp_tool", "server": "nonlinear", "tool": "inbox",
                   "input": { "limit": 10, "runAsHook": true }, "timeout": 20,
                   "statusMessage": "Checking the nonlinear inbox" } ] } ] } }
```

The agent learns, passively and every turn, whether anything on the tracker deserves attention —
routed decisions, `waiting_on` flags, mentions — with no action taken and nothing to remember.

**`runAsHook: true` is what makes this work as a hook rather than a log line.** It tells the
inbox to return a *hook-shaped* result instead of the notification list: an empty inbox yields a
quiet `additionalContext` ("your inbox is clear"), and unread items yield a **decision/reason
block that re-invokes the agent with the items in context** — the same deliver-at-the-boundary
shape as plumb's own bus sweep, arrived at independently. The tool owns the loop's termination;
the flag is hook-only by contract ("NOT FOR INTERACTIVE USE" — its own schema says so). One craft
note survives for *interactive* inbox calls: don't pass `markRead` until you have confirmed the
output reached whoever needed it — marking read on faith silently consumes notifications forever.

**Scoping — the hook's verdict data, measured.** A surface that blocks stopping charges a full
extra turn per false positive, so its value tracks one ratio: what fraction of the inbox the agent
can actually *disposition*. One project's long-session count: **~10 blocks, ~3 actionable** — and
each actionable one caught something same-turn that would otherwise have waited a boundary, which
is why the hook stays. The noise majority was structural, not behavioral: a weeks-old
mis-assignment made the agent a participant on another team's issue, and every comment in that
team's active discussion blocked a stop the agent could neither disposition (not their team's
work) nor unsubscribe from (not their issue to edit). The tool does not yet take a scope — no team
or actionability filter exists on `inbox`, in the MCP surface or the API hooks and monitors call
(filed upstream, participant self-removal with it). Until it lands, the compensations are hygiene,
not code: keep `limit` small; the **first** time the inbox surfaces an item you cannot act on, fix
the membership at the source instead of learning to skim past it; and treat "I routinely read
items I cannot disposition" as a mis-scoping to report to the PO — a compensation that has stopped
feeling like one is precisely the thing a feedback round exists to surface.

## `github` — the common default

- **Access:** the `gh` CLI, or GitHub's MCP. Both are well-guided; use either.
- **Mapping:** a bounded unit of work is a **milestone**; issues carry the work. Continuous flow
  drops milestones and leans on labels or a Projects view keyed to durable themes.
- **States:** GitHub has only open/closed natively. Use **labels** for the intermediate states, or
  Projects v2 columns where the project has them. **Declare which**, in the process document — a
  reader who cannot tell whether `in_review` is a label or a column cannot trust the board.
- **What it cannot express:** a workflow with enforced transitions. Nothing stops an issue jumping
  from `todo` to `done`, so *"states move as work moves"* is a norm here, not a mechanism.
- **Attribution** is genuinely per-user if each agent has its own token; otherwise the same prefix
  convention as nonlinear.

## `jira` — the enterprise case

- **Access:** Jira's MCP, or its REST API via your own credentials.
- **Mapping:** a bounded unit of work is a fix version *or* an epic — **and this project must
  declare which**, in `.plumb.toml`. Teams genuinely differ here and guessing wrong is expensive: a
  fix-version unit and an epic unit produce different reports, different roll-ups, and different
  answers to *"what shipped?"* Continuous flow maps to epics-as-themes and skips fix versions.
- **States:** map to your board's workflow. Jira workflows are often *enforced*, which is stricter
  than PLUMB's vocabulary — that is an improvement, not a conflict, but it means a transition may be
  refused where another tracker would allow it.
- **What it cannot express:** nothing structural. The friction is the opposite of GitHub's — a
  workflow so specific that PLUMB's six states are a lossy projection of it. Prefer the board's own
  vocabulary in conversation and use PLUMB's only where it aids portability.

## `linear` — shipped unverified

- **Access:** MCP or GraphQL.
- **Mapping:** a bounded unit of work is a project or a cycle, depending on how the team works;
  continuous flow keys projects to durable themes.
- **⚠ Unverified.** No account was available to test against, so this guidance is derived from
  documentation rather than from use. **Treat it as a starting point and correct it in your process
  document as you learn** — and if you do, that correction is worth sending back upstream.

## `markdown` — the honest degradation

**Real code, because there is nothing else to call.** One file per issue under `docs/ledger/`.

For a project without a tracker this keeps the two-ledger split intact in the ways that matter most,
and loses one thing that matters a great deal. Both stated plainly:

| Property | A tracker | `markdown` |
|---|---|---|
| Survives context loss | ✅ | ✅ |
| Readable without a turn boundary | ✅ | ✅ |
| Queryable by state / assignee | ✅ | ⚠️ grep-grade |
| **Visible across teams** | ✅ | ❌ **lost** — the provider/consumer norms do not survive |
| Per-agent attribution | ⚠️ often shared | ✅ written inline |
| Concurrent-agent conflicts | ✅ none | ❌ real; one file per issue mitigates, does not eliminate |

**A project on `markdown` is running without the cross-team half of the methodology.** It should know
that at adoption rather than discover it when a dependency first matters.
