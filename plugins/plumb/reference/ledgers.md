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
directions at once. The diagnosis generalises, so it is stated here as law:

> **A record either sits on a path the work forces you through, or it needs a named reconciliation
> trigger. There is no third option — "discipline" is the name of the missing trigger.**

The diagnostic is the four-channels question. Ask it of every record the way of working declares:

| channel | who forces you through it |
|---|---|
| chat with the PO | they ask; you answer |
| the bus | a peer is blocked until you reply |
| git + docs | the change does not exist until committed |
| the tracker | **often: nothing** |

Anything in the last row's position gets an instrument, a trigger, **or it does not get declared**
— the declaration and its maintenance mechanism arrive together or not at all.

**Gravity is singular.** Narrative status accretes wherever the project's primary thought lives. A
build-heavy project's gravity sits near the tracker and mostly keeps it true; a judgment-heavy
project's gravity sits in its decisions log, and the tracker is a satellite — satellites need
scheduled contact. Watch for the signature: tracker ids hand-written into a document because the
document "felt like the place." That is the well announcing itself. (Some trackers can host
decision records natively; where yours does, co-locating with the gravity is worth more than the
boundary aesthetics — one home matters more than which home.)

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
commit that reaches the default branch closes the issue natively — the sweep is free there.)

**Declare the scope, in the manifest.** `[ledger] scope = "..."` says in your own words what the
ledger does and does not hold — "PO window + cross-team; play-by-play lives on the bus" is a claim
practice can keep, where an unscoped `[ledger]` claims everything and makes the shortfall
invisible. `doctor` will note an undeclared scope. Narrowing the scope does not relax the truth
obligation — it concentrates it: whatever the ledger still holds is exactly what the PO reads.

---

## `nonlinear` — the reference implementation

**This is what the evidence base actually ran on**, across sixteen arcs.

- **Access:** MCP. The agent calls nonlinear's own tools; PLUMB does not proxy them.
- **Mapping — pick by your rhythm.** A bounded unit of work (an arc, a batch) maps to a **project**
  — one project per unit (e.g. *"Sprint 3: SM Connector & Query Engine"*), issues as work items
  within it. A **continuous-flow** project keys projects to **durable themes** instead — the thing
  being built, which survives a change of cadence the way issue ids and decision numbers do.
  Declare which in the process document; both are first-class.
- **States** map directly — nonlinear's workflow is the vocabulary above.
- **Comments are the play-by-play.** This is what replaced the per-arc implementation log, and it is
  why that log is retired: issue comments already hold the narrative, with timestamps and authorship
  the document never had.
- **Attribution — the known gap.** All agents on a project typically share one nonlinear identity, so
  author fields cannot distinguish them. The convention is to prefix every comment with the author's
  bus handle: `(@arch)`, `(@impl)`. **A convention surviving on discipline, inside the artifact whose
  whole purpose is surviving context loss, is the wrong shape** — so where per-agent credentials are
  available, use them. `mcc` injects per-agent environment at session launch and `.mcp.json` can
  reference environment variables, which is the seam that closes this properly.
- **Cross-team:** file issues against a dependency in *that team's* space, and reference issue ids
  bidirectionally.

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
