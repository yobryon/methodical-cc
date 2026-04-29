#!/usr/bin/env python3
"""mcc - methodical-cc helper CLI

Usage:
  mcc <name>               Resume Claude Code session registered as <name>.
                           Auto-adds bus channel flags if bus is set up here.
  mcc list                 List all registered sessions in this project
  mcc status               Show plugin state and registered sessions
  mcc setup                Interactive first-time setup (install + enable user-wide)
  mcc update               Update the methodical-cc marketplace and all plugins
  mcc enable <plugin>      Enable plugin (pdt|mam|mama|bus) in current project
  mcc disable <plugin>     Disable plugin (pdt|mam|mama|bus) in current project
  mcc switch <target>      Swap impl plugin: mam | mama | off (leaves pdt alone)
  mcc bus setup            Install + enable bus plugin for this project; verify
                           Node >= 20 is on PATH and the server bundle is present
  mcc bus status           Show bus state for this project (identities, threads,
                           pending counts, runtime state)
  mcc version              Show mcc version
  mcc help                 Show this help

Sessions are registered from inside Claude Code via /pdt:session, /mam:session,
or /mama:session.

Plugin scoping: enable/disable/switch operate on the current project; setup
operates on the user scope. Per-project always wins over user when both are set.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MCC_VERSION = "1.0.0"

PLUGINS = ("pdt", "mam", "mama", "bus")
MARKETPLACE = "methodical-cc"
STATE_DIR_GLOBS = (".pdt", ".pdt-*", ".mam", ".mam-*", ".mama", ".mama-*")
BUS_INBOX_ROOT = Path(".mcc/bus/inbox")
BUS_CROSSOVER_ROOT = Path("docs/crossover")


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


# ----------------------------- Commands -----------------------------

def _bus_active_in_project():
    """Best-effort detection: was `mcc bus setup` run in this project?

    The presence of `.mcc/bus/inbox/` means the user explicitly set up the bus
    here. We use this as the signal to add channel-loading flags to claude
    invocations, so the user doesn't have to remember the dev flag every time.
    """
    return BUS_INBOX_ROOT.exists()


def _build_claude_resume_args(sid):
    """Build the argv for `claude -r <sid>` with channel flags if appropriate."""
    args = ["claude", "-r", sid]
    if _bus_active_in_project():
        args.extend(["--dangerously-load-development-channels", f"plugin:bus@{MARKETPLACE}"])
    return args


def cmd_resume(argv):
    if not argv:
        die("usage: mcc <name>")
    name = argv[0]
    sid, src = find_session(name)
    if not sid:
        print(f"No session registered as '{name}'.", file=sys.stderr)
        print()
        cmd_list([])
        sys.exit(1)
    if not have_claude():
        die("'claude' command not found on PATH.")
    args = _build_claude_resume_args(sid)
    bus_note = " (+bus channel)" if _bus_active_in_project() else ""
    print(f"Resuming '{name}' from {src}{bus_note}", file=sys.stderr)
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

    # If bus is in the enabled set, verify Node ≥ 20. Don't block, but warn loudly.
    if "bus" in enabled:
        node_ok, node_ver = _node_version_ok()
        if not node_ok:
            print()
            if node_ver:
                print(f"  ⚠️  Node v{node_ver} found, but the bus MCP server requires Node ≥ 20.")
                print(f"      Bus will install but won't run until Node is upgraded.")
                print(f"      Update Node: https://nodejs.org/")
            else:
                print(f"  ⚠️  Node.js not found on PATH. The bus MCP server requires Node ≥ 20.")
                print(f"      Bus will install but won't run until Node is installed.")
                print(f"      Install Node: https://nodejs.org/")
            print(f"      (After installing/upgrading, re-run `mcc bus setup` to verify.)")

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


# ----------------------------- Bus subcommands -----------------------------

def _bus_server_dir():
    """Locate plugins/bus/server/ relative to mcc.py."""
    mcc_dir = Path(__file__).resolve().parent  # /tools
    return mcc_dir.parent / "plugins" / "bus" / "server"


def _bus_bundle_path():
    return _bus_server_dir() / "server.bundle.js"


def _ensure_gitignore_for_mcc():
    gitignore = Path(".gitignore")
    line = ".mcc/"
    if not gitignore.exists():
        gitignore.write_text(f"{line}\n")
        return True
    content = gitignore.read_text()
    if line in content.splitlines():
        return False
    if not content.endswith("\n"):
        content += "\n"
    gitignore.write_text(content + f"{line}\n")
    return True


def _node_version_ok():
    """Return (ok, version_str). ok=True if Node is installed and >= v20."""
    if not shutil.which("node"):
        return False, None
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            return False, None
        ver = result.stdout.strip().lstrip("v")
        major = int(ver.split(".")[0])
        return major >= 20, ver
    except Exception:
        return False, None


def cmd_bus(argv):
    if not argv:
        die("usage: mcc bus <setup|status>")
    sub = argv[0]
    if sub == "setup":
        return cmd_bus_setup(argv[1:])
    if sub == "status":
        return cmd_bus_status(argv[1:])
    die(f"unknown bus subcommand '{sub}' (expected: setup, status)")


def cmd_bus_setup(argv):
    if not have_claude():
        die("'claude' command not found on PATH.")

    print("Bus setup")
    print("=========")
    print()

    # 0. Verify Node ≥ 20 (required to run the bundled MCP server)
    node_ok, node_ver = _node_version_ok()
    if not node_ok:
        if node_ver:
            print(f"  Error: Node {node_ver} found, but v20+ is required for the bus MCP server.")
        else:
            print("  Error: Node.js not found on PATH.")
        print("  Install Node ≥ 20 from https://nodejs.org/ then re-run `mcc bus setup`.")
        sys.exit(1)
    print(f"→ Node v{node_ver} OK")

    # 1. Verify the bundled server is present in the marketplace clone
    bundle = _bus_bundle_path()
    if not bundle.exists():
        print(f"  Error: bus server bundle not found at {bundle}")
        print("  This usually means the marketplace clone is incomplete or out of date.")
        print("  Try `mcc update` to refresh, or report this as a bug.")
        sys.exit(1)
    size_kb = bundle.stat().st_size // 1024
    print(f"→ Bus server bundle present ({size_kb} KB)")

    # 2. Install at user scope (idempotent)
    print(f"→ Ensuring bus@{MARKETPLACE} is installed at user scope...")
    result = claude_plugins("install", "-s", "user", f"bus@{MARKETPLACE}", capture=True)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        print(f"  (note: {stderr or 'install returned non-zero — may already be installed'})")

    # 3. Enable for project
    print(f"→ Enabling bus for current project...")
    rc = claude_plugins("enable", "-s", "project", f"bus@{MARKETPLACE}").returncode
    if rc != 0:
        print(f"  Warning: enable returned rc={rc}")

    # 4. Create inbox directory structure
    BUS_INBOX_ROOT.mkdir(parents=True, exist_ok=True)
    print(f"→ Created {BUS_INBOX_ROOT}/")

    # 5. Update .gitignore
    if _ensure_gitignore_for_mcc():
        print(f"→ Added .mcc/ to .gitignore")

    print()
    print("Bus setup complete.")
    print()
    print("Note: Channels are in research preview. To use the bus, launch Claude Code with:")
    print("  claude --dangerously-load-development-channels plugin:bus@methodical-cc")
    print()
    print("Inside a Claude session, register identity with /pdt:session, /mam:session,")
    print("or /mama:session — that name becomes your bus identity.")


def cmd_bus_status(argv):
    print("Bus status")
    print("==========")
    print()

    # Plugin state
    if have_claude():
        print("Plugin state (from `claude plugins list`):")
        result = claude_plugins("list", capture=True)
        if result.returncode == 0:
            for line in (result.stdout or "").splitlines():
                if "bus" in line.lower():
                    print(f"  {line.strip()}")
        else:
            print("  (claude plugins list failed)")
    print()

    # Identities (from sessions files in cwd)
    print("Registered identities in this project:")
    found_any = False
    for d in find_state_dirs():
        sf = d / "sessions"
        if sf.exists():
            for line in sf.read_text().splitlines():
                line = line.strip()
                if not line or "=" not in line:
                    continue
                name, sid = line.split("=", 1)
                inbox = BUS_INBOX_ROOT / name.strip()
                pending = 0
                if inbox.exists():
                    pending = len([p for p in inbox.iterdir()
                                   if p.is_file() and p.suffix == ".json"])
                pending_str = f"  ({pending} pending)" if pending else ""
                print(f"  {name.strip():<14} {sf}{pending_str}")
                found_any = True
    if not found_any:
        print("  (none — register sessions via /pdt:session, /mam:session, or /mama:session)")

    # Active threads
    print()
    print("Active threads:")
    crossover = BUS_CROSSOVER_ROOT
    found_threads = False
    if crossover.exists():
        for d in sorted(crossover.iterdir()):
            if not d.is_dir():
                continue
            state_file = d / ".bus-state.json"
            if not state_file.exists():
                continue
            try:
                import json as _json
                state = _json.loads(state_file.read_text())
            except Exception:
                continue
            if state.get("status") != "open":
                continue
            participants = ", ".join(state.get("participants", []))
            last = state.get("last_activity_at", "?")
            awaiting = state.get("awaiting") or "—"
            print(f"  {d.name}  [{participants}]  last: {last}, awaiting: {awaiting}")
            found_threads = True
    if not found_threads:
        print("  (none open)")

    # Runtime status
    print()
    print("Runtime:")
    node_ok, node_ver = _node_version_ok()
    if node_ok:
        print(f"  ✓ Node v{node_ver}")
    elif node_ver:
        print(f"  ✗ Node v{node_ver} found but v20+ required — install a newer Node")
    else:
        print("  ✗ Node not on PATH — install Node ≥ 20")
    bundle = _bus_bundle_path()
    if bundle.exists():
        size_kb = bundle.stat().st_size // 1024
        print(f"  ✓ server.bundle.js ({size_kb} KB) at {bundle}")
    else:
        print(f"  ✗ server.bundle.js missing at {bundle} — try `mcc update`")


# ----------------------------- Dispatch -----------------------------

HANDLERS = {
    "list": cmd_list,
    "status": cmd_status,
    "setup": cmd_setup,
    "update": cmd_update,
    "enable": cmd_enable,
    "disable": cmd_disable,
    "switch": cmd_switch,
    "bus": cmd_bus,
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
