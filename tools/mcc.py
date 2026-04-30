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
  mcc team setup                   Explicitly create/update the bus team config
                                   for the current project (also runs implicitly
                                   on every `mcc <name>` and `mcc create <name>`)
  mcc team status                  Show the project's bus team state
  mcc migrate                      Consolidate legacy .mam/.mama/.pdt[-scope]/
                                   state directories into .mcc[-scope]/
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

MCC_VERSION = "1.1.2"

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

def derive_team_name(cwd=None):
    """Team name = sanitized repo basename. Lowercase, replace dots/spaces with dashes."""
    cwd = cwd or Path.cwd()
    base = cwd.name
    # Sanitize: lowercase, replace non-alphanumeric (except - and _) with -
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", base).lower().strip("-")
    return sanitized or "project"


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
    print("Bus team setup")
    print("==============")
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
