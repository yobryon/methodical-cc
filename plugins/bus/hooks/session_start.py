#!/usr/bin/env python3
"""Bus SessionStart hook.

Stdlib-only. Reads session_id from stdin JSON, resolves identity from sessions
files, and emits to stdout:
  - Identity context ("you are operating as X on the bus")
  - Active threads where this identity is a participant
  - Unread message count

The stdout becomes additionalContext per Channels conventions.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SESSION_FILE_GLOBS = (
    ".pdt/sessions", ".pdt-*/sessions",
    ".mam/sessions", ".mam-*/sessions",
    ".mama/sessions", ".mama-*/sessions",
)
INBOX_ROOT = Path(".mcc/bus/inbox")
CROSSOVER_ROOT = Path("docs/crossover")
THREAD_STATE_FILE = ".bus-state.json"
CONSUMED_DIR = ".consumed"


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


def list_pending(identity: str, root: Path):
    d = root / INBOX_ROOT / identity
    if not d.exists():
        return []
    return [p for p in d.iterdir() if p.is_file() and p.suffix == ".json"]


def list_active_threads(identity: str, root: Path):
    """Return list of (thread_id, state_dict) for open threads where identity is a participant."""
    out = []
    crossover = root / CROSSOVER_ROOT
    if not crossover.exists():
        return out
    for d in sorted(crossover.iterdir()):
        if not d.is_dir():
            continue
        state_file = d / THREAD_STATE_FILE
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            continue
        if state.get("status") != "open":
            continue
        if identity not in state.get("participants", []):
            continue
        out.append((d.name, state))
    return out


def humanize_age(iso: str | None) -> str:
    if not iso:
        return "unknown"
    try:
        t = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return iso
    delta = datetime.now(timezone.utc) - t
    secs = int(delta.total_seconds())
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        payload = {}
    session_id = payload.get("session_id")

    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()

    print("=== METHODICAL-CC BUS ===")

    if not session_id:
        print("(no session_id in hook payload — bus identity cannot be resolved)")
        return

    identity, sources = resolve_identity(session_id, root)

    if identity:
        print(f"Identity: {identity}  (registered in {sources})")
        print(f"  Use peer_send to message peers; received messages arrive as <channel source=\"bus\" ...> tags.")
    else:
        print(f"Identity: anonymous  (this session is not registered)")
        print(f"  You can still send messages, but peers cannot address you by name.")
        print(f"  Run /pdt:session set <name>, /mam:session set <name>, or /mama:session set <name> to register.")

    # Pending unread
    if identity:
        pending = list_pending(identity, root)
        if pending:
            print(f"Unread: {len(pending)} message(s) — will deliver in chrono order.")

    # Active threads
    if identity:
        threads = list_active_threads(identity, root)
        if threads:
            print(f"Active threads:")
            for tid, state in threads:
                last = humanize_age(state.get("last_activity_at"))
                awaiting = state.get("awaiting") or "—"
                participants = ", ".join(p for p in state.get("participants", []) if p != identity)
                print(f"  - {tid}  (with {participants})  last: {last}, awaiting: {awaiting}")

    print("---")


if __name__ == "__main__":
    main()
