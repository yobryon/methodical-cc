#!/usr/bin/env python3
"""mcc - methodical-cc helper CLI

Run `mcc -h` for help, `mcc <command> -h` for command-specific help.

Sessions are registered from inside Claude Code via /pdt:session,
/mam:session, or /mama:session — and via `mcc create <name>` from the shell.

Plugin scoping: enable/disable/switch operate on the current project; setup
operates on the user scope. Per-project always wins over user when both are set.
"""

import os
import re
import shlex
import shutil
import subprocess
import argparse
import sys
from pathlib import Path

MCC_VERSION = "1.29.0"

import json
import time

PLUGINS = ("pdt", "mam", "mama", "bus", "docs", "plumb")
MARKETPLACE = "methodical-cc"
STATE_DIR_GLOBS = (".mcc", ".mcc-*")

LEGACY_PLUGIN_PREFIXES = ("pdt", "mam", "mama")  # legacy state-dir prefixes (pre-3.0.0)
TEAMS_ROOT = Path.home() / ".claude" / "teams"
PHANTOM_LEAD_NAME = "coordinator"
PHANTOM_LEAD_SESSION_ID = "00000000-0000-0000-0000-000000000000"
DEFAULT_LEAD_MODEL = "claude-opus-4-7"


# ----------------------------- Helpers -----------------------------

def die(msg, code=1):
    print(f"mcc: {msg}", file=sys.stderr)
    sys.exit(code)


def have_claude():
    return shutil.which("claude") is not None


def claude_plugins(*args, capture=False):
    """Run `claude plugins ...`. Returns CompletedProcess."""
    cmd = ["claude", "plugins", *args]
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True)
    return subprocess.run(cmd)


def find_state_dirs():
    cwd = Path.cwd()
    dirs = []
    for pattern in STATE_DIR_GLOBS:
        dirs.extend(p for p in cwd.glob(pattern) if p.is_dir())
    return sorted(dirs)


def find_session(name):
    for d in find_state_dirs():
        sessions_file = d / "sessions"
        if not sessions_file.exists():
            continue
        for line in sessions_file.read_text().splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            n, sid = line.split("=", 1)
            if n.strip() == name:
                return sid.strip(), sessions_file
    return None, None


def find_session_args(name):
    """Look up per-session launch args declared as `<name>:args=<string>` in the
    sessions file. Returns the raw string (suitable for `shlex.split`) or None.

    Co-located with the session id by design: one source of truth, viewable in
    one file, no separate index to keep in sync.
    """
    key = f"{name}:args"
    for d in find_state_dirs():
        sessions_file = d / "sessions"
        if not sessions_file.exists():
            continue
        for line in sessions_file.read_text().splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            n, val = line.split("=", 1)
            if n.strip() == key:
                return val.strip()
    return None


def detect_version(state_file):
    """Pull a version stamp from architect_state.md; tolerate bold markers."""
    if not state_file.exists():
        return None
    content = state_file.read_text().replace("*", "")
    m = re.search(r"(MAMA|MAM|PDT)\s+Version:\s*([0-9.]+)", content)
    return m.group(2) if m else None


def prompt(message, default=None):
    suffix = f" [{default}]" if default else ""
    raw = input(f"{message}{suffix}: ").strip()
    return raw or (default or "")


def confirm(message, default=True):
    suffix = "[Y/n]" if default else "[y/N]"
    raw = input(f"{message} {suffix} ").strip().lower()
    if not raw:
        return default
    return raw.startswith("y")


def is_windows():
    return os.name == "nt"


def is_macos():
    return sys.platform == "darwin"


def user_local_bin():
    return Path.home() / ".local" / "bin"


def directory_on_path(directory):
    target = os.path.normcase(os.path.normpath(str(directory)))
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        if os.path.normcase(os.path.normpath(entry)) == target:
            return True
    return False


def install_mcc_on_path(source_dir):
    """Make mcc available as a plain `mcc` command from any terminal.

    Linux/Mac: symlink ~/.local/bin/mcc -> <source>/mcc
    Windows:   write ~/.local/bin/mcc.cmd as a small forwarder to <source>/mcc.cmd

    Both approaches auto-pick-up updates because the source script in the
    marketplace clone is the one that gets updated.

    Handles re-runs gracefully: if the link/shim already points to the right
    place, says so and moves on. If it points somewhere stale (e.g. an older
    marketplace path), updates it transparently. If it's a regular file the
    user placed there themselves, asks before clobbering.
    """
    target_dir = user_local_bin()
    target_dir.mkdir(parents=True, exist_ok=True)

    if is_windows():
        target = target_dir / "mcc.cmd"
        source = source_dir / "mcc.cmd"
        shim = f'@echo off\r\n"{source}" %*\r\n'
        if target.exists():
            existing = target.read_text()
            if existing == shim:
                print(f"  ✓ mcc.cmd already installed at {target} (no changes)")
                return target_dir
            # Existing forwarder shim from us, just pointing elsewhere — update silently
            looks_like_our_shim = (
                existing.strip().startswith("@echo off")
                and "mcc.cmd" in existing
                and len(existing.splitlines()) <= 4
            )
            if looks_like_our_shim:
                target.write_text(shim)
                print(f"  ✓ Updated mcc.cmd at {target} to point at current marketplace path")
                return target_dir
            # Looks like something the user wrote — ask before clobbering
            print(f"  {target} exists and doesn't look like an mcc forwarder.")
            if not confirm("  Replace it?", default=False):
                print(f"  Skipped — left {target} as-is.")
                return target_dir
            target.write_text(shim)
            print(f"  ✓ Wrote forwarder at {target}")
        else:
            target.write_text(shim)
            print(f"  ✓ Wrote forwarder at {target}")
    else:
        target = target_dir / "mcc"
        source = source_dir / "mcc"
        if target.is_symlink():
            current = os.readlink(target)
            if target.resolve() == source.resolve():
                print(f"  ✓ mcc already linked at {target} (no changes)")
                return target_dir
            # Symlink we (or a prior install) created — update transparently
            target.unlink()
            target.symlink_to(source)
            print(f"  ✓ Updated symlink: {target} → {source}")
            print(f"      (was pointing to: {current})")
            return target_dir
        if target.exists():
            print(f"  {target} exists and is not a symlink (looks like a manual copy or unrelated file).")
            if not confirm("  Replace it with a symlink?", default=False):
                print(f"  Skipped — left {target} as-is.")
                return target_dir
            target.unlink()
        target.symlink_to(source)
        print(f"  ✓ Symlinked {target} → {source}")

    return target_dir


def warn_if_target_not_on_path(target_dir):
    if directory_on_path(target_dir):
        return
    print()
    print(f"  Note: {target_dir} is not on your PATH.")
    if is_windows():
        print("  Add it permanently with PowerShell:")
        print(f'      [Environment]::SetEnvironmentVariable("Path", "$env:Path;{target_dir}", "User")')
        print("  Or via Windows Settings → System → About → Advanced system settings → Environment Variables.")
        print("  Restart your terminal after the change takes effect.")
    else:
        shell = os.environ.get("SHELL", "")
        rc = "~/.zshrc" if "zsh" in shell else "~/.bashrc"
        print(f"  Add this line to {rc} (then start a new shell):")
        print('      export PATH="$HOME/.local/bin:$PATH"')


# ----------------------------- Team management -----------------------------

def _compute_default_team_name(cwd):
    """Default team name = sanitized repo basename. Lowercase, replace non-alnum with dashes."""
    base = cwd.name
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", base).lower().strip("-")
    return sanitized or "project"


def _team_name_file(cwd=None):
    """Persisted team-name lives at <project>/.mcc/team-name regardless of scoping.
    A project's team is a single thing even if state is split across .mcc-{scope}/ dirs.

    Presence of this file is also the **opt-in marker** for team mode:
      - `mcc team setup` writes this file and bootstraps the team
      - `mcc <name>` / `mcc create <name>` only do team-related work
        (claude --team-name flags, settings.json env, team config maintenance)
        when this file exists
    Without it, mcc operates as plain session-naming sugar over `claude -r`.
    """
    cwd = cwd or Path.cwd()
    return cwd / ".mcc" / "team-name"


def _team_mode_enabled(cwd=None):
    """True iff team mode has been explicitly opted into (via `mcc team setup`)
    for this project. Implicit setup was retired in 1.6.0 — projects that just
    want session-naming convenience get plain `claude -r` without team flags."""
    return _team_name_file(cwd).exists()


def _load_persisted_team_name(cwd=None):
    """Read the team name from .mcc/team-name. Returns None if not set."""
    f = _team_name_file(cwd)
    if not f.exists():
        return None
    name = f.read_text().strip()
    return name or None


def _persist_team_name(name, cwd=None):
    """Write team name to .mcc/team-name, creating .mcc/ if needed."""
    f = _team_name_file(cwd)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(name + "\n")


def _passive_upgrade_team_name(cwd=None):
    """If no persisted team name yet but a team config exists at the dirname-derived
    name, silently persist that default so future renames are explicit. Idempotent."""
    cwd = cwd or Path.cwd()
    if _load_persisted_team_name(cwd) is not None:
        return  # already persisted
    default = _compute_default_team_name(cwd)
    if (TEAMS_ROOT / default / "config.json").exists():
        _persist_team_name(default, cwd)


def derive_team_name(cwd=None):
    """Resolve the team name for the current project.

    Order: persisted (.mcc/team-name) → dirname-derived default. The persisted
    file is the source of truth once set; before that, the dirname is used.
    """
    cwd = cwd or Path.cwd()
    persisted = _load_persisted_team_name(cwd)
    if persisted:
        return persisted
    return _compute_default_team_name(cwd)


def team_dir(team_name):
    return TEAMS_ROOT / team_name


def team_config_path(team_name):
    return team_dir(team_name) / "config.json"


def team_inboxes_dir(team_name):
    return team_dir(team_name) / "inboxes"


def now_ms():
    return int(time.time() * 1000)


def make_member(name, team_name, agent_type="teammate", model=DEFAULT_LEAD_MODEL,
                cwd=None):
    return {
        "agentId": f"{name}@{team_name}",
        "name": name,
        "agentType": agent_type,
        "model": model,
        "joinedAt": now_ms(),
        "tmuxPaneId": "",
        "cwd": str(cwd or Path.cwd()),
        "subscriptions": [],
    }


def read_team_config(team_name):
    p = team_config_path(team_name)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def write_team_config(team_name, config):
    p = team_config_path(team_name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(config, indent=2))


def collect_registered_identities():
    """Find all (name, session_id) pairs across this project's sessions files."""
    out = []
    for d in find_state_dirs():
        sf = d / "sessions"
        if not sf.exists():
            continue
        for line in sf.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            n, sid = line.split("=", 1)
            n = n.strip()
            if ":" in n:
                continue  # namespaced metadata (e.g. `<name>:args`); not a session id
            out.append((n, sid.strip()))
    return out


def ensure_team_setup(verbose=False):
    """Idempotent: ensure the team config exists and members are current.

    Returns the team_name. Safe to call repeatedly. Logs only when changes happen
    (or always, when verbose=True). Callers are responsible for deciding whether
    to invoke this — `mcc team setup` always does, and `mcc <name>` / `mcc create`
    only do when team mode is opted-in (see `_team_mode_enabled`)."""
    team_name = derive_team_name()
    config = read_team_config(team_name)
    cwd = Path.cwd().resolve()

    created = False
    if config is None:
        # Bootstrap a fresh config with phantom lead
        config = {
            "name": team_name,
            "description": f"methodical-cc team for {team_name}",
            "createdAt": now_ms(),
            "leadAgentId": f"{PHANTOM_LEAD_NAME}@{team_name}",
            "leadSessionId": PHANTOM_LEAD_SESSION_ID,
            "members": [
                make_member(PHANTOM_LEAD_NAME, team_name,
                            agent_type="team-lead", cwd=cwd)
            ],
        }
        created = True
        if verbose:
            print(f"  Created team '{team_name}' at {team_config_path(team_name)}")

    # Ensure inboxes dir
    inbox_dir = team_inboxes_dir(team_name)
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Top up members from registered identities
    existing_names = {m["name"] for m in config["members"]}
    added = []
    for name, _sid in collect_registered_identities():
        if name in existing_names:
            continue
        config["members"].append(make_member(name, team_name, cwd=cwd))
        existing_names.add(name)
        added.append(name)

    if created or added:
        write_team_config(team_name, config)
        if verbose and added:
            print(f"  Added members: {', '.join(added)}")

    # Ensure CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 in project settings
    ensure_experimental_teams_flag(verbose=verbose)

    return team_name


def ensure_experimental_teams_flag(verbose=False):
    """Add CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 to .claude/settings.json env."""
    settings_path = Path(".claude") / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except Exception:
            settings = {}
    else:
        settings = {}

    env = settings.setdefault("env", {})
    if env.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") == "1":
        return False  # already set

    env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    if verbose:
        print(f"  Set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 in {settings_path}")
    return True


def cmd_team_setup(args):
    """Interactive: prompt for team name (default = persisted or dirname).
    Non-interactive: `mcc team setup --name <name>` skips the prompt."""
    print("Bus team setup")
    print("==============")
    print()

    explicit_name = args.name

    # Run passive upgrade first so a pre-existing team gets its name persisted
    # before we ask the user about it
    _passive_upgrade_team_name()
    current = _load_persisted_team_name()
    default = current or _compute_default_team_name(Path.cwd())

    if explicit_name:
        chosen = explicit_name.strip()
    else:
        chosen = prompt("Team name", default=default).strip()
    chosen = re.sub(r"[^a-zA-Z0-9_-]+", "-", chosen).lower().strip("-")
    if not chosen:
        die("team name cannot be empty")

    if current and chosen != current:
        # User wants to rename. Offer to move the existing team dir if it
        # exists at the old name.
        old_dir = TEAMS_ROOT / current
        new_dir = TEAMS_ROOT / chosen
        if old_dir.exists():
            print()
            print(f"Renaming team '{current}' → '{chosen}'.")
            print(f"  Existing team dir: {old_dir}")
            if new_dir.exists():
                die(f"target {new_dir} already exists; refusing to overwrite")
            if not confirm(f"Move team dir to {new_dir}?", default=True):
                die("rename aborted")
            shutil.move(str(old_dir), str(new_dir))
            print(f"  ✓ moved to {new_dir}")
            print(f"  (Open sessions still hold the old --team-name flag in memory; "
                  f"`mcc <name>` to relaunch them under the new name.)")

    _persist_team_name(chosen)
    print(f"Persisted team name: {chosen} (in {_team_name_file()})")
    print()

    team_name = ensure_team_setup(verbose=True)
    config = read_team_config(team_name)
    print()
    print(f"Team: {team_name}")
    print(f"Config: {team_config_path(team_name)}")
    print(f"Inboxes: {team_inboxes_dir(team_name)}")
    print(f"Members ({len(config['members'])}):")
    for m in config["members"]:
        marker = " (lead — phantom)" if m["name"] == PHANTOM_LEAD_NAME else ""
        print(f"  - {m['name']} ({m['agentId']}){marker}")
    print()
    print("Setup complete. Sessions registered via /{plugin}:session set <name> or")
    print("`mcc create <name>` automatically join this team on launch.")


def cmd_team_status(args):
    team_name = derive_team_name()
    config = read_team_config(team_name)
    print(f"Team: {team_name}")
    print(f"Config: {team_config_path(team_name)}")
    if config is None:
        print("  (not set up — run `mcc team setup` or any `mcc <name>` will create it)")
        return
    print(f"Lead (phantom): {config.get('leadAgentId', '?')}")
    print(f"Members ({len(config['members'])}):")
    inbox_root = team_inboxes_dir(team_name)
    for m in config["members"]:
        marker = " (phantom)" if m["name"] == PHANTOM_LEAD_NAME else ""
        inbox_file = inbox_root / f"{m['name']}.json"
        pending = ""
        if inbox_file.exists():
            try:
                inbox = json.loads(inbox_file.read_text())
                unread = sum(1 for msg in inbox if not msg.get("read"))
                if unread:
                    pending = f"  ({unread} unread)"
            except Exception:
                pass
        print(f"  - {m['name']} ({m['agentId']}){marker}{pending}")


# ----------------------------- Migration -----------------------------

def find_legacy_dirs():
    """Return list of (legacy_path, target_path) pairs for any pre-3.0.0 plugin dirs."""
    cwd = Path.cwd()
    pairs = []
    for prefix in LEGACY_PLUGIN_PREFIXES:
        for path in sorted(cwd.glob(f".{prefix}")) + sorted(cwd.glob(f".{prefix}-*")):
            if not path.is_dir():
                continue
            name = path.name  # e.g. ".mama-backend" or ".pdt"
            scope = name[len(prefix) + 2:]  # strip ".{prefix}-" or ".{prefix}"
            target_name = ".mcc" + (f"-{scope}" if scope else "")
            pairs.append((path, cwd / target_name))
    return pairs


def in_git_repo():
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, check=False,
        )
        return r.returncode == 0 and r.stdout.strip() == "true"
    except FileNotFoundError:
        return False


def _git_mv(src, dst):
    """git mv if in repo, else plain rename. Returns True on success."""
    if in_git_repo():
        r = subprocess.run(["git", "mv", str(src), str(dst)], capture_output=True, text=True)
        if r.returncode == 0:
            return True
        # fall through to plain mv if git refuses (e.g. file isn't tracked)
    try:
        shutil.move(str(src), str(dst))
        return True
    except Exception as e:
        print(f"  ! could not move {src} → {dst}: {e}")
        return False


def _merge_sessions_files(src, dst):
    """Merge src sessions file into dst (concat + dedupe by name, last write wins)."""
    src_lines = src.read_text().splitlines() if src.exists() else []
    dst_lines = dst.read_text().splitlines() if dst.exists() else []
    merged = {}
    order = []
    for line in dst_lines + src_lines:  # src wins on collision (later)
        line = line.strip()
        if not line or "=" not in line:
            continue
        name, sid = line.split("=", 1)
        name = name.strip()
        if name not in merged:
            order.append(name)
        merged[name] = sid.strip()
    dst.write_text("\n".join(f"{n}={merged[n]}" for n in order) + "\n")


def cmd_migrate(args):
    """Migrate legacy .mam/.mama/.pdt[-scope]/ state dirs into .mcc[-scope]/."""
    pairs = find_legacy_dirs()
    if not pairs:
        print("No legacy plugin state directories found. Nothing to migrate.")
        return

    print("Legacy state directories detected:")
    for src, dst in pairs:
        print(f"  {src.name}/  →  {dst.name}/")
    print()
    if not confirm("Proceed with migration?", default=True):
        print("Aborted.")
        return

    print()
    git_avail = in_git_repo()
    if git_avail:
        print("(git repo detected — using `git mv` to preserve history)")
        print()

    for src, dst in pairs:
        print(f"Migrating {src.name}/ → {dst.name}/")
        dst.mkdir(exist_ok=True)
        for entry in sorted(src.iterdir()):
            target = dst / entry.name
            if entry.name == "sessions" and target.exists():
                print(f"  merge sessions: {entry} + {target}")
                _merge_sessions_files(entry, target)
                if git_avail:
                    subprocess.run(["git", "rm", "-f", str(entry)], capture_output=True)
                    subprocess.run(["git", "add", str(target)], capture_output=True)
                else:
                    entry.unlink()
                continue
            if target.exists():
                print(f"  ! collision (skipping): {target} already exists, leaving {entry} in place")
                continue
            print(f"  move: {entry.name}")
            _git_mv(entry, target)

        # Try to remove the now-empty legacy dir
        try:
            remaining = list(src.iterdir())
        except FileNotFoundError:
            remaining = []
        if not remaining:
            try:
                src.rmdir()
                print(f"  removed empty {src.name}/")
            except OSError as e:
                print(f"  ! could not remove {src}: {e}")
        else:
            print(f"  ! {src.name}/ still has {len(remaining)} item(s); leaving in place")

    print()
    print("Migration complete. Verify with `git status` (if applicable) before committing.")
    print("Next: in each session, run `/<plugin>:upgrade` to refresh the agent's mental model.")


# ----------------------------- VS Code integration -----------------------------

def collect_all_registered_sessions():
    """Return ordered list of unique session names across all .mcc[-scope]/sessions files."""
    names = []
    seen = set()
    for d in find_state_dirs():
        sf = d / "sessions"
        if not sf.exists():
            continue
        for line in sf.read_text().splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            n = line.split("=", 1)[0].strip()
            if n and n not in seen:
                seen.add(n)
                names.append(n)
    return names


def collect_sessions_by_scope():
    """Return ordered list of (scope, [names]) tuples across all .mcc[-scope]/sessions files.

    Scope is "" for the default .mcc/ dir, or the suffix after .mcc- otherwise.
    A name registered in multiple scopes appears in each. Empty scopes are skipped.
    """
    out = []
    for d in find_state_dirs():
        sf = d / "sessions"
        if not sf.exists():
            continue
        scope = d.name[len(".mcc-"):] if d.name.startswith(".mcc-") else ""
        names = []
        seen = set()
        for line in sf.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            n = line.split("=", 1)[0].strip()
            if ":" in n:
                continue  # namespaced metadata (e.g. `<name>:args`)
            if n and n not in seen:
                seen.add(n)
                names.append(n)
        if names:
            out.append((scope, names))
    return out


def _strip_jsonc_comments(text):
    """Strip // line comments and /* */ block comments so plain json.loads can parse JSONC.
    Conservative — respects string literals when scanning for //."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    out_lines = []
    for line in text.splitlines():
        in_str = False
        cut_at = None
        i = 0
        while i < len(line):
            c = line[i]
            if c == '"' and (i == 0 or line[i - 1] != "\\"):
                in_str = not in_str
            elif not in_str and c == "/" and i + 1 < len(line) and line[i + 1] == "/":
                cut_at = i
                break
            i += 1
        out_lines.append(line if cut_at is None else line[:cut_at])
    return "\n".join(out_lines)


def _make_session_task(name, group="personas", command=None):
    return {
        "label": f"mcc:{name}",
        "type": "shell",
        "command": command or f"mcc {name}",
        "isBackground": True,
        "presentation": {
            "reveal": "always",
            "panel": "dedicated",
            "group": group,
            "echo": False,
            "showReuseMessage": False,
        },
        "problemMatcher": [],
    }


def _make_aggregator_task(label, dep_names, run_on_folder_open=False):
    task = {
        "label": label,
        "dependsOn": [f"mcc:{n}" for n in dep_names],
        "dependsOrder": "parallel",
        "problemMatcher": [],
    }
    if run_on_folder_open:
        task["runOptions"] = {"runOn": "folderOpen"}
    return task


def _write_vscode_tasks(new_mcc_tasks):
    """Merge new mcc:* tasks into .vscode/tasks.json, preserving every non-mcc
    task. Returns (tasks_file, had_comments). Shared by the interactive
    `mcc vscode` flow and the `.mcc/term` projection."""
    vscode_dir = Path(".vscode")
    tasks_file = vscode_dir / "tasks.json"
    config = {"version": "2.0.0", "tasks": []}
    had_comments = False
    if tasks_file.exists():
        text = tasks_file.read_text(encoding="utf-8", errors="replace")
        if "//" in text or "/*" in text:
            had_comments = True
        try:
            config = json.loads(_strip_jsonc_comments(text))
        except json.JSONDecodeError as e:
            die(f"could not parse {tasks_file}: {e}")
        if not isinstance(config, dict):
            die(f"{tasks_file} is not a JSON object; refusing to overwrite.")
        if "tasks" not in config or not isinstance(config["tasks"], list):
            config["tasks"] = []
        if "version" not in config:
            config["version"] = "2.0.0"

    # Replace existing mcc:* tasks; preserve everything else
    other_tasks = [
        t for t in config["tasks"]
        if not (isinstance(t, dict)
                and isinstance(t.get("label"), str)
                and t["label"].startswith("mcc:"))
    ]
    config["tasks"] = other_tasks + new_mcc_tasks

    vscode_dir.mkdir(exist_ok=True)
    tasks_file.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return tasks_file, had_comments


def _parse_selection(raw, registered):
    """Parse a comma-separated selection of numbers and/or names against an ordered list.
    Returns list of names preserving the registered order. 'all' returns everything.
    Raises ValueError on bad input."""
    raw = raw.strip().lower()
    if raw in ("", "all"):
        return list(registered)
    selected = set()
    for tok in raw.split(","):
        tok = tok.strip()
        if not tok:
            continue
        if tok.isdigit():
            i = int(tok)
            if i < 1 or i > len(registered):
                raise ValueError(f"index out of range: {i}")
            selected.add(registered[i - 1])
        elif tok in registered:
            selected.add(tok)
        else:
            raise ValueError(f"unknown: {tok}")
    return [n for n in registered if n in selected]


VALID_GROUP_BY = ("scope", "none", "custom")


def _validate_group_label(label):
    label = label.strip()
    if not label:
        die("group label cannot be empty")
    if ":" in label:
        die(f"group label cannot contain ':' (got {label!r})")
    return label


def _resolve_groups(selection, name_scope, mode):
    """Group session names per the requested mode.

    selection: ordered list of (name, custom_label_or_None). For non-custom
               modes the second element is ignored.
    name_scope: {name: scope_str_or_empty}.
    mode: "scope" | "none" | "custom".

    Returns ordered list of (group_label, [names]) tuples. Group order =
    first-seen-in-selection. Within each group, order = selection order.
    """
    if mode == "none":
        return [("personas", [n for n, _ in selection])]
    groups = []
    bucket = {}
    for n, custom in selection:
        if mode == "scope":
            label = name_scope.get(n) or "default"
        elif mode == "custom":
            if not custom:
                die(f"session '{n}' has no group assignment")
            label = _validate_group_label(custom)
        else:
            die(f"unknown group-by mode: {mode}")
        if label not in bucket:
            bucket[label] = []
            groups.append((label, bucket[label]))
        bucket[label].append(n)
    return groups


def _vscode_group_string(label):
    """VSCode presentation.group string. Use 'personas' for the lone tab in
    'none' mode (preserves single-project shape), else 'personas:<label>'."""
    return "personas" if label == "personas" else f"personas:{label}"


def cmd_vscode(args):
    """Bootstrap or update .vscode/tasks.json with mcc session tasks.

    Grouping modes (--group-by):
      scope   one tab per .mcc-{scope}/ (default in multi-project repos)
      none    everything in one tab (default in single-project repos)
      custom  user-defined groups via --group <label>=<a>,<b> (repeatable)

    Passing any --group ... implies --group-by custom unless explicitly set.

    Per-group aggregator tasks `mcc:all:<label>` are emitted alongside the
    top-level `mcc:all`. The mcc:all:* sub-namespace is reserved.

    Auto-run on folder open is opt-in per group (default: none) in scope/custom
    mode. Single-project ('none' mode) auto-runs `mcc:all` by default.

    Source of truth: if .mcc/term exists it is projected into tasks.json
    (tabs -> groups, layouts collapsed since VSCode can't place grids). Pass
    --no-term to ignore it and use the interactive/CLI flow below.
    """
    no_folder_open = bool(args.no_folder_open)
    group_by = args.group_by  # may be None; resolved below
    cli_args = list(args.tokens or [])

    # --- .mcc/term projection (source of truth when present) ---
    term_path = None if getattr(args, "no_term", False) else _find_existing_term_file()
    if term_path is not None:
        model = _build_term_model(_read_term_cp(term_path))
        # Positional tokens select tabs by title (mirrors `mcc term up`).
        tabs = _select_term_tabs(model, cli_args)
        new_tasks, dupes = _term_to_vscode_tasks(model, tabs, no_folder_open)
        tasks_file, had_comments = _write_vscode_tasks(new_tasks)
        print(f"Wrote {tasks_file} from {term_path}  ({len(tabs)} tab(s))")
        for t in tabs:
            members = ", ".join(_layout_leaves(t["tree"]))
            tag = " (auto-run on folder open)" if t["autostart"] and not no_folder_open else ""
            print(f"  [{t['title']}] {members}{tag}")
        for name, owner, skipped in dupes:
            print(f"  ! '{name}' in both '{owner}' and '{skipped}' — kept '{owner}'")
        if had_comments:
            print("  ! existing JSONC comments were dropped on write")
        print("  note: pane grid geometry isn't represented — VSCode splits "
              "share one terminal group per tab.")
        print()
        print("In VS Code: Cmd/Ctrl+Shift+P → 'Tasks: Run Task' → "
              "mcc:all (or mcc:all:<tab>) or any mcc:<name>")
        return

    # Parse repeated --group label=name1,name2 specs
    custom_groups = []  # list of (label, [names])
    for spec in (args.group or []):
        if "=" not in spec:
            die(f"--group expected 'label=name1,name2', got {spec!r}")
        label, csv = spec.split("=", 1)
        label = _validate_group_label(label)
        members = [s.strip() for s in csv.split(",") if s.strip()]
        if not members:
            die(f"--group {label!r} has no members")
        custom_groups.append((label, members))

    # If --group given without --group-by, infer custom mode
    if custom_groups and group_by is None:
        group_by = "custom"
    if custom_groups and group_by != "custom":
        die("--group is only valid with --group-by custom")

    by_scope = collect_sessions_by_scope()
    if not by_scope:
        die("no sessions registered in this project. Run `mcc create <name> ...` first.")

    multi_project = any(scope for scope, _ in by_scope)

    # Build flat ordered list and a name → scope map
    flat = []
    name_scope = {}
    for scope, names in by_scope:
        for n in names:
            if n not in name_scope:
                flat.append(n)
                name_scope[n] = scope

    # If --group given without positional selection, the group definitions
    # imply the selection (union of member names).
    if not cli_args and custom_groups:
        seen = set()
        cli_args = []
        for _, members in custom_groups:
            for m in members:
                if m not in seen:
                    seen.add(m)
                    cli_args.append(m)

    # Selection: CLI args may name sessions OR scopes (multi-project only),
    # or the literal "all".
    if cli_args:
        selected = []
        seen = set()
        for tok in cli_args:
            if tok == "all":
                for n in flat:
                    if n not in seen:
                        seen.add(n)
                        selected.append(n)
            elif multi_project and any(s == tok for s, _ in by_scope):
                # scope argument — include all sessions in that scope
                for s, ns in by_scope:
                    if s == tok:
                        for n in ns:
                            if n not in seen:
                                seen.add(n)
                                selected.append(n)
            elif tok in name_scope:
                if tok not in seen:
                    seen.add(tok)
                    selected.append(tok)
            else:
                die(f"not registered: {tok}. Known sessions: {', '.join(flat)}"
                    + (f"; scopes: {', '.join(s for s, _ in by_scope if s)}" if multi_project else ""))
        names = selected
    else:
        # Interactive
        if multi_project:
            print("Registered sessions by project scope:")
            i = 1
            for scope, ns in by_scope:
                print(f"  {scope or '(default)'}/")
                for n in ns:
                    print(f"    {i}. {n}")
                    i += 1
            print()
            raw = prompt("Which to include? (numbers, scope names, or 'all')", default="all")
        else:
            print("Registered sessions in this project:")
            for i, n in enumerate(flat, 1):
                print(f"  {i}. {n}")
            print()
            raw = prompt("Which to include? (e.g. 1,2,3 or 'all')", default="all")

        if multi_project:
            # Allow scope names alongside numbers
            try:
                names = []
                seen = set()
                raw_l = raw.strip().lower()
                if raw_l in ("", "all"):
                    names = list(flat)
                else:
                    for tok in raw_l.split(","):
                        tok = tok.strip()
                        if not tok:
                            continue
                        if any(s == tok for s, _ in by_scope):
                            for s, ns in by_scope:
                                if s == tok:
                                    for n in ns:
                                        if n not in seen:
                                            seen.add(n)
                                            names.append(n)
                        elif tok.isdigit():
                            i = int(tok)
                            if i < 1 or i > len(flat):
                                raise ValueError(f"index out of range: {i}")
                            n = flat[i - 1]
                            if n not in seen:
                                seen.add(n)
                                names.append(n)
                        elif tok in name_scope:
                            if tok not in seen:
                                seen.add(tok)
                                names.append(tok)
                        else:
                            raise ValueError(f"unknown: {tok}")
            except ValueError as e:
                die(f"invalid selection: {e}")
        else:
            try:
                names = _parse_selection(raw, flat)
            except ValueError as e:
                die(f"invalid selection: {e}")

    if not names:
        die("no sessions selected; nothing to do.")

    # Decide grouping mode if not yet set (interactive or default)
    if group_by is None:
        if cli_args:
            # Non-interactive default
            group_by = "scope" if multi_project else "none"
        else:
            print()
            default_mode = "scope" if multi_project else "none"
            print("Group sessions into VSCode tabs how?")
            print("  scope    one tab per project scope")
            print("  none     all in one tab")
            print("  custom   manually assign each session to a group label")
            raw = prompt("Mode", default=default_mode).strip().lower()
            if raw not in VALID_GROUP_BY:
                die(f"invalid mode {raw!r}; expected one of: {', '.join(VALID_GROUP_BY)}")
            group_by = raw

    # Build the (name, custom_label_or_None) selection
    if group_by == "custom":
        if custom_groups:
            # Custom groups defined via CLI: build assignment from them
            assigned = {}
            for label, members in custom_groups:
                for m in members:
                    if m not in name_scope:
                        die(f"--group {label!r} references unknown session '{m}'")
                    if m not in names:
                        die(f"--group {label!r} references '{m}' which wasn't selected")
                    if m in assigned:
                        die(f"session '{m}' assigned to multiple groups "
                            f"({assigned[m]!r} and {label!r})")
                    assigned[m] = label
            unassigned = [n for n in names if n not in assigned]
            if unassigned:
                die(f"sessions with no group assignment: {', '.join(unassigned)}. "
                    f"Add them to a --group, or remove from selection.")
            selection = [(n, assigned[n]) for n in names]
        else:
            # Interactive: walk through each session, default = scope or last entered
            print()
            print("Custom grouping — enter a group label for each session.")
            print("(Sessions with the same label share a VSCode tab.)")
            selection = []
            last_label = None
            for n in names:
                default_label = last_label or name_scope.get(n) or "default"
                raw = prompt(f"  {n}", default=default_label).strip()
                if not raw:
                    raw = default_label
                _validate_group_label(raw)
                selection.append((n, raw))
                last_label = raw
    else:
        selection = [(n, None) for n in names]

    grouped = _resolve_groups(selection, name_scope, group_by)

    # Decide which aggregators run on folder open
    auto_run_groups = set()  # group labels whose mcc:all:<g> runs on open
    auto_run_top = False     # whether top-level mcc:all runs on open
    if not no_folder_open:
        if group_by == "none":
            # Single tab — fold "auto-run on open" into mcc:all (single-project default)
            auto_run_top = True
        elif cli_args:
            # Non-interactive with multiple groups: don't presume; user can re-run
            # interactively or pass --no-folder-open. Default = none.
            pass
        else:
            group_labels = [g for g, _ in grouped]
            print()
            print("Auto-run on folder open?")
            print(f"  Groups available: {', '.join(group_labels)} "
                  f"(or 'all' for everything, 'none' for nothing)")
            raw = prompt("Which to auto-run?", default="none").strip().lower()
            if raw in ("", "none"):
                pass
            elif raw == "all":
                auto_run_top = True
            else:
                for tok in raw.split(","):
                    tok = tok.strip()
                    if not tok:
                        continue
                    if tok in group_labels:
                        auto_run_groups.add(tok)
                    else:
                        die(f"unknown group: {tok}")

    # Build tasks
    new_mcc_tasks = []
    for label, ns in grouped:
        gstr = _vscode_group_string(label)
        for n in ns:
            new_mcc_tasks.append(_make_session_task(n, group=gstr))

    # Per-group aggregators (skip in 'none' mode — there's only one group, and
    # the top-level mcc:all already covers it)
    if group_by != "none":
        for label, ns in grouped:
            new_mcc_tasks.append(_make_aggregator_task(
                f"mcc:all:{label}", ns,
                run_on_folder_open=(label in auto_run_groups),
            ))

    # Top-level aggregator
    new_mcc_tasks.append(_make_aggregator_task(
        "mcc:all", names, run_on_folder_open=auto_run_top
    ))

    tasks_file, had_comments = _write_vscode_tasks(new_mcc_tasks)

    print(f"Wrote {tasks_file} with mcc tasks for: {', '.join(names)}")
    print(f"  group-by: {group_by}")
    if group_by != "none":
        for label, ns in grouped:
            tag = " (auto-run on folder open)" if label in auto_run_groups else ""
            print(f"  mcc:all:{label} → {', '.join(ns)}{tag}")
    top_tag = " (auto-run on folder open)" if auto_run_top else ""
    print(f"  mcc:all → everything{top_tag}")
    if had_comments:
        print(f"  ! existing JSONC comments were dropped on write")
    print()
    aggregator_hint = "mcc:all" if group_by == "none" else "mcc:all (or mcc:all:<group>)"
    print(f"In VS Code: Cmd/Ctrl+Shift+P → 'Tasks: Run Task' → {aggregator_hint} or any individual mcc:<name>")
    if _find_existing_term_file() is None:
        print()
        print("Tip: `mcc term init` captures this as a portable .mcc/term that "
              "also drives `mcc term up` (Windows Terminal) and future `mcc vscode` runs.")


# ----------------------------- Terminal arrangements (mcc term) ---------------
#
# `.mcc/term` declares how this project's sessions are laid out across terminal
# tabs and panes. It is the single source of truth that `mcc term` renders into
# a live terminal (Windows Terminal on Windows/WSL, iTerm2 on macOS) and that
# `mcc vscode` will later render into tasks.json. Each renderer honors what its
# surface can express and silently degrades the rest: vscode can't place
# arbitrary grids, so it keeps grouping + autostart and drops geometry; iTerm2's
# AppleScript split has no size parameter, so `name@40` pins degrade to even
# splits there.
#
# Format (INI, parsed with configparser):
#
#   [term]
#   window  = cc-{dir}            # wt -w target; {dir}=project dir, {slug}=sanitized
#   default = mcc {name}          # per-pane command template; {name}=leaf name
#   profile = Ubuntu              # wt profile (-p) panes launch under; inherits
#                                 # the launching shell's cwd ('distro' alias ok)
#   shell   = bash                # wrapper for pane commands: bash | cmd |
#                                 # powershell | none. Default: cmd on Windows,
#                                 # bash elsewhere. (Or wrap = cmd /k {cmd}.)
#
#   [tab.core]
#   layout = mcc | mcc-docs                #  | columns, / rows, () nesting, name@40 size
#
#   [tab.support]
#   layout    = (mcc / mcc-docs) | mcc-term
#   autostart = true                       # vscode-only hint; ignored by wt
#   cmd.mcc-term = mcc mcc-term            # per-pane command override
#
# The layout is a small slicing grammar: leaves are session names, `|` splits a
# region into columns, `/` into rows, parentheses nest, and `name@40` pins a
# pane to 40% of its split. Any guillotine (X-by-Y) grid is expressible; a
# non-slicing pinwheel is intentionally not.

class TermError(Exception):
    """Raised on a malformed .mcc/term layout expression."""


_LAYOUT_LEAF_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_-]*")
_LAYOUT_SIZE_RE = re.compile(r"\d+(?:\.\d+)?")


def _lex_layout(expr):
    """Tokenize a layout expression into '(' ')' '|' '/' and ('NAME', name, size)."""
    toks = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c.isspace():
            i += 1
            continue
        if c in "()|/":
            toks.append(c)
            i += 1
            continue
        m = _LAYOUT_LEAF_RE.match(expr, i)
        if not m:
            raise TermError(f"unexpected character {c!r} in layout {expr!r}")
        name = m.group(0)
        i = m.end()
        size = None
        if i < len(expr) and expr[i] == "@":
            sm = _LAYOUT_SIZE_RE.match(expr, i + 1)
            if not sm:
                raise TermError(f"expected a number after '@' in layout {expr!r}")
            size = float(sm.group(0))
            if size > 1:  # accept either 40 or 0.4
                size /= 100.0
            i = sm.end()
        toks.append(("NAME", name, size))
    return toks


def _parse_layout(expr):
    """Parse a layout expression into a tree.

    Leaf nodes are {"name": str, "size": float|None}; split nodes are
    {"op": "|"|"/", "children": [...]}. Operators at one level must match;
    mix them only via parentheses.
    """
    toks = _lex_layout(expr)
    if not toks:
        raise TermError("empty layout")
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def advance():
        t = toks[pos[0]]
        pos[0] += 1
        return t

    def parse_operand():
        t = peek()
        if t == "(":
            advance()
            node = parse_expr()
            if peek() != ")":
                raise TermError(f"missing ')' in layout {expr!r}")
            advance()
            return node
        if isinstance(t, tuple) and t[0] == "NAME":
            advance()
            return {"name": t[1], "size": t[2]}
        raise TermError(f"expected a session name or '(' in layout {expr!r}")

    def parse_expr():
        operands = [parse_operand()]
        ops = []
        while peek() in ("|", "/"):
            ops.append(advance())
            operands.append(parse_operand())
        if not ops:
            return operands[0]
        if len(set(ops)) > 1:
            raise TermError(
                f"mixed '|' and '/' at the same level — parenthesize: {expr!r}")
        return {"op": ops[0], "children": operands}

    node = parse_expr()
    if pos[0] != len(toks):
        raise TermError(f"trailing tokens in layout {expr!r}")
    return node


def _layout_leaves(node):
    if "name" in node:
        return [node["name"]]
    out = []
    for c in node["children"]:
        out.extend(_layout_leaves(c))
    return out


def _first_leaf(node):
    while "name" not in node:
        node = node["children"][0]
    return node


def _pane_prog(cmd, shell, wrap=None):
    """Wrap a pane command for the chosen shell so the user's PATH/aliases
    (incl. `mcc`) resolve and a bare `mcc <name>` (which may be a .cmd/.bat shim
    on Windows) actually runs.

    Spawned via wt's `-p <profile>` (see _compile_tab_ops) rather than
    `wsl.exe -d <distro>` because the profile inherits the launching shell's
    working directory — so project-relative state (.mcc/sessions) is found.

    `wrap` (a template containing the literal token `{cmd}`) overrides `shell`
    for full control, e.g. `wrap = cmd /k {cmd}`.
    """
    if wrap:
        return [cmd if t == "{cmd}" else t for t in wrap.split()]
    s = (shell or "").lower()
    if s == "cmd":
        return ["cmd", "/c", cmd]
    if s in ("powershell", "pwsh"):
        exe = "pwsh" if s == "pwsh" else "powershell"
        return [exe, "-NoLogo", "-Command", cmd]
    if s == "none":
        return shlex.split(cmd)
    return ["bash", "-lic", cmd]  # default


def _compile_tab_ops(tab_title, node, resolve_cmd, profile, start_dir=None):
    """Compile one tab's layout tree into an ordered list of wt subcommand
    token-lists (`nt ...`, `sp ...`, `mf ...`). resolve_cmd(name) returns the
    pane program token list for a leaf.

    Geometry is built outer-split-first so spanning panes span: a split carves
    the full region before either half is subdivided. Focus walks back with
    `mf` after each subtree so siblings land in the right place.

    start_dir, when given, pins every pane's working directory via `-d` so the
    pane lands in the project (not the wt profile's startingDirectory). Used on
    Windows where profile cwd-inheritance is unreliable.
    """
    # --suppressApplicationTitle keeps our --title from being clobbered by the
    # app running in the pane (e.g. claude rewriting the tab title). Every pane
    # needs it — any unsuppressed pane can rewrite the shared tab title.
    pane_opts = (["-d", start_dir] if start_dir else []) + ["-p", profile]
    ops = [["nt", "--title", tab_title, "--suppressApplicationTitle"] + pane_opts
           + resolve_cmd(_first_leaf(node)["name"])]

    def render(n):
        if "name" in n:  # leaf — already spawned by the caller's nt/sp
            return
        axis = "-V" if n["op"] == "|" else "-H"
        back = "left" if n["op"] == "|" else "up"
        children = n["children"]
        count = len(children)
        # Target fraction of the region for each child: pinned leaves take their
        # @size, everything else shares the remainder evenly. (A parenthesized
        # group can't be pinned — only leaves carry a size.)
        fixed = {i: c["size"] for i, c in enumerate(children)
                 if "name" in c and c.get("size") is not None}
        used = sum(fixed.values())
        if used >= 1.0:  # over-pinned — fall back to even rather than degenerate
            fixed, used = {}, 0.0
        free = count - len(fixed)
        even = (1.0 - used) / free if free else 0.0
        frac = [fixed.get(i, even) for i in range(count)]
        # Slice the growing tail. wt's --size is the *new* pane's share of the
        # pane being split, so the split that places child i fixes child i-1's
        # final region: S_i = 1 - frac[i-1]/P, where P is the running tail size.
        tail = 1.0
        for i in range(1, count):
            size = min(max(1.0 - frac[i - 1] / tail, 0.05), 0.95)
            ops.append(["sp", axis, "--size", f"{size:.3f}",
                        "--suppressApplicationTitle"] + pane_opts
                       + resolve_cmd(_first_leaf(children[i])["name"]))
            tail *= size
        # Subdivide right-to-left, stepping focus back toward the first sibling.
        for i in range(count - 1, -1, -1):
            render(children[i])
            if i > 0:
                ops.append(["mf", back])

    render(node)
    return ops


def _cmd_quote(tok):
    """Quote a token for a Windows cmd command line (double quotes)."""
    if tok and not any(c in tok for c in ' \t"^&|<>;()'):
        return tok
    return '"' + tok.replace('"', '""') + '"'


def _render_term_dryrun(window, ops):
    """Render the flattened op list as a copy-pasteable command line in the
    syntax of the shell mcc is running in: bash (`\\;` separators, `\\` line
    continuations, single-quote) on posix/WSL, cmd (`;` separators, `^` line
    continuations, double-quote) on Windows."""
    if is_windows():
        quote, sep, cont, head = _cmd_quote, " ; ^", " ^", "wt.exe -w {} ^"
    else:
        quote, sep, cont, head = shlex.quote, " \\; \\", " \\", "wt.exe -w {} \\"
    lines = [head.format(quote(window))]
    last = len(ops) - 1
    for i, op in enumerate(ops):
        body = " ".join(quote(t) for t in op)
        lines.append(f"  {body}" + (sep if i < last else ""))
    return "\n".join(lines)


def _find_existing_term_file():
    """Return the first .mcc[-scope]/term that exists, or None."""
    for d in find_state_dirs():
        p = d / "term"
        if p.exists():
            return p
    return None


def _read_term_cp(path):
    import configparser
    cp = configparser.ConfigParser()
    cp.optionxform = str  # preserve case in keys (session names, cmd.<name>)
    try:
        cp.read(path, encoding="utf-8")
    except configparser.Error as e:
        die(f"could not parse {path}: {e}")
    return cp


def _load_term_config():
    """Locate and parse .mcc[-scope]/term. Returns (path, ConfigParser)."""
    path = _find_existing_term_file()
    if path is None:
        die("no .mcc/term found. Create one with `mcc term init` and try again.")
    return path, _read_term_cp(path)


def _term_to_vscode_tasks(model, tabs, no_folder_open=False):
    """Project a .mcc/term model into VSCode task dicts.

    VSCode can't place arbitrary grids, so geometry is dropped: a tab's layout
    leaves become split-terminal tasks sharing one presentation group, and
    `autostart` maps to runOn=folderOpen on that tab's aggregator. Per-pane
    command overrides and the `default` template are honored.

    A session that appears in more than one tab can't map to a unique task
    label; the first occurrence wins and the rest are returned as `dupes`.
    """
    single = len(tabs) == 1
    new_tasks = []
    seen = {}  # name -> tab title that owns its task
    dupes = []  # (name, owning_title, skipped_title)
    for t in tabs:
        group = f"personas:{t['title']}"
        for name in _layout_leaves(t["tree"]):
            if name in seen:
                dupes.append((name, seen[name], t["title"]))
                continue
            seen[name] = t["title"]
            cmd = t["cmd"].get(name) or model["default"].replace("{name}", name)
            new_tasks.append(_make_session_task(name, group=group, command=cmd))

    if not single:
        for t in tabs:
            members = [n for n in _layout_leaves(t["tree"]) if seen.get(n) == t["title"]]
            new_tasks.append(_make_aggregator_task(
                f"mcc:all:{t['title']}", members,
                run_on_folder_open=t["autostart"] and not no_folder_open))

    top_auto = single and tabs[0]["autostart"] and not no_folder_open
    new_tasks.append(_make_aggregator_task("mcc:all", list(seen.keys()),
                                           run_on_folder_open=top_auto))
    return new_tasks, dupes


def _build_term_model(cp):
    """Resolve a parsed .mcc/term into {window, default, distro, tabs[]}."""
    g = cp["term"] if cp.has_section("term") else {}
    window_tmpl = g.get("window", "cc-{dir}")
    default_tmpl = g.get("default", "mcc {name}")
    # wt profile (-p) the panes launch under; inherits the launching shell's cwd.
    # `distro` accepted as a back-compat alias. Defaults are platform-aware: a
    # Windows host wants the cmd profile + cmd wrapper, WSL/posix wants the
    # distro profile + bash wrapper.
    if is_windows():
        default_profile, default_shell = "Command Prompt", "cmd"
    elif is_macos():
        # iTerm2 ships a profile named "Default"; users with custom profiles
        # can override in [term]. Shell stays bash — Mac default.
        default_profile, default_shell = "Default", "bash"
    else:
        default_profile = os.environ.get("WSL_DISTRO_NAME") or "Ubuntu"
        default_shell = "bash"
    profile = g.get("profile") or g.get("distro") or default_profile
    shell = g.get("shell") or default_shell
    wrap = g.get("wrap") or None

    dirname = Path.cwd().name
    slug = re.sub(r"[^A-Za-z0-9]+", "-", dirname).strip("-").lower() or "project"
    window = window_tmpl.replace("{dir}", dirname).replace("{slug}", slug)

    tabs = []
    for sec in cp.sections():
        if not sec.startswith("tab."):
            continue
        title = sec[len("tab."):]
        layout = cp[sec].get("layout")
        if not layout:
            die(f"[{sec}] in .mcc/term has no 'layout'")
        try:
            tree = _parse_layout(layout)
        except TermError as e:
            die(f"[{sec}] layout error: {e}")
        overrides = {k[len("cmd."):]: v for k, v in cp[sec].items()
                     if k.startswith("cmd.")}
        autostart = cp[sec].get("autostart", "false").strip().lower() in (
            "1", "true", "yes", "on")
        tabs.append({"title": title, "tree": tree, "cmd": overrides,
                     "autostart": autostart, "layout": layout.strip()})
    if not tabs:
        die("no [tab.*] sections in .mcc/term")
    return {"window": window, "default": default_tmpl, "profile": profile,
            "shell": shell, "wrap": wrap, "tabs": tabs}


def _select_term_tabs(model, wanted):
    if not wanted:
        return model["tabs"]
    known = {t["title"] for t in model["tabs"]}
    unknown = [w for w in wanted if w not in known]
    if unknown:
        die(f"unknown tab(s): {', '.join(unknown)}. Known: {', '.join(sorted(known))}")
    return [t for t in model["tabs"] if t["title"] in wanted]


def _compile_term(model, tabs):
    """Flatten selected tabs into one ordered wt op list."""
    # On Windows, pin the pane cwd to the project dir via `-d`: launching wt
    # fresh uses the profile's startingDirectory, not the caller's, so a bare
    # `mcc <name>` would run somewhere without .mcc/. On WSL/posix the wt.exe
    # `-d` would need a Windows-form path; profile cwd-inheritance works there,
    # so we leave it unpinned.
    start_dir = os.getcwd() if is_windows() else None
    all_ops = []
    for t in tabs:
        def resolve(name, t=t):
            raw = t["cmd"].get(name) or model["default"].replace("{name}", name)
            return _pane_prog(raw, model["shell"], model.get("wrap"))
        all_ops.extend(_compile_tab_ops(t["title"], t["tree"], resolve,
                                        model["profile"], start_dir))
    return all_ops


# --- macOS / iTerm2 renderer ---------------------------------------------------
#
# iTerm2's AppleScript dictionary exposes `create window`, `create tab`, and
# `split vertically/horizontally with default profile command "..."`. Each split
# returns the new session; recursing into a node means addressing the right
# variable. The Windows compiler's `--size` knob has no analogue here, so
# `name@40` pins are silently dropped on macOS — splits are always even.

def _as_quote(s):
    """Escape a string for embedding inside an AppleScript "..." literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _macos_pane_cmd(name, t, model, start_dir):
    """Build the literal shell string iTerm2 should run for one pane: a
    cd-into-project prefix so `mcc <name>` finds .mcc/, wrapped through the
    configured shell so PATH/aliases resolve."""
    raw = t["cmd"].get(name) or model["default"].replace("{name}", name)
    cd_prefix = f"cd {shlex.quote(start_dir)} && "
    prog = _pane_prog(cd_prefix + raw, model["shell"], model.get("wrap"))
    return " ".join(shlex.quote(tok) for tok in prog)


def _emit_iterm_applescript(model, tabs):
    """Render the selected tabs into a single AppleScript program that drives
    iTerm2. Tabs land in a fresh window; each tab's first leaf seeds the tab,
    subsequent leaves are placed by splitting from the running anchor.

    We avoid iTerm2's `create ... command "..."` parameter form (its AppleScript
    parser is fussy about keyword ordering across versions) and instead create
    each session with the profile's default shell, then `write text` the pane
    command. The pane sees one extra prompt for an instant before our command
    runs — harmless."""
    start_dir = os.getcwd()
    lines = ['tell application "iTerm"', "\tactivate"]
    sid = [0]

    def newvar():
        sid[0] += 1
        return f"s{sid[0]}"

    def write_into(var, name, t):
        cmd = _macos_pane_cmd(name, t, model, start_dir)
        lines.append(f'\ttell {var} to write text "{_as_quote(cmd)}"')

    def render_split_tree(node, anchor_var, t):
        """Carve `anchor_var` per `node`. For a split with N children, child 0
        stays in `anchor_var`; children 1..N-1 are placed by splitting from the
        previously created child (mirrors the Windows growing-tail order)."""
        if "name" in node:
            return
        axis = "vertically" if node["op"] == "|" else "horizontally"
        children = node["children"]
        child_vars = [anchor_var]
        current = anchor_var
        for c in children[1:]:
            leaf = _first_leaf(c)
            v = newvar()
            lines.append(f"\ttell {current}")
            lines.append(
                f"\t\tset {v} to (split {axis} with default profile)"
            )
            lines.append("\tend tell")
            write_into(v, leaf["name"], t)
            child_vars.append(v)
            current = v
        for c, v in zip(children, child_vars):
            render_split_tree(c, v, t)

    win_var = "win"
    for i, t in enumerate(tabs):
        first_leaf_name = _first_leaf(t["tree"])["name"]
        anchor = newvar()
        if i == 0:
            lines.append(f"\tset {win_var} to (create window with default profile)")
        else:
            lines.append(f"\ttell {win_var} to create tab with default profile")
        lines.append(f"\tset {anchor} to current session of current tab of {win_var}")
        lines.append(f'\ttell {anchor} to set name to "{_as_quote(t["title"])}"')
        write_into(anchor, first_leaf_name, t)
        render_split_tree(t["tree"], anchor, t)

    lines.append("end tell")
    return "\n".join(lines)


def cmd_term_ls(args):
    path, cp = _load_term_config()
    model = _build_term_model(cp)
    print(f"{path}")
    print(f"  window '{model['window']}'  profile '{model['profile']}'  "
          f"shell '{model['shell']}'  default '{model['default']}'")
    for t in model["tabs"]:
        star = "  *autostart" if t["autostart"] else ""
        print(f"  [tab.{t['title']}]{star}")
        print(f"      layout: {t['layout']}")
        print(f"      panes:  {', '.join(_layout_leaves(t['tree']))}")
        for name, cmd in t["cmd"].items():
            print(f"      cmd.{name}: {cmd}")


def cmd_term_up(args):
    path, cp = _load_term_config()
    model = _build_term_model(cp)
    tabs = _select_term_tabs(model, list(args.tabs or []))

    # macOS — drive iTerm2 via osascript. (No Windows Terminal here; geometry
    # @size pins degrade to even splits, since iTerm2's AppleScript split has
    # no size parameter.)
    if is_macos():
        script = _emit_iterm_applescript(model, tabs)
        if args.dry_run:
            print(f"# from {path}  -> iTerm2, "
                  f"profile '{model['profile']}', shell '{model['shell']}'")
            print(f"# tabs: {', '.join(t['title'] for t in tabs)}")
            print(script)
            return
        try:
            rc = subprocess.run(["osascript", "-e", script]).returncode
        except FileNotFoundError:
            die("osascript not found. macOS-only path; ensure you're on macOS "
                "with iTerm2 installed, or use `mcc term up --dry-run` to "
                "print the AppleScript.")
        if rc != 0:
            die(f"osascript exited {rc}", code=rc)
        print(f"Launched {len(tabs)} tab(s) into iTerm2.")
        return

    # Windows / WSL — drive wt.exe.
    ops = _compile_term(model, tabs)

    if args.dry_run:
        c = "rem" if is_windows() else "#"
        print(f"{c} from {path}  -> wt window '{model['window']}', "
              f"profile '{model['profile']}', shell '{model['shell']}'")
        print(f"{c} tabs: {', '.join(t['title'] for t in tabs)}")
        print(_render_term_dryrun(model["window"], ops))
        return

    # Live launch: drive wt.exe directly (no shell, so ';' separators are passed
    # as literal argv tokens rather than being eaten by bash).
    argv = ["wt.exe", "-w", model["window"]]
    for i, op in enumerate(ops):
        if i:
            argv.append(";")
        argv.extend(op)
    try:
        rc = subprocess.run(argv).returncode
    except FileNotFoundError:
        die("wt.exe not found on PATH. Run from WSL with Windows interop "
            "enabled, or use `mcc term up --dry-run` to print the command.")
    if rc != 0:
        die(f"wt.exe exited {rc}", code=rc)
    print(f"Launched {len(tabs)} tab(s) into window '{model['window']}'.")


def _write_term_file(path, window, default, profile, shell, tab_layouts):
    """Render a clean, commented .mcc/term from elicited values."""
    lines = [
        "# .mcc/term — terminal arrangement for this project.",
        "# Generated by `mcc term init`; safe to hand-edit.",
        "#",
        "# layout grammar:  leaf = session name,  | = columns,  / = rows,",
        "#                  () = nesting,  name@40 = pin a pane to 40% of its split.",
        "",
        "[term]",
        f"window  = {window}",
        f"default = {default}",
        f"profile = {profile}",
        f"shell   = {shell}",
        "",
    ]
    for label, layout in tab_layouts:
        lines.append(f"[tab.{label}]")
        lines.append(f"layout = {layout}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def cmd_term_init(args):
    """Interactively elicit a .mcc/term: select sessions, group into tabs,
    set each tab's layout, then write the file."""
    state_dirs = find_state_dirs()
    # Prefer the default .mcc/ for the term file; fall back to the first scope.
    target_dir = next((d for d in state_dirs if d.name == ".mcc"),
                      state_dirs[0] if state_dirs else Path(".mcc"))
    term_path = target_dir / "term"
    if term_path.exists() and not args.force:
        if not confirm(f"{term_path} exists. Overwrite?", default=False):
            die("aborted.")

    by_scope = collect_sessions_by_scope()
    if not by_scope:
        die("no sessions registered in this project. Run `mcc create <name>` first.")

    flat, name_scope = [], {}
    for scope, names in by_scope:
        for n in names:
            if n not in name_scope:
                flat.append(n)
                name_scope[n] = scope
    multi = any(s for s, _ in by_scope)

    # --- selection ---
    print("Registered sessions:")
    for i, n in enumerate(flat, 1):
        scope_tag = f"  ({name_scope[n]})" if multi and name_scope[n] else ""
        print(f"  {i}. {n}{scope_tag}")
    print()
    raw = prompt("Which to include? (e.g. 1,2,3 or 'all')", default="all")
    try:
        names = _parse_selection(raw, flat)
    except ValueError as e:
        die(f"invalid selection: {e}")
    if not names:
        die("nothing selected; aborting.")

    # --- grouping into tabs ---
    print()
    print("Group sessions into tabs how?")
    print("  none    all selected sessions in one tab")
    print("  scope   one tab per project scope")
    print("  custom  assign each session a tab label")
    default_mode = "scope" if multi else "none"
    mode = prompt("Mode", default=default_mode).strip().lower()
    if mode not in VALID_GROUP_BY:
        die(f"invalid mode {mode!r}; expected one of: {', '.join(VALID_GROUP_BY)}")

    if mode == "none":
        title = prompt("Tab name", default="main").strip() or "main"
        _validate_group_label(title)
        grouped = [(title, names)]
    elif mode == "custom":
        print("Enter a tab label for each session (same label ⇒ same tab):")
        selection, last = [], None
        for n in names:
            dl = last or name_scope.get(n) or "main"
            lab = prompt(f"  {n}", default=dl).strip() or dl
            _validate_group_label(lab)
            selection.append((n, lab))
            last = lab
        grouped = _resolve_groups(selection, name_scope, "custom")
    else:  # scope
        grouped = _resolve_groups([(n, None) for n in names], name_scope, "scope")

    # --- per-tab layout ---
    print()
    print("Layout per tab. Default = even columns. Use | (cols) / (rows) () name@40.")
    tab_layouts = []
    for label, ns in grouped:
        default_layout = " | ".join(ns)
        while True:
            lay = prompt(f"  [{label}]", default=default_layout).strip() or default_layout
            try:
                tree = _parse_layout(lay)
            except TermError as e:
                print(f"    ! {e}")
                continue
            unknown = [l for l in _layout_leaves(tree) if l not in name_scope]
            if unknown:
                print(f"    ! unknown session(s): {', '.join(unknown)}")
                continue
            tab_layouts.append((label, lay))
            break

    # --- globals (platform-aware defaults) ---
    if is_windows():
        dflt_profile, dflt_shell = "Command Prompt", "cmd"
    elif is_macos():
        dflt_profile, dflt_shell = "Default", "bash"
    else:
        dflt_profile, dflt_shell = os.environ.get("WSL_DISTRO_NAME") or "Ubuntu", "bash"
    profile_label = "iTerm2 profile" if is_macos() else "wt profile (-p)"
    print()
    window = prompt("Window name (-w; {dir}/{slug} expand)", default="cc-{dir}").strip() or "cc-{dir}"
    default_cmd = prompt("Per-pane command template", default="mcc {name}").strip() or "mcc {name}"
    profile = prompt(profile_label, default=dflt_profile).strip() or dflt_profile
    shell = prompt("Pane shell (bash/cmd/powershell/none)", default=dflt_shell).strip() or dflt_shell

    _write_term_file(term_path, window, default_cmd, profile, shell, tab_layouts)
    print()
    print(f"Wrote {term_path}:")
    for label, layout in tab_layouts:
        print(f"  [tab.{label}]  {layout}")
    print()
    print("Preview the launch:  mcc term up --dry-run")
    print("Launch:              mcc term up")


# ----------------------------- Session transcript -----------------------------
#
# Reads ~/.claude/projects/<slug>/<sid>.jsonl and renders a clean markdown
# transcript by walking parentUuid from the most recent live leaf back to the
# root, traversing through compaction boundaries (which leave pre-compact history
# intact in the file). Tool calls render as compact slugs.
#
# Defensive throughout: malformed lines are skipped with a warning, missing
# fields are treated as absent rather than crashing.

def _claude_config_dir():
    """Honor CLAUDE_CONFIG_DIR env var (CC's `getClaudeConfigHomeDir`,
    src/utils/envUtils.ts:7-14), falling back to ~/.claude. NFC-normalized
    so non-ASCII paths match what CC actually wrote."""
    import unicodedata
    raw = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(unicodedata.normalize("NFC", raw))


CLAUDE_PROJECTS_ROOT = _claude_config_dir() / "projects"
TRANSCRIPT_TYPES = {"user", "assistant", "attachment", "system"}
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
_SLUG_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]")
_MAX_SLUG_LEN = 200


def _looks_like_uuid(s):
    return bool(UUID_RE.match(s or ""))


def _project_slug_for_cwd(cwd=None):
    """Mirror Claude Code's slug derivation (sessionStoragePortable.ts:311-319):
    every non-alphanumeric character becomes '-'; if the result exceeds 200
    chars, append a stable djb2-style hash of the original path. NFC-normalize
    the cwd first so macOS decomposed-form paths match what CC wrote."""
    import unicodedata
    cwd = (cwd or Path.cwd()).resolve()
    name = unicodedata.normalize("NFC", str(cwd))
    sanitized = _SLUG_NON_ALNUM.sub("-", name)
    if len(sanitized) <= _MAX_SLUG_LEN:
        return sanitized
    # CC uses Bun.hash (wyhash) when available, else simpleHash. djb2 is good
    # enough for our purposes — only used to disambiguate truncated long paths.
    h = 5381
    for ch in name:
        h = ((h * 33) + ord(ch)) & 0xFFFFFFFF
    suffix = format(h, "x")
    return f"{sanitized[:_MAX_SLUG_LEN]}-{suffix}"


def _find_jsonl(sid, cwd=None):
    """Find the JSONL file for a session id. Try cwd-derived slug first, then glob."""
    if not CLAUDE_PROJECTS_ROOT.exists():
        return None
    slug = _project_slug_for_cwd(cwd)
    direct = CLAUDE_PROJECTS_ROOT / slug / f"{sid}.jsonl"
    if direct.exists():
        return direct
    # Fallback: glob across all project dirs
    for p in CLAUDE_PROJECTS_ROOT.glob(f"*/{sid}.jsonl"):
        return p
    return None


def _parse_jsonl(path):
    """Read JSONL, returning a list of parsed entries. Skips malformed lines."""
    entries = []
    skipped = 0
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    skipped += 1
    except OSError as e:
        die(f"could not read {path}: {e}")
    if skipped:
        print(f"  ! skipped {skipped} malformed line(s) in {path}", file=sys.stderr)
    return entries


def _entry_text(entry):
    """Extract a flat text string from an entry's message content (best-effort)."""
    if not isinstance(entry, dict):
        return ""
    msg = entry.get("message") or {}
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for b in c:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text") or "")
        return "\n".join(parts)
    return ""


def _identify_harness_command_uuids(entries):
    """Find slash-command entries that didn't go to Claude — display/harness
    events like /exit, /terminal-setup, /model, /compact, /plugin. Discriminator:
    a real plugin command produces a paired `isMeta: true` child carrying the
    expanded skill body; a harness command has no such body (and may have a
    local-command-stdout/stderr/caveat sibling instead).

    Whitelist-free — we use the empirical structural marker rather than
    enumerating which commands belong to which class."""
    by_uuid = {}
    children_of = {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        u = e.get("uuid")
        if not u:
            continue
        by_uuid[u] = e
        pid = e.get("parentUuid")
        if pid:
            children_of.setdefault(pid, []).append(u)

    harness = set()
    for u, e in by_uuid.items():
        if e.get("type") != "user":
            continue
        text = _entry_text(e)
        if "<command-name>" not in text:
            continue
        # Look for an isMeta:true child whose content isn't local-command markup
        has_skill_body = False
        for cu in children_of.get(u, ()):
            child = by_uuid.get(cu)
            if not child or child.get("type") != "user":
                continue
            if not child.get("isMeta"):
                continue
            ctext = _entry_text(child)
            if _LOCAL_COMMAND_MARKUP_RE.search(ctext):
                continue  # this is local-command output, not a skill body
            has_skill_body = True
            break
        if not has_skill_body:
            harness.add(u)
    return harness


def _select_chronological(entries):
    """Return all transcript-type entries in timestamp order. Default mode.

    Picks up everything the file knows about — including content from
    disjoint subtrees that don't share a connected parentUuid chain (which
    happens in long-running sessions resumed across breaks). The cost: when
    a rewind has occurred, the abandoned branch appears inline alongside
    the live continuation in time order. For research/reflection use that's
    a feature — you can see the evolution of thought including roads not
    taken — but `--live-branch-only` exposes the strict tree-walk view for
    when only the resumable conversation matters."""
    out = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        if e.get("type") not in TRANSCRIPT_TYPES:
            continue
        if e.get("isSidechain"):
            continue
        out.append(e)
    out.sort(key=lambda e: e.get("timestamp", ""))
    return out


def _select_live_branch(entries):
    """Walk back from the leaf of the longest live chain to its earliest root.
    Returns ordered list (root first) or [] if no chain found.

    Why longest chain instead of "most recent leaf by timestamp" (what claude
    -r would do): a long-running session with rewinds and forks may contain
    multiple disjoint subtrees. The most recent leaf can live on a stub fork
    that doesn't reach the original conversation. Picking the leaf with the
    longest chain gravitates to the main conversation thread, breaking ties
    by timestamp so live work still wins among equal-length branches.

    Caveat: when the file contains genuinely disjoint subtrees (sessions
    resumed across breaks where parent chains don't reconnect), this only
    returns ONE subtree — you'll miss content that lives in others. Default
    mode (`_select_chronological`) covers that case."""
    msgs = {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        if e.get("type") not in TRANSCRIPT_TYPES:
            continue
        u = e.get("uuid")
        if not u:
            continue
        msgs[u] = e

    # Children set: any uuid that's referenced as a parent (parentUuid OR
    # logicalParentUuid — the latter carries the chain across compaction
    # and other session-break boundaries)
    children = set()
    for e in msgs.values():
        for k in ("parentUuid", "logicalParentUuid"):
            pid = e.get(k)
            if pid:
                children.add(pid)

    # Leaves: terminal user/assistant entries on the main thread
    leaves = [
        m for m in msgs.values()
        if m["uuid"] not in children
        and m.get("type") in ("user", "assistant")
        and not m.get("isSidechain", False)
    ]
    if not leaves:
        return []

    # Compute chain length for every msg (memoized DFS).
    # Iterative form to avoid Python recursion limits on deep chains.
    depth = {}
    for start_uuid in msgs:
        if start_uuid in depth:
            continue
        # Walk back collecting the path until we hit a known node or root
        path = []
        cur_uuid = start_uuid
        guard = set()  # local cycle guard
        while cur_uuid and cur_uuid not in depth and cur_uuid not in guard:
            guard.add(cur_uuid)
            msg = msgs.get(cur_uuid)
            if not msg:
                break
            path.append(cur_uuid)
            pid = msg.get("parentUuid") or msg.get("logicalParentUuid")
            cur_uuid = pid if (pid and pid in msgs) else None
        # Backfill depths along the path
        base = depth.get(cur_uuid, 0) if cur_uuid else 0
        for i, u in enumerate(reversed(path)):
            depth[u] = base + i + 1

    # Pick the leaf whose chain is deepest (most recent timestamp tiebreak)
    leaf = max(leaves, key=lambda m: (depth.get(m["uuid"], 0),
                                      m.get("timestamp", "")))

    # Walk parentUuid back (falling back to logicalParentUuid when parentUuid
    # is null — Claude Code nullifies parentUuid on session-break boundaries
    # like compact_boundary, but logicalParentUuid still points at the
    # pre-boundary tail). Cycle protection is mandatory; otherwise a corrupt
    # file could spin us forever.
    chain = []
    seen = set()
    cur = leaf
    while cur is not None:
        u = cur.get("uuid")
        if not u or u in seen:
            if u in seen:
                print(f"  ! cycle detected at {u}; truncating chain", file=sys.stderr)
            break
        seen.add(u)
        chain.append(cur)
        pid = cur.get("parentUuid") or cur.get("logicalParentUuid")
        cur = msgs.get(pid) if pid else None

    chain.reverse()
    return chain


def _walk_back_one(leaf, msgs, skip=None):
    """Walk back from leaf via parentUuid → logicalParentUuid (compact bridge).

    Returns (chain_root_first, bridges_followed, dead_bridge_or_None, stop_reason)
    where stop_reason is one of:
      'root'        — reached an entry with no parent/logical reference (natural start)
      'dead_bridge' — parent/logical referenced a uuid not in the file
      'skip'        — converged into already-claimed content (fork stub)
      'cycle'       — re-encountered a uuid (corrupt/circular file)
    """
    skip = skip or set()
    chain = []
    seen = set()
    cur = leaf
    bridges = 0
    dead_bridge = None
    stop_reason = "root"
    while cur is not None:
        u = cur.get("uuid")
        if u in seen:
            stop_reason = "cycle"
            break
        if u in skip:
            stop_reason = "skip"
            break
        seen.add(u)
        chain.append(cur)
        parent_id = cur.get("parentUuid")
        nxt = msgs.get(parent_id) if parent_id else None
        if nxt is None:
            logical_id = cur.get("logicalParentUuid")
            nxt = msgs.get(logical_id) if logical_id else None
            if nxt is not None:
                bridges += 1
            elif parent_id or logical_id:
                dead_bridge = {
                    "at_uuid": cur.get("uuid"),
                    "type": cur.get("type"),
                    "subtype": cur.get("subtype"),
                    "ts": cur.get("timestamp"),
                    "wanted_parent": parent_id,
                    "wanted_logical": logical_id,
                }
                stop_reason = "dead_bridge"
                break
            else:
                stop_reason = "root"
                break
        cur = nxt
    chain.reverse()
    return chain, bridges, dead_bridge, stop_reason


def _select_walk_back_segments(entries):
    """Walk back from the latest-eligible leaf, then enumerate orphan
    subtrees (disconnected from the main chain because of dead compact-
    bridge predecessors but still walkable on their own).

    Returns a list of segments in chronological order (oldest segment first,
    main segment last). Each segment is:
      {chain, leaf, bridges, dead_bridge, is_main}
    """
    msgs = {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        u = e.get("uuid")
        if not u:
            continue
        msgs[u] = e

    eligible = [
        e for e in msgs.values()
        if e.get("type") in ("user", "assistant")
        and not e.get("isSidechain", False)
        and e.get("timestamp")
    ]
    if not eligible:
        return []

    # ---- Main segment: walk from latest-by-timestamp eligible leaf ----
    # Prefer true leaves (entries not referenced as parent by anyone) — when
    # multiple entries share the same timestamp (a chain in the same tick),
    # picking an internal node would leave the actual tip outside the chain.
    referenced_as_parent = set()
    for e in msgs.values():
        for k in ("parentUuid", "logicalParentUuid"):
            pid = e.get(k)
            if pid:
                referenced_as_parent.add(pid)
    leaf_eligible = [e for e in eligible if e.get("uuid") not in referenced_as_parent]
    primary_leaf = max(
        leaf_eligible or eligible,
        key=lambda e: e.get("timestamp", ""),
    )
    primary_chain, primary_bridges, primary_dead, _ = _walk_back_one(primary_leaf, msgs)
    claimed = {e.get("uuid") for e in primary_chain}

    # ---- Orphan segments: enumerate eligible entries not in claimed,
    # find their leaves (within-orphan-set), walk each back stopping at
    # already-claimed entries. Discard "fork stubs" — segments that
    # converge into already-claimed content rather than reaching a real
    # root or dead bridge — they're branches that diverged then merged
    # back, not lost upstream history.
    orphans = [e for e in eligible if e.get("uuid") not in claimed]
    orphan_segments = []
    while orphans:
        orphan_uuids = {e.get("uuid") for e in orphans}
        referenced = set()
        for e in orphans:
            for k in ("parentUuid", "logicalParentUuid"):
                pid = e.get(k)
                if pid in orphan_uuids:
                    referenced.add(pid)
        orphan_leaves = [e for e in orphans if e.get("uuid") not in referenced]
        if not orphan_leaves:
            break
        orphan_leaves.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        leaf = orphan_leaves[0]
        chain, bridges, dead, stop_reason = _walk_back_one(leaf, msgs, skip=claimed)
        # Always claim the walked entries so we don't re-walk them, even if
        # we drop the segment (fork stub).
        chain_ids = {e.get("uuid") for e in chain}
        claimed |= chain_ids
        orphans = [e for e in orphans if e.get("uuid") not in claimed]
        if not chain:
            continue
        if stop_reason in ("skip", "cycle"):
            continue  # fork stub: this branch converged into already-walked content
        orphan_segments.append({
            "chain": chain,
            "leaf": leaf,
            "bridges": bridges,
            "dead_bridge": dead,
            "is_main": False,
        })

    # Order: orphan segments by leaf-ts ASCENDING (oldest first), then main last.
    orphan_segments.sort(key=lambda s: s["leaf"].get("timestamp", ""))
    segments = orphan_segments + [{
        "chain": primary_chain,
        "leaf": primary_leaf,
        "bridges": primary_bridges,
        "dead_bridge": primary_dead,
        "is_main": True,
    }]
    return segments


def _verify_walk_segments(entries, segments):
    """Check whether the file's first/last eligible entries by timestamp both
    appear in any segment. Returns a list of (which, entry) tuples for missing
    endpoints — empty list = PASS."""
    eligible = [
        e for e in entries
        if isinstance(e, dict)
        and e.get("type") in ("user", "assistant")
        and not e.get("isSidechain", False)
        and e.get("timestamp")
    ]
    if not eligible:
        return []
    eligible.sort(key=lambda e: e.get("timestamp", ""))
    union_uuids = set()
    for seg in segments:
        union_uuids.update(e.get("uuid") for e in seg["chain"])
    findings = []
    if eligible[0].get("uuid") not in union_uuids:
        findings.append(("first", eligible[0]))
    if eligible[-1].get("uuid") not in union_uuids:
        findings.append(("last", eligible[-1]))
    return findings


def _excerpt_for_diag(entry, n=120):
    text = _entry_text(entry)
    text = " ".join(text.split())
    return (text[:n] + "…") if len(text) > n else text


def _tool_slug(block):
    """Render a tool_use content block as a compact slug."""
    name = block.get("name", "Tool")
    inp = block.get("input") or {}
    if not isinstance(inp, dict):
        inp = {}

    if name == "Bash":
        cmd = (inp.get("command") or "").strip()
        if len(cmd) > 80:
            cmd = cmd[:77] + "..."
        return f"`[Bash: {cmd}]`"
    if name in ("Read", "Edit", "Write", "NotebookEdit"):
        path = inp.get("file_path") or inp.get("notebook_path") or ""
        base = path.rsplit("/", 1)[-1] if path else ""
        return f"`[{name}: {base}]`"
    if name in ("Glob", "Grep"):
        pat = inp.get("pattern") or inp.get("query") or ""
        return f"`[{name}: {pat}]`"
    if name == "TodoWrite":
        todos = inp.get("todos")
        n = len(todos) if isinstance(todos, list) else "?"
        return f"`[TodoWrite: {n} items]`"
    if name in ("Task", "Agent"):
        sub = inp.get("subagent_type") or inp.get("description") or ""
        return f"`[Agent: {sub}]`"
    if name == "SendMessage":
        to = inp.get("to") or ""
        return f"`[SendMessage → {to}]`"
    if name == "WebFetch":
        url = inp.get("url") or ""
        return f"`[WebFetch: {url}]`"
    if name == "WebSearch":
        q = inp.get("query") or ""
        return f"`[WebSearch: {q}]`"
    if name.startswith("mcp__"):
        parts = name.split("__", 2)
        srv = parts[1] if len(parts) > 1 else ""
        tool = parts[2] if len(parts) > 2 else ""
        return f"`[mcp:{srv}/{tool}]`"
    return f"`[{name}]`"


_COMMAND_NAME_RE = re.compile(r"<command-name>([^<]*)</command-name>")
_COMMAND_ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.DOTALL)
_LOCAL_COMMAND_MARKUP_RE = re.compile(r"<local-command-(stdout|stderr|caveat)")
# Older Claude Code versions emitted post-compact summary user messages
# without the isCompactSummary flag. Content-based fallback uses the
# canonical opening phrase, which is specific enough to not collide with
# legitimate user content in practice.
_COMPACT_SUMMARY_OPENING = (
    "This session is being continued from a previous conversation "
    "that ran out of context"
)


def _render_user(entry, opts):
    # System-injected meta content — slash command bodies, local-command
    # caveats, system reminders. The user didn't write any of these.
    # Default skip; --include-meta opts in.
    if entry.get("isMeta") and not opts.get("include_meta"):
        return None

    msg = entry.get("message") or {}
    content = msg.get("content")

    # Collapse content to a single text string (we still need to spot
    # pure-tool_result plumbing messages and the slash-command markup)
    text = None
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if all(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return None  # plumbing
        parts = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                t = (b.get("text") or "").strip()
                if t:
                    parts.append(t)
        text = "\n\n".join(parts) if parts else None
    if not text or not text.strip():
        return None

    # Compaction summary — suppressed by default. The summary is the
    # post-compact context the model needs but it isn't conversation; the
    # boundary marker alone is enough. Detection uses the explicit flag
    # OR the canonical opening phrase (older Claude Code versions didn't
    # emit the flag).
    if not opts.get("include_compact_summaries"):
        if entry.get("isCompactSummary"):
            return None
        if _COMPACT_SUMMARY_OPENING in text:
            return None

    # Slash-command meta entries: <command-name>/foo</command-name> +
    # <command-args>...</command-args>. Render cleanly so the verbose
    # markup doesn't bury the actual user intent.
    if "<command-name>" in text:
        # Harness/display-only commands (e.g. /exit, /terminal-setup, /model,
        # /compact) never went to Claude — they're session-management events,
        # not part of the conversation. Suppressed by default; opt back in
        # via --include-harness-commands.
        if (entry.get("uuid") in opts.get("harness_uuids", ())
                and not opts.get("include_harness_commands")):
            return None
        name_m = _COMMAND_NAME_RE.search(text)
        args_m = _COMMAND_ARGS_RE.search(text)
        cmd = name_m.group(1).strip() if name_m else "?"
        cmd = cmd if cmd.startswith("/") else f"/{cmd}"
        args = args_m.group(1).strip() if args_m else ""
        if args:
            return f"## User (slash command)\n\n`{cmd}` {args}"
        return f"## User (slash command)\n\n`{cmd}`"

    return f"## User\n\n{text.strip()}"


def _render_assistant(entry, include_thinking):
    msg = entry.get("message") or {}
    blocks = msg.get("content") or []
    if not isinstance(blocks, list):
        return None
    parts = []
    for b in blocks:
        if not isinstance(b, dict):
            continue
        bt = b.get("type")
        if bt == "text":
            t = (b.get("text") or "").strip()
            if t:
                parts.append(t)
        elif bt == "thinking" and include_thinking:
            tk = (b.get("thinking") or "").strip()
            if tk:
                parts.append(f"*[thinking]*\n\n{tk}")
        elif bt in ("tool_use", "server_tool_use", "mcp_tool_use"):
            parts.append(_tool_slug(b))
        # tool_result, redacted_thinking, web_search_tool_result, etc. — skip
    if not parts:
        return None
    return "## Assistant\n\n" + "\n\n".join(parts)


def _render_attachment(entry):
    msg = entry.get("message") or {}
    name = (msg.get("filename") or msg.get("name")
            or msg.get("path") or "attachment")
    return f"`[Attachment: {name}]`"


def _detect_fork_origin(entries):
    """If this session was created via `--fork-session`, every entry carries a
    `forkedFrom: {sessionId, messageUuid}` back-pointer to the parent file
    (src/commands/branch/branch.ts:122-146). Return (parent_sid, fork_msg_uuid)
    if found, else (None, None). This is the only cross-file linkage in the
    JSONL contract."""
    for e in entries:
        if not isinstance(e, dict):
            continue
        ff = e.get("forkedFrom")
        if isinstance(ff, dict) and ff.get("sessionId"):
            return ff.get("sessionId"), ff.get("messageUuid")
    return None, None


def _render_compact_boundary(entry):
    cm = entry.get("compactMetadata") or {}
    trigger = cm.get("trigger", "?")
    pre = cm.get("preTokens", "?")
    n = cm.get("messagesSummarized", "?")
    user_ctx = (cm.get("userContext") or "").strip()
    line = f"*[Compaction — `{trigger}`, {pre} tokens, {n} messages summarized"
    if user_ctx:
        # Inline user context (the `/compact <text>` text the user provided).
        # Useful for reflection: "this is where I told it to focus on the
        # auth-flow refactor going forward."
        snippet = user_ctx if len(user_ctx) <= 200 else user_ctx[:197] + "..."
        line += f"; user context: \"{snippet}\""
    line += "]*"
    return f"---\n\n{line}\n\n---"


def _render_chain(chain, opts):
    # Optional slice to post-most-recent-compact-boundary
    if opts.get("post_compact_only"):
        last_boundary = -1
        for i, e in enumerate(chain):
            if (e.get("type") == "system"
                    and e.get("subtype") == "compact_boundary"):
                last_boundary = i
        if last_boundary >= 0:
            chain = chain[last_boundary:]

    # Per-through-line: optional fork markers — uuid → list of file references
    fork_markers = opts.get("fork_markers") or {}

    out_parts = []
    for e in chain:
        if e.get("isSidechain"):
            continue  # belt + suspenders; main JSONLs don't have these in current mode
        u = e.get("uuid")
        # Inline fork marker BEFORE this entry, if applicable
        if u in fork_markers:
            files = fork_markers[u]
            ts = e.get("timestamp", "")[:16].replace("T", " ")
            label = ", ".join(files)
            out_parts.append(
                f"---\n\n*[Fork point at {ts} — alternate path(s): {label}]*\n\n---"
            )
        t = e.get("type")
        rendered = None
        if t == "system":
            if e.get("subtype") == "compact_boundary":
                rendered = _render_compact_boundary(e)
            # other system subtypes: skip
        elif t == "user":
            rendered = _render_user(e, opts)
        elif t == "assistant":
            rendered = _render_assistant(e, opts.get("include_thinking", False))
        elif t == "attachment":
            rendered = _render_attachment(e)
        if rendered:
            out_parts.append(rendered)
    return "\n\n".join(out_parts) + "\n"


# cmd_session was a manual subverb dispatcher; argparse subparsers now route
# directly to cmd_session_list / cmd_session_set / cmd_session_transcript /
# cmd_resume. This stub remains only as documentation of the previous shape.


# ----------------------------- Reflection submission -----------------------------
#
# `mama:reflect` produces methodology-feedback artifacts at tmp/mama_reflection_*.md.
# This is the submission side — list/scan/submit, with a privacy gate via `claude -p`
# before anything goes to GitHub Issues.

FEEDBACK_REPO_DEFAULT = "yobryon/methodical-cc"
FEEDBACK_LABEL = "methodology-feedback"
PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
PRIVACY_SCAN_PROMPT = PROMPT_DIR / "methodology_feedback_privacy_scan.md"
REFLECTION_GLOB_PATTERNS = ("mama_reflection*.md", "pdt_reflection*.md")


def _list_reflection_files(cwd=None):
    """Return list of (path, sent_url_or_None) tuples for reflection artifacts in
    ./tmp/. Sent status determined by sidecar file `<artifact>.sent`."""
    cwd = cwd or Path.cwd()
    refl_dir = cwd / "tmp"
    if not refl_dir.exists():
        return []
    files = []
    seen = set()
    for pat in REFLECTION_GLOB_PATTERNS:
        for p in sorted(refl_dir.glob(pat)):
            if p in seen:
                continue
            seen.add(p)
            sidecar = p.with_suffix(p.suffix + ".sent")
            url = None
            if sidecar.exists():
                lines = sidecar.read_text().strip().splitlines()
                url = lines[0] if lines else "(sent — no url recorded)"
            files.append((p, url))
    return files


def _pick_latest_unsent(cwd=None):
    """Return the most-recently-modified unsent reflection artifact, or None."""
    candidates = [p for p, url in _list_reflection_files(cwd) if url is None]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _extract_reflection_title(path):
    """Pull the title from the artifact's first `# ` heading; fall back to a
    generic dated title."""
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                # Cap at GitHub's title limit (256), but practically keep <120
                if len(title) > 120:
                    title = title[:117] + "..."
                if title:
                    return title
    except OSError:
        pass
    return f"Methodology feedback: {time.strftime('%Y-%m-%d')}"


def _run_privacy_scan(path):
    """Run `claude -p` with the bundled privacy-scan prompt over the artifact.
    Returns (is_clear: bool, output_text: str). If anything prevents the scan
    (claude missing, prompt missing, etc.), returns (True, '<reason>') —
    we don't block submission on infrastructure problems."""
    if not PRIVACY_SCAN_PROMPT.exists():
        return True, f"(privacy scan prompt not found at {PRIVACY_SCAN_PROMPT}; skipping)"
    if not have_claude():
        return True, "(claude not on PATH; skipping privacy scan)"
    try:
        artifact_text = path.read_text()
    except OSError as e:
        return True, f"(could not read {path}: {e}; skipping privacy scan)"

    prompt_text = PRIVACY_SCAN_PROMPT.read_text()
    full_prompt = f"{prompt_text}\n\n{artifact_text}\n"
    try:
        result = subprocess.run(
            ["claude", "-p", "--no-session-persistence", full_prompt],
            capture_output=True, text=True, check=False,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return True, "(privacy scan timed out after 180s; skipping)"
    if result.returncode != 0:
        return True, f"(privacy scan failed: {result.stderr.strip()[:200]}; skipping)"
    output = result.stdout.strip()
    # First non-empty line determines verdict
    first_line = next((ln for ln in output.splitlines() if ln.strip()), "")
    is_clear = first_line.strip().upper().startswith("CLEAR")
    return is_clear, output


def _ensure_github_label(repo, label):
    """Idempotent: ensure the methodology-feedback label exists on the repo.
    Issue templates declare labels but only create them on first UI use, which
    bites the very first `mcc reflect submit` to a fresh repo. We create-if-
    missing here so the actual `gh issue create --label ...` always succeeds.

    Returns (ok, message). On already-exists or successful create, returns
    (True, ...). On other failures (auth, network, perms), returns (False, ...)
    and the caller can decide how to handle."""
    # `gh label create` returns non-zero with "already exists" in stderr if
    # the label is present. We swallow that and treat it as success.
    cmd = [
        "gh", "label", "create", label,
        "--repo", repo,
        "--description", "Methodology reflection / friction / wishes "
                         "from `mcc reflect submit`",
        "--color", "0E8A16",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as e:
        return False, str(e)
    if result.returncode == 0:
        return True, "created"
    stderr = (result.stderr or "").strip()
    if "already exists" in stderr.lower():
        return True, "already-exists"
    return False, stderr


def _submit_reflection_to_github(path, repo, title, label):
    """Run `gh issue create` to publish the artifact. Returns (url, error_msg)
    where exactly one is non-None."""
    if not shutil.which("gh"):
        return None, ("gh CLI not on PATH. Install from https://cli.github.com,\n"
                      f"  or paste manually at https://github.com/{repo}/issues/new")

    # Pre-flight: ensure the label exists. Don't hard-fail if this errors —
    # auth or perm issues here will surface again at issue-create time with
    # the same gh, and the user will see the real error there.
    label_ok, label_msg = _ensure_github_label(repo, label)
    if not label_ok:
        # Soft warning, but try the submission anyway in case the label
        # exists already and the create probe failed for unrelated reasons.
        print(f"  (label pre-flight had a hiccup: {label_msg[:200]}; "
              f"continuing)", file=sys.stderr)

    cmd = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", title,
        "--label", label,
        "--body-file", str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as e:
        return None, str(e)
    if result.returncode != 0:
        return None, f"gh issue create failed:\n  {result.stderr.strip()}"
    # gh prints the issue URL as the last non-empty line of stdout
    lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    url = lines[-1] if lines else "(submitted, but gh did not print the URL)"
    return url, None


# cmd_reflect was a manual subverb dispatcher; argparse subparsers route
# directly to cmd_reflect_list / cmd_reflect_scan / cmd_reflect_submit now.


def cmd_reflect_list(args):
    """List reflection artifacts in ./tmp/, marked sent or unsent."""
    files = _list_reflection_files()
    if not files:
        print(f"No reflection artifacts found in ./tmp/. Run /mama:reflect first.")
        return
    print(f"Reflections in {Path.cwd()}/tmp/:")
    print()
    for p, url in files:
        if url:
            print(f"  {p.name:<60} [sent → {url}]")
        else:
            print(f"  {p.name:<60} [unsent]")


def cmd_reflect_scan(args):
    """Dry-run: just runs the privacy scan and prints output."""
    path = Path(args.path)
    if not path.exists():
        die(f"no file at {path}")
    print(f"Running privacy scan on {path}...")
    print()
    is_clear, output = _run_privacy_scan(path)
    print(output)
    print()
    print(f"Result: {'CLEAR — safe to submit' if is_clear else 'concerns flagged — review before submitting'}")


def cmd_reflect_submit(args):
    """Submit a reflection artifact to GitHub Issues."""
    explicit_path = args.path
    repo = args.repo or FEEDBACK_REPO_DEFAULT
    skip_scan = bool(args.no_scan)
    skip_confirm = bool(args.no_confirm)

    if explicit_path:
        path = Path(explicit_path)
        if not path.exists():
            die(f"no file at {path}")
    else:
        path = _pick_latest_unsent()
        if path is None:
            die("no unsent reflections found in ./tmp/. Specify a path, "
                "or run /mama:reflect first.")
        print(f"Auto-picked latest unsent: {path}")

    sidecar = path.with_suffix(path.suffix + ".sent")
    if sidecar.exists():
        existing = sidecar.read_text().strip().splitlines()
        url = existing[0] if existing else "(unknown)"
        die(f"already submitted: {url}\n  Sidecar: {sidecar}")

    if not skip_scan:
        print(f"Running privacy scan...")
        is_clear, scan_output = _run_privacy_scan(path)
        if is_clear:
            # Only print the scan output if it's a status note (not the literal "CLEAR")
            first = next((ln for ln in scan_output.splitlines() if ln.strip()), "")
            if first.strip().upper() != "CLEAR":
                print(f"  {scan_output}")
            print(f"  ✓ scan: CLEAR")
        else:
            print(f"  ⚠ scan flagged concerns:")
            print()
            for line in scan_output.splitlines():
                print(f"    {line}")
            print()
            if skip_confirm:
                die("aborted: privacy scan flagged concerns and --no-confirm was set")
            if not confirm("Submit anyway?", default=False):
                print("Aborted. The artifact is unchanged; edit it and retry.")
                return

    title = _extract_reflection_title(path)
    print(f"Submitting to {repo}")
    print(f"  Title: \"{title}\"")
    print(f"  Label: {FEEDBACK_LABEL}")
    print(f"  Body:  {path}")
    if not skip_confirm and not confirm("Proceed with submission?", default=True):
        print("Aborted.")
        return

    url, err = _submit_reflection_to_github(path, repo, title, FEEDBACK_LABEL)
    if err:
        die(f"submission failed: {err}")

    sidecar.write_text(f"{url}\n{time.strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
    print(f"✓ Submitted: {url}")
    print(f"  Sidecar written: {sidecar}")


# Session metadata helpers (used by `list` and the `set` picker)

def _registered_names_by_sid():
    """Reverse the .mcc[-scope]/sessions registry.

    Returns {sid: {"name": <name>, "scope": <scope>}}, where scope is "" for
    the default .mcc/ and "<s>" for .mcc-<s>/.
    """
    out = {}
    for d in find_state_dirs():
        sf = d / "sessions"
        if not sf.exists():
            continue
        try:
            text = sf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        scope = "" if d.name == ".mcc" else d.name[len(".mcc-"):]
        for line in text.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            n, sid = line.split("=", 1)
            n = n.strip()
            if ":" in n:
                continue  # namespaced metadata (e.g. `<name>:args`)
            out[sid.strip()] = {"name": n, "scope": scope}
    return out


def _project_jsonl_files(cwd=None, all_projects=False):
    """Return list of (sid, jsonl_path) for the current project (default) or
    all projects (`all_projects=True`)."""
    if not CLAUDE_PROJECTS_ROOT.exists():
        return []
    out = []
    if all_projects:
        for p in CLAUDE_PROJECTS_ROOT.glob("*/*.jsonl"):
            sid = p.stem
            if _looks_like_uuid(sid):
                out.append((sid, p))
    else:
        slug = _project_slug_for_cwd(cwd)
        for p in (CLAUDE_PROJECTS_ROOT / slug).glob("*.jsonl"):
            sid = p.stem
            if _looks_like_uuid(sid):
                out.append((sid, p))
    return out


def _extract_session_meta(jsonl_path):
    """Read a JSONL once and pluck out best-effort title signals + a first-user
    preview. Returns a dict; missing fields are None."""
    agent_name = None
    custom_title = None
    ai_title = None
    first_user_text = None
    last_ts = None
    last_assistant_ts = None
    line_count = 0

    try:
        with open(jsonl_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line_count += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(e, dict):
                    continue

                t = e.get("type")
                ts = e.get("timestamp")
                if ts and (last_ts is None or ts > last_ts):
                    last_ts = ts

                if t == "agent-name":
                    agent_name = e.get("agentName") or agent_name
                elif t == "custom-title":
                    custom_title = e.get("customTitle") or custom_title
                elif t == "ai-title":
                    ai_title = e.get("aiTitle") or ai_title
                elif t == "user":
                    if e.get("isMeta") or e.get("isCompactSummary"):
                        continue
                    text = _entry_text(e).strip()
                    if not text:
                        continue
                    if "<command-name>" in text:
                        continue  # slash-command meta — skip for preview
                    if _COMPACT_SUMMARY_OPENING in text:
                        continue
                    # Skip harness-injected wrappers (local command output,
                    # IDE-opened-file notices, system reminders) — they're
                    # not real user content
                    if text.lstrip().startswith((
                        "<local-command-",
                        "<ide_opened_file>",
                        "<system-reminder>",
                        "<command-message>",
                    )):
                        continue
                    if first_user_text is None:
                        first_user_text = text
                elif t == "assistant":
                    if ts:
                        last_assistant_ts = ts
    except OSError:
        return None

    return {
        "agent_name": agent_name,
        "custom_title": custom_title,
        "ai_title": ai_title,
        "first_user_text": first_user_text,
        "last_ts": last_ts,
        "last_assistant_ts": last_assistant_ts,
        "line_count": line_count,
    }


def _session_title(meta, max_len=80):
    """Best-effort title with fallback chain: /rename -> /title -> ai-title ->
    first user message preview."""
    if not meta:
        return "(unreadable)"
    for k in ("agent_name", "custom_title", "ai_title"):
        v = meta.get(k)
        if v:
            v = " ".join(v.split())
            return v if len(v) <= max_len else v[:max_len - 1] + "…"
    text = meta.get("first_user_text") or ""
    text = " ".join(text.split())
    if not text:
        return "(no preview)"
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


def _format_ts(ts_str):
    """Render an ISO timestamp as 'YYYY-MM-DD HH:MM' for display."""
    if not ts_str:
        return "—"
    # ISO format like 2026-04-29T02:01:30.077Z
    return ts_str[:16].replace("T", " ")


def _gather_session_summaries(cwd=None, all_projects=False):
    """Return list of summary dicts sorted by last_ts descending."""
    registered = _registered_names_by_sid()
    summaries = []
    for sid, path in _project_jsonl_files(cwd=cwd, all_projects=all_projects):
        meta = _extract_session_meta(path)
        if meta is None:
            continue
        reg = registered.get(sid)
        summaries.append({
            "sid": sid,
            "path": path,
            "registered_as": reg["name"] if reg else None,
            "registered_scope": reg["scope"] if reg else None,
            "title": _session_title(meta),
            "last_ts": meta.get("last_ts") or "",
            "lines": meta.get("line_count", 0),
        })
    summaries.sort(key=lambda s: s["last_ts"], reverse=True)
    return summaries


def _print_session_table(summaries, show_path=False, show_scope=False):
    """Render a list of session summaries as a columnar readout. Full SIDs
    are shown so they can be copy-pasted into `mcc session set <name> <sid>`.

    show_scope: include a "Scope" column showing which .mcc-{scope}/ each
    registered session lives in. Only meaningful in multi-project repos.
    """
    if not summaries:
        print("  (none)")
        return
    title_max = max(len(s["title"]) for s in summaries)
    title_w = min(title_max, 80)
    sid_w = 36  # full UUID
    reg_w = max(10, *(len(s["registered_as"] or "") for s in summaries))

    # Compute scope column width if needed
    scope_w = 0
    if show_scope:
        scope_w = max(7, *(len(s.get("registered_scope") or "") for s in summaries))

    if show_scope:
        header = f"  {'Session ID':<{sid_w}}  {'Last activity':<16}  {'Reg.':<{reg_w}}  {'Scope':<{scope_w}}  Title / preview"
        rule   = f"  {'-'*sid_w}  {'-'*16}  {'-'*reg_w}  {'-'*scope_w}  {'-'*title_w}"
    else:
        header = f"  {'Session ID':<{sid_w}}  {'Last activity':<16}  {'Reg.':<{reg_w}}  Title / preview"
        rule   = f"  {'-'*sid_w}  {'-'*16}  {'-'*reg_w}  {'-'*title_w}"
    print(header)
    print(rule)
    for s in summaries:
        ts = _format_ts(s["last_ts"])
        reg = s["registered_as"] or ""
        title = s["title"]
        if len(title) > title_w:
            title = title[:title_w - 1] + "…"
        if show_scope:
            scope = s.get("registered_scope")
            scope_disp = "" if scope is None else (scope or "(default)")
            print(f"  {s['sid']:<{sid_w}}  {ts:<16}  {reg:<{reg_w}}  {scope_disp:<{scope_w}}  {title}")
        else:
            print(f"  {s['sid']:<{sid_w}}  {ts:<16}  {reg:<{reg_w}}  {title}")
        if show_path:
            pad_extra = (scope_w + 2) if show_scope else 0
            print(f"  {' '*sid_w}  {' '*16}  {' '*reg_w}  {' '*pad_extra}{s['path']}")


def cmd_session_list(args):
    """List Claude Code sessions for the current project (or all projects)."""
    all_projects = bool(args.all)
    show_path = bool(args.paths)

    summaries = _gather_session_summaries(all_projects=all_projects)
    where = "all Claude Code projects" if all_projects else f"this project ({Path.cwd()})"
    print(f"Sessions in {where}:")
    print()
    # Show the scope column when this project actually has multiple state scopes,
    # or when listing across projects (where mixed scopes are likely).
    multi_scope = all_projects or len(_list_existing_scopes()) > 1
    _print_session_table(
        summaries,
        show_path=show_path or all_projects,
        show_scope=multi_scope,
    )


def _list_existing_scopes():
    """Return sorted list of scope names ("" for the default .mcc/) for state dirs that exist."""
    scopes = []
    for d in find_state_dirs():
        if d.name == ".mcc":
            scopes.append("")
        elif d.name.startswith(".mcc-"):
            scopes.append(d.name[len(".mcc-"):])
    return sorted(scopes)


def _scope_dir_name(scope):
    return ".mcc" if not scope else f".mcc-{scope}"


def _guess_scope_from_name(session_name, candidate_scopes):
    """If session_name starts with a scope name followed by '-' or '_', return that scope.
    Otherwise return None. Only considers non-empty scopes."""
    for s in candidate_scopes:
        if not s:
            continue
        if session_name == s or session_name.startswith(s + "-") or session_name.startswith(s + "_"):
            return s
    return None


def _resolve_scope_for_write(session_name, explicit_scope=None):
    """Resolve which scope's sessions file to write to.

    explicit_scope: caller-supplied scope ("" or "<name>"). If given, used as-is.
    Else: looks at existing state dirs.
      - 0 dirs → "" (caller will create .mcc/)
      - 1 dir → that scope (no prompt)
      - 2+ dirs → prompt interactively if stdin is a TTY, with a prefix-match
                  default. If not interactive, raises SystemExit with a clear
                  hint to pass --scope.
    """
    if explicit_scope is not None:
        return explicit_scope
    scopes = _list_existing_scopes()
    if not scopes:
        return ""
    if len(scopes) == 1:
        return scopes[0]
    # Multiple scopes — disambiguate
    guess = _guess_scope_from_name(session_name, scopes)
    pretty = ", ".join(s or "(default)" for s in scopes)
    if not sys.stdin.isatty():
        hint = f" (e.g. --scope {guess})" if guess else ""
        die(f"multiple state scopes exist ({pretty}); pass --scope <name> to disambiguate{hint}")
    print(f"Multiple state scopes exist: {pretty}")
    if guess:
        print(f"  (guessing '{guess}' from session name '{session_name}')")
    raw = prompt("Which scope?", default=(guess if guess is not None else "")).strip()
    if raw == "(default)":
        raw = ""
    if raw not in scopes:
        die(f"unknown scope: {raw!r}. Known scopes: {pretty}")
    return raw


def _write_session_registration(name, sid, cwd=None, scope=None):
    """Append/update <name>=<sid> in <scope>/sessions, creating the dir if needed.

    scope: None → resolve via _resolve_scope_for_write (may prompt).
           "" → write to .mcc/sessions.
           "<s>" → write to .mcc-<s>/sessions.
    """
    cwd = cwd or Path.cwd()
    resolved_scope = _resolve_scope_for_write(name, explicit_scope=scope)
    state_dir = cwd / _scope_dir_name(resolved_scope)
    state_dir.mkdir(parents=True, exist_ok=True)
    target = state_dir / "sessions"

    # Read existing, update or append
    existing_lines = []
    if target.exists():
        existing_lines = target.read_text().splitlines()
    out = []
    found = False
    for line in existing_lines:
        s = line.strip()
        if not s or "=" not in s:
            out.append(line)
            continue
        n, _ = s.split("=", 1)
        if n.strip() == name:
            out.append(f"{name}={sid}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{name}={sid}")
    target.write_text("\n".join(out) + "\n")
    return target


def _write_session_args(name, value, scope=None, cwd=None):
    """Set or clear the `<name>:args=...` line in the appropriate sessions file.

    Locates the file by scope (or single-scope shortcut, same logic as session
    registration). value=None means clear. Returns (target_path, action) where
    action is one of: 'set', 'cleared', 'noop' (cleared but nothing was there).
    """
    cwd = cwd or Path.cwd()
    sid, existing_path = find_session(name)
    if sid is None and scope is None:
        die(f"no session registered as '{name}'. "
            f"Run `mcc session set {name} <sid>` first, or pass --scope explicitly.")
    if existing_path is not None:
        target = existing_path
    else:
        # No session yet, but explicit scope given — write into that scope's file.
        target = cwd / _scope_dir_name(scope) / "sessions"
        target.parent.mkdir(parents=True, exist_ok=True)

    key = f"{name}:args"
    existing_lines = target.read_text().splitlines() if target.exists() else []
    out = []
    found = False
    for line in existing_lines:
        s = line.strip()
        if not s or "=" not in s:
            out.append(line)
            continue
        n, _ = s.split("=", 1)
        if n.strip() == key:
            found = True
            if value is None:
                continue  # drop the line (clear)
            out.append(f"{key}={value}")
        else:
            out.append(line)
    if not found and value is not None:
        out.append(f"{key}={value}")
    target.write_text("\n".join(out) + "\n")
    if value is None:
        return target, ("cleared" if found else "noop")
    return target, "set"


def cmd_session_args(args):
    """Get, set, or clear per-session launch args."""
    name = args.name
    explicit_scope = args.scope if args.scope is not None else None
    if args.clear:
        if args.value:
            die("--clear and a value are mutually exclusive")
        target, action = _write_session_args(name, None, scope=explicit_scope)
        if action == "cleared":
            print(f"Cleared {name}:args from {target}")
        else:
            print(f"No saved args for '{name}' (nothing to clear)")
        return
    if not args.value:
        # Show current
        current = find_session_args(name)
        if current is None:
            print(f"No saved args for '{name}'.")
            print(f"Set with: mcc session args {name} \"<args>\"")
        else:
            print(f"{name}:args = {current}")
        return
    # Set
    value = " ".join(args.value)
    # Validate that it tokenizes — fail fast on quote mismatch etc.
    try:
        shlex.split(value)
    except ValueError as e:
        die(f"value does not parse as shell tokens: {e}")
    target, _action = _write_session_args(name, value, scope=explicit_scope)
    print(f"Set {name}:args = {value} (in {target})")


def cmd_session_set(args):
    """Register a session id under a name in .mcc[-scope]/sessions.

    Forms:
      mcc session set <name> <session-id> [--scope <s>]  — non-interactive
      mcc session set [--scope <s>]                      — interactive picker
    """
    rest = list(args.posargs or [])
    explicit_scope = args.scope

    if len(rest) == 2:
        name, sid = rest
        if not _looks_like_uuid(sid):
            die(f"second arg must be a session-id UUID; got '{sid}'")
        target = _write_session_registration(name, sid, scope=explicit_scope)
        print(f"Registered: {name}={sid}")
        print(f"  in: {target}")
        # Only top up team config if team mode is opted-in for this project
        if _team_mode_enabled():
            team_name = ensure_team_setup(verbose=True)
            print(f"  team: {team_name}")
        return

    if len(rest) == 1:
        die("usage: mcc session set <name> <session-id> [--scope <s>]  OR  "
            "mcc session set [--scope <s>]  (no positional args, for the interactive picker)")

    # Interactive picker
    summaries = _gather_session_summaries()
    if not summaries:
        die("no Claude Code sessions found for this project. Have you run "
            "`claude` here yet?")
    print(f"Sessions in {Path.cwd()}:")
    print()
    sid_w = 36
    multi_scope = len(_list_existing_scopes()) > 1
    reg_w = max(10, *(len(s["registered_as"] or "") for s in summaries))
    if multi_scope:
        scope_w = max(7, *(len(s.get("registered_scope") or "") for s in summaries))
        print(f"  {'#':<3}  {'Session ID':<{sid_w}}  {'Last activity':<16}  {'Reg.':<{reg_w}}  {'Scope':<{scope_w}}  {'Title / preview'}")
        print(f"  {'-'*3}  {'-'*sid_w}  {'-'*16}  {'-'*reg_w}  {'-'*scope_w}  {'-'*60}")
    else:
        print(f"  {'#':<3}  {'Session ID':<{sid_w}}  {'Last activity':<16}  {'Reg.':<{reg_w}}  {'Title / preview'}")
        print(f"  {'-'*3}  {'-'*sid_w}  {'-'*16}  {'-'*reg_w}  {'-'*60}")
    for i, s in enumerate(summaries, 1):
        ts = _format_ts(s["last_ts"])
        reg = s["registered_as"] or ""
        title = s["title"]
        if len(title) > 60:
            title = title[:59] + "…"
        if multi_scope:
            scope = s.get("registered_scope")
            scope_disp = "" if scope is None else (scope or "(default)")
            print(f"  {i:<3}  {s['sid']:<{sid_w}}  {ts:<16}  {reg:<{reg_w}}  {scope_disp:<{scope_w}}  {title}")
        else:
            print(f"  {i:<3}  {s['sid']:<{sid_w}}  {ts:<16}  {reg:<{reg_w}}  {title}")
    print()
    raw = prompt(f"Pick a session (1-{len(summaries)})", default="").strip()
    if not raw:
        print("Cancelled.")
        return
    try:
        idx = int(raw)
        if not (1 <= idx <= len(summaries)):
            raise ValueError
    except ValueError:
        die(f"invalid selection: {raw}")
    chosen = summaries[idx - 1]
    default_name = chosen["registered_as"] or ""
    name = prompt("Name to register as", default=default_name).strip()
    if not name:
        die("name cannot be empty")
    target = _write_session_registration(name, chosen["sid"], scope=explicit_scope)
    print()
    print(f"Registered: {name}={chosen['sid']}")
    print(f"  in: {target}")
    if _team_mode_enabled():
        team_name = ensure_team_setup(verbose=True)
        print(f"  team: {team_name}")


def cmd_session_transcript(args):
    """Dump a session's transcript to a single markdown file.

    Default: walk-back from the latest-eligible leaf via parentUuid →
    logicalParentUuid (the compact-bridge field). Verifies that the file's
    first/last eligible messages both made it into the chain; on a negative
    finding, emits a diagnostic to stderr.

    Alt modes:
      --chronological: dump every eligible entry by timestamp (covers
        disjoint subtrees that the walk-back can't reach via parent links).
      --live-branch: longest-chain leaf-pick instead of latest-by-timestamp;
        an escape hatch for cases where the natural leaf is on a stub.
    """
    target = args.target
    output = args.output
    include_thinking = bool(args.include_thinking)
    include_compact_summaries = bool(args.include_compact_summaries)
    include_meta = bool(args.include_meta)
    include_harness_commands = bool(args.include_harness_commands)
    post_compact_only = bool(args.post_compact_only)
    chronological = bool(args.chronological)
    live_branch = bool(args.live_branch)
    if chronological and live_branch:
        die("--chronological and --live-branch are mutually exclusive")

    # Resolve session id
    if _looks_like_uuid(target):
        sid = target
        label = target
    else:
        sid, _src = find_session(target)
        if not sid:
            die(f"no session registered as '{target}' (and not a session-id UUID)")
        label = target

    # Locate JSONL
    jsonl_path = _find_jsonl(sid)
    if jsonl_path is None:
        die(f"could not find JSONL for session {sid} under {CLAUDE_PROJECTS_ROOT}")

    # Parse
    entries = _parse_jsonl(jsonl_path)
    if not entries:
        die(f"{jsonl_path} contained no parseable entries")

    # Pre-compute harness-only command uuids (slash-command entries that
    # didn't go to Claude — /exit, /terminal-setup, /model, etc.).
    harness_uuids = _identify_harness_command_uuids(entries)

    # Detect --fork-session origin (the only cross-file linkage in CC's JSONL
    # contract). Surfaced in transcript headers so a fork file doesn't read
    # like a standalone session.
    fork_origin = _detect_fork_origin(entries)

    base_opts = {
        "include_thinking": include_thinking,
        "include_compact_summaries": include_compact_summaries,
        "include_meta": include_meta,
        "include_harness_commands": include_harness_commands,
        "harness_uuids": harness_uuids,
        "post_compact_only": post_compact_only,
    }

    # ---- Pick chain(s) ----
    segments = []
    if chronological:
        chain = _select_chronological(entries)
        mode = "chronological (all eligible entries by timestamp)"
        single_chain = chain
    elif live_branch:
        chain = _select_live_branch(entries)
        mode = "live-branch (longest reachable chain)"
        single_chain = chain
    else:
        segments = _select_walk_back_segments(entries)
        mode = "walk-back (latest-eligible leaf + orphan-subtree splicing)"
        single_chain = None
        if not segments:
            die(f"no transcript entries found in {jsonl_path}")
    if single_chain is not None and not single_chain:
        die(f"no transcript entries found in {jsonl_path}")

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    fork_line = ""
    if fork_origin and fork_origin[0]:
        parent_sid, fork_msg = fork_origin
        if fork_msg:
            fork_line = (
                f"- **Forked from**: session `{parent_sid}` "
                f"at message `{fork_msg}`\n"
            )
        else:
            fork_line = f"- **Forked from**: session `{parent_sid}`\n"

    # ---- Render body ----
    if segments:
        total_entries = sum(len(s["chain"]) for s in segments)
        total_bridges = sum(s["bridges"] for s in segments)
        seg_lines = []
        for i, seg in enumerate(segments, 1):
            kind = "main" if seg["is_main"] else "orphan"
            leaf = seg["leaf"]
            root = seg["chain"][0]
            seg_lines.append(
                f"  - segment {i} [{kind}]: {len(seg['chain'])} entries, "
                f"{seg['bridges']} bridges, "
                f"root ts {root.get('timestamp')}, leaf ts {leaf.get('timestamp')}"
            )
        seg_block = "\n".join(seg_lines)
        walk_meta = (
            f"- Segments: {len(segments)} (orphan: {len(segments) - 1}, main: 1)\n"
            f"- Total logical bridges followed: {total_bridges}\n"
            f"{seg_block}\n"
        )
        body_parts = []
        for i, seg in enumerate(segments):
            kind = "main" if seg["is_main"] else "orphan"
            leaf = seg["leaf"]
            root = seg["chain"][0]
            body_parts.append(
                f"---\n\n"
                f"## Segment {i + 1} of {len(segments)} — {kind}\n\n"
                f"- Chain: {len(seg['chain'])} entries\n"
                f"- Logical bridges: {seg['bridges']}\n"
                f"- Leaf: `{leaf.get('uuid')}` ts `{leaf.get('timestamp')}`\n"
                f"- Root: `{root.get('uuid')}` ts `{root.get('timestamp')}`\n"
            )
            if seg["dead_bridge"]:
                db = seg["dead_bridge"]
                want_l = (db["wanted_logical"] or "")[:8] if db["wanted_logical"] else None
                want_p = (db["wanted_parent"] or "")[:8] if db["wanted_parent"] else None
                bridge_line = ""
                if want_p:
                    bridge_line += f"parentUuid={want_p} (unresolved)"
                if want_l:
                    if bridge_line:
                        bridge_line += "; "
                    bridge_line += f"logicalParentUuid={want_l} (unresolved)"
                body_parts.append(
                    f"- **Dead bridge** at root: {bridge_line}\n"
                    f"  History prior to this point exists in another segment "
                    f"or is missing from the file.\n"
                )
            body_parts.append("\n---\n\n")
            body_parts.append(_render_chain(seg["chain"], base_opts))
        body = "".join(body_parts)
        entries_summary = total_entries
    else:
        walk_meta = ""
        body = "---\n\n" + _render_chain(single_chain, base_opts)
        entries_summary = len(single_chain)

    header = (
        f"# Transcript: {label}\n\n"
        f"- Session ID: `{sid}`\n"
        f"- Source: `{jsonl_path}`\n"
        f"- Generated: {now}\n"
        f"- Mode: {mode}\n"
        f"- Entries selected: {entries_summary}\n"
        f"{walk_meta}"
        f"{fork_line}"
        f"- Options: thinking={include_thinking} "
        f"compact_summaries={include_compact_summaries} "
        f"meta={include_meta} "
        f"harness_commands={include_harness_commands} "
        f"post_compact_only={post_compact_only}\n\n"
    )

    short_sid = sid[:8]
    ts_label = time.strftime("%Y%m%d-%H%M%S")
    if output:
        out_path = Path(output)
    else:
        out_path = Path("tmp") / f"transcript_{label}_{short_sid}_{ts_label}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + body, encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  {entries_summary} entries from {jsonl_path}")

    # ---- Verification (walk-back mode only) ----
    if chronological or live_branch:
        return

    findings = _verify_walk_segments(entries, segments)
    eligible_count = sum(
        1 for e in entries
        if isinstance(e, dict)
        and e.get("type") in ("user", "assistant")
        and not e.get("isSidechain", False)
        and e.get("timestamp")
    )
    total_bridges = sum(s["bridges"] for s in segments)
    print(
        f"  verification: file eligible={eligible_count} "
        f"chain={entries_summary} segments={len(segments)} bridges={total_bridges}",
        file=sys.stderr,
    )
    if not findings:
        print("  verification: PASS — first and last eligible messages reached", file=sys.stderr)
        return

    print("  verification: NEGATIVE FINDINGS", file=sys.stderr)
    for which, entry in findings:
        print(
            f"    {which} eligible NOT in any segment: "
            f"uuid={(entry.get('uuid') or '')[:8]} "
            f"ts={entry.get('timestamp')} "
            f"type={entry.get('type')}",
            file=sys.stderr,
        )
        print(f"      content: {_excerpt_for_diag(entry)}", file=sys.stderr)
    # Surface dead bridges across all segments
    for i, seg in enumerate(segments, 1):
        db = seg["dead_bridge"]
        if not db:
            continue
        print(
            f"    segment {i} terminated at uuid={(db['at_uuid'] or '')[:8]} "
            f"({db['type']}/{db['subtype']}) ts={db['ts']}",
            file=sys.stderr,
        )
        if db["wanted_parent"]:
            print(
                f"      wanted parentUuid={db['wanted_parent'][:8]} (unresolved)",
                file=sys.stderr,
            )
        if db["wanted_logical"]:
            print(
                f"      wanted logicalParentUuid={db['wanted_logical'][:8]} (unresolved)",
                file=sys.stderr,
            )
    print(
        "  share this diagnostic + the offending session file so we can refine the algorithm.",
        file=sys.stderr,
    )


# ----------------------------- Commands -----------------------------

def inject_agent_identity(name):
    """Put this session's identity into the process environment before launch.

    `os.execvp` replaces the process image but keeps the environment, and
    `subprocess.run` inherits it, so setting it here reaches claude either way.

    This CANNOT live in .claude/settings.json: that env block is project-wide
    and every session in the project would read the same value. Identity is
    per-session by definition, so it has to be injected per-process at launch.

    The same lever carries per-agent credentials later — .mcp.json can
    reference env vars, so the injection that tells the bus who I am can also
    hand a tracker a key that is mine rather than the project's. That closes
    the whoami problem where every agent authenticates as one shared identity
    and comment attribution survives only on convention.
    """
    os.environ["PLUMB_AGENT"] = name
    return name


def _team_launch_args(name, sid, team_name):
    """Build claude argv with team flags.

    Note: --agent-id is stamped as "team-lead" for every session. This is a
    workaround for Claude Code's current permission-gating logic, which routes
    permission prompts to whichever agent matches the team-lead agentId. Our
    real lead is a phantom (never running), so without this stamp permission
    requests would have nowhere to land. The team config file itself is
    untouched — only the launch flag is overridden.
    """
    return [
        "claude", "-r", sid,
        "--team-name", team_name,
        "--agent-name", name,
        "--agent-id", "team-lead",
    ]


def _resolve_persona(persona_arg):
    """Parse 'plugin:role' → (plugin, role, persona_path). Returns (None, None, None) on error.

    Looks for the persona file in two locations, in order:
      1. plugins/<plugin>/personas/<role>.md   — primary-role starter profiles
         (e.g. mama:architect, pdt:design-partner). Brief, identity-only.
      2. plugins/<plugin>/agents/<role>/agent.md — teammate-agent definitions
         (e.g. mama:implementor, mama:ux-designer). Full agent profiles.
    """
    if ":" not in persona_arg:
        return (None, None, None)
    plugin, role = persona_arg.split(":", 1)
    if plugin not in PLUGINS:
        return (None, None, None)
    plugins_root = Path(__file__).resolve().parent.parent / "plugins"
    candidates = [
        plugins_root / plugin / "personas" / f"{role}.md",
        plugins_root / plugin / "agents" / role / "agent.md",
    ]
    for path in candidates:
        if path.exists():
            return (plugin, role, path)
    return (plugin, role, None)


def _ensure_settings_local_allows_read(path):
    """Add Read(<path>) to .claude/settings.local.json's permissions.allow if absent."""
    settings_path = Path(".claude") / "settings.local.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except Exception:
            settings = {}
    else:
        settings = {}
    perms = settings.setdefault("permissions", {})
    allow = perms.setdefault("allow", [])
    rule = f"Read({path})"
    if rule in allow:
        return False
    allow.append(rule)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    return True


def cmd_create(args):
    """Create a new session, register it, optionally pre-load persona profile."""
    name = args.name
    persona = args.persona
    plugin = args.plugin
    scope = args.scope

    # Resolve scope upfront if multiple state dirs exist (interactive prompt allowed here).
    # Resolved value is passed through to the inner agent so it doesn't have to guess.
    scope = _resolve_scope_for_write(name, explicit_scope=scope)

    if not have_claude():
        die("'claude' command not found on PATH.")

    # Resolve persona (if given) and derive plugin from it
    persona_path = None
    if persona:
        persona_plugin, persona_role, persona_path = _resolve_persona(persona)
        if persona_plugin is None:
            die(f"invalid --persona '{persona}'. Expected '<plugin>:<role>' where plugin is one of {PLUGINS}")
        if persona_path is None:
            die(f"persona file not found at expected path for '{persona}'")
        if plugin is None:
            plugin = persona_plugin
        elif plugin != persona_plugin:
            die(f"--plugin '{plugin}' conflicts with --persona '{persona}' (plugin '{persona_plugin}')")

    # If no plugin given/derived, infer from common conventions
    if plugin is None:
        # Default: mama (covers most multi-agent scenarios)
        plugin = "mama"
        print(f"(no --plugin specified; defaulting to '{plugin}'. Pass --plugin <p> to override.)",
              file=sys.stderr)

    if plugin not in PLUGINS:
        die(f"unknown plugin '{plugin}' (expected one of {PLUGINS})")

    # Ensure team setup
    team_name = ensure_team_setup(verbose=False)

    # If persona loading, ensure read permission
    if persona_path:
        if _ensure_settings_local_allows_read(persona_path):
            print(f"  Granted read permission for {persona_path} in .claude/settings.local.json",
                  file=sys.stderr)

    # Construct prompt for `claude -p`. Pass scope explicitly so the inner agent
    # writes to the right .mcc[-scope]/sessions file without having to guess.
    scope_arg = f" --scope {scope}" if scope else ""
    if persona_path:
        prompt_text = (
            f"/{plugin}:session set {name}{scope_arg}\n\n"
            f"Then read your persona profile at @{persona_path} "
            f"and acknowledge with \"ok\"."
        )
    else:
        prompt_text = f"/{plugin}:session set {name}{scope_arg}"

    # Launch claude -p
    print(f"Creating session '{name}' on team '{team_name}'"
          f"{' with persona ' + persona if persona else ''}...", file=sys.stderr)
    print(f"  (claude -p will run; this may take a few seconds)", file=sys.stderr)
    print(file=sys.stderr)

    inject_agent_identity(name)
    rc = subprocess.run(["claude", "-p", prompt_text]).returncode
    if rc != 0:
        die(f"claude -p exited with rc={rc}; session may not have been created")

    # Verify registration
    sid, src = find_session(name)
    print(file=sys.stderr)
    if sid:
        print(f"✓ Created session '{name}' (id {sid}) registered in {src}.")
        print(f"  Resume with: mcc {name}")
        # Top up team config only if team mode is opted-in for this project
        if _team_mode_enabled():
            ensure_team_setup(verbose=False)
    else:
        print(f"⚠ claude -p completed but no session registered as '{name}' was found.",
              file=sys.stderr)
        print(f"  Try running /{plugin}:session set {name} manually inside the new session.",
              file=sys.stderr)


def cmd_resume(args):
    name = args.name
    sid, src = find_session(name)
    if not sid:
        # If we can't find the session but legacy plugin dirs are present,
        # the session likely lives there — prompt the user to migrate first.
        legacy = find_legacy_dirs()
        if legacy:
            print(f"No session '{name}' found in .mcc/, but legacy plugin state dirs exist:",
                  file=sys.stderr)
            for src_dir, dst_dir in legacy:
                print(f"  {src_dir.name}/  →  {dst_dir.name}/", file=sys.stderr)
            print(f"\nRun `mcc migrate` to consolidate them under .mcc/, then try again.",
                  file=sys.stderr)
            sys.exit(1)
        print(f"No session registered as '{name}'.", file=sys.stderr)
        print()
        _print_registered()
        sys.exit(1)
    if not have_claude():
        die("'claude' command not found on PATH.")
    # Team-mode-aware launch: only attach team flags if the project has opted
    # into team mode (`mcc team setup` writes .mcc/team-name as the marker).
    # Otherwise mcc is plain session-naming sugar over `claude -r`.
    team_name = None
    if _team_mode_enabled():
        team_name = ensure_team_setup(verbose=False)
        argv = _team_launch_args(name, sid, team_name)
        launch_note = f"claude -r {sid} (+team flags)"
    else:
        argv = ["claude", "-r", sid]
        launch_note = f"claude -r {sid}"

    # Append per-session args from `<name>:args=...` in sessions file.
    saved_args_raw = find_session_args(name)
    if saved_args_raw:
        try:
            saved_args = shlex.split(saved_args_raw)
        except ValueError as e:
            die(f"could not parse '{name}:args' value as shell tokens: {e}")
        argv.extend(saved_args)
        launch_note += f" +saved-args ({saved_args_raw})"

    # Append CLI passthrough (everything after `--` on the mcc invocation).
    passthrough = getattr(args, "extra", None) or []
    if passthrough:
        argv.extend(passthrough)
        launch_note += f" +passthrough ({' '.join(passthrough)})"

    inject_agent_identity(name)

    on_team = f" on team '{team_name}'" if team_name else ""
    print(f"Resuming '{name}' from {src}{on_team} → {launch_note}", file=sys.stderr)

    # Hand off the terminal to claude.
    #
    # On Unix, os.execvp is canonical: it replaces the current process image
    # in-place, so the python process *becomes* the claude process with the
    # same PID and direct ownership of the controlling terminal.
    #
    # On Windows, os.execvp is a leaky simulation — CPython spawns claude.exe
    # via CreateProcess and exits the parent python.exe. The console host
    # (Windows Terminal, conhost.exe, VSCode's pty wrapper) was tracking the
    # parent for input routing and resize event delivery; when the parent
    # exits, those linkages partially detach, leaving claude with degraded
    # console handles. Symptoms: keyboard input doesn't reach claude (native
    # terminal forces a Task Manager kill), or resize events don't propagate
    # to claude (VSCode terminal renders at the original size forever).
    #
    # Fix on Windows: keep the python process alive as a thin passthrough
    # via subprocess.run. The console host's linkage stays intact, claude
    # runs as a child, and signals (Ctrl-C via the console process group)
    # reach both processes naturally.
    if is_windows():
        rc = subprocess.run(argv).returncode
        sys.exit(rc)
    os.execvp(argv[0], argv)


def _print_registered(args=None):
    """Registered-name dump used by the resume-error path. `mcc list` itself
    is sugar for `mcc session list` (the richer view); this remains because
    a failed `mcc <name>` wants to show exactly the registry it searched."""
    state_dirs = find_state_dirs()
    found_any = False
    for d in state_dirs:
        sessions_file = d / "sessions"
        if not sessions_file.exists():
            continue
        # First pass: collect args metadata so we can render it next to its session.
        args_by_name = {}
        sessions = []
        for line in sessions_file.read_text().splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            n, val = line.split("=", 1)
            n = n.strip()
            val = val.strip()
            if ":args" in n and n.endswith(":args"):
                args_by_name[n[:-len(":args")]] = val
            elif ":" not in n:
                sessions.append((n, val))
        print(f"{sessions_file}:")
        for n, sid in sessions:
            line = f"  {n:<12}  →  claude -r {sid}"
            if n in args_by_name:
                line += f"  (+args: {args_by_name[n]})"
            print(line)
        found_any = True
    if not found_any:
        print("No sessions registered. Use /pdt:session, /mam:session, or /mama:session to register.")


def cmd_status(args):
    print("=== Plugins (claude plugins list) ===")
    if have_claude():
        result = claude_plugins("list")
        if result.returncode != 0:
            print("(claude plugins list failed)")
    else:
        print("(claude not on PATH)")
    print()

    print("=== Methodical-CC state in this project ===")
    state_dirs = find_state_dirs()
    if not state_dirs:
        print("  (none — no .mcc/ directory here)")
    else:
        for d in state_dirs:
            arch_state = d / "architect_state.md"
            ver = detect_version(arch_state) if arch_state.exists() else None
            ver_str = f"  [v{ver}]" if ver else ""
            print(f"  {d}/{ver_str}")
            sessions_file = d / "sessions"
            if sessions_file.exists():
                for line in sessions_file.read_text().splitlines():
                    line = line.strip()
                    if not line or "=" not in line:
                        continue
                    n, sid = line.split("=", 1)
                    print(f"      {n.strip():<10}  claude -r {sid.strip()}")
    print()

    print("=== Team mode ===")
    if _team_mode_enabled():
        team_name = _load_persisted_team_name()
        cfg_path = team_config_path(team_name) if team_name else None
        cfg = read_team_config(team_name) if team_name else None
        print(f"  Enabled — team: {team_name}")
        if cfg_path:
            print(f"  Config: {cfg_path}{' (present)' if cfg else ' (MISSING — run mcc team setup)'}")
        if cfg:
            real_members = [m["name"] for m in cfg.get("members", [])
                            if m.get("name") != PHANTOM_LEAD_NAME]
            print(f"  Members: {', '.join(real_members) if real_members else '(none registered yet)'}")
        print(f"  `mcc <name>` will resume with --team-name flags.")
    else:
        # Detect orphan team configs from older mcc versions or manual setup
        default = _compute_default_team_name(Path.cwd())
        if (TEAMS_ROOT / default / "config.json").exists():
            print(f"  Disabled (no .mcc/team-name marker).")
            print(f"  Note: a team config exists at {TEAMS_ROOT / default}/")
            print(f"  — run `mcc team setup` to opt in, or ignore it for plain "
                  f"session-naming.")
        else:
            print(f"  Disabled — `mcc <name>` runs `claude -r <sid>` with no team flags.")
            print(f"  To enable: `mcc team setup`")


def _validate_plugin(name):
    if name not in PLUGINS:
        die(f"unknown plugin '{name}' (expected one of: {', '.join(PLUGINS)})")


def cmd_enable(args):
    plugin = args.plugin
    _validate_plugin(plugin)
    if not have_claude():
        die("'claude' command not found on PATH.")
    print(f"Enabling {plugin}@{MARKETPLACE} in current project...")
    rc = claude_plugins("enable", "-s", "project", f"{plugin}@{MARKETPLACE}").returncode
    sys.exit(rc)


def cmd_disable(args):
    plugin = args.plugin
    _validate_plugin(plugin)
    if not have_claude():
        die("'claude' command not found on PATH.")
    print(f"Disabling {plugin}@{MARKETPLACE} in current project...")
    rc = claude_plugins("disable", "-s", "project", f"{plugin}@{MARKETPLACE}").returncode
    sys.exit(rc)


def cmd_switch(args):
    target = args.target
    if target not in ("mam", "mama", "off"):
        die(f"unknown switch target '{target}' (expected mam, mama, or off)")
    if not have_claude():
        die("'claude' command not found on PATH.")

    if target == "mam":
        print("Disabling mama, enabling mam (project scope)...")
        claude_plugins("disable", "-s", "project", f"mama@{MARKETPLACE}")
        claude_plugins("enable", "-s", "project", f"mam@{MARKETPLACE}")
        print("→ MAM is now active in this project. (pdt unchanged.)")
    elif target == "mama":
        print("Disabling mam, enabling mama (project scope)...")
        claude_plugins("disable", "-s", "project", f"mam@{MARKETPLACE}")
        claude_plugins("enable", "-s", "project", f"mama@{MARKETPLACE}")
        print("→ MAMA is now active in this project. (pdt unchanged.)")
    else:  # off
        print("Disabling both mam and mama (project scope)...")
        claude_plugins("disable", "-s", "project", f"mam@{MARKETPLACE}")
        claude_plugins("disable", "-s", "project", f"mama@{MARKETPLACE}")
        print("→ Implementation plugins disabled in this project. (pdt unchanged.)")


def cmd_update(args):
    if not have_claude():
        die("'claude' command not found on PATH.")

    print(f"Updating {MARKETPLACE} marketplace and plugins...")
    print()

    failed = []

    print(f"→ marketplace ({MARKETPLACE})")
    rc = subprocess.run(["claude", "plugin", "marketplace", "update", MARKETPLACE]).returncode
    if rc != 0:
        failed.append(f"marketplace update (rc={rc})")

    for plugin in PLUGINS:
        print(f"→ {plugin}")
        rc = subprocess.run(["claude", "plugin", "update", f"{plugin}@{MARKETPLACE}"]).returncode
        if rc != 0:
            failed.append(f"{plugin} update (rc={rc})")

    print()
    if failed:
        print("Some updates returned non-zero exit codes:")
        for f in failed:
            print(f"  • {f}")
        print("(A plugin not installed locally will report an error here — that's expected.)")
        sys.exit(1)
    print("Update complete. Restart any active Claude Code sessions to pick up changes.")

    # If shell completions are installed, mcc's command surface may have
    # changed — remind the user to refresh in current shells.
    shell = _detect_shell()
    if shell:
        rc = _rc_file_for(shell)
        try:
            if rc and rc.exists() and _COMPLETION_BLOCK_BEGIN in rc.read_text():
                print()
                print("Tab-completion: command surface may have changed. Refresh now with:")
                print(f'  eval "$(mcc completions {shell})"')
                print("Or open a new shell.")
        except OSError:
            pass


def cmd_setup(args):
    print("Methodical-CC setup")
    print("===================")
    print()
    print("This installs pdt, mam, mama, bus, and docs at user scope, then asks which (if")
    print("any) should be enabled user-wide. Any combination is valid — including")
    print("all-off (you can enable per-project later).")
    print()
    print("The opinionated default is 'pdt bus' — PDT for design thinking and the bus")
    print("so design and implementation sessions can talk to each other directly.")
    print("Add 'mam' or 'mama' to that if you usually use one of those impl plugins.")
    print()
    if not have_claude():
        die("'claude' command not found on PATH. Install Claude Code first.")
    if not confirm("Proceed?", default=True):
        print("Aborted.")
        return

    print()
    print("Installing plugins at user scope...")
    for plugin in PLUGINS:
        print(f"  → {plugin}")
        result = claude_plugins("install", "-s", "user", f"{plugin}@{MARKETPLACE}", capture=True)
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            print(f"    (note: {stderr or 'install returned non-zero — may already be installed'})")

    print()
    print("Which plugins should be enabled user-wide?")
    print("Enter a space-separated list (e.g. 'pdt bus mama'), 'all', or 'none'.")
    print(f"Available: {', '.join(PLUGINS)}")
    choice = prompt("Enabled user-wide", default="pdt bus").strip().lower()

    if choice == "all":
        enabled = set(PLUGINS)
    elif choice == "none" or not choice:
        enabled = set()
    else:
        enabled = set(choice.split())
        invalid = enabled - set(PLUGINS)
        if invalid:
            die(f"unknown plugins: {', '.join(invalid)}")

    print()
    for plugin in PLUGINS:
        if plugin in enabled:
            print(f"  Enabling {plugin} user-wide...")
            claude_plugins("enable", "-s", "user", f"{plugin}@{MARKETPLACE}", capture=True)
        else:
            print(f"  Disabling {plugin} user-wide...")
            claude_plugins("disable", "-s", "user", f"{plugin}@{MARKETPLACE}", capture=True)

    print()
    if confirm("Install mcc on your PATH (creates ~/.local/bin/mcc)?", default=True):
        source_dir = Path(__file__).resolve().parent
        target_dir = install_mcc_on_path(source_dir)
        if target_dir is not None:
            warn_if_target_not_on_path(target_dir)

    print()
    print("Setup complete. Per-project overrides:")
    print("  mcc enable <plugin>     - enable in current project")
    print("  mcc disable <plugin>    - disable in current project")
    print("  mcc switch mam|mama|off - swap implementation plugin")


def _find_plumb_bin(name):
    """Locate a file in plumb's bin/.

    Prefer the checkout mcc itself lives in (dev repo or marketplace clone —
    always version-matched to this mcc), then the newest installed plugin
    cache. The bus-observer surfaces are read-only, so any recent version is
    safe.
    """
    sibling = Path(__file__).resolve().parent.parent / "plugins" / "plumb" / "bin" / name
    if sibling.is_file():
        return sibling
    def _ver(p):
        try:
            return tuple(int(x) for x in p.parent.parent.name.split("."))
        except ValueError:
            return (0,)
    cached = sorted(Path.home().glob(
        f".claude/plugins/cache/methodical-cc/plumb/*/bin/{name}"), key=_ver)
    return cached[-1] if cached else None


def cmd_bus_tail(args):
    engine = _find_plumb_bin("bus.py")
    if engine is None:
        die("plumb's bus engine not found — is the plumb plugin installed? "
            "(`mcc update` refreshes the marketplace)")
    argv = ["python3", str(engine), "tail", "-n", str(args.lines)]
    if args.no_follow:
        argv.append("--no-follow")
    try:
        sys.exit(subprocess.run(argv).returncode)
    except KeyboardInterrupt:
        sys.exit(0)


def cmd_bus_log(args):
    engine = _find_plumb_bin("bus.py")
    if engine is None:
        die("plumb's bus engine not found — is the plumb plugin installed? "
            "(`mcc update` refreshes the marketplace)")
    argv = ["python3", str(engine), "log", "-n", str(args.lines)]
    for flag, val in (("--record", args.record), ("--thread", args.thread),
                      ("--from", getattr(args, "from_", None)), ("--to", args.to)):
        if val:
            argv += [flag, val]
    sys.exit(subprocess.run(argv).returncode)


def cmd_bus_view(args):
    """Mailbox TUI. Shelled out via `uv run` — the viewer declares its own
    dependencies (PEP 723 inline metadata), so mcc itself stays stdlib-only."""
    viewer = _find_plumb_bin("busview.py")
    if viewer is None:
        die("plumb's bus viewer not found — is the plumb plugin installed? "
            "(`mcc update` refreshes the marketplace)")
    if not shutil.which("uv"):
        die("`uv` is required to run the bus viewer (it installs the viewer's "
            "own dependencies in an ephemeral env; core mcc stays dep-free).\n"
            "  Install: https://docs.astral.sh/uv/  — e.g.\n"
            "    curl -LsSf https://astral.sh/uv/install.sh | sh\n"
            "  or: pipx install uv")
    argv = ["uv", "run", str(viewer)]
    if args.db:
        argv += ["--db", args.db]
    try:
        sys.exit(subprocess.run(argv).returncode)
    except KeyboardInterrupt:
        sys.exit(0)


def cmd_version(args):
    print(f"mcc {MCC_VERSION}")
    print(f"  script: {Path(__file__).resolve()}")


# ----------------------------- Completion --------------------------
#
# Shell tab-completion is split in two halves:
#
#   1. Static structure lives in shell. `mcc completions bash|zsh` emits a
#      complete shell function with all subcommands, sub-verbs, and flags
#      hard-coded (so per-Tab dispatch never invokes Python).
#
#   2. Dynamic value sets are served by the `mcc complete --kind <kind>`
#      fast path. The shell function shells out only for these kinds:
#      session, scope, persona, session_or_scope_or_all, command_path.
#
# Users wire it in via `eval "$(mcc completions bash)"` in their rc file
# (or `mcc completions install`, which appends a marked block for them).

_COMPLETION_BLOCK_BEGIN = "# >>> mcc completions >>>"
_COMPLETION_BLOCK_END   = "# <<< mcc completions <<<"


def _fast_session_names(cwd=None):
    cwd = cwd or Path.cwd()
    names = set()
    for pat in STATE_DIR_GLOBS:
        for d in cwd.glob(pat):
            if not d.is_dir():
                continue
            sessions = d / "sessions"
            if not sessions.exists():
                continue
            try:
                text = sessions.read_text()
            except OSError:
                continue
            for line in text.splitlines():
                line = line.strip()
                if not line or "=" not in line:
                    continue
                n, _ = line.split("=", 1)
                n = n.strip()
                if n:
                    names.add(n)
    return sorted(names)


def _fast_scope_names(cwd=None):
    """Named scopes only — empty/default scope is not surfaced for completion."""
    cwd = cwd or Path.cwd()
    scopes = set()
    for d in cwd.glob(".mcc-*"):
        if d.is_dir():
            suffix = d.name[len(".mcc-"):]
            if suffix:
                scopes.add(suffix)
    return sorted(scopes)


def _fast_personas():
    plugins_root = Path(__file__).resolve().parent.parent / "plugins"
    if not plugins_root.is_dir():
        return []
    out = set()
    for plugin in PLUGINS:
        pdir = plugins_root / plugin
        personas = pdir / "personas"
        if personas.is_dir():
            for p in personas.glob("*.md"):
                out.add(f"{plugin}:{p.stem}")
        agents = pdir / "agents"
        if agents.is_dir():
            for sub in agents.iterdir():
                if sub.is_dir() and (sub / "agent.md").exists():
                    out.add(f"{plugin}:{sub.name}")
    return sorted(out)


def _fast_command_paths():
    """Walk the parser tree and enumerate every reachable command path.

    Powers `mcc complete --kind command_path`. Cheap (parser construction is
    microseconds) and stays in sync with the actual command surface.
    """
    parser = build_parser()
    paths = set()
    for act in parser._actions:
        if isinstance(act, argparse._SubParsersAction):
            for cmd, sp in act.choices.items():
                paths.add(cmd)
                for sub_act in sp._actions:
                    if isinstance(sub_act, argparse._SubParsersAction):
                        for verb in sub_act.choices:
                            paths.add(f"{cmd} {verb}")
            break
    return sorted(paths)


def cmd_complete(args):
    """Fast-path completion data source for shell completion functions.

    Usage: mcc complete --kind <kind>

    Kinds: session, scope, session_or_scope_or_all, persona, plugin,
    command_path.

    Output: candidates one per line on stdout. No errors, no prompts —
    completion functions swallow stderr and treat empty output as "no
    candidates."
    """
    kind = args.kind
    items = []
    if kind == "session":
        items = _fast_session_names()
    elif kind == "scope":
        items = _fast_scope_names()
    elif kind == "session_or_scope_or_all":
        items = sorted(set(_fast_session_names()) | set(_fast_scope_names()) | {"all"})
    elif kind == "persona":
        items = _fast_personas()
    elif kind == "plugin":
        items = list(PLUGINS)
    elif kind == "command_path":
        items = _fast_command_paths()
    for x in items:
        print(x)


# --------------------- Bundled bash completion (file-loaded) ---------------------
# The shell-side completion function lives at tools/completions/mcc.bash and is
# generated from the parser tree by `mcc completions emit`. The file is checked
# into git; CI / pre-commit may run `mcc completions verify` to guard against
# drift.

def _bundled_bash_completion_path():
    return Path(__file__).resolve().parent / "completions" / "mcc.bash"


def _emit_bash_completion():
    p = _bundled_bash_completion_path()
    if not p.exists():
        die(f"missing bundled completion at {p}; run `mcc completions emit`")
    return p.read_text(encoding="utf-8")


def _emit_zsh_completion():
    """Zsh completion via bashcompinit shim. Reuses the bundled bash function."""
    return (
        "# Generated by `mcc completions zsh`. Loads the bash completion\n"
        "# function under zsh's bashcompinit shim.\n"
        "if ! whence -w bashcompinit >/dev/null 2>&1; then\n"
        "    autoload -U +X bashcompinit && bashcompinit\n"
        "fi\n"
        "if ! whence -w compinit >/dev/null 2>&1; then\n"
        "    autoload -U +X compinit && compinit\n"
        "fi\n"
    ) + _emit_bash_completion()


_LEGACY_BASH = r"""
_mcc_complete() {
    COMPREPLY=()
    local cur cword words prev IFS=$' \t\n'
    cur="${COMP_WORDS[COMP_CWORD]}"
    cword=$COMP_CWORD
    words=("${COMP_WORDS[@]}")
    prev=""
    (( cword > 0 )) && prev="${words[$((cword-1))]}"

    # ---- Top level: subcommands ∪ registered session names ----
    if (( cword == 1 )); then
        local subs="list status setup update enable disable switch team create migrate vscode session reflect version help completions"
        local sessions
        sessions=$(mcc complete --kind session 2>/dev/null)
        COMPREPLY=( $(compgen -W "${subs} ${sessions}" -- "${cur}") )
        return
    fi

    local cmd1="${words[1]}"
    local cmd2=""
    local args_start=2

    # ---- Two-level nouns: complete the verb at position 2, then continue ----
    case "$cmd1" in
        team|session|reflect|completions)
            if (( cword == 2 )); then
                local verbs=""
                case "$cmd1" in
                    team)        verbs="setup status" ;;
                    session)     verbs="list set resume transcript" ;;
                    reflect)     verbs="list scan submit" ;;
                    completions) verbs="bash zsh install uninstall print" ;;
                esac
                COMPREPLY=( $(compgen -W "$verbs" -- "$cur") )
                return
            fi
            cmd2="${words[2]}"
            args_start=3
            ;;
    esac

    # ---- Special case: --group <label>=<csv-of-sessions> ----
    # When the previous word is --group and we're typing label=item1,item2,...
    # we complete the comma-separated session list after '='.
    if [[ "$prev" == "--group" && "$cur" == *=* ]]; then
        local label="${cur%%=*}"
        local list="${cur#*=}"
        local last="${list##*,}"
        local prefix=""
        [[ "$list" == *,* ]] && prefix="${list%,*}"
        local sessions s
        sessions=$(mcc complete --kind session 2>/dev/null)
        COMPREPLY=()
        for s in $sessions; do
            [[ "$s" == "$last"* ]] || continue
            if [[ -n "$prefix" ]]; then
                COMPREPLY+=( "${label}=${prefix},${s}" )
            else
                COMPREPLY+=( "${label}=${s}" )
            fi
        done
        return
    fi

    # ---- Flag-with-value: complete the value ----
    case "$prev" in
        --persona)
            local items
            items=$(mcc complete --kind persona 2>/dev/null)
            COMPREPLY=( $(compgen -W "$items" -- "$cur") )
            return ;;
        --plugin)
            COMPREPLY=( $(compgen -W "pdt mam mama bus" -- "$cur") )
            return ;;
        --scope)
            local items
            items=$(mcc complete --kind scope 2>/dev/null)
            COMPREPLY=( $(compgen -W "$items" -- "$cur") )
            return ;;
        --group-by)
            COMPREPLY=( $(compgen -W "scope none custom" -- "$cur") )
            return ;;
        --shell)
            COMPREPLY=( $(compgen -W "bash zsh" -- "$cur") )
            return ;;
        --output)
            compopt -o default 2>/dev/null
            COMPREPLY=()
            return ;;
        --name|--repo|--min-divergence)
            return ;;
        --group)
            # Awaiting "label=..." — let the user type the label
            return ;;
    esac

    # ---- Bare flag completion (cur starts with -) ----
    if [[ "$cur" == -* ]]; then
        local flags=""
        case "$cmd1:$cmd2" in
            create:)                                       flags="--persona --plugin --scope" ;;
            vscode:)                                       flags="--group-by --group --no-folder-open" ;;
            team:setup)                                    flags="--name" ;;
            session:list)                                  flags="--all --paths --show-path" ;;
            session:set)                                   flags="--scope" ;;
            session:transcript)                            flags="--output --min-divergence --include-thinking --include-compact-summaries --include-meta --include-harness-commands --include-incomplete-branches --single-file --live-branch-only --post-compact-only" ;;
            reflect:submit)                                flags="--repo --no-scan --no-confirm" ;;
            completions:install|completions:uninstall)     flags="--shell" ;;
        esac
        COMPREPLY=( $(compgen -W "$flags" -- "$cur") )
        return
    fi

    # ---- Count positional args consumed (skipping flags + their values) ----
    local pos_idx=0 i w
    for ((i=args_start; i<cword; i++)); do
        w="${words[$i]}"
        case "$w" in
            --persona|--plugin|--scope|--group-by|--group|--name|--repo|--shell|--output|--min-divergence)
                ((i++)) ;;
            --*)
                ;;
            *)
                ((pos_idx++)) ;;
        esac
    done

    # ---- Positional completion ----
    case "$cmd1:$cmd2" in
        enable:|disable:)
            (( pos_idx == 0 )) && COMPREPLY=( $(compgen -W "pdt mam mama bus" -- "$cur") )
            return ;;
        switch:)
            (( pos_idx == 0 )) && COMPREPLY=( $(compgen -W "mam mama off" -- "$cur") )
            return ;;
        create:)
            if (( pos_idx == 0 )); then
                local items
                items=$(mcc complete --kind session 2>/dev/null)
                COMPREPLY=( $(compgen -W "$items" -- "$cur") )
            fi
            return ;;
        vscode:)
            local items
            items=$(mcc complete --kind session_or_scope_or_all 2>/dev/null)
            COMPREPLY=( $(compgen -W "$items" -- "$cur") )
            return ;;
        session:resume|session:transcript|session:set)
            if (( pos_idx == 0 )); then
                local items
                items=$(mcc complete --kind session 2>/dev/null)
                COMPREPLY=( $(compgen -W "$items" -- "$cur") )
            fi
            return ;;
        reflect:scan|reflect:submit)
            compopt -o default 2>/dev/null
            COMPREPLY=()
            return ;;
        help:)
            local items
            items=$(mcc complete --kind command_path 2>/dev/null)
            local oldIFS="$IFS"; IFS=$'\n'
            COMPREPLY=( $(compgen -W "$items" -- "$cur") )
            IFS="$oldIFS"
            return ;;
    esac
}
complete -F _mcc_complete mcc
"""
del _LEGACY_BASH  # historical reference only; the bundled file is the source of truth


def _detect_shell():
    name = Path(os.environ.get("SHELL", "")).name
    if name in ("bash", "zsh"):
        return name
    return None


def _rc_file_for(shell):
    home = Path.home()
    if shell == "bash":
        return home / ".bashrc"
    if shell == "zsh":
        return home / ".zshrc"
    return None


def _completions_block(shell):
    return (
        f"{_COMPLETION_BLOCK_BEGIN}\n"
        f'eval "$(mcc completions {shell})"\n'
        f"{_COMPLETION_BLOCK_END}\n"
    )


def _strip_completion_block(text):
    """Remove the marked completion block. Returns (new_text, found)."""
    begin = _COMPLETION_BLOCK_BEGIN
    end = _COMPLETION_BLOCK_END
    if begin not in text:
        return text, False
    pre, _, rest = text.partition(begin)
    _, _, post = rest.partition(end)
    pre = pre.rstrip("\n")
    post = post.lstrip("\n")
    sep = "\n\n" if pre and post else ("\n" if pre or post else "")
    return (pre + sep + post).rstrip("\n") + ("\n" if (pre + post) else ""), True


def _completions_install(shell, rc_override):
    if shell is None:
        shell = _detect_shell()
        if shell is None:
            die("could not detect shell from $SHELL; pass --shell bash|zsh")
    if shell not in ("bash", "zsh"):
        die(f"unsupported shell: {shell} (supported: bash, zsh)")
    rc = rc_override or _rc_file_for(shell)
    if rc is None:
        die(f"no rc file known for shell: {shell}")

    block = _completions_block(shell)
    existing = rc.read_text() if rc.exists() else ""
    stripped, had_block = _strip_completion_block(existing)
    base = stripped.rstrip("\n")
    sep = "\n\n" if base else ""
    new = base + sep + block
    rc.parent.mkdir(parents=True, exist_ok=True)
    rc.write_text(new)
    if had_block:
        print(f"Updated mcc completions block in {rc}")
    else:
        print(f"Added mcc completions block to {rc}")
    print()
    print("To activate now in this shell:")
    print(f'  eval "$(mcc completions {shell})"')
    print("Or open a new shell.")
    if shell == "bash" and sys.platform == "darwin":
        bp = Path.home() / ".bash_profile"
        print()
        print(f"Note: macOS Terminal.app starts a login shell, which loads "
              f"~/.bash_profile, not ~/.bashrc. If completions don't activate "
              f"in new terminals, ensure ~/.bash_profile sources ~/.bashrc:")
        print(f"  [ -f ~/.bashrc ] && source ~/.bashrc")
        if bp.exists():
            try:
                bp_text = bp.read_text()
                if ".bashrc" not in bp_text:
                    print(f"  ({bp} exists but does not appear to source ~/.bashrc.)")
            except OSError:
                pass


def _completions_uninstall(shell, rc_override):
    if shell is None:
        shell = _detect_shell()
        if shell is None:
            die("could not detect shell from $SHELL; pass --shell bash|zsh")
    rc = rc_override or _rc_file_for(shell)
    if rc is None or not rc.exists():
        print(f"No rc file at {rc} — nothing to remove.")
        return
    text = rc.read_text()
    new, found = _strip_completion_block(text)
    if not found:
        print(f"No mcc completions block found in {rc}.")
        return
    rc.write_text(new)
    print(f"Removed mcc completions block from {rc}.")
    print("(Existing shells still have completions loaded; open a new shell to clear.)")


def cmd_completions_bash(args):
    sys.stdout.write(_emit_bash_completion())


def cmd_completions_zsh(args):
    sys.stdout.write(_emit_zsh_completion())


def cmd_completions_print(args):
    shell = args.shell or _detect_shell()
    if shell == "bash":
        sys.stdout.write(_emit_bash_completion())
    elif shell == "zsh":
        sys.stdout.write(_emit_zsh_completion())
    else:
        die("could not detect shell; pass --shell bash|zsh")


def cmd_completions_install(args):
    rc_override = Path(args.rc_file).expanduser() if args.rc_file else None
    _completions_install(args.shell, rc_override)


def cmd_completions_uninstall(args):
    rc_override = Path(args.rc_file).expanduser() if args.rc_file else None
    _completions_uninstall(args.shell, rc_override)


def cmd_completions_emit(args):
    """Regenerate the on-disk bash completion file from the live parser tree."""
    parser = build_parser()
    text = _generate_bash_from_parser(parser)
    target = Path(args.output) if args.output else _bundled_bash_completion_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"Wrote {target}")


def cmd_completions_verify(args):
    """Compare on-disk bash completion against parser-derived output."""
    parser = build_parser()
    expected = _generate_bash_from_parser(parser)
    on_disk = _bundled_bash_completion_path()
    if not on_disk.exists():
        die(f"missing {on_disk}; run `mcc completions emit` to generate it")
    actual = on_disk.read_text(encoding="utf-8")
    if actual == expected:
        print(f"OK: {on_disk} matches the parser-derived output.")
        return
    import difflib
    diff = "".join(difflib.unified_diff(
        actual.splitlines(keepends=True),
        expected.splitlines(keepends=True),
        fromfile=str(on_disk),
        tofile="<parser-derived>",
        n=3,
    ))
    sys.stdout.write(diff)
    die(f"\n{on_disk} is out of date — run `mcc completions emit` and commit the result.")


# ----------------------------- Parser-driven bash generation ------------------
#
# The shell completion script in tools/completions/mcc.bash is generated from
# the argparse parser tree. Any command/flag the parser knows about gets
# completion; anything else does not. This eliminates drift between the tool
# shape and the completion script.
#
# Completion hints are stamped on argparse Actions via a small helper:
#   act = parser.add_argument(...)
#   act.complete = "session" | "scope" | "persona" | "plugin" | "shell" |
#                  "group_by_mode" | "switch_target" | "session_or_scope_or_all"
#                  | "command_path" | "file" | "group_label_eq_csv"
# Bool flags and value-less args get no hint.

def _action_kind(action):
    """Return the completion kind stamped on an action, or None."""
    return getattr(action, "complete", None)


def _is_value_flag(action):
    """True if this argparse action consumes a value after the flag."""
    if not action.option_strings:
        return False
    return action.nargs not in (0,) and not isinstance(
        action, (argparse._StoreTrueAction, argparse._StoreFalseAction,
                 argparse._CountAction, argparse._HelpAction, argparse._VersionAction)
    )


def _all_flag_strings(parser):
    """Set of every long flag declared anywhere in the parser tree (for the
    bash positional-arg counting case-skip table)."""
    flags = set()
    def walk(p):
        for act in p._actions:
            for opt in act.option_strings:
                if opt.startswith("--") and _is_value_flag(act):
                    flags.add(opt)
        for sa in p._actions:
            if isinstance(sa, argparse._SubParsersAction):
                for sub in sa.choices.values():
                    walk(sub)
    walk(parser)
    return flags


def _generate_bash_from_parser(parser):
    """Walk the parser tree and emit a complete bash completion function.

    Output is deterministic (sorted where order doesn't matter) so `mcc
    completions verify` can exact-match the on-disk file.
    """
    # Collect: top-level cmds, sub-verbs per noun, flags + positionals per (cmd, sub).
    # Subparsers structure: parser → subparsers action → choices dict
    top_subs = None
    for act in parser._actions:
        if isinstance(act, argparse._SubParsersAction):
            top_subs = act
            break
    if top_subs is None:
        die("internal: top-level parser has no subparsers")

    top_cmds = sorted(c for c in top_subs.choices if c != "complete")
    # Nouns (have their own subparsers) vs leaves
    nouns = {}  # cmd → [verbs]
    for cmd, sp in top_subs.choices.items():
        sub_action = next((a for a in sp._actions
                           if isinstance(a, argparse._SubParsersAction)), None)
        if sub_action is not None:
            nouns[cmd] = sorted(sub_action.choices.keys())

    # Per-(cmd, verb) flag list and positional kind
    def collect(p):
        flags = []
        positionals = []
        for act in p._actions:
            if isinstance(act, argparse._SubParsersAction):
                continue
            if act.option_strings:
                # Skip help/version
                if isinstance(act, (argparse._HelpAction, argparse._VersionAction)):
                    continue
                # Pick the longest-form long option for completion
                long_opts = [o for o in act.option_strings if o.startswith("--")]
                if long_opts:
                    flags.append(long_opts[0])
            else:
                positionals.append(act)
        return sorted(flags), positionals

    per_cmd = {}  # (cmd1, cmd2) → (flags, positionals)
    for cmd, sp in top_subs.choices.items():
        if cmd in nouns:
            sub_action = next(a for a in sp._actions
                              if isinstance(a, argparse._SubParsersAction))
            for verb, vp in sub_action.choices.items():
                per_cmd[(cmd, verb)] = collect(vp)
        else:
            per_cmd[(cmd, "")] = collect(sp)

    # Build value-flag lookup (flag → completion kind), considering all parsers
    flag_kinds = {}  # "--flag" → kind (or None for "no completion known")
    def gather_flags(p):
        for act in p._actions:
            if isinstance(act, argparse._SubParsersAction):
                for sub in act.choices.values():
                    gather_flags(sub)
                continue
            if not act.option_strings:
                continue
            if not _is_value_flag(act):
                continue
            kind = _action_kind(act)
            for opt in act.option_strings:
                if opt.startswith("--"):
                    # First seen wins — flags reused across subparsers should
                    # share a kind anyway.
                    flag_kinds.setdefault(opt, kind)
    gather_flags(parser)

    value_flags_all = sorted(flag_kinds.keys())

    # ---- Emit bash ----
    out = []
    o = out.append
    o("# Generated by `mcc completions emit` from the argparse parser.")
    o("# DO NOT EDIT BY HAND — run `mcc completions emit` to regenerate.")
    o("")
    o("_mcc_complete() {")
    o("    COMPREPLY=()")
    o("    local cur cword words prev IFS=$' \\t\\n'")
    o('    cur="${COMP_WORDS[COMP_CWORD]}"')
    o("    cword=$COMP_CWORD")
    o('    words=("${COMP_WORDS[@]}")')
    o('    prev=""')
    o('    (( cword > 0 )) && prev="${words[$((cword-1))]}"')
    o("")
    o("    # ---- Top level: subcommands ∪ registered session names ----")
    o("    if (( cword == 1 )); then")
    o(f'        local subs="{ " ".join(top_cmds) } help"')
    o("        local sessions")
    o("        sessions=$(mcc complete --kind session 2>/dev/null)")
    o('        COMPREPLY=( $(compgen -W "${subs} ${sessions}" -- "${cur}") )')
    o("        return")
    o("    fi")
    o("")
    o('    local cmd1="${words[1]}"')
    o('    local cmd2=""')
    o("    local args_start=2")
    o("")
    o("    # ---- Two-level nouns ----")
    o('    case "$cmd1" in')
    for n in sorted(nouns):
        verbs = " ".join(nouns[n])
        o(f"        {n})")
        o("            if (( cword == 2 )); then")
        o(f'                COMPREPLY=( $(compgen -W "{verbs}" -- "$cur") )')
        o("                return")
        o("            fi")
        o('            cmd2="${words[2]}"')
        o("            args_start=3")
        o("            ;;")
    o("    esac")
    o("")
    # Special case: --group label=name1,name2
    o("    # ---- Special case: --group <label>=<csv-of-sessions> ----")
    o('    if [[ "$prev" == "--group" && "$cur" == *=* ]]; then')
    o('        local label="${cur%%=*}"')
    o('        local list="${cur#*=}"')
    o('        local last="${list##*,}"')
    o('        local prefix=""')
    o('        [[ "$list" == *,* ]] && prefix="${list%,*}"')
    o("        local sessions s")
    o("        sessions=$(mcc complete --kind session 2>/dev/null)")
    o("        COMPREPLY=()")
    o('        for s in $sessions; do')
    o('            [[ "$s" == "$last"* ]] || continue')
    o('            if [[ -n "$prefix" ]]; then')
    o('                COMPREPLY+=( "${label}=${prefix},${s}" )')
    o("            else")
    o('                COMPREPLY+=( "${label}=${s}" )')
    o("            fi")
    o("        done")
    o("        return")
    o("    fi")
    o("")
    # Per-flag value completion
    o("    # ---- Flag-with-value: complete the value ----")
    o('    case "$prev" in')
    # Group flags by kind for compactness
    by_kind = {}
    for flag in value_flags_all:
        by_kind.setdefault(flag_kinds[flag], []).append(flag)
    fixed_lists = {
        "plugin": " ".join(PLUGINS),
        "shell": "bash zsh",
        "group_by_mode": "scope none custom",
        "switch_target": "mam mama off",
    }
    # Order: hint kinds with shell shellouts first, then fixed lists, then no-hint
    for kind in sorted(k for k in by_kind if k):
        flags = by_kind[kind]
        if kind == "group_label_eq_csv":
            # --group is handled by the special-case block above; here we just
            # avoid completing it as a regular flag value.
            o(f'        {"|".join(flags)})')
            o("            return ;;")
            continue
        if kind in fixed_lists:
            o(f'        {"|".join(flags)})')
            o(f'            COMPREPLY=( $(compgen -W "{fixed_lists[kind]}" -- "$cur") )')
            o("            return ;;")
        elif kind == "file":
            o(f'        {"|".join(flags)})')
            o("            compopt -o default 2>/dev/null")
            o("            COMPREPLY=()")
            o("            return ;;")
        elif kind == "command_path":
            o(f'        {"|".join(flags)})')
            o("            local items")
            o("            items=$(mcc complete --kind command_path 2>/dev/null)")
            o('            local oldIFS="$IFS"; IFS=$\'\\n\'')
            o('            COMPREPLY=( $(compgen -W "$items" -- "$cur") )')
            o('            IFS="$oldIFS"')
            o("            return ;;")
        else:
            # Generic dynamic kind: shell out to mcc complete --kind <kind>
            o(f'        {"|".join(flags)})')
            o("            local items")
            o(f'            items=$(mcc complete --kind {kind} 2>/dev/null)')
            o('            COMPREPLY=( $(compgen -W "$items" -- "$cur") )')
            o("            return ;;")
    # No-hint value flags: just don't complete
    if None in by_kind:
        o(f'        {"|".join(by_kind[None])})')
        o("            return ;;")
    o("    esac")
    o("")
    # Bare flag completion
    o("    # ---- Bare flag completion (cur starts with -) ----")
    o('    if [[ "$cur" == -* ]]; then')
    o('        local flags=""')
    o('        case "$cmd1:$cmd2" in')
    for (cmd, verb), (flags, _pos) in sorted(per_cmd.items()):
        if not flags:
            continue
        # Filter out --help; argparse always adds it but the shell help is via -h
        flag_list = [f for f in flags if f != "--help"]
        if not flag_list:
            continue
        o(f'            {cmd}:{verb})  flags="{" ".join(flag_list)}" ;;')
    o("        esac")
    o('        COMPREPLY=( $(compgen -W "$flags" -- "$cur") )')
    o("        return")
    o("    fi")
    o("")
    # Positional skip table
    skip_flags = " ".join(sorted(value_flags_all))
    o("    # ---- Count positional args consumed (skipping flags + their values) ----")
    o("    local pos_idx=0 i w")
    o("    for ((i=args_start; i<cword; i++)); do")
    o('        w="${words[$i]}"')
    o('        case "$w" in')
    o(f'            {"|".join(sorted(value_flags_all))})')
    o("                ((i++)) ;;")
    o("            --*)")
    o("                ;;")
    o("            *)")
    o("                ((pos_idx++)) ;;")
    o("        esac")
    o("    done")
    o("")
    # Positional completion per (cmd, verb)
    o("    # ---- Positional completion ----")
    o('    case "$cmd1:$cmd2" in')
    for (cmd, verb), (_flags, positionals) in sorted(per_cmd.items()):
        if not positionals:
            continue
        # Collect kinds for positional slots in order
        slot_kinds = [_action_kind(p) for p in positionals]
        # nargs="*"-style positionals (e.g., vscode tokens): every position takes the same kind
        nargs_star = any(p.nargs in ("*", "+", argparse.REMAINDER) for p in positionals)
        if not any(slot_kinds):
            continue
        o(f"        {cmd}:{verb})")
        if nargs_star:
            kind = slot_kinds[0]
            _emit_positional_case(o, kind, "")  # always complete
        else:
            for idx, kind in enumerate(slot_kinds):
                if not kind:
                    continue
                _emit_positional_case(o, kind, f"(( pos_idx == {idx} )) && ")
        o("            return ;;")
    o("    esac")
    o("}")
    o("complete -F _mcc_complete mcc")
    o("")
    return "\n".join(out)


def _emit_positional_case(o, kind, guard):
    """Emit the right bash bit for a positional kind, behind the guard."""
    fixed_lists = {
        "plugin": " ".join(PLUGINS),
        "switch_target": "mam mama off",
    }
    if kind in fixed_lists:
        o(f'            {guard}COMPREPLY=( $(compgen -W "{fixed_lists[kind]}" -- "$cur") )')
    elif kind == "file":
        o(f"            {guard}compopt -o default 2>/dev/null")
        o(f"            {guard}COMPREPLY=()")
    elif kind == "command_path":
        o(f"            {guard}{{")
        o("                local items")
        o("                items=$(mcc complete --kind command_path 2>/dev/null)")
        o('                local oldIFS="$IFS"; IFS=$\'\\n\'')
        o('                COMPREPLY=( $(compgen -W "$items" -- "$cur") )')
        o('                IFS="$oldIFS"')
        o("            }")
    else:
        o(f"            {guard}{{")
        o("                local items")
        o(f"                items=$(mcc complete --kind {kind} 2>/dev/null)")
        o('                COMPREPLY=( $(compgen -W "$items" -- "$cur") )')
        o("            }")


# ----------------------------- Parser construction --------------------


def _arg(parser, *args, complete=None, **kwargs):
    """add_argument that stamps a 'complete' hint on the resulting action."""
    act = parser.add_argument(*args, **kwargs)
    act.complete = complete
    return act


def build_parser():
    p = argparse.ArgumentParser(
        prog="mcc",
        description="mcc — methodical-cc helper CLI",
        add_help=True,
    )
    p.add_argument("--version", "-v", action="store_true",
                   help="show mcc version and exit")
    sub = p.add_subparsers(dest="cmd", metavar="<command>")

    # --- list ---
    pl = sub.add_parser("list",
                        help="list Claude Code sessions for this project (alias for `session list`)")
    _arg(pl, "--all", action="store_true", help="list across all Claude Code projects")
    _arg(pl, "--paths", action="store_true", help="show jsonl path under each row")
    _arg(pl, "--show-path", action="store_true", help="alias for --paths", dest="paths")
    pl.set_defaults(func=cmd_session_list)

    # --- status ---
    ps = sub.add_parser("status", help="show plugin state and registered sessions")
    ps.set_defaults(func=cmd_status)

    # --- setup ---
    pset = sub.add_parser("setup", help="interactive first-time install + enable user-wide")
    pset.set_defaults(func=cmd_setup)

    # --- update ---
    pu = sub.add_parser("update", help="update marketplace and all plugins")
    pu.set_defaults(func=cmd_update)

    # --- enable / disable ---
    pe = sub.add_parser("enable", help="enable plugin in current project")
    _arg(pe, "plugin", help="plugin name (pdt|mam|mama|bus)", complete="plugin")
    pe.set_defaults(func=cmd_enable)

    pd = sub.add_parser("disable", help="disable plugin in current project")
    _arg(pd, "plugin", help="plugin name (pdt|mam|mama|bus)", complete="plugin")
    pd.set_defaults(func=cmd_disable)

    # --- switch ---
    psw = sub.add_parser("switch", help="swap impl plugin: mam | mama | off")
    _arg(psw, "target", help="mam, mama, or off", complete="switch_target")
    psw.set_defaults(func=cmd_switch)

    # --- create ---
    pc = sub.add_parser(
        "create",
        help="create a new Claude Code session and register it",
    )
    _arg(pc, "name", help="session name (e.g. arch, impl, design)", complete="session")
    _arg(pc, "--persona", help="persona to load, e.g. mama:architect", complete="persona")
    _arg(pc, "--plugin", help="override inferred plugin (pdt|mam|mama)", complete="plugin")
    _arg(pc, "--scope", help="state scope (multi-project repos); '' for default .mcc/",
         complete="scope")
    pc.set_defaults(func=cmd_create)

    # --- migrate ---
    pm = sub.add_parser("migrate",
                        help="consolidate legacy .mam/.mama/.pdt[-scope]/ state dirs")
    pm.set_defaults(func=cmd_migrate)

    # --- vscode ---
    pv = sub.add_parser(
        "vscode",
        help="bootstrap .vscode/tasks.json with mcc session tasks",
        description=(
            "Bootstrap or update .vscode/tasks.json with mcc session tasks.\n"
            "Grouping (--group-by): scope (default in multi-project), none "
            "(default in single-project), custom (with --group)."),
    )
    _arg(pv, "tokens", nargs="*",
         help="session names, scope names, or 'all' (interactive if empty)",
         complete="session_or_scope_or_all")
    _arg(pv, "--group-by", choices=("scope", "none", "custom"),
         help="how to group sessions into VSCode tabs",
         complete="group_by_mode")
    _arg(pv, "--group", action="append", metavar="LABEL=A,B",
         help="custom group: 'label=name1,name2' (repeatable; implies --group-by custom)",
         complete="group_label_eq_csv")
    _arg(pv, "--no-folder-open", action="store_true",
         help="don't auto-run anything on folder open")
    _arg(pv, "--no-term", action="store_true",
         help="ignore .mcc/term and use the interactive/CLI flow")
    pv.set_defaults(func=cmd_vscode)

    # --- term ---
    pterm = sub.add_parser(
        "term",
        help="render .mcc/term into a terminal (wt.exe)",
        description=(
            "Render the .mcc/term arrangement into a live terminal.\n"
            "Targets Windows Terminal (wt.exe) on Windows/WSL and iTerm2\n"
            "(via osascript) on macOS. Use `up --dry-run` to print without\n"
            "running."),
    )
    pterm_sub = pterm.add_subparsers(dest="term_cmd", metavar="<verb>")
    pterm_init = pterm_sub.add_parser(
        "init", help="interactively write .mcc/term (select sessions, tabs, layouts)")
    _arg(pterm_init, "--force", action="store_true",
         help="overwrite an existing .mcc/term without prompting")
    pterm_init.set_defaults(func=cmd_term_init)
    pterm_up = pterm_sub.add_parser(
        "up", help="launch the arrangement (or --dry-run to print it)")
    _arg(pterm_up, "tabs", nargs="*", help="tab names to launch (default: all)")
    _arg(pterm_up, "--dry-run", action="store_true",
         help="print the launch command (wt.exe or AppleScript) without running it")
    _arg(pterm_up, "--terminal", choices=("wt", "iterm"), default=None,
         help="terminal backend (default: wt on Win/WSL, iterm on macOS)")
    pterm_up.set_defaults(func=cmd_term_up)
    pterm_ls = pterm_sub.add_parser("ls", help="show tabs/panes defined in .mcc/term")
    pterm_ls.set_defaults(func=cmd_term_ls)
    pterm.set_defaults(func=lambda a: pterm.print_help())

    # --- team ---
    pt = sub.add_parser("team", help="bus team: setup, status")
    pt_sub = pt.add_subparsers(dest="team_cmd", metavar="<verb>")
    pt_setup = pt_sub.add_parser("setup", help="opt this project into team mode")
    _arg(pt_setup, "--name", help="team name (skip prompt)")
    pt_setup.set_defaults(func=cmd_team_setup)
    pt_status = pt_sub.add_parser("status", help="show project's team state")
    pt_status.set_defaults(func=cmd_team_status)

    # --- session ---
    psess = sub.add_parser("session", help="session list/set/resume/transcript")
    psess_sub = psess.add_subparsers(dest="session_cmd", metavar="<verb>")

    psl = psess_sub.add_parser("list", help="list Claude Code sessions for this project")
    _arg(psl, "--all", action="store_true", help="list across all Claude Code projects")
    _arg(psl, "--paths", action="store_true", help="show jsonl path under each row")
    _arg(psl, "--show-path", action="store_true", help="alias for --paths",
         dest="paths")  # keep behavior; --show-path is the legacy spelling
    psl.set_defaults(func=cmd_session_list)

    psset = psess_sub.add_parser(
        "set", help="register a session under a name in .mcc[-scope]/sessions",
    )
    _arg(psset, "posargs", nargs="*", metavar="[<name> <session-id>]",
         help="optional non-interactive form: name and UUID. Empty for interactive picker.",
         complete="session")
    _arg(psset, "--scope", help="state scope; '' for default .mcc/", complete="scope")
    psset.set_defaults(func=cmd_session_set)

    psresume = psess_sub.add_parser("resume", help="formal verb for `mcc <name>`")
    _arg(psresume, "name", help="registered session name", complete="session")
    _arg(psresume, "extra", nargs=argparse.REMAINDER,
         help="args after `--` are passed through to claude")
    psresume.set_defaults(func=cmd_resume)

    pargs = psess_sub.add_parser(
        "args", help="get/set/clear per-session launch args (forwarded to claude on resume)",
    )
    _arg(pargs, "--clear", action="store_true",
         help="remove any saved args for this session")
    _arg(pargs, "--scope", help="state scope; '' for default .mcc/", complete="scope")
    _arg(pargs, "name", help="registered session name", complete="session")
    _arg(pargs, "value", nargs=argparse.REMAINDER,
         help="new args (e.g. --chrome); omit to show current; --clear to delete")
    pargs.set_defaults(func=cmd_session_args)

    pst = psess_sub.add_parser(
        "transcript", help="dump a session transcript to a single markdown file",
    )
    _arg(pst, "target", help="session name or session-id UUID", complete="session")
    _arg(pst, "--output", help="output file path", complete="file")
    _arg(pst, "--include-thinking", action="store_true")
    _arg(pst, "--include-compact-summaries", action="store_true")
    _arg(pst, "--include-meta", action="store_true")
    _arg(pst, "--include-harness-commands", action="store_true")
    _arg(pst, "--chronological", action="store_true",
         help="alt mode: dump every eligible entry by timestamp")
    _arg(pst, "--live-branch", action="store_true",
         help="alt mode: longest-chain leaf-pick instead of latest-by-timestamp")
    _arg(pst, "--post-compact-only", action="store_true",
         help="skip pre-compact history")
    pst.set_defaults(func=cmd_session_transcript)

    # --- reflect ---
    pr = sub.add_parser("reflect", help="reflect list/scan/submit (methodology feedback)")
    pr_sub = pr.add_subparsers(dest="reflect_cmd", metavar="<verb>")

    prl = pr_sub.add_parser("list", help="list reflection artifacts in ./tmp/")
    prl.set_defaults(func=cmd_reflect_list)

    prs = pr_sub.add_parser("scan", help="dry-run privacy scan")
    _arg(prs, "path", help="reflection artifact to scan", complete="file")
    prs.set_defaults(func=cmd_reflect_scan)

    prsub = pr_sub.add_parser("submit", help="submit reflection to GitHub Issues")
    _arg(prsub, "path", nargs="?", help="reflection artifact (auto-picks latest if omitted)",
         complete="file")
    _arg(prsub, "--repo", help=f"GitHub repo (default {FEEDBACK_REPO_DEFAULT})")
    _arg(prsub, "--no-scan", action="store_true", help="skip privacy scan")
    _arg(prsub, "--no-confirm", action="store_true", help="skip confirmation prompts")
    prsub.set_defaults(func=cmd_reflect_submit)

    # --- docs ---
    from mcc_docs import (
        cmd_docs_setup, cmd_docs_publish, cmd_docs_pull, cmd_docs_status,
    )
    pdocs = sub.add_parser("docs", help="docs publish/pull (stakeholder docs sharing)")
    pdocs_sub = pdocs.add_subparsers(dest="docs_cmd", metavar="<verb>")

    pdocs_setup = pdocs_sub.add_parser("setup", help="interactive: write manifest, set up gitignore")
    pdocs_setup.set_defaults(func=cmd_docs_setup)

    pdocs_pub = pdocs_sub.add_parser("publish", help="convert markdown sources to docx in publish_path")
    _arg(pdocs_pub, "patterns", nargs="*",
         help="optional patterns to narrow the manifest's docs list (paths, dirs, or globs)",
         complete="file")
    _arg(pdocs_pub, "--skip-pending", action="store_true",
         help="publish only docs whose feedback is fully addressed; skip the rest")
    _arg(pdocs_pub, "--include-pending", action="store_true",
         help="publish everything, accepting unresolved feedback")
    pdocs_pub.set_defaults(func=cmd_docs_publish)

    pdocs_pull = pdocs_sub.add_parser("pull", help="parse Word comments in publish_path → feedback files")
    _arg(pdocs_pull, "--resync", action="store_true",
         help="clear seen-comment state and re-pull every comment (existing feedback files preserved)")
    pdocs_pull.set_defaults(func=cmd_docs_pull)

    pdocs_status = pdocs_sub.add_parser("status", help="show docs config and pending-feedback count")
    pdocs_status.set_defaults(func=cmd_docs_status)

    # --- bus (plumb peer-bus utilities) ---
    pbus = sub.add_parser("bus", help="peer-bus utilities (plumb): tail")
    pbus_sub = pbus.add_subparsers(dest="bus_cmd", metavar="<verb>")
    pbus_tail = pbus_sub.add_parser(
        "tail", help="follow this project's bus traffic (read-only observer view)")
    _arg(pbus_tail, "-n", "--lines", type=int, default=20,
         help="how much backlog to show first (default 20)")
    _arg(pbus_tail, "--no-follow", action="store_true", help="print backlog and exit")
    pbus_tail.set_defaults(func=cmd_bus_tail)
    pbus_log = pbus_sub.add_parser(
        "log", help="lookback: chronology, delivery state, repo hash — one line per message")
    _arg(pbus_log, "-n", "--lines", type=int, default=30, help="how far back (default 30)")
    _arg(pbus_log, "--record", help="only messages citing this durable record (substring)")
    _arg(pbus_log, "--thread", help="only this thread")
    _arg(pbus_log, "--from", dest="from_", help="only from this agent")
    _arg(pbus_log, "--to", help="only to this agent")
    pbus_log.set_defaults(func=cmd_bus_log)
    pbus_view = pbus_sub.add_parser(
        "view", help="mailbox TUI over the bus (read-only; needs `uv`)")
    _arg(pbus_view, "--db", help="bus database path (default: ./.mcc/bus.db)",
         complete="file")
    pbus_view.set_defaults(func=cmd_bus_view)

    # --- completions ---
    pcomp = sub.add_parser("completions", help="shell tab-completion: install/emit")
    pcomp_sub = pcomp.add_subparsers(dest="completions_cmd", metavar="<verb>")

    pcomp_bash = pcomp_sub.add_parser("bash", help="emit bash completion script")
    pcomp_bash.set_defaults(func=cmd_completions_bash)
    pcomp_zsh = pcomp_sub.add_parser("zsh", help="emit zsh completion script")
    pcomp_zsh.set_defaults(func=cmd_completions_zsh)

    pcomp_print = pcomp_sub.add_parser("print", help="emit script for detected shell")
    _arg(pcomp_print, "--shell", choices=("bash", "zsh"),
         help="override detected shell", complete="shell")
    pcomp_print.set_defaults(func=cmd_completions_print)

    pcomp_inst = pcomp_sub.add_parser("install", help="install completion in your rc file")
    _arg(pcomp_inst, "--shell", choices=("bash", "zsh"),
         help="override detected shell", complete="shell")
    _arg(pcomp_inst, "--rc-file", help="override rc file path", complete="file")
    pcomp_inst.set_defaults(func=cmd_completions_install)

    pcomp_uninst = pcomp_sub.add_parser("uninstall", help="remove completion from your rc file")
    _arg(pcomp_uninst, "--shell", choices=("bash", "zsh"),
         help="override detected shell", complete="shell")
    _arg(pcomp_uninst, "--rc-file", help="override rc file path", complete="file")
    pcomp_uninst.set_defaults(func=cmd_completions_uninstall)

    pcomp_emit = pcomp_sub.add_parser(
        "emit", help="regenerate the bundled bash completion file from the parser")
    _arg(pcomp_emit, "--output", help="override output path", complete="file")
    pcomp_emit.set_defaults(func=cmd_completions_emit)

    pcomp_verify = pcomp_sub.add_parser(
        "verify", help="check that the bundled completion matches the parser")
    pcomp_verify.set_defaults(func=cmd_completions_verify)

    # --- complete (fast-path; not advertised to users) ---
    pcompfast = sub.add_parser("complete", help=argparse.SUPPRESS)
    _arg(pcompfast, "--kind", required=True,
         choices=("session", "scope", "session_or_scope_or_all",
                  "persona", "plugin", "command_path"))
    pcompfast.set_defaults(func=cmd_complete)

    # --- version ---
    pver = sub.add_parser("version", help="show mcc version")
    pver.set_defaults(func=cmd_version)

    return p


# ----------------------------- Top-level help (categorical) -------------------

TOP_HELP_GROUPS = [
    ("Session", [
        ("<name>",  "Resume session by name (shorthand for `session resume`)"),
        ("create",  "Create + register a new session"),
        ("list",    "List Claude Code sessions (alias for `session list`)"),
        ("session", "session list/set/resume/transcript (`mcc session -h`)"),
    ]),
    ("Project", [
        ("status",  "Show plugin state and registered sessions"),
        ("vscode",  "Bootstrap .vscode/tasks.json with session tasks"),
        ("term",    "Render .mcc/term into a terminal (`mcc term -h`)"),
        ("team",    "Bus team setup/status (`mcc team -h`)"),
        ("docs",    "Stakeholder docs publish/pull (`mcc docs -h`)"),
        ("bus",     "Peer-bus utilities: tail traffic (`mcc bus -h`)"),
        ("migrate", "Migrate legacy .mam/.mama/.pdt[-scope]/ state dirs"),
    ]),
    ("Plugins", [
        ("setup",   "Interactive first-time install + enable user-wide"),
        ("enable",  "Enable plugin (pdt|mam|mama|bus) in current project"),
        ("disable", "Disable plugin (pdt|mam|mama|bus) in current project"),
        ("switch",  "Swap impl plugin: mam | mama | off"),
        ("update",  "Update the marketplace and all plugins"),
    ]),
    ("Feedback", [
        ("reflect", "reflect list/scan/submit (`mcc reflect -h`)"),
    ]),
    ("Shell", [
        ("completions", "Tab-completion: install/emit (`mcc completions -h`)"),
    ]),
    ("Other", [
        ("version", "Show mcc version"),
        ("help",    "Show this help (or `mcc <cmd> -h` for details)"),
    ]),
]


def print_help():
    print("mcc — methodical-cc helper CLI")
    print()
    print("Usage:")
    print("  mcc <command> [args...]")
    print("  mcc <name>                 Resume registered session")
    print()
    for group, items in TOP_HELP_GROUPS:
        print(f"{group}:")
        for tok, desc in items:
            print(f"  {tok:<11} {desc}")
        print()
    print("Run `mcc <command> -h` for detailed help.")


# ----------------------------- Dispatch -----------------------------

def main():
    argv = sys.argv[1:]

    # Fast path for shell tab-completion. Must stay cheap — invoked on every
    # Tab keypress that hits a dynamic slot.
    if argv and argv[0] == "complete":
        # Build a minimal parser just for this subcommand
        parser = build_parser()
        args = parser.parse_args(argv)
        return args.func(args)

    # Top-level help / version shortcuts (categorical print_help)
    if not argv or argv[0] in ("help", "-h", "--help"):
        print_help()
        return
    if argv[0] in ("--version", "-v"):
        cmd_version(None)
        return

    parser = build_parser()
    known_cmds = set()
    for act in parser._actions:
        if isinstance(act, argparse._SubParsersAction):
            known_cmds.update(act.choices.keys())
            break

    # Bareword resume: if argv[0] isn't a known command and isn't a flag,
    # treat as `mcc session resume <name>`. Optional `--` separator forwards
    # the rest of argv to the launched claude as passthrough args.
    if argv[0] not in known_cmds and not argv[0].startswith("-"):
        name = argv[0]
        extra = []
        if len(argv) > 1:
            if argv[1] == "--":
                extra = argv[2:]
            else:
                die(f"unknown command '{name}' (bareword resume takes a name; "
                    f"use `mcc {name} -- <args>` to pass args through to claude)")
        ns = argparse.Namespace(name=name, extra=extra)
        return cmd_resume(ns)

    args = parser.parse_args(argv)

    # Each leaf subparser sets `func` via set_defaults. Nouns without a verb
    # fall through here with no `func`.
    func = getattr(args, "func", None)
    if func is None:
        # Identify which noun was given and emit its help
        if args.cmd in ("team", "session", "reflect", "completions"):
            # Find the corresponding subparser and print its help
            for act in parser._actions:
                if isinstance(act, argparse._SubParsersAction):
                    sp = act.choices.get(args.cmd)
                    if sp is not None:
                        sp.print_help()
                        return
        die(f"missing subcommand for `mcc {args.cmd}` (try `mcc {args.cmd} -h`)")

    # Top-level --version handling (when argparse did parse it)
    if getattr(args, "version", False):
        cmd_version(None)
        return

    func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(130)

