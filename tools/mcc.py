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
import shutil
import subprocess
import sys
from pathlib import Path

MCC_VERSION = "1.11.0"

import json
import time

PLUGINS = ("pdt", "mam", "mama", "bus")
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
            out.append((n.strip(), sid.strip()))
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


def cmd_team(argv):
    if not argv:
        die("usage: mcc team <setup|status>")
    sub = argv[0]
    if sub == "setup":
        return cmd_team_setup(argv[1:])
    if sub == "status":
        return cmd_team_status(argv[1:])
    die(f"unknown team subcommand '{sub}' (expected: setup, status)")


def cmd_team_setup(argv):
    """Interactive: prompt for team name (default = persisted or dirname).
    Non-interactive: `mcc team setup --name <name>` skips the prompt."""
    print("Bus team setup")
    print("==============")
    print()

    # Parse --name flag for non-interactive use
    explicit_name = None
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--name" and i + 1 < len(argv):
            explicit_name = argv[i + 1]
            i += 2
        else:
            rest.append(argv[i])
            i += 1
    if rest:
        die(f"unknown args to `team setup`: {' '.join(rest)}")

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


def cmd_team_status(argv):
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


def cmd_migrate(argv):
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


def _make_session_task(name, group="personas"):
    return {
        "label": f"mcc:{name}",
        "type": "shell",
        "command": f"mcc {name}",
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


def cmd_vscode(argv):
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
    """
    no_folder_open = False
    group_by = None
    custom_groups = []  # list of (label, [names])
    cli_args = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--no-folder-open":
            no_folder_open = True
            i += 1
        elif a == "--group-by":
            if i + 1 >= len(argv):
                die("--group-by requires a value (one of: scope, none, custom)")
            v = argv[i + 1].strip().lower()
            if v not in VALID_GROUP_BY:
                die(f"--group-by must be one of: {', '.join(VALID_GROUP_BY)} (got {v!r})")
            group_by = v
            i += 2
        elif a == "--group":
            if i + 1 >= len(argv):
                die("--group requires a value like 'label=name1,name2'")
            spec = argv[i + 1]
            if "=" not in spec:
                die(f"--group expected 'label=name1,name2', got {spec!r}")
            label, csv = spec.split("=", 1)
            label = _validate_group_label(label)
            members = [s.strip() for s in csv.split(",") if s.strip()]
            if not members:
                die(f"--group {label!r} has no members")
            custom_groups.append((label, members))
            i += 2
        elif a.startswith("--"):
            die(f"unknown flag: {a}")
        else:
            cli_args.append(a)
            i += 1

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


def _categorize_leaf(leaf):
    """Classify a terminal main-thread entry as 'endpoint' (real conversational
    end) or 'noise' (tool-flow artifact, harness-injected, slash command, etc.).

    The default through-line selection only considers 'endpoint' leaves —
    avoids producing transcript files that end mid-tool-call or on harness
    plumbing. --include-incomplete-branches restores noise leaves for
    forensic work."""
    t = leaf.get("type")
    msg = leaf.get("message") or {}
    content = msg.get("content")

    if t == "assistant":
        if not isinstance(content, list):
            return "noise"
        block_types = [b.get("type") for b in content if isinstance(b, dict)]
        # Last block being tool_use means Claude was about to call a tool but
        # the tool_result never came back — interrupted mid-flight.
        if block_types and block_types[-1] == "tool_use":
            return "noise"
        has_text = any(
            isinstance(b, dict) and b.get("type") == "text"
            and (b.get("text") or "").strip()
            for b in content
        )
        return "endpoint" if has_text else "noise"

    if t == "user":
        if leaf.get("isMeta") or leaf.get("isCompactSummary"):
            return "noise"
        if isinstance(content, str):
            return "endpoint" if content.strip() else "noise"
        if not isinstance(content, list):
            return "noise"
        block_types = [b.get("type") for b in content if isinstance(b, dict)]
        has_text = any(
            isinstance(b, dict) and b.get("type") == "text"
            and (b.get("text") or "").strip()
            for b in content
        )
        # tool_result with no real text = orphaned tool_result, not a real msg
        if "tool_result" in block_types and not has_text:
            return "noise"
        if has_text:
            text = next(
                (b["text"] for b in content
                 if isinstance(b, dict) and b.get("type") == "text"),
                "",
            )
            stripped = text.lstrip()
            if stripped.startswith("<command-name>"):
                return "noise"
            if stripped.startswith(("<local-command-", "<ide_opened_file>",
                                    "<system-reminder>")):
                return "noise"
            return "endpoint"
        return "noise"

    return "noise"


def _walk_chain(leaf, msgs):
    """Walk parentUuid+logicalParentUuid back from leaf. Returns ordered list
    (root-first), with cycle protection."""
    chain = []
    cur = leaf
    seen = set()
    while cur is not None:
        u = cur.get("uuid")
        if not u or u in seen:
            break
        seen.add(u)
        chain.append(cur)
        pid = cur.get("parentUuid") or cur.get("logicalParentUuid")
        cur = msgs.get(pid) if pid else None
    chain.reverse()
    return chain


def _select_through_lines(entries, min_divergence=10, include_incomplete=False):
    """Identify significant through-lines: each one is a complete chain from a
    real-endpoint leaf back to the file's earliest reachable root, where the
    chain has at least `min_divergence` entries that don't appear in any other
    selected through-line.

    Returns a list of dicts:
      {leaf, chain (root-first), chain_set, unique_count, fork_points}

    Sorted by leaf timestamp DESCENDING — most recent through-line is index 0
    (and gets the smallest filename number).

    Fork points are nodes along the chain whose parents have other children
    leading to OTHER selected through-lines. Annotated as
      [(uuid_of_first_child_after_fork, sorted_list_of_other_through_line_indices)]
    in the order they appear when walking root-to-leaf.
    """
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

    # Children-set check (parentUuid + logicalParentUuid) — same logic as
    # _select_live_branch's leaf detection.
    children_set = set()
    for e in msgs.values():
        for k in ("parentUuid", "logicalParentUuid"):
            pid = e.get(k)
            if pid:
                children_set.add(pid)

    candidates = [
        m for m in msgs.values()
        if m["uuid"] not in children_set
        and m.get("type") in ("user", "assistant")
        and not m.get("isSidechain", False)
    ]
    if not include_incomplete:
        candidates = [c for c in candidates if _categorize_leaf(c) == "endpoint"]
    if not candidates:
        return []

    # Walk each candidate back to root (uses + cycle protection)
    chain_lists = {}
    chain_sets = {}
    for leaf in candidates:
        chain_list = _walk_chain(leaf, msgs)
        chain_lists[leaf["uuid"]] = chain_list
        chain_sets[leaf["uuid"]] = {e["uuid"] for e in chain_list}

    # Refcount: how many candidate chains include each uuid
    import collections as _c
    refcount = _c.Counter()
    for s in chain_sets.values():
        for u in s:
            refcount[u] += 1

    # Apply divergence filter
    selected = []
    for leaf in candidates:
        chain_set = chain_sets[leaf["uuid"]]
        unique = sum(1 for u in chain_set if refcount[u] == 1)
        if unique < min_divergence:
            continue
        selected.append({
            "leaf": leaf,
            "chain": chain_lists[leaf["uuid"]],
            "chain_set": chain_set,
            "unique_count": unique,
        })

    # Sort by leaf timestamp DESCENDING (most recent through-line = index 0)
    selected.sort(
        key=lambda d: d["leaf"].get("timestamp", ""),
        reverse=True,
    )

    # Refcount over SELECTED chains only (for fork-point cross-references)
    refcount_selected = _c.Counter()
    uuid_to_tl_idxs = _c.defaultdict(list)
    for i, tl in enumerate(selected):
        for u in tl["chain_set"]:
            refcount_selected[u] += 1
            uuid_to_tl_idxs[u].append(i)

    # Full children map across all msgs (used for sibling lookup at fork points)
    full_children = _c.defaultdict(list)
    for u, e in msgs.items():
        for k in ("parentUuid", "logicalParentUuid"):
            pid = e.get(k)
            if pid:
                full_children[pid].append(u)

    # Identify fork points per through-line
    for i, tl in enumerate(selected):
        forks = []
        for entry in tl["chain"]:
            pid = entry.get("parentUuid") or entry.get("logicalParentUuid")
            if not pid:
                continue
            sibs = full_children.get(pid, ())
            if len(sibs) <= 1:
                continue  # no fork
            # Find OTHER through-lines that pass through any sibling
            others = set()
            my_uuid = entry["uuid"]
            for sib in sibs:
                if sib == my_uuid:
                    continue
                others.update(uuid_to_tl_idxs.get(sib, ()))
            others.discard(i)
            if others:
                forks.append((my_uuid, sorted(others)))
        tl["fork_points"] = forks

    return selected


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


def _through_line_filename(idx, total):
    """Stable filename like through-line-01.md, padded to width of total count."""
    width = max(2, len(str(total)))
    return f"through-line-{idx + 1:0{width}d}.md"


def _through_line_title(tl, max_len=80):
    """Best-effort title for a through-line: last user message preview."""
    for e in reversed(tl["chain"]):
        if e.get("type") != "user":
            continue
        if e.get("isMeta") or e.get("isCompactSummary"):
            continue
        text = _entry_text(e).strip()
        if not text:
            continue
        if "<command-name>" in text:
            continue
        if text.lstrip().startswith(("<local-command-", "<ide_opened_file>",
                                     "<system-reminder>")):
            continue
        if _COMPACT_SUMMARY_OPENING in text:
            continue
        text = " ".join(text.split())
        return text if len(text) <= max_len else text[:max_len - 1] + "…"
    # Fallback: last assistant message preview
    for e in reversed(tl["chain"]):
        if e.get("type") != "assistant":
            continue
        text = _entry_text(e).strip()
        if text:
            text = " ".join(text.split())
            return text if len(text) <= max_len else text[:max_len - 1] + "…"
    return "(no preview)"


def _render_through_line_files(through_lines, sid, label, jsonl_path, opts, out_dir,
                                fork_origin=None):
    """Render an index.md plus one through-line-NN.md per through-line.
    Returns list of (filename, num_entries_rendered) tuples."""
    total = len(through_lines)
    # Pre-compute filenames for cross-referencing in fork markers
    filenames = [_through_line_filename(i, total) for i in range(total)]
    titles = [_through_line_title(tl) for tl in through_lines]

    # Index
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    idx_lines = [
        f"# Transcript: {label}",
        "",
        f"- Session ID: `{sid}`",
        f"- Source: `{jsonl_path}`",
        f"- Generated: {now}",
        f"- Through-lines: **{total}**",
        f"- Min divergence threshold: {opts.get('min_divergence')}",
        f"- Mode: per-through-line (one file per significant branch)",
    ]
    if fork_origin and fork_origin[0]:
        parent_sid, fork_msg = fork_origin
        if fork_msg:
            idx_lines.append(
                f"- **Forked from**: session `{parent_sid}` at message `{fork_msg}`"
            )
        else:
            idx_lines.append(f"- **Forked from**: session `{parent_sid}`")
    idx_lines.extend([
        "",
        "## Through-lines",
        "",
        "| # | File | Leaf time | Chain length | Unique entries | Forks | Title / preview |",
        "|---|------|-----------|--------------|----------------|-------|-----------------|",
    ])
    for i, tl in enumerate(through_lines):
        leaf = tl["leaf"]
        ts = leaf.get("timestamp", "")[:16].replace("T", " ")
        chain_len = len(tl["chain"])
        unique = tl["unique_count"]
        forks = len(tl.get("fork_points", []))
        title = titles[i].replace("|", "\\|")
        idx_lines.append(
            f"| {i + 1} | [{filenames[i]}](./{filenames[i]}) | {ts} | "
            f"{chain_len} | {unique} | {forks} | {title} |"
        )
    idx_lines.append("")
    idx_lines.append(
        "Through-lines are numbered by leaf timestamp, most-recent first. "
        "The unique-entries count reflects entries that don't appear in any "
        "other through-line — a measure of how much this branch diverges."
    )
    idx_lines.append("")
    (out_dir / "index.md").write_text("\n".join(idx_lines))

    results = []
    for i, tl in enumerate(through_lines):
        # Build fork-marker map for this through-line
        fork_markers = {}
        for uuid, other_idxs in tl.get("fork_points", []):
            files = [filenames[oi] for oi in other_idxs]
            fork_markers[uuid] = files

        chain_opts = dict(opts)
        chain_opts["fork_markers"] = fork_markers
        body = _render_chain(tl["chain"], chain_opts)

        leaf = tl["leaf"]
        ts = leaf.get("timestamp", "")[:16].replace("T", " ")

        # Per-file header
        header_lines = [
            f"# Through-line {i + 1} of {total}: {ts}",
            "",
            f"- Session ID: `{sid}`",
            f"- Leaf UUID: `{leaf.get('uuid')}`",
            f"- Leaf timestamp: `{leaf.get('timestamp', '')}`",
            f"- Chain length: {len(tl['chain'])} entries",
            f"- Unique to this branch: {tl['unique_count']}",
            f"- Fork points on this path: {len(tl.get('fork_points', []))}",
            f"- Index: [index.md](./index.md)",
        ]
        if fork_origin and fork_origin[0]:
            parent_sid, fork_msg = fork_origin
            if fork_msg:
                header_lines.append(
                    f"- Forked from: session `{parent_sid}` at message `{fork_msg}`"
                )
            else:
                header_lines.append(f"- Forked from: session `{parent_sid}`")
        if tl.get("fork_points"):
            related = sorted({fi for _, ois in tl["fork_points"] for fi in ois})
            related_files = [f"[{filenames[ri]}](./{filenames[ri]})"
                             for ri in related]
            header_lines.append(
                f"- Related (sibling branches): {', '.join(related_files)}"
            )
        header_lines.append("")
        header_lines.append("---")
        header_lines.append("")

        (out_dir / filenames[i]).write_text(
            "\n".join(header_lines) + "\n" + body
        )
        results.append((filenames[i], len(tl["chain"])))
    return results


def cmd_session(argv):
    if not argv:
        die("usage: mcc session <list|set|resume|transcript> ...")
    sub = argv[0]
    if sub == "transcript":
        return cmd_session_transcript(argv[1:])
    if sub == "list":
        return cmd_session_list(argv[1:])
    if sub == "set":
        return cmd_session_set(argv[1:])
    if sub == "resume":
        # Formal verb for the `mcc <name>` shorthand.
        return cmd_resume(argv[1:])
    die(f"unknown session subcommand '{sub}' "
        f"(expected: list, set, resume, transcript)")


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
            ["claude", "-p", full_prompt],
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


def cmd_reflect(argv):
    if not argv:
        die("usage: mcc reflect <list|submit|scan> ...")
    sub = argv[0]
    if sub == "list":
        return cmd_reflect_list(argv[1:])
    if sub == "submit":
        return cmd_reflect_submit(argv[1:])
    if sub == "scan":
        return cmd_reflect_scan(argv[1:])
    die(f"unknown reflect subcommand '{sub}' (expected: list, submit, scan)")


def cmd_reflect_list(argv):
    """List reflection artifacts in ./tmp/, marked sent or unsent."""
    if argv:
        die("usage: mcc reflect list  (no args)")
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


def cmd_reflect_scan(argv):
    """Dry-run: just runs the privacy scan and prints output."""
    if not argv or argv[0].startswith("--"):
        die("usage: mcc reflect scan <path>")
    path = Path(argv[0])
    if not path.exists():
        die(f"no file at {path}")
    print(f"Running privacy scan on {path}...")
    print()
    is_clear, output = _run_privacy_scan(path)
    print(output)
    print()
    print(f"Result: {'CLEAR — safe to submit' if is_clear else 'concerns flagged — review before submitting'}")


def cmd_reflect_submit(argv):
    """Submit a reflection artifact to GitHub Issues."""
    explicit_path = None
    repo = FEEDBACK_REPO_DEFAULT
    skip_scan = False
    skip_confirm = False

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--repo" and i + 1 < len(argv):
            repo = argv[i + 1]
            i += 2
        elif a == "--no-scan":
            skip_scan = True
            i += 1
        elif a == "--no-confirm":
            skip_confirm = True
            i += 1
        elif a.startswith("--"):
            die(f"unknown flag: {a}")
        else:
            if explicit_path is not None:
                die(f"unexpected positional arg: {a}")
            explicit_path = a
            i += 1

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
            out[sid.strip()] = {"name": n.strip(), "scope": scope}
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


def cmd_session_list(argv):
    """List Claude Code sessions for the current project (or all projects)."""
    all_projects = False
    show_path = False
    for a in argv:
        if a == "--all":
            all_projects = True
        elif a in ("--paths", "--show-path"):
            show_path = True
        elif a.startswith("--"):
            die(f"unknown flag: {a}")
        else:
            die(f"unexpected arg: {a}")

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


def cmd_session_set(argv):
    """Register a session id under a name in .mcc[-scope]/sessions.

    Forms:
      mcc session set <name> <session-id> [--scope <s>]  — non-interactive
      mcc session set [--scope <s>]                      — interactive picker
    """
    rest = []
    explicit_scope = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--scope":
            if i + 1 >= len(argv):
                die("--scope requires a value (use '' for the default .mcc/)")
            explicit_scope = argv[i + 1]
            i += 2
            continue
        if a.startswith("--"):
            die(f"unknown flag: {a}")
        rest.append(a)
        i += 1

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


def cmd_session_transcript(argv):
    """Dump a session's transcript to markdown.

    Default: per-through-line — one file per significant branch in a
    subdirectory, plus an index.md summarizing the fork structure.
    --single-file: classic single-file output (chronological by default).
    --live-branch-only: implies --single-file; renders just the deepest chain.
    """
    output = None
    include_thinking = False
    include_compact_summaries = False
    include_meta = False
    include_harness_commands = False
    include_incomplete_branches = False
    post_compact_only = False
    live_branch_only = False
    single_file = False
    min_divergence = 10
    target = None

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--output" and i + 1 < len(argv):
            output = argv[i + 1]
            i += 2
        elif a == "--min-divergence" and i + 1 < len(argv):
            try:
                min_divergence = int(argv[i + 1])
            except ValueError:
                die(f"--min-divergence requires an integer (got '{argv[i + 1]}')")
            if min_divergence < 1:
                die("--min-divergence must be >= 1")
            i += 2
        elif a == "--include-thinking":
            include_thinking = True
            i += 1
        elif a == "--include-compact-summaries":
            include_compact_summaries = True
            i += 1
        elif a == "--include-meta":
            include_meta = True
            i += 1
        elif a == "--include-harness-commands":
            include_harness_commands = True
            i += 1
        elif a == "--include-incomplete-branches":
            include_incomplete_branches = True
            i += 1
        elif a == "--post-compact-only":
            post_compact_only = True
            i += 1
        elif a == "--live-branch-only":
            live_branch_only = True
            single_file = True  # live-branch-only is inherently a single chain
            i += 1
        elif a == "--single-file":
            single_file = True
            i += 1
        elif a.startswith("--"):
            die(f"unknown flag: {a}")
        else:
            if target is not None:
                die(f"unexpected positional arg: {a}")
            target = a
            i += 1

    if target is None:
        die("usage: mcc session transcript <name|session-id> "
            "[--output <path>] [--min-divergence N] "
            "[--include-thinking] [--include-compact-summaries] "
            "[--include-meta] [--include-harness-commands] "
            "[--include-incomplete-branches] "
            "[--post-compact-only] [--live-branch-only] [--single-file]")

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

    short_sid = sid[:8]
    ts_label = time.strftime("%Y%m%d-%H%M%S")

    # ---- Single-file modes ----
    if single_file:
        if live_branch_only:
            chain = _select_live_branch(entries)
            mode = "live-branch (depth-first tree walk)"
        else:
            chain = _select_chronological(entries)
            mode = "chronological (all entries by timestamp)"
        if not chain:
            die(f"no transcript entries found in {jsonl_path}")

        body = _render_chain(chain, base_opts)
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
        header = (
            f"# Transcript: {label}\n\n"
            f"- Session ID: `{sid}`\n"
            f"- Source: `{jsonl_path}`\n"
            f"- Generated: {now}\n"
            f"- Mode: {mode}\n"
            f"- Entries selected: {len(chain)}\n"
            f"{fork_line}"
            f"- Options: thinking={include_thinking} "
            f"compact_summaries={include_compact_summaries} "
            f"meta={include_meta} "
            f"harness_commands={include_harness_commands} "
            f"post_compact_only={post_compact_only}\n\n"
            f"---\n\n"
        )
        if output:
            out_path = Path(output)
        else:
            out_path = Path("tmp") / f"transcript_{label}_{short_sid}_{ts_label}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(header + body)
        print(f"Wrote {out_path}")
        print(f"  {len(chain)} entries from {jsonl_path}")
        return

    # ---- Default: per-through-line ----
    through_lines = _select_through_lines(
        entries,
        min_divergence=min_divergence,
        include_incomplete=include_incomplete_branches,
    )
    if not through_lines:
        die(
            f"no through-lines met the threshold (min_divergence={min_divergence}). "
            f"Try a lower --min-divergence, or use --single-file."
        )

    if output:
        out_dir = Path(output)
    else:
        out_dir = Path("tmp") / f"transcript_{label}_{short_sid}_{ts_label}"
    out_dir.mkdir(parents=True, exist_ok=True)

    base_opts["min_divergence"] = min_divergence
    results = _render_through_line_files(
        through_lines, sid, label, jsonl_path, base_opts, out_dir,
        fork_origin=fork_origin,
    )

    print(f"Wrote {len(results)} through-line file(s) to {out_dir}/")
    print(f"  index: {out_dir}/index.md")
    print(f"  threshold: --min-divergence {min_divergence}")
    print(f"  source: {jsonl_path}")


# ----------------------------- Commands -----------------------------

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
    """Parse 'plugin:role' → (plugin, role, persona_path). Returns (None, None, None) on error."""
    if ":" not in persona_arg:
        return (None, None, None)
    plugin, role = persona_arg.split(":", 1)
    if plugin not in PLUGINS:
        return (None, None, None)
    # Persona file lives at <marketplace-clone>/plugins/<plugin>/agents/<role>/agent.md
    mcc_dir = Path(__file__).resolve().parent  # /tools
    persona_path = mcc_dir.parent / "plugins" / plugin / "agents" / role / "agent.md"
    if not persona_path.exists():
        return (plugin, role, None)
    return (plugin, role, persona_path)


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


def cmd_create(argv):
    """Create a new session, register it, optionally pre-load persona profile."""
    if not argv:
        die("usage: mcc create <name> [--persona <plugin>:<role>] [--plugin <p>] [--scope <s>]")

    # Parse args
    name = None
    persona = None
    plugin = None
    scope = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--persona":
            if i + 1 >= len(argv):
                die("--persona requires an argument like 'mama:implementor'")
            persona = argv[i + 1]
            i += 2
        elif a == "--plugin":
            if i + 1 >= len(argv):
                die("--plugin requires an argument like 'mama'")
            plugin = argv[i + 1]
            i += 2
        elif a == "--scope":
            if i + 1 >= len(argv):
                die("--scope requires a value (use '' for the default .mcc/)")
            scope = argv[i + 1]
            i += 2
        elif name is None:
            name = a
            i += 1
        else:
            die(f"unexpected argument: {a}")
    if not name:
        die("usage: mcc create <name> [--persona <plugin>:<role>] [--plugin <p>] [--scope <s>]")

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


def cmd_resume(argv):
    if not argv:
        die("usage: mcc <name>")
    name = argv[0]
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
        cmd_list([])
        sys.exit(1)
    if not have_claude():
        die("'claude' command not found on PATH.")
    # Team-mode-aware launch: only attach team flags if the project has opted
    # into team mode (`mcc team setup` writes .mcc/team-name as the marker).
    # Otherwise mcc is plain session-naming sugar over `claude -r`.
    if _team_mode_enabled():
        team_name = ensure_team_setup(verbose=False)
        args = _team_launch_args(name, sid, team_name)
        print(f"Resuming '{name}' from {src} on team '{team_name}' → "
              f"claude -r {sid} (+team flags)", file=sys.stderr)
    else:
        args = ["claude", "-r", sid]
        print(f"Resuming '{name}' from {src} → claude -r {sid}",
              file=sys.stderr)
    os.execvp(args[0], args)


def cmd_list(argv):
    state_dirs = find_state_dirs()
    found_any = False
    for d in state_dirs:
        sessions_file = d / "sessions"
        if not sessions_file.exists():
            continue
        print(f"{sessions_file}:")
        for line in sessions_file.read_text().splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            n, sid = line.split("=", 1)
            print(f"  {n.strip():<12}  →  claude -r {sid.strip()}")
        found_any = True
    if not found_any:
        print("No sessions registered. Use /pdt:session, /mam:session, or /mama:session to register.")


def cmd_status(argv):
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


def cmd_enable(argv):
    if not argv:
        die("usage: mcc enable <pdt|mam|mama>")
    plugin = argv[0]
    _validate_plugin(plugin)
    if not have_claude():
        die("'claude' command not found on PATH.")
    print(f"Enabling {plugin}@{MARKETPLACE} in current project...")
    rc = claude_plugins("enable", "-s", "project", f"{plugin}@{MARKETPLACE}").returncode
    sys.exit(rc)


def cmd_disable(argv):
    if not argv:
        die("usage: mcc disable <pdt|mam|mama>")
    plugin = argv[0]
    _validate_plugin(plugin)
    if not have_claude():
        die("'claude' command not found on PATH.")
    print(f"Disabling {plugin}@{MARKETPLACE} in current project...")
    rc = claude_plugins("disable", "-s", "project", f"{plugin}@{MARKETPLACE}").returncode
    sys.exit(rc)


def cmd_switch(argv):
    if not argv:
        die("usage: mcc switch <mam|mama|off>")
    target = argv[0]
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


def cmd_update(argv):
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


def cmd_setup(argv):
    print("Methodical-CC setup")
    print("===================")
    print()
    print("This installs pdt, mam, mama, and bus at user scope, then asks which (if")
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


def cmd_version(argv):
    print(f"mcc {MCC_VERSION}")
    print(f"  script: {Path(__file__).resolve()}")


# ----------------------------- Dispatch -----------------------------

HANDLERS = {
    "list": cmd_list,
    "status": cmd_status,
    "setup": cmd_setup,
    "update": cmd_update,
    "enable": cmd_enable,
    "disable": cmd_disable,
    "switch": cmd_switch,
    "team": cmd_team,
    "create": cmd_create,
    "migrate": cmd_migrate,
    "vscode": cmd_vscode,
    "session": cmd_session,
    "reflect": cmd_reflect,
    "version": cmd_version,
}


# Per-command help. Each entry is detailed help shown by `mcc <cmd> -h` or
# `mcc <noun> <verb> -h`. Top-level summary in print_help() is built separately.
HELP = {
    # Top-level
    "<name>": """\
mcc <name> — resume the Claude Code session registered as <name>

Shorthand for `mcc session resume <name>`. If team mode is opted-in
(via `mcc team setup`), passes --team-name flags to claude; otherwise
runs plain `claude -r <sid>`.""",
    "create": """\
mcc create <name> [--persona <plugin>:<role>] [--plugin <p>] [--scope <s>]

Create a new Claude Code session, register it under <name>, and optionally
pre-load a persona profile.

  --persona <plugin>:<role>   e.g. mama:implementor
  --plugin  <p>               override inferred plugin (pdt|mam|mama)
  --scope   <s>               write registration to .mcc-<s>/sessions
                              (multi-project repos; auto-prompts if needed)""",
    "list": "mcc list — list all registered sessions in this project",
    "status": "mcc status — show plugin state and registered sessions",
    "setup": "mcc setup — interactive first-time setup (install + enable user-wide)",
    "update": "mcc update — update the methodical-cc marketplace and all plugins",
    "enable": "mcc enable <plugin> — enable plugin (pdt|mam|mama|bus) in current project",
    "disable": "mcc disable <plugin> — disable plugin (pdt|mam|mama|bus) in current project",
    "switch": "mcc switch <target> — swap impl plugin: mam | mama | off (leaves pdt alone)",
    "migrate": """\
mcc migrate — consolidate legacy state directories

Migrates legacy .mam/, .mama/, and .pdt[-scope]/ state directories into
the unified .mcc[-scope]/ layout. Idempotent.""",
    "vscode": """\
mcc vscode [<name|scope>...] [--group-by <mode>] [--group <label>=<a>,<b>]...
           [--no-folder-open]

Bootstrap or update .vscode/tasks.json with mcc session tasks.

Selection: positional args may be session names or scope names (multi-project
repos). With no positional args, prompts interactively.

Grouping (--group-by): controls how sessions are grouped into VSCode tabs.
  scope    one tab per .mcc-{scope}/ (default in multi-project repos)
  none     all sessions in one tab (default in single-project repos)
  custom   user-defined groups via --group <label>=<a>,<b> (repeatable)
           Passing any --group implies --group-by custom.

Per-group aggregator tasks `mcc:all:<label>` are emitted alongside the
top-level `mcc:all`. The mcc:all:* sub-namespace is reserved.

Auto-run on folder open: opt-in per group in scope/custom mode (default
none); none mode auto-runs `mcc:all` by default.

Flags:
  --group-by <scope|none|custom>
  --group <label>=<name1>,<name2>      repeatable; implies --group-by custom
  --no-folder-open                     don't auto-run anything on open

Examples:
  mcc vscode --group-by scope                       # tabs per project scope
  mcc vscode --group-by none                        # one tab with everything
  mcc vscode --group arch=admin-arch,app-arch \\
             --group impl=admin-impl,app-impl       # custom cross-project tabs""",
    "version": "mcc version — show mcc version",

    # mcc team
    "team": """\
mcc team — bus team setup and status

Subcommands:
  mcc team setup [--name <name>]   opt this project into team mode
  mcc team status                  show the project's bus team state

Run `mcc team <verb> -h` for full help.""",
    "team setup": """\
mcc team setup [--name <name>]

Opt this project into team mode and create the bus team config.
Interactive prompt for the team name (default = dirname); pass --name
to skip. Writes `.mcc/team-name` as the opt-in marker; thereafter
`mcc <name>` passes team flags to claude. Without this, mcc operates
as plain session-naming sugar.""",
    "team status": "mcc team status — show the project's bus team state",

    # mcc session
    "session": """\
mcc session — registered session management

Subcommands:
  mcc session list [--all] [--paths]              list sessions
  mcc session set [<name> <session-id>] [--scope <s>]
                                                  register a session
  mcc session resume <name>                       formal verb for `mcc <name>`
  mcc session transcript <name|sid> [opts...]     dump transcript

Run `mcc session <verb> -h` for full help.""",
    "session list": """\
mcc session list [--all] [--paths]

List Claude Code sessions for the current project (default) or all projects
(--all). Works without .mcc/ setup. Shows last activity, registered name,
and a title (best-effort: /rename → /title → ai-title → first user message
preview).""",
    "session set": """\
mcc session set <name> <session-id> [--scope <s>]
mcc session set [--scope <s>]

Register a session id under <name>. Two forms:
  - With both args: non-interactive registration.
  - No positional args: interactive picker — pick from sessions in this
    project, then enter a name.

In multi-project repos with multiple .mcc-{scope}/ directories, you must
disambiguate via --scope; if not given, mcc prompts (interactive) or
errors with a hint (non-interactive). The prompt's default is derived
from the session-name prefix (e.g. "admin-arch" → "admin").

If team mode is opted-in, also tops up the team config.""",
    "session resume": "mcc session resume <name> — formal verb for `mcc <name>`",
    "session transcript": """\
mcc session transcript <name|session-id> [options]

Dump a session transcript to markdown.

Default: per-through-line — emits a subdirectory with one file per
significant branch (chain root → real conversational leaf), plus an
index.md.

Options:
  --output <path>                  output dir or file
  --min-divergence N               min unique entries for a branch to
                                   count as significant (default 10)
  --include-thinking
  --include-compact-summaries
  --include-meta                   system-injected meta entries
  --include-harness-commands       harness-only slash commands like /exit
  --include-incomplete-branches    restore tool-flow leaves (forensic)
  --single-file                    one combined markdown file (chronological
                                   all-entries by default)
  --live-branch-only               with --single-file, render deepest chain
  --post-compact-only              skip pre-compact history

Default output: tmp/transcript_*/ (dir) or tmp/transcript_*.md (single-file).""",

    # mcc reflect
    "reflect": """\
mcc reflect — submit methodology-feedback artifacts

Subcommands:
  mcc reflect list                 list reflection artifacts in ./tmp/
  mcc reflect scan <path>          dry-run privacy scan
  mcc reflect submit [<path>]      submit reflection to GitHub Issues

Run `mcc reflect <verb> -h` for full help.""",
    "reflect list": """\
mcc reflect list — list reflection artifacts in ./tmp/, marked sent/unsent

Artifacts at tmp/mama_reflection_*.md or similar. Sent ones have a `.sent`
sidecar containing the issue URL.""",
    "reflect scan": "mcc reflect scan <path> — dry-run: just runs the privacy scan",
    "reflect submit": """\
mcc reflect submit [<path>] [--repo <r>] [--no-scan] [--no-confirm]

Submit a reflection artifact to GitHub Issues. Auto-picks latest unsent if
no path. Runs a privacy scan via `claude -p` first; user confirms before
posting. On success, writes a `.sent` sidecar with the issue URL.""",
}


# Top-level help structure: ordered groups → list of (token, one-liner).
TOP_HELP_GROUPS = [
    ("Session", [
        ("<name>",  "Resume session by name (shorthand for `session resume`)"),
        ("create",  "Create + register a new session"),
        ("list",    "List registered sessions"),
        ("session", "session list/set/resume/transcript (`mcc session -h`)"),
    ]),
    ("Project", [
        ("status",  "Show plugin state and registered sessions"),
        ("vscode",  "Bootstrap .vscode/tasks.json with session tasks"),
        ("team",    "Bus team setup/status (`mcc team -h`)"),
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
            print(f"  {tok:<10} {desc}")
        print()
    print("Run `mcc <command> -h` for detailed help.")


def print_help_for(tokens):
    """Print detailed help for a command path like ['session', 'set'] or ['vscode']."""
    key = " ".join(tokens)
    if key in HELP:
        print(HELP[key])
        return
    # Maybe they asked for a noun that we have but with a verb suffix typo
    if len(tokens) >= 2 and tokens[0] in HELP:
        print(f"Unknown subcommand for `mcc {tokens[0]}`. Showing top-level help for `mcc {tokens[0]}`:")
        print()
        print(HELP[tokens[0]])
        return
    die(f"no help for: mcc {key}")


def _is_help_flag(s):
    return s in ("-h", "--help")


def main():
    argv = sys.argv[1:]
    # Top-level: no args, or `help`/`-h`/`--help` as the first token
    if not argv or argv[0] in ("help", "-h", "--help"):
        print_help()
        return
    if argv[0] in ("--version", "-v"):
        cmd_version(argv[1:])
        return

    # Help requests anywhere in the argv: `mcc <cmd> -h`, `mcc <noun> <verb> -h`
    if any(_is_help_flag(a) for a in argv):
        # Strip help flags and treat the remainder as the command path
        path = [a for a in argv if not _is_help_flag(a)]
        if not path:
            print_help()
            return
        print_help_for(path)
        return

    cmd = argv[0]
    rest = argv[1:]

    handler = HANDLERS.get(cmd)
    if handler is not None:
        handler(rest)
    else:
        # Anything not a known subcommand is treated as a session name
        cmd_resume([cmd])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(130)
