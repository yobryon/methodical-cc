#!/usr/bin/env python3
"""plumb — the process host.

PLUMB's job is not to help agents work. It is to make specific,
repeatedly-observed failures impossible or loud.

This tool is the part that makes one of those failures impossible: a process a
project evolved away from returning through a tool that still encodes it.

It does that by refusing to know any artifact's filename. Skills ask for a
*role* ("the plan", "the state doc"); the project's own `.plumb.toml` resolves
it. A role the project retired resolves to a refusal carrying the reason and
the date, which is the whole point — deprecated ceremony must fail rather than
fade.

Run `plumb -h` for commands.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PLUMB_VERSION = "0.1.0"
MANIFEST_NAME = ".plumb.toml"

# Exit codes are part of the contract — callers branch on them.
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_RETIRED = 2  # the role exists and is dead; do not work around this
EXIT_UNKNOWN_ROLE = 3
EXIT_NO_MANIFEST = 4


# ---------------------------------------------------------------- TOML reading

def _load_toml(path):
    """Read TOML. Uses stdlib on 3.11+, falls back to a subset parser below."""
    try:
        import tomllib
    except ImportError:
        return _toml_subset(path.read_text(encoding="utf-8"))
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _toml_subset(text):
    """Enough TOML for a manifest: tables, dotted tables, scalars, flat arrays.

    Deliberately small. If a project's manifest needs more than this, it has
    started encoding process semantics — see the design doc's warning about
    exactly that.
    """
    data, table = {}, None
    for raw in text.splitlines():
        line = _strip_comment(raw).strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            table = data
            for part in line[1:-1].strip().split("."):
                table = table.setdefault(part.strip().strip('"'), {})
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        target = data if table is None else table
        target[key.strip().strip('"')] = _toml_value(val.strip())
    return data


def _strip_comment(line):
    """Drop a trailing # comment, respecting quoted strings.

    Retirement reasons are free prose a human wrote; one of them will contain a
    '#' eventually, and truncating it would silently corrupt the reason a
    refusal is supposed to teach with.
    """
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            return line[:i]
    return line


def _toml_value(val):
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        return [_toml_value(v.strip()) for v in inner.split(",") if v.strip()] if inner else []
    if val in ("true", "false"):
        return val == "true"
    try:
        return int(val)
    except ValueError:
        return val


# ------------------------------------------------------------------- discovery

def find_project_root(start=None):
    """Walk up for a manifest, then for a repo root. cwd if neither."""
    here = Path(start or os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / MANIFEST_NAME).is_file():
            return candidate
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return here


class Manifest:
    """The project's declaration of its own way of working."""

    def __init__(self, root, data, path):
        self.root = root
        self.path = path
        self.data = data

    # -- loading

    @classmethod
    def load(cls, root=None, required=True):
        root = Path(root) if root else find_project_root()
        path = root / MANIFEST_NAME
        if not path.is_file():
            if not required:
                return None
            die(
                f"no {MANIFEST_NAME} found at or above {root}.\n"
                f"  This project has not declared a process. Run `plumb init` to scaffold one.",
                EXIT_NO_MANIFEST,
            )
        return cls(root, _load_toml(path), path)

    # -- accessors

    @property
    def process_version(self):
        return self.data.get("process_version")

    @property
    def document(self):
        doc = self.data.get("document")
        return (self.root / doc) if doc else None

    @property
    def roles(self):
        """Live roles are the string entries of [artifacts]; `retired` is a sub-table."""
        return {k: v for k, v in (self.data.get("artifacts", {}) or {}).items()
                if isinstance(v, str)}

    @property
    def retired(self):
        return dict(self.data.get("artifacts", {}).get("retired", {}) or {})

    @property
    def ledger(self):
        return dict(self.data.get("ledger", {}) or {})

    @property
    def actors(self):
        return dict(self.data.get("roles", {}) or {})

    # -- the load-bearing operation

    def resolve(self, role, arc=None):
        """Resolve an artifact role to a path.

        Raises Retired for a role the project killed — carrying the reason, so
        the refusal teaches instead of merely blocking.
        """
        if role in self.retired:
            raise Retired(role, self.retired[role], self.process_version)
        if role not in self.roles:
            raise UnknownRole(role, sorted(self.roles), sorted(self.retired))
        template = self.roles[role]
        if "{arc}" in template:
            if arc is None:
                raise ValueError(
                    f"role '{role}' is arc-scoped ({template}) — pass --arc")
            template = template.replace("{arc}", str(arc))
        return self.root / template


class Retired(Exception):
    def __init__(self, role, reason, version):
        self.role, self.reason, self.version = role, reason, version
        super().__init__(reason)


class UnknownRole(Exception):
    def __init__(self, role, live, retired):
        self.role, self.live, self.retired = role, live, retired
        super().__init__(role)


# --------------------------------------------------------------------- helpers

def die(msg, code=EXIT_ERROR):
    print(f"plumb: {msg}", file=sys.stderr)
    sys.exit(code)


def report_retired(exc):
    """The Sprint 14 guard, spoken out loud."""
    print(
        f"plumb: artifact role '{exc.role}' is RETIRED — this project does not have one.\n"
        f"\n"
        f"  Reason on record: {exc.reason}\n"
        f"\n"
        f"  This is not an error to work around, and creating the file anyway is the\n"
        f"  exact failure this refusal exists to prevent: a process the project evolved\n"
        f"  away from returning through a tool that still encodes it.\n"
        f"\n"
        f"  If the role should genuinely return, that is a PROCESS CHANGE, not a\n"
        f"  workaround: say so in the process document, then edit {MANIFEST_NAME}.",
        file=sys.stderr,
    )
    sys.exit(EXIT_RETIRED)


def report_unknown(exc):
    live = ", ".join(exc.live) or "(none declared)"
    print(
        f"plumb: no artifact role named '{exc.role}'.\n"
        f"  Declared roles: {live}\n"
        + (f"  Retired roles: {', '.join(exc.retired)}\n" if exc.retired else "")
        + f"  Skills address artifacts by role, never by filename. If this project\n"
          f"  needs a new one, declare it in {MANIFEST_NAME}.",
        file=sys.stderr,
    )
    sys.exit(EXIT_UNKNOWN_ROLE)


# -------------------------------------------------------------- process reader

def read_section(doc_text, wanted):
    """Return a markdown section by heading substring, with its subsections.

    This is how a skill consults the project's norms without restating them.
    """
    lines = doc_text.splitlines()
    heads = [(i, len(m.group(1)), m.group(2).strip())
             for i, ln in enumerate(lines)
             if (m := re.match(r"^(#{1,6})\s+(.*)$", ln))]
    needle = wanted.strip().lower()
    hit = next((h for h in heads if needle in h[2].lower()), None)
    if hit is None:
        return None, [h[2] for h in heads]
    start, level, _ = hit
    end = next((i for i, lv, _ in heads if i > start and lv <= level), len(lines))
    return "\n".join(lines[start:end]).rstrip(), [h[2] for h in heads]


# ---------------------------------------------------------------- decision nos.

DECISION_RE = re.compile(r"^\s*#{1,6}\s*D-(\d+)\b|^\s*\|\s*D-(\d+)\b|^\s*\*\*D-(\d+)\b",
                         re.MULTILINE)


def scan_decision_numbers(text):
    return sorted({int(n) for m in DECISION_RE.finditer(text) for n in m.groups() if n})


# -------------------------------------------------------------------- commands

def cmd_init(args):
    root = Path(args.root).resolve() if args.root else find_project_root()
    path = root / MANIFEST_NAME
    if path.exists() and not args.force:
        die(f"{path} already exists (use --force to overwrite)")
    doc = args.document or "docs/way_of_working.md"
    path.write_text(MANIFEST_TEMPLATE.format(document=doc), encoding="utf-8")
    print(f"wrote {path}")
    doc_path = root / doc
    if not doc_path.exists():
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(PROCESS_DOC_TEMPLATE, encoding="utf-8")
        print(f"wrote {doc_path}  (starter process document — make it yours)")
    else:
        print(f"kept  {doc_path}  (already exists)")
    print("\nBoth files belong in version control. The manifest declares WHERE things\n"
          "are and WHAT IS DEAD; the document holds the norms. Skills read both.")


def cmd_path(args):
    mf = Manifest.load(args.root)
    try:
        print(mf.resolve(args.role, arc=args.arc))
    except Retired as exc:
        report_retired(exc)
    except UnknownRole as exc:
        report_unknown(exc)
    except ValueError as exc:
        die(str(exc))


def cmd_roles(args):
    mf = Manifest.load(args.root)
    if args.json:
        print(json.dumps({"live": mf.roles, "retired": mf.retired}, indent=2))
        return
    print("Live roles:")
    for role, tmpl in sorted(mf.roles.items()):
        print(f"  {role:<18} {tmpl}")
    if mf.retired:
        print("\nRetired roles (asking for one is a refusal, with its reason):")
        for role, reason in sorted(mf.retired.items()):
            print(f"  {role:<18} {reason}")


def cmd_process(args):
    mf = Manifest.load(args.root)
    doc = mf.document
    if doc is None:
        die(f"{MANIFEST_NAME} declares no `document` — nowhere to read norms from")
    if not doc.is_file():
        die(f"process document not found: {doc}\n"
            f"  {MANIFEST_NAME} points at it. Either write it or correct the manifest.")
    text = doc.read_text(encoding="utf-8")
    if args.list:
        for m in re.finditer(r"^(#{1,6})\s+(.*)$", text, re.MULTILINE):
            print(f"{'  ' * (len(m.group(1)) - 1)}{m.group(2).strip()}")
        return
    if not args.section:
        print(f"<!-- {doc} (process v{mf.process_version}) -->")
        print(text)
        return
    body, headings = read_section(text, args.section)
    if body is None:
        print(f"plumb: no section matching '{args.section}' in {doc}\n"
              f"  Sections: {', '.join(headings)}", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    print(f"<!-- {doc} § (process v{mf.process_version}) — the project's own words -->")
    print(body)


def cmd_manifest(args):
    mf = Manifest.load(args.root)
    if args.json:
        print(json.dumps({"root": str(mf.root), "manifest": str(mf.path), **mf.data},
                         indent=2, default=str))
        return
    print(f"root            {mf.root}")
    print(f"manifest        {mf.path}")
    print(f"process_version {mf.process_version}")
    print(f"document        {mf.document}")
    print(f"ledger          {mf.ledger.get('adapter', '(none)')}"
          + (f"  space={mf.ledger['space']}" if mf.ledger.get("space") else ""))
    if mf.actors:
        print("actors          " + ", ".join(f"{k}={v}" for k, v in sorted(mf.actors.items())))
    print(f"roles           {len(mf.roles)} live, {len(mf.retired)} retired")


def cmd_decision_next(args):
    mf = Manifest.load(args.root)
    try:
        log = mf.resolve("decisions")
    except (Retired, UnknownRole):
        die("this project declares no `decisions` role — nothing to allocate against")
    if not log.is_file():
        print(1)
        return
    used = scan_decision_numbers(log.read_text(encoding="utf-8"))
    nxt = (used[-1] + 1) if used else 1
    if args.verbose:
        print(f"# highest on record: D-{used[-1] if used else '(none)'} in {log}",
              file=sys.stderr)
        print("# Read the log's tail before writing. Numbers are claimed by the log,\n"
              "# never from memory; on a collision, commit order is the tiebreak and\n"
              "# both entries carry a note pointing at each other.", file=sys.stderr)
    print(nxt)


def cmd_doctor(args):
    mf = Manifest.load(args.root)
    problems, notes = [], []

    doc = mf.document
    if doc is None:
        problems.append(f"{MANIFEST_NAME} declares no `document`")
    elif not doc.is_file():
        problems.append(f"process document missing: {doc}")
    else:
        notes.append(f"process document: {doc} ({len(doc.read_text(encoding='utf-8').splitlines())} lines)")

    if mf.process_version is None:
        problems.append("no `process_version` — the plugin cannot honour a process it can't name")

    for role, tmpl in sorted(mf.roles.items()):
        if "{arc}" in tmpl:
            notes.append(f"role '{role}' is arc-scoped: {tmpl}")
            continue
        p = mf.root / tmpl
        (notes if p.exists() else problems).append(
            f"role '{role}' → {tmpl}" + ("" if p.exists() else "  MISSING"))

    overlap = set(mf.roles) & set(mf.retired)
    for role in sorted(overlap):
        problems.append(f"role '{role}' is declared BOTH live and retired — ambiguous")

    adapter = mf.ledger.get("adapter")
    if not adapter:
        problems.append("no ledger adapter declared")
    elif adapter == "markdown":
        notes.append("ledger adapter 'markdown': running WITHOUT the cross-team half of "
                     "the methodology (see the adapter's degradation table)")
    elif adapter == "linear":
        notes.append("ledger adapter 'linear': shipped UNVERIFIED — no account was "
                     "available to test against")
    else:
        notes.append(f"ledger adapter '{adapter}'")

    for n in notes:
        print(f"  ok   {n}")
    for p in problems:
        print(f"  FAIL {p}")
    if problems:
        print(f"\n{len(problems)} problem(s).")
        sys.exit(EXIT_ERROR)
    print("\nmanifest is coherent.")


# ------------------------------------------------------------------- templates

MANIFEST_TEMPLATE = '''\
# PLUMB process manifest — versioned, hand-edited, read by every skill.
#
# This file declares WHERE the project's artifacts live and WHAT IS DEAD.
# It does not declare how to work; that is prose, in the document below,
# where a human wrote it.

process_version = 1
document = "{document}"

[roles]
architect   = "arch"
implementor = "impl"
design      = "pdt"

[ledger]
# nonlinear | github | jira | linear | markdown
adapter = "markdown"
# space = "PROJ"

[artifacts]
plan            = "docs/arcs/arc_{{arc}}/implementation_plan.md"
state           = "docs/arcs/arc_{{arc}}/state.md"
decisions       = "docs/decisions_log.md"
backlog         = "docs/concept_backlog.md"
failure_catalog = "docs/failure_shapes.md"
roadmap         = "docs/roadmap.md"

[artifacts.retired]
# A role listed here becomes a REFUSAL carrying its reason. This is how a
# process you evolved away from is stopped from returning through a tool that
# still encodes it. Add entries as you kill things; never delete them.
implementation_log = "Died with MAMA: triplication. Issue comments are the play-by-play."
brief              = "Died with MAMA: folded into the plan doc plus the kickoff message."
'''

PROCESS_DOC_TEMPLATE = '''\
# Way of Working

**Status:** Living
**Process version:** 1

This document holds the project's **norms** — standing behaviours, always on,
checked by habit. It is the source of truth for how this project works.

PLUMB skills hold the **procedures** — ordered sequences run rarely, consulted
by name at the moment of need. A skill reads this document for judgment and
defers to it. **Where a skill's guidance and this document disagree, this
document wins, and the skill should say so rather than quietly proceed.**

## Roles

| Role | Identity | What they are |
|---|---|---|
| Product Owner | the human | Direction, decisions, domain knowledge, external actions |
| Architect | `arch` | Design coherence, arc planning, reconciliation |
| Implementor | `impl` | Executes arcs. A **separate session**, not a subagent |

## The Two-Ledger Principle

Execution state and design memory live in different systems, each shaped for
its job.

- **Ledger 1 — the tracker.** Work items, states, the play-by-play of doing.
- **Ledger 2 — the repo.** Docs, decisions, backlog, one plan per arc.

The boundary: *why / what / how-it-should-be* is a doc. *who / when / status /
what-happened* is an issue.

## Norms

<!-- Add yours here as they are earned. The rhythm that works: log an
     observation as an instance; promote it to a norm once it has recurred.
     `plumb:promote` runs that pass. -->

## Reflection Log

| Date | Observation |
|---|---|
'''


# ------------------------------------------------------------------------ main

def build_parser():
    p = argparse.ArgumentParser(prog="plumb", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"plumb {PLUMB_VERSION}")
    p.add_argument("--root", help="project root (default: discovered)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="scaffold a process manifest and starter document")
    s.add_argument("--document", help="path for the process document")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("path", help="resolve an artifact ROLE to a path")
    s.add_argument("role")
    s.add_argument("--arc", help="arc identifier, for arc-scoped roles")
    s.set_defaults(func=cmd_path)

    s = sub.add_parser("roles", help="list declared and retired artifact roles")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_roles)

    s = sub.add_parser("process", help="print the project's process document, or a section")
    s.add_argument("section", nargs="?", help="heading substring to extract")
    s.add_argument("--list", action="store_true", help="list section headings")
    s.set_defaults(func=cmd_process)

    s = sub.add_parser("manifest", help="show the resolved manifest")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_manifest)

    s = sub.add_parser("decision", help="decision-number operations")
    dsub = s.add_subparsers(dest="subcmd", required=True)
    d = dsub.add_parser("next", help="the next unclaimed decision number")
    d.add_argument("-v", "--verbose", action="store_true")
    d.set_defaults(func=cmd_decision_next)

    s = sub.add_parser("doctor", help="validate the manifest against the filesystem")
    s.set_defaults(func=cmd_doctor)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except BrokenPipeError:
        pass
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
