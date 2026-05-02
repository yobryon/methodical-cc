#!/usr/bin/env python3
"""mcc - methodical-cc helper CLI

Usage:
  mcc <name>                       Resume Claude Code session registered as <name>,
                                   joined to the project's bus team automatically
  mcc create <name> [--persona <plugin>:<role>] [--plugin <p>]
                                   Create a new session, register it under <name>,
                                   optionally pre-load a persona profile (e.g.
                                   `mcc create impl --persona mama:implementor`)
  mcc list                         List all registered sessions in this project
  mcc status                       Show plugin state and registered sessions
  mcc setup                        Interactive first-time setup (install + enable user-wide)
  mcc update                       Update the methodical-cc marketplace and all plugins
  mcc enable <plugin>              Enable plugin (pdt|mam|mama|bus) in current project
  mcc disable <plugin>             Disable plugin (pdt|mam|mama|bus) in current project
  mcc switch <target>              Swap impl plugin: mam | mama | off (leaves pdt alone)
  mcc team setup [--name <name>]   Explicitly create/update the bus team config
                                   for the current project (interactive prompt
                                   for the team name, default = dirname; pass
                                   --name to skip the prompt). Also runs
                                   implicitly on every `mcc <name>` and
                                   `mcc create <name>`.
  mcc team status                  Show the project's bus team state
  mcc migrate                      Consolidate legacy .mam/.mama/.pdt[-scope]/
                                   state directories into .mcc[-scope]/
  mcc vscode [<name>...] [--no-folder-open]
                                   Bootstrap/update .vscode/tasks.json with
                                   mcc session tasks (interactive if no names)
  mcc session transcript <name|session-id> [--output <path>]
                                  [--include-thinking] [--post-compact-only]
                                   Dump a session transcript to markdown.
                                   Walks parentUuid through compactions to
                                   produce the unbroken original conversation.
                                   Default output: tmp/transcript_*.md
  mcc version                      Show mcc version
  mcc help                         Show this help

Sessions are registered from inside Claude Code via /pdt:session, /mam:session,
or /mama:session — and via `mcc create <name>` from the shell.

Plugin scoping: enable/disable/switch operate on the current project; setup
operates on the user scope. Per-project always wins over user when both are set.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MCC_VERSION = "1.4.0"

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
    A project's team is a single thing even if state is split across .mcc-{scope}/ dirs."""
    cwd = cwd or Path.cwd()
    return cwd / ".mcc" / "team-name"


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
    (or always, when verbose=True).
    """
    # Passive upgrade: if a team was set up before the persisted-name feature,
    # snapshot its dirname-derived name into .mcc/team-name so subsequent runs
    # are stable even if the user later renames the directory.
    _passive_upgrade_team_name()
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


def _make_session_task(name):
    return {
        "label": f"mcc:{name}",
        "type": "shell",
        "command": f"mcc {name}",
        "isBackground": True,
        "presentation": {
            "reveal": "always",
            "panel": "dedicated",
            "group": "personas",
            "echo": False,
            "showReuseMessage": False,
        },
        "problemMatcher": [],
    }


def _make_aggregator_task(names):
    return {
        "label": "mcc:all",
        "dependsOn": [f"mcc:{n}" for n in names],
        "dependsOrder": "parallel",
        "runOptions": {"runOn": "folderOpen"},
        "problemMatcher": [],
    }


def cmd_vscode(argv):
    """Bootstrap or update .vscode/tasks.json with mcc session tasks."""
    no_folder_open = False
    names = []
    for a in argv:
        if a == "--no-folder-open":
            no_folder_open = True
        elif a.startswith("--"):
            die(f"unknown flag: {a}")
        else:
            names.append(a)

    registered = collect_all_registered_sessions()
    if not registered:
        die("no sessions registered in this project. Run `mcc create <name> ...` first.")

    if not names:
        # Interactive selection
        print("Registered sessions in this project:")
        for i, n in enumerate(registered, 1):
            print(f"  {i}. {n}")
        print()
        raw = prompt("Which to include? (e.g. 1,2,3 or 'all')", default="all").strip().lower()
        if raw == "all":
            names = list(registered)
        else:
            try:
                idxs = [int(x.strip()) for x in raw.split(",") if x.strip()]
                names = [registered[i - 1] for i in idxs]
            except (ValueError, IndexError):
                die(f"invalid selection: {raw}")
    else:
        unknown = [n for n in names if n not in registered]
        if unknown:
            die(f"not registered: {', '.join(unknown)}. Run `mcc create <name>` first.")

    if not names:
        die("no sessions selected; nothing to do.")

    new_mcc_tasks = [_make_session_task(n) for n in names]
    if not no_folder_open:
        new_mcc_tasks.append(_make_aggregator_task(names))

    vscode_dir = Path(".vscode")
    tasks_file = vscode_dir / "tasks.json"
    config = {"version": "2.0.0", "tasks": []}
    had_comments = False
    if tasks_file.exists():
        text = tasks_file.read_text()
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
    tasks_file.write_text(json.dumps(config, indent=2) + "\n")

    print(f"Wrote {tasks_file} with mcc tasks for: {', '.join(names)}")
    if not no_folder_open:
        print(f"  mcc:all will run automatically on folder open")
    if had_comments:
        print(f"  ! existing JSONC comments were dropped on write")
    print()
    print("In VS Code: Cmd/Ctrl+Shift+P → 'Tasks: Run Task' → mcc:all (or any individual mcc:<name>)")


# ----------------------------- Session transcript -----------------------------
#
# Reads ~/.claude/projects/<slug>/<sid>.jsonl and renders a clean markdown
# transcript by walking parentUuid from the most recent live leaf back to the
# root, traversing through compaction boundaries (which leave pre-compact history
# intact in the file). Tool calls render as compact slugs.
#
# Defensive throughout: malformed lines are skipped with a warning, missing
# fields are treated as absent rather than crashing.

CLAUDE_PROJECTS_ROOT = Path.home() / ".claude" / "projects"
TRANSCRIPT_TYPES = {"user", "assistant", "attachment", "system"}
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


def _looks_like_uuid(s):
    return bool(UUID_RE.match(s or ""))


def _project_slug_for_cwd(cwd=None):
    """Mirror Claude Code's slug derivation: full absolute path with / replaced by -."""
    cwd = (cwd or Path.cwd()).resolve()
    return str(cwd).replace("/", "-")


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
        with open(path) as f:
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


def _build_through_line(entries):
    """Walk parentUuid from the most-recent live leaf back to root.
    Returns ordered list (root first) or [] if no chain found."""
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

    # Children set: any uuid that appears as another entry's parentUuid
    children = set()
    for e in msgs.values():
        pid = e.get("parentUuid")
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

    # Most-recent live leaf — what `claude -r` would resume to
    leaf = max(leaves, key=lambda m: m.get("timestamp", ""))

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


def _render_user(entry):
    msg = entry.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        s = content.strip()
        return f"## User\n\n{s}" if s else None
    if isinstance(content, list):
        # Pure tool_result messages are plumbing — suppress
        if all(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return None
        text_parts = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                t = (b.get("text") or "").strip()
                if t:
                    text_parts.append(t)
        if text_parts:
            return "## User\n\n" + "\n\n".join(text_parts)
    return None


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


def _render_compact_boundary(entry):
    cm = entry.get("compactMetadata") or {}
    trigger = cm.get("trigger", "?")
    pre = cm.get("preTokens", "?")
    n = cm.get("messagesSummarized", "?")
    return (f"---\n\n"
            f"*[Compaction — `{trigger}`, {pre} tokens, {n} messages summarized]*\n\n"
            f"---")


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

    out_parts = []
    for e in chain:
        if e.get("isSidechain"):
            continue  # belt + suspenders; main JSONLs don't have these in current mode
        t = e.get("type")
        rendered = None
        if t == "system":
            if e.get("subtype") == "compact_boundary":
                rendered = _render_compact_boundary(e)
            # other system subtypes: skip
        elif t == "user":
            rendered = _render_user(e)
        elif t == "assistant":
            rendered = _render_assistant(e, opts.get("include_thinking", False))
        elif t == "attachment":
            rendered = _render_attachment(e)
        if rendered:
            out_parts.append(rendered)
    return "\n\n".join(out_parts) + "\n"


def cmd_session(argv):
    if not argv:
        die("usage: mcc session <transcript> ...")
    sub = argv[0]
    if sub == "transcript":
        return cmd_session_transcript(argv[1:])
    die(f"unknown session subcommand '{sub}' (expected: transcript)")


def cmd_session_transcript(argv):
    """Dump a session's transcript to markdown."""
    output = None
    include_thinking = False
    post_compact_only = False
    target = None

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--output" and i + 1 < len(argv):
            output = argv[i + 1]
            i += 2
        elif a == "--include-thinking":
            include_thinking = True
            i += 1
        elif a == "--post-compact-only":
            post_compact_only = True
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
            "[--output <path>] [--include-thinking] [--post-compact-only]")

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

    # Parse + walk
    entries = _parse_jsonl(jsonl_path)
    if not entries:
        die(f"{jsonl_path} contained no parseable entries")

    chain = _build_through_line(entries)
    if not chain:
        die(f"no transcript chain found in {jsonl_path} (no live leaf?)")

    body = _render_chain(chain, {
        "include_thinking": include_thinking,
        "post_compact_only": post_compact_only,
    })

    # Header
    short_sid = sid[:8]
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    header = (
        f"# Transcript: {label}\n\n"
        f"- Session ID: `{sid}`\n"
        f"- Source: `{jsonl_path}`\n"
        f"- Generated: {now}\n"
        f"- Entries in chain: {len(chain)}\n"
        f"- Options: thinking={include_thinking} post_compact_only={post_compact_only}\n\n"
        f"---\n\n"
    )

    # Output path
    if output:
        out_path = Path(output)
    else:
        ts = time.strftime("%Y%m%d-%H%M%S")
        out_path = Path("tmp") / f"transcript_{label}_{short_sid}_{ts}.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + body)

    print(f"Wrote {out_path}")
    print(f"  {len(chain)} entries from {jsonl_path}")


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
        die("usage: mcc create <name> [--persona <plugin>:<role>] [--plugin <p>]")

    # Parse args
    name = None
    persona = None
    plugin = None
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
        elif name is None:
            name = a
            i += 1
        else:
            die(f"unexpected argument: {a}")
    if not name:
        die("usage: mcc create <name> [--persona <plugin>:<role>] [--plugin <p>]")

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

    # Construct prompt for `claude -p`
    if persona_path:
        prompt_text = (
            f"/{plugin}:session set {name}\n\n"
            f"Then read your persona profile at @{persona_path} "
            f"and acknowledge with \"ok\"."
        )
    else:
        prompt_text = f"/{plugin}:session set {name}"

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
        # Top up team config now that the new identity is registered
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
    # Implicitly ensure team setup is current (idempotent — fast no-op when nothing changed)
    team_name = ensure_team_setup(verbose=False)
    args = _team_launch_args(name, sid, team_name)
    print(f"Resuming '{name}' from {src} on team '{team_name}' → "
          f"claude -r {sid} (+team flags)", file=sys.stderr)
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
        print("  (none — no .pdt/, .mam*/, or .mama*/ directories here)")
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
    "version": cmd_version,
}


def print_help():
    print(__doc__.strip())


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("help", "-h", "--help"):
        print_help()
        return
    if argv[0] in ("--version", "-v"):
        cmd_version(argv[1:])
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
