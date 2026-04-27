#!/usr/bin/env python3
"""mcc - methodical-cc helper CLI

Usage:
  mcc <name>               Resume Claude Code session registered as <name>
  mcc list                 List all registered sessions in this project
  mcc status               Show plugin state and registered sessions
  mcc setup                Interactive first-time setup (install + enable user-wide)
  mcc enable <plugin>      Enable plugin (pdt|mam|mama) in current project
  mcc disable <plugin>     Disable plugin (pdt|mam|mama) in current project
  mcc switch <target>      Swap impl plugin: mam | mama | off (leaves pdt alone)
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

PLUGINS = ("pdt", "mam", "mama")
MARKETPLACE = "methodical-cc"
STATE_DIR_GLOBS = (".pdt", ".pdt-*", ".mam", ".mam-*", ".mama", ".mama-*")


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
    print(f"Resuming '{name}' from {src} → claude -r {sid}", file=sys.stderr)
    os.execvp("claude", ["claude", "-r", sid])


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


def cmd_setup(argv):
    print("Methodical-CC setup")
    print("===================")
    print()
    print("This installs pdt, mam, and mama at user scope, then asks which (if any)")
    print("should be enabled user-wide. Any combination is valid — including all-off.")
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
    print("Enter a space-separated list (e.g. 'pdt mam'), 'all', or 'none'.")
    print(f"Available: {', '.join(PLUGINS)}")
    choice = prompt("Enabled user-wide", default="pdt").strip().lower()

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


# ----------------------------- Dispatch -----------------------------

HANDLERS = {
    "list": cmd_list,
    "status": cmd_status,
    "setup": cmd_setup,
    "enable": cmd_enable,
    "disable": cmd_disable,
    "switch": cmd_switch,
}


def print_help():
    print(__doc__.strip())


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("help", "-h", "--help"):
        print_help()
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
