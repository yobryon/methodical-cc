#!/usr/bin/env python3
"""plumb migrate — inventory a MAMA project, and say what is actually alive.

Migration is not a file conversion. A MAMA project's real way of working is
discoverable from its artifacts, and the only question that matters for each one
is the one that caught the drift in the first place:

    Can anyone point to when this was chosen?

An artifact nobody chose and nobody maintains is not state to carry forward — it
is scaffolding that rode in attached to a tool, and carrying it forward is how
the same process comes back under a new plugin's name.

So this reports two things per artifact: **is it there**, and **is it alive** —
last touched, by whom, how long ago, relative to how active the repo is. The
judgment stays with the Product Owner; this just refuses to let them judge from
memory.

Nothing is deleted. MAMA state is left exactly where it is.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Artifacts PLUMB has retired BY DESIGN — these are not judgment calls, they are
# already-made decisions, and each carries the reason it was made.
RETIRED_BY_DESIGN = {
    "implementation_log": (
        "Died with MAMA: triplication. Its phase table duplicated the tracker's "
        "states and nobody maintained it. Issue comments are the play-by-play."),
    "brief": (
        "Died with MAMA: folded into the plan doc plus the kickoff message. A "
        "kickoff is a thing that was SAID at a moment; writing it to a file "
        "records the wrong half."),
    "implementor_state": (
        "Died with MAMA: it existed to APPROXIMATE compaction for an agent that "
        "had none. A running session compacts; a subagent has its parent as "
        "continuity; an ended session resumes with its context. It was also a "
        "fourth ledger — rulings belong in the decisions log, environment traps "
        "in the failure catalog, progress in the tracker."),
}

PROBES = [
    ("architect_state", [".mcc*/architect_state.md"], "carry"),
    ("implementor_state", [".mcc*/implementor_state.md"], "retire"),
    ("sprint_log", [".mcc*/sprint_log.md"], "carry"),
    ("implementation_log", ["docs/**/implementation_log*.md",
                            "docs/**/*implementation-log*.md"], "retire"),
    # Path-SHAPE match, deliberately narrow: a loose "*brief*" glob once
    # flagged a live two-day-old DESIGN brief as a dead MAMA implementor
    # brief — a check that is right about something other than what it does.
    ("brief", ["docs/**/implementor_brief*.md", "docs/**/*implementor-brief*.md",
               ".mcc*/implementor_brief*.md"], "retire"),
    ("plan", ["docs/**/implementation_plan*.md", "docs/**/*_plan.md"], "carry"),
    ("decisions", ["docs/**/decisions_log.md", "docs/**/decisions.md"], "carry"),
    ("backlog", ["docs/**/concept_backlog.md", "docs/**/backlog.md"], "carry"),
    ("roadmap", ["docs/**/roadmap.md"], "carry"),
    ("crossover", ["docs/crossover/**/*.md"], "note"),
]

# MAMA's command surface, and what replaces it. Several have no replacement
# because the operation stopped being necessary rather than moving.
COMMAND_MAP = [
    ("/mama:arch-sprint-prep", "a project-authored skill", "What an arc IS is project-defined. `plumb:establish` helps you write your own"),
    ("/mama:arch-sprint-start", "a project-authored skill", "This is the skill whose template caused the drift. It does not ship"),
    ("/mama:arch-sprint-complete", "a project-authored skill", "Your close, in your vocabulary"),
    ("/mama:impl-begin", "— nothing —", "A user-launched implementor just starts working"),
    ("/mama:impl-end", "— nothing —", "**The chore is gone.** The implementor compacts and continues; there is nothing to end"),
    ("/mama:impl-export", "— nothing —", "The state document is retired; see above"),
    ("/mama:consult-pdt", "the bus", "`bus_send` to the design partner, `gating` if it changes their next move"),
    ("/mama:debrief-pdt", "the bus", "Same channel; the artifact is a ledger entry, not a crossover file"),
    ("/mama:session", "`mcc <name>`", "Session control belongs to the user, not to an agent"),
    ("/mama:pattern-add", "`plumb:promote`", "Norms arrive by recurrence and land in your process document"),
]


def git(root, *args):
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True,
                           text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def repo_pulse(root):
    """How recently the repo itself moved — the baseline 'stale' is measured against."""
    out = git(root, "log", "-1", "--format=%ct")
    return float(out) if out.strip().isdigit() else time.time()


def last_touch(root, rel):
    out = git(root, "log", "-1", "--format=%ct|%an|%s", "--", str(rel))
    if not out or "|" not in out:
        return None
    ts, _, rest = out.partition("|")
    author, _, subject = rest.partition("|")
    if not ts.strip().isdigit():
        return None
    return {"when": float(ts), "author": author, "subject": subject}


def scan(root):
    root = Path(root)
    pulse = repo_pulse(root)
    found = []
    for name, patterns, disposition in PROBES:
        # Patterns overlap by design (implementation_plan*.md and *_plan.md both
        # match the same file), so dedupe BEFORE counting — an inflated count
        # makes an artifact look more alive than it is.
        paths = set()
        for pat in patterns:
            paths |= {p for p in root.glob(pat) if p.is_file()}
        if not paths:
            continue
        entries = []
        for p in sorted(paths)[:40]:
            rel = p.relative_to(root)
            touch = last_touch(root, rel)
            age_days = ((pulse - touch["when"]) / 86400) if touch else None
            entries.append({"path": str(rel), "touch": touch,
                            "age_days": round(age_days, 1) if age_days is not None else None})
        found.append({"role": name, "disposition": disposition,
                      "count": len(paths), "entries": entries})
    return found, pulse


STALE_DAYS = 30.0


def report(root, found, as_json=False):
    if as_json:
        print(json.dumps(found, indent=2))
        return
    if not found:
        print("No MAMA artifacts found. If this project ran MAMA, its state may be\n"
              "under a scoped directory (.mcc-<scope>/) — pass --root explicitly.")
        return

    print("MAMA artifacts in this project\n")
    print("Disposition is a PROPOSAL, not a decision. The question for each is the")
    print("one that caught the drift: can anyone point to when this was chosen?")
    print("Matches are by path shape — a match is a lead, not a verdict. Read a")
    print("file before retiring on its name.\n")

    for f in found:
        role, disp, entries = f["role"], f["disposition"], f["entries"]
        stale = [e for e in entries if e["age_days"] is not None and e["age_days"] > STALE_DAYS]
        untracked = [e for e in entries if e["touch"] is None]
        mark = {"carry": "CARRY ", "retire": "RETIRE", "note": "NOTE  "}[disp]
        print(f"  [{mark}] {role}  ({f['count']} file(s))")
        for e in entries[:4]:
            if e["touch"] is None:
                print(f"           {e['path']}  — untracked by git")
            else:
                age = f"{e['age_days']:.0f}d before HEAD" if e["age_days"] else "current"
                print(f"           {e['path']}  — last touched {age} "
                      f"by {e['touch']['author']}")
        if f["count"] > 4:
            print(f"           …and {f['count'] - 4} more")

        if disp == "retire" and role in RETIRED_BY_DESIGN:
            print(f"           ↳ PLUMB retires this by design: {RETIRED_BY_DESIGN[role][:100]}…")
        elif stale and len(stale) == len(entries):
            print(f"           ↳ Every instance is stale (>{STALE_DAYS:.0f}d). "
                  f"**Strong retirement candidate** — an artifact nobody maintains "
                  f"is a hazard, not state.")
        elif untracked:
            print(f"           ↳ Untracked by git. It was never shared, so it was "
                  f"never load-bearing for anyone but its author.")
        print()

    print("Command surface — what replaces what:\n")
    w = max(len(c) for c, _, _ in COMMAND_MAP)
    for cmd, repl, why in COMMAND_MAP:
        print(f"  {cmd:<{w}}  →  {repl}")
        print(f"  {'':<{w}}     {why}")
    print("\nNothing here has been changed or deleted. Run `plumb:migrate` for the")
    print("conversation that turns this inventory into a manifest and a process document.")


def cmd_scan(args):
    root = Path(args.root).resolve() if args.root else Path.cwd()
    found, _ = scan(root)
    report(root, found, args.json)


def cmd_retired_block(args):
    """Emit the [artifacts.retired] entries this project has earned."""
    root = Path(args.root).resolve() if args.root else Path.cwd()
    found, _ = scan(root)
    print("[artifacts.retired]")
    seen = set()
    for f in found:
        role = f["role"]
        if role in RETIRED_BY_DESIGN and role not in seen:
            seen.add(role)
            print(f'{role:<18} = "{RETIRED_BY_DESIGN[role]}"')
    for role, reason in RETIRED_BY_DESIGN.items():
        if role not in seen:
            print(f'# {role:<16} = "{reason}"   # not found in this project')


def build_parser():
    p = argparse.ArgumentParser(prog="plumb migrate", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root")
    p.add_argument("--root", help=argparse.SUPPRESS)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", parents=[common], help="inventory MAMA artifacts and their liveness")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_scan)
    s = sub.add_parser("retired", parents=[common],
                       help="emit the [artifacts.retired] block this project has earned")
    s.set_defaults(func=cmd_retired_block)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except BrokenPipeError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
