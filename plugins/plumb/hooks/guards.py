#!/usr/bin/env python3
"""plumb guards — lessons that became guards.

The strongest single finding of the effort PLUMB is built from:

    Recorded PROCEDURAL lessons do not self-apply. The rAF-timing trap fired
    twice. Control-byte separators fired three times — twice against the same
    person who had written the lesson down. Shared-index commit races fired
    three times. Lessons that can become guards, should.

    (Recorded STRUCTURAL shapes did self-apply. It is specifically the
    procedural ones that decay.)

None of the checks here require judgment, which is exactly why they belong in
tooling rather than in a document. Each is attached to an incident.

Dispatches on hook event; registered for PreToolUse and PostToolUse on Bash,
and PostToolUse on Edit/Write (to maintain the touched-path set the
foreign-staged guard needs).

Every guard is individually disable-able via `[guards]` in .plumb.toml.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
try:
    from plumb import Manifest, find_project_root
except ImportError:  # guards must never break a session because an import moved
    Manifest, find_project_root = None, None


# ------------------------------------------------------------------ plumbing

def emit_deny(reason):
    """Block the tool call. The reason is the whole value — make it teach."""
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, sys.stdout)
    sys.exit(0)


def emit_context(event, text):
    json.dump({"hookSpecificOutput": {
        "hookEventName": event,
        "additionalContext": text,
    }}, sys.stdout)
    sys.exit(0)


def guards_enabled(root):
    """Read [guards] from the manifest. Absent manifest → all guards on.

    A project that has not adopted PLUMB's process still gets the guards; they
    are useful on their own and cost nothing to a project that never trips one.
    """
    if Manifest is None:
        return {}
    try:
        mf = Manifest.load(root, required=False)
    except SystemExit:
        return {}
    return dict(mf.data.get("guards", {}) or {}) if mf else {}


def enabled(cfg, name):
    return cfg.get(name, True) is not False


def git(root, *args):
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True,
                             text=True, timeout=15)
        return out.stdout if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def state_dir(root):
    d = Path(root) / ".mcc" / "plumb"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ------------------------------------------------- guard 1: foreign staged

def is_git_commit(cmd):
    return bool(re.search(r"\bgit\b(?![^|;&]*\b--help\b)[^|;&]*\bcommit\b", cmd))


def has_explicit_pathspec(cmd):
    """`git commit -- <paths>` is safe by construction — it cannot sweep."""
    return bool(re.search(r"\bcommit\b[^|;&]*\s--\s+\S", cmd))


def touched_file(root, session):
    return state_dir(root) / f"touched-{session or 'anon'}"


def record_touch(root, session, path):
    if not path:
        return
    try:
        rel = os.path.relpath(Path(path).resolve(), Path(root).resolve())
    except ValueError:
        return
    if rel.startswith(".."):
        return
    f = touched_file(root, session)
    seen = set(f.read_text(encoding="utf-8").split("\n")) if f.exists() else set()
    if rel not in seen:
        with f.open("a", encoding="utf-8") as fh:
            fh.write(rel + "\n")


def read_touched(root, session):
    f = touched_file(root, session)
    if not f.exists():
        return set()
    return {ln for ln in f.read_text(encoding="utf-8").split("\n") if ln}


def guard_foreign_staged(root, session):
    """One agent's staged work riding into another's commit in a shared tree.

    Three instances. Most recently it caught the Architect mid-sentence *about
    process drift*: three `git rm`'d files rode into the Implementor's commit
    under a message about error codes. Content unharmed, attribution wrong.

    The window was seconds and still lost the race — a shared index has no turn
    boundary even when the bus does.
    """
    staged = [p for p in git(root, "diff", "--cached", "--name-only").split("\n") if p]
    if not staged:
        return None
    touched = read_touched(root, session)
    if not touched:
        # Nothing recorded — this session did its edits some way we can't see
        # (a shell heredoc, an external editor). Staying silent beats crying
        # wolf on every commit.
        return None
    foreign = [p for p in staged if p not in touched]
    if not foreign:
        return None
    listing = "\n".join(f"    {p}" for p in foreign[:20])
    more = f"\n    … and {len(foreign) - 20} more" if len(foreign) > 20 else ""
    return (
        f"BLOCKED — {len(foreign)} staged path(s) this session never touched:\n\n"
        f"{listing}{more}\n\n"
        f"A bare `git commit` commits the whole index, so another agent's staged "
        f"work rides into your commit under your message. This has happened three "
        f"times in the effort this guard came from; content survived, attribution "
        f"did not.\n\n"
        f"  • If these ARE yours, commit explicitly:  git commit -- <your paths>\n"
        f"  • If they are another agent's, leave them staged and commit only yours.\n"
        f"  • Never `git rm`/`git mv` and then go do something else — `git mv` "
        f"stages\n    immediately, so it is published into a shared place the "
        f"moment it is made.\n\n"
        f"Stage and commit in one breath, or not at all."
    )


# ------------------------------------------ guard 2: control bytes in sources

CONTROL_OK = {0x09, 0x0A, 0x0D}  # tab, LF, CR


def guard_control_bytes(root):
    """A source file containing raw control bytes.

    `grep` silently skips a file it considers binary, so "not found" means "not
    searched" — and the wrong reading was nearly acted on. Three instances; the
    third was a PRE-EXISTING one (raw 0x1F in a test literal, grep-invisible for
    several sprints).

    The generalisable half, and the reason this guard is worth more than the
    bug it catches: **a tool returning nothing is ambiguous between "absent"
    and "unsearchable."** Verify the tool could see before believing what it
    didn't find.
    """
    staged = [p for p in git(root, "diff", "--cached", "--name-only",
                             "--diff-filter=ACM").split("\n") if p]
    hits = []
    for rel in staged:
        p = Path(root) / rel
        if not p.is_file() or p.stat().st_size > 2_000_000:
            continue
        try:
            raw = p.read_bytes()
        except OSError:
            continue
        if b"\x00" not in raw and not any(
                b < 0x20 and b not in CONTROL_OK for b in raw[:200_000]):
            continue
        for i, b in enumerate(raw[:200_000]):
            if b < 0x20 and b not in CONTROL_OK:
                line = raw[:i].count(b"\n") + 1
                hits.append((rel, f"0x{b:02X}", line))
                break
    if not hits:
        return None
    listing = "\n".join(f"    {f}  byte {b} at line {ln}" for f, b, ln in hits)
    return (
        f"BLOCKED — {len(hits)} staged source file(s) contain raw control bytes:\n\n"
        f"{listing}\n\n"
        f"A file like this reads as binary to `grep`, which then SKIPS it silently. "
        f"Every later search of this repo will report 'not found' when it means "
        f"'not searched'.\n\n"
        f"The durable fix is not a luckier byte — every instance of this was "
        f"someone reaching for an 'unlikely' separator. Stop choosing separators: "
        f"`JSON.stringify([...])` or escape-before-join sidesteps the question "
        f"instead of picking a different character to collide with later."
    )


# ------------------------------------------------------- guard 3: secret scan

SECRET_PATTERNS = [
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{36,}\b"), "GitHub token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b"), "GitHub fine-grained PAT"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}"), "Anthropic API key"),
    (re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"), "OpenAI-style API key"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"), "JWT"),
    (re.compile(r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token)"
                r"\s*[:=]\s*[\"']([^\"'\s]{12,})[\"']"), "credential assignment"),
]

PLACEHOLDER = re.compile(r"(?i)(example|placeholder|redacted|your[_-]?|xxx+|\.\.\.|"
                         r"<[^>]+>|\$\{|changeme|dummy|fake|sample|test[_-]?key)")


def guard_secrets(root):
    """Credentials entering history.

    Caught a live API token that a `git add -A` had swept into staging. Once a
    secret is in history, removing it is a rewrite, not an edit.

    Scans ADDED lines only — existing content is already committed, and
    re-flagging it every time would train the reader to dismiss the guard.
    """
    diff = git(root, "diff", "--cached", "--unified=0")
    hits, current = [], "?"
    for line in diff.split("\n"):
        if line.startswith("+++ b/"):
            current = line[6:]
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:]
        if PLACEHOLDER.search(body):
            continue
        for pat, label in SECRET_PATTERNS:
            if pat.search(body):
                hits.append((current, label, body.strip()[:80]))
                break
    if not hits:
        return None
    listing = "\n".join(f"    {f}: {label}\n      {snippet}" for f, label, snippet in hits[:10])
    return (
        f"BLOCKED — {len(hits)} possible credential(s) in staged additions:\n\n"
        f"{listing}\n\n"
        f"Once this is committed, removing it is a history rewrite rather than an "
        f"edit — and if the branch has been pushed, the credential must be treated "
        f"as compromised and rotated regardless of what you do to the history.\n\n"
        f"If this is genuinely not a secret, unstage it, make that legible (a "
        f"placeholder, an env var, an `.env.example` entry), and re-stage."
    )


# --------------------------------------------- guard 4: build verdict / stale

STALE_FLAGS = re.compile(r"--no-build\b|--no-restore\b|--no-compile\b|-DskipTests\b")
BUILD_CMD = re.compile(r"\b(?:dotnet\s+build|msbuild|make\b|cargo\s+build|"
                       r"go\s+build|tsc\b|npm\s+run\s+build|pnpm\s+build|"
                       r"yarn\s+build|gradle\s+build|mvn\s+(?:compile|package))")
BUILD_FAIL = re.compile(
    r"(?i)\bbuild failed\b|\bcompilation (?:failed|error)\b|"
    r"\berror [A-Z]{1,4}\d{2,}\b|\b[1-9]\d*\s+error\(s\)|"
    r"\berrors?\s*:\s*[1-9]")

EXIT_KEYS = ("exit_code", "exitCode", "returnCode", "return_code", "code", "status")


def response_exit_code(resp):
    """Prefer the real exit code; the field name varies, so accept the family.

    Regex on output is the fallback, not the method — 'Failed: 0' in a build
    that also prints a test summary reads as a failure to any naive pattern,
    which would mark a good build bad and then nag about every later --no-build.
    """
    if not isinstance(resp, dict):
        return None
    for key in EXIT_KEYS:
        val = resp.get(key)
        if isinstance(val, bool):
            continue
        if isinstance(val, int):
            return val
        if isinstance(val, str) and val.strip().lstrip("-").isdigit():
            return int(val.strip())
    return None


def build_state_file(root, session):
    return state_dir(root) / f"build-{session or 'anon'}"


def record_build(root, session, ok):
    build_state_file(root, session).write_text("ok" if ok else "failed", encoding="utf-8")


def last_build(root, session):
    f = build_state_file(root, session)
    return f.read_text(encoding="utf-8").strip() if f.exists() else None


def guard_build_verdict(root, session, cmd):
    """`--no-build` running stale binaries after a failed build.

    Twice in two days, on two different implementors: four green suites
    containing none of the changes under test. **A green indistinguishable from
    a green** — the reporting surface was silent in a way indistinguishable from
    healthy, which is the family this whole guard set exists for.
    """
    if not STALE_FLAGS.search(cmd):
        return None
    state = last_build(root, session)
    if state == "ok":
        return None
    detail = ("no successful build has been recorded in this session"
              if state is None else "the last recorded build in this session FAILED")
    return (
        f"⚠ plumb: this command skips the build ({STALE_FLAGS.search(cmd).group(0)}) "
        f"and {detail}.\n"
        f"A pass here is evidence about whatever binary is already on disk — which "
        f"may contain none of your changes. Twice in two days this produced four "
        f"green suites testing code that was never compiled: a green "
        f"indistinguishable from a green.\n"
        f"Build first, or state plainly in your report that this result is not "
        f"evidence about the current source."
    )


# --------------------------------------------------- guard 5: skip surfacing

SKIP_PATTERNS = [
    re.compile(r"(?i)\bskipped[:\s]+(\d+)"),
    re.compile(r"(?i)\b(\d+)\s+skipped\b"),
    re.compile(r"(?i)\bignored[:\s]+(\d+)"),
]
TEST_CMD = re.compile(r"\b(?:dotnet\s+test|pytest\b|npm\s+(?:run\s+)?test|"
                      r"pnpm\s+test|yarn\s+test|jest\b|vitest\b|go\s+test|"
                      r"cargo\s+test|mvn\s+test|gradle\s+test)")


def guard_skip_count(cmd, output):
    """A suite reporting success while an entire integration layer skipped.

    28 tests went dark behind a lying skip condition; the console said
    `Failed: 0`. A skip is not a pass, and a skip reason that lies is worse than
    a missing one — the norm that came out of it is that suite reports state
    their skip count, because **a total is the one number a skip cannot move.**
    """
    if not TEST_CMD.search(cmd):
        return None
    counts = [int(m.group(1)) for pat in SKIP_PATTERNS
              for m in pat.finditer(output or "") if m.group(1).isdigit()]
    total = max(counts) if counts else 0
    if total == 0:
        return None
    return (
        f"⚠ plumb: this run SKIPPED {total} test(s).\n"
        f"A skip is not a pass. Report the skip count alongside the pass count — a "
        f"suite that prints `Failed: 0` while an integration layer is dark reads "
        f"exactly like a healthy one. Before treating this as green, check that "
        f"the skip condition is still true and still means what it says: a "
        f"diagnostic that lies is worse than a missing one."
    )


# ------------------------------------------------------------------ dispatch

def handle_pre_bash(payload, root, cfg):
    cmd = (payload.get("tool_input") or {}).get("command", "")
    if not is_git_commit(cmd):
        return
    session = payload.get("session_id")
    reasons = []
    # Secrets and control bytes are properties of the CONTENT, so an explicit
    # pathspec does not make them safe — it only changes whose commit carries
    # them. Only the foreign-staged guard is moot under `git commit -- <paths>`,
    # because that form cannot sweep in the first place.
    if enabled(cfg, "secrets"):
        reasons.append(guard_secrets(root))
    if enabled(cfg, "control_bytes"):
        reasons.append(guard_control_bytes(root))
    if enabled(cfg, "foreign_staged") and not has_explicit_pathspec(cmd):
        reasons.append(guard_foreign_staged(root, session))
    reasons = [r for r in reasons if r]
    if reasons:
        emit_deny("\n\n———\n\n".join(reasons))


def handle_post_bash(payload, root, cfg):
    cmd = (payload.get("tool_input") or {}).get("command", "")
    resp = payload.get("tool_response") or {}
    output = resp if isinstance(resp, str) else (
        resp.get("stdout", "") + "\n" + resp.get("stderr", ""))
    session = payload.get("session_id")

    if BUILD_CMD.search(cmd) and not STALE_FLAGS.search(cmd):
        rc = response_exit_code(resp)
        ok = (rc == 0) if rc is not None else not BUILD_FAIL.search(output or "")
        record_build(root, session, ok=ok)

    notes = []
    if enabled(cfg, "build_verdict"):
        notes.append(guard_build_verdict(root, session, cmd))
    if enabled(cfg, "skip_count"):
        notes.append(guard_skip_count(cmd, output))
    notes = [n for n in notes if n]
    if notes:
        emit_context("PostToolUse", "\n\n".join(notes))


def handle_post_edit(payload, root):
    ti = payload.get("tool_input") or {}
    record_touch(root, payload.get("session_id"), ti.get("file_path"))


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    root = payload.get("cwd") or (find_project_root() if find_project_root else Path.cwd())
    if find_project_root:
        root = find_project_root(root)
    cfg = guards_enabled(root)
    if cfg.get("enabled") is False:
        return

    event = payload.get("hook_event_name")
    tool = payload.get("tool_name")
    if event == "PreToolUse" and tool == "Bash":
        handle_pre_bash(payload, root, cfg)
    elif event == "PostToolUse" and tool == "Bash":
        handle_post_bash(payload, root, cfg)
    elif event == "PostToolUse" and tool in ("Edit", "Write", "NotebookEdit"):
        handle_post_edit(payload, root)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a guard must never take the session down with it
        print(f"plumb guards: internal error ({exc.__class__.__name__}: {exc})",
              file=sys.stderr)
    sys.exit(0)
