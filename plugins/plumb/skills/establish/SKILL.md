---
name: establish
description: Negotiate this project's way of working with the Product Owner, and record it. New project — interview. Existing project — read what is there, infer the de facto process, propose it back. Produces the manifest, the process document, and the project's own skills. Re-runnable, because process evolves. Use when adopting PLUMB, when a project's way of working has drifted from what is written, or when a phase change makes the old shape wrong.
---

# Establish this project's way of working

Everything else in PLUMB defers to a document. **This is the skill that writes it — with the Product
Owner, not for them.**

MAMA shipped a process and asked projects to conform. PLUMB does the opposite: the process is
negotiated, recorded in the project, and **PLUMB reads it.** So this conversation is not setup. It is
the product.

---

## The stance, before you start

Three things that will make this go wrong if you forget them:

**1. Do not propose a methodology.** You are not here to sell an arc rhythm. If you arrive with a
shape and collect agreement to it, you have written a template with extra steps — and a template
arriving attached to a tool is the precise failure PLUMB exists to prevent.

**2. Write the minimum, and expect to be wrong.** A process document authored in one sitting, before
any work has happened, is a guess wearing a document's clothes. Establish the *skeleton* — who does
what, where things live, what is already dead — and let norms arrive the way the good ones actually
arrive:

> Every good norm in the source project's process document was **logged as an instance and promoted
> after it recurred.** Left to memory, they stay in the log where nobody reads them.

So the reflection log matters more than the norms section on day one. The norms section is supposed
to be thin at the start. **Say that out loud** so its thinness does not read as incompleteness.

**3. This skill is re-runnable, and that is the point.** An establishing step that runs once is a
template. Say when you finish: *"run this again when the way of working has moved."*

---

## Step 1 — Read before you ask

Never open with a blank page. Even on a greenfield repo there is usually something.

```bash
plumb manifest 2>/dev/null      # already established? then this is a RE-run — see Step 6
plumb ceremony list
```

Then read what the project already says about itself:

- `CLAUDE.md` / `AGENTS.md` — often the de facto process, written informally
- `README`, `CONTRIBUTING`, anything in `docs/`
- **`git log`** — the real cadence. Commit shapes, release rhythm, who touches what
- Existing trackers, issue templates, PR templates
- **MAMA artifacts** (`.mcc/`, `docs/sprint/`, `architect_state.md`) — see Step 5

Come to the conversation with **observations, not questions**. *"You seem to release on a tag and
squash-merge everything else — is that a rule or a habit?"* beats *"how do you release?"*

---

## Step 2 — Establish the skeleton, by asking

Six things. Ask about what is not already answered by Step 1; confirm what is.

1. **Who is in this?** Which roles actually exist here — is there a separate implementor session, a
   design partner, only the PO and one agent? Do not assume PLUMB's default cast. A project with one
   agent and one human is legitimate and much of PLUMB still applies.
2. **Where does execution state live?** The tracker, or nothing yet. This sets `[ledger] adapter`.
   If they have no tracker, say plainly what the `markdown` adapter costs them — the cross-team half
   of the methodology does not survive it.
3. **Where does design memory live?** Which documents exist, which are load-bearing, which are
   fiction. This sets `[artifacts]`.
4. **What is already dead?** The highest-value question in the interview, and the one nobody thinks
   to ask. *"What have you tried and stopped doing? What document does nobody maintain?"* Every
   answer becomes an `[artifacts.retired]` entry **with its reason**, and that entry is a permanent
   guard against the thing coming back attached to a tool.
5. **What do you do repeatedly that you would want shorthand for?** This is Step 4.
6. **What has gone wrong more than once?** Not to fix now — to know what this project's guards should
   watch, and what its failure catalog will open with.

---

## Step 3 — Write the manifest and the document

```bash
plumb init --document <path they chose>   # scaffolds both; skips an existing document
plumb doctor                              # then make it pass
```

Then edit both to match the conversation. Rules:

- **`[artifacts]` contains only roles this project actually has.** Delete the scaffold's suggestions
  it does not use. An unused role is a suggestion, and suggestions become obligations.
- **`[artifacts.retired]` carries reasons, in the PO's own words where possible.** The reason is what
  makes the refusal teach instead of merely block.
- **The process document holds only what they actually said.** Do not fill sections to make it look
  complete. An empty Norms section with a live Reflection Log is *correct* on day one.
- Set `process_version = 1`. It moves when the process moves, not when PLUMB does.

Show them the retired list explicitly and explain what it will do. It is the least obvious part of
the manifest and the one with the sharpest teeth.

---

## Step 4 — Author the project's own skills

**This is the half that distinguishes PLUMB from MAMA, and it is easy to skip.**

The shipped skill set is a **floor, not a ceiling**. A project's own procedures — the release
ceremony, the grain-change sequence, the way this team onboards a data source — belong in the
project's own `.claude/skills/`, invocable by name, so the PO gets shorthand through *their* workflow
rather than ours.

From Step 2's question 5, and from what `git log` showed you:

```bash
plumb ceremony new <name> --description "<when to reach for it>"
```

Then fill it in **with them**. Two rules the scaffold states and you must enforce:

1. **Address artifacts by role, never by filename.** Project-authored skills are *more* likely to
   smuggle a template than PLUMB's own, not less — they are written close to the work, in a hurry,
   by someone who knows the filename. This is where the drift will come back if it comes back.
2. **Carry sequence, not standing behaviour.** If a step is really *"always do X"*, it is a norm —
   move it to the document.

**Do not invent ceremonies.** If nothing comes to mind, write none, and say what will prompt one
later: the second time you run something, that is `plumb:ceremony`.

---

## Step 5 — If this is an existing MAMA project

Full migration is a separate piece of work and is deliberately not built yet. What you can do now:

- **Read the MAMA artifacts as evidence of the de facto process**, and say plainly which parts were
  *chosen* versus which arrived as scaffolding. The distinguishing question is the one that caught
  it last time: **can anyone point to when this was decided?** If not, it is a candidate for
  `[artifacts.retired]`, not for carrying forward.
- Anything MAMA created that the project stopped maintaining goes straight into the retired table
  with the reason. That is the migration's most valuable half and it costs nothing.
- Do **not** delete MAMA state or disable the plugin. Both can coexist; say so.

---

## Step 6 — If this is a RE-run

Different conversation, and the more important one. The project has been working; the document has
been sitting still. Assume drift and go looking for it.

- **Diff the document against reality.** What does it say that is no longer true? What is everyone
  doing that it never mentions?
- **Ask what died since last time** — retired entries are additive, and this is when most of them
  get added.
- **Run `plumb:promote`** if reflection-log entries have recurred enough to become norms. That is the
  mechanism by which this document is *supposed* to grow.
- **Bump `process_version`** if the shape changed, and note what moved.

The tell that a re-run was overdue: *nobody can point to when the current way of working was
decided.*

---

## Done when

- [ ] `plumb doctor` passes
- [ ] Every role in `[artifacts]` is one the project actually has
- [ ] `[artifacts.retired]` has at least one entry, with a reason — a project with nothing dead has
      either not been asked, or is genuinely new, and you should know which
- [ ] The process document says only what the PO said
- [ ] The reflection log exists and its purpose was explained
- [ ] Project skills authored, or explicitly none with a note on what would prompt one
- [ ] Both files committed
- [ ] The PO knows this skill is **re-runnable**, and roughly when to re-run it
