#!/usr/bin/env python3
"""plumb ledger — execution state, for a project that has nowhere else to put it.

PLUMB does not wrap trackers. `nonlinear` and `linear` are MCP servers the agent
already holds; `github` and `jira` have mature CLIs and MCPs that carry their own
guidance at the point of use. Wrapping any of them would duplicate a well-guided
tool and could only fall behind it — so for those, PLUMB ships GUIDANCE
(`plumb ledger guide`) and gets out of the way.

`markdown` is the exception, because there is nothing to call. One file per
issue under a directory the manifest names. It keeps the properties that make
Ledger 1 worth having — survives context loss, readable without waiting on
anyone's turn — and loses cross-team visibility entirely, which the guidance
says out loud rather than letting a project discover it when a dependency first
matters.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

STATES = ("triage", "backlog", "todo", "in_progress", "in_review", "done")
SLUG_RE = re.compile(r"[^a-z0-9]+")

ISSUE_TEMPLATE = """---
id: {id}
title: {title}
state: {state}
arc: {arc}
created: {created}
---

# {id} — {title}

{body}

## Log

<!-- The play-by-play. Append as work moves; never rewrite. Prefix each entry
     with who wrote it, because a shared identity cannot be recovered later. -->
"""


def slug(text, limit=48):
    return SLUG_RE.sub("-", text.lower()).strip("-")[:limit] or "issue"


class MarkdownLedger:
    def __init__(self, root, base="docs/ledger"):
        self.root = Path(root)
        self.base = self.root / base

    def arc_dir(self, arc):
        d = self.base / f"arc-{arc}" if arc else self.base / "unfiled"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _next_id(self, arc):
        d = self.arc_dir(arc)
        n = 0
        for f in self.base.rglob("*.md"):
            m = re.match(r"(\d+)-", f.name)
            if m:
                n = max(n, int(m.group(1)))
        return n + 1

    def create(self, arc, title, body="", state="todo"):
        if state not in STATES:
            raise ValueError(f"state must be one of {STATES}")
        n = self._next_id(arc)
        ident = f"{n:03d}"
        path = self.arc_dir(arc) / f"{ident}-{slug(title)}.md"
        path.write_text(ISSUE_TEMPLATE.format(
            id=ident, title=title, state=state, arc=arc or "",
            created=time.strftime("%Y-%m-%d"), body=body or "_(no description)_"),
            encoding="utf-8")
        return path

    def find(self, ident):
        for f in self.base.rglob(f"{ident}-*.md"):
            return f
        for f in self.base.rglob("*.md"):
            if f.name.startswith(str(ident)):
                return f
        return None

    def comment(self, ident, body, author=None):
        path = self.find(ident)
        if path is None:
            raise FileNotFoundError(f"no issue {ident}")
        who = author or os.environ.get("PLUMB_AGENT") or "unknown"
        stamp = time.strftime("%Y-%m-%d %H:%M")
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n**(@{who}) {stamp}**\n\n{body}\n")
        return path

    def set_state(self, ident, state):
        if state not in STATES:
            raise ValueError(f"state must be one of {STATES}")
        path = self.find(ident)
        if path is None:
            raise FileNotFoundError(f"no issue {ident}")
        text = path.read_text(encoding="utf-8")
        new, n = re.subn(r"^state: .*$", f"state: {state}", text, count=1,
                         flags=re.MULTILINE)
        if not n:
            raise ValueError(f"{path} has no `state:` field to move")
        path.write_text(new, encoding="utf-8")
        return path

    def list(self, arc=None, state=None):
        out = []
        root = self.arc_dir(arc) if arc else self.base
        if not root.exists():
            return out
        for f in sorted(root.rglob("*.md")):
            text = f.read_text(encoding="utf-8")
            meta = dict(re.findall(r"^(id|title|state|arc): (.*)$", text, re.MULTILINE))
            if state and meta.get("state") != state:
                continue
            meta["path"] = str(f.relative_to(self.root))
            out.append(meta)
        return out


def _resolve(args):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import plumb
    mf = plumb.Manifest.load(args.root)
    adapter = mf.ledger.get("adapter")
    return mf, adapter


def cmd_guide(args):
    ref = Path(__file__).resolve().parent.parent / "reference" / "ledgers.md"
    if not ref.is_file():
        print(f"plumb: guidance not found at {ref}", file=sys.stderr)
        sys.exit(1)
    text = ref.read_text(encoding="utf-8")
    name = args.adapter
    if not name:
        try:
            _, name = _resolve(args)
        except SystemExit:
            name = None
    if not name:
        print(text)
        return
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import plumb
    body, _ = plumb.read_section(text, f"`{name}`")
    if body is None:
        print(text)
        return
    print(body)
    if name == "linear":
        print("\n⚠ This adapter is shipped UNVERIFIED — no account was available to "
              "test against. Correct it in your process document as you learn.")
    if name == "markdown":
        print("\nThis project is running WITHOUT the cross-team half of the "
              "methodology. See the table above for what else degrades.")


def cmd_states(_args):
    print("PLUMB's normalized state vocabulary:\n")
    print("  " + " → ".join(STATES))
    print("\nStates move as work moves. Where a tracker cannot express one of these,")
    print("its guidance says so rather than approximating silently.")


def _md(args):
    mf, adapter = _resolve(args)
    if adapter != "markdown":
        print(f"plumb: this project's ledger adapter is '{adapter}', not 'markdown'.\n"
              f"  PLUMB does not proxy that tracker — use its own tools, and run\n"
              f"  `plumb ledger guide` for how an arc and the states map onto it.",
              file=sys.stderr)
        sys.exit(1)
    return MarkdownLedger(mf.root, mf.ledger.get("path", "docs/ledger"))


def cmd_create(args):
    body = args.body
    if body == "-":
        body = sys.stdin.read()
    print(_md(args).create(args.arc, args.title, body or "", args.state))


def cmd_comment(args):
    body = args.body if args.body != "-" else sys.stdin.read()
    print(_md(args).comment(args.id, body))


def cmd_state(args):
    print(_md(args).set_state(args.id, args.state))


def cmd_list(args):
    rows = _md(args).list(args.arc, args.state)
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    if not rows:
        print("(no issues)")
        return
    for r in rows:
        print(f"  {r.get('id','?'):<6} {r.get('state','?'):<12} {r.get('title','')}")


def build_parser():
    p = argparse.ArgumentParser(prog="plumb ledger", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root")
    p.add_argument("--root", help=argparse.SUPPRESS)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("guide", parents=[common],
                       help="how an arc and the states map onto this project's tracker")
    s.add_argument("adapter", nargs="?",
                   choices=("nonlinear", "github", "jira", "linear", "markdown"))
    s.set_defaults(func=cmd_guide)

    s = sub.add_parser("states", parents=[common], help="the normalized state vocabulary")
    s.set_defaults(func=cmd_states)

    s = sub.add_parser("create", parents=[common], help="[markdown] create an issue")
    s.add_argument("title")
    s.add_argument("--arc")
    s.add_argument("--body", default="")
    s.add_argument("--state", default="todo", choices=STATES)
    s.set_defaults(func=cmd_create)

    s = sub.add_parser("comment", parents=[common], help="[markdown] append to the log")
    s.add_argument("id")
    s.add_argument("body", help="text, or '-' for stdin")
    s.set_defaults(func=cmd_comment)

    s = sub.add_parser("state", parents=[common], help="[markdown] move an issue's state")
    s.add_argument("id")
    s.add_argument("state", choices=STATES)
    s.set_defaults(func=cmd_state)

    s = sub.add_parser("list", parents=[common], help="[markdown] list issues")
    s.add_argument("--arc")
    s.add_argument("--state", choices=STATES)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_list)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"plumb ledger: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
