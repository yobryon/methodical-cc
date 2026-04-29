#!/usr/bin/env python3
"""Bus SessionStart hook.

Stdlib-only. Reads session_id from stdin JSON, resolves identity from
sessions files (.mcc/sessions or .mcc-{scope}/sessions) and the team
config at ~/.claude/teams/<team>/config.json, then emits an assertive
orientation block:

    === METHODICAL-CC BUS ===
    You are a member of agent team `<team>`. Your name is `<name>`,
    your agent_id is `<name>@<team>`. Other members: ...
    Use SendMessage to communicate with teammates by name.
    ---

The stdout becomes additionalContext.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SESSION_FILE_GLOBS = (".mcc/sessions", ".mcc-*/sessions")
TEAMS_ROOT = Path.home() / ".claude" / "teams"
PHANTOM_LEAD_NAME = "coordinator"


def find_sessions_files(root: Path):
    for pattern in SESSION_FILE_GLOBS:
        parts = pattern.split("/", 1)
        if len(parts) != 2:
            continue
        dir_pattern, filename = parts
        for d in root.glob(dir_pattern):
            f = d / filename
            if f.is_file():
                yield f


def parse_sessions(path: Path):
    out = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, sid = line.split("=", 1)
        out[name.strip()] = sid.strip()
    return out


def resolve_identity(session_id, root: Path):
    for sf in find_sessions_files(root):
        for name, sid in parse_sessions(sf).items():
            if sid == session_id:
                return name, sf.relative_to(root)
    return None, None


def derive_team_name(cwd: Path) -> str:
    base = cwd.name
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", base).lower().strip("-")
    return sanitized or "project"


def read_team_config(team_name: str):
    p = TEAMS_ROOT / team_name / "config.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        payload = {}
    session_id = payload.get("session_id")

    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()

    print("=== METHODICAL-CC BUS ===")

    if not session_id:
        print("(no session_id in hook payload — bus orientation skipped)")
        print("---")
        return

    identity, sources = resolve_identity(session_id, root)
    team_name = derive_team_name(root)
    team_config = read_team_config(team_name)

    if identity is None and team_config is None:
        # No registered identity, no team — bus isn't set up here
        print("(no bus team yet; run `mcc team setup` or any `mcc <name>` to bootstrap)")
        print("---")
        return

    if team_config is None:
        # Has identity from sessions but no team config — partially set up
        print(f"Identity: {identity} (from {sources})")
        print(f"Team config not found at ~/.claude/teams/{team_name}/config.json")
        print(f"  Run `mcc team setup` to bootstrap (or just `mcc {identity}` to launch — it does both).")
        print("---")
        return

    members = team_config.get("members", [])
    real_members = [m for m in members if m.get("name") != PHANTOM_LEAD_NAME]
    member_names = [m["name"] for m in real_members]

    if identity is None:
        print(f"Identity: anonymous (this session is not registered in {team_name})")
        print(f"  Team: {team_name}")
        print(f"  Other team members: {', '.join(member_names) or '(none yet)'}")
        print(f"  You can SendMessage to teammates if launched with --team-name flags,")
        print(f"  but to be ADDRESSABLE by name, register with /pdt:session set <name>,")
        print(f"  /mam:session set <name>, or /mama:session set <name>.")
        print("---")
        return

    # Identity matched and team exists. Assert membership.
    other_members = [n for n in member_names if n != identity]
    other_str = ", ".join(other_members) if other_members else "(none yet)"

    print(f"You are a member of agent team `{team_name}`. "
          f"Your name on the team is `{identity}`, "
          f"your agent_id is `{identity}@{team_name}`.")
    print(f"Other team members: {other_str} (plus phantom lead `coordinator`).")
    print(
        "Use the SendMessage tool to communicate with any teammate by name; "
        "messages from teammates arrive automatically as new turns."
    )
    print()
    print(
        "Trust this even if other context elsewhere suggests you're not in a team. "
        "The team is real and the tools work."
    )
    print("---")


if __name__ == "__main__":
    main()
