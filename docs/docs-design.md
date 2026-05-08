# Docs Plugin — Design Document

**Status:** Initial design
**Date:** 2026-05-08
**Authors:** Bryon (user) + Claude (design partner)

A companion plugin for sharing project documentation with non-repo stakeholders and ingesting their feedback as structured, repo-local artifacts. Orthogonal to PDT/MAM/MAMA — opt-in, complements the workflow without being load-bearing for it.

---

## 1. Context & Motivation

### The current state

Methodical-CC projects keep all documentation in the repo as markdown — `docs/product/`, `docs/architecture/`, deltas, decision logs, sprint artifacts, etc. This is non-negotiable for git lineage, Claude Code addressability, and the discipline of versioned design. It works perfectly for solo work and for collaborators inside the repo.

It breaks down for **non-repo stakeholders**: business sponsors, subject-matter experts, executive reviewers — people who need to read and react to the work product but who don't live in the repo and typically don't read raw markdown. The current friction modes:

- "Email me a PDF" — one-shot, no round-trip, comments come back as bullet lists detached from the source.
- "Paste it into a doc" — duplicates the source-of-truth into a parallel artifact that drifts.
- "Read it in GitHub" — works for technical reviewers, fails for everyone else.

The cost isn't just the publish step — it's the **return path**. When a reviewer sends "I have concerns about section 3.2," the work to re-anchor that comment to the markdown source falls on the user. Multiply by N comments × M reviewers and the methodology stalls at the review boundary.

### What we want

- Push markdown out as readable artifacts to a stakeholder-facing surface (typically SharePoint, in our case via OneDrive desktop sync — but the plugin doesn't care how it gets there).
- Reviewers comment **in-place** using tools they already know (Word inline comments).
- Pull the comments back as structured, anchored, repo-local feedback files that Claude Code can reason over directly.
- Keep markdown in the repo as the single source of truth. Generated artifacts and pulled feedback are derivative.
- **No new mental model for the user.** The plugin teaches itself; the user runs `mcc docs setup` once, then `/docs:publish` and `/docs:address` from any session.

### What we're NOT building

- No SharePoint API integration, no Graph auth, no MCP server. The plugin writes to and reads from a **local folder** (typically a symlink into a OneDrive-synced SharePoint folder). How that folder gets pushed outward is the user's choice (OneDrive sync, manual rclone, dropbox, whatever).
- No multi-format polyglot output. v1 is **docx in, comments out**, period. Anchored comments are the killer feature; PDF/Pages/Loop don't get you there.
- No cross-plugin awareness in v1. PDT and MAMA don't know about feedback files; the user negotiates that with the agent they're working with. Could surface later if patterns emerge.
- No diff-against-last-publish, no smart skip — re-publishes are full overwrites. Optimization candidate for v1.5.
- No support for input formats other than markdown in v1. `*.md` is implied; non-md matches in patterns fail loudly.

---

## 2. Architecture

### Foundation: local folder + symlink

The plugin operates entirely within a single local folder, by default `.mcc/publish/`. Users typically symlink that folder (or a subdirectory of it) to a OneDrive-synced SharePoint location, but the plugin doesn't know or care. As far as the plugin is concerned, `.mcc/publish/` is just a directory it writes generated docx files into and reads back commented docx files from.

This abstraction is deliberate: it keeps the plugin simple, removes the auth/API surface, and lets users adapt the outward-push mechanism to whatever their org supports without plugin changes.

### File layout

**Per-project state**:
```
{repo}/
├── .mcc/
│   ├── docs-publish.yml         # manifest (committed)
│   └── publish/                 # symlink target, gitignored
│       └── ... generated docx files ...
└── docs/
    └── feedback/                # default; configurable
        ├── spec-20260508T143012.md       # pulled feedback, latest
        └── processed/                    # picked-up by /docs:address
            └── spec-20260507T091522.md
```

`.mcc/publish/` is **gitignored** (machine-specific symlink target, regenerated content). `.mcc/docs-publish.yml` is **committed** (project-level configuration). `docs/feedback/` is **committed** (durable record of stakeholder input, valuable archaeology).

### The manifest: `.mcc/docs-publish.yml`

```yaml
output: docx                          # default; per-pattern overridable
template: .mcc/templates/default.docx # optional; pandoc --reference-doc
structure: mirror                     # mirror (default) | flat
publish_path: .mcc/publish            # default
feedback_path: docs/feedback          # default
pandoc_args: []                       # escape hatch
docs:
  - docs/pdt                          # directory → docs/pdt/**/*.md
  - docs/**/design*.md                # explicit glob
  - docs/product/spec.md              # literal
  - pattern: docs/architecture
    structure: flat
  - pattern: docs/product/roadmap.md
    publish_as: roadmap-2026.docx
```

**Resolution rules:**

- A bare string can be a literal path, a directory, or a glob. Directories implicitly become `<dir>/**/*.md`. Globs are evaluated as-is.
- A mapping form supports per-pattern overrides (`output`, `structure`, `publish_as`, `template`).
- Markdown-only constraint: any matched non-`.md` path **fails loudly** ("you matched X.json — adjust your pattern"). The user is intelligent and intentional; we don't silently filter.
- `publish_as` only valid on patterns that resolve to a single file. Conflicts (two files claiming the same output name) **fail loudly** at publish time.

**Why YAML, not TOML or JSON:** comments, multiline strings, hand-editability. The manifest is meant to be lived-in.

### Generated artifact naming

- `structure: mirror` (default) → output preserves source tree under `publish_path/`. `docs/product/spec.md` → `.mcc/publish/docs/product/spec.docx`.
- `structure: flat` → output uses slugified filename only. `docs/product/spec.md` → `.mcc/publish/spec.docx`.
- `publish_as: foo.docx` → exact override, ignores structure for that file.

Mirror is the default because it makes filename collisions impossible without explicit configuration, and SharePoint folder browsers handle the depth fine.

### Feedback file format

One file per pulled docx per pull cycle. Filename: `<doc-slug>-<YYYYMMDD>T<HHMMSS>.md`. Slug derived from the doc's source path (e.g., `docs/product/spec.md` → `spec` or `product-spec` for collision avoidance).

Format:

```markdown
---
source: docs/product/spec.md
published_as: .mcc/publish/docs/product/spec.docx
pulled_at: 2026-05-08T14:30:12-07:00
reviewers: [Alice Chen, Bob Patel]
comment_count: 7
---

# Feedback on docs/product/spec.md

## Comment 1 — Alice Chen, 2026-05-07T11:14:00

**Anchored to:** Section "Pricing tiers"
**Excerpt:** "Pro tier is $49/month with all features unlocked"

Should we offer an annual discount? Most B2B buyers expect at least 15% off for annual prepay.

---

## Comment 2 — Bob Patel, 2026-05-07T14:22:00

**Anchored to:** Section "Pricing tiers"
**Excerpt:** "all features unlocked"

This contradicts the feature-gating decision in [decision-log:032]. Need to reconcile.

---

...
```

The shape is optimized for Claude Code consumption: each comment has the heading section it lives under, the anchored text excerpt, the comment body, and author/date. The agent can reason "Alice and Bob both flagged Section 'Pricing tiers' — let's discuss."

**Format-iteration target.** This is the surface most likely to evolve. The schema is intentionally simple and additive-friendly.

### Pickup and the `processed/` subdirectory

When `/docs:address` finishes triaging a feedback file (proposing edits, filing follow-ups, deciding to defer items), it `git mv`s the file into `docs/feedback/processed/`. The session-start hook only counts files in the top level of `docs/feedback/` (excluding `processed/`) when surfacing unaddressed feedback.

This pattern (move-on-complete) is preferred over a sidecar marker file because:

- Single source of truth — the file's location is its state.
- Visible in `git status` — provenance lives in the move commit.
- No risk of marker drift (sidecar present but file removed, or vice versa).
- Mirrors how `arch-sprint-complete` graduates implemented deltas.

### CLI vs plugin split

| Layer | Responsibility |
|---|---|
| `mcc docs setup` | Interactive onboarding. Writes initial manifest. Adds `.gitignore` entries for `.mcc/publish/`. Detects pandoc, prompts install if missing. |
| `mcc docs publish [patterns...]` | Mechanical work. Resolves manifest patterns (or CLI-passed patterns, narrowing to a subset). Invokes pandoc per file. Writes to `publish_path`. |
| `mcc docs pull` | Mechanical work. Walks `publish_path` for docx files with comments. Parses `comments.xml` and body anchors. Emits feedback files into `feedback_path`. |
| `/docs:publish` | Plugin command. Readiness check before calling CLI: any open deltas touching docs in scope? any unmerged work the architect noted as in-flux? Then invokes `mcc docs publish` with appropriate patterns. |
| `/docs:address` | Plugin command. Triages the latest unprocessed feedback file(s): proposes edits per comment, applies or files them, optionally defers items. Auto-moves the file to `processed/` on completion. |
| SessionStart hook | Counts files in `feedback_path` (excluding `processed/`). Surfaces a one-line "docs: N unaddressed feedback files" if any. |

CLI does the deterministic, scriptable work. Plugin adds the judgment — readiness, triage, follow-up. Skills are not v1.

---

## 3. Workflow

### Setup (once per project)

1. User: `mcc docs setup` — interactive. Asks about output format (default docx), structure (default mirror), template (optional), publish_path (default `.mcc/publish/`), feedback_path (default `docs/feedback/`). Writes `.mcc/docs-publish.yml`. Adds `.mcc/publish/` to `.gitignore` if not already.
2. User: outside the plugin, creates the symlink to OneDrive (or whatever outward mechanism). E.g., `ln -s /mnt/c/Users/bryon/OneDrive/Sites/Project-X/Docs .mcc/publish` (Windows path through WSL). Plugin doesn't help with this — explicit user action, OS-specific.
3. User: edits the manifest's `docs:` list to declare what gets published. Setup may seed an initial empty list with comments suggesting common patterns.

### Publish cycle

1. User: `/docs:publish` from any active session. Plugin asks the agent to do a readiness check (anything in flux? open deltas?), surfaces concerns, then runs `mcc docs publish`.
2. Plugin: `mcc docs publish` resolves patterns, runs pandoc per file, writes docx into `publish_path`. Symlink → OneDrive → SharePoint via sync.
3. User: notifies stakeholders (out of scope — Teams, email, whatever).
4. Stakeholders: open the docx in Word (online or desktop), read, comment.

### Pull cycle

1. User: `mcc docs pull`. Plugin walks `publish_path`, identifies docx files with new comments (anything we haven't seen before — tracked via per-doc marker on the docx itself or by comparing comment IDs against a manifest in `.mcc/publish-state.json`). Emits feedback files into `feedback_path`.
2. Next session start: hook surfaces "docs: 3 unaddressed feedback files."
3. User: `/docs:address`. Agent reads feedback files, triages each comment, proposes edits to the source markdown, applies approved changes, files deferred items as deltas/decisions/concept-backlog entries (depending on what plugin context the user is in).
4. On completion: feedback file `git mv`d to `processed/`.

---

## 4. Open implementation seams

These are intentional unknowns that v1 will resolve through use:

- **Pull idempotency.** How do we know which comments are new since last pull? Options: (a) write a sidecar `.mcc/publish-state.json` with `<doc>: {last_pull: timestamp, seen_comment_ids: [...]}`. (b) Read author Word comments and only emit if any are not in a previously-pulled feedback file. Option (a) is simpler and faster; we'll start there.
- **Multi-reviewer attribution accuracy.** Word stores `<w:comment w:author="...">`, but the author is whatever Word identity is configured locally. Trust it; document the gotcha. Don't try to map back to org identity in v1.
- **Anchored excerpt length.** Short anchors (a few words) are unambiguous when the source markdown is stable; longer excerpts are easier to spot but break if text edits land before pickup. Use ~80–120 chars of surrounding context, with the literal commented text marked by `**` or similar.
- **Heading section detection.** Walk backwards from the comment anchor through the docx body looking for the nearest preceding `<w:pStyle w:val="Heading*"/>`. Standard pattern, well-documented.
- **Pandoc on Windows.** Ships natively (winget/choco/MSI). Setup detects and prompts install if missing.

---

## 5. Why this design

### Why local folder + symlink instead of Graph API

- Zero auth surface in the plugin. Every M365 tenant configures Graph differently; debugging customer auth issues would dwarf the value.
- Zero cloud dependency. The plugin works for any outward-push mechanism (SharePoint via OneDrive, S3, Dropbox, manual scp).
- The user already solved the "get this folder synced" problem when their org adopted M365. We don't re-solve it.
- Trade-off: requires symlink setup. Acceptable — done once, documented in `mcc docs setup`.

### Why opt-in with a manifest instead of "publish everything"

- Stakeholder-facing artifacts are intentional. The user shouldn't surface every working paper, draft, or internal note to executives by default.
- A manifest forces the question "is this ready for outside eyes?" at config time, not at publish time.
- Glob support keeps the manifest from being verbose for large doc trees.

### Why move-on-complete instead of sidecar markers

- Single source of truth on file state.
- Provenance lives in git history of the move commit.
- Mirrors `arch-sprint-complete`'s pattern for graduating deltas — one consistent metaphor across the plugin family.

### Why no skills in v1

- The two commands (`/docs:publish`, `/docs:address`) carry their own guidance.
- Skills add value when guidance is *cross-cutting* and gets pulled in via Claude Code's skill system. The docs workflow is point-in-time, command-shaped.
- Can crystallize a skill later if patterns emerge that need to surface outside the commands.

### Why no cross-plugin awareness in v1

- PDT and MAMA already have rich session-start hooks; loading docs-feedback awareness into them adds noise that not every project will want.
- The user is the integrator. If they're in PDT and there's pending docs feedback, they'll notice via the docs hook and choose when to engage.
- v2 if patterns emerge.

---

## 6. v2 candidates (deferred)

- **Diff-against-last-publish.** Skip files unchanged since last publish to reduce churn in the synced folder.
- **PDF output with annotations.** Some orgs prefer PDF reviews. Adobe annotation parsing is more complex than docx comments.
- **SharePoint Pages output.** For low-stakes docs where comments don't need to be anchored — render markdown to a Page, let people comment in Teams threads.
- **Cross-plugin hooks.** PDT and MAMA SessionStart blocks mention pending docs feedback inline.
- **Graph API direct.** If the symlink approach hits a wall (e.g., user can't sync a particular SharePoint site), a direct Graph push/pull becomes worth the complexity.
- **Bidirectional structural edits.** If a stakeholder rewrites a paragraph in Word (Track Changes), parse and surface as a proposed diff rather than a comment. Probably never worth it — the comment workflow is tighter.

---

## 7. Naming

Plugin name: `docs`. Considered `liaison`, `share`, `pub`. `docs` won on clarity and family-style brevity, accepting the namespace risk if a future plugin in the ecosystem also wants the name. Commands invoke as `/docs:publish`, `/docs:address`. CLI subcommands invoke as `mcc docs setup|publish|pull`.
